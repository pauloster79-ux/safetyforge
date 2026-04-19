# Project Screen — Information Architecture Audit

**Status:** Pre-implementation artifact. Source of truth for what surfaces on the Project screen, where, and how.
**Author:** Claude + Paul (2026-04-19)
**Scope:** Every feature from `PRODUCT_VISION §3` mapped to its Project-screen surface. Nothing orphaned. Meta-tab dashboards and quick-action cards specified per state, with the MCP tool + conversational flow each dispatches.
**Depends on:** [project-lifecycle-flow.md](project-lifecycle-flow.md) · [project-screen-brief.md](project-screen-brief.md) · [preview/project-screen-lifecycle.html](../preview/project-screen-lifecycle.html)
**Supersedes:** ad-hoc tab lists in earlier design drafts.

---

## 1. Purpose

The Project screen is Kerf's primary working surface. Every capability described in `PRODUCT_VISION §3` has to surface on this screen for the project in question — or has to live elsewhere with a clear reason. This document maps the mapping.

It exists to:
- Guarantee no feature gets orphaned during implementation.
- Give each vertical slice (see `vertical-slices.md`) a clear answer to *"where does this live on the screen?"*.
- Prevent the grey-mush risk Paul raised: fifty features each nearly-implemented, nothing whole.

---

## 2. Governing Principles (recap)

1. **Operator controls state transitions** (Principle #15). Dashboard surfaces urgent items; tabs and quick-actions never auto-fire.
2. **Conversation is primary** (`§3.13`, `§3.15`). Every tap has a voice equivalent. Every card is a shortcut for a chat intent, not a distinct UI path.
3. **Dashboards all the way down.** Meta-tabs open to their own dashboards, not sub-tabs. Drill happens by clicking entities, not by descending tab hierarchies.
4. **Canvas on demand** (`§3.15`). Open questions produce canvases in the conversation pane; the Project screen's structured surfaces do not duplicate what canvas does.
5. **Graph-native everything.** Every card, every drill, every number traces to the graph.

---

## 3. Navigation Shape

```
┌──────────────────────────────────────────────────────────────────┐
│ Header: project · state chip · overlay chips · key metric · CTA   │
├──────────────────────────────────────────────────────────────────┤
│ Meta-tabs:  Dashboard │ Work │ Site │ Money │ Contract │ Docs │ People │
├──────────────────────────────────────────────────────────────────┤
│ Meta-tab body:                                                    │
│   → State-aware dashboard for that meta-tab                       │
│     → Click entity → drill into full record                       │
│     → No sub-tabs                                                 │
└──────────────────────────────────────────────────────────────────┘
 Agent panel (chat + voice) persistent on the left / FAB on mobile
```

- **Meta-tabs** are fixed across every state. Same set of 7. Content shifts with state; identity of the tab does not.
- **Meta-tab dashboard** is the landing view when you click a meta-tab. It's a *curated surface* for that domain — what's urgent, what's active, what's coming — not a grid of sub-tabs.
- **Drill** happens on click. Clicking a specific WorkItem from Work→Scope opens the WorkItem inspector. Clicking an inspection from Site→Safety opens the Inspection full record (same UI as global Inspections surface, scoped to this project).
- **Overlays** (`PAUSED`, `DLP_OPEN`, `RETENTION_HELD`, `DISPUTE_OPEN`) render as chips on the header and coloured bands above the meta-tab body when active.

---

## 4. The Seven Meta-Tabs

| # | Meta-tab | Scope | Global surface (icon rail) |
|---|---|---|---|
| 1 | **Dashboard** | State-aware primary surface. The "what matters right now" view. | — |
| 2 | **Work** | Scope, WorkItems, Variations, Schedule, Daily logs, Timeline | Global Projects / Schedule |
| 3 | **Site** | Safety, Quality, Crew, Equipment — everything that happens on the jobsite | Global Inspections, Workers, Equipment |
| 4 | **Money** | Invoices, payments, cost tracking, margin, variations (financial view) | Global Finance |
| 5 | **Contract** | Contract terms, assumptions, exclusions, warranty, retention, signed documents, ContractVersion history, disputes | — |
| 6 | **Docs** | All uploaded files (plans, specs, photos, permits, COIs, inspection reports) | Global Docs |
| 7 | **People** | Client contacts, GC, subs, inspectors, anyone connected to this project | Global Workers, Subs |

Disputes get a chip on the header when open but live inside **Contract → Disputes** for detail. When `DISPUTE_OPEN` overlay is active, the chip is prominent.

---

## 5. Feature Map — every §3 item placed

For each capability in `PRODUCT_VISION §3`, where it surfaces on the Project screen, where it lives globally, and how it reaches the main Dashboard when urgent.

### 5.1 Find and Qualify Work (§3.1)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Project created as LEAD from call/email/invitation | Created directly, lands on Dashboard `LEAD` state | Global Projects list | LEAD state IS the surfacing |
| Link to client contact | People meta-tab (plus summary card on LEAD Dashboard) | Global Workers/Contacts | — |
| Assess work-type fit, capacity, cert gaps | LEAD Dashboard "Client" card + Peachtree reference + agent note | — | Flags expiring certs / capacity conflicts → "Needs your call" |
| Past-GC payment history | People meta-tab → client drill; also on LEAD Dashboard "Client" card | — | Flagged if payment history poor |

### 5.2 Estimate and Price (§3.2)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| WorkItems capture from voice | Work → Scope; also entered via agent panel from any screen | — | `QUOTED` state Dashboard IS the quote document (per Option C) |
| Plan / spec extraction | Docs meta-tab → upload → agent parses | Global Docs | Flagged quantities mismatched vs. current WorkItems |
| Historical rate application | Inline on WorkItems (source tags); drill via WorkItem inspector | — | — |
| Regulatory requirements flagged | Site → Safety dashboard; Scope → WorkItem inspector shows applicable regs | Global Inspections / Regulations | Flags regulatory gaps before quote sends |
| Margin & total | Header total; QUOTED Dashboard metrics; Money meta-tab dashboard | — | Always visible in header |

### 5.3 Propose and Win (§3.3)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Generate proposal document | QUOTED Dashboard CTA; produces `Document` of type `proposal` | Global Docs | QUOTED state = primary surface |
| Magic-link client view | External surface (client sees it via emailed link). Linked from Dashboard. | — | Inbound client action appears in "Needs your call" |
| Contract parse & lock | ACCEPTED transition snapshots `ContractVersion v1` | — | ACCEPTED state IS the surfacing |
| State progression | Header state chip | — | Always visible |

### 5.4 Plan and Mobilise (§3.4)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| 2–4 week lookahead | Work meta-tab → Schedule dashboard | Global Schedule | "Upcoming" panel in ACTIVE Dashboard |
| Cert / equipment / weather conflict detection | Agent surfaces via Site dashboard + "Needs your call" | Global Inspections / Equipment | Flagged when booking conflicts arise |
| Crew assignment | Site → Crew dashboard; assignable per WorkItem | Global Workers | — |
| Material orders | Work → Daily logs + Money → Purchase orders; ACCEPTED Dashboard "Before we start" card shows pending orders | Global Suppliers | Flagged when lead time threatens schedule |

### 5.5 Execute and Document (§3.5)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Clock-in / clock-out | Site → Crew dashboard (per-worker time); also via agent | Global Workers | "Today" panel on ACTIVE Dashboard |
| Toolbox talk delivery + sign-off | Site → Safety dashboard | Global Inspections | Morning brief card on ACTIVE Dashboard |
| Site walk — voice narration | Agent panel voice mode; populates daily log + safety + quality simultaneously (§3.13) | — | Today's walk summary on ACTIVE Dashboard |
| Daily log | Work → Daily logs dashboard; Timeline meta-tab shows chronologically | — | Today's log summary on ACTIVE Dashboard |
| Safety inspections + hazards + CAs + incidents | Site → Safety dashboard | Global Inspections | Open critical hazards / overdue CAs → "Needs your call" |
| Quality inspections + deficiencies | Site → Quality dashboard | Global Inspections | Open blocking deficiencies → "Needs your call" |
| Time tracking (linked to WorkItem) | Work → Scope (per WI) + Site → Crew (per worker) | Global Workers | Over-budget labour in "Needs your call" |
| Progress tracking | Work → Scope dashboard (progress bars); Dashboard metrics row | — | "Complete %" tile in ACTIVE Dashboard |

### 5.6 Manage Money (§3.6)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Auto-derived job costing | Money meta-tab dashboard | — | "Spent · Budget" tile on ACTIVE Dashboard |
| Cost narrative ("you're 18% over on labour because…") | Money dashboard + agent panel explanation | — | Variance flagged in "Needs your call" |
| Variation auto-detection | Work → Variations dashboard; agent flags in chat | — | Draft variation surfaces in "Needs your call" |
| Variation lifecycle (Draft → Issued → Approved) | Work → Variations register | — | Open variations count shown on Variations tab |

### 5.7 Close Out (§3.7)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Deficiency list generation | Site → Quality dashboard; PC Dashboard pulls summary | Global Inspections | PC state Dashboard |
| Final inspection | Site → Safety/Quality | Global Inspections | — |
| As-built docs assembly | Docs meta-tab; PC Dashboard has a "ready to hand over?" section | Global Docs | — |
| Warranty obligation recording | Contract meta-tab → warranty | — | DLP overlay chip |

### 5.8 Get Paid (§3.8)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Invoicing | Money meta-tab → Invoices | Global Finance / QuickBooks sync | Outstanding invoice tile |
| Payment applications | Money meta-tab → Payment apps | — | — |
| QuickBooks sync | Background integration; status shown on Money meta-tab | Global Settings / Integrations | Sync errors flagged |
| Payment monitoring | Money dashboard + header "Invoiced · Paid" tile | — | Overdue payments in "Needs your call" |

### 5.9 Learn (§3.9)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Post-mortem narrative | PC and CLOSED Dashboard; also available via canvas (§3.15) question-ask | — | — |
| Insight harvesting | CLOSED Dashboard "Insights harvested" section | Global Knowledge | Feed-forward visible on LEAD for similar work types |
| Ad-hoc questions | Agent panel (conversation); canvas pane renders answers | — | — |

### 5.10 Cross-cutting: Safety and Compliance (§3.10)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| Regulatory rule traversal | Site → Safety dashboard shows applicable regs per project | Global Inspections + Regulations graph | Gaps flagged before quoting or scheduling |
| Cert check on task assignment | Site → Crew dashboard flags expiring certs | Global Workers | Expiring certs in "Needs your call" |
| Equipment maintenance check | Site → Equipment dashboard | Global Equipment | Due maintenance flagged |
| Site-specific safety plan | Site → Safety dashboard; generated at ACCEPTED | Global Inspections | — |
| Morning brief (risk score, weather, expirations, CAs, schedule) | ACTIVE Dashboard morning-brief card | Global Morning Brief | Morning brief IS the surfacing |

### 5.11 Cross-cutting: Subcontractor Management (§3.11)

| Sub-capability | Project screen | Global | Main Dashboard surfacing |
|---|---|---|---|
| When contractor is a sub | People → Client (GC) · Site → Crew includes subs managing this project | Global Subs | GC prequal deadlines in "Needs your call" |
| When contractor manages subs | Site → Crew dashboard scoped to this project's subs | Global Subs | Sub compliance issues flagged |
| COI parsing | Docs meta-tab → upload → agent parses | Global Subs | Expiring COI flagged |
| Performance scoring | People meta-tab → sub drill; also global Subs surface | Global Subs | — |

### 5.12 Cross-cutting: The Agent (§3.12)

Not a meta-tab — permeates every surface.

- **Agent panel** persistent on left (desktop) or FAB (mobile). Visible on every meta-tab.
- Every quick-action card dispatches a chat intent the agent handles (see §7 below).
- Every conversation on this Project is linked to the Project and available for retrieval — from any tab.

### 5.13 Cross-cutting: Voice and Mobile (§3.13)

Not a meta-tab — a modality that applies to everything.

- Voice capture from agent panel.
- Walking estimate capture: voice session populates WorkItems in Work → Scope in real-time.
- One utterance → many writes: a site-walk voice session populates Site → Safety + Site → Quality + Work → Daily logs + Work → Timeline + Scope progress simultaneously.
- Offline-first: every write queues locally on mobile and reconciles on sync.

### 5.14 Cross-cutting: Email as Client Channel (§3.14)

Not a meta-tab — a channel.

- Outbound: agent drafts emails from any client-facing context (quote send, variation issue, invoice send, dispute response). Shown in agent panel for approval.
- Inbound: replies to Kerf-originated threads land in the agent panel as events, linked to this Project.
- Email history visible in Work → Timeline (chronological) and Docs → Emails (indexed).

### 5.15 Cross-cutting: Conversation and Canvas (§3.15)

Not a meta-tab — a response mode that opens a new middle pane.

- Open questions ("why did margin drop?", "show me the Peachtree comparison") → agent renders a **canvas** in a **new middle pane** between the agent panel (left) and the Project canvas (right).
- When canvas opens, the Project canvas minimises to the right as a collapsible strip — readable but narrow. The agent panel on the left stays its normal width, conversation intact.
- Canvas may cite entities from any meta-tab. Clicking a citation from within the canvas expands the Project canvas back to full width and scrolls to the entity in the right tab.
- Canvas does not replace meta-tab dashboards — they're for structured, frequent, known surfaces. Canvas is for ad-hoc, open questions.
- *Layout default for now — will evolve as canvas patterns mature in production.*

---

## 6. Meta-Tab Dashboards — what lives in each

For each meta-tab, what its landing dashboard shows, and how it changes per state.

### 6.1 Dashboard (meta-tab 1) — state-aware primary surface

Fully specified in `project-lifecycle-flow.md` and `preview/project-screen-lifecycle.html`. Per state:

| State | Primary content |
|---|---|
| `LEAD` | Next-action card · Peachtree reference · Client card · Quick-action cards |
| `QUOTED` | Quote total tiles · WorkItem table with source tags · Assumptions / Exclusions / Payment Schedule / Warranty / Retention / Sources panels (the seven numbered sections Claude Design produced) |
| `ACCEPTED` | Contract-reference strip · Planned start / Deposit / Duration / Crew tiles · "Before we start" checklist · Recent activity |
| `ACTIVE` | Complete / Spent / Invoiced / Next-milestone tiles · "⚡ Needs your call" panel (variations, variances, expiring certs, open CAs) · Progress by WorkItem · Today · Quick-actions |
| `PC` | PC date / Final value / Net margin / DLP end tiles · Close-out status checklist · DLP defects register · Insights harvested |
| `CLOSED` | Revive card · Final summary tiles · Collapsed project timeline |

### 6.2 Work (meta-tab 2)

**Scope within:** WorkItems · WorkPackages · Variations · Schedule · Daily logs · Timeline

**Dashboard content (state-aware):**

| State | What surfaces |
|---|---|
| `LEAD` | Scope capture entry point · empty Variations · Schedule not yet relevant |
| `QUOTED` | Full WorkItem list with source tags · Variations empty · Schedule proposed dates |
| `ACCEPTED` | WorkItem list (price-locked) · Variations empty · Schedule confirmed · first Daily log ready to capture |
| `ACTIVE` | WorkItem progress summary · Variations register (1 draft, 0 open) · This week's Schedule · Recent Daily logs · Timeline highlights |
| `PC` | WorkItems all complete · Variations all resolved · Schedule closed · Daily logs archive · Timeline |
| `CLOSED` | Archived view — WorkItems completion summary · Variations approved · Timeline |

**Drill-throughs:**
- WorkItem → inspector (labour + items + methodology + insight + sources — see `preview/quoting-detail-mockups.html`)
- Variation → inspector (line items + signatures + effective sum impact)
- Schedule entry → day detail with crew + equipment + trades
- Daily log → full narrative + photos + extracted observations
- Timeline event → event detail

### 6.3 Site (meta-tab 3)

**Scope within:** Safety · Quality · Crew · Equipment

**Dashboard content (state-aware):**

| State | What surfaces |
|---|---|
| `LEAD` | Empty — no field activity yet |
| `QUOTED` | Projected crew · Projected equipment needs · Applicable regulations |
| `ACCEPTED` | Site-specific safety plan draft · Crew assigned · Equipment list · Cert-coverage check |
| `ACTIVE` | **Today: who's on site · what toolbox talk was delivered · open hazards · open CAs · open deficiencies** · Crew with time summary · Equipment with status · Morning brief card |
| `PC` | Closed inspections summary · DLP defects register · Crew time totals · Equipment demobbed |
| `CLOSED` | Archive of all inspections · final crew time · final equipment |

**Drill-throughs:**
- Safety inspection → full inspection record (same UI as global Inspections surface)
- Hazard → hazard detail with photos + assigned CA
- Incident → incident report with chain
- CA → corrective action detail with closure evidence
- Toolbox talk → talk record with sign-off list
- Quality inspection → full record
- Deficiency → deficiency detail with assignment + closure
- Worker → Crew member detail: cert list, time on this project, time on all projects
- Equipment → equipment detail: maintenance schedule, inspection status, schedule

**Why Safety + Quality + Crew + Equipment together under Site:** all four describe "what's happening on the jobsite right now." They share a primary rhythm — the **daily site walk**. The same walk produces safety observations, quality deficiencies, crew-presence confirmation, and equipment-status notes. Quality does not belong with Work (which is desk-side scope + progress planning); it belongs with Safety (which is walked alongside it). Grouping them under **Site** matches how Marco or a superintendent actually uses them — one pass, not four separate visits.

### 6.4 Money (meta-tab 4)

**Scope within:** Invoices · Payments · Cost tracking · Margin · Financial view of Variations · QuickBooks sync status · Retention balance

**Dashboard content (state-aware):**

| State | What surfaces |
|---|---|
| `LEAD` | Empty · projected value from drafted WorkItems |
| `QUOTED` | Proposed contract value · margin projection · payment schedule |
| `ACCEPTED` | Contract value locked · deposit invoice status · payment schedule with upcoming milestones |
| `ACTIVE` | Spent vs. budget · invoices issued vs. paid · outstanding balance · retention held · cost by WorkItem (variance flagged) · upcoming payment trigger |
| `PC` | Final value · final invoice status · retention released/pending · realised margin vs. bid margin |
| `CLOSED` | Final financial summary · full invoice + payment history · realised margin · QuickBooks sync confirmation |

**Drill-throughs:**
- Invoice → invoice detail (line items by WorkItem + approved variations + retention calc)
- Payment → payment record with source (Stripe / check / wire)
- WorkItem cost variance → WorkItem inspector opened to Spent tab
- Retention → retention entity with release schedule

### 6.5 Contract (meta-tab 5)

**Scope within:** ContractVersion history (v1, any subsequent) · Assumptions · Exclusions · Warranty · Retention (terms) · Payment terms · Jurisdiction · Signed documents · **Disputes**

**Dashboard content (state-aware):**

| State | What surfaces |
|---|---|
| `LEAD` | Empty · no contract yet |
| `QUOTED` | Proposed terms (draft) · assumptions + exclusions editable |
| `ACCEPTED` onwards | Immutable `ContractVersion v1` · signed proposal link · assumptions + exclusions (read-only) · warranty + retention terms · approved variations linked · signed documents · disputes (if open) |
| `PC` | Same as ACCEPTED plus PC certificate document · Gary's acknowledgment signature |
| `CLOSED` | Full contract archive · all signed documents · retention release evidence · any dispute resolutions |

**Drill-throughs:**
- ContractVersion → full snapshot (sum, parties, dates, terms, hash of accepted documents)
- Variation → variation detail
- Assumption → assumption record with variation-trigger conditions
- Dispute → dispute lifecycle view (Raised → Negotiating → [Adjudication | Mediation | Arbitration] → Resolved)
- Signed document → PDF view with signature chain

### 6.6 Docs (meta-tab 6)

**Scope within:** All uploaded files linked to this project

**Dashboard content:**

Grouped by type:
- **Plans** — drawings with sheet list, revisions
- **Specifications** — spec documents with section extraction
- **Contracts** — signed contract, amendments
- **Permits** — building / electrical / mechanical / plumbing permits
- **COIs** — insurance certificates (ours + subs')
- **Photos** — site photos grouped by date / WorkItem
- **Reports** — inspection reports, delivered proposals, generated invoices
- **Emails** — inbound + outbound threads linked to this project

**Drill-throughs:**
- Any file → full preview + extraction summary + linked entities
- Plan → annotated view with fixture counts, regions
- Spec → section view with AI-highlighted relevant clauses

### 6.7 People (meta-tab 7)

**Scope within:** Client contacts · GC · Subs · Inspectors · Kerf-side crew (if viewing from GC perspective)

**Dashboard content:**

| Group | What surfaces |
|---|---|
| Client | Primary contact · secondary contacts · communication history · magic-link access log |
| GC | If working as sub — the GC contact and prequal status |
| Subs | If managing subs — each sub's compliance status, training currency, insurance validity, performance metrics |
| Inspectors | Jurisdiction + contact, past inspection history |
| Own crew | Lead + journeymen assigned (cross-link to Site → Crew) |

**Drill-throughs:**
- Contact → full person record with every Project they touch, communication history, preferences
- Sub → sub entity with COI, training records, past jobs, performance scorecard
- Inspector → inspector record with past interactions

---

## 7. Quick-Action Cards — per state, per meta-tab dashboard

Each card dispatches a chat intent. The agent handles the rest. Three parts per card: **label**, **MCP tool** (backend verb), **agent flow** (conversational sequence).

### 7.1 Main Dashboard · LEAD

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Schedule visit | `schedule_project_event` | Form-card with date/time picker (default: next business day 09:00). Confirm → `CalendarEvent` created, synced to Google/Outlook. | "Schedule a site walk for Thursday at 9." |
| Start scope now | `start_voice_scope_capture` | Agent opens voice mode; extracts WorkItems live from utterances; saves to Project on stop. | "Start scope capture." |
| Draft email | `draft_client_email` | Agent: "What do you want to say?" → drafts → user reviews → sends via `§3.14`. | "Draft an email to Gary about scheduling." |
| Mark lost | `mark_project_closed` (reason: `lead_lost`) | Typed reason picker (cashflow / competitor / scope shrank / no response / other) → confirm → state flip. | "Mark this lead as lost — went with someone else." |

### 7.2 Main Dashboard · QUOTED

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Generate proposal | `generate_proposal_document` | Renders PDF from current WorkItems + terms → returns link + email draft to client. Sarah reviews → sends. | "Generate the proposal for Maple Ridge." |
| Send quote | `send_quote_to_client` | Composes email with magic-link to Quote v1 + PDF attachment → Sarah approves → sends. Creates `Quote v1` snapshot. | "Send the quote to Gary." |
| Tighten margins | `propose_margin_adjustment` | Agent analyses current margin vs. target and proposes per-WorkItem tweaks. Sarah accepts/rejects individually. | "Tighten margins — we're below target." |
| Add variation | (pre-contract scope change, not a `Variation` entity) | Agent opens scope edit flow — add a WorkItem, revise quantities. Creates a new Quote version if Quote is already sent. | "Add another 4 floor boxes." |
| Withdraw quote | `withdraw_quote` | Confirm + reason → quote marked `Withdrawn`. Project stays `QUOTED` with no active quote. | "Withdraw the quote." |
| Compare to past job | (canvas query, not state-changing) | Opens canvas in agent pane: side-by-side WorkItem compare. | "Compare Maple Ridge to Peachtree." |

### 7.3 Main Dashboard · ACCEPTED

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Send deposit invoice | `send_invoice` (type: deposit) | Agent drafts invoice from payment schedule → Sarah approves → sends via email + QuickBooks sync. | "Send the deposit invoice to Gary." |
| Submit permit | `submit_permit_application` | Agent opens drafted permit application (pre-filled from contract) → Sarah reviews → submits (jurisdiction-specific path). | "Submit the Phoenix electrical permit." |
| Order materials | `create_material_order` | Agent opens PO draft from material-requirement inference on WorkItems → Sarah confirms supplier + delivery → sends. | "Order the panels and rough wire." |
| Confirm start date | `update_project_date` | Edit planned start date → Sarah confirms → GC + crew notified. | "Confirm Monday start." |
| Log first hours | `log_time_entry` | Opens time-entry flow. First entry flips state to `ACTIVE`. | "Clock in for Maple Ridge." |

### 7.4 Main Dashboard · ACTIVE

The busiest state. Cards prioritised by urgency.

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Log time | `log_time_entry` | Agent picks most likely WorkItem based on GPS + recent activity. Sarah confirms or picks. | "Clock in on WI 04 for 4 hours." |
| Daily log | `capture_daily_log` | Agent opens voice capture; Sarah narrates the day; agent extracts to daily log + safety + quality + time. | "Start the daily log." |
| Photo | `capture_photo` | Camera opens; Sarah tags WorkItem / issue / phase; agent classifies (hazard / progress / defect / context). | "Take a photo." |
| Draft variation | `draft_variation_from_chat` | If triggered from chat context, agent uses evidence from logs + photos + time entries to pre-populate. Otherwise, agent prompts. | "Draft a variation for the extra slab cores." |
| Send progress invoice | `send_invoice` (type: interim) | Agent composes invoice at current % complete per WI + approved variations → Sarah approves → sends. | "Invoice for May progress." |
| Pause project | `pause_project` | Typed pause_type + reason + expected resume date. Creates overlay. | "Pause Maple Ridge — owner on vacation until Apr 28." |
| Declare PC | `declare_practical_completion` | Precondition check (all WI 100% or de-scoped). If fails, lists open items. If passes, opens PC flow — punch list capture, scope snapshot, DLP start. | "We're done at Maple Ridge." |

### 7.5 Main Dashboard · PRACTICAL COMPLETION

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Send final invoice | `send_invoice` (type: final) | Composes final invoice (contract + approved variations − paid to date) → Sarah approves → sends. | "Send the final invoice." |
| Capture punch item | `create_defect_item` | Agent prompts: description · location · responsibility · severity. Creates `DefectItem` node. | "Punch item — south hallway pendant misaligned." |
| Resolve defect | `resolve_defect_item` | Opens open defect list → Sarah picks → agent logs time + photo of fix. | "Defect on can 3 resolved — swapped driver." |
| Close project | `mark_project_closed` (reason: `completed`) | Flag any open items (invoices, variations, defects) with warn-not-block per Principle #15. Sarah confirms → state flip to `CLOSED`. | "Close Maple Ridge." |
| Harvest insights | (automatic on closure; card shows review link) | Agent proposes insights detected from this job's variance between estimate and actuals. Sarah accepts/modifies. | "Show me what we learned on Maple Ridge." |

### 7.6 Main Dashboard · CLOSED

| Card | MCP tool | Agent flow | Voice equivalent |
|---|---|---|---|
| Revive this project | `revive_project` | Agent confirms with nudge scaled to exit reason (soft for `lead_lost`, firmer for `abandoned`, loud for `terminated_*`). Reverses state. | "Revive Maple Ridge — Gary's back." |
| New linked Project | `create_project` (with `LINKED_TO` reference) | Creates a new Project linked to this one. Starts at `LEAD`. | "New project for Maple Ridge Phase III." |
| View post-mortem canvas | (canvas query) | Opens canvas in agent pane: estimated vs actual by WorkItem + narrative + insights. | "How did Maple Ridge go?" |

### 7.7 Quick-actions inside meta-tab dashboards

Each meta-tab dashboard has its own per-state quick-action row. Abbreviated pattern — full list deferred to slice-level design:

- **Work** → Add WorkItem · Reorder packages · Adjust progress · Draft variation · Edit methodology
- **Site** → Start site walk · Log hazard · Log incident · Clock in worker · Mark equipment on-site · Deliver toolbox talk
- **Money** → Draft invoice · Record payment · Generate payment application · Sync to QuickBooks · Adjust retention
- **Contract** → View signed contract · Edit assumptions (if pre-accept) · Raise dispute · View variation register
- **Docs** → Upload · Scan document · Link existing · Extract to entities
- **People** → Add contact · Add sub · Request COI · Record communication

Every one of these is a chat intent. Agent handles the flow.

---

## 8. Overlays — how they surface

| Overlay | Where it shows | Interaction |
|---|---|---|
| `PAUSED` (typed: `on_hold` / `suspended`) | Yellow band above meta-tab body · chip on header | Click → pause record with reason, timeline, resume timer. Agent card: "ready to resume?" |
| `DLP_OPEN` | Muted chip on header · section in Contract meta-tab | Click → DLP details, defects register |
| `RETENTION_HELD` | Muted chip on header · tile in Money meta-tab | Click → retention entity, release schedule |
| `DISPUTE_OPEN` | Red chip on header · prominent section in Contract meta-tab · "Needs your call" card on main Dashboard | Click → Dispute entity lifecycle view |

---

## 9. Nothing-Orphaned Check

Cross-referencing `PRODUCT_VISION §3.1–§3.15` against this audit:

| §3 item | Covered in audit? |
|---|---|
| 3.1 Find and Qualify Work | ✅ §5.1 · primary in `LEAD` Dashboard + People meta-tab |
| 3.2 Estimate and Price | ✅ §5.2 · primary in `QUOTED` Dashboard + Work meta-tab |
| 3.3 Propose and Win | ✅ §5.3 · state transitions, magic-link view, Contract meta-tab |
| 3.4 Plan and Mobilise | ✅ §5.4 · Work → Schedule + Site → Crew/Equipment |
| 3.5 Execute and Document | ✅ §5.5 · `ACTIVE` Dashboard + Site meta-tab + Work → Daily logs |
| 3.6 Manage Money | ✅ §5.6 · Money meta-tab + Work → Variations |
| 3.7 Close Out | ✅ §5.7 · `PC` Dashboard + Site → Quality deficiencies |
| 3.8 Get Paid | ✅ §5.8 · Money meta-tab · QuickBooks integration |
| 3.9 Learn | ✅ §5.9 · `CLOSED` Dashboard insights + agent canvas for ad-hoc questions |
| 3.10 Safety & Compliance (cross-cutting) | ✅ §5.10 · Site → Safety + cert/equipment/regulatory surfacing on main Dashboard |
| 3.11 Sub Management (cross-cutting) | ✅ §5.11 · People meta-tab + Site → Crew when managing · Docs for COIs |
| 3.12 The Agent (cross-cutting) | ✅ §5.12 · persistent panel on every surface + every quick-action dispatches a chat intent |
| 3.13 Voice and Mobile (cross-cutting) | ✅ §5.13 · voice capture in agent panel · walking estimate capture → Work → Scope · one-utterance-many-writes across Site + Work · offline-first on mobile |
| 3.14 Email as Client Channel (cross-cutting) | ✅ §5.14 · agent panel for compose/review · Timeline + Docs → Emails for history |
| 3.15 Conversation and Canvas (cross-cutting) | ✅ §5.15 · canvas renders in agent pane for open questions · cites entities from any meta-tab · does not duplicate structured surfaces |

**Orphan check: all 15 items covered. No feature lives only in design-dead-space.**

---

## 10. Decisions Made in This Audit

1. **Seven meta-tabs, fixed across states.** Dashboard · Work · Site · Money · Contract · Docs · People.
2. **Dashboard inside each meta-tab, no sub-tabs.** Each meta-tab's landing is a state-aware summary dashboard; drilling is by entity click.
3. **Site meta-tab (renamed from Field) groups Safety + Quality + Crew + Equipment.** Rationale: one daily site walk produces all four surfaces' data. Quality belongs with Safety (both observed on the walk), not with Work (which is desk-side scope + progress planning).
4. **Disputes live inside Contract meta-tab.** With a prominent header chip when open.
5. **Quick-action cards are chat intents.** Each card has a named MCP tool and a conversational flow. Voice equivalents explicit.
6. **Canvas (§3.15) is not a tab.** It opens in a **new middle pane** between the agent panel and the Project canvas. The Project minimises to the right as a collapsible strip; the agent conversation on the left is unchanged. Default layout for now — needs more thought as canvas usage matures.
7. **People meta-tab uses role chips**, not split tabs. Client contacts, GC, subs, inspectors, Kerf-side crew all coexist with role chips for filtering.
8. **WorkPackage groupings shown in Work → Scope** with expand/collapse. Flat list for Jake-scale jobs; nested-by-Package for Sarah-scale.
9. **Overlays render as header chips + body bands.** Paused is the most visible; DLP / Retention subtle; Dispute loud.
10. **Every quick-action has a voice equivalent.** No tap-only paths.
11. **A separate Home screen exists at the app level**, covering all projects (morning brief, cross-project summaries, rollups). Project screen is one-of-many; Home is the overview. Home design is its own document — see §12.

---

## 11. Remaining Open Items

1. **Canvas full-width behaviour** — middle-pane default is locked per §10 #6. When canvas needs the full horizontal space for a big visualisation (e.g. a project comparison table, a Gantt, a map), does it hide the agent chat or keep both visible? Parked for post-MVP canvas work.

**Resolved after Paul's review (2026-04-19):**
- Sub-handling → GC compliance requirements (prequal, COI, training) live inside **People meta-tab**, on the GC contact drill, as a "Requirements of this GC" panel. Prequal-deadline flags surface on main Dashboard's "Needs your call" when due.

---

## 12. Home Screen — the cross-project surface (follow-on design pass)

The Project screen is project-scoped. Kerf also needs a **Home screen** at the app level — the default landing after login, covering all active projects.

**What Home surfaces (scoping outline, not full design):**

- **Morning brief** — per `PRODUCT_VISION §7`. Cross-project risk score, weather, expiring certifications, yesterday's open corrective actions, today's schedule across all sites, job-cost status across active projects, toolbox talks ready.
- **Active projects summary** — a card per active project with state chip, key metric (outstanding invoice, days remaining, % complete), most-urgent signal. Clicking drills into that Project's screen.
- **"Needs your call" aggregate** — pulled from every project's main Dashboard's "Needs your call" panel, deduplicated + prioritised.
- **Pipeline** — leads and quoted projects, so Sarah can scan "what might turn into revenue this month."
- **Cash overview** — invoiced vs. paid across projects, upcoming payment milestones.
- **Canvas entry point** — ad-hoc questions that span all projects (e.g., *"which of my jobs is at risk of losing money this month?"*).

**How Home relates to the icon rail:**

The icon rail currently sits on the left: Chat · Projects · Workers · Quotes · Inspections · Equipment · Settings. Home likely becomes the **default surface** (top of icon rail) that the contractor lands on after login. Projects becomes a filterable list view that drills into individual Project screens.

**What Home does NOT try to do:**

Home is not a replacement for per-project detail. It summarises and routes. The Project screen is where the work actually lives.

**Status:** Scoped for its own design document. Referenced here so the Project screen can be designed with clear boundaries — anything cross-project belongs on Home, not crammed into the per-project view.

---

## 13. What This Enables

With this audit in place, every future vertical slice has:
- A specific meta-tab dashboard it's contributing to.
- A specific set of quick-action cards (with MCP tools) it's implementing.
- A specific drill-through entity view it's building.
- A specific Dashboard surfacing rule for urgency.

The vertical-slices document (`docs/implementation/vertical-slices.md`, to be written next) slices horizontally across meta-tabs per persona journey — e.g., "LEAD through QUOTED for Jake" touches `Dashboard`, `Work`, `Docs`, `People` — but each slice is bounded by what's specified here.

Home screen (§12) is its own design doc and its own slice track. Will be referenced from the vertical-slices doc to ensure nothing from the cross-project surface gets implemented twice (on Home and on Project).

---

*End of audit.*
