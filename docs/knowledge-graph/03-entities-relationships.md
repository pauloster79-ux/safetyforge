# Entity & Relationship Discovery (Revised)

## Core Design Principles

### 1. Lifecycle Over Duplication
Concepts that appear separate are often the same thing at different stages. A lead is a Project in early status. Costing lives on the WorkItem, not on a separate Estimate entity above it.

### 2. Two Layers + Detail
The model has exactly two structural layers: Project (the job) and WorkItem(s) (the work within it). Everything else is detail attached to one of these two layers. WorkPackage is the one optional grouping — a folder, not a layer. The minimum viable graph is always: Company → Project → WorkItem(s) + Contact.

### 3. Global-First Naming
No US-specific entity names. The underlying concept is named, not the jurisdiction-specific form. RFI → ProjectQuery. OSHA 300 Log Entry → IncidentLogEntry. Punch list → DeficiencyList.

### 4. Consolidation Over Proliferation
If two entities share the same structure and differ only by a category field, they should be one entity with a category. MockInspectionResult → Inspection with type "simulated". EnvironmentalProgram → Document with type "environmental_compliance".

### 5. Permission = Traversability + Role Depth
Access is determined by what you're connected to in the graph AND your role's depth of traversal. A Worker traverses to their assigned Projects but not to Estimates or Invoices. A Foreman sees WorkItems and TimeEntries but not margins. A GC sees their sub's compliance data on shared projects but not the sub's other projects. This is the graph-native permission model: no path = no data, role = how deep you can go.

---

## Entity Catalog

### Organisational & Locale

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Company** | Tenant root. Contractor, GC, sub, or client organisation. Carries jurisdiction, locale, currency, measurement system | Existing (enriched) | All |
| **Member** | A person with a system login. Has an `access_role` that determines traversal depth | Existing (enriched) | Auth, assignments, 074-081 |
| **Contact** | An external person the company interacts with (client, architect, GC project manager, inspector). May not have an account. Referenced by projects, queries, invoices | New | 001, 004, 011, 064 |

**Enrichment on Company for globalisation:**
- `jurisdiction_code` (existing) — links to Jurisdiction
- `default_currency` — ISO 4217 (GBP, USD, AUD, CAD, EUR)
- `measurement_system` — metric / imperial
- `default_language` — primary language for generated content
- `additional_languages` — workforce languages (for safety briefings, toolbox talks)

**Enrichment on Member/Worker:**
- `preferred_language` — individual language preference

**Enrichment on Member for access control:**
- `access_role` — determines default traversal depth. Values:
  - `owner` — full access to everything in the company
  - `admin` — full access to everything in the company
  - `manager` — full access to assigned projects including commercial data
  - `foreman` — access to assigned projects' operational data (work items, time, inspections) but NOT commercial data (margins, total contract values, invoice amounts)
  - `worker` — access to own assignments, own time entries, safety data only

### Access & Permissions

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **AccessGrant** | An explicit grant of access beyond the default role. Used for: (a) giving a foreman temporary access to commercial data, (b) granting an external Contact access to specific project data, (c) any exception to the default role-based depth. Carries scopes, expiry, and who granted it | New | 074-081 |

**How permissions work in the graph:**

The model combines relationship-derived access with role-based depth:

1. **What you're connected to** determines WHICH data you can see:
   - A Member sees projects they're connected to (via MANAGES or ASSIGNED_TO)
   - A Worker sees projects they're ASSIGNED_TO
   - A GC sees sub data on projects linked via GC_OVER + shared project membership
   - A Contact with an AccessGrant sees what the grant specifies

2. **Your access_role** determines HOW DEEP you can traverse:
   - `owner/admin`: full traversal — Project → Estimates → WorkItems → margins → Invoices → Payments
   - `manager`: full traversal on assigned projects
   - `foreman`: Project → WorkItems → TimeEntries → Inspections. STOPS before Estimate margins, Invoice amounts, Payment data
   - `worker`: Project → own TimeEntries, own Assignments, Safety data (inspections, hazards, toolbox talks)

3. **AccessGrant** handles exceptions:
   - External GC accessing sub compliance data on shared projects
   - Client portal access to progress and invoices
   - Architect/consultant access to project queries and review submissions
   - Temporary elevation (foreman needs to see commercial data during a negotiation)

This is enforced at the service layer, not in the graph structure itself. The graph provides the paths; the service layer checks role + grants before returning data.

### Regulatory (shared across tenants)

These are the jurisdiction-neutral knowledge base entities. Shared by all tenants. Seeded from jurisdiction YAML files.

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Jurisdiction** | A regulatory jurisdiction (US, UK, AU, CA). Carries locale defaults: languages, currency, measurement system | Existing (enriched) | 007, 055, 070-073 |
| **Region** | A sub-jurisdiction (state, province, territory) with additional or overriding requirements | Existing | 007, 055 |
| **RegulatoryGroup** | A grouping of related regulations (e.g., a subpart or chapter) | Existing | 055 |
| **Regulation** | A specific regulatory requirement. Carries temporal validity (valid_from/valid_until), source citation, and jurisdiction | Existing | 007, 055, 056, A03 |
| **CertificationType** | A type of certification that workers can hold (e.g., working at height, confined space). Jurisdiction-linked | Existing | 016, 056 |
| **TradeType** | A construction trade (electrical, plumbing, concrete, carpentry). Jurisdiction-neutral, maps to local terminology | Existing | 015 |
| **Role** | A defined site role (e.g., competent person, site supervisor, safety officer). Roles have regulatory significance — certain activities require a named person in a specific role | Existing | 015 |
| **Activity** | A type of construction activity (e.g., working at height, trenching, hot work). Links to regulations that govern it | Existing | 007, 055, 056 |
| **HazardCategory** | A category of hazard (fall, struck-by, electrical, chemical exposure). Jurisdiction-neutral classification | Existing | 026 |
| **Substance** | A hazardous substance with jurisdiction-specific exposure limits (PELs in US, WELs in UK, WES in AU) | Existing | 059 |
| **DocumentType** | A type of document required by regulation in a jurisdiction (e.g., safety plan, risk assessment, method statement) | Existing | 069 |
| **InspectionType** | A type of inspection defined by regulation (e.g., scaffold inspection, excavation inspection) | Existing | 025 |
| **RegionalRequirement** | An additional requirement that applies in a specific region beyond the base jurisdiction rules | Existing | 055 |
| **ViolationType** | A classification of regulatory violation with associated severity and penalty structure | Existing | 025 |
| **IncidentClassification** | How incidents are categorised in a jurisdiction (recordable vs first-aid in US, RIDDOR-reportable in UK, notifiable in AU) | Existing | 053 |
| **RecordForm** | A regulatory record-keeping form required in a jurisdiction. Jurisdiction-neutral name, maps to local equivalent (OSHA 300 in US, accident book in UK) | Existing (renamed conceptually) | 060 |
| **RegulatoryVersion** | A version of a regulation, for tracking amendments over time. Supports temporal queries | Existing | A03 |

**Enrichment on Jurisdiction for globalisation (CQ-070 to CQ-073):**
- `languages` — list of common languages in this jurisdiction
- `default_currency` — ISO 4217
- `measurement_system` — metric / imperial
- `date_format` — locale date convention

### The Work Model

This is the architectural core of the platform expansion.

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Project** | The central entity. Lifecycle: lead → quoted → active → complete → closed (+ lost). A lead IS a Project in early status, not a separate entity | Existing (enriched) | Nearly all |
| **WorkPackage** | An optional grouping of related work items (e.g., "electrical rough-in", "ground floor fit-out"). Used by larger contractors for organising, assigning crews, and tracking progress. Not required — solo contractors skip this level | New | 023, 036, 037 |
| **WorkItem** | A discrete piece of deliverable construction work. The atomic unit of the platform. Has optional quantity (sometimes measurable, sometimes lump sum). Carries its own cost estimate (labour + materials). Progresses through: estimated → scheduled → in-progress → complete. Tracked and eventually invoiced | New | 005, 006, 009, 010, 018, 023, 024, 031, 034, 036, 037, 040, 050, 067 |
| **WorkCategory** | A hierarchical classification of work types. What kind of work is this? Links to the regulatory graph (electrical work requires different certs than concrete work). Replaces "cost code" — it's a category of work, not just a category of cost | New | 005, 006, 037, 052 |

**Key design: WorkItem costing is bottom-up.**
A WorkItem carries its own estimated cost (labour + materials + equipment). A WorkPackage total is the sum of its WorkItems plus optional margin/overhead. A Project total is the sum of its WorkPackages (or WorkItems directly if no packages).

**Key design: Flexible hierarchy.**
```
Simple:  (Project)-[:HAS_WORK_ITEM]->(WorkItem)
Complex: (Project)-[:HAS_WORK_PACKAGE]->(WorkPackage)-[:CONTAINS]->(WorkItem)
```

### Commercial

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Contract** | A formalised agreement for a project. Carries terms: value, retention percentage, payment schedule, scope description, key dates | New | 013, 038, 047 |

**Key design: No separate Estimate entity.**
The work items on a project at "quoted" status ARE the estimate. When the project moves to "active", those same work items become the work to deliver and track. Change history is captured by provenance fields and conversation memory. No version nodes, no duplication.

### Financial

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **TimeEntry** | Time worked by a worker. Linked to WorkItem (what they were doing), Project, and optionally GPS-verified. Source: worker self-entry, foreman crew entry, or auto-detected | New | 028, 029, 036, 037, 039, 052 |
| **Variation** | A change to the original agreed scope. Has evidence chain (daily records, photos, time entries). The global term for "change order" (US), "variation" (UK/AU), "extra" (informal) | New | 038, 039, 050 |
| **Invoice** | A payment request. Direction: outbound (to client) or inbound (from sub). Can cover specific WorkItems or a percentage of overall progress | New | 040, 041, 042 |
| **InvoiceLine** | A line on an invoice, linked to WorkItem(s) it covers | New | 040 |
| **Payment** | A payment received against an invoice | New | 041, 042, 049 |
| **PaymentApplication** | A formal progress claim / draw request (common on commercial work with staged billing) | New | 047, 048 |

**Naming note — Variation not ChangeOrder:** "Change order" is US-specific. "Variation" is the term used in UK, Australia, and international contracts (JCT, NEC, FIDIC). It's the more globally understood term for a scope/cost change.

### Workforce

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Worker** | A person who does work on projects. Carries trade, certifications, language preference. May or may not have a system login | Existing (enriched) | 015, 016, 028, 029, 035, 052, 056 |
| **Certification** | An instance of a worker holding a specific certification. Links to CertificationType. Has expiry date | Existing | 016, 056 |
| **Crew** | A named group of workers who typically work together. Has a foreman/lead. Referenced by WorkPackage/WorkItem assignment and for productivity analysis | New | 015, 052 |

### Equipment

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Equipment** | A piece of equipment or vehicle owned or rented | Existing | 017, 019 |
| **EquipmentInspectionLog** | An inspection record for a piece of equipment | Existing | 017 |

### Safety & Quality

All inspection and observation entities. Re-examined for consolidation and global naming.

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Inspection** | A site inspection event. `category` field distinguishes: safety, quality, environmental, equipment, simulated (replacing MockInspectionResult as a separate entity). One walk can produce multiple inspection categories | Existing (consolidated) | 022, 025, 057 |
| **InspectionItem** | A single checklist item within an inspection | Existing | 025 |
| **Incident** | A safety incident (injury, near-miss, property damage, environmental spill) | Existing | 053 |
| **HazardReport** | A hazard observation reported by anyone on site | Existing | 026 |
| **HazardObservation** | A specific hazard identified within a HazardReport (child item, like InspectionItem is to Inspection). Renamed from IdentifiedHazard for clarity | Existing (renamed) | 026 |
| **CorrectiveAction** | An action required to fix a finding. Can originate from any source: inspection, incident, hazard report, project query | Existing | 026, 027, 030, 031 |
| **ToolboxTalk** | A safety briefing delivered to workers. Jurisdiction-neutral term (used globally). Content generated in the workforce's language(s) | Existing | 058 |
| **ExposureRecord** | A record of worker exposure to a hazardous substance. Links to Substance for jurisdiction-specific limits | Existing | 059 |
| **MorningBrief** | An AI-generated daily briefing summarising risks, schedule, and required actions | Existing | 058 |
| **DeficiencyList** | A list of deficiencies / snags for closeout. Global term — replaces "punch list" (US only) | Existing | 043 |
| **DeficiencyItem** | A single deficiency. Status: identified → assigned → corrected → verified → closed | Existing | 030, 043 |
| **IncidentLogEntry** | An entry in a jurisdiction-required incident record. Replaces OshaLogEntry — the underlying concept is jurisdiction-neutral; the format varies (OSHA 300 in US, accident book in UK, incident register in AU) | Existing (renamed, generalised) | 053, 060 |

**Consolidations:**
- `MockInspectionResult` → absorbed into `Inspection` with `category: "simulated"`
- `IdentifiedHazard` → renamed to `HazardObservation` for clarity
- `OshaLogEntry` → renamed to `IncidentLogEntry` (jurisdiction-neutral)
- `EnvironmentalProgram` → absorbed into `Document` with `type: "environmental_compliance"` (see Documents below)

### Daily Operations

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **DailyLog** | The daily project record. Auto-populated from safety, time, and equipment data. The most legally important document a contractor produces | Existing | 022, 038 |
| **MaterialDelivery** | A record of materials received on site | Existing | 022 |
| **DelayRecord** | A documented delay event with cause, duration, and impact | Existing | 022, 050 |
| **VisitorRecord** | A record of visitors to site | Existing | 022 |

### Scheduling

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Milestone** | A key date or deliverable in the project schedule. Project-level markers (unlike WorkItems which are the tasks themselves) | New | 019, 034 |

**Note:** There is no separate ScheduleTask entity. Scheduling properties (planned start, planned end, dependencies) live on the WorkItem. The WorkItem IS the task. Milestones are project-level date markers that don't represent deliverable work.

### Project Coordination

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **ProjectQuery** | A formal tracked question between project participants requiring a written response. Known as RFI (US), Technical Query/TQ (UK), Site Instruction (AU). The underlying concept: a question with an assignee, due date, and response workflow | New | 063, 064 |
| **QueryResponse** | A response to a ProjectQuery | New | 064 |
| **ReviewSubmission** | A document or product data submitted for review/approval before work proceeds. Known as Submittal (US), material approval (UK/AU). The underlying concept: something requiring sign-off | New | 065 |
| **Warranty** | A warranty obligation on completed work. Scope, dates, terms | New | 046 |

### Subcontractor Management

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **GcRelationship** | A GC-subcontractor relationship between two companies | Existing | 045, 054 |
| **InsuranceCertificate** | A certificate of insurance held by a company. AI-parsed from uploaded documents | Existing | 045, 068 |
| **PrequalPackage** | A prequalification submission from a sub to a GC | Existing | 045 |
| **PaymentRelease** | A payment release document associated with a payment (lien waiver in US, equivalent in other jurisdictions) | Existing | 048 |

### Conversation & Memory

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Conversation** | A chat or voice interaction session. Mode: chat / voice. Absorbs the existing VoiceSession concept — a voice conversation is a Conversation with mode "voice" | New (absorbs VoiceSession) | 032, 033, 061, 062 |
| **Message** | A single message within a conversation. Carries a vector embedding for semantic similarity search. Role: user / assistant / system | New | 032, 062 |
| **Decision** | A decision extracted from a conversation. Records what was decided, the reasoning, and what entities are affected | New | 033 |
| **Insight** | Institutional knowledge expressed in conversation — rates, preferences, patterns. "I use 0.38 hours per receptacle in renovations because low ceilings slow us down" | New | 061 |

**Consolidation:** `VoiceSession` → absorbed into `Conversation` with `mode: "voice"`. Both produce transcripts, both link to entities discussed.

### Documents & Intelligence

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Document** | An uploaded or generated document. Type field covers all variants: safety_plan, risk_assessment, method_statement, environmental_compliance, contract, specification, drawing, insurance_certificate, permit, report. Absorbs EnvironmentalProgram as a document type | Existing (absorbs EnvironmentalProgram) | 008, 013, 044, 066, 069 |
| **DocumentChunk** | A semantic segment of a document with a vector embedding for similarity search. Preserves reading order via NEXT_CHUNK. Links to entities it mentions | New | 008, 066, 067 |

**Consolidation:** `EnvironmentalProgram` → absorbed into `Document` with `type: "environmental_compliance"`. An environmental program is a compliance document. The regulatory requirement for it is captured by `Regulation → REQUIRES_DOCUMENT → DocumentType`.

### Spatial

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **Location** | A physical location (project site, office, storage yard). Structured address + coordinates | Existing | 017, 028 |
| **SafetyZone** | A designated zone within a project site (permit-required, fall hazard, restricted access) | Existing | 025 |

### Agentic

| Entity | Description | New/Existing | CQs |
|--------|-------------|-------------|-----|
| **AgentIdentity** | An AI agent registered in the system. Has scopes, budget, type, version | Existing | A01-A05 |
| **ComplianceAlert** | An alert generated by the compliance agent | Existing | 025 |
| **BriefingSummary** | A summary generated by the briefing agent | Existing | 058 |

---

## Relationship Catalog

### Organisational & Tenant Isolation

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| OWNS_PROJECT | Company → Project | Tenant isolation root | All project CQs |
| EMPLOYS | Company → Worker | Workers belong to a company | 015, 028 |
| HAS_MEMBER | Company → Member | System users in a company | Auth |
| HAS_CONTACT | Company → Contact | External contacts | 001, 004 |
| HAS_EQUIPMENT | Company → Equipment | Equipment ownership | 017 |
| HAS_WORK_CATEGORY | Company → WorkCategory | Company-specific work classification | 005, 006 |
| IN_JURISDICTION | Company → Jurisdiction | Which regulatory jurisdiction applies | 070-073 |
| IN_REGION | Company → Region | Which sub-jurisdiction (state/province) | 055 |
| GC_OVER | Company → Company (via GcRelationship) | GC-sub relationship | 045, 054 |
| BELONGS_TO | AgentIdentity → Company | Agent tenant scoping | A02 |

### The Work Model

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_WORK_PACKAGE | Project → WorkPackage | Grouped work (optional) | 023, 036 |
| HAS_WORK_ITEM | Project → WorkItem | Direct work items (simple projects) | 023, 024, 036 |
| CONTAINS | WorkPackage → WorkItem | Work items within a package | 023, 037 |
| CLASSIFIED_AS | WorkItem → WorkCategory | What type of work this is | 005, 006, 055 |
| PRECEDED_BY | WorkItem → WorkItem | Scheduling dependency | 019, 021 |
| ASSIGNED_TO_WORKER | WorkItem → Worker | Who is doing this work | 015, 035 |
| ASSIGNED_TO_CREW | WorkItem → Crew | Crew assignment | 015, 052 |
| USES_EQUIPMENT | WorkItem → Equipment | Equipment needed | 017 |
| PERFORMED_BY | WorkItem → Company | Sub company performing this work | 054 |
| AT_LOCATION | WorkItem → Location | Where on site | 024 |

### Commercial

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_CONTRACT | Project → Contract | Formalised agreement | 013, 038, 047 |
| CLIENT_IS | Project → Contact | Client contact for this project | 001, 004, 011 |
| CLIENT_COMPANY | Project → Company | Client organisation | 001, 011 |

### Financial

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_TIME_ENTRY | WorkItem → TimeEntry | Actual time logged against this work | 028, 036, 037 |
| LOGGED_BY | TimeEntry → Worker | Who worked this time | 028, 029 |
| FOR_PROJECT | TimeEntry → Project | Which project (redundant but useful for direct queries) | 028, 036 |
| HAS_VARIATION | Project → Variation | Scope/cost changes | 038, 039, 050 |
| EVIDENCED_BY | Variation → DailyLog / TimeEntry / Document | Evidence supporting the variation | 039 |
| VARIES | Variation → WorkItem | Which work items are added/changed | 038 |
| HAS_INVOICE | Project → Invoice | Invoices for this project | 040, 041, 042 |
| HAS_LINE | Invoice → InvoiceLine | Lines on the invoice | 040 |
| COVERS | InvoiceLine → WorkItem | Which work items this line covers | 040 |
| PAID_BY | Invoice → Payment | Payments received | 041, 042, 049 |
| HAS_PAYMENT_APP | Project → PaymentApplication | Progress claims | 047, 048 |
| WAIVED_BY | PaymentApplication → PaymentRelease | Payment release documents | 048 |

### Workforce

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| ASSIGNED_TO_PROJECT | Worker → Project | Worker assigned to project | 015, 028 |
| HOLDS_CERT | Worker → Certification | Certifications held | 016, 056 |
| OF_TYPE | Certification → CertificationType | What kind of certification | 056 |
| HAS_TRADE | Worker → TradeType | Worker's trade(s) | 015 |
| MEMBER_OF | Worker → Crew | Crew membership | 052 |
| LED_BY | Crew → Worker | Crew foreman/lead | 015 |

### Safety & Quality

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_INSPECTION | Project → Inspection | Inspections on this project | 022, 025, 057 |
| CONDUCTED_BY | Inspection → Worker/Member | Who performed the inspection (regulatory requirement) | 025 |
| HAS_ITEM | Inspection → InspectionItem | Checklist items | 025 |
| HAS_INCIDENT | Project → Incident | Incidents on this project | 053 |
| INVOLVED_IN | Worker → Incident | Worker involved (role: injured_party, witness, first_responder) | 053 |
| HAS_HAZARD_REPORT | Project → HazardReport | Hazard observations | 026 |
| REPORTED_BY | HazardReport → Worker/Member | Who reported the hazard (may differ from data entry person) | 026 |
| HAS_OBSERVATION | HazardReport → HazardObservation | Individual hazards within a report | 026 |
| HAS_CORRECTIVE_ACTION | (multiple) → CorrectiveAction | Required fixes from any source | 026, 027 |
| RESOLVE_BY | CorrectiveAction → Worker/Company | Who must fix it | 027 |
| HAS_TOOLBOX_TALK | Project → ToolboxTalk | Safety briefings | 058 |
| ATTENDED_BY | ToolboxTalk → Worker | Who attended | 058 |
| HAS_EXPOSURE | Worker → ExposureRecord | Substance exposure records | 059 |
| EXPOSURE_TO | ExposureRecord → Substance | Which substance | 059 |
| HAS_INCIDENT_LOG | Company → IncidentLogEntry | Jurisdiction-required incident records | 053, 060 |
| RECORDS | IncidentLogEntry → Incident | Which incident this log entry records | 053 |
| HAS_DEFICIENCY_LIST | Project → DeficiencyList | Deficiency lists for this project | 043 |
| HAS_DEFICIENCY | DeficiencyList → DeficiencyItem | Items on the list | 030, 043 |
| RESOLVE_BY | DeficiencyItem → Worker/Company | Who must fix it | 043 |

### Daily Operations

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_DAILY_LOG | Project → DailyLog | Daily records | 022, 038 |
| RECORDED_ON | TimeEntry → DailyLog | Time entries for this day's log | 022, 028 |
| RECORDED_ON | Inspection → DailyLog | Inspections captured in this day's log | 022 |
| RECORDED_ON | Incident → DailyLog | Incidents captured in this day's log | 022 |
| HAS_SUB_CREW | DailyLog → Company | Sub company headcount for the day (headcount property on relationship) | 022 |
| HAS_DELIVERY | DailyLog → MaterialDelivery | Deliveries that day | 022 |
| HAS_DELAY | DailyLog → DelayRecord | Delays that day | 022, 050 |
| HAS_VISITOR | DailyLog → VisitorRecord | Visitors that day | 022 |

### Scheduling

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_MILESTONE | Project → Milestone | Key dates | 019, 034 |

### Spatial

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| LOCATED_AT | Project → Location | Project site location | — |
| HAS_SAFETY_ZONE | Project → SafetyZone | Designated zones within the site | 025 |

### Project Coordination

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_QUERY | Project → ProjectQuery | Formal queries on this project | 063 |
| HAS_RESPONSE | ProjectQuery → QueryResponse | Responses to a query | 064 |
| ASSIGNED_TO_RESPONDER | ProjectQuery → Contact/Member | Who must respond | 064 |
| HAS_SUBMISSION | Project → ReviewSubmission | Documents submitted for approval | 065 |
| HAS_WARRANTY | Project → Warranty | Warranty obligations | 046 |

### Subcontractor Management

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_INSURANCE | Company → InsuranceCertificate | Insurance held | 045, 068 |
| HAS_PREQUAL | Company → PrequalPackage | Prequalification submissions | 045 |
| SUB_ON | Company → Project | Sub working on this project | 045, 054 |

### Conversation & Memory

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_CONVERSATION | Company → Conversation | Tenant scoping | 032, 062 |
| ABOUT_PROJECT | Conversation → Project | Which projects discussed | 032 |
| PART_OF | Message → Conversation | Message belongs to conversation | 062 |
| FOLLOWS | Message → Message | Preserves message order | 062 |
| SENT_BY | Message → Member/AgentIdentity | Who sent this | A01 |
| REFERENCES | Message → (any entity) | Entities discussed in message | 032, 062 |
| PRODUCED_DECISION | Conversation → Decision | Decisions extracted | 033 |
| AFFECTS | Decision → (any entity) | What the decision impacts | 033 |
| EXPRESSED_KNOWLEDGE | Conversation → Insight | Institutional knowledge captured | 061 |

### Documents & Intelligence

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_DOCUMENT | Project → Document | Documents for this project | 044, 069 |
| CHUNK_OF | DocumentChunk → Document | Chunk belongs to document | 066 |
| NEXT_CHUNK | DocumentChunk → DocumentChunk | Reading order | 066 |
| MENTIONS | DocumentChunk → (any entity) | Entities mentioned in chunk | 008, 066, 067 |

### Regulatory (Layer 3 — Rules as traversable structure)

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| HAS_REGION | Jurisdiction → Region | Sub-jurisdictions | 055 |
| BELONGS_TO_GROUP | Regulation → RegulatoryGroup | Regulation groupings | 055 |
| REGULATED_BY | Activity → Regulation | Which regulations govern this activity | 007, 055 |
| REQUIRES_CONTROL | Regulation → CertificationType | What certs/controls are required. Carries `when` condition | 016, 056 |
| REQUIRES_DOCUMENT | Regulation → DocumentType | What documents are required | 069 |
| REQUIRES_ROLE | Regulation → Role | What roles must be filled | 015 |
| HAS_CLASSIFICATION | Jurisdiction → IncidentClassification | How incidents are classified here | 053 |
| HAS_VIOLATION_TYPE | Jurisdiction → ViolationType | Violation categories | 025 |
| HAS_RECORD_FORM | Jurisdiction → RecordForm | Required record-keeping forms | 060 |
| SUPERSEDES | Regulation → Regulation | Version chain for amended regulations | A03 |
| INVOLVES_SUBSTANCE | Activity → Substance | Hazardous substances associated with activity | 059 |
| LINKS_TO_ACTIVITY | WorkCategory → Activity | Work category maps to regulated activities | 055, 056 |

### Access & Permissions

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| MANAGES | Member → Project | Manager-level access to a project | 074 |
| HAS_ACCESS_GRANT | Member/Contact → AccessGrant | Explicit access exception | 074, 077-080 |
| GRANT_FOR | AccessGrant → Project/Company | What the grant gives access to | 077-080 |

**How external access works:**
- A GC Contact gets an AccessGrant scoped to compliance data on a specific Project
- A client Contact gets an AccessGrant scoped to progress + invoices on their Project
- An architect Contact gets an AccessGrant scoped to ProjectQueries + ReviewSubmissions
- AccessGrants carry: `scopes` (what data domains), `granted_by`, `granted_at`, `expires_at`
- Expired grants are automatically invalid. No manual revocation needed for time-limited access

**How internal role depth works (enforced at service layer):**
```
owner/admin  → can traverse: everything within the company
manager      → can traverse: assigned projects → full depth (including commercial)
foreman      → can traverse: assigned projects → work items, time, inspections
               STOPS at: estimate margins, invoice amounts, payment data
worker       → can traverse: own assignments, own time entries, safety data
               STOPS at: other workers' data, all commercial data
```

### Agentic

| Relationship | From → To | Purpose | CQs |
|-------------|-----------|---------|-----|
| BELONGS_TO | AgentIdentity → Company | Tenant scoping | A02 |
| HAS_GRANT | AgentIdentity → Company | Permission scopes (independently revocable) | A02 |
| GENERATED_BY | ComplianceAlert/BriefingSummary → AgentIdentity | Provenance | A01 |

---

## Vector Indexes

| Index Name | Node Label | Property | Purpose | CQs |
|------------|-----------|----------|---------|-----|
| message_embeddings | Message | embedding | Semantic search over past conversations | 062 |
| chunk_embeddings | DocumentChunk | embedding | Semantic search over document content | 066, 067 |

---

## Consolidations from Existing Schema

| Old Entity | Action | Rationale |
|-----------|--------|-----------|
| MockInspectionResult | → Inspection with `category: "simulated"` | Same structure as Inspection, differs only by category |
| EnvironmentalProgram | → Document with `type: "environmental_compliance"` | A compliance document. Regulatory requirement captured by Regulation → DocumentType |
| VoiceSession | → Conversation with `mode: "voice"` | Both produce transcripts and link to entities. Same underlying concept |
| IdentifiedHazard | → HazardObservation (renamed) | Clearer name. Same parent-child pattern as InspectionItem |
| OshaLogEntry | → IncidentLogEntry (renamed) | US-specific name for a jurisdiction-neutral concept |
| ComplianceProgram | Kept as regulatory entity | It's a TYPE of required program (fall protection plan, hearing conservation program), not a document instance. DocumentType covers the document; ComplianceProgram covers the regulatory requirement for a program of activities |

---

## CQ Coverage

All 86 CQs + 5 agentic CQs = 91 total are answerable. The full coverage matrix mapping each CQ to specific entities and relationships is maintained separately due to size.

## Entity Count

| Category | Entities | New | Existing | Consolidated |
|----------|---------|-----|----------|-------------|
| Organisational & Locale | 3 | 1 | 2 | 0 |
| Regulatory | 17 | 0 | 17 | 0 |
| Work Model | 4 | 3 | 1 | 0 |
| Commercial | 1 | 1 | 0 | 0 |
| Financial | 6 | 6 | 0 | 0 |
| Workforce | 3 | 1 | 2 | 0 |
| Equipment | 2 | 0 | 2 | 0 |
| Safety & Quality | 12 | 0 | 12 | 3 absorbed |
| Daily Operations | 4 | 0 | 4 | 0 |
| Scheduling | 1 | 1 | 0 | 0 |
| Project Coordination | 4 | 4 | 0 | 0 |
| Sub Management | 4 | 0 | 4 | 0 |
| Conversation & Memory | 4 | 4 | 0 | 1 absorbed |
| Documents & Intelligence | 2 | 1 | 1 | 1 absorbed |
| Spatial | 2 | 0 | 2 | 0 |
| Access & Permissions | 1 | 1 | 0 | 0 |
| Agentic | 3 | 0 | 3 | 0 |
| **Total** | **~73** | **~23** | **~50** | **5 absorbed** |
