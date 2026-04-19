# Vertical Slices — Implementation Plan

**Status:** Pre-implementation artifact. Orders the work into end-to-end deliverable slices.
**Date:** 2026-04-19
**Purpose:** Each slice delivers a working persona journey in the browser. No backend-first-frontend-later. No big-bang release. Preview-driven fidelity throughout.
**Depends on:** [project-screen-ia-audit.md](../design/project-screen-ia-audit.md) · [micro-details-ledger.md](../design/micro-details-ledger.md) · [data-model-delta.md](data-model-delta.md) · [project-lifecycle-flow.md](../design/project-lifecycle-flow.md)

---

## 0. Slicing Principles

1. **Every slice ships to a persona.** Closing a slice means: Jake, Sarah, or Marco can do the thing end-to-end in the browser.
2. **Every slice is preview-linked.** Its tickets cite regions of `docs/preview/*.html` or timecodes of `quoting-prototype/src/scenes/*.tsx` as the source-of-truth visuals.
3. **Every slice is small.** Target 3–7 days. Longer means re-slice.
4. **Every slice has a fidelity pass.** Before merge, preview-vs-app side-by-side diff against the micro-details ledger.
5. **Every slice can be rolled back.** Feature flag on backend writes + explicit migration rollback scripts where data shape changes.
6. **No slice fakes data.** Per `CLAUDE.md`, no mocks for internal services. Slice calls real backend or doesn't ship.

---

## 1. Phase Overview

Seven phases, ~30 slices. Each phase ends with a reviewable milestone Paul can use in demos.

| Phase | Theme | Slice count | Milestone |
|---|---|---|---|
| **0** | Foundations | 3 | Project shell live with dark Site Board chrome and a persistent agent panel. Existing data flows through. |
| **1** | Lifecycle through quote | 5 | Sarah captures scope for a new lead, sends a quote, issues a revision, client accepts via magic link. |
| **2** | Contract through active | 3 | Accepted state snapshots a ContractVersion; deposit invoice drafts; first time entry flips to ACTIVE. |
| **3** | Execution intelligence | 7 | Mid-job on ACTIVE: variations draft from chat, WorkItem inspector opens with full provenance drill, methodology cascade visible. |
| **4** | Site operations | 6 | Site meta-tab lit up. Site walk voice-captures safety + quality + crew + equipment simultaneously. |
| **5** | Money + Contract | 4 | Money meta-tab handles invoicing lifecycle. Contract meta-tab handles assumptions/exclusions/disputes. |
| **6** | Close and beyond | 4 | PC declaration + final invoice + closure with typed reason + revive flow. |
| **7** | Overlays and edges | 4 | PAUSED typed overlay, DLP, Retention, Dispute UI fully integrated. |

Total: **33 slices**. Seriatim, this is roughly 5–6 months. Parallelisable on multiple tracks — but slice dependencies below govern ordering.

---

## 2. Slice-Level Detail

Each entry below specifies: **ID · Name · Value delivered · Data model · MCP tools · UI · Fidelity · Persona acceptance · Dependencies**.

---

### Phase 0 — Foundations

#### A1 · Project shell

**Value:** Contractor opens any existing project; sees the new dark Site Board Project screen with header, meta-tabs, and persistent agent panel. Existing data (WorkItems, contacts) renders through the new chrome.

**Data model:** No changes. Pure UI re-wrap over existing services.

**MCP tools:** None new. Chat already exists.

**UI:** `preview/project-screen-lifecycle.html` — shell visible in all six state frames. `preview/project-screen-mockups.html` — Option C structure.

**Fidelity:** `micro-details-ledger.md §1–5` (layout shell, top header, tab bar, state chips, overlays).

**Persona acceptance:**
- Sarah opens Maple Ridge Phase II → sees the new shell in full dark Site Board style.
- Tab click → content changes (even if empty/placeholder).
- Agent panel conversation is persistent on the left (desktop) or FAB (mobile).

**Dependencies:** none (foundational).

---

#### A2 · MCP tool infrastructure + chat-intent dispatching

**Value:** The quick-action cards specified in the IA audit §7 work as chat shortcuts. Tapping a card sends the intent to the agent panel; agent responds; action executes through existing MCP path.

**Data model:** None new. Extends existing MCP tool registry.

**MCP tools:** Infrastructure — not new tools, but the pipe that lets UI cards dispatch chat intents. One-line Dashboard config per card.

**UI:** `preview/project-screen-lifecycle.html` — every quick-action card at the bottom of the state dashboards.

**Fidelity:** `micro-details-ledger.md §12` (quick-action cards).

**Persona acceptance:**
- Tapping `Mark Lost` on a lead is equivalent to Sarah typing "mark this lead as lost" — same agent response, same execution path.
- Every card in the audit (§7) has a voice equivalent phrase implemented and testable.

**Dependencies:** A1.

---

#### A3 · Voice capture session handling

**Value:** The agent panel's hold-to-speak works end-to-end: capture → transcribe → agent response. Works offline (queues locally). Works on mobile with the FAB.

**Data model:** `VoiceSession` entity already exists per Kerf's current architecture (or add minimal shape if not).

**MCP tools:** `start_voice_session`, `end_voice_session` wired to the hold button.

**UI:** `preview/project-screen-lifecycle.html` — agent panel input bar with HOLD + SEND.

**Fidelity:** `micro-details-ledger.md §10.6` (chat input).

**Persona acceptance:**
- Sarah presses-and-holds HOLD from the truck. Releases. Transcribed text appears in chat. Agent responds.
- Offline: capture queues. On reconnect: syncs. No data loss.

**Dependencies:** A1.

---

### Phase 1 — Lifecycle through quote

#### B1 · Project state machine migration

**Value:** Enables everything downstream — the new state enum is in place, closed_reason + state_at_closure work, existing projects migrated cleanly.

**Data model:** `data-model-delta.md §1`. Project state migration Cypher. Index + constraint adds.

**MCP tools:** None new. Existing state-change tools updated to new enum values.

**UI:** Header state chip now shows correct per-state colour (per `micro-details-ledger.md §4`).

**Fidelity:** `micro-details-ledger.md §4` (state chips colour matrix).

**Persona acceptance:**
- All existing projects display with correct new-enum state chip in header.
- Transitions between states happen correctly from the existing UI paths.
- Validation queries (`data-model-delta.md §16`) all pass on migrated data.

**Dependencies:** A1.

---

#### B2 · LEAD state Dashboard

**Value:** New lead comes in. Dashboard lands on "Next action" + Peachtree reference + Client card + 4 quick-action cards. The thing Jake opens when he takes a call.

**Data model:** No new entities. Uses existing Project, Contact, and prior-project-reference.

**MCP tools:** `schedule_project_event`, `start_voice_scope_capture`, `draft_client_email`, `mark_project_closed` (with reason: `lead_lost`).

**UI:** `preview/project-screen-lifecycle.html` — State 1 LEAD frame.

**Fidelity:** `micro-details-ledger.md §6 (metric tiles), §12 (quick-action cards), §7 (section cards)`. LEAD-state specific: next-action yellow card, "⚑ From Peachtree" reference card.

**Persona acceptance:**
- Jake opens Kerf, taps New Project, says "Kate called about a kitchen remodel on Oak Street" → Project created in LEAD with Client + next-action captured.
- Kerf finds Peachtree (if past similar project exists) and renders the reference card.
- Tapping `Schedule visit` opens the chat-intent flow → Calendar event created.

**Dependencies:** A1, A2, B1.

---

#### B3 · Quote entity + QUOTED Dashboard (quote document)

**Value:** Sarah finishes scope capture. Dashboard reshapes to the seven-section quote document (Claude Design's screenshot). Source tags visible on every WorkItem.

**Data model:** `data-model-delta.md §8` (Quote entity + versioning). `§10` (source provenance on Labour, Item).

**MCP tools:** `generate_proposal_document`, `send_quote_to_client`, `propose_margin_adjustment`, `withdraw_quote`, `compare_to_past_job`.

**UI:** `preview/project-screen-lifecycle.html` — State 2 QUOTED frame. Plus `preview/quoting-detail-mockups.html` — Screen 1 (quote overview with source tags).

**Fidelity:** `micro-details-ledger.md §8 (WorkItem table + sub-chip tags), §18 (source tags), §7.2 (section glyphs)`. The seven numbered sections layout matches Claude Design exactly.

**Persona acceptance:**
- Sarah finishes scope capture → Dashboard reshapes to the quote document view.
- Every WorkItem row shows its source tag (Catalog / Past · Nx / Insight / Stated).
- Margin column is green; Sell column is yellow.
- "⚑ +15% insight" sub-chip renders on affected rows.

**Dependencies:** B2.

---

#### B4 · Magic-link client view (public surface)

**Value:** Kate gets an email with a link. She clicks it. She sees the quote in the client-facing view. She can accept, decline, ask a question, or leave it.

**Data model:** `data-model-delta.md §12` (MagicLink entity). Scope: `view_quote`, `accept_quote`.

**MCP tools:** `issue_magic_link`, `validate_magic_link`. Public-facing endpoint for client responses.

**UI:** **New preview required.** Not covered in existing mockups — design pass before build. Based on the Quote document from §B3 rendered in a client-friendly layout (lighter theme option, or same dark with simplified chrome).

**Fidelity:** Matches QUOTED document spec + new client-portal chrome rules (to be specified in a client-portal micro-details ledger addition).

**Persona acceptance:**
- Sarah sends quote → Kate receives email → Kate clicks link → sees full proposal.
- Accept button works: triggers B6 state transition.
- Decline / question route back to the agent panel on Sarah's side.
- Single-use tokens: once accepted, the link is expended.

**Dependencies:** B3.

---

#### B5 · Quote revision flow (v2 supersedes v1)

**Value:** Kate replies with "can we see this without the pantry outlet?" — agent drafts V2, Sarah reviews, issues V2, V1 marked superseded but retained. Email reply flow handles the inbound.

**Data model:** Quote entity already has versioning (B3). No schema change, just correct SUPERSEDES relationship wiring. `data-model-delta.md §11` (email tracking).

**MCP tools:** `draft_quote_revision`, `issue_quote_revision`. Email inbound: `handle_client_email_reply`.

**UI:** Agent panel chat events showing inbound email + quote revision drafted inline (uses event-pill pattern from `micro-details-ledger.md §10.4`).

**Fidelity:** §10.4 event markers (dashed border, `◈` glyph). §8.1 sub-chips indicating superseded.

**Persona acceptance:**
- Kate emails reply → event appears in Sarah's agent panel with `◈` glyph, distinct from messages.
- Sarah taps the draft-variation suggestion → V2 drafts.
- V2 sent → V1 SUPERSEDES in graph. Client view shows V2 only.
- History navigation lets Sarah view V1.

**Dependencies:** B3, B4.

---

### Phase 2 — Contract through active

#### B6 · ACCEPTED transition + ContractVersion snapshot

**Value:** Kate accepts → ContractVersion v1 is immutably snapshotted. Scope is now variation-only. Dashboard reshapes to the pre-start checklist.

**Data model:** `data-model-delta.md §2` (ContractVersion entity). Variation becomes the only scope-change path from here.

**MCP tools:** `accept_quote`, `snapshot_contract_version`. State transition QUOTED → ACCEPTED.

**UI:** `preview/project-screen-lifecycle.html` — State 3 ACCEPTED frame.

**Fidelity:** `micro-details-ledger.md §21` (contract-reference strip at top of ACCEPTED). §6 metric tiles (4 primary) — Planned start, Deposit, Duration, Crew.

**Persona acceptance:**
- Kate clicks Accept → ContractVersion v1 locks with sum, doc_hash, parties, dates, terms, jurisdiction.
- Project state flips ACCEPTED. Chip pulses (per §26 animation).
- Dashboard reshapes to pre-start view.

**Dependencies:** B4, B5.

---

#### B7 · Deposit invoice + pre-start checklist

**Value:** Dashboard shows the "Before we start" checklist. Deposit invoice drafts automatically; Sarah approves + sends; Kate pays; Kerf logs.

**Data model:** Invoice entity (may exist; confirm in verification step). New state transitions on invoice.

**MCP tools:** `send_invoice` (type: deposit), `record_invoice_payment`, `submit_permit_application`, `create_material_order`, `update_project_date`.

**UI:** `preview/project-screen-lifecycle.html` — State 3 ACCEPTED frame (checklist rows).

**Fidelity:** `micro-details-ledger.md §7.2` (section glyphs), checklist row pattern from the preview.

**Persona acceptance:**
- On ACCEPTED, Kerf drafts deposit invoice + permit application + material order.
- Sarah taps `Nudge Gary` → email reminder sent.
- Kate pays → payment recorded → checklist row flips to Paid chip.

**Dependencies:** B6.

---

#### B8 · First time entry → ACTIVE; "Needs your call" panel

**Value:** Sarah clocks in → ACCEPTED flips to ACTIVE. Dashboard reshapes to execution view. Any urgent issues surface in the "Needs your call" panel.

**Data model:** Time entry entity exists (Domain 17). Trigger state transition on first entry per `project-lifecycle-flow.md §2.3`.

**MCP tools:** `log_time_entry`, `transition_to_active`.

**UI:** `preview/project-screen-lifecycle.html` — State 4 ACTIVE frame. The "⚡ Needs your call" panel is the signature element.

**Fidelity:** `micro-details-ledger.md §13` (Needs your call panel — machine-yellow border, 3px left-border on cards, urgency colour coding).

**Persona acceptance:**
- Sarah logs first time entry → Project flips ACTIVE (chip colour change + pulse).
- Dashboard reshapes. "Needs your call" panel appears if any items are urgent (initially empty or pulls from existing flags).

**Dependencies:** B6, B7.

---

### Phase 3 — Execution intelligence

#### B9 · Variation entity + lifecycle (Draft → Issued → Approved)

**Value:** Mid-job, Kerf detects a variation-worthy scope change (from chat or daily log) and drafts a Variation. Sarah reviews, issues, Kate approves via magic link.

**Data model:** `data-model-delta.md §3` (Variation entity). Critical.

**MCP tools:** `draft_variation_from_chat`, `draft_variation_from_daily_log`, `issue_variation`, `approve_variation` (via magic link), `reject_variation`, `revise_variation`.

**UI:** `preview/project-screen-lifecycle.html` — State 4 ACTIVE frame shows V1 in Draft in the "Needs your call" panel.

**Fidelity:** `micro-details-ledger.md §13` (Needs-your-call card for V1), §14 (insight card if variation carries one).

**Persona acceptance:**
- Sarah says in chat "there are 4 extra slab cores needed" → Kerf drafts V1.
- Draft V1 surfaces in "Needs your call".
- Sarah taps Review & issue → email sent to Kate with magic-link approval.
- Kate approves → V1 Approved immutable. Effective sum recomputes. Event logged.

**Dependencies:** B8.

---

#### C1 · WorkItem inspector — split canvas

**Value:** Click any WorkItem row → inspector panel slides in from the right with labour, items, insight card, methodology summary, sources. Main list dims but stays visible.

**Data model:** No new entities. Uses existing WorkItem + Labour + Item + Methodology.

**MCP tools:** `get_workitem_detail` (extended to include provenance).

**UI:** `preview/quoting-detail-mockups.html` — Screen 2 (WorkItem inspector open).

**Fidelity:** `micro-details-ledger.md §11` (inspector slide-in rules, sticky header, dim-main-list). §14 (insight card).

**Persona acceptance:**
- Sarah clicks WI 04 → inspector slides in.
- Summary tiles visible. Insight card visible if insight applied. Labour table visible. Items table visible. Methodology summary at bottom.
- Clicking another row swaps inspector content; list doesn't re-mount.

**Dependencies:** A1.

---

#### C2 · Labour line detail + lineage equation

**Value:** Sarah clicks a labour line → lineage equation renders: `12 × 1.33 + 15% = 18.4`. Base productivity sample (3 jobs) shown. Rate source explained.

**Data model:** `data-model-delta.md §10` (Labour source provenance fields).

**MCP tools:** `get_labour_detail_with_provenance`, `override_labour_rate`.

**UI:** `preview/quoting-detail-mockups.html` — Screen 3 (labour detail).

**Fidelity:** `micro-details-ledger.md §16` (lineage equation node variants — default/base/insight/final).

**Persona acceptance:**
- Click a labour line → lineage equation visible with correct node colouring.
- 3-job sample cards show past-job evidence.
- Override button works (creates a stated override).

**Dependencies:** C1.

---

#### C3 · Item line detail + price history

**Value:** Sarah clicks an item line → price history renders. Supplier, last PO price, alternatives considered and rejected.

**Data model:** No new entities. Extends existing MaterialCatalogEntry + PurchaseOrder history queries.

**MCP tools:** `get_item_price_history`, `view_alternatives`.

**UI:** `preview/quoting-detail-mockups.html` — Screen 4 (item detail).

**Fidelity:** `micro-details-ledger.md §8` (tables), §18 (source tags on the PO rows).

**Persona acceptance:**
- Click an item → price history column visible: today's catalog, past POs, trend.
- Rejected alternatives (Legrand 1-gang, Wiremold 880CM) show with rejection reason.

**Dependencies:** C1.

---

#### C4 · Methodology cascade UI

**Value:** Sarah clicks "Methodology" in the WorkItem inspector → cascade view shows Project / Package / Item with override highlighting. Effective map at the bottom.

**Data model:** Methodology entity exists per prior handoff (schema ready). This slice implements the resolution query + UI.

**MCP tools:** `resolve_methodology_cascade` — returns the project/package/item methodology + the merged effective map.

**UI:** `preview/quoting-detail-mockups.html` — Screen 5 (methodology cascade).

**Fidelity:** `micro-details-ledger.md §15` (cascade — level colours, override pills, effective map block).

**Persona acceptance:**
- Click Methodology → cascade visible with three levels.
- Override keys highlighted in machine-yellow.
- Effective map shows merged state with origin column (proj/pkg/item).
- "Why methodology matters" explainer visible.

**Dependencies:** C1. Also depends on the methodology service from the 2026-04-17 handoff (if not yet built, that's a sub-slice — see Verification).

---

#### C5 · Source provenance tree drill + confidence meters

**Value:** Sarah asks "full provenance of $9,800" → agent renders the full tree. Every number traces to catalog / past / insight / stated.

**Data model:** No new entities. Extended traversal query.

**MCP tools:** `get_full_provenance_tree`.

**UI:** `preview/quoting-detail-mockups.html` — Screen 6 (provenance tree + confidence distribution).

**Fidelity:** `micro-details-ledger.md §17` (provenance tree), §19 (confidence meters).

**Persona acceptance:**
- Sarah asks in chat "where did $9,800 come from?" → provenance tree renders.
- Every branch carries its source tag.
- Confidence meters at bottom show per-dimension (labour / items / adjustment / overall) with correct colour bands.

**Dependencies:** C1, C2, C3.

---

#### C6 · Source tags everywhere

**Value:** Source tags render consistently on every WorkItem, every labour line, every item line, everywhere a number exists.

**Data model:** Completes the `data-model-delta.md §10` wiring.

**MCP tools:** Existing tools updated to always return source tag info.

**UI:** Applies to all surfaces.

**Fidelity:** `micro-details-ledger.md §18` (source tags canonical variants).

**Persona acceptance:**
- No number on any screen displays without its source tag.
- Tag colours match the canonical variants.

**Dependencies:** B3, C1, C2, C3 (cumulative).

---

### Phase 4 — Site operations

#### D1 · Site meta-tab shell

**Value:** Click Site tab → meta-tab dashboard loads showing state-aware "what's happening on the jobsite" summary. Drills to specific entity views on click.

**Data model:** No new entities. Uses existing Inspection, Worker, Equipment entities scoped to this project.

**MCP tools:** `get_site_dashboard_state_aware` — returns per-state summary.

**UI:** Needs new preview. Design pass based on IA audit §6.3.

**Fidelity:** `micro-details-ledger.md` cross-cutting rules apply. Specific Site dashboard details go in a Site addition to the ledger.

**Persona acceptance:**
- Marco taps Site on his Maple Ridge project → sees today's toolbox talk status + open hazards + crew on site + equipment list.

**Dependencies:** A1, B1.

---

#### D2 · Safety dashboard within Site

**Value:** Site → Safety drill shows this project's inspections, open hazards, CAs, incidents, toolbox talks. Same engine as global Inspections, scoped.

**Data model:** No new entities. Filtered views of existing.

**MCP tools:** Existing Inspection tools — filter by project.

**UI:** Site-safety dashboard layout. Reuse global Inspections entity views for drill.

**Fidelity:** Follow global Inspections component styling; apply Site Board token discipline.

**Persona acceptance:**
- Click Site → Safety → dashboard with open hazards / CAs / recent inspections for this project.
- Click an inspection → full inspection record (same UI as global).

**Dependencies:** D1.

---

#### D3 · Quality dashboard within Site

**Value:** Same engine as Safety, different templates. Quality deficiency tracking surfaces here.

**Data model:** None new.

**MCP tools:** Same as D2, filter by inspection type = quality.

**UI:** Mirrors Safety layout, with quality-specific affordances.

**Persona acceptance:**
- Quality deficiencies for this project render. Closure lifecycle works end-to-end.

**Dependencies:** D1, D2.

---

#### D4 · Crew dashboard

**Value:** Site → Crew shows workers on this project with cert status, time summary, productivity.

**Data model:** None new. Joins Workers + TimeEntries + Certifications scoped to project.

**MCP tools:** `get_crew_for_project`, `get_worker_cert_status`.

**UI:** Crew roster with per-worker cert chips + time totals.

**Persona acceptance:**
- Sarah sees Mike + crew on Maple Ridge with cert status + hours this week.
- Cert expiring in 10 days flagged in red.

**Dependencies:** D1.

---

#### D5 · Equipment dashboard

**Value:** Site → Equipment shows equipment assigned to this project with maintenance + inspection status.

**Data model:** None new. Equipment entity exists; assignment relationship queries.

**MCP tools:** `get_equipment_for_project`.

**UI:** Equipment list with status chips.

**Persona acceptance:**
- Forklift assigned to Maple Ridge shows as on-site with next maintenance due date.

**Dependencies:** D1.

---

#### D6 · Daily log dashboard (Work meta-tab)

**Value:** Work → Daily logs shows chronological narrative with voice-captured entries. One utterance populates multiple surfaces per `§3.13`.

**Data model:** DailyLog entity exists.

**MCP tools:** `capture_daily_log_from_voice` extended to populate safety + quality + time + scope simultaneously.

**UI:** Daily log timeline view.

**Persona acceptance:**
- Marco narrates a site walk → daily log populates + safety observations extracted + quality notes extracted + time entries suggested.
- All four surfaces reflect the one utterance.

**Dependencies:** A3, D1, D2, D3.

---

### Phase 5 — Money + Contract

#### E1 · Money meta-tab shell

**Value:** Money tab → spent / budget / invoiced / paid tiles. Cost-by-WorkItem with variance flagged.

**Data model:** No new entities. Aggregation queries.

**MCP tools:** `get_money_dashboard_state_aware`.

**UI:** Needs new preview. Money-meta-tab-specific dashboard layout.

**Persona acceptance:**
- Sarah sees spent vs. budget with variance flagged red.
- Per-WorkItem cost breakdown available.

**Dependencies:** A1, B1.

---

#### E2 · Invoice lifecycle

**Value:** Draft → Sent → Paid lifecycle on Invoice entity. QuickBooks sync.

**Data model:** Invoice entity exists (verify). Extends state enum.

**MCP tools:** `draft_invoice`, `send_invoice`, `record_payment`, `sync_to_quickbooks`.

**UI:** Invoice drill + list view.

**Persona acceptance:**
- Progress invoice for May draftable from the Money dashboard.
- Payment recording updates paid status.
- QuickBooks sync confirms (or flags error).

**Dependencies:** E1.

---

#### E3 · Contract meta-tab shell + assumptions/exclusions

**Value:** Contract tab → ContractVersion summary, assumptions (editable pre-accept, read-only after), exclusions, warranty, retention, variation register.

**Data model:** Uses existing ContractVersion + Assumption + Exclusion entities.

**MCP tools:** Existing + `edit_assumption_pre_accept`.

**UI:** Contract dashboard layout from mockups.

**Persona acceptance:**
- Pre-accept (QUOTED): Sarah edits an assumption; it updates the live quote.
- Post-accept: assumptions read-only. Any change is a variation.

**Dependencies:** A1, B1, B6.

---

#### E4 · Dispute entity + lifecycle

**Value:** Contract tab → Dispute register. Raise dispute flow. Lifecycle: Raised → Negotiating → [Adjudication | ... ] → Resolved.

**Data model:** `data-model-delta.md §4`.

**MCP tools:** `raise_dispute`, `escalate_dispute`, `resolve_dispute`.

**UI:** Dispute inspector — lifecycle view, evidence chain, resolution outcome. Plus `DISPUTE_OPEN` header chip.

**Fidelity:** `micro-details-ledger.md §5` (overlay chips — dispute = red).

**Persona acceptance:**
- Sarah raises a dispute from Contract tab.
- Dispute entity tracks through lifecycle.
- Header chip appears in red when DISPUTE_OPEN.

**Dependencies:** E3.

---

### Phase 6 — Close and beyond

#### B10 · PC declaration + WorkItem 100% gate

**Value:** Sarah declares PC. Kerf checks WorkItems all complete or de_scoped. Punch list captured. PC snapshotted.

**Data model:** `data-model-delta.md §7` (WorkItem state migration done in B1 if not separately). `PracticalCompletion` entity (snapshot).

**MCP tools:** `declare_practical_completion` with pre-condition check.

**UI:** PC Dashboard from `preview/project-screen-lifecycle.html` State 5. Pre-condition error flow: if WI not complete, Kerf lists blockers and offers to de-scope via variation.

**Fidelity:** `micro-details-ledger.md §22` (PC close-summary tiles).

**Persona acceptance:**
- Sarah says "we're done" → all WI 100% → PC fires. Punch list captured via voice prompt.
- If one WI is at 80% → Kerf lists it, offers to mark complete or de-scope.

**Dependencies:** B8, B9.

---

#### B11 · Final invoice + payment recording

**Value:** Final invoice auto-drafts at PC (contract + approved variations − paid to date). Sarah approves + sends. Client pays. Recorded.

**Data model:** Invoice entity — final type.

**MCP tools:** `draft_final_invoice`, `send_invoice`, `record_payment`.

**UI:** PC Dashboard shows final invoice status.

**Persona acceptance:**
- On PC, final invoice $6,065 balance pre-drafted.
- Sarah approves + sends. Client pays via Stripe link. Recorded.

**Dependencies:** B10, E2.

---

#### B12 · CLOSED transition + typed closed_reason

**Value:** Sarah closes the project. Typed reason captured. Archived.

**Data model:** `closed_reason` + `state_at_closure` already in B1.

**MCP tools:** `mark_project_closed` with reason enum.

**UI:** CLOSED Dashboard from State 6. Archive styling (header opacity 0.85, neutral chip).

**Fidelity:** `micro-details-ledger.md §23` (revive card — though not yet interactive in this slice).

**Persona acceptance:**
- Sarah taps `Close project` → prompted for reason → confirms.
- Project flips CLOSED. Header styling changes.
- Kerf warns-but-doesn't-block if unpaid invoice or open defect exists.

**Dependencies:** B10, B11.

---

#### B13 · Revive mechanism

**Value:** Client calls back about a closed project. Sarah revives. State reversal; Revival event captured. Nudge scales to original exit reason.

**Data model:** `data-model-delta.md §5` (Revival entity).

**MCP tools:** `revive_project`.

**UI:** Revive card on CLOSED Dashboard. Nudge text per reason.

**Fidelity:** `micro-details-ledger.md §23` (revive card animation — subtle pulse).

**Persona acceptance:**
- Sarah taps `Revive this project` on a closed project → appropriate nudge (soft / firmer / loud legal caution per reason).
- On confirm → state reverses to pre-close. Revival event logged on timeline.

**Dependencies:** B12.

---

### Phase 7 — Overlays and edges

#### F1 · PauseRecord + PAUSED overlay UI

**Value:** Sarah pauses a project (owner on vacation). Typed reason + expected resume date captured. Overlay chip + body band render. Later: resume.

**Data model:** `data-model-delta.md §6.1` (PauseRecord entity).

**MCP tools:** `pause_project`, `resume_project`.

**UI:** Yellow overlay chip on header + warning band above meta-tab body.

**Fidelity:** `micro-details-ledger.md §5` (overlay chips + PAUSED body band — explicit, not collapsed into chip alone).

**Persona acceptance:**
- Sarah pauses → chip + band visible.
- Nudge at expected_resume_at → resume flow.

**Dependencies:** A1, B1.

---

#### F2 · DLP overlay

**Value:** When contract has DLP (commercial), at PC declaration the DLP_OPEN overlay activates. Auto-nudge at DLP expiry.

**Data model:** `data-model-delta.md §6.2` (DefectsLiabilityPeriod entity).

**MCP tools:** `open_dlp`, `close_dlp_at_expiry`.

**UI:** Muted chip. Contract meta-tab has DLP section.

**Persona acceptance:**
- Commercial project hits PC → DLP auto-opens.
- At expiry → nudge to close DLP (per Principle #15, operator confirms).

**Dependencies:** B10.

---

#### F3 · Retention overlay

**Value:** When contract has retention, RETENTION_HELD overlay tracks held amount, trust requirements, release triggers.

**Data model:** `data-model-delta.md §6.3` (RetentionHolding entity).

**MCP tools:** `hold_retention`, `release_retention` (partial at PC, balance at DLP end).

**UI:** Muted chip. Money meta-tab tile showing held amount.

**Persona acceptance:**
- Commercial project with 5% retention: held amount tracked. Partial release at PC → tile updates. Balance at DLP end.

**Dependencies:** B6, F2.

---

#### F4 · Dispute UI integration

**Value:** Dispute entity from E4 gets full header-chip + body-band integration. "Needs your call" surfaces disputes with escalation cues.

**Data model:** None new (E4 did the entity).

**MCP tools:** None new.

**UI:** Red chip on header. Prominent section in Contract meta-tab. Surfaces on main Dashboard "Needs your call" when new.

**Fidelity:** `micro-details-ledger.md §5` (DISPUTE_OPEN chip = loud red).

**Persona acceptance:**
- Dispute raised → red chip appears on header + Contract tab count badge.
- Closing the dispute clears the chip.

**Dependencies:** E4.

---

## 3. Dependency Graph Summary

```
A1 (shell) ──────────┬───────────────────────────────────────────────┐
                     │                                                │
A2 (MCP dispatch) ───┤                                                │
A3 (voice)      ─────┤                                                │
                     │                                                │
B1 (state migr.) ────┼──▶ B2 (LEAD) ─▶ B3 (QUOTED) ─▶ B4 (magic link) ─▶ B5 (revision)
                     │                       │
                     │                       │
                     ▼                       ▼
                  D1 (Site)             C1 (WI inspector)
                  ├ D2, D3              │
                  ├ D4, D5              ├─ C2 (labour)
                  └ D6 (daily log)      ├─ C3 (item)
                                        ├─ C4 (methodology)
                                        ├─ C5 (provenance)
                                        └─ C6 (source tags everywhere)

B5 ─▶ B6 (accepted) ─▶ B7 (deposit + pre-start) ─▶ B8 (→ACTIVE + needs-call) ─▶ B9 (variations)

B9, B8 ─▶ B10 (PC) ─▶ B11 (final invoice) ─▶ B12 (CLOSED) ─▶ B13 (revive)

E1 (money) ─▶ E2 (invoice) ─▶ B7, B11
E3 (contract) ─▶ E4 (dispute) ─▶ F4

F1 (pause), F2 (DLP), F3 (retention), F4 (dispute UI)
```

---

## 4. Preview Anchoring Per Slice

Every slice ticket must cite the specific preview region it's implementing. Below, the anchor map:

| Slice | Preview file | Section / Anchor |
|---|---|---|
| A1 | `project-screen-lifecycle.html` | Entire shell, all six state frames |
| A2 | `project-screen-lifecycle.html` | All quick-action cards at the bottom of each state |
| A3 | `project-screen-lifecycle.html` | Agent panel input row |
| B1 | `project-screen-lifecycle.html` | Header chip colour matrix |
| B2 | `project-screen-lifecycle.html` | State 1 LEAD |
| B3 | `project-screen-lifecycle.html` | State 2 QUOTED · `quoting-detail-mockups.html` Screen 1 |
| B4 | (new preview needed — client portal design pass) | — |
| B5 | `project-screen-lifecycle.html` | State 2 + agent panel event markers |
| B6 | `project-screen-lifecycle.html` | State 3 ACCEPTED |
| B7 | `project-screen-lifecycle.html` | State 3 ACCEPTED — checklist rows |
| B8 | `project-screen-lifecycle.html` | State 4 ACTIVE — "Needs your call" |
| B9 | `project-screen-lifecycle.html` | State 4 ACTIVE — variation draft card |
| B10 | `project-screen-lifecycle.html` | State 5 PC |
| B11 | `project-screen-lifecycle.html` | State 5 PC — final invoice row |
| B12 | `project-screen-lifecycle.html` | State 6 CLOSED |
| B13 | `project-screen-lifecycle.html` | State 6 CLOSED — revive card |
| C1 | `quoting-detail-mockups.html` | Screen 2 WI inspector |
| C2 | `quoting-detail-mockups.html` | Screen 3 labour drill |
| C3 | `quoting-detail-mockups.html` | Screen 4 item detail |
| C4 | `quoting-detail-mockups.html` | Screen 5 methodology cascade |
| C5 | `quoting-detail-mockups.html` | Screen 6 provenance tree |
| C6 | All mockups — source tags throughout |
| D1–D6 | (new previews needed — Site meta-tab design pass) | — |
| E1–E4 | (new previews needed — Money + Contract meta-tab design pass) | — |
| F1 | `project-screen-mockups.html` | Option C — paused mini-mockup |
| F2–F4 | (preview additions during that phase) | — |

**Preview gaps (need design work before build):**
- Client portal (magic-link view) — for B4
- Site meta-tab dashboards — for D1–D6
- Money meta-tab dashboards — for E1–E2
- Contract meta-tab dashboards — for E3–E4

These gaps become **design-pass sub-slices** that precede the build-slice. Done by the design agent (Claude or human) ahead of engineering pickup.

---

## 5. Fidelity Gate Per Slice

Each slice, before merge:

1. **Preview-vs-app visual diff.** Two browser windows side-by-side. Reviewer notes any divergence.
2. **Micro-details-ledger checklist.** Reviewer opens `micro-details-ledger.md` and checks each referenced section against the implemented surface.
3. **Voice-equivalent phrase test.** If the slice adds tap affordances, the voice phrase per `project-screen-ia-audit.md §7` must be implemented and testable.
4. **Persona acceptance test.** At least one persona walkthrough (Jake, Sarah, or Marco) executed end-to-end on real data.
5. **Validation queries pass.** CI-run queries from `data-model-delta.md §16` green.

No slice merges without all five. Per Paul's concern about fidelity risk, this is the guard.

---

## 6. Rolling Risk Management

As slices land, some risks crystallise. Track here:

- **Data model discovery.** Verifications in `data-model-delta.md §19` shift the migration plan. Re-size B1 when we find out the real `Contract`/`Quote`/`ChangeOrder` state.
- **Insight / ResourceRate coverage.** Existing Domain 17 services may cover parts of Labour/Item provenance. C2 and C3 might collapse if existing services expose the needed data already.
- **Client portal design.** Not yet drawn. Blocker for B4 — design-pass sub-slice before build.
- **Site meta-tab previews.** Not drawn. Blocker for Phase 4. Same pattern.
- **Methodology service.** Per handoff, schema ready but service pending. C4 depends on this — either do the methodology service as part of C4 or break it out as a pre-C4 sub-slice.

Each risk's mitigation is a design-pass or verification task before the slice kicks off.

---

## 7. What "Done" Looks Like

Every phase's milestone is demo-ready at the end of its last slice. The final state (end of Phase 7):

- Jake can take a lead, quote, accept, execute, PC, close, revive — all in the new dark Site Board UI with every source-provenance detail visible.
- Sarah can manage a commercial project with variations, disputes, pauses, DLP, retention, and multiple crews + equipment.
- Marco can use the Site meta-tab as his daily command centre, voice-narrating a walk that populates four surfaces simultaneously.
- Every number on every screen is traceable. Every state transition is operator-triggered. Every consequential email is draft-and-approve.

The canvas (§3.15) and Home screen (§12 of IA audit) are separate implementation tracks not in this document.

---

*End of vertical slices plan. Four pre-implementation docs now complete — ready for Phase 0 kickoff.*
