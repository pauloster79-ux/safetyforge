# Project Lifecycle Flow — Design

**Status:** Design locked through the core state machine. Open items flagged at the end for follow-up work.
**Author:** Claude + Paul (persona-driven walkthrough, session 2026-04-18)
**Scope:** The full lifecycle of a Project in Kerf — from first inbound contact (`LEAD`) through closure (`CLOSED`), including variations, disputes, pauses, revivals, and terminal exits. WorkItem sub-states covered. Progress invoicing and client-portal UX flagged as follow-on design passes.
**Related:**
  - [canonical-work-categories.md](canonical-work-categories.md) — WorkItems carry `CATEGORISED_AS`
  - [methodology.md](methodology.md) — Methodology cascades through the lifecycle
  - [estimating-intelligence.md](estimating-intelligence.md) — Insights attach via methodology
  - [research/lifecycle-01-contract-conventions.md](research/lifecycle-01-contract-conventions.md) — industry contract norms
  - [research/lifecycle-02-competitor-state-handling.md](research/lifecycle-02-competitor-state-handling.md) — competitor state models (partial verification pending — see [handoff-2026-04-18-competitor-market-scan.md](../workflow/handoff-2026-04-18-competitor-market-scan.md))
  - [research/lifecycle-03-variation-and-payment.md](research/lifecycle-03-variation-and-payment.md) — variation / payment / close-out mechanics
  - `PRODUCT_VISION.md §3.12` (Agent autonomy), `§3.14` (Email channel), `§6 principle #15` (Operator controls transitions)

---

## 1. Design Principle (Governing)

**Principle #15 from `PRODUCT_VISION.md`:**

> Advise, highlight, keep logical, do what you're told. The contractor controls state transitions, and every other consequential action. Kerf advises with context, highlights issues and risks, enforces only those preconditions where a transition is logically impossible without them, and then does what the operator asks.

This principle governs every decision below. Hard preconditions exist only where a transition is logically inconsistent without them. Everything else is a nudge.

---

## 2. The Core State Machine

### 2.1 States

```
LEAD ──send quote──▶ QUOTED ──Kate accepts──▶ ACCEPTED ──1st time entry──▶ ACTIVE ──Jake declares──▶ PC ──Jake flips──▶ CLOSED
  │                     │                                                                                                  ▲
  └────── nudge ────────┴──────────────── any state (Jake flips) ─────────────────────────────────────────────────────────┘

Terminal state CLOSED carries a typed `closed_reason`:
  completed | terminated_convenience | terminated_cause | abandoned | lead_lost

`state_at_closure` is captured so the pre-close context is preserved.
```

### 2.2 Active states — roles and semantics

| State | Meaning | What exists | What can change | Who triggers entry |
|---|---|---|---|---|
| `LEAD` | Inbound contact; pursuing or not yet decided | Contact, optional address, notes, possibly draft WorkItems | Everything — no commitment yet | System on first Project creation |
| `QUOTED` | Formal price proposal sent to client | `Quote v1` snapshot (versionable); WorkItems with prices; methodology attached; valid-through date | Revisions create `Quote v2` (supersedes v1); scope edits create new versions | Jake hits "Send quote" |
| `ACCEPTED` | Client has accepted the quote; contract formed | `ContractVersion v1` snapshot locked (sum, hash of accepted quote, parties, dates, payment terms, retention, jurisdiction); scope is variation-only | Only via `Variation` | Client (Kate) clicks Accept on magic link / signs via emailed approval |
| `ACTIVE` | Work is happening; time, materials, variations flow | Time entries, receipts, daily logs, photos, variations, updated WorkItem states | Scope only via approved `Variation`; other properties evolve freely | System on first time entry against the project |
| `PRACTICAL_COMPLETION` (PC) | Work substantively done; client in beneficial use | Frozen `PracticalCompletion` node (date, scope-at-PC snapshot, punch list); DLP clock where required | Only defect fixes, punch items, outstanding variations | Jake — with one hard precondition (see 2.4) |
| `CLOSED` | Terminal. Record archived for historical and analytical purposes | Closure snapshot: `closed_at`, `closed_by`, `closed_reason`, `state_at_closure`, any open-items flags | Revive flips state back (see §6) | Jake |

### 2.3 Transitions — triggers and effects

| Transition | Trigger | Hard preconditions | Snapshot captured |
|---|---|---|---|
| *new* → `LEAD` | Project created | — | — |
| `LEAD` → `QUOTED` | Jake hits Send on a quote | Quote has at least one WorkItem priced; validity date set | `Quote v1` snapshot |
| `QUOTED` → `ACCEPTED` | Client accepts via magic link or emailed approval; OR Jake records a verbal acceptance manually | Quote is current (not superseded by an un-sent draft) | `ContractVersion v1` immutable snapshot |
| `ACCEPTED` → `ACTIVE` | First time entry logged against the project (by Jake) | — | — |
| `ACTIVE` → `PRACTICAL_COMPLETION` | Jake declares done | **All in-scope WorkItems are `complete` or `de_scoped`** (the only hard gate) | `PracticalCompletion` node (date, scope-at-PC = `v1 + approved variations`, punch list from Jake's optional capture) |
| `PRACTICAL_COMPLETION` → `CLOSED` | Jake flips when ready | — | `CLOSED` record with `closed_reason: completed`, `state_at_closure: PRACTICAL_COMPLETION` |
| any state → `CLOSED` (early exit) | Jake flips, choosing the reason | — (Kerf warns on suspect closures; never blocks) | `CLOSED` record with typed reason (`terminated_convenience`, `terminated_cause`, `abandoned`, `lead_lost`) and `state_at_closure` |
| `CLOSED` → prior state (revive) | Jake flips | — | `Revival` event on the timeline (`revived_at`, `revived_by`, `prior_closed_reason`, optional note) |

### 2.4 Practical Completion — the pivot transition

This is the operationally biggest transition. Per [research #3 §3.1, §6.4](research/lifecycle-03-variation-and-payment.md), at PC:

- Risk of damage shifts to owner; insurance shifts; LDs stop; contractor off-site except for defects.
- Retention half-release where applicable (residential typically no retention — see overlays §4).
- DLP clock starts where applicable.
- Contract sum frozen except for outstanding claims.

**Kerf's implementation:**

- **Trigger:** Jake declares done. One hard precondition — all in-scope WorkItems at state `complete` or `de_scoped`. Nothing else gates this (per Principle #15).
- **Snapshot:** `PracticalCompletion` node captures the date, scope-at-PC (`ContractVersion v1 + approved Variations`), punch list (from Jake's capture — *"any touch-ups noted?"*), and DLP terms where applicable.
- **Nudges Kerf shows Jake before the transition** (not gates):
  - Any Variation still in `Draft` or `Issued` — *"V2 still unsigned; close or skip?"*
  - Any failed or missing final inspection where the work was permitted — *"rough passed, final not logged"*
  - Outstanding invoice balance — *"deposit paid, final not sent; draft it?"*
- **Client acknowledgment is an event, not a gate.** Kerf sends Kate a PC certificate via email with a magic-link acknowledge. Her confirm-click is recorded on the `PracticalCompletion` node as `acknowledged_at` / `acknowledgment_method`. Absence is recorded as a gap in the audit trail — Jake's certificate still stands.

---

## 3. The Variation Lifecycle

Variations are **numbered addenda** attached to `ContractVersion v1` — not new ContractVersions. This matches [research #3 §1.2, §6.2](research/lifecycle-03-variation-and-payment.md): *"Universal: amendment in place. Variations are numbered addenda incorporated by reference."* See Decision 6 rationale.

### 3.1 Variation state machine

```
Draft → Issued → Approved
           ├→ Rejected
           └→ Superseded     (when Jake revises after client pushback)
```

| State | Meaning | Visible to client? |
|---|---|---|
| `Draft` | Jake composing; not yet sent | No |
| `Issued` | Sent to client (email + magic link) | Yes |
| `Approved` | Client signed; immutable; adjusts effective contract sum | Yes |
| `Rejected` | Client declined; immutable terminal; not billable | Yes |
| `Superseded` | Jake revised in response to client pushback; V1.1 replaces V1 | Yes (history available) |

Events inside `Issued` (not state changes): client viewed, client asked question, client requested revision.

### 3.2 Variation data model

```cypher
(:Variation {
  id: "var_a1b2c3d4",
  number: 1,                            // gap-free sequence per contract
  state: "Approved",
  subject: "Pantry outlet, USB at coffee station, black pendants",
  sum_delta_cents: 38500,               // +$385
  time_delta_days: 0.5,                 // +0.5 day
  issued_at: datetime(),
  issued_by: "user_jake",
  approved_at: datetime(),
  approved_by: "client_kate",           // signature-equivalent
  approval_method: "magic_link",
  // + standard actor provenance
})

(ContractVersion {id: "cv_v1", ...})-[:HAS_VARIATION]->(Variation)
(Variation)-[:HAS_LINE_ITEM]->(WorkItem)        // zero or more
(Variation)-[:SUPERSEDES]->(Variation)          // when revised
```

### 3.3 Bundle vs. split

Kate's three requests (pantry outlet, USB outlet, pendant colour change) can be one `Variation` with three line items (bundle — whole-thing approve/reject) or three separate `Variation`s (split — per-item approve/reject granularity). This is **Jake's choice at draft time**. The data model supports either.

### 3.4 Scope changes after acceptance

From the moment the Project hits `ACCEPTED`, scope can change only via `Variation`. Pre-start additions ("Kate calls Monday asking to add the pantry refresh") are variations, even if Jake treats them informally — the record is what protects him downstream. Kerf nudges to formalise; doesn't block.

Work performed on variation scope before approval follows Principle #15 — Kerf doesn't hard-block time entries on un-approved scope, but auto-detects them, flags Jake, and proposes drafting the variation from the evidence already captured. See [research #3 §1.4](research/lifecycle-03-variation-and-payment.md) on the jurisdictional risk of unsigned work.

### 3.5 Effective contract sum

Never stored. Always computed:

```
effective_sum = ContractVersion_v1.sum + Σ(Variation.sum_delta_cents where state = 'Approved')
```

At Practical Completion, the snapshot `PracticalCompletion.scope_at_pc` freezes this value for audit.

---

## 4. Overlays

Overlays are orthogonal dimensions on a Project; they do not replace the base state. Multiple overlays can coexist (e.g., a Project can be `ACTIVE` + `PAUSED` + `DISPUTE_OPEN` simultaneously).

### 4.1 `PAUSED` overlay (Decision 9)

Single typed overlay covering both informal holds and formal suspensions.

```cypher
(Project)-[:PAUSED {
  pause_type: "on_hold" | "suspended",
  reason: "owner_vacation" | "contractor_non_payment" | "regulatory" | "owner_cashflow" | ...,
  paused_at: datetime(),
  paused_by: "user_jake",
  expected_resume_at: date(),        // optional
  cure_deadline: date(),             // if pause_type = "suspended"
  client_request_ref: "email_xyz"    // optional — evidence Kate requested the hold
}]->(Project)
```

**Who can pause:** Jake only. Kate's requests to pause arrive via email / call; Jake captures them on the pause record as evidence.

**Unpausing:** Jake clears the overlay. Kerf can nudge when `expected_resume_at` passes.

### 4.2 `DLP_OPEN` overlay (Decision 8)

Activates only when the contract or jurisdiction requires it. Residential default = no overlay (per Decision 8). Commercial / retention jobs activate it at Practical Completion.

```cypher
(Project)-[:DLP_OPEN {
  dlp_start: date(),
  dlp_duration_days: 365,
  dlp_end: date(),
  source: "contract_clause" | "statutory"
}]->(Project)
```

### 4.3 `RETENTION_HELD` overlay

Activates only where retention applies (commercial; NZ trust regime; Ontario statutory holdback). Residential default = no overlay.

```cypher
(Project)-[:RETENTION_HELD {
  retention_pct: 5.0,
  held_in_trust: true,
  trust_account_ref: "acc_xyz",
  scheduled_releases: [{trigger: "PC", pct: 2.5}, {trigger: "final_completion", pct: 2.5}]
}]->(Project)
```

### 4.4 `DISPUTE_OPEN` overlay

Derived — true whenever at least one linked `Dispute` is un-resolved (see §5).

### 4.5 Overlay composition

Overlays are independent. A project can be in `ACTIVE` + `PAUSED[pause_type: suspended, reason: contractor_non_payment]` + `DISPUTE_OPEN`. Each overlay is queryable independently, and the UI surfaces them as chips on the Project card.

---

## 5. Disputes

`Dispute` is a first-class entity with its own lifecycle (Decision 12). Multiple disputes per Project are supported.

### 5.1 Dispute state machine

```
Raised → Negotiating → [Adjudication | Mediation | Arbitration] → Resolved
                                                                      │
                                                                      └→ (possibly further escalation)
```

- `Raised` — recorded; parties notified.
- `Negotiating` — informal resolution attempts (common and typically sufficient in residential).
- `Adjudication` / `Mediation` / `Arbitration` — formal escalation paths (commercial; statutory in UK / IE / AU / NZ / Canada).
- `Resolved` — final outcome: `settled | withdrawn | adjudicated | abandoned`.

### 5.2 Data model

```cypher
(:Dispute {
  id: "disp_a1b2c3d4",
  state: "Negotiating",
  subject: "Final payment / pantry outlet position",
  raised_by: "client_kate",
  raised_at: datetime(),
  amount_in_dispute_cents: 606500,
  resolution_outcome: null,
  // + full actor provenance
})

(Project)-[:DISPUTE_OVER]->(Dispute)
(Dispute)-[:HAS_EVIDENCE]->(Document|Photo|Conversation)
(Dispute)-[:HAS_ADJUDICATOR]->(Contact)
(Dispute)-[:RESOLVED_BY]->(Adjudication|Settlement|Withdrawal)
```

### 5.3 Dispute interaction with other states

Disputes do **not** change the Project state. A Project can remain `ACTIVE` while `DISPUTE_OPEN` — work continues unless a party also invokes `PAUSED` (suspension). See [research #3 §4.4](research/lifecycle-03-variation-and-payment.md).

---

## 6. Revive

Per Decision 11. Revive is **state reversal**, operator-controlled, with Kerf's nudges calibrated by the exit reason.

```
CLOSED[lead_lost]           → LEAD           (soft nudge — "you closed this 6 months ago; continue from where you left off?")
CLOSED[abandoned]           → prior state    (firmer — "this was abandoned mid-job; contract validity may have lapsed")
CLOSED[terminated_*]        → prior state    (loud legal caution — "was formally terminated; consider a new Project")
CLOSED[completed]           → — ("no revive; any new scope is a new Project — start fresh linked to this client?")
```

Revive captures an immutable `Revival` event on the timeline:

```cypher
(:Revival {
  id: "rev_a1b2c3d4",
  revived_at: datetime(),
  revived_by: "user_jake",
  prior_closed_reason: "lead_lost",
  state_before_revival: "CLOSED",
  state_after_revival: "LEAD",
  note: "Kate called — kitchen is back on"
})

(Project)-[:HAS_REVIVAL]->(Revival)
```

State history reads cleanly: `LEAD → CLOSED[lead_lost] → LEAD (revived) → QUOTED → ACCEPTED → ...`. Closure records are never deleted — they stay on the timeline as historical facts.

### 6.1 Why this matters

Research #2 flagged revive-with-context as a gap no competitor handles well. Reviving preserves the full conversation history, Pinterest reference boards, prior quote drafts, methodology captures, and client context — which are the treasure. This is a material Kerf differentiator.

---

## 7. WorkItem State (Decision 13)

WorkItems carry their own state enum, semi-independent of the parent Project.

```
not_started → in_progress → complete
                   │
                   └→ de_scoped   (via Variation — never a hard delete)
```

### 7.1 State semantics

| State | Meaning | Triggered by |
|---|---|---|
| `not_started` | No time entries yet; no work has begun | Creation (default) |
| `in_progress` | At least one time entry logged against the item | Time-entry auto-derivation |
| `complete` | Jake has explicitly marked the item done | Jake's explicit marking |
| `de_scoped` | Removed from contract scope via approved Variation; immutable record retained | Variation approval with `removed_work_item_ids` |

### 7.2 Progress percent

Separate property, independent of state. Used by:
- **Sarah** — load-bearing for progress invoicing (bills based on `% complete` per line)
- **Jake** — barely used; he'll often jump straight from `not_started` to `complete` on small items

### 7.3 The PC precondition

`ACTIVE → PRACTICAL_COMPLETION` requires every in-scope WorkItem to be either `complete` or `de_scoped`. This is the only hard gate on the PC transition (per Decision 7). Kerf surfaces the offending items if Jake tries to declare PC prematurely: *"WorkItem XYZ is still in_progress — mark complete or de-scope via variation?"*

---

## 8. Client-Counterparty Actions

Per Principle #15, only Jake (the operator) triggers state transitions. The exception is when the state transition *is* a counterparty action by design — specifically, the client accepting a Quote or a Variation.

| Action | Effect |
|---|---|
| Kate clicks Accept on `Quote v2` via magic link | `QUOTED → ACCEPTED`; `ContractVersion v1` snapshot locks |
| Kate clicks Approve on `Variation V1` | `Variation.state = Approved`; immutable; effective contract sum recomputes |
| Kate clicks Acknowledge on PC certificate | `PracticalCompletion.acknowledged_at` recorded; no state change (PC already fired on Jake's declaration) |
| Kate declines / rejects | Quote or Variation flips to `Rejected`; Project state unchanged |

Kate's actions are first-class counterparty events — the only non-Jake triggers for any structural change. Everything else about Kate (comments, questions, inbound email, magic-link views) is a timeline event, not a structural trigger.

---

## 9. Agent Autonomy in Lifecycle Transitions

Per `PRODUCT_VISION.md §3.12`, updated today. Summary of where each transition sits:

| Transition | Tier | Rationale |
|---|---|---|
| Agent drafting quotes, variations, emails, invoices | Propose and confirm | Draft-before-send; Jake reviews |
| Agent sending client-facing emails | Contractor approves | Explicit approval required; never autonomous |
| Agent suggesting state transitions (PC ready, close ready, etc.) | Propose and confirm | Surfaced as nudge; Jake confirms |
| State transition execution | Contractor approves | Jake taps the affirmative action |
| Event capture (daily log, defect report, photo, time entry, client-email-parse) | Autonomous | Underlying data capture; no state effect |
| Nudge surfacing (idle leads, expiring quotes, overdue payments, etc.) | Autonomous | Surfacing doesn't act |

---

## 10. Persona Walkthrough Summary — Jake's Kitchen Remodel

Condensed trace of the walkthrough that drove this design:

1. **Tuesday 4pm.** Kate calls Jake — kitchen remodel. Jake notes address, agrees to Thursday. *Project created in `LEAD`.*
2. **Thursday 9am.** Site visit. Jake walks kitchen, notes FPE panel, takes photos, hears about pendants from Pinterest.
3. **Thursday evening.** Jake voice-dictates scope. Kerf drafts WorkItems, methodology, quote. $14,200, 60/40. Jake hits Send. *`LEAD → QUOTED`. `Quote v1` snapshotted.*
4. **Friday lunch.** Kate opens magic link, asks a question. Jake replies via email; issues `Quote v2` with pantry outlet as optional. *v2 supersedes v1.*
5. **Saturday.** Kate + Dave review v2. Yes-with-pantry.
6. **Monday 8:15am.** Kate accepts via magic link. *`QUOTED → ACCEPTED`. `ContractVersion v1` locked: $14,200, 60/40, AZ jurisdiction.*
7. **Monday.** Deposit invoice ($8,520) drafted + sent. Kate pays. Permit application drafted + submitted.
8. **Tuesday.** Permit issued.
9. **Wednesday 3pm.** Jake picks up materials. Logs time entry. *`ACCEPTED → ACTIVE`.*
10. **Thu–Sat.** On-site work. Rough inspection Fri (pass). Daily logs voice-captured. Time entries rolling.
11. **Saturday 5pm.** Kate asks for three changes (pantry outlet, USB, black pendants). Jake drafts `V1` with three line items. Issues via email.
12. **Sunday 9am.** Kate approves V1. *Variation V1 immutable. Effective sum: $14,585.*
13. **Sun–Tue.** Variation work + final inspection (pass).
14. **Wednesday 10am.** Walk-through with Kate. Jake declares done. All WorkItems at `complete`. *`ACTIVE → PRACTICAL_COMPLETION`. `PracticalCompletion` snapshot captured; DLP overlay not activated (residential, no retention).*
15. **Wednesday.** Final invoice ($6,065 = $14,585 − $8,520 deposit) drafted + sent.
16. **Thursday.** Kate pays.
17. **~3 months later.** Flickering can light. Kate texts. Jake swings by Saturday, swaps driver. *`DefectReport` + resolution event on timeline; no state change.*
18. **~6 months later.** No further defects. Jake closes. *`PC → CLOSED[completed]`.*

Every transition traces back to Jake's deliberate action (or Kate's as counterparty). No auto-transitions on silence or elapsed time. Kerf drafted every artefact; Jake approved every send.

---

## 11. Decisions Ledger

| # | Decision | Chosen | Rationale |
|---|---|---|---|
| 1 | Lead entity or Lead state? | Lead is a state of Project | One entity, one mental model; addresses revive-with-context gap |
| 2 | Pre-contract states | `LEAD → QUOTED` (two states only) | `QUOTING` state adds nothing derivable from data presence; noise |
| 3 | Quote revisions | Versioned quotes (`v2 SUPERSEDES v1`) | Audit trail for trust; aligns with post-signature variation model |
| 4 | State between QUOTED and ACTIVE? | Yes — `ACCEPTED` as distinct state | Lock point too big to collapse; pre-start is legally distinct |
| 5 | `ACCEPTED → ACTIVE` trigger | First time entry of any kind | Prep is real work; simplest machine |
| 6 | Variation modelling | Numbered addenda to `ContractVersion v1`, not new ContractVersions | Industry standard; supports bundle-vs-split; direct audit of delta |
| 7 | PC trigger | Jake declares; WorkItems at 100% or de-scoped is the only hard gate | Operator-controlled per Principle #15 |
| 8 | DLP / post-PC shape | Ultra-lean — `PC → CLOSED`; overlays activate only when contractually required | Residential reality (no warranty ceremony); commercial scales via overlays |
| 9 | Pause modelling | One `PAUSED` overlay with typed dimensions | Structured queries, one code path, scales from informal to statutory |
| 10 | Terminal states | Single `CLOSED` with typed `closed_reason` + `state_at_closure` | State machine minimal; typed metadata carries complexity |
| 11 | Revive mechanism | State reversal (not clone); nudges calibrated by exit reason | Lightest-touch UX; preserves context; addresses research gap |
| 12 | Disputes | First-class `Dispute` entity with its own lifecycle | Scales from Jake's phone call to Sarah's adjudication |
| 13 | WorkItem state | `not_started | in_progress | complete | de_scoped` + optional progress percent | Explicit "complete" transition prevents "stuck at 99%"; drives PC gate |
| + | Governing principle | Principle #15 — *Advise, highlight, keep logical, do what you're told* | Shapes every transition decision |

---

## 12. Open Questions (Follow-on Design Passes)

The following items are flagged as out-of-scope for this pass, but relevant and identified:

1. **Progress invoicing.** Interim claims, Schedule of Values, milestone billing (HIA residential schedules, commercial measured work). More data-model than state-machine. Owns its own design pass with Sarah as the lead persona.
2. **Client-portal shape per state.** What Kate sees at each state — derivable from decisions already locked but needs a dedicated UX pass.
3. **Quote expiry with preserved context.** Research #2 gap. Currently handled as a nudge (per Decision 2 + Principle #15), but the UX for "expired but revivable" deserves attention.
4. **Scope lock graduation.** Research #2 gap: *"locked for pricing / editable for description."* Currently scope is fully locked at acceptance; Kerf could support granular edit permissions on non-structural fields.
5. **Sub-contractor states.** Relevant to Sarah (who manages subs) and as-GC workflows. Not Jake's problem.
6. **Multi-party certifiers.** NZS 3910 (2023) splits into Contract Administrator + Independent Certifier. Kerf supports both as abstract roles, but the UI / data-model for the split needs definition.
7. **Final Certificate vs. CLOSED** for commercial. Current model collapses "all obligations settled" into `CLOSED[completed]` triggered by Jake. Commercial contracts require a `FinalCertificate` document at a distinct moment; may need a sub-state or event-type within PC.
8. **Progress billing interaction with `ACCEPTED`.** Can Jake invoice a deposit before `ACCEPTED → ACTIVE`? Today yes (we did it). Formalise.
9. **Client-initiated state transitions.** Kate triggers `QUOTED → ACCEPTED` directly; otherwise she's passive. Are there other counterparty-driven transitions we haven't identified?

---

## 13. Next Steps

1. **UX design pass — Quote process end-to-end.** Scope capture → quote document generation → send → client view (magic link) → question / revision flow → acceptance. HTML preview file first. Builds on existing work (WorkItems, methodology, canonical categories, email channel).
2. **UX design pass — Project screen shape.** Main Jake-facing Project view: states visible, overlays surfaced, timeline, per-state actions, WorkItems list, methodology summary, Variations register, invoices, Disputes tab.
3. **UX design pass — Client portal.** Kate's state-by-state view; derivative of #1 and #2.
4. **Background (pending from 2026-04-17 handoff):**
   - Methodology service + MCP tools build (design complete in [methodology.md](methodology.md))
   - Source-enforcement tightening on `create_labour` / `create_item`
   - Knowledge page frontend enhancements
   - Live Neo4j test against a real instance

Progress invoicing design (item 1 of §12) happens after the Quote process UX settles — the two are closely coupled.

---

## 14. Supersedes / Supplements

This document supersedes any prior informal references to Project state in design docs. Where older docs reference states like `bidding` or `production` (e.g., early estimating drafts in `estimating-intelligence.md`), those should be re-aligned with this state machine on their next substantive revision.

Architectural implications (new node types, overlay relationships, Variation / Dispute / Revival entities) should be folded into `docs/architecture/CONSTRUCTION_ONTOLOGY.md` and recorded as ADRs in `docs/architecture/DECISIONS.md` in a subsequent pass.
