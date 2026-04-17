# Phase 2 Handoff: Conversation Infrastructure

## What was just completed (Phase 1)

The entire backend has been migrated to the Kerf Ontology v3.0:
- `backend/graph/schema.cypher` — full rewrite, all ~73 entity types, 2 vector indexes (Message.embedding, DocumentChunk.embedding)
- `backend/fixtures/golden/sample-data.cypher` — 3 realistic scenarios (Jake/Sarah/Dave) including a Conversation with Messages, Decision, and Insight
- 36 existing service files updated for entity renames and relationship changes
- 12 new service files created including `conversation_service.py` and `message_service.py`
- Guardrails fixed: human chat users now bypass agent guardrails
- All Python files parse clean, zero syntax errors

## What this phase builds

Persist every conversation and message to Neo4j. Enable conversation memory. The goal: every interaction recorded from day one, linked to the graph, searchable.

## Key files already created (read these first)

- `backend/app/services/conversation_service.py` — CRUD for Conversation nodes. Has: create, get, list_by_company, list_by_project, end_conversation. Relationships: `(Company)-[:HAS_CONVERSATION]->(Conversation)`, `(Conversation)-[:ABOUT_PROJECT]->(Project)`.
- `backend/app/services/message_service.py` — CRUD for Message nodes. Has: create, get, list_by_conversation, search_by_embedding. Relationships: `(Message)-[:PART_OF]->(Conversation)`, `(Message)-[:FOLLOWS]->(Message)`, `(Message)-[:SENT_BY]->(Member|AgentIdentity)`, `(Message)-[:REFERENCES]->(any entity)`.
- `backend/app/services/chat_service.py` — The existing streaming chat service. Uses in-memory `ChatSession` dict with 1h TTL. Streams via Anthropic SSE with tool-use loop (max 5 iterations). Two modes: `general` (10 tools including `query_graph`) and `inspection` (5 tools, state machine).
- `backend/app/services/llm_service.py` — Routes Anthropic API calls by model tier (fast/standard/advanced). Per-agent cost tracking with circuit breaker.

## What to build

### 1. Wire ChatService to persist conversations in Neo4j

The in-memory session stays (it handles streaming state for the Anthropic API). Add graph persistence alongside:

- On conversation start (new session_id): call `ConversationService.create()` to make a Conversation node. Store the `conversation_id` on the in-memory session.
- On each user message: call `MessageService.create()` with role="user", content, SENT_BY → Member.
- On each assistant response (after streaming completes): call `MessageService.create()` with role="assistant", content (full accumulated text), SENT_BY → AgentIdentity (or a system agent identity for the chat agent).
- On tool calls: optionally create Messages with role="system" containing tool call/result summaries.
- Link conversations to projects: when the chat context includes a `project_id`, create `ABOUT_PROJECT` relationship.

Key constraint: graph writes must NOT block the streaming response. Use fire-and-forget async writes or background tasks.

### 2. Embedding generation service

Create `backend/app/services/embedding_service.py`:
- Accepts text, generates a 1536-dim embedding vector
- Use OpenAI `text-embedding-3-small` or Anthropic's embedding endpoint (check what's available)
- Fallback: if no embedding API is configured, skip silently (embeddings are optional for MVP)
- After each Message is persisted, queue embedding generation. Write the vector to `Message.embedding`.
- Must be async / non-blocking.

### 3. Decision and Insight extraction

Create `backend/app/services/memory_extraction_service.py`:
- After a conversation turn completes, run a lightweight LLM pass (use FAST tier from LLMService) to check if any decisions or insights were expressed.
- A Decision is: something the user decided ("let's price it at $2400", "use OSHA 30 for this project"). Create a Decision node linked via `(Conversation)-[:PRODUCED_DECISION]->(Decision)` and `(Decision)-[:AFFECTS]->(entity)`.
- An Insight is: institutional knowledge expressed ("kitchen rewires average 16 hours", "I use 0.38 hours per receptacle in renovations"). Create an Insight node linked via `(Conversation)-[:EXPRESSED_KNOWLEDGE]->(Insight)`.
- This should run in the background, not blocking chat.
- Include a structured prompt that returns JSON: `{decisions: [{description, reasoning, affects_entity_type, affects_entity_id}], insights: [{content, applicability_tags}]}`.

### 4. Entity linking from tool calls

When the chat service executes a tool call (e.g., `check_worker_compliance(worker_id="wkr_123")`), create `REFERENCES` relationships from the Message to the entities mentioned:
- Parse tool call parameters for entity IDs
- Create `(Message)-[:REFERENCES {entity_type: "Worker"}]->(Worker {id: "wkr_123"})`

### 5. Conversation search endpoint

Add to the chat router or a new conversations router:
- `GET /me/conversations` — list conversations for company
- `GET /me/conversations/:id` — get conversation with messages
- `POST /me/conversations/search` — hybrid search: vector similarity on Message.embedding + graph traversal on relationships. Query: "what did we discuss about Project X?"

## Ontology reference (Conversation domain)

```
Conversation (prefix: conv)
  - id, mode (chat/voice), title, started_at, ended_at, transcript_url + provenance
  
Message (prefix: msg)  
  - id, role (user/assistant/system), content, timestamp, embedding (vector 1536)
  - NO provenance fields (immutable, author via SENT_BY)

Decision (prefix: dec)
  - id, description, reasoning, confidence, created_at

Insight (prefix: ins)
  - id, content, confidence, applicability_tags, created_at

Relationships:
  (Company)-[:HAS_CONVERSATION]->(Conversation)
  (Conversation)-[:ABOUT_PROJECT]->(Project)
  (Message)-[:PART_OF]->(Conversation)
  (Message)-[:FOLLOWS]->(Message)
  (Message)-[:SENT_BY]->(Member|AgentIdentity)
  (Message)-[:REFERENCES {entity_type}]->(any entity)
  (Conversation)-[:PRODUCED_DECISION]->(Decision)
  (Decision)-[:AFFECTS]->(any entity)
  (Conversation)-[:EXPRESSED_KNOWLEDGE]->(Insight)
```

## Testing

After building:
1. Send a chat message via the existing `/me/chat` endpoint
2. Verify a Conversation node and Message nodes appear in Neo4j
3. Verify FOLLOWS chain is correct (messages in order)
4. Verify SENT_BY relationships point to the right actor
5. Send a message referencing a project — verify ABOUT_PROJECT relationship
6. Check that embeddings are generated async (Message.embedding is populated)
7. Test the conversation search endpoint
