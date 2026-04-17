# Competitor Data Model Analysis

Comparison of major construction management platform data models against the Kerf ontology. Research conducted April 2026.

---

## 1. Per-Platform Findings

### 1.1 Procore (Enterprise Leader)

**Financial data model -- the most mature in the industry.**

Procore's financial architecture introduces several concepts absent or underspecified in Kerf:

**Work Breakdown Structure (WBS) with custom segments.** Procore moved beyond simple cost codes to a configurable WBS system. A budget code has default segments (cost code, cost type, optional sub job) but companies can create up to 10 custom segments and arrange them in any order. Segments can be flat (a list) or tiered (hierarchical tree with parent/child). This is significantly more flexible than Kerf's WorkCategory tree.

**Prime Contract vs Commitment distinction.** Procore explicitly separates the upstream contract (Prime Contract -- the agreement with whoever is paying you) from downstream commitments (Subcontracts and Purchase Orders to your subs/vendors). Both are first-class entities with their own Schedule of Values, change order workflows, and invoicing paths. Kerf has a single Contract entity and lacks the upstream/downstream distinction. Kerf's model-reality-test identified inbound sub invoices as a gap (G1), and Procore's architecture shows the standard industry solution: separate the Prime Contract from Commitments.

**Tiered change order workflow.** Procore supports 1-, 2-, or 3-tier change management:
- Tier 1: Change Order only
- Tier 2: Potential Change Order (PCO) then Change Order
- Tier 3: Change Event then PCO then Change Order (CCO)

Each tier adds approval steps. Kerf has a single Variation entity. For simple contractors this is fine, but for commercial work the multi-tier workflow is important. A Change Event (the trigger -- an architect's revised drawing, a site condition) is distinct from a Potential Change Order (the cost estimate) which is distinct from the executed Change Order (the contractual amendment).

**Schedule of Values (SOV) as a first-class concept.** Each commitment has a general SOV (cost code level breakdown) and optionally a Subcontractor SOV (detailed line-item breakdown provided by the sub). The SSOV is what carries through to invoicing. Kerf's InvoiceLine covers the invoicing side but lacks the SOV structure that connects contract scope to billing milestones.

**Observations as separate from Inspections.** Procore splits these into two distinct tools:
- Inspections are template-driven checklists (safety, quality, commissioning)
- Observations are ad-hoc items assigned to someone for resolution (deficiencies, safety hazards, commissioning items, warranty items, work to complete)

Observations have their own lifecycle (Initiated, Ready for Review, Closed) and are typed (Safety Hazard, Safety Violation, Near Miss, Quality, Commissioning, Warranty, Work to Complete). Kerf consolidates these under Inspection + InspectionItem + CorrectiveAction. The Procore approach of separating template-driven checklists from ad-hoc tracked items is arguably cleaner.

**Daily log with 12+ sub-types.** Procore's daily log is not a single record but a collection of typed sections: Manpower, Weather (auto-populated from weather APIs), Notes, Deliveries, Equipment, Phone Calls, Accidents, Scheduled Work, Productivity, Safety Violations, Plan Revisions, Quantities, Dumpster, Waste, Delays, and Inspections. Each is a distinct sub-entity within the daily log. Kerf has DailyLog with child entities (MaterialDelivery, DelayRecord, VisitorRecord) but fewer sub-types.

**Concepts Procore has that Kerf is missing:**
- Purchase Order as a distinct commitment type (separate from Subcontract)
- Change Event (the triggering event, separate from the cost change)
- Potential Change Order (cost estimate stage before formal change)
- Schedule of Values / Subcontractor SOV
- Bid Package / Bidding (soliciting bids from subs/vendors)
- Drawing Management (versioned drawings, markups, revisions)
- Meeting Management (agendas, minutes, action items)
- Transmittal (formal document transmission records)
- Punch List as a separate tool (not just DeficiencyList)
- Manpower log (headcount per company per day, separate from TimeEntry)
- Quantities log (installed quantities tracked daily, separate from WorkItem progress)

---

### 1.2 JobTread (Fastest-Growing Competitor)

**Estimate-to-budget continuity is the core differentiator.**

JobTread's data model centres on a single financial truth that flows from estimate through to job costing:

**Cost Catalog with Cost Items and Cost Groups.** The catalogue is a reusable library of cost items (individual materials, labour tasks) grouped into cost groups (trade-level or phase-level groupings). Cost items carry a default cost and a markup/margin percentage, so pricing is calculated automatically. This is similar to Kerf's WorkCategory + Item concept but more tightly integrated -- the catalog item includes both the cost structure and the pricing logic.

**Estimate becomes Budget in one step.** When a client accepts a proposal, the estimate line items become the project budget. There is no separate "create budget from estimate" step -- the data structure is the same entity transitioning states. This validates Kerf's DD-06 approach of not having separate Estimate and Budget entities. However, JobTread added a formal Estimate entity (with versioning via SUPERSEDES), and the Kerf model-reality-test acknowledged this was needed.

**Budget depletion tracking.** Each cost item in the budget shows real-time depletion (how much of the budgeted amount has been committed via POs or spent). Colour-coded indicators show items that are over/under budget. Kerf can compute this from WorkItem estimates vs TimeEntry/Invoice actuals, but JobTread's model makes depletion a first-class tracked property.

**Payment and Bill Schedules.** JobTread recently added payment schedules (for customer invoicing) and bill schedules (for vendor/sub payments) as entities attached to documents. This allows milestone-based billing, progress billing, and scheduled payment plans. Kerf has PaymentApplication but not a generalised payment schedule concept.

**Vendor Portal.** Unique portal links generated per vendor per document. Vendors can view and approve orders, submit invoices, and communicate through the portal. Kerf has AccessGrant for external access but no specific vendor/sub portal model.

**Concepts JobTread has that Kerf is missing:**
- Cost Catalog as a reusable pricing library (Item is close but lacks pricing/margin data)
- Bill Schedule (scheduled payments to vendors/subs)
- Payment Schedule (scheduled invoicing to clients)
- Budget depletion tracking as explicit state
- Vendor portal with per-document authentication

---

### 1.3 Buildertrend (Residential Focus)

**Selections and the client experience are the differentiator.**

Buildertrend (which absorbed CoConstruct in 2022) has the most developed homeowner-facing model:

**Selections with Allowances.** A Selection is a client decision point -- "choose your kitchen countertop." Each selection has:
- An allowance amount (the budget set in the contract)
- Predefined choices (specific products with prices) or open-ended choices
- A client approval workflow
- Automatic change order generation when the selection exceeds the allowance

The allowance can be "single" (unique to one selection) or "shared" (a budget pool across multiple selections -- e.g., a $5,000 lighting allowance shared across kitchen, bathroom, and bedroom lighting selections).

This is a concept Kerf does not model at all. For residential and custom home work, selections and allowances are a core workflow. The Kerf model has WorkItem with materials_allowance but no concept of a client-facing selection with predefined choices, allowance tracking, and overage-to-change-order flow.

**Estimate vs Proposal distinction.** The Estimate is the internal cost breakdown. The Proposal is the client-facing document generated from the estimate, with introductory text, terms, and signature collection. Updates to the estimate flow through to proposals, selections, change orders, and invoices without re-entry. Kerf does not distinguish between the internal cost view and the client-facing proposal.

**Draw Schedule for fixed-price jobs.** Divides the total contract into scheduled draws aligned with project milestones. When the estimate is finalised and sent to the budget, draft invoices are automatically created from the draw schedule. This is more structured than Kerf's PaymentApplication, which is a manual process.

**Concepts Buildertrend has that Kerf is missing:**
- Selection entity (client decision point with choices)
- Allowance entity/property (budget pool for client selections, single or shared)
- Proposal as a client-facing document generated from the estimate
- Draw Schedule (automated invoice generation from milestone schedule)
- Shared allowance pools across multiple selections

---

### 1.4 CoConstruct (Historical -- now merged into Buildertrend)

**Purpose-built for custom home builders. Best-in-class selection management.**

Though now merged, CoConstruct's model is worth studying because it solved problems Kerf faces:

**Three financial concepts per line item.** Every item in CoConstruct has:
- Budget (your internal cost)
- Client Price (what the client pays -- budget plus markup)
- Allowance (what the client has available to spend, visible to them)

The relationship between these three numbers drives the entire financial workflow. When a client makes a selection that exceeds the allowance, the overage automatically flows to a change order. Kerf has cost data on WorkItem but no explicit separation of internal cost, client price, and allowance.

**Fixed Price vs Open Book project types.** CoConstruct supported two fundamental financial structures:
- Fixed Price: client sees allowances and selection prices, not your costs
- Open Book (cost-plus): client sees actual costs plus your markup percentage

The visibility rules change based on this project-level setting. Kerf's permission model (role-based depth) could support this, but it is not modelled as a project-level financial structure choice.

**Specification vs Selection distinction.** Specifications are items that are automatically included (framing, excavation -- no client decision needed). Selections are items where the client must choose (countertops, flooring, fixtures). Both live on the same estimate but have different workflows. Kerf treats all WorkItems the same regardless of whether a client decision is required.

**Selection deadlines tied to schedule.** Selection due dates can be linked to schedule milestones ("choose your tile by 4 weeks before bathroom rough-in starts") or set as fixed dates. Late selections trigger alerts. This connects the selection workflow to the project schedule in a way Kerf does not model.

**Concepts CoConstruct modelled that Kerf is missing:**
- Three-number model per item (budget / client price / allowance)
- Project financial structure type (fixed price vs open book/cost-plus)
- Specification vs Selection distinction on work items
- Selection deadline linked to schedule milestone

---

### 1.5 Fieldwire (Task Management Focus)

**Plan-centric task management with spatial awareness.**

Fieldwire's data model is narrow but deep in task management:

**Tasks pinned to plan locations.** Every task has optional X/Y coordinates on a specific plan sheet. The task appears as a coloured pin on the drawing, visible to anyone viewing that sheet. Pin colour changes with status. Kerf has Location and SafetyZone but no concept of pinning work items or tasks to specific coordinates on a drawing.

**Custom task statuses (up to 20).** Default statuses are P1, P2, P3, Completed, Verified. But projects can define up to 20 custom statuses that match their workflow (e.g., "Waiting on Predecessor", "Ready for QA", "Verified"). Each status has a colour that maps to the pin on the drawing. Kerf has fixed status progressions on WorkItem and Inspection.

**Categories as trades.** Task categories map to trades but are fully customizable per project. This is similar to Kerf's WorkCategory but flatter and more flexible.

**Checklists within tasks.** Tasks can contain checklists (stepped sub-items) and linked forms. The checklist tracks who checked off each item and when. This is similar to Kerf's InspectionItem pattern but applied to general work tasks, not just inspections.

**Forms as a separate entity.** Forms are reusable templates that can be linked to tasks. A form has its own status and completion tracking independent of the task. Kerf does not have a general-purpose Form entity -- inspections serve this role for safety/quality but not for general field documentation.

**Concepts Fieldwire has that Kerf is missing:**
- Spatial pinning of tasks to plan coordinates
- Drawing/Plan as a first-class entity with sheets and versions
- Custom task statuses (configurable per project)
- Form as a reusable template linkable to tasks
- Checklist as a sub-entity of general tasks (not just inspections)

---

### 1.6 SafetyCulture / iAuditor (Inspection Platform)

**Template-driven inspection with intelligent conditional logic.**

SafetyCulture's inspection model is more sophisticated than Kerf's in several ways:

**Smart Fields and Dynamic Fields.** Template items can be conditionally shown or hidden based on responses to previous items. Dynamic Fields allow repeating groups (e.g., an employee register section that repeats for each person on site). Kerf's InspectionItem is flat -- no conditional logic or dynamic repeating groups.

**Actions vs Issues distinction.** SafetyCulture separates:
- Actions: structured tasks created from inspection findings, with assignee, priority, due date, and completion tracking. Can be created mid-inspection or standalone.
- Issues: lightweight, ad-hoc observations reported by anyone via the app or QR code. Lower friction than a full inspection.

Kerf has CorrectiveAction (similar to Actions) and HazardReport (similar to Issues) but does not draw the distinction as cleanly. The QR-code-based issue reporting for frontline workers is a UX pattern worth noting.

**Asset-linked inspections.** Inspections can be linked to specific assets (equipment, vehicles, facilities). The asset maintains an inspection history, and recurring inspection schedules can be set per asset. Kerf has EquipmentInspectionLog but does not generalise this to all asset types.

**Recurring inspection schedules.** Schedules generate inspections automatically at configured frequencies (daily, weekly, monthly, custom patterns). Missed or late inspections are flagged. Kerf has no scheduling entity -- inspections are created manually.

**Template inheritance and auto-sharing.** Templates carry sharing/permission settings that are inherited by inspections created from them. This means inspection access is partly determined by the template, not just the project. Kerf's permissions are project-based only.

**Concepts SafetyCulture has that Kerf is missing:**
- Conditional/smart fields in inspection templates
- Dynamic repeating groups in inspections
- Recurring inspection schedules with missed/late tracking
- Asset entity as a generalised inspectable thing (beyond just Equipment)
- QR-code-based lightweight issue reporting
- Template-level permission inheritance

---

## 2. Cross-Platform Patterns

Patterns that appear across multiple competitors and differ from Kerf's approach:

### 2.1 Upstream vs Downstream Contract Separation

**Who does it:** Procore (Prime Contract vs Commitment), JobTread (Customer documents vs Vendor documents), Buildertrend (Client contract vs Sub/vendor POs)

**The pattern:** Every platform separates the contract with whoever is paying you (upstream) from commitments to whoever you are paying (downstream). These have different workflows, different document types, and different visibility rules.

**Kerf's gap:** Kerf has a single Contract entity and Invoice with a direction indicator suggested in the model-reality-test. The industry standard is to treat these as structurally different entities, not the same entity with a direction flag. The upstream contract has retention, draw schedules, and a client-facing SOV. Downstream commitments have purchase orders, subcontracts, sub invoicing, and lien waivers.

### 2.2 Schedule of Values as the Billing Bridge

**Who does it:** Procore, Buildertrend (draw schedule), JobTread (payment schedule)

**The pattern:** An SOV is the agreed-upon billing breakdown that sits between the contract and individual invoices. It defines what milestones or line items can be billed, and invoices reference SOV lines. The SOV may differ from the internal cost breakdown.

**Kerf's gap:** Kerf goes directly from WorkItem to InvoiceLine. There is no intermediate structure that defines the billing breakdown agreed with the client. For commercial work, the SOV is a critical document that defines how progress billing works.

### 2.3 Selections and Allowances (Residential)

**Who does it:** Buildertrend, CoConstruct (historical), JobTread (allowances in proposals)

**The pattern:** For residential/custom work, clients choose finishes, fixtures, and products. Each choice point has a budgeted allowance. The client sees their choices, the allowance, and the price impact. Overages automatically generate change orders.

**Kerf's gap:** Kerf has no Selection, Allowance, or client-choice workflow. For the residential market (Jake, Dave, the landscaper from the model-reality-test), this is a significant gap. The "selection to change order" flow is table stakes for residential construction software.

### 2.4 Cost Catalog / Pricing Library

**Who does it:** JobTread (Cost Catalog), Procore (Cost Codes + Cost Library), Buildertrend (Estimate templates)

**The pattern:** A reusable library of priced items with default costs, units, and markup percentages. Building an estimate means selecting items from the catalog, adjusting quantities, and the pricing calculates automatically.

**Kerf's gap:** Kerf has Item (global shared catalogue) but it only carries a name, description, and default unit -- no pricing data. WorkItem carries the cost, but there is no reusable "priced item" template. The contractor must re-enter pricing data for each estimate. A PricedItem or CatalogItem that carries default cost and markup would close this gap.

### 2.5 Multi-Tier Change Management

**Who does it:** Procore (1/2/3-tier), Buildertrend (Change Event to Change Order), JobTread (change orders from budget)

**The pattern:** Change management has multiple stages: the triggering event (site condition, design change), the cost estimation (what will this cost?), and the formal amendment (signed change order). Larger projects need all three stages; smaller projects need just the last one.

**Kerf's gap:** Kerf has a single Variation entity. For small contractors this is fine. For commercial work (Sarah's scenario), the trigger-estimate-execute pipeline is industry standard.

### 2.6 Drawing/Plan Management

**Who does it:** Procore (Drawings tool), Fieldwire (Plans with spatial tasks), Buildertrend (Plans)

**The pattern:** Drawings/plans are versioned, organised by discipline (architectural, structural, MEP), and serve as a spatial canvas for pinning tasks, observations, and inspections.

**Kerf's gap:** Kerf has Document but no specific Drawing/Plan entity with versioning, sheet management, or spatial coordinate support. This is not critical for the safety-first MVP but becomes important for project management features.

### 2.7 Daily Log Sub-Types

**Who does it:** Procore (12+ typed sections), Buildertrend (daily log with typed entries)

**The pattern:** The daily log is not a monolithic record but a collection of typed entries: manpower, weather, notes, deliveries, equipment hours, phone calls, delays, quantities installed, safety violations, visitors. Each type has its own fields and workflow.

**Kerf's gap:** Kerf has DailyLog with MaterialDelivery, DelayRecord, and VisitorRecord as sub-entities, but is missing: Manpower (headcount by company), Weather (auto-populated), Phone Calls, Quantities (installed quantities separate from WorkItem tracking), and Equipment Hours as daily log sub-types.

### 2.8 Recurring/Scheduled Inspections

**Who does it:** SafetyCulture (rich scheduling), Procore (inspection scheduling)

**The pattern:** Inspections can be scheduled to recur at defined frequencies. Missed or late inspections generate alerts. This is critical for regulatory compliance (e.g., weekly scaffold inspections, daily excavation inspections).

**Kerf's gap:** Kerf has no inspection scheduling entity. Given that Kerf's core value proposition is safety compliance, and many regulations require inspections at defined frequencies, this is a notable gap. An InspectionSchedule entity that generates Inspection instances on a recurring basis would align with the regulatory knowledge graph.

---

## 3. Specific Recommendations for Kerf's Ontology

### High Priority (addresses gaps identified across 3+ competitors)

**R1. Split Contract into PrimeContract and Commitment.**
Rename the existing Contract to PrimeContract (upstream -- with the client). Add Commitment as a new entity with subtypes Subcontract and PurchaseOrder (downstream -- to subs and vendors). Both carry their own SOV, change order chain, and invoicing workflow. This resolves model-reality-test gaps G1 (inbound sub invoices) and G2 (WorkPackage to sub link). The Commitment replaces the need for Invoice.direction.

**R2. Add ScheduleOfValues entity.**
An SOV sits between a PrimeContract or Commitment and its Invoices. SOV lines define the billing breakdown. Each InvoiceLine references an SOV line, not a WorkItem directly. This decouples the internal cost structure from the client-facing billing structure, which is critical for commercial work.

**R3. Add Selection and Allowance concepts.**
For residential work:
- Add a `requires_selection` boolean or `selection_status` to WorkItem
- Add an Allowance entity (or property on WorkItem) with budgeted amount
- Add SelectionChoice entity linked to WorkItem, carrying the chosen product, price, and client approval status
- When a SelectionChoice exceeds the allowance, auto-generate a Variation
- Support shared allowances across multiple WorkItems

**R4. Add InspectionSchedule entity.**
Links an InspectionType to a Project with a recurrence rule (frequency, day-of-week, etc.). Generates Inspection instances automatically. Tracks missed/late inspections. Connects to the regulatory graph: Regulation REQUIRES InspectionType at frequency X.

**R5. Enrich Item into CatalogItem with pricing.**
Add default_cost, default_markup_pct, and supplier fields to Item (or create a company-scoped CatalogItem that references the global Item). This enables reusable pricing libraries and faster estimating.

### Medium Priority (addresses gaps identified by 2 competitors)

**R6. Add Change Event entity.**
A Change Event is the triggering event for a scope change (architect revision, site condition, client request). It precedes and may generate one or more Variations. For simple projects, Change Events are optional. For commercial projects, they provide the audit trail from trigger to cost impact.

**R7. Add Drawing/Plan entity.**
A versioned drawing with sheets, discipline classification, and optional spatial coordinate system. Tasks, observations, and inspections can be pinned to plan locations. Not critical for safety MVP but needed for project management expansion.

**R8. Expand DailyLog sub-types.**
Add ManpowerEntry (company, headcount, hours), WeatherEntry (auto-populated), PhoneCallEntry, and QuantityEntry (installed quantities by work item) as additional DailyLog child entities.

**R9. Add conditional logic to InspectionItem.**
Support show/hide conditions on inspection template items based on responses to previous items. This is important for creating intelligent inspection checklists that adapt to site conditions.

### Lower Priority (addresses gaps identified by 1 competitor or edge cases)

**R10. Support custom statuses on WorkItem.**
Consider making WorkItem statuses configurable per project or company, rather than a fixed progression. Fieldwire's approach of up to 20 custom statuses is flexible but may add complexity.

**R11. Add project financial structure type.**
Add a `financial_structure` property to Project: "fixed_price", "cost_plus", "time_and_materials". This affects what the client can see (CoConstruct pattern) and how markup is calculated.

**R12. Add Bill Schedule and Payment Schedule entities.**
Generalise the scheduling of payments (both outbound to subs and inbound from clients) beyond the current PaymentApplication. Link schedule milestones to WorkItem completion or calendar dates.

---

## 4. Validation Points (Where Kerf's Approach is Confirmed)

### 4.1 Lifecycle over Duplication -- Validated

Kerf's principle of "a lead is a Project in early status" matches how JobTread, Buildertrend, and Procore handle project lifecycle. None of them have a separate Lead entity. The project status progression (lead, quoted, active, complete) is the industry standard.

### 4.2 WorkItem as the Atomic Unit -- Validated

Every competitor has an equivalent concept: Procore has budget line items, JobTread has cost items, Buildertrend has estimate line items, Fieldwire has tasks. The atomic unit of work that carries cost, schedule, and assignment is universal.

### 4.3 WorkPackage as Optional Grouping -- Validated

Procore's cost codes and WBS segments, JobTread's cost groups, Buildertrend's estimate categories all serve as optional groupings of work items. The "Project to WorkItem directly or via WorkPackage" pattern matches industry practice.

### 4.4 Bottom-Up Costing -- Validated

All competitors calculate totals by summing up from line items. None store independent "top-down" budgets disconnected from line items. Kerf's bottom-up costing design (DD-06) is correct.

### 4.5 Variation/Change Order as First-Class Entity -- Validated

Every competitor has a change order entity. Kerf's decision to make Variation a first-class entity with evidence chains (daily logs, photos, time entries) is well-aligned. The only enhancement needed is the optional multi-tier staging (Change Event to Variation).

### 4.6 Global-First Naming -- Differentiated

No competitor uses global-first naming. Procore uses US terms (RFI, Punch List, Change Order). Buildertrend uses US terms. Kerf's choice of ProjectQuery, DeficiencyList, and Variation is a genuine differentiator for international markets.

### 4.7 Safety as a Core Domain -- Differentiated

Among general construction management platforms, only Procore has deep safety tooling (observations, inspections, incidents). Buildertrend, JobTread, and Fieldwire treat safety as peripheral. SafetyCulture is safety-only with no project management. Kerf's integration of safety as a first-class domain within a project management platform is a genuine competitive advantage, provided the inspection and compliance models are at least as deep as SafetyCulture's (which the recurring schedule and conditional logic recommendations would help achieve).

### 4.8 Graph-Native Permissions -- Differentiated

No competitor uses graph-native permissions. All use traditional role-based access control with entity-level permission checks. Kerf's approach of "permission equals traversability plus role depth" is architecturally novel and should remain a differentiator, particularly for the GC-sub data sharing use case.

### 4.9 Regulatory Knowledge Graph -- Unique

No competitor encodes regulations as traversable graph structure. Procore and SafetyCulture provide inspection templates but the regulatory logic is hardcoded or manual. Kerf's Layer 3 knowledge graph for regulatory rules is genuinely unique in the market and should be protected as a core architectural advantage.

### 4.10 Conversation Memory and Institutional Knowledge -- Unique

No competitor models conversation memory, decisions extracted from conversations, or institutional knowledge (Insights). This is a genuinely novel capability. The pattern of capturing "I use 0.38 hours per receptacle in renovations" as a reusable Insight is not replicated anywhere in the competitive landscape.

---

## Summary Matrix

| Concept | Procore | JobTread | Buildertrend | CoConstruct | Fieldwire | SafetyCulture | Kerf Status |
|---------|---------|----------|-------------|-------------|-----------|---------------|-------------|
| Upstream/downstream contract split | Yes | Yes | Yes | Yes | N/A | N/A | **Gap -- R1** |
| Schedule of Values | Yes | Partial | Yes | No | N/A | N/A | **Gap -- R2** |
| Selections + Allowances | No | Partial | Yes | Yes | No | N/A | **Gap -- R3** |
| Recurring inspection schedules | Partial | No | No | No | No | Yes | **Gap -- R4** |
| Cost catalog with pricing | Yes | Yes | Yes | Yes | No | N/A | **Gap -- R5** |
| Multi-tier change management | Yes | No | Partial | No | No | N/A | **Gap -- R6** |
| Drawing/plan management | Yes | No | Yes | No | Yes | No | **Gap -- R7** |
| Rich daily log sub-types | Yes | No | Partial | No | No | N/A | **Gap -- R8** |
| Conditional inspection logic | Partial | No | No | No | No | Yes | **Gap -- R9** |
| Custom task statuses | No | No | No | No | Yes | No | Consider -- R10 |
| Project financial structure type | No | No | No | Yes | N/A | N/A | Consider -- R11 |
| Payment/bill schedules | Partial | Yes | Yes | No | N/A | N/A | Consider -- R12 |
| Global-first naming | No | No | No | No | No | No | **Kerf advantage** |
| Regulatory knowledge graph | No | No | No | No | No | No | **Kerf unique** |
| Conversation memory/insights | No | No | No | No | No | No | **Kerf unique** |
| Graph-native permissions | No | No | No | No | No | No | **Kerf advantage** |
| Safety as core domain | Partial | No | No | No | No | Yes (only) | **Kerf advantage** |
