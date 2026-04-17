"""Embedding service for generating vector representations of text.

Uses Anthropic's Voyage AI embeddings (voyage-3-lite, 1024-dim) via the
anthropic SDK. Falls back silently if the API key is not configured or the
call fails — embeddings are optional for MVP.

Vectors are written to Message.embedding and DocumentChunk.embedding for
semantic search via Neo4j vector indexes.
"""

import logging
from typing import Any

from anthropic import Anthropic

from neo4j import Driver

from app.config import Settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "voyage-3-lite"
EMBEDDING_DIM = 1024
BATCH_SIZE = 32


class EmbeddingService:
    """Generates text embeddings and writes them to Neo4j nodes.

    Attributes:
        driver: Neo4j driver for writing embeddings back to nodes.
        client: Anthropic client (used for Voyage embeddings).
        enabled: Whether the embedding API is available.
    """

    def __init__(self, driver: Driver, settings: Settings) -> None:
        """Initialise the embedding service.

        Args:
            driver: Neo4j driver for writing embeddings to graph nodes.
            settings: Application settings containing the Anthropic API key.
        """
        self.driver = driver
        # Voyage embeddings require a separate API key (VOYAGE_API_KEY).
        # Disable until configured — the Anthropic SDK doesn't expose embeddings.
        voyage_key = getattr(settings, "voyage_api_key", "")
        self.enabled = bool(voyage_key)
        self._client: Anthropic | None = None
        if self.enabled:
            self._client = Anthropic(api_key=voyage_key)

    def generate_embedding(self, text: str) -> list[float] | None:
        """Generate a vector embedding for the given text.

        Args:
            text: The text to embed. Truncated to 8000 chars for token limits.

        Returns:
            A list of floats (1024-dim), or None if unavailable/failed.
        """
        if not self.enabled or not self._client:
            return None

        try:
            truncated = text[:8000]
            response = self._client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=truncated,
            )
            return response.data[0].embedding
        except Exception:
            logger.warning("Embedding generation failed, skipping", exc_info=True)
            return None

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Generate embeddings for a batch of texts.

        Processes in batches of BATCH_SIZE to respect API limits.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (or None for failures), same order as input.
        """
        if not self.enabled or not self._client or not texts:
            return [None] * len(texts)

        results: list[list[float] | None] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = [t[:8000] for t in texts[i : i + BATCH_SIZE]]
            try:
                response = self._client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch,
                )
                for item in response.data:
                    results.append(item.embedding)
            except Exception:
                logger.warning(
                    "Batch embedding failed for batch starting at %d, skipping",
                    i,
                    exc_info=True,
                )
                results.extend([None] * len(batch))

        return results

    def embed_and_store_message(self, message_id: str, content: str) -> None:
        """Generate an embedding for a message and write it to Neo4j.

        This is a fire-and-forget operation — failures are logged but not raised.

        Args:
            message_id: The Message node ID in Neo4j.
            content: The text content to embed.
        """
        embedding = self.generate_embedding(content)
        if embedding is None:
            return

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (msg:Message {id: $message_id})
                    SET msg.embedding = $embedding
                    """,
                    message_id=message_id,
                    embedding=embedding,
                )
            logger.debug("Stored embedding for message %s", message_id)
        except Exception:
            logger.warning(
                "Failed to store embedding for message %s", message_id,
                exc_info=True,
            )

    def embed_and_store_chunks(self, chunk_ids: list[str], texts: list[str]) -> int:
        """Generate embeddings for document chunks and write them to Neo4j.

        Args:
            chunk_ids: List of DocumentChunk node IDs.
            texts: Corresponding chunk texts.

        Returns:
            Number of chunks successfully embedded.
        """
        if len(chunk_ids) != len(texts):
            raise ValueError("chunk_ids and texts must have the same length")

        embeddings = self.generate_embeddings_batch(texts)
        stored = 0

        for chunk_id, embedding in zip(chunk_ids, embeddings):
            if embedding is None:
                continue
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (c:DocumentChunk {id: $chunk_id})
                        SET c.embedding = $embedding
                        """,
                        chunk_id=chunk_id,
                        embedding=embedding,
                    )
                stored += 1
            except Exception:
                logger.warning(
                    "Failed to store embedding for chunk %s", chunk_id,
                    exc_info=True,
                )

        logger.info("Stored embeddings for %d/%d chunks", stored, len(chunk_ids))
        return stored

    def generate_query_embedding(self, query: str) -> list[float] | None:
        """Generate an embedding for a search query.

        Convenience wrapper that delegates to generate_embedding.

        Args:
            query: The search query text.

        Returns:
            A list of floats, or None if unavailable.
        """
        return self.generate_embedding(query)
