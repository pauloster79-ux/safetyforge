# Handoff: Kerf Memory / Retrieval / Continuous Chat — Phases 1–2 Complete

**Date:** 2026-04-15
**From:** Phase 1 + Phase 2 session
**To:** Phase 3 (Continuous scope-tagged chat) session
**Plan file:** `C:\Users\paulo\.claude\plans\parallel-foraging-fog.md` (read first)

---

## The overall initiative

Make Kerf a **singular, persistent, continuous, scope-aware, learning** assistant.
Six phases, Phases 1 + 2 now done, Phases 3–6 pending.

1. ✅ **Phase 1** — Multi-user demo tokens + per-message provenance (model, tokens, cost, latency, actor_type, agent_id, agent_version)
2. ✅ **Phase 2** — Knowledge view (conversations / decisions / insights / trace) surfacing what the graph has recorded
3. ⏳ **Phase 3** — Continuous scope-tagged chat (one rolling conversation per user, scope tag = current project)
4. ⏳ **Phase 4** — Retrieval service — inject past Messages / Decisions / Insights / Preferences into the prompt
5. ⏳ **Phase 5** — Preference node + brain-chip save UX + Memory drawer (the learning loop)
6. ⏳ **Phase 6** — Skills/modes refactor — core.md + per-skill prompts + auto-detected skill chip

Phases are independent once the prior one lands. Phase 3 requires Phases 1–2 (needs multi-user seeds for testing and Knowledge view to verify scope tagging visually).

---

## What Phase 1 delivered

### Backend
- **`backend/app/dependencies.py`** — `DEMO_USERS` registry + `_resolve_demo_token()` helper mapping `demo-token-gp01`…`demo-token-gp10` to the 10 seeded golden owners. Plain `demo-token` still resolves to GP04 for back-compat.
- **`backend/app/routers/auth.py`** — new `GET /auth/demo-users` (404 outside dev/test). Data-drives the dev switcher.
- **`backend/app/services/message_service.py`** — `create()` accepts a `provenance: dict | None` kwarg; 9 whitelisted keys (`actor_type`, `agent_id`, `agent_version`, `model_id`, `input_tokens`, `output_tokens`, `cost_cents`, `latency_ms`, `confidence`) persisted as Message properties. Added `scope_project_id` plumbing (written from Phase 3).
- **`backend/app/services/chat_service.py`** — after each streamed turn, reads `stream.get_final_message().usage` + wall-clock latency; computes `cost_cents` using inline pricing helper `_calculate_cost_cents` (matches llm_service STANDARD tier). Stamps `agent_chat` / `1.0.0` on every assistant Message. Tool-result synthetic turns get `actor_type="agent"` so the trace view distinguishes them.
- **`backend/graph/schema.cypher`** — three new Message indexes (`scope_project_id`, `role`, `actor_type`).
- **`backend/fixtures/golden/validation-tests.cypher`** — 8 V-MSG-* structural queries (all currently PASS after one-time backfill).

### Frontend
- **`frontend/src/hooks/useAuth.ts`** — `DEMO_USERS` registry (mirrors backend), `DEFAULT_DEMO_ALIAS`, `switchDemoUser(alias)` helper. `getToken()` returns `demo-token-${alias}` reading `sessionStorage.kerf_demo_user`.
- **`frontend/src/hooks/useClerkAuth.ts`** — same alias-aware behaviour for the Clerk-enabled path.
- **`frontend/src/components/dev/DemoUserSwitcher.tsx`** — bottom-left floating chip, gated on `import.meta.env.DEV && isDemoMode`. Dropdown of all 10 users; switching reloads the page.
- **`frontend/src/components/shell/AppShell.tsx`** — mounts the switcher.

### Tests
- **`backend/tests/test_phase1_multi_user_and_provenance.py`** — 4 pure-function tests for `_resolve_demo_token` (verified PASS in isolation), 4 integration tests for provenance persistence (need live Neo4j via the existing autouse `cleanup_neo4j` fixture).

### One-time backfill (already run against the running graph)
502 legacy messages got `actor_type` set from `role` (143 tool-results→agent, 112 user→human, 247 assistant→agent). All V-MSG-* queries now PASS.

---

## What Phase 2 delivered

### Backend
**`backend/app/routers/knowledge.py`** (new) — five endpoints, all scoped via `Company.created_by = user_uid`:

| Endpoint | Returns |
|---|---|
| `GET /me/knowledge/conversations` | List with turn count, total cost, project link |
| `GET /me/knowledge/conversations/{id}/trace` | Full denormalised tree: messages + provenance + tool calls/results + REFERENCES + decisions + insights + roll-up totals |
| `GET /me/knowledge/decisions` | Cross-conversation decisions with source link |
| `GET /me/knowledge/insights` | Cross-conversation insights with source link |
| `GET /me/knowledge/entities/{type}/{id}/mentions` | Every Message REFERENCING the entity |

Single source of truth for tenant resolution is `_resolve_company_id` — change here when Phase 5 adds Member-level access.

**`backend/app/main.py`** — imports and wires `knowledge.router` (note: Phase 0 / audit work by a parallel session added `audit` router imports here too; leave those intact).

### Frontend
- **`frontend/src/lib/knowledge-api.ts`** (new) — typed `knowledgeApi` client (TS types match backend payloads).
- **`frontend/src/components/knowledge/KnowledgePage.tsx`** (new) — three tabs (Conversations / Decisions / Insights) with internal selection state for drilling into a trace.
- **`frontend/src/components/knowledge/ConversationTrace.tsx`** (new) — turn-by-turn trace with role icons (User / Assistant / Tool result), collapsible tool call JSON, REFERENCES chips, per-turn provenance row (`model · tokens · cost · latency · agent_id@version`), and extracted-decisions/insights footer.
- **`frontend/src/hooks/useShell.ts`** — added `'knowledge'` to `RailItem` union.
- **`frontend/src/components/shell/IconRail.tsx`** — Brain icon / `KnowledgePage` entry.
- **`frontend/src/components/shell/CanvasPane.tsx`** — registered `KnowledgePage` in `PAGE_COMPONENTS`.

### Critical bug fix (was silently breaking Phase 1)
**`frontend/src/lib/api.ts`** — `getAuthToken()` was hardcoding `'demo-token'` before the registered getter ran, so every React Query / fetch call went out as gp04 regardless of the switcher. Fixed to defer to the registered getter first. Without this fix, the first chat I sent as "gp07" ended up attributed to `demo_user_001` in Neo4j. That conversation was cleaned up; new chats attribute correctly.

---

## Live system state (as of handoff)

- **Neo4j:** Docker container `5sy-neo4j`, `bolt://localhost:7687`, creds `neo4j / fiveseasons2026` (from `backend/.env`).
- **Backend:** uvicorn with `--reload`, port 8000. **Gotcha:** Windows zombie python workers can linger after kill. If a new backend seems to have the right routes when imported (`from app.main import app; for r in app.routes: ...`) but the HTTP server returns 404, `powershell Get-Process python | Stop-Process -Force` on any process whose CommandLine mentions `multiprocessing.spawn`. Use `mcp__Claude_Preview__preview_start { "name": "backend" }` to (re)start via `.claude/launch.json`.
- **Frontend:** vite dev server, port 5173. Running via `mcp__Claude_Preview__preview_start { "name": "frontend" }`.
- **Clerk is NOT configured.** Dev uses the `demo-token-<alias>` bypass. To switch: bottom-left dropdown chip, OR `sessionStorage.setItem('kerf_demo_user','gp07'); sessionStorage.setItem('kerf_demo','true'); sessionStorage.setItem('kerf_company_id','comp_gp07'); location.reload()`.
- **Context:** one real gp03 conversation (`conv_a0dba2247df9b00c`) and one real gp07 conversation (`conv_587b71c1469a0a7c`) exist as demo data for the Knowledge view. Plus 500ish historical messages from prior sessions (all actor_type-backfilled).

---

## What's next — Phase 3 spec

Read `C:\Users\paulo\.claude\plans\parallel-foraging-fog.md` Phase 3 section for the full plan. Summary:

**Data-model change**
- Add `scope_project_id` (nullable) to `Message` schema — **already added to indexes in Phase 1**, just needs to be populated.
- Move from session-id-per-mount to **one rolling Conversation per user** (`conv_user_{uid}`). `_ensure_conversation` in `chat_service.py` becomes an upsert keyed on the user's uid, not the session.

**Backend**
- `POST /me/chat` accepts `scope_project_id` in the request body; writes it onto the Message node (not the Conversation).
- `GET /me/chat/history?before=<iso>&limit=50` — paginated backward scroll. Consumed by the chat pane on mount + infinite scroll.

**Frontend**
- `frontend/src/hooks/useChat.ts` — on mount, load last N messages via history endpoint; on scope change (read from `useShell()`), send `scope_project_id` with next message.
- `frontend/src/components/shell/ChatPane.tsx` — infinite-scroll backward, scope chip above input ("General" | "Project: Riverside Kitchen"), visual separator when scope changes mid-stream, chat **does not remount** when CanvasPane contents change.
- "New chat" button → "Jump to latest" / scope filter. Deletion moves to Knowledge view.

**Acceptance tests**
- Send message in general → open a project → send message → close project → send another message. All three appear in one continuous scroll with correct scope tags.
- Reload page mid-conversation; recent history + scroll position restored.
- Knowledge view filtering by project shows only that project's scope-tagged messages.
- Cross-tenant: switching demo user should show a **different** rolling conversation.

---

## Gotchas the new session should know about

1. **Don't revert parallel changes.** Another session added an AuditEvent schema + `audit_service.py` + `audit` router while I was working. Those are NOT part of this initiative — leave them alone.
2. **`getAuthToken` behaviour:** defer to the registered getter, never hardcode `demo-token`. Phase 1's regression here was real.
3. **Chat request body currently carries `company_id` from client sessionStorage** — Phase 3 must NOT trust this for tenant checks; the backend derives company from the user's uid via `_resolve_company_id`. Keep it that way.
4. **Windows zombie python processes:** netstat can show dead PIDs still LISTENING. Use `Get-NetTCPConnection -LocalPort 8000` in PowerShell for authoritative state.
5. **Neo4j password:** `fiveseasons2026`, not `password`. Test suite uses `password` via env vars — untouched.
6. **Frontend build has ~50 pre-existing TS errors** unrelated to this work (unused `useNavigate` imports, type mismatches in `demo-data.ts`). Ignore them; just verify your own files compile clean.
7. **Existing `/me/conversations` endpoint is still used** by other code; don't remove it when adding the new `/me/chat/history`. Parallel life.

---

## Verification checklist for end of Phase 3

- [ ] One rolling Conversation per user in Neo4j: `MATCH (c:Conversation) RETURN c.id, c.created_by, count{(m:Message)-[:PART_OF]->(c)} AS turns` — each user has exactly one row.
- [ ] `scope_project_id` is set on Messages sent while a project was open; null on Messages sent while the Canvas was closed.
- [ ] The V-MSG-08 validation query (scope_project_id belongs to same Company) returns 0 violations.
- [ ] Chat survives a page reload — history fetched via `/me/chat/history` renders + scroll position restored.
- [ ] Switching demo users (gp03 → gp07 via the dev switcher) shows a different chat stream.
- [ ] Knowledge view's conversation list shows one-per-user after migration.
