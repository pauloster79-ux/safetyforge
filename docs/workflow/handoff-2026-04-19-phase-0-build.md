# Handoff — Phase 0 Build (Foundations)

**Date:** 2026-04-19
**From:** Planning session that produced the full pre-implementation doc set (IA audit, micro-details ledger, data-model delta, vertical-slices plan, consolidated HTML)
**To:** Fresh Claude session executing the build
**Scope:** **Phase 0 — Foundations.** Four vertical slices: F1 Project shell · F2 MCP tool infrastructure · F3 Voice capture · F4 State machine migration. Plus a data-model verification step that runs first.

---

## TL;DR

1. **Read the 6 docs in `## 1. Read first` before writing anything.** They contain every decision already made.
2. **Do the data-model verification step FIRST** (`§ 3`). It's a 20–30-minute spelunk against current schema + service code. Confirms whether entities like `Contract`, `ChangeOrder`, `Quote`, `Labour.rate_source_id` already exist so you don't build duplicates.
3. **Four slices in Phase 0:** F1 (shell) · F2 (MCP dispatching) · F3 (voice) · F4 (state migration). F1 unblocks everything. F2/F3 can proceed in parallel once F1 is underway. F4 runs after verifications.
4. **Each slice has a fidelity gate before merge** — preview-vs-app diff · ledger checklist · voice-equivalent test · persona test · validation queries green.
5. **Per `CLAUDE.md`:** no mocks for internal services/APIs/DB. Full-stack completion means it works in the browser for a persona. Paul commits — you do not.
6. **Open the progress HTML** (`docs/preview/implementation-plan.html`) and cycle the status chips for F1–F4 as you work.

---

## 1. Read first (in this order)

Each is self-contained. Don't skip.

1. **`docs/preview/implementation-plan.html`** — opens in browser. The overview tab has the 8 phases, 51 slices, progress state, principle banner. Get the shape in your head first.
2. **`docs/design/project-lifecycle-flow.md`** — state machine, principle #15, 13 locked decisions. Governs every transition.
3. **`docs/design/project-screen-ia-audit.md`** — seven meta-tabs, feature map, quick-action cards with MCP tools, overlays, orphan check. The IA you're implementing.
4. **`docs/design/micro-details-ledger.md`** — 31 sections of fidelity rules. **This is the visual contract.** Especially §4 state chips, §10 chat pane (event markers with `◈` glyph, distinct `ChatEvent` component), §12 quick-action cards, §26 animations, §27 typography tokens, §28 colour semantics.
5. **`docs/implementation/data-model-delta.md`** — what's new or changing in the graph. §1 Project state, §14 indexes, §15 constraints, §16 validation queries. **§19 Verifications** is your first action — see below.
6. **`docs/implementation/vertical-slices.md`** — full per-slice detail (values, acceptance, MCP tools, preview anchors, fidelity references). Phase 0 slices are the ones you're executing.

Visual references (open alongside code):
- `docs/preview/project-screen-lifecycle.html` — canonical state appearances (6 frames)
- `docs/preview/project-screen-mockups.html` — structural Option C (the chosen tab layout)
- `frontend/src/index.css` — Site Board tokens and type scale

Governing CLAUDE.md rules (project root):
- **No mocks** for internal services, APIs, or DB. Tests hit real Neo4j or fail honestly.
- **Full-stack completion.** Each slice must be usable in the browser by a persona.
- **Persona-based exploratory testing** with rich golden data.
- **Don't commit.** Paul commits.

Governing memory feedback worth re-reading:
- `feedback_operator_controls_transitions.md` — Principle #15 in full force.
- `feedback_docs_in_html.md` — any docs you write are HTML in Site Board style (though *this* handoff is allowed in markdown).

---

## 2. What was done in the planning session (context)

So you don't wonder what already happened:

- **Full persona walkthrough** of Jake's kitchen remodel was done, locking 13 decisions about the state machine. Output in `project-lifecycle-flow.md`.
- **Option C chosen** for the Project-screen tab structure (7 meta-tabs, no sub-tabs, dashboard inside each). Rationale in `project-screen-ia-audit.md`.
- **Full HTML mockups** produced at two levels:
  - Lifecycle: 6 states of the same project (Maple Ridge Phase II · MRP-2024-118)
  - Quoting detail: 6 drill-down screens (quote overview → WorkItem inspector → labour → items → methodology → provenance tree)
- **Two Remotion compositions** built: `ProjectLifecycleFlow` (81s) and `QuotingDetailFlow` (48s). Run with `cd quoting-prototype && npm start`.
- **Four pre-implementation docs** produced and reviewed with Paul. IA audit 13 sections. Micro-details ledger 31 sections. Data-model delta 19 sections. Vertical-slices plan 7 phases × 51 slices.
- **Consolidated HTML plan** at `docs/preview/implementation-plan.html` with progress tracking (localStorage).
- **Phase restructure**: Paul flagged that I had Phase 1 as process-thin and the quoting-engine compressed into 1 slice. Restructured so Phase 1 = quote creation engine (16 slices, the actual Kerf substance) and Phase 2 = thin client handoff (5 slices).

You don't need to know more than this. Everything is in the docs.

---

## 3. Do this FIRST — data-model verification spelunk

Before writing any migration code, confirm what already exists in the graph. Spend 20–30 minutes on these checks so F4 (state migration) doesn't build duplicates.

Sources to read: `backend/graph/schema.cypher`, `backend/app/models/`, `backend/app/services/`, `backend/app/routers/`.

**For each item below, file a one-line finding in a new `docs/workflow/data-model-audit-2026-04-19.md`:**

1. Current `Project.state` enum values in schema — confirm `lead | quoted | active | completed | closed | lost`.
2. `Project.status` field — in use anywhere? Any production data carrying `on_hold` / `suspended` / `delayed`?
3. `Contract` entity (mentioned in `estimating-intelligence.md`) — exists? What shape? Should it become `ContractVersion` or remain distinct?
4. `ChangeOrder` / `Variation` — green-field, or exists under some name? Shape?
5. `Quote` entity — green-field, or exists? Versioning already?
6. `Labour.rate_source` / `rate_source_id` / `contractor_stated` — exist? Named what?
7. `Item.price_source` / `price_source_id` — exist? Named what?
8. `ProductivityRate` / `ResourceRate` — current shape? Relationships to Labour?
9. `Insight` node — does it have `applies_when` / `approach_match` properties?
10. `MaterialCatalogEntry` — exists? What's the "current price" property called?

**Deliverable:** `docs/workflow/data-model-audit-2026-04-19.md` — a 10-line report. For each item, one of:
- ✅ Exists as spec'd — no migration delta needed
- ⚠ Exists, named differently — update `data-model-delta.md` and migration scripts to match
- ❌ Green-field — build per spec in `data-model-delta.md`

Commit this report back to Paul before starting F1 (or do it first-thing during F1).

---

## 4. The four slices

### F1 · Project shell

**Goal:** Every existing project renders in the new dark Site Board shell with header + 7 meta-tabs + persistent agent panel. No new behaviour yet — just the new chrome wrapping existing data.

**Preview anchor:** `docs/preview/project-screen-lifecycle.html` — all six state frames share the same shell. `docs/preview/project-screen-mockups.html` Option C is the structural choice.

**Key fidelity refs (from `micro-details-ledger.md`):**
- §1 Layout shell (icon rail 48px, agent panel 300–320px)
- §2 Top header (logo tile, project code styling, chip placement, right cluster)
- §3 Tab bar (padding, active treatment, count badges)
- §4 State chips (six per-state colour treatments — critical)
- §27 Typography tokens — never inline `text-[10px]`; use `text-kicker`/`text-label`/etc
- §28 Colour semantics — use existing CSS tokens from `frontend/src/index.css`

**What to build:**
- New layout component wrapping the existing `ProjectPage` content
- Icon rail component (reuse from existing if matches; rebuild if not at spec)
- Top header with state-aware chip rendering
- Tab bar with the seven meta-tab names — content bodies may be empty placeholders in F1
- Agent panel as persistent left sidebar (reuse existing chat if possible)
- Responsive: mobile collapses rail → bottom nav, agent panel → FAB

**Acceptance (persona-based):**
- Open any existing project at any state → new shell renders with correct colour chip
- Click each tab → content area changes (even if content is a placeholder)
- Agent panel persistent on left (desktop) / FAB (mobile)
- No console errors; existing data renders through

**Fidelity gate:**
- Open `preview/project-screen-lifecycle.html` beside the live app. Sanity-diff each state's chip colour, header layout, tab bar.
- Every Site Board token referenced comes from `frontend/src/index.css` — no inlined colors/sizes.

**No commits.** Paul reviews, then commits.

---

### F2 · MCP tool infrastructure + chat-intent dispatching

**Goal:** Any UI card can dispatch a chat intent to the agent panel; the agent handles it via its normal path. Foundation for every subsequent quick-action card across every state.

**Pattern (from `project-screen-ia-audit.md §7`):**

A quick-action card is a labelled shortcut over a chat message. When tapped:
1. UI dispatches `dispatchChatIntent(intent: string)` — e.g. `"mark this lead as lost"`
2. Agent panel receives the intent as if Sarah typed it
3. Agent responds through its normal MCP tool path (tool pick + prompt + handling)
4. Any state changes flow through existing state-change tools

**What to build:**
- `dispatchChatIntent(intent)` function on the chat panel — injects the message into the chat as if typed
- Card component that takes `{label, icon, subtext, intentPhrase, voicePhrase}` and renders a Site Board card that dispatches on tap
- Voice-equivalent phrases stored alongside the card (so voice tests can assert parity)

**Acceptance:**
- Tap a test card ("test intent") → appears in chat panel → agent responds
- Same card's voice equivalent (spoken via F3 voice) produces same agent response
- No new MCP tools needed at this slice — F2 is the pipe, not the tools themselves

**Fidelity gate:**
- `micro-details-ledger.md §12` quick-action card styling (grid, icon, label, sub, hover)
- Voice-equivalent phrase stored + testable

**Dependency:** F1.

---

### F3 · Voice capture session handling

**Goal:** Hold-to-speak works end-to-end from the agent panel input bar. Captures audio, transcribes, submits as chat message.

**Preview anchor:** `project-screen-lifecycle.html` — bottom of agent panel shows the input row with `◉ HOLD` + `SEND`.

**What to build:**
- Press-and-hold on the HOLD button captures audio (Web Audio API).
- On release, audio submits to transcription service (existing infrastructure — verify).
- Transcribed text inserts into chat as if typed.
- Offline-first: if network is down, queue locally and flush on reconnect.
- On mobile: the FAB is the primary voice button.

**Acceptance:**
- Desktop: press-and-hold HOLD → spoken text appears in chat → agent responds.
- Mobile: FAB press-and-hold does the same.
- Airplane mode mid-capture: message queues locally; enabling network pushes it through and agent responds.

**Fidelity gate:**
- `micro-details-ledger.md §10.6` chat input styling
- Voice equivalent parity maintained — anything tap-doable must be voice-doable through F3 plus F2

**Dependency:** F1. Can run in parallel with F2.

---

### F4 · Project state machine migration

**Goal:** Graph schema has the new `Project.state` enum (`LEAD | QUOTED | ACCEPTED | ACTIVE | PRACTICAL_COMPLETION | CLOSED`) + `closed_reason` + `state_at_closure`. Existing projects migrated. Validation queries green.

**Spec:** `data-model-delta.md §1`.

**Prerequisite:** the data-model audit (§3 above). You need to know what's there before you migrate.

**What to build:**
- Append constraints + indexes to `backend/graph/schema.cypher` (§1.2 of delta).
- Migration Cypher — idempotent — (§1.3 of delta). Don't hardcode paths; make it a script that can run against dev, staging, production.
- Add validation queries to `backend/fixtures/golden/validation-tests.cypher` (§16 of delta).
- Update service code that writes `Project.state` to the new enum values.
- Remove `Project.status` writes; on migration, existing `on_hold` / `suspended` rows migrate to PauseRecord entities (spec in delta §6.1 — PauseRecord entity is not a Phase 0 deliverable, but the migration cleanup is; just the legacy-status rows get their overlay record created now).

**Acceptance:**
- All existing projects display the correct new-enum state chip in the header (F1 depends on this being live).
- Validation queries from delta §16 all pass against migrated data.
- No existing functionality breaks (tests green).

**Fidelity gate:**
- `micro-details-ledger.md §4` state chip colour matrix — verify each state's chip renders correctly after migration.
- Validation queries in CI pipeline (or equivalent).

**Dependency:** data-model audit. Runs in parallel with F2/F3 once F1 is underway.

---

## 5. Sequencing within Phase 0

Suggested order:

1. **Day 1 morning:** Data-model audit (§3 above). Commit report.
2. **Day 1 afternoon onward:** F1 (Project shell) kicks off.
3. **Once F1 has at least the shell structure in place:** F2 and F3 can start in parallel — they're orthogonal.
4. **Once F1 is close to done and audit is clear:** F4 (state migration) runs. F1's state chip rendering will immediately start using the correct new enum values.
5. **Phase 0 closes** when all four slice acceptance criteria are met and fidelity gates pass.

---

## 6. Rules you must not violate

1. **No mocks for internal services, APIs, or DB.** Tests hit real backend.
2. **Full-stack completion** — if it doesn't work in the browser for a persona, it's not done.
3. **Every tap affordance has a voice equivalent.** Per `project-screen-ia-audit.md §7`. Missing voice = incomplete fidelity.
4. **Principle #15** — operator controls transitions. No auto-flips based on inferred facts or silence.
5. **Don't commit.** Paul commits.
6. **Update the HTML plan** (`docs/preview/implementation-plan.html`) — cycle the status chip for each slice as you work (Not started → In progress → In review → Shipped). Each chip is a click. Progress persists in browser localStorage.
7. **If you notice fidelity details not in the micro-details ledger, add them.** Extend the ledger. That's what "living document" means.
8. **If a slice's preview anchor doesn't exist yet (GAP in the plan), don't just build by imagination.** Stop and request a design-pass sub-slice. Paul would rather you ask than invent.

---

## 7. What "done" looks like at end of Phase 0

- Existing projects open with the new dark Site Board shell: header with state chip + meta-tabs + agent panel.
- State chips render correctly for every project at every state (migrated or fresh).
- Tapping a quick-action card dispatches a chat intent (the infrastructure; specific tools come in Phase 1 slices).
- Holding the voice button captures audio and submits to chat end-to-end; offline-first works.
- Validation queries in CI pass on all environments.
- `data-model-audit-2026-04-19.md` is written and filed.
- All four F slices marked Shipped on `implementation-plan.html`.

Ready to hand back to Paul for Phase 1 kickoff.

---

## 8. Suggested opening prompt for the fresh session

> "I'm executing Phase 0 of the Kerf implementation plan. The full doc set is at `docs/implementation/` and `docs/design/`; the consolidated plan HTML is at `docs/preview/implementation-plan.html`. Read the six docs in §1 of `docs/workflow/handoff-2026-04-19-phase-0-build.md` first. Then do the data-model audit in §3. Then F1 (Project shell). Paul is available for questions but not commits. I don't commit — Paul commits."

---

## 9. Repo state on handoff

- Modified / new files across `docs/design/`, `docs/implementation/`, `docs/preview/`, `docs/workflow/`, `quoting-prototype/src/`, memory.
- **Nothing committed** per `CLAUDE.md` rule.
- Run `git status` to see the current diff before starting.

---

*End of handoff.*
