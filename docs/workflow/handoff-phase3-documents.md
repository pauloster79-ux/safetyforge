# Phase 3 Handoff: Document Pipeline

## What was just completed (Phase 1)

The entire backend has been migrated to the Kerf Ontology v3.0:
- `backend/graph/schema.cypher` — full rewrite, all ~73 entity types, vector index on `DocumentChunk.embedding` (1536 dims, cosine)
- `backend/app/services/document_service.py` — existing CRUD for Document nodes. Updated: `document_type` property renamed to `type`. `EnvironmentalProgram` absorbed into Document with `type: "environmental_compliance"`.
- 12 new service files created, 36 existing files updated. All Python files parse clean.

## What this phase builds

Upload documents, chunk them, embed them, link to the graph. This is the foundation for plan reading, spec extraction, COI parsing, and semantic search across all uploaded content.

## Key files to read first

- `backend/app/services/document_service.py` — existing Document CRUD. Stores `_content_json` on the node. Relationship: `(Company)-[:HAS_DOCUMENT]->(Document)` and `(Project)-[:HAS_DOCUMENT]->(Document)`.
- `backend/app/models/document.py` — Pydantic models for Document.
- `backend/graph/schema.cypher` — see the DocumentChunk constraints and vector index.

## Ontology reference (Document domain)

```
Document (prefix: doc)
  - id, title, type, status, file_url, file_type, ingestion_status, chunk_count + provenance
  - type: "safety_plan", "risk_assessment", "method_statement", "environmental_compliance", 
          "contract", "specification", "drawing", "insurance_certificate", "permit", "report"
  - status: "draft", "active", "archived", "superseded"
  - ingestion_status: "pending", "processing", "complete", "failed"

DocumentChunk (prefix: dchk)
  - id, text, page, position, chunk_index, embedding (vector 1536), created_at
  - NO provenance fields

Relationships:
  (Company)-[:HAS_DOCUMENT]->(Document)
  (Project)-[:HAS_DOCUMENT]->(Document)
  (DocumentChunk)-[:CHUNK_OF]->(Document)
  (DocumentChunk)-[:NEXT_CHUNK]->(DocumentChunk)
  (DocumentChunk)-[:MENTIONS {entity_type}]->(any entity)
```

## What to build

### 1. File upload endpoint

Add to the existing document router or create a new one:
- `POST /me/projects/:project_id/documents/upload` — accepts file upload (multipart/form-data)
- Store the raw file to local filesystem for now (create `backend/uploads/` directory). S3-compatible storage later.
- Create the Document node with `file_url` pointing to local path, `ingestion_status: "pending"`
- Return the document ID immediately — ingestion happens async.

### 2. Document ingestion service

Create `backend/app/services/document_ingestion_service.py`:

**Text extraction:**
- PDF: use `PyPDF2` or `pdfplumber` (check what's in requirements, add if needed)
- DOCX: use `python-docx`
- Plain text: read directly
- Images: skip for now (OCR is a later phase)

**Chunking:**
- Split extracted text into chunks of ~500 tokens with ~50 token overlap
- Each chunk becomes a `DocumentChunk` node
- Preserve reading order: `chunk_index` (integer), `page` number if available
- Create `CHUNK_OF` relationship to parent Document
- Create `NEXT_CHUNK` chain between sequential chunks

**Status tracking:**
- Set `Document.ingestion_status = "processing"` when starting
- Set `Document.ingestion_status = "complete"` and `Document.chunk_count = N` when done
- Set `Document.ingestion_status = "failed"` on error

### 3. Embedding generation for chunks

Reuse the embedding service from Phase 2 if it exists, or create `backend/app/services/embedding_service.py`:
- For each DocumentChunk, generate a 1536-dim embedding
- Write to `DocumentChunk.embedding` property
- The vector index `chunk_embeddings` is already defined in schema.cypher
- Process chunks in batches (not one API call per chunk)
- If no embedding API is configured, skip — chunks are still useful for text search

### 4. Entity extraction from chunks

After chunking and embedding, run an LLM pass over each chunk to extract entity mentions:
- Use FAST tier from LLMService
- Prompt: given this text chunk and a list of known entity types, identify which entities are mentioned
- For each mention, create `(DocumentChunk)-[:MENTIONS {entity_type: "Worker"}]->(entity)` if the entity can be matched by name/ID
- This is best-effort — not all mentions will resolve to existing entities

### 5. Hybrid search endpoint

Add a search endpoint:
- `POST /me/documents/search` — accepts a query string
- Generate embedding for the query
- Run hybrid search: vector similarity on DocumentChunk.embedding + optional graph traversal filters (project_id, document type)
- Return ranked results with: chunk text, source document title, page number, relevance score

Neo4j hybrid search pattern:
```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_embedding)
YIELD node AS chunk, score
MATCH (chunk)-[:CHUNK_OF]->(doc:Document)<-[:HAS_DOCUMENT]-(p:Project)<-[:OWNS_PROJECT]-(c:Company {id: $company_id})
WHERE doc.status = 'active'
RETURN chunk.text, doc.title, chunk.page, score
ORDER BY score DESC
```

### 6. COI (Certificate of Insurance) parsing

This is a specific document type that's high value:
- When a document with `type: "insurance_certificate"` is uploaded, run an LLM extraction pass
- Extract: carrier, policy_number, coverage_type, coverage_limit, effective_date, expiration_date, additional_insured
- Create or update an `InsuranceCertificate` node from the extracted data
- Link: `(Document)-[:SOURCE_OF]->(InsuranceCertificate)`

## Dependencies

- This phase is independent of Phase 2 (Conversation) and Phase 4 (Frontend)
- Uses the same embedding service concept as Phase 2 — if Phase 2 creates it first, reuse it
- If building the embedding service, make it a standalone module both phases can import

## Testing

1. Upload a test PDF → verify Document node created with `ingestion_status: "pending"`
2. Trigger ingestion → verify DocumentChunk nodes created with correct `chunk_index` order
3. Verify `CHUNK_OF` and `NEXT_CHUNK` relationships
4. Verify embeddings populated on chunks (if embedding API configured)
5. Run a search query → verify relevant chunks returned with scores
6. Upload a sample COI PDF → verify InsuranceCertificate node created with extracted fields
