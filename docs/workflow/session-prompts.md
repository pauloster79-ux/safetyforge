# Parallel Session Prompts

Copy each prompt into a separate Claude Code session. All three can run simultaneously — they work on independent areas (backend conversation, backend documents, frontend).

---

## Session A: Conversation Infrastructure

```
Read docs/workflow/handoff-phase2-conversation.md — this is your handoff from Phase 1.

Phase 1 just completed: the entire backend was migrated to the Kerf Ontology v3.0. All ~73 entities, 54 service files, new schema.cypher. Everything compiles clean.

Your job is Phase 2: wire conversation persistence into the chat service so every interaction is recorded in Neo4j. Build the embedding service, decision/insight extraction, entity linking, and conversation search.

Start by reading the handoff doc, then read these files to understand what exists:
- backend/app/services/conversation_service.py (new, from Phase 1)
- backend/app/services/message_service.py (new, from Phase 1)
- backend/app/services/chat_service.py (existing streaming chat)
- backend/app/services/llm_service.py (model routing + cost tracking)

Then build everything described in the handoff. Use maximum effort. Test by verifying Neo4j nodes are created when chat messages are sent.
```

---

## Session B: Document Pipeline

```
Read docs/workflow/handoff-phase3-documents.md — this is your handoff from Phase 1.

Phase 1 just completed: the entire backend was migrated to the Kerf Ontology v3.0. All ~73 entities, 54 service files, new schema.cypher with a vector index on DocumentChunk.embedding. Everything compiles clean.

Your job is Phase 3: build the document upload, ingestion (PDF/DOCX text extraction + chunking), embedding generation, entity extraction, and hybrid search pipeline.

Start by reading the handoff doc, then read these files to understand what exists:
- backend/app/services/document_service.py (existing CRUD, updated in Phase 1)
- backend/app/models/document.py (updated models)
- backend/graph/schema.cypher (see DocumentChunk constraints + vector index)

Then build everything described in the handoff. Use maximum effort. Test by uploading a PDF and verifying DocumentChunk nodes appear in Neo4j.
```

---

## Session C: Frontend Shell

```
Read docs/workflow/handoff-phase4-frontend.md — this is your handoff from Phase 1.

Phase 1 just completed on the backend. The frontend was not touched. Your job is Phase 4: build a new frontend shell purpose-built for conversational-first interaction.

The current frontend has chat as a sidebar overlay. You are rebuilding the app shell so chat is the PRIMARY pane, with existing pages becoming canvas detail views in a split layout.

Start by reading the handoff doc, then read these files to understand the current state:
- frontend/src/components/layout/AppLayout.tsx (current shell — being replaced)
- frontend/src/components/chat/ChatPanel.tsx (current chat overlay — logic being promoted)
- frontend/src/hooks/useChat.ts (streaming state machine — reuse exactly)
- frontend/src/components/voice-inspection/VoiceInspectionPage.tsx (the conversational-first template)
- frontend/src/App.tsx (current routing)
- frontend/src/index.css (design tokens)

Then build everything described in the handoff. Use maximum effort. Do NOT touch any backend files. Reuse all existing hooks, ui primitives, and data layer.
```
