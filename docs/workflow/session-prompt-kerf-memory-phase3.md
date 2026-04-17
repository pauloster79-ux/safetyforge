# Session-start prompt — Kerf Memory initiative, Phase 3

Paste the following into a new Claude Code session. The handoff doc and plan
file are the two references you need — read both before touching any code.

---

```
I'm continuing a multi-phase initiative to make Kerf a singular, persistent,
continuous, scope-aware, learning assistant. Phases 1 and 2 are complete. You
are picking up at Phase 3 (continuous scope-tagged chat).

Before writing any code, read these two files in full:

  1. C:\Users\paulo\.claude\plans\parallel-foraging-fog.md
     The original six-phase plan. Phase 3 is the one to execute now.

  2. C:\Users\paulo\Documents\GitHub\safetyforge\docs\workflow\handoff-kerf-memory-phase2-complete.md
     What Phases 1 + 2 delivered, current live system state, gotchas, and the
     Phase 3 acceptance checklist.

Then pick up Phase 3.

Key context, in case the docs don't make it obvious:
  - Neo4j password is "fiveseasons2026" (from backend/.env), not "password".
  - Dev auth is demo-token-<alias> where alias is gp01..gp10. Switcher is the
    bottom-left chip in the frontend; or set sessionStorage.kerf_demo_user.
  - A parallel session has added an unrelated AuditEvent schema + audit router.
    Leave those alone — they aren't part of this initiative.
  - Existing /me/conversations endpoint is still used elsewhere; Phase 3 adds a
    new /me/chat/history endpoint rather than changing the old one.
  - Phase 3 makes the chat "one rolling Conversation per user" (conv_user_<uid>)
    with scope_project_id tagged on each Message. The Message property + index
    already exists from Phase 1; this phase writes to it.
  - `frontend/src/lib/api.ts::getAuthToken` MUST defer to the registered token
    getter — don't hardcode 'demo-token' (that's the Phase 1 regression I just
    fixed; don't reintroduce it).

When you begin, use EnterPlanMode to confirm your approach to the data-model
migration before writing code — the shift from "session-id-per-mount
Conversation" to "one rolling Conversation per user" is the biggest risk and
I'd like to sign off on the migration strategy (do existing conversations
get merged into the new rolling one, left as historical, or archived?).

Live stack:
  - Neo4j already running (docker "5sy-neo4j", port 7687)
  - Backend can be started via `mcp__Claude_Preview__preview_start { "name": "backend" }`
  - Frontend can be started via `mcp__Claude_Preview__preview_start { "name": "frontend" }`
  - Chrome MCP is available for live verification

At the end of Phase 3, run the checklist at the bottom of the handoff doc,
then write a new handoff for Phase 4.
```

---

**Tips for opening the new session:**

- Start fresh (not a `/resume`) so the 78%-full context from this session is discarded.
- First message should be the block above verbatim.
- Expect the new session to spend its first couple of turns reading the plan + handoff before touching code. That's intentional.
