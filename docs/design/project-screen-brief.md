# Design Brief — Project Screen

**Audience:** Claude Design (or any design agent given this brief)
**Status:** Ready to start
**Date:** 2026-04-18
**Primary deliverable:** `docs/preview/project-screen.html` — single-file HTML preview showing the Project screen across its representative states
**Secondary deliverable:** `docs/design/project-screen-ui.md` — rationale, component inventory, state-by-state design notes

---

## 1. What this is

Kerf's **Project screen** is the primary working surface for a contractor. A contractor opens Kerf, taps a project, and lands here. Everything about that project — its state, scope, people, conversations, money, documents, variations, disputes, methodology — is reachable within this screen.

Design the screen: information architecture, visual treatment, state-by-state behaviour, responsive rules, key interactions. Build it as an HTML preview first, then write the rationale.

---

## 2. Context — read before starting

In this order:

1. **`docs/PRODUCT_VISION.md`** — what Kerf is, who it's for, beliefs, personas. Pay specific attention to:
   - `§2` Beliefs (voice-first, one tool not six, conversational interface, safety is connective tissue)
   - `§3.12` Agent autonomy matrix
   - `§3.13` Voice and mobile as the primary interface
   - `§3.14` Email as a client channel
   - `§6 Principle #15` Advise, highlight, keep logical, do what you're told — **this principle governs the screen's behaviour; no auto-transitions, no blockers on inferred facts, nudges not gates**
2. **`docs/design/project-lifecycle-flow.md`** — the full state machine this screen must represent. §2 (state machine), §4 (overlays), §10 (Jake walkthrough summary)
3. **`docs/preview/work-items.html`** — the visual direction that's already established. Follow this aesthetic; don't reinvent.
4. **`docs/design/work-item-ui.md`** — WorkItem UI pattern
5. **`docs/design/methodology.md`** — methodology cascade; §9 for UI surface notes
6. **`docs/design/canonical-work-categories.md`** — WorkItems carry categories
7. **`CLAUDE.md`** (project root) — dev rules (no mocks, persona-based testing, full-stack completion)
8. **Design system reference** — look in `docs/architecture/` for any `DESIGN_SYSTEM.md` and in the `frontend/` tree for existing shadcn/ui components and Tailwind patterns. Don't invent tokens; use what's there.

---

## 3. Personas the screen must serve

Full persona details in `PRODUCT_VISION.md §5`. In summary:

### Jake Torres (primary for this screen)

Solo electrician, recently independent. Revenue ~$180K/year. Works almost entirely from his phone, on jobsites, often with dirty hands or gloves. Uses voice heavily. Zero tolerance for friction. Typical behaviour: opens Kerf in the driveway, talks to it, puts it away. Max 2 minutes before interrupted. Runs ~3 concurrent small jobs.

**Implication for this screen:**
- Must work one-handed on a phone
- Must be navigable by voice where possible
- Must show at a glance: what state, what's pending, what to do next
- Must avoid deep navigation — everything material is one-or-two taps from the screen
- Mobile-first. Desktop is a bonus.

### Sarah Chen (secondary)

Owner of a 45-person electrical firm, Atlanta. Uses Kerf from her home office evenings and from her truck during the day. Manages 6-10 active projects concurrently, reviews crew lead inputs rather than executing directly. Spends more time on dashboards and reports than Jake does.

**Implication:**
- Must scale to projects with dozens of WorkItems, multiple variations, multiple disputes, sub-contractors
- Must surface cost / margin information clearly for financial management
- Desktop usage is heavier; three-column or split-view layouts work for her

### Marco Gutierrez (secondary)

22-person concrete crew lead, Phoenix. Bilingual (Spanish/English). 5:30 AM starts. Runs 3 active projects. Heavy voice user. Morning brief matters.

**Implication:**
- Must render in Spanish when set to Spanish locale
- Morning-brief equivalent surface per project is useful
- Crew size and daily log density are higher than Jake's

---

## 4. The problem this screen solves

In Jake's pre-Kerf world, "a project" is scattered: texts with the client, a scrap of paper with the address, photos in his camera roll, a Word doc with the estimate, a receipt for the panel, a text asking "are you coming Friday?", a permit PDF in email, his mental record of "oh yeah, Kate wants the pantry outlet added."

**Kerf replaces all of that with one surface.** The Project screen is that surface. It's the home base for everything about one job.

---

## 5. Lifecycle states the screen must represent

Per `project-lifecycle-flow.md §2`:

| State | What it means | What's visible |
|---|---|---|
| `LEAD` | Inbound contact, pursuing or exploring | Minimal scope, contact info, next-action cues |
| `QUOTED` | Quote sent, awaiting response | Quote history (v1, v2...), client interactions (viewed, asked question), days-in-state age |
| `ACCEPTED` | Client has signed; contract locked | ContractVersion v1 summary, deposit invoice status, permit pending, planned start |
| `ACTIVE` | Work happening | WorkItems with progress, time entries, variations register, daily logs, photos, inspection records |
| `PRACTICAL_COMPLETION` | Substantively done, in beneficial use | PC certificate, punch list, defect reports, final invoice, DLP clock (where applicable) |
| `CLOSED` | Archived, typed reason (`completed` / `terminated_*` / `abandoned` / `lead_lost`) | Full history; revive action available |

**Overlays** (any state can carry any or all of these):

| Overlay | Visible treatment |
|---|---|
| `PAUSED` (typed: `on_hold` or `suspended`) | Distinct chip, reason, resume date or cure deadline |
| `DLP_OPEN` | Chip with DLP end date (commercial only) |
| `RETENTION_HELD` | Chip with retention % held (commercial only) |
| `DISPUTE_OPEN` | Chip with count of open disputes (n=1 typical, more possible) |

---

## 6. Information architecture

A proposed starting structure. Refine based on what works visually.

### 6.1 Persistent elements

- **Header**
  - Project title (e.g. "Kitchen Remodel — 123 Oak St")
  - Client chip (Kate Dempsey)
  - Current state chip (one, large, unmistakable)
  - Overlay chips (Paused, Dispute, DLP — if active)
  - Key financial (effective contract sum)
- **Agent panel** — always accessible (chat + voice). On mobile, a floating action button that expands to fullscreen. On desktop, a right rail.
- **Timeline spine** — chronological event log, runs down the screen or is a dedicated tab. Events: state transitions, voice notes, photos, emails (inbound + outbound), time entries, invoices, payments, variations, inspections, defect reports, client acknowledgments. Every event shows actor (human / agent), timestamp, and source (voice / email / tap).

### 6.2 Sections / tabs

Arranged by relevance. A mobile view collapses these to an accordion or a bottom nav; a desktop view may show them as a sidebar.

- **Scope** — WorkItems list with state, progress, methodology summary per item. Grouped by WorkPackage where relevant.
- **Quote** — current quote version, version history, client-view link (magic-link preview), days-in-state, "draft revision" action.
- **Variations** — register (V1, V2, V3...), each with state chip, line items, sum delta, approval status.
- **Financials** — contract sum (original), effective sum (v1 + approved variations), invoices (deposit, interim, final), payments, outstanding balance. For Sarah: margin tracking vs. estimate.
- **Disputes** — open and historical. For each: subject, amount in dispute, state, resolution path.
- **People** — contractor (Jake), client(s), subs, inspectors, any other contacts tied to the project.
- **Documents** — attached files: plans, contracts, photos, permits, inspection records, COIs, signed quotes, approved variations.
- **Methodology** — current project-level methodology; cascade into WorkPackages and WorkItems; insights applied.
- **Daily logs** — chronological log narrative (relevant during ACTIVE).

### 6.3 Key actions — state-aware primary affordance

Each state should have a dominant next-action CTA, plus secondary actions.

| State | Primary action | Secondary actions |
|---|---|---|
| `LEAD` | Capture scope (voice) | Draft quote, schedule site visit, mark lost |
| `QUOTED` | View client status | Respond to client question, issue revision, record verbal acceptance, withdraw |
| `ACCEPTED` | Send deposit invoice | Draft permit, order materials, confirm start date |
| `ACTIVE` | Log time / Daily log | Draft variation, log inspection, send interim invoice, pause, declare PC |
| `PRACTICAL_COMPLETION` | Send final invoice | Capture punch item, resolve defect, close project |
| `CLOSED` | — | Revive |

Secondary actions should be discoverable but not cluttered. Consider a "+ Action" menu or contextual buttons per section.

---

## 7. Design principles for the screen

1. **State and overlays visible at a glance.** From the header, Jake should know in one second: what state, what's overlaid, how much money's at stake, what's outstanding.
2. **Agent panel always accessible.** Voice / chat throughout — the contractor can ask "draft the final invoice" or "what did Kate's last email say?" without leaving the screen.
3. **Mobile-first, voice-native.** One-handed, dirty-gloved operation. Voice initiates everything that can be initiated by voice.
4. **Operator Principle #15 visible in the UX.** Language bias — Kerf "suggests" / "drafts" / "proposes"; operator "approves" / "sends" / "declares". No buttons that say "Kerf will automatically do X" for consequential actions.
5. **Timeline is the spine.** Everything happens in time; the timeline is how Jake reconstructs what happened. Make it searchable and filterable.
6. **One tap to any key action.** Sending a quote from LEAD, logging time from ACTIVE, sending an invoice, declaring PC — each is one tap from the Project screen (with confirmation steps where consequential).
7. **State is reason, not just label.** When a state has a "why" (especially overlays with typed reasons), surface it. "Paused — owner on vacation until Apr 28" beats "Paused".
8. **Visual density appropriate to screen size.** Phone: minimal chrome, maximum content. Desktop: can show more at once, but never overwhelming.
9. **Safety is connective, not bolted on.** Per Product Vision — safety data enriches other features. Expiring certs, open hazard reports, incident history all surface on the Project screen where relevant, not in a separate silo.

---

## 8. Responsive behaviour

- **Mobile (primary, 375-428px wide):** single-column, tabs collapse to vertical sections or a segmented control, agent panel is a floating button that expands to fullscreen chat.
- **Tablet (768-1024px):** two-column — Project content + agent panel.
- **Desktop (1280px+):** three-column — sidebar nav + Project content + agent panel.

---

## 9. Deliverables

### 9.1 `docs/preview/project-screen.html`

Single-file HTML preview with inline Tailwind (use the Tailwind CDN or inline compiled CSS to match the precedent of `work-items.html`). Shows the Project screen in **six representative states**, each fully rendered with realistic data. Use a state picker at the top (tabs or a dropdown) to switch between them:

1. **`LEAD`** — Jake's first scope capture from a voice session. Address on file (123 Oak St), client contact (Kate Dempsey), a handful of provisional WorkItems from the kitchen-remodel walkthrough in `project-lifecycle-flow.md §10`. Primary action: "Draft quote".
2. **`QUOTED`** — `Quote v1` sent 2 days ago, Kate viewed 4 hours ago, she asked a question yesterday (inbound email on the timeline). Draft response half-drafted by the agent, awaiting Jake's approval. Revision to `v2` is imminent.
3. **`ACCEPTED`** — `Quote v2` accepted Monday 8:15am. Deposit invoice ($8,520) drafted and sent Monday 11am. Kate paid Monday 3pm. Permit application drafted Monday afternoon. State is pre-execution — no time entries yet.
4. **`ACTIVE`** — Mid-job Friday evening. Demolition done, wire pulled, panel installed, rough inspection passed 3pm today. Three time entries. Daily logs from Thu and Fri. One Variation (V1) in `Draft` — pantry outlet + USB + pendant colour, not yet sent. Primary action: "Log time" / "Issue V1".
5. **`ACTIVE + PAUSED`** — Suspended overlay with typed reason `contractor_non_payment`. Original state is `ACTIVE`. Cure deadline Apr 28. Dispute is NOT open (separate overlay). Shows the state + overlay interplay clearly.
6. **`PRACTICAL_COMPLETION`** — Wed 10am, Jake declared done. All WorkItems at 100%. V1 approved; black pendants and USB outlet installed. Final invoice ($6,065) drafted and sent. Kate paid Thursday. Three months later: one resolved defect (flickering can). No DLP overlay (residential, no retention).

Each state annotation (as inline comments or callouts in the preview) explaining:
- What's intentional about the treatment
- What's a design decision worth reviewing
- What's an open question

### 9.2 `docs/design/project-screen-ui.md`

Rationale + component inventory + state-by-state notes.

Structure:
- §1 Purpose
- §2 Information architecture decisions (what's tabbed vs. inline vs. modal)
- §3 Component inventory (which shadcn/ui components, any new components proposed)
- §4 State-by-state design notes (one per state in the preview)
- §5 Responsive behaviour
- §6 Agent panel placement and behaviour
- §7 Accessibility notes
- §8 Open questions

---

## 10. Constraints and conventions

- **Tech:** React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui. Don't propose components that require adding a new dependency unless justified.
- **No mocks of internal services.** Any data shown in the preview should be the representative data from `project-lifecycle-flow.md §10` (Jake's kitchen remodel — Kate, 123 Oak, $14,200, V1 +$385, etc.) to keep it realistic and consistent with the design doc.
- **Preview pattern.** Inline HTML + Tailwind (CDN or compiled). Single file. Mirror the precedent set by `docs/preview/work-items.html`.
- **Do not commit** — the human handles commits.

---

## 11. Out of scope for this brief

- The client portal (Kate's view) — separate design pass, derives from this one
- The Quote document itself (the PDF / magic-link artefact) — separate design pass, depends on this
- The projects-list entry screen — a minimal entry is assumed; detailed design can wait
- Reporting / analytics dashboards
- Team / settings / admin screens
- The agent panel's internal conversation UX — design its footprint and affordances on the Project screen, not its internal turns

---

## 12. Method

- Read §2's file list before designing.
- Build visually first (HTML preview), then write the rationale.
- Use Jake's kitchen-remodel data as the running example (§9.1 specifies which state shows which moment).
- Ask questions if anything is ambiguous — don't guess on anything load-bearing.
- Call out anywhere the lifecycle model (in `project-lifecycle-flow.md`) needs refinement based on what the UI surfaces. Design often exposes design gaps.
- Surface open questions explicitly in the rationale doc (§8).

---

## 13. Success criteria

- Jake, handed the preview on his phone, can identify the Project's state and next action within 5 seconds.
- The screen represents all six states in the preview without contorting.
- Overlays (Paused, Dispute, DLP) compose cleanly with base states.
- The agent panel is always reachable without interrupting the Jake's current task.
- Nothing on the screen violates Principle #15 (no auto-transitions, no blockers on "should-have" conditions).
- The rationale doc lets a fresh developer understand every deliberate choice and every open question.

---

*End of brief.*
