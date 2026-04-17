# Session prompt — Layer 5 (Compliance during quoting)

Paste this into a new Claude Code session to pick up Layer 5 of the Kerf quote-process build.

---

You're picking up the Kerf build. Phase 0 foundations + layers 1-4 of the quote process are done. You're starting Layer 5 — safety & regulatory compliance surfaced during quoting. This is the moat — the thing no other construction tool does from a quote context.

**Read these first, in order:**

1. `CLAUDE.md` (project root) — the development process. No mocks. Persona-based testing is mandatory, not optional. Full-stack completion before declaring done.
2. `docs/workflow/handoff-layer5-compliance.md` — the full handoff. Decisions already made with Paul, what's in the codebase, what to build, critical files to read, open questions to flag.
3. `docs/PRODUCT_VISION.md` section 3.10 "Cross-Cutting: Safety and Compliance" and the opening beliefs block.
4. `~/.claude/projects/C--Users-paulo-Documents-GitHub-safetyforge/memory/feedback_exploratory_testing.md` — the testing ritual. This is how Paul expects you to validate your work. Do not regress to verify-mode.

**What you're building (from the handoff):**

- Structured `Activity` node type linking WorkItems to Regulations (not string tags — graph edges)
- Compliance check service that traverses WorkItem → Activity → Regulation → CertificationType → Worker
- Three severity tiers (Fatal/Required/Advisory) with Fatal blocking proposal generation
- MCP tools for compliance checking during quote
- UI: Compliance tab, banner on Contract tab, inline indicators on WorkItem rows, proposal section
- System prompt: Kerf proactively checks compliance on every WorkItem creation
- Multi-jurisdiction from day one (US/UK/CA/AU jurisdiction packs already exist)

**How Paul expects you to work:**

- Start with `EnterPlanMode` to investigate the existing compliance-adjacent code (`compliance_agent.py`, `mock_inspection_service.py`, existing `check_compliance` MCP tools), understand what to extend vs build new, and settle the open design questions the handoff flagged.
- Surface the design questions Paul needs to answer before you build (severity location, activity inference model, unmet-cert UI handling, whether clients see compliance gaps on the proposal). Don't assume — ask.
- Build in thin vertical slices. Don't build all the backend and then discover the UI needs a different shape.
- Verify in the browser as a persona, not via API. Marco in Austin quoting a 15ft trench on a hot July day.

**What's running:**

- Backend on port 8000 (`backend/app/main.py`)
- Frontend on port 5174 (5173 belongs to the 5seasons project, don't fight it)
- Neo4j on localhost:7687 (password: `fiveseasons2026`)
- Demo tokens `demo-token-gp01` through `demo-token-gp10`

**First concrete move:** enter plan mode, read the handoff, then read the files it points to, then report back to Paul with:

1. What exists you can extend vs what's truly new
2. Your answers to the open design questions (severity location, inference model, unmet-cert UI, proposal visibility)
3. Proposed build sequence and first-slice scope

Then wait for Paul to confirm before building.
