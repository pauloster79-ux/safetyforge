# Research: Competitor State Handling Patterns

**Purpose:** Input for `docs/design/project-lifecycle-flow.md`. How existing contractor-software models lifecycle states, transitions, and edge cases.
**Date:** 2026-04-17

---

## Per-product summaries

### Procore (mid-to-large GCs)

- **Two layers:** `Project Status` (Active/Inactive binary) + `Stage of Construction` (Bidding / Pre-Construction / Course of Construction / Warranty / Post-Construction + customisable)
- **Change Order statuses:** Draft / Pending - In Review / Pending - Revised / Approved / Rejected
- **Lock-on-approval cascade:** Approved CO → SOV locked, CO cannot be deleted, Change Event line items lock. To edit a non-latest CO, revert subsequent COs to Draft working backward (rigorous but punitive)
- **No explicit On Hold** — widely-cited gap; users overload Inactive as proxy
- **Reactivation:** Inactive → Active, no data loss
- Sub-object states entirely decoupled from parent
- No first-class client portal — owner is another user

### Buildertrend (residential, merged with CoConstruct)

- **Job states:** Pre-Sale (Lead) / Open (Active) / Warranty / Closed, plus separate Lead Opportunity object
- **First-class Warranty state** — residential-industry best practice; dedicated Warranty tab with Claim workflow
- **Lost lead:** Mark lost, data retained; no revive pattern — returning client = new lead
- **On hold:** No explicit state; teams use Pre-Sale/Open flag + custom fields
- Light enforcement on read-only; closed jobs drop from default menu but not hard-locked
- Rich client portal with builder-controlled feature visibility per state
- 4-state model shows age for complex scenarios

### Autodesk Construction Cloud (ACC / Autodesk Build)

- **Project-level:** Active + Archived only (thin)
- **Cost Management lifecycle** (budget items + COs): draft/pending/approved flows
- **Budget Snapshots** — immutable point-in-time records, comparable over time (uncommon and powerful; closest to Git-style financial capture)
- **Forecast tool:** separates Revised Budget / Work Completed / Actual Costs / Forecast-Final
- Relies on Schedule tool phase tracking for stage concepts

### CMiC (enterprise ERP)

- PMI-style phases: Initiation / Planning / Execution / Monitoring-Control / Closeout
- Highly customisable workflow engine per tenant — users define their own state machine
- Single-database ERP
- Thin public docs (enterprise sales motion)

### JobTread (residential GC)

- **Pipeline-based** rather than fixed states; common: Lead / Estimate / Proposal Sent / Signed / Pre-Construction / Production / Closeout / Completed
- **Workflow Automations engine (2025)** — triggers advance pipeline, create to-dos, load schedule templates
- **Auto-decline on expiry** for proposals (rare, thoughtful)
- Document statuses visible to customer (estimates, COs); signed → contract view
- Trigger-based model is more flexible than Buildertrend's fixed states

### Knowify (small-to-mid trade contractors)

- **Contract states:** Lead → Bidding → Out for Signature → Active → Pending Changes → Completed
- **Automatic transitions** on events (draft saved, sent, signed); also manual made-active toggle
- **Strong line-item lock on signature** — changes MUST go via CO
- **Pending Changes** sub-state: jobs still track costs/revenue but can't invoice full contract until COs resolved
- Dedicated customer portal with Approved $ vs Pending approval $ split
- **Clearest state machine** of any researched product

### Contractor Foreman

- Work Order: Open / Estimating / Submitted / Approved / Completed
- Project: Pending / In Progress / Completed (generic)
- Custom project phases (user-defined) compensate for thin state model
- Close-out is workflow-driven (task lists), not state-driven
- Light enforcement on read-only

### Houzz Pro (residential designers + contractors)

- **Lead stages:** New / Followed Up / Connected / Meeting Scheduled / Proposal/Estimate Sent / Won — built-ins uneditable, New and Won required anchors
- **Proposal/Estimate states:** Draft / Sent / Approved / Declined / Paid / Partially Paid / Invoiced / Partially Invoiced
- **Approved/Paid/Invoiced cannot be deleted or archived** — must reopen for editing (strong audit trail via explicit un-approval)
- **Snooze action** — defer without changing stage (unusual)
- Sub-object state auto-flips (product added to project → Project Tracker updates)

### ServiceTitan (service trades, emerging construction)

- **Layered:**
  - Appointment: Scheduled / Dispatched / Working / Done / Canceled / Hold
  - Job: progress from % appointments Done; Hold and Canceled at whole-job level
  - Project: container for related jobs; customisable statuses + sub-statuses
  - Invoice: Pending / Posted (locked — strongest financial close pattern)
- **Automatic transitions** driven by field events (dispatching, arriving, completing)
- **First-class Hold** at both job and appointment level; "on hold purgatory" is a known pain point
- Three-entity model (Job / Appointment / Technician) separates scheduling, execution, deliverable
- Posting lock + audit-trail unposting for corrections

### Jobber (service trades small biz)

- **Quote:** Draft / Awaiting Response / Changes Requested / Approved / Converted / Archived
- **Job:** Active / Late / Unscheduled / Action Required / Requires Invoicing / Archived
- **Invoice:** Draft / Awaiting Payment / Past Due / Paid / Bad Debt
- **`Action Required`** — explicit stalled-but-active state (rare and honest; extend with typed reasons for Kerf)
- **Late visit vs job-on-hold** — distinct; visit-level staleness vs job-level stall
- Automatic transitions from visit events
- Progress invoicing = job open while partially billing

### JobNimbus (contractors, strong in roofing)

- **Stages (fixed, not renamable):** Lead / Estimating / Sold / In Production / Accounts Receivable / Completed + Lost
- **Statuses** (customisable per stage) give teams local vocabulary
- **Days In Status** counter on every card — explicit rot detection
- **Lost → re-entry: all previous dates clear**, Estimating reset (engineered for revive-as-fresh-deal analytics)
- Light enforcement; emphasis on visibility not locking

---

## Cross-product synthesis

### Common patterns
1. **Separation of lifecycle status from phase/stage label** (Procore, JobNimbus, Buildertrend)
2. **Lock-on-signature for scope** — universal; Knowify strictest, Procore strongest for commercial
3. **Change orders as the only legitimate scope-change path** — universal
4. **Approved/Posted invoices immutable** — ServiceTitan cleanest
5. **Sub-object states operate semi-independently** of parent state
6. **Pre-sale Lead pipelines separate** from project lifecycle (except Procore — expects CRM elsewhere)

### Divergent approaches
| Concern | Approach A | Approach B | Why divergent |
|---|---|---|---|
| On hold | Explicit state (ServiceTitan, Jobber) | Overloaded via Inactive (Procore, ACC) | Service trades have routine stalls; long builds rarely truly pause |
| State customisation | Fixed enum (Buildertrend, Houzz anchors) | Fully user-defined (CMiC, JobTread) | Enterprise wants tailoring; SMB wants opinionated defaults |
| Warranty | First-class (Buildertrend) or stage (Procore) | Implicit (most service trades) | Residential has contractual warranty periods; service trades usually don't |
| Lost/revive | Fresh record (most) | Stage re-entry w/ date reset (JobNimbus) | Roofing cycles are long; honest about deal-age rot |

### Gaps no one handles well (Kerf's openings)

1. **On-hold as first-class with typed reason codes** — only Jobber/ServiceTitan acknowledge, neither asks WHY or automates re-engagement
2. **Revive vs new for returning clients** — JobNimbus gets closest but still forces stage re-entry
3. **Variation-approved-but-out-of-scope** — Knowify's Pending Changes is elegant but binary
4. **Closeout as timed phase** — everyone has closeout tasks; nobody has contractual duration ("SC + 30 days → auto-close unless open items")
5. **Warranty period auto-expiry** — Buildertrend has state but no automatic transition on expiry
6. **Quote expiry with preserved context** — JobTread auto-declines but expired quote becomes dead
7. **Abandoned/cancelled mid-execution distinct from closed-complete** — important for margin analysis
8. **Scope lock graduation** — binary locked/unlocked is crude; real life has "locked for pricing / editable for description"
9. **Client-portal view explicitly modelled per state** — no product *requires* state-specific client content
10. **Provenance on state transitions** — everyone logs who, nobody ties to the event that caused it

### Recommendations for Kerf's state machine

- **Adopt Knowify's rigour** on signature-driven auto-transitions with scope lock
- **Adopt JobNimbus's split** of fixed Stages (for reporting) vs custom Statuses (for team vocabulary)
- **Adopt ServiceTitan's model** of automatic field-event-driven transitions
- **Adopt Jobber's `Action Required`** honesty about stalled work — extend with typed reasons
- **Avoid Procore's revert chain** for CO edits (punitive)
- **Avoid Buildertrend's single-dimension states** (don't scale beyond simple residential)
- **Fill the gaps above** — especially typed-hold, timed closeout, warranty auto-expiry, revive-with-context, state-dependent client-portal contracts
