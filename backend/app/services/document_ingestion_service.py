"""Document ingestion pipeline: text extraction, chunking, embedding, and search.

Handles the full pipeline from uploaded file to searchable document chunks
stored in Neo4j with vector embeddings for hybrid semantic search.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import tiktoken

from neo4j import Driver

from app.config import Settings
from app.exceptions import DocumentNotFoundError
from app.models.actor import Actor
from app.models.document import (
    DocumentChunk,
    DocumentChunkResult,
    IngestionStatus,
)
from app.services.base_service import BaseService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

CHUNK_TARGET_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50


class DocumentIngestionService(BaseService):
    """Extracts text, chunks documents, generates embeddings, and provides search.

    Graph model:
        (DocumentChunk)-[:CHUNK_OF]->(Document)
        (DocumentChunk)-[:NEXT_CHUNK]->(DocumentChunk)
    """

    def __init__(self, driver: Driver, settings: Settings) -> None:
        """Initialise the ingestion service.

        Args:
            driver: Neo4j driver.
            settings: Application settings.
        """
        super().__init__(driver)
        self.embedding_service = EmbeddingService(driver, settings)
        self._tokenizer = tiktoken.get_encoding("cl100k_base")

    # -- Text extraction -----------------------------------------------------------

    def _extract_text_pdf(self, file_path: str) -> list[dict[str, Any]]:
        """Extract text from a PDF file, page by page.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of dicts with 'page' (1-indexed) and 'text' keys.
        """
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": i + 1, "text": text})
        return pages

    def _extract_text_docx(self, file_path: str) -> list[dict[str, Any]]:
        """Extract text from a DOCX file.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            List with a single dict (no page numbers in DOCX).
        """
        from docx import Document as DocxDocument

        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)
        if not full_text.strip():
            return []
        return [{"page": None, "text": full_text}]

    def _extract_text_plain(self, file_path: str) -> list[dict[str, Any]]:
        """Extract text from a plain text file.

        Args:
            file_path: Path to the text file.

        Returns:
            List with a single dict.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        if not text.strip():
            return []
        return [{"page": None, "text": text}]

    def extract_text(self, file_path: str, file_type: str) -> list[dict[str, Any]]:
        """Extract text from a file based on its type.

        Args:
            file_path: Path to the file.
            file_type: MIME type or file extension (pdf, docx, txt).

        Returns:
            List of dicts with 'page' and 'text' keys.

        Raises:
            ValueError: If the file type is unsupported.
        """
        ft = file_type.lower()
        if ft in ("application/pdf", "pdf", ".pdf"):
            return self._extract_text_pdf(file_path)
        elif ft in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "docx",
            ".docx",
        ):
            return self._extract_text_docx(file_path)
        elif ft in ("text/plain", "txt", ".txt"):
            return self._extract_text_plain(file_path)
        else:
            raise ValueError(f"Unsupported file type for text extraction: {file_type}")

    # -- Chunking ------------------------------------------------------------------

    def _count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            Token count.
        """
        return len(self._tokenizer.encode(text))

    def chunk_text(
        self, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Split extracted text into overlapping chunks.

        Splits on paragraph boundaries (double newlines), falling back to
        sentence boundaries, with ~500 token target size and ~50 token overlap.

        Args:
            pages: List of dicts with 'page' and 'text' keys from extraction.

        Returns:
            List of chunk dicts with 'text', 'page', 'chunk_index', 'position'.
        """
        chunks: list[dict[str, Any]] = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data["page"]
            text = page_data["text"]

            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            if not paragraphs:
                continue

            current_chunk_parts: list[str] = []
            current_tokens = 0

            for para in paragraphs:
                para_tokens = self._count_tokens(para)

                if para_tokens > CHUNK_TARGET_TOKENS:
                    if current_chunk_parts:
                        chunk_text = "\n\n".join(current_chunk_parts)
                        chunks.append({
                            "text": chunk_text,
                            "page": page_num,
                            "chunk_index": chunk_index,
                            "position": chunk_index,
                        })
                        chunk_index += 1
                        current_chunk_parts = []
                        current_tokens = 0

                    sentences = para.replace(". ", ".\n").split("\n")
                    for sent in sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        sent_tokens = self._count_tokens(sent)
                        if current_tokens + sent_tokens > CHUNK_TARGET_TOKENS and current_chunk_parts:
                            chunk_text = " ".join(current_chunk_parts)
                            chunks.append({
                                "text": chunk_text,
                                "page": page_num,
                                "chunk_index": chunk_index,
                                "position": chunk_index,
                            })
                            chunk_index += 1
                            overlap_text = " ".join(current_chunk_parts)
                            overlap_tokens = self._tokenizer.encode(overlap_text)
                            if len(overlap_tokens) > CHUNK_OVERLAP_TOKENS:
                                overlap_decoded = self._tokenizer.decode(
                                    overlap_tokens[-CHUNK_OVERLAP_TOKENS:]
                                )
                                current_chunk_parts = [overlap_decoded]
                                current_tokens = CHUNK_OVERLAP_TOKENS
                            else:
                                current_chunk_parts = [overlap_text]
                                current_tokens = len(overlap_tokens)

                        current_chunk_parts.append(sent)
                        current_tokens += sent_tokens
                    continue

                if current_tokens + para_tokens > CHUNK_TARGET_TOKENS and current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunks.append({
                        "text": chunk_text,
                        "page": page_num,
                        "chunk_index": chunk_index,
                        "position": chunk_index,
                    })
                    chunk_index += 1

                    overlap_text = "\n\n".join(current_chunk_parts)
                    overlap_tokens = self._tokenizer.encode(overlap_text)
                    if len(overlap_tokens) > CHUNK_OVERLAP_TOKENS:
                        overlap_decoded = self._tokenizer.decode(
                            overlap_tokens[-CHUNK_OVERLAP_TOKENS:]
                        )
                        current_chunk_parts = [overlap_decoded]
                        current_tokens = CHUNK_OVERLAP_TOKENS
                    else:
                        current_chunk_parts = [overlap_text]
                        current_tokens = len(overlap_tokens)

                current_chunk_parts.append(para)
                current_tokens += para_tokens

            if current_chunk_parts:
                chunk_text = "\n\n".join(current_chunk_parts)
                chunks.append({
                    "text": chunk_text,
                    "page": page_num,
                    "chunk_index": chunk_index,
                    "position": chunk_index,
                })
                chunk_index += 1

        return chunks

    # -- Graph operations ----------------------------------------------------------

    def _create_chunk_nodes(
        self, document_id: str, chunks: list[dict[str, Any]]
    ) -> list[str]:
        """Create DocumentChunk nodes and relationships in Neo4j.

        Creates CHUNK_OF relationships to the parent Document and NEXT_CHUNK
        chain between sequential chunks.

        Args:
            document_id: Parent Document node ID.
            chunks: List of chunk dicts from chunk_text().

        Returns:
            List of created chunk IDs in order.
        """
        chunk_ids: list[str] = []
        now = datetime.now(timezone.utc).isoformat()

        for chunk_data in chunks:
            chunk_id = self._generate_id("dchk")
            chunk_ids.append(chunk_id)

            self._write_tx_single(
                """
                MATCH (doc:Document {id: $document_id})
                CREATE (c:DocumentChunk {
                    id: $chunk_id,
                    text: $text,
                    page: $page,
                    position: $position,
                    chunk_index: $chunk_index,
                    created_at: $now
                })
                CREATE (c)-[:CHUNK_OF]->(doc)
                RETURN c.id AS id
                """,
                {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "text": chunk_data["text"],
                    "page": chunk_data["page"],
                    "position": chunk_data["position"],
                    "chunk_index": chunk_data["chunk_index"],
                    "now": now,
                },
            )

        for i in range(len(chunk_ids) - 1):
            self._write_tx_single(
                """
                MATCH (a:DocumentChunk {id: $from_id})
                MATCH (b:DocumentChunk {id: $to_id})
                CREATE (a)-[:NEXT_CHUNK]->(b)
                RETURN a.id AS from_id
                """,
                {"from_id": chunk_ids[i], "to_id": chunk_ids[i + 1]},
            )

        return chunk_ids

    def _update_document_status(
        self,
        document_id: str,
        ingestion_status: str,
        chunk_count: int | None = None,
    ) -> None:
        """Update the ingestion status on a Document node.

        Args:
            document_id: The Document node ID.
            ingestion_status: New status value.
            chunk_count: Number of chunks if ingestion is complete.
        """
        params: dict[str, Any] = {
            "document_id": document_id,
            "ingestion_status": ingestion_status,
            "now": datetime.now(timezone.utc).isoformat(),
        }

        set_clause = "d.ingestion_status = $ingestion_status, d.updated_at = $now"
        if chunk_count is not None:
            set_clause += ", d.chunk_count = $chunk_count"
            params["chunk_count"] = chunk_count

        self._write_tx_single(
            f"""
            MATCH (d:Document {{id: $document_id}})
            SET {set_clause}
            RETURN d.id AS id
            """,
            params,
        )

    # -- Full pipeline -------------------------------------------------------------

    def ingest_document(self, document_id: str, file_path: str, file_type: str) -> int:
        """Run the full ingestion pipeline for a document.

        1. Set status to processing
        2. Extract text
        3. Chunk text
        4. Create chunk nodes in Neo4j
        5. Generate and store embeddings
        6. Set status to complete

        Args:
            document_id: The Document node ID.
            file_path: Path to the uploaded file.
            file_type: MIME type or extension of the file.

        Returns:
            Number of chunks created.

        Raises:
            DocumentNotFoundError: If the document does not exist.
            ValueError: If the file type is unsupported.
        """
        self._update_document_status(document_id, IngestionStatus.PROCESSING.value)

        try:
            pages = self.extract_text(file_path, file_type)
            if not pages:
                self._update_document_status(
                    document_id, IngestionStatus.COMPLETE.value, chunk_count=0
                )
                logger.info("Document %s has no extractable text", document_id)
                return 0

            chunks = self.chunk_text(pages)
            if not chunks:
                self._update_document_status(
                    document_id, IngestionStatus.COMPLETE.value, chunk_count=0
                )
                return 0

            chunk_ids = self._create_chunk_nodes(document_id, chunks)

            embedded_count = self.embedding_service.embed_and_store_chunks(
                chunk_ids, [c["text"] for c in chunks]
            )
            logger.info(
                "Document %s: %d chunks created, %d embedded",
                document_id,
                len(chunk_ids),
                embedded_count,
            )

            self._update_document_status(
                document_id, IngestionStatus.COMPLETE.value, chunk_count=len(chunk_ids)
            )
            return len(chunk_ids)

        except Exception:
            logger.error(
                "Ingestion failed for document %s", document_id, exc_info=True
            )
            self._update_document_status(document_id, IngestionStatus.FAILED.value)
            raise

    # -- Search --------------------------------------------------------------------

    def search_chunks(
        self,
        company_id: str,
        query: str,
        project_id: str | None = None,
        document_type: str | None = None,
        top_k: int = 10,
    ) -> list[DocumentChunkResult]:
        """Hybrid search over document chunks using vector similarity.

        Generates an embedding for the query, then uses Neo4j vector index
        to find the most similar chunks, filtered by company access path.

        Args:
            company_id: The company to scope results to.
            query: The search query text.
            project_id: Optional project filter.
            document_type: Optional document type filter.
            top_k: Number of results to return.

        Returns:
            List of DocumentChunkResult sorted by relevance score.
        """
        query_embedding = self.embedding_service.generate_query_embedding(query)

        if query_embedding is not None:
            return self._vector_search(
                company_id, query_embedding, project_id, document_type, top_k
            )

        return self._text_search(
            company_id, query, project_id, document_type, top_k
        )

    def _vector_search(
        self,
        company_id: str,
        query_embedding: list[float],
        project_id: str | None,
        document_type: str | None,
        top_k: int,
    ) -> list[DocumentChunkResult]:
        """Run vector similarity search over document chunks.

        Args:
            company_id: Company scope.
            query_embedding: The query embedding vector.
            project_id: Optional project filter.
            document_type: Optional document type filter.
            top_k: Max results.

        Returns:
            Ranked list of chunk results.
        """
        where_clauses = [
            "doc.deleted = false",
            "doc.status IN ['active', 'draft', 'final']",
        ]
        params: dict[str, Any] = {
            "company_id": company_id,
            "top_k": top_k,
            "query_embedding": query_embedding,
        }

        if project_id:
            where_clauses.append("p.id = $project_id")
            params["project_id"] = project_id

        if document_type:
            where_clauses.append("doc.document_type = $document_type")
            params["document_type"] = document_type

        where_str = " AND ".join(where_clauses)

        results = self._read_tx(
            f"""
            CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_embedding)
            YIELD node AS chunk, score
            MATCH (chunk)-[:CHUNK_OF]->(doc:Document)
            MATCH (doc)<-[:HAS_DOCUMENT]-(c:Company {{id: $company_id}})
            WHERE {where_str}
            RETURN chunk.id AS chunk_id,
                   chunk.text AS text,
                   chunk.page AS page,
                   chunk.chunk_index AS chunk_index,
                   doc.id AS document_id,
                   doc.title AS document_title,
                   doc.document_type AS document_type,
                   score
            ORDER BY score DESC
            LIMIT $top_k
            """,
            params,
        )

        return [
            DocumentChunkResult(
                chunk_id=r["chunk_id"],
                text=r["text"],
                page=r.get("page"),
                chunk_index=r["chunk_index"],
                document_id=r["document_id"],
                document_title=r["document_title"],
                document_type=r.get("document_type"),
                score=r["score"],
            )
            for r in results
        ]

    def _text_search(
        self,
        company_id: str,
        query: str,
        project_id: str | None,
        document_type: str | None,
        top_k: int,
    ) -> list[DocumentChunkResult]:
        """Fallback text search using CONTAINS when embeddings are unavailable.

        Args:
            company_id: Company scope.
            query: The search query text.
            project_id: Optional project filter.
            document_type: Optional document type filter.
            top_k: Max results.

        Returns:
            List of matching chunk results with score=1.0.
        """
        where_clauses = [
            "doc.deleted = false",
            "doc.status IN ['active', 'draft', 'final']",
            "toLower(chunk.text) CONTAINS toLower($query)",
        ]
        params: dict[str, Any] = {
            "company_id": company_id,
            "query": query,
            "top_k": top_k,
        }

        if project_id:
            where_clauses.append("p.id = $project_id")
            params["project_id"] = project_id

        if document_type:
            where_clauses.append("doc.document_type = $document_type")
            params["document_type"] = document_type

        where_str = " AND ".join(where_clauses)

        results = self._read_tx(
            f"""
            MATCH (chunk:DocumentChunk)-[:CHUNK_OF]->(doc:Document)
            MATCH (doc)<-[:HAS_DOCUMENT]-(c:Company {{id: $company_id}})
            WHERE {where_str}
            RETURN chunk.id AS chunk_id,
                   chunk.text AS text,
                   chunk.page AS page,
                   chunk.chunk_index AS chunk_index,
                   doc.id AS document_id,
                   doc.title AS document_title,
                   doc.document_type AS document_type,
                   1.0 AS score
            LIMIT $top_k
            """,
            params,
        )

        return [
            DocumentChunkResult(
                chunk_id=r["chunk_id"],
                text=r["text"],
                page=r.get("page"),
                chunk_index=r["chunk_index"],
                document_id=r["document_id"],
                document_title=r["document_title"],
                document_type=r.get("document_type"),
                score=r["score"],
            )
            for r in results
        ]

    def get_document_chunks(self, document_id: str) -> list[DocumentChunk]:
        """Get all chunks for a document in order.

        Args:
            document_id: The Document node ID.

        Returns:
            List of DocumentChunk models ordered by chunk_index.
        """
        results = self._read_tx(
            """
            MATCH (c:DocumentChunk)-[:CHUNK_OF]->(d:Document {id: $document_id})
            RETURN c.id AS id,
                   $document_id AS document_id,
                   c.text AS text,
                   c.page AS page,
                   c.position AS position,
                   c.chunk_index AS chunk_index,
                   c.embedding IS NOT NULL AS has_embedding,
                   c.created_at AS created_at
            ORDER BY c.chunk_index ASC
            """,
            {"document_id": document_id},
        )

        return [
            DocumentChunk(
                id=r["id"],
                document_id=r["document_id"],
                text=r["text"],
                page=r.get("page"),
                position=r.get("position"),
                chunk_index=r["chunk_index"],
                has_embedding=r.get("has_embedding", False),
                created_at=r["created_at"],
            )
            for r in results
        ]

    def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document.

        Args:
            document_id: The Document node ID.

        Returns:
            Number of chunks deleted.
        """
        result = self._write_tx_single(
            """
            MATCH (c:DocumentChunk)-[:CHUNK_OF]->(d:Document {id: $document_id})
            WITH c, count(c) AS cnt
            DETACH DELETE c
            RETURN cnt
            """,
            {"document_id": document_id},
        )
        return result["cnt"] if result else 0
