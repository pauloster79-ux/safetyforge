# Adversarial Ontology Review

**Date:** 2026-04-11
**Reviewer context:** Fresh session, no involvement in design. Reviewing against the validation checklist, design patterns reference, and the AGENTIC_INFRASTRUCTURE playbook.

**Severity levels:**
- **BLOCKER** -- Must fix before implementation. Incorrect, contradictory, or would cause data integrity issues.
- **ISSUE** -- Should fix. Will cause friction, confusion, or technical debt if shipped as-is.
- **NOTE** -- Worth considering. Not wrong, but could be improved.

---

## A. Structural Issues

### A-01: BLOCKER -- Estimate entity exists in DD-06 but not in the schema

DD-06 ("Estimate as Versioned Snapshot") describes a full Estimate entity with properties (`version`, `status`, `total_value`, `margin_pct`, `sent_date`, `accepted_date`), an `INCLUDES` relationship to WorkItems, and a `SUPERSEDES` relationship between Estimate versions. DD-01 assigns it the `est` prefix.

The schema definition (05-schema-definition.md line 154) states: "There is no separate Estimate entity. The work items on a project at 'quoted' status ARE the estimate."

These two documents directly contradict each other. Either the Estimate entity exists or it does not. If it does not exist, DD-06 must be deleted or rewritten. If it does exist, the schema must include its node definition, properties, and relationships.

**Impact:** A developer reading DD-06 will build an Estimate node. A developer reading the schema will not. This will cause implementation divergence.

### A-02: BLOCKER -- ID prefix collision: ProjectQuery and PrequalPackage both use `pq_`

DD-01 assigns `pq` to ProjectQuery. The schema definition assigns `pq_{hex}` to both ProjectQuery (line 554) and PrequalPackage (line 624). The ID prefix is supposed to identify entity type at a glance. Two entities sharing a prefix defeats that purpose and could cause confusion in logs, debugging, and data inspection.

**Fix:** Rename PrequalPackage prefix to `prq` or `pqp`.

### A-03: BLOCKER -- Incident has no relationship to Worker

There is no relationship between Incident and Worker in either the entity catalog or the schema. You cannot answer:
- "Which worker was injured in this incident?"
- "What is this worker's incident history?"
- "What is our incident rate per worker/crew?"

CQ-053 asks about incident rate trends. CQ-029 asks about fatigue risk. Without an Incident-to-Worker link, you cannot correlate incidents with specific workers. For a safety platform, this is a critical omission.

**Fix:** Add `INVOLVED_IN` (Worker -> Incident) or `INVOLVES_WORKER` (Incident -> Worker) with a `role` property ("injured_party", "witness", "first_responder").

### A-04: BLOCKER -- Inspection has no relationship to the person who conducted it

Inspections have no `CONDUCTED_BY` or `INSPECTED_BY` relationship to a Worker or Member. The `created_by` provenance field partially covers this (the person who created the record), but the person who physically performed the inspection may differ from the person who entered the data. Many regulatory jurisdictions require the inspector's identity on inspection records.

**Fix:** Add `CONDUCTED_BY` (Inspection -> Worker/Member).

### A-05: ISSUE -- HazardReport has no relationship to the reporter

There is no `REPORTED_BY` relationship from HazardReport to Worker/Member. The `created_by` provenance field covers the system author, but "who reported this hazard" is a distinct concept from "who entered the data into the system" (a foreman might enter a hazard reported verbally by a labourer).

**Fix:** Add `REPORTED_BY` (HazardReport -> Worker/Member).

### A-06: ISSUE -- DailyLog has no structural links to the day's activities

The DailyLog is described as "auto-populated from safety, time, and equipment data" but has no relationships to TimeEntry, Inspection, Incident, or HazardReport. How does auto-population work without traversable links?

Currently, to assemble a daily log, you would need to query by date across multiple entity types and filter by project. This is a multi-query pattern that should be a single traversal.

**Fix:** Add relationships: `INCLUDES_TIME` (DailyLog -> TimeEntry), `INCLUDES_INSPECTION` (DailyLog -> Inspection), `INCLUDES_INCIDENT` (DailyLog -> Incident). Or use a generic `RECORDED_ON` (entity -> DailyLog) from the child entities.

### A-07: ISSUE -- WorkPackage missing PERFORMED_BY and ASSIGNED_TO_CREW relationships

The reality test (Scenario 4, Dave the GC) identified that WorkPackages need a PERFORMED_BY link to a sub Company, and Scenario 6 identified the need for ASSIGNED_TO_CREW at the package level. The reality test's own "Key Recommendations" section lists these as items 1 and 2.

However, the schema definition does not include either relationship. The recommendations from the reality test were not carried back into the schema.

**Fix:** Add to the Work Model relationship table:
- `PERFORMED_BY` (WorkPackage -> Company) with cardinality N:1
- `ASSIGNED_TO_CREW` (WorkPackage -> Crew) with cardinality N:1

### A-08: ISSUE -- `crew_count_sub` on DailyLog is stored as JSON string

Line 490 of the schema: `crew_count_sub | String | No | No | JSON: sub company -> headcount`. The validation checklist explicitly flags "No arrays stored as JSON strings" and "No implicit relationships via foreign-key properties" as requirements.

This should be a relationship. Each sub company's headcount for the day is a fact about the relationship between a DailyLog and a Company.

**Fix:** Create a relationship `HAS_SUB_CREW` (DailyLog -> Company) with a `headcount` property. Or create a `SubCrewEntry` node if additional metadata is needed.

### A-09: ISSUE -- `photo_urls` as List<String> on three entities

InspectionItem, HazardReport, and DeficiencyItem all store `photo_urls` as `List<String>`. If photos ever need metadata (who took it, when, GPS location, which specific deficiency it documents), this list-of-URLs approach cannot accommodate it. Photos are a cross-entity concept that could benefit from being nodes.

**Fix for now:** Acceptable if photos are truly just URL references. Flag for future promotion to a Photo/Attachment node if metadata requirements emerge. At minimum, document this as a known simplification.

### A-10: ISSUE -- `additional_languages` on Company and `languages` on Jurisdiction as List<String>

These are not queryable cross-entity. You cannot efficiently answer "which companies have Spanish-speaking workforces?" because list properties are not indexed in Neo4j. If workforce language matching becomes important (e.g., assigning bilingual safety briefings), this will require a full label scan.

**Fix:** Consider promoting Language to a node with `SPEAKS` relationships if cross-company language queries are needed. Or accept the limitation and document it.

### A-11: NOTE -- SafetyZone and Location have no relationship to Project in the schema

SafetyZone exists in the entity catalog and schema definition but has no relationships defined in the relationship specification tables. It is an orphan node type. Similarly, Location is defined but the only relationship connecting it is `AT_LOCATION` (WorkItem -> Location). There is no `LOCATED_AT` (Project -> Location) despite the design patterns document recommending this pattern.

**Fix:** Add `HAS_SAFETY_ZONE` (Project -> SafetyZone) and `LOCATED_AT` (Project -> Location). Also add `WITHIN_ZONE` (SafetyZone -> Location) if zones are sub-areas of a project site.

### A-12: NOTE -- ComplianceProgram is mentioned but has no definition

The entity catalog consolidation table says "ComplianceProgram: Kept as regulatory entity." The schema's regulatory section lists it among entities that "retain their existing property structures." But ComplianceProgram never appears in any entity table, relationship table, or CQ mapping. It is referenced but undefined.

**Fix:** Either define it fully (properties, relationships, CQ mappings) or remove the reference.

---

## B. CQ Coverage Gaps

### B-01: BLOCKER -- CQ-029 (fatigue risk from excessive hours) is not answerable

CQ-029: "Is any worker at fatigue risk (excessive consecutive hours)?"

This is marked as RULE type. To answer it, you need:
1. TimeEntry records for a worker across consecutive days
2. A rule defining what constitutes fatigue risk (varies by jurisdiction -- EU Working Time Directive, OSHA general duty clause, Australian WHS fatigue codes)

The regulatory graph has no fatigue-related rules encoded. There is no Regulation -> "maximum consecutive hours" rule chain. The TimeEntry entity has hours but no relationship to fatigue rules. This CQ is marked as answerable but cannot be answered through graph traversal alone -- it requires application logic with hardcoded thresholds.

**Fix:** Either encode fatigue rules in the regulatory graph (Activity -> REGULATED_BY -> Regulation with `when: "consecutive_hours > X"`), or reclassify this CQ as requiring application logic and document the dependency.

### B-02: ISSUE -- CQ-036/CQ-037 (budget tracking) rely on non-existent stored properties

The CQ validation query for CQ-036 references `wi.estimated_total` and `wi.actual_total`, but the WorkItem schema explicitly states: "All calculated values are computed at query time, not stored." Neither `estimated_total` nor `actual_total` exists as a property on WorkItem.

The query as written will return null for both fields. The correct query would need to compute: `labour_hours * labour_rate + materials_allowance` for estimated, and aggregate TimeEntry hours for actual. This is significantly more complex than the sample query suggests.

**Fix:** Either update the sample queries to use the actual computation, or reconsider whether caching these computed values as properties is warranted for performance.

### B-03: ISSUE -- CQ-012 (effective margin based on crew performance) requires data not in the model

CQ-012: "What's our effective margin at this price, based on how our crews actually perform?"

Answering this requires historical crew performance data: how fast did this crew complete similar work in the past? The model has TimeEntry and WorkItem, so you can compute actual hours vs estimated hours per crew per work category historically. But there is no pre-computed performance metric and no explicit relationship linking Crew to WorkCategory for performance aggregation.

This is answerable but requires a complex multi-hop aggregation across historical projects. Document the query pattern.

### B-04: ISSUE -- CQ-067 (estimate vs plan quantities) lacks a clear query path

CQ-067: "Does the estimate match the quantities shown in the plans?"

This requires comparing USES_ITEM quantities on WorkItems against quantities extracted from DocumentChunks via the MENTIONS relationship. But MENTIONS only records that a DocumentChunk mentions an entity -- it does not carry quantity information. If a plan says "84 receptacles" and the estimate says "84 receptacles", there is no structured way to compare these through graph traversal. This comparison requires NLP over document text, not graph queries.

**Fix:** Reclassify as a hybrid CQ (graph + LLM interpretation) or add a `QuantityExtraction` node that captures structured quantities from documents.

### B-05: ISSUE -- CQ-048 (lien waivers collected) has an incomplete query path

CQ-048: "Have all required lien waivers / payment release documents been collected?"

The relationship chain is: Project -> HAS_PAYMENT_APP -> PaymentApplication -> WAIVED_BY -> LienWaiver. But lien waivers are also required from subcontractors before the GC pays them. The current model only links LienWaiver to PaymentApplication. For a GC managing subs, the question is: "Have I received lien waivers from all my subs before I pay them?" This requires a link from LienWaiver to the sub Company and to the specific Invoice being waived, which does not exist.

**Fix:** Add `WAIVER_FROM` (LienWaiver -> Company) and `WAIVES` (LienWaiver -> Invoice) relationships.

### B-06: NOTE -- Missing obvious contractor questions not in the CQ list

Several questions a contractor would commonly ask are absent:

1. "What is my cash flow projection for the next 30/60/90 days?" -- Requires aggregating expected receivables (outstanding invoices + uninvoiced completed work) against expected payables (sub invoices due). No CQ covers forward-looking cash flow.

2. "Which of my workers' certifications are expiring in the next 30 days?" -- Partially covered by CQ-016 (valid through work dates) but there is no general "expiring soon" CQ.

3. "What is my insurance renewal schedule?" -- InsuranceCertificate has expiry dates but no CQ asks about the company's own insurance timeline.

4. "How does this project compare to budget at the same percentage of completion?" -- Earned value analysis. CQ-036 asks "is it on budget" but not "is it on budget for how far along we are?"

5. "Which projects are at risk of going over budget based on current burn rate?" -- Predictive, not just current state.

---

## C. Real-World Scenario Gaps

### C-01: Roofing Contractor -- Weather-Dependent, High-Risk

**Profile:** 18 employees. Residential and commercial roofing. Revenue ~$2.5M. Highly weather-dependent. High fall-risk trade.

**Key characteristics not well-covered:**

1. **Weather-dependent scheduling.** A roofing crew cannot work in rain, high wind, or extreme cold. The model has `weather_summary` on DailyLog (after the fact) but no weather-based scheduling constraint. WorkItem has `planned_start`/`planned_end` but no mechanism to flag "this work item is weather-sensitive" or to link weather conditions to schedule changes.

2. **Material waste tracking.** Roofing materials (shingles, felt, flashing) have significant waste factors (10-15% overage is standard). The USES_ITEM relationship has `quantity` and `actual_cost` but no `waste_factor` or `quantity_ordered` vs `quantity_installed`. A roofer tracking profitability needs to know: "Did we waste more materials than we budgeted for?"

3. **Fall protection compliance is per-worker-per-day.** Every worker on a roof must have current fall protection training AND be using the correct PPE. The model links Worker -> Certification and Activity -> Regulation -> CertificationType. But there is no per-day PPE verification record. The Inspection entity can cover this, but it is a daily requirement, not a periodic one.

**Verdict:** The model handles the core workflow (estimate, schedule, execute, invoice) adequately. Weather sensitivity and material waste are not modelled. PPE tracking gaps exist for high-risk trades.

### C-02: Multi-Site Commercial Contractor

**Profile:** 85 employees. Fits out retail chain stores -- same scope repeated across 20+ locations. Revenue ~$15M.

**Key characteristics not well-covered:**

1. **Template projects.** This contractor does the same fit-out repeatedly. They need a "template project" with predefined WorkPackages, WorkItems, and material lists that can be cloned for each new location. The model has no concept of project templates. Every new location would require manual re-creation of the work structure.

2. **Multi-project reporting.** CQs focus on single-project queries. This contractor needs: "Across all my active store fit-outs, what is the total budget vs actual?" "Which stores are behind schedule?" The model supports this (query across projects with a filter) but no CQ validates this pattern.

3. **Standardised pricing across locations.** WorkItem costs might be defined once ("install POS system: $3,200 per location") and applied across 20 projects. The model has no mechanism for standard cost templates that can be applied to multiple projects.

**Verdict:** The model handles individual projects well but lacks template/clone capabilities for repetitive work. This is arguably application logic, not ontology, but the absence means an agent cannot create projects from templates without understanding the full WorkItem structure.

### C-03: International Contractor Operating in Two Jurisdictions

**Profile:** UK-based contractor with projects in both UK and Ireland. 30 employees. Electrical and data cabling.

**Key characteristics not well-covered:**

1. **Single company, two jurisdictions.** The model has `IN_JURISDICTION` (Company -> Jurisdiction) as N:1, meaning a Company can only be in ONE jurisdiction. A company operating in both UK and Ireland cannot be linked to both. The model would require two Company nodes for the same legal entity, which breaks tenant isolation (the company's workers, equipment, and financials are shared across jurisdictions).

2. **Worker certifications valid in one jurisdiction but not another.** A UK electrician's Part P certification is not valid in Ireland (which requires Safe Electric registration). The model handles this per-worker via Certification -> CertificationType -> Jurisdiction. But when assigning a UK-certified worker to an Irish project, the compliance check needs to know: "This worker's UK cert does not satisfy Ireland's requirements." The model can answer this IF the CertificationType nodes are jurisdiction-specific, which they appear to be. But the question is whether the compliance agent will correctly traverse the Irish regulations for a UK-based company's project.

3. **Dual currency.** Projects in Ireland are in EUR, projects in UK are in GBP. The Company has `default_currency` but projects in the other jurisdiction need a different currency. There is no `currency` property on Project.

**Verdict:** The single-jurisdiction-per-company assumption is a significant limitation for international contractors. The workaround (two Company nodes) is architecturally ugly and creates data duplication.

### C-04: Contractor Who Also Does Maintenance/Service Work

**Profile:** HVAC company. 25 employees. 40% installation (project-based), 60% maintenance contracts (recurring service work).

**Key characteristics not well-covered:**

1. **Recurring service agreements.** A maintenance contract is not a one-time project -- it is an ongoing agreement to service equipment at regular intervals. The model has Contract but it is linked to Project (a one-time thing). A maintenance contract might cover 50 buildings, each visited quarterly. Creating a "project" for each visit is possible (like the plumber callout scenario) but creates hundreds of lightweight projects per year per client.

2. **Equipment service history.** The model has Equipment and EquipmentInspectionLog for the contractor's own equipment. But a maintenance contractor services the CLIENT'S equipment. There is no model for customer-owned assets that the contractor maintains. This would require an Asset entity belonging to the client, with a service history.

3. **Scheduled recurring work.** The model has no concept of recurring work patterns. A quarterly HVAC filter change at 50 locations is a repeating pattern, not a one-time project. WorkItems have `planned_start`/`planned_end` but no recurrence.

**Verdict:** The model is heavily project-centric and does not accommodate recurring service/maintenance business models. This is a significant gap for any trade that does both project and service work (HVAC, electrical, plumbing).

---

## D. Consistency Issues

### D-01: BLOCKER -- Relationship name inconsistency: LINKS_TO_CATEGORY vs LINKS_TO_ACTIVITY

The entity catalog (03-entities-relationships.md, line 421) names the relationship `LINKS_TO_CATEGORY`. The design decisions (04-design-decisions.md, line 218) and the schema definition (05-schema-definition.md, line 985) name it `LINKS_TO_ACTIVITY`.

These are different names for the same relationship (WorkCategory -> Activity). The schema and design decisions agree, but the entity catalog disagrees.

**Fix:** Update the entity catalog to use `LINKS_TO_ACTIVITY`.

### D-02: ISSUE -- WorkItem status values differ between DD-05 and the schema

DD-05 defines the progression as: `estimated -> scheduled -> in_progress -> complete -> invoiced`
The schema (line 121) defines: `"draft", "scheduled", "in_progress", "complete", "invoiced", "on_hold", "cancelled"`

`estimated` in DD-05 became `draft` in the schema. The schema also adds `on_hold` and `cancelled` which DD-05 mentions as "additional terminal states" but lists them there as `cancelled` and `on_hold` (matching). The initial state mismatch (`estimated` vs `draft`) is the issue.

**Fix:** Align DD-05 to use `draft` or update the schema to use `estimated`. Given that `draft` is used consistently across many other entities (Invoice, Contract, Variation, etc.), `draft` is the better choice. Update DD-05.

### D-03: ISSUE -- Inconsistent use of ASSIGNED_TO relationship name

`ASSIGNED_TO` is used for three different relationship types:
1. Worker -> Project (workforce, line 885)
2. CorrectiveAction -> Worker/Company (safety, line 903)
3. ProjectQuery -> Contact/Member (coordination, line 935)
4. DeficiencyItem -> Worker/Company (safety, line 912)

This violates the design pattern guideline against "generic relationships used for multiple distinct meanings." While Neo4j allows the same relationship type between different node label pairs, it creates ambiguity in queries and makes the schema harder to reason about.

**Fix:** Differentiate: `ASSIGNED_TO_PROJECT` (Worker -> Project), `ASSIGNED_TO_RESOLVER` (CorrectiveAction/DeficiencyItem -> Worker/Company), `ASSIGNED_TO_RESPONDER` (ProjectQuery -> Contact/Member). Or accept the ambiguity and document the convention.

### D-04: ISSUE -- Provenance fields not consistently applied

The schema states provenance fields are on "every mutable tenant-scoped entity." But several entities lack the explicit `+ provenance fields` marker:

- SafetyZone -- mutable, tenant-scoped (via Project), no provenance fields listed
- Location -- mutable, no provenance fields listed

Also, the provenance convention says `updated_by` and `updated_at` are "Required: Yes" but many entities may never be updated (e.g., a TimeEntry after approval, a Message). If these fields are required at creation time, they would need to be set to the same values as `created_by`/`created_at`, which is redundant. Consider making them required only after first update.

### D-05: NOTE -- Status value style inconsistency

Most status values use `snake_case` (e.g., `in_progress`, `under_review`, `partially_paid`). But some use single words where compound forms exist elsewhere:
- Equipment: `"maintenance"` vs `"in_progress"` elsewhere
- InsuranceCertificate: `"expiring_soon"` (descriptive) vs `"active"` (state)
- Milestone: `"upcoming"`, `"met"`, `"missed"` (adjective style) vs `"draft"`, `"submitted"`, `"approved"` (past participle style) elsewhere

This is cosmetic but affects API consistency. Developers will need to remember different patterns for different entities.

### D-06: NOTE -- `id` vs `agent_id` / `alert_id` / `briefing_id` naming

All entities use `id` as their primary key property name except:
- AgentIdentity uses `agent_id`
- ComplianceAlert uses `alert_id`
- BriefingSummary uses `briefing_id`

This breaks the convention established everywhere else and will require special-casing in generic query builders and service layer code.

**Fix:** Rename to `id` on all three entities for consistency.

---

## E. Anti-Patterns

### E-01: ISSUE -- Property bag: DailyLog has 12+ properties including JSON

DailyLog has `weather_summary`, `temperature_high`, `temperature_low`, `wind_conditions`, `precipitation`, `crew_count_own`, `crew_count_sub` (JSON), `work_performed`, `notes`, `submitted_at`, `submitted_by`, plus provenance fields. That is 18+ properties on a single node, and the weather data alone could be a separate Weather node shared across DailyLogs on the same date and location.

**Fix:** Consider extracting weather into a Weather node (or accept the property count and just fix the JSON issue from A-08).

### E-02: ISSUE -- Missing indexes on frequently-queried properties

The validation checklist requires: "Indexes exist on all properties used in WHERE / ORDER BY." Several properties that will clearly be queried frequently are not indexed:

- `Inspection.inspection_date` -- IS indexed (good)
- `TimeEntry.clock_in` -- IS indexed (good)
- `DailyLog.log_date` -- IS indexed (good)
- `WorkItem.planned_start` / `planned_end` -- NOT indexed (scheduling queries will use these)
- `Certification.expiry_date` -- IS indexed (good)
- `CorrectiveAction.due_date` -- IS indexed (good)
- `Invoice.due_date` -- IS indexed (good)
- `Variation.status` -- IS indexed (good)
- `WorkPackage.status` -- NOT indexed (filtering active packages)
- `ToolboxTalk.date` -- NOT indexed (querying by date)
- `Milestone.planned_date` -- NOT indexed (schedule queries)
- `HazardReport.status` -- IS indexed (good)

**Fix:** Add indexes on `WorkItem.planned_start`, `WorkItem.planned_end`, `WorkPackage.status`, `ToolboxTalk.date`, and `Milestone.planned_date`.

### E-03: ISSUE -- Phantom entity: ComplianceProgram

As noted in A-12, ComplianceProgram is referenced but never defined. No properties, no relationships, no CQ mappings. This matches the "phantom types" anti-pattern: "Node types that exist in schema but have zero instances."

### E-04: NOTE -- Potential over-modelling: QueryResponse

QueryResponse has only `id`, `content`, `response_date`, and provenance fields. It has exactly one inbound relationship (`HAS_RESPONSE` from ProjectQuery). A node with 3 meaningful properties and exactly one relationship is a candidate for being a property on the parent entity (or a list of responses stored as a property).

However, ProjectQueries can have multiple responses (back-and-forth), and responses carry provenance (who responded). Keeping it as a node is defensible for audit trail purposes.

**Verdict:** Acceptable as-is, but worth noting.

### E-05: NOTE -- `applicability_tags` on Insight should be Tag nodes

Insight stores `applicability_tags` as `List<String>`. The design patterns reference explicitly recommends: "Tags are nodes, not array properties (enables cross-entity queries: 'all entities tagged X')." If you want to find all Insights related to "renovation" across the system, you need to scan every Insight's list property.

**Fix:** Promote to Tag nodes with `TAGGED_WITH` relationships if cross-entity tag queries are needed.

---

## F. Global Readiness

### F-01: ISSUE -- Single-jurisdiction-per-company assumption

As explored in Scenario C-03, `IN_JURISDICTION` (Company -> Jurisdiction) is N:1. A company can only be in one jurisdiction. This is a US/UK-centric assumption. Many contractors operate across borders:
- UK + Ireland (common for electrical, plumbing)
- US border states working in two states with different requirements
- Australian contractors working across state lines (each state has its own WHS regulator)
- Canadian contractors working across provinces

The cardinality should be N:M, or there should be a mechanism for project-level jurisdiction override.

**Fix:** Either change `IN_JURISDICTION` to N:M, or add a `jurisdiction_code` property to Project that defaults to the Company's jurisdiction but can be overridden per project.

### F-02: ISSUE -- No currency property on Project

Projects inherit currency from the Company's `default_currency`. But a UK contractor working on an Irish project bills in EUR, not GBP. There is no `currency` property on Project or Contract.

**Fix:** Add `currency` (String, ISO 4217) to both Project and Contract, defaulting to the Company's `default_currency`.

### F-03: ISSUE -- LienWaiver is US-centric despite global naming effort

"Lien waiver" is a specifically US legal concept. In the UK, there is no equivalent (retention release is handled differently). In Australia, "statutory declaration" or "payment claim" under the Security of Payment Act serve a similar but legally distinct function.

The entity catalog acknowledges this ("lien waiver in US, equivalent in other jurisdictions") but the entity name is still `LienWaiver` and the properties (`type: "conditional" / "unconditional"`) are US-specific (conditional vs unconditional lien waiver is a US legal distinction).

**Fix:** Rename to `PaymentRelease` or `PaymentClearance` with a jurisdiction-specific `form_type` property. Or keep `LienWaiver` and add a `jurisdiction_form` property that maps to the local equivalent.

### F-04: NOTE -- Tax handling absent from the model

No entity or property handles tax (VAT in UK/AU/EU, sales tax in US, GST in AU/Canada). Invoices have `amount` but no `tax_amount`, `tax_rate`, or `tax_code`. For UK contractors, every invoice must show VAT separately. For Australian contractors, GST must be itemised.

This may be intentionally deferred (it is complex and jurisdiction-specific), but its absence should be explicitly documented as a known gap.

### F-05: NOTE -- No concept of "permit" as a project-level entity

Many jurisdictions require permits before work begins (building permit, electrical permit, plumbing permit). The model has `Document` with `type: "permit"` but a permit is more than a document -- it has an application process, an approval workflow, an expiry date, and conditions. In many jurisdictions (US especially), work without a permit is a criminal offence.

Document with type "permit" may be sufficient for document storage, but if the system needs to answer "does this project have all required permits?" it needs a relationship from the regulatory graph: `Regulation -> REQUIRES_PERMIT -> PermitType`, and a project-level check that the permit has been obtained.

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| BLOCKER | 5 | A-01, A-02, A-03, A-04, B-01 |
| ISSUE | 17 | A-05, A-06, A-07, A-08, A-09, A-10, B-02, B-03, B-04, B-05, D-01, D-02, D-03, D-04, E-01, E-02, E-03, F-01, F-02, F-03 |
| NOTE | 10 | A-11, A-12, B-06, D-05, D-06, E-04, E-05, F-04, F-05, C-01 through C-04 (scenario analysis) |

### Recommended Fix Order

1. **Resolve the Estimate entity contradiction (A-01)** -- This is the single biggest source of confusion. Decide once, update all documents.
2. **Add Incident -> Worker relationship (A-03)** -- Core safety data integrity.
3. **Add Inspection -> Conductor relationship (A-04)** -- Regulatory requirement.
4. **Fix the ID prefix collision (A-02)** -- Simple rename, prevents future confusion.
5. **Encode fatigue rules or reclassify CQ-029 (B-01)** -- Safety CQ that cannot be answered.
6. **Carry reality test recommendations into the schema (A-07)** -- WorkPackage PERFORMED_BY and ASSIGNED_TO_CREW.
7. **Fix the LINKS_TO naming inconsistency (D-01)** -- Single find-and-replace.
8. **Fix the JSON property on DailyLog (A-08)** -- Anti-pattern.
9. **Add currency to Project and Contract (F-02)** -- Global readiness.
10. **Address single-jurisdiction assumption (F-01)** -- Global readiness.
