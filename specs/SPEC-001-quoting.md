# SPEC-001: Quoting — Commercial Intelligence for Construction Estimates

*Version 1.0 — 2026-04-14*

---

## TIER 1: PRODUCT SPECIFICATION

---

### 1. THE PROBLEM

#### Summary

Contractors lose money not because they can't do arithmetic, but because they don't think through everything they should — and then can't defend their price when things go wrong during construction. The quoting feature adds the commercial intelligence layer to Kerf: structured assumptions, exclusions, resource rates, productivity rates, and qualified terms that make quotes defensible, learnable, and commercially strategic.

#### Problem Statement

**Current state:** Contractors estimate jobs using spreadsheets, memory, or verbal quotes. Cost calculations may be roughly correct, but the terms surrounding the price — what's included, what's excluded, what conditions the price depends on, what happens when things change — are either absent or buried as prose in a PDF. When a GC delays access by 3 weeks, the contractor can't substantiate a variation claim because their overhead wasn't broken out by duration. When a homeowner asks for "just one more outlet," there's no documented mechanism to charge for it.

**Desired state:** Kerf guides the contractor through quoting conversationally, captures structured assumptions and exclusions as graph data (not PDF prose), applies the contractor's own historical rates and productivity, and generates a qualified quote document. During construction, the system monitors assumption triggers and auto-drafts variation claims with the contractual basis already established.

**Impact:** Competitor analysis confirms no small-contractor tool generates structured terms and conditions, learns from historical job data to improve future quotes, or connects quote assumptions to variation detection during execution. This is open whitespace. The closest competitor (Handoff) does fast AI arithmetic but produces prices without qualified terms — which is exactly what Tim's estimating course identifies as the failure mode that bankrupts contractors.

#### Out of Scope

- Plan/drawing takeoff automation (document intelligence — Phase 8)
- Subcontractor quote management and levelling (future expansion)
- Progress billing / AIA G702-G703 payment applications (existing Domain 13)
- Supplier pricing integration / live material costs (future expansion)
- Multi-currency support

#### Dependencies

- **WorkItem, WorkPackage, WorkCategory** — exist in codebase but NOT in ontology. This spec formalizes them as Domain 11a (Work Structure) alongside the new Domain 16 entities.
- **Project** — exists in ontology (Domain 1). Extended with quoting properties.
- **CostCode** — exists in ontology (Domain 10). Extended with default rate links.
- **Document** — exists in ontology (Domain 9). Used for proposal PDF generation.
- **ChangeEvent / Variation** — exists in ontology (Domain 14) and codebase. Connected via assumption triggers.
- **TimeEntry** — exists in ontology (Domain 10). Source data for derived rates and productivity.

---

### 2. THE USERS

#### User Stories

**US-1: Solo contractor quotes a residential job conversationally**
As Jake (solo electrician), I want to describe work while walking a site and have Kerf build a structured quote with terms, so that I stop giving verbal quotes with no documentation.

*Acceptance criteria:*
- Conversational input (voice or text) creates WorkItems with labour and material breakdowns
- Agent applies my historical rates and productivities, not book rates
- Agent flags items I frequently miss (permits, wait time, code requirements)
- Quote includes structured assumptions, exclusions, and additional work rates
- Output is a professional PDF quote document I can send to the client

**US-2: Commercial sub quotes a GC job with qualified terms**
As Sarah (45-person electrical sub), I want to submit a letter of offer with duration-based prelims, schedule reliance, mobilisation counts, and variation rates, so that I can claim variations when the GC delays me.

*Acceptance criteria:*
- WorkItems organised into WorkPackages (divisions)
- Assumptions linked to affected WorkItems with variation triggers
- Overhead items broken out by duration (weeks x rate) not lump sum
- Exclusions include trade-standard defaults plus project-specific items
- VE options as alternate WorkItems with price adjustments
- Variation rates established in the quote for additional work pricing
- Agent cross-references uploaded plans across drawing sets

**US-3: Contractor reviews and edits draft quote terms**
As a contractor, I want to see assumptions, exclusions, and rates as editable fields in my draft quote (not just in the PDF), so that I can review and adjust them before sending.

*Acceptance criteria:*
- Assumptions shown as cards with category, statement, variation trigger toggle
- Exclusions shown as cards with scope boundary and partial inclusion notes
- Template assumptions/exclusions from company defaults auto-applied
- Additional work rates editable
- All editable in the app, not just visible in the generated PDF

**US-4: System learns from completed jobs to improve future quotes**
As a contractor who has completed 15+ jobs, I want my quotes to use my actual labour rates and productivity, not what I enter manually, so that my quotes get more accurate over time.

*Acceptance criteria:*
- ResourceRates derived from TimeEntry actuals across completed jobs
- ProductivityRates derived from actual output per cost code/work category
- Rates show source (manual entry vs derived from actuals) and sample size
- Agent uses derived rates when available, manual rates as fallback
- Rate accuracy comparison available (estimated vs actual per cost code)

**US-5: Assumption triggers variation detection during construction**
As a contractor, when a condition I assumed in my quote turns out to be wrong during construction, I want the system to detect it and draft a variation claim with the contractual basis from my original quote.

*Acceptance criteria:*
- Assumptions with variation_trigger=true are monitored during project execution
- When a daily log, schedule update, or inspection reveals a trigger condition, the system links back to the assumption
- The affected WorkItems and their rates are identified
- A draft ChangeEvent is created with the assumption as the contractual basis

#### Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Quote accuracy improvement | 15%+ after 10 jobs | Estimated vs actual cost comparison |
| Time to produce quote | 80% reduction vs pre-Kerf | Measured from first WorkItem to PDF generation |
| Variation capture rate | 2x increase | Variations claimed vs scope changes detected |
| Assumption template reuse | 70%+ of assumptions from templates after 5 jobs | Template-sourced vs manually-created assumptions |
| Quote terms completeness | 100% of quotes have assumptions + exclusions | Quotes generated with vs without structured terms |

---

### 3. THE RULES

#### Business Rules

**BR-1: WorkItem is the atomic unit**
A WorkItem is a discrete piece of deliverable work with a cost. It flows through lifecycle states: draft (quote line) -> scheduled (task) -> in_progress -> complete -> invoiced (cost line). No separate estimate line, task, or cost line entities exist.

**BR-2: Project lifecycle IS the quoting lifecycle**
A Project in "estimating" state with WorkItems and terms attached IS the estimate. In "proposed" state it IS the quote. No separate Quote or Estimate entity exists. The Project entity gains quoting-specific properties (estimate_confidence, target_margin, contract_type, quote_valid_until).

**BR-3: Assumptions are structured graph data, not prose**
Every assumption has a category, statement, variation trigger flag, and relationships to affected WorkItems. Assumptions are queryable, monitorable, and referenceable in variation claims.

**BR-4: Exclusions are structured and reusable**
Exclusions are graph nodes with statement, partial inclusion notes, and trade type. Company-level exclusion templates are copied to projects and auto-suggested by trade type.

**BR-5: ResourceRates can be manual or derived from actuals**
A ResourceRate is a company-level rate for labour, material, or equipment. It can be entered manually (source=manual_entry) or derived from completed job actuals (source=derived_from_actuals). Derived rates include sample size and standard deviation.

**BR-6: ProductivityRates are company-specific and condition-specific**
A ProductivityRate captures how fast a crew produces output for a specific work type under specific conditions. It links to CostCode and/or WorkCategory. It includes whether non-productive time is baked in.

**BR-7: Alternates are WorkItems, not separate entities**
A value engineering option or alternate pricing is a WorkItem with an ALTERNATE_TO relationship to the base WorkItem. When the client accepts an alternate, the base WorkItem state becomes "superseded" and the alternate becomes active.

**BR-8: All monetary values in cents**
All prices, rates, costs, and amounts are stored as integers in cents. $95.00 = 9500. No floating-point money.

**BR-9: Variation trigger monitoring**
Assumptions with variation_trigger=true are actively monitored during project execution. The agent checks daily logs, schedule updates, and inspection findings against trigger conditions. When violated, the system creates a ChangeEvent linked to the assumption.

**BR-10: Quote document generated from graph data**
The quote PDF is generated from the Project's WorkItems, Assumptions, Exclusions, and rates — not from manually entered text. The Document entity (type="proposal") stores the generated PDF. The graph data is the source of truth; the PDF is a rendering.

**BR-11: Template inheritance for assumptions and exclusions**
Company-level template Assumptions and Exclusions are owned by the Company node. When a new quote is started, relevant templates are copied to the Project as project-specific instances, linked back to their template via ASSUMPTION_FROM_TEMPLATE / EXCLUSION_FROM_TEMPLATE relationships.

**BR-12: Learning loop feeds actuals back to rates**
When a Project reaches "complete" status, the system compares estimated vs actual for each WorkItem. The deltas feed back into ResourceRate and ProductivityRate derivation. Rates improve with every completed job.

**BR-13: WorkItem cost is bottom-up**
A WorkItem's cost is calculated from its components: (labour_hours x labour_rate) + materials_total + equipment_total. The sell price adds the margin. The project total is the sum of all WorkItem sell prices. Cost is never top-down allocation.

#### Validation Rules

**VR-1: WorkItem requires description**
A WorkItem must have a non-empty description. All other fields are optional at creation (populated progressively during quoting).

**VR-2: Labour rate must be positive if labour hours are set**
If labour_hours > 0, labour_rate must be > 0. If labour_hours is null/0, labour_rate is ignored.

**VR-3: Margin percent must be 0-100**
margin_pct must be between 0.0 and 100.0 inclusive.

**VR-4: Assumption must have category and statement**
An Assumption requires a non-empty category (from the enum) and a non-empty statement.

**VR-5: Exclusion must have statement**
An Exclusion requires a non-empty statement.

**VR-6: ResourceRate must have positive rate**
rate_cents must be > 0.

**VR-7: ProductivityRate must have positive rate**
rate must be > 0.

**VR-8: Alternate WorkItem must reference a base**
A WorkItem with is_alternate=true must have an ALTERNATE_TO relationship to exactly one base WorkItem.

**VR-9: Quote validity date must be future**
quote_valid_until on a Project must be a future date when set.

#### Gherkin Scenarios

```gherkin
Scenario: Contractor creates a work item from conversation
Given Jake is quoting a residential panel upgrade
When he says "200-amp panel upgrade, Federal Pacific removal"
Then a WorkItem is created with description containing the scope
And the agent suggests ResourceRates from Jake's history
And labour_hours is populated from the matching ProductivityRate

Scenario: Agent flags a frequently missed item
Given Jake has excluded permit fees on his last 4 quotes
And the current quote has no permit line item
When the agent reviews the quote for completeness
Then the agent suggests adding a Phoenix electrical permit at $134
And the suggestion references the 4 previous omissions

Scenario: Assumption triggers variation during construction
Given Sarah's quote for Peterson GC includes assumption "19-week duration"
And the assumption has variation_trigger=true
And the assumption affects WorkItems for foreman and PM overhead
When the project duration exceeds 19 weeks
Then a ChangeEvent is created with origin="assumption_triggered"
And the ChangeEvent links to the original Assumption
And the estimated cost impact is calculated from the weekly overhead rates

Scenario: Company exclusion templates auto-apply to new quote
Given Chen Electrical has 5 exclusion templates for trade_type="electrical"
When Sarah starts a new quote for an electrical project
Then all 5 exclusion templates are copied as project exclusions
And each project exclusion links back to its template via EXCLUSION_FROM_TEMPLATE
And Sarah can add, remove, or edit the project-specific exclusions

Scenario: Historical rates improve after job completion
Given Sarah has completed 38 jobs with EMT conduit installation
And her derived ProductivityRate for CostCode "26-050" is 32 LF/hour
When she completes job 39 with actual productivity of 34 LF/hour
Then the ProductivityRate is recalculated as weighted average
And the sample_size increments to 39
And the std_deviation is updated

Scenario: Alternate work item represents a VE option
Given Sarah's base quote includes EMT conduit in all areas at $33,200
When she creates an alternate WorkItem for MC cable in non-clinical areas
Then the alternate WorkItem has ALTERNATE_TO relationship to the base
And alternate_label is "VE-1"
And the quote shows both options with the price difference
When Peterson accepts VE-1
Then the base WorkItem state becomes "superseded"
And the alternate WorkItem state becomes "draft" (active)
```

#### Scenario Traceability

| Scenario | Rules Traced |
|---|---|
| Create work item from conversation | BR-1, BR-5, BR-6, VR-1 |
| Agent flags missed item | BR-12, BR-11 |
| Assumption triggers variation | BR-3, BR-9, VR-4 |
| Exclusion templates auto-apply | BR-4, BR-11, VR-5 |
| Historical rates improve | BR-5, BR-6, BR-12, VR-6, VR-7 |
| Alternate work item VE option | BR-7, VR-8 |

---

### 4. THE EXPERIENCE

#### Functional Summary

##### Step 1: Start a Quote
**Screen**: Chat pane (existing)

The contractor opens Kerf and describes the job conversationally. "Starting a quote. Maria Gonzalez, 1847 East Meadow Drive. 200-amp panel upgrade and kitchen circuits." The agent creates a Project in "estimating" status, asks clarifying questions (homeowner direct or GC sub?), and begins capturing WorkItems as the contractor describes scope.

##### Step 2: Build Work Items
**Screen**: Chat pane + Canvas pane (Work Items tab)

As the contractor talks through the scope, WorkItems appear in the canvas pane's Work Items tab. Each WorkItem shows two lines: description with quantity on line 1, labour hours and material cost breakdown on line 2 (muted). The agent applies ResourceRates and ProductivityRates from the contractor's history, flagging where it's correcting their typical under-estimates. Highlighted rows indicate agent interventions.

##### Step 3: Open Work Item Detail
**Screen**: Canvas pane (Work Item detail view)

Clicking a WorkItem opens the pricing worksheet: labour breakdown (task, rate, hours, cost per line), materials breakdown (item, qty, unit cost, cost per line), rate source card explaining where the numbers came from, and the cost-to-sell-price summary (subtotal + margin = sell price).

##### Step 4: Review Terms
**Screen**: Canvas pane (Terms tab)

The Terms tab shows Assumptions as editable cards (category badge, statement, variation trigger toggle, template indicator) and Exclusions as editable cards (scope boundary with partial inclusion notes, template indicator). The agent auto-populates from company templates and adds project-specific items from the conversation (e.g., asbestos exclusion added when the agent flagged the Federal Pacific panel).

##### Step 5: Set Rates and Review Summary
**Screen**: Canvas pane (Rates tab)

The Rates tab shows additional work rates (variation pricing), payment terms, and a quote summary (work item count, assumptions count with trigger count, exclusions count, total). A "Generate Quote PDF" button produces the proposal document.

##### Step 6: Generate and Send Quote
**Screen**: Quote document overlay

The generated quote document appears as an overlay, showing the professional proposal with pricing schedule, inclusions, exclusions, assumptions, additional work rates, and payment terms. The contractor reviews and sends to the client.

##### Step 7: During Construction — Assumption Monitoring
**Screen**: No new screen — agent notifications in chat

When a daily log entry, schedule update, or inspection finding triggers an assumption, the agent notifies the contractor in chat: "Your assumption that the service entrance was in serviceable condition has been triggered — today's daily log reports corroded conduit. Draft variation created with $485 scope based on line item 3." The contractor reviews and submits the variation.

#### Error Experience

| Situation | What the User Sees | What the User Can Do |
|---|---|---|
| No historical rates available | Agent uses book rates, notes "no history yet — using industry standard" | Enter manual rates or proceed with book rates |
| WorkItem missing labour and materials | Warning on item: "No cost breakdown — add labour hours or materials" | Open detail view and add breakdown |
| Assumption contradicts exclusion | Agent flags: "You assumed serviceable conduit but excluded conduit replacement — these may conflict" | Edit either the assumption or exclusion |
| Quote generated with zero assumptions | Warning: "This quote has no assumptions. Quotes without qualified terms leave you exposed." | Add assumptions or proceed with warning |
| Rate derivation has high variance | Rate card shows: "Based on 3 jobs but std deviation is 40% — consider more data" | Use the derived rate or enter a manual override |
| Template exclusion contradicts spec | Agent flags: "Your standard exclusion for fire alarm conflicts with spec Division 28 requirement" | Remove the exclusion or qualify it differently |

#### User Journeys (High-Level)

##### UJ-1: Solo Contractor Quotes a Residential Job

**Persona:** Jake Torres, solo electrician
**Goal:** Produce a professional quote from a site walkthrough conversation

1. Jake opens Kerf and describes the job while walking the property
2. WorkItems populate in the canvas as he talks through scope
3. Agent intervenes with corrections from his history (floor box time, permit fee, APS wait)
4. Agent flags asbestos risk and adds it as an exclusion
5. Jake reviews the Work Items tab — two-line rows with labour/materials breakdown
6. Jake opens a work item to see the full pricing worksheet with rate source
7. Jake switches to Terms tab — 4 assumptions and 5 exclusions, some from templates
8. Jake toggles variation triggers on 2 assumptions
9. Jake reviews Rates tab — additional work at $95/hr, payment terms
10. Jake clicks Generate Quote PDF
11. Professional proposal document with pricing, inclusions, exclusions, assumptions, additional work clause
12. Jake sends to homeowner

**Traces:** BR-1, BR-3, BR-4, BR-5, BR-6, BR-10, BR-11, BR-13

##### UJ-2: Commercial Sub Quotes a GC Job with Qualified Terms

**Persona:** Sarah Chen, 45-person electrical contractor
**Goal:** Submit a letter of offer with duration-based prelims and variation protection

1. Sarah uploads 14 plan/spec files and describes the bid conditions
2. Agent reads plans, produces scope summary with quantities
3. Agent cross-references electrical and mechanical drawings, flags 2 missing circuits
4. Sarah confirms: include the missing circuits, call out as plan discrepancies
5. Agent suggests VE option (MC cable alternate) with labour/material savings calculated
6. Sarah creates an alternate WorkItem for VE-1
7. WorkItems organised into 9 divisions (WorkPackages)
8. Overhead items (foreman, PM) broken out as weekly rates x 19 weeks
9. Terms tab: schedule-reliance assumption with 19-week duration, mob count assumption
10. Exclusions: 15 items including trade-standard templates
11. Variation rates established ($95/hr journeyman, $58/hr apprentice, materials cost + 15%)
12. Sarah generates the letter of offer
13. During construction: Peterson delays access, assumption triggers, variation auto-drafted

**Traces:** BR-1, BR-2, BR-3, BR-4, BR-5, BR-7, BR-9, BR-10, BR-11, BR-12

##### UJ-3: Learning Loop — Rates Improve After Job Completion

**Persona:** Jake Torres, after completing his 16th job
**Goal:** See that his rates have updated based on actual performance

1. Jake marks the Gonzalez kitchen project as complete
2. System compares estimated vs actual for each WorkItem
3. Floor box labour: estimated 1.8 hrs, actual 1.9 hrs — rate adjusts slightly
4. Panel upgrade labour: estimated 6.2 hrs, actual 5.8 hrs — rate adjusts down
5. ResourceRate for journeyman labour: recalculated from 16 jobs
6. ProductivityRate for panel upgrades: sample size now 16
7. On next quote, agent applies updated rates automatically
8. Jake can see rate history and accuracy trends

**Traces:** BR-5, BR-6, BR-12

---

### 5. THE CONSTRAINTS

#### Ontology Conventions (from CONSTRUCTION_ONTOLOGY.md)

- All entity IDs: `{prefix}_{token_hex(8)}`
- All monetary values: integers in cents
- All entities: Actor Provenance fields (created_by, actor_type, agent_id, updated_by, updated_actor_type, model_id, confidence)
- All timestamps: UTC ISO format
- Lifecycle via status enums, not soft delete booleans (WorkItem uses both: state for lifecycle, deleted for soft delete)
- No foreign key properties — references MUST be relationships (Design Principle #8)
- Cross-domain edges are the intelligence layer (Design Principle #5)

#### Non-Functional Requirements

| Requirement | Target |
|---|---|
| Quote generation time | < 2 seconds from button click to PDF |
| Rate derivation | < 5 seconds for full company recalculation |
| Assumption monitoring | Check on every daily log submission, schedule update |
| Historical rate query | < 200ms per CostCode lookup |
| WorkItem creation from conversation | < 500ms per item |

#### Design System References

- Component decisions: `.claude/rules/COMPONENT_DECISIONS.md`
- Design tokens: `.claude/rules/DESIGN_SYSTEM.md`
- Layout patterns: `.claude/rules/COMPONENT_PATTERNS.md`

---

## TIER 2: ARCHITECTURE

*(Stage 2 — to be completed by Claude Code during /discover-spec)*

### 6. System Context

*(Stage 2)*

### 7. Data Model

*(Stage 2 — will formalize WorkItem/WorkPackage/WorkCategory as Domain 11a and add Domain 16 entities: Assumption, Exclusion, ResourceRate, ProductivityRate)*

### 8. Service Architecture

*(Stage 2)*

### 9. Integration Scenarios (IS-X)

*(Stage 2)*

### 10. User Journey Test Specs (UJ-X)

*(Stage 2)*

### 11. Architecture Decisions

*(Stage 2)*

---

## TIER 3: IMPLEMENTATION

*(Stage 2 — to be completed by Claude Code during /discover-spec)*

### 12. Task Decomposition

*(Stage 2)*

### 13. Behaviour Contracts

*(Stage 2)*

### 14. Integration Test Specs

*(Stage 2)*

### 15. E2E Test Specs

*(Stage 2)*

### 16. Coverage Matrix

*(Stage 2)*

---

## CHANGE LOG

| Date | Version | Change |
|---|---|---|
| 2026-04-14 | 1.0 | Initial Tier 1 specification — product requirements for quoting feature |
