# Kerf Construction Ontology

*Version 2.3 — 2026-04-08*

**v2.3 changes:** Expanded Quality domain (renamed PunchList/PunchItem to DeficiencyList/DeficiencyItem, added NonConformanceReport, Observation, InspectionTestPlan with HoldPoint/WitnessPoint, MaterialTestRecord). Renamed Budget.budget_type to contract_type. Updated AgentIdentity with cost control fields from Agentic Infrastructure Playbook. Updated Actor Provenance with model_id and confidence. Added temporal validity to Regulation nodes. Added UK site register note to time tracking.

**v2.2 changes:** Removed all redundant foreign-key-style `_id` properties from operational nodes — graph relationships replace property-based joins (aligns with Design Principle #6). Removed `company_id` from all nodes — tenant isolation is enforced by graph traversal, not query-layer filtering. Added 20+ missing relationships to replace CONVERT-category properties. Added Domain 15: Procurement. Added ScheduleDependency reification relationships. Removed ScheduleDependency node (replaced by DEPENDS_ON relationship with properties). Added new Design Principle #8 (no foreign key properties).

**v2.1 changes:** Graph-native permissions (Design Principle #6 rewritten), AgentIdentity node added to Domain 2, Actor Provenance fields added as universal schema, AI-powered regulatory population strategy added to Domain 1.

This document defines the knowledge graph schema for Kerf — the formal data language for construction operations. Every node label, relationship type, and property is specified here. The ontology covers all 15 domains needed for a comprehensive construction operations platform, even those not yet implemented.

The ontology is the ceiling of agent intelligence. An agent can only reason about relationships that exist in the graph.

---

## Terminology

| Term | Definition | Relational DB Equivalent |
|---|---|---|
| **Node** | An entity — a thing that exists and can have relationships. A Worker, a Project, an Inspection. | A table/row |
| **Property** | A piece of data stored on a node. `Worker.first_name`, `Worker.status`. Essentially a field. | A column |
| **Relationship (Edge)** | A typed, directional connection between two nodes. `Worker -[ASSIGNED_TO]-> Project`. Relationships can also carry properties (e.g. `start_date`). | A foreign key / join table |
| **Label** | The type of a node. `Worker`, `Project`, `Inspection`. A node can have multiple labels. | A table name |
| **Required** | The property must have a value. Cannot be null. | NOT NULL constraint |
| **Optional** | The property can be null/absent. | Nullable column |
| **Unique** | The property value must be unique across all nodes of this label. | UNIQUE constraint |
| **Indexed** | The property is indexed for fast lookup. Used in WHERE clauses. | Database index |

---

## Design Principles

1. **Standards organise by hazard/activity, not by trade.** OSHA does not map standards to trades — it maps them to activities and exposures. The graph follows this: `Trade -[PERFORMS]-> Activity -[REGULATED_BY]-> Regulation`, never `Trade -[REQUIRES]-> Regulation` directly.

2. **Separate Type from Instance.** Following IFC and COBie patterns: `EquipmentType` (the specification) vs `Equipment` (a specific physical asset). `CertificationType` (the credential definition) vs `Certification` (a specific cert held by a worker).

3. **Location is a first-class hub node.** Location connects safety, quality, scheduling, equipment, materials, and incidents. It is a node, not a string property. Uses typed edges (`OCCURRED_AT`, `DEPLOYED_TO`) not generic `has_location`.

4. **Recursive spatial hierarchy.** Following Procore's proven unlimited-tier approach: `Location -[CONTAINS]-> Location`. Not a fixed 4-level schema.

5. **Cross-domain edges are the intelligence layer.** The value of the graph is in the edges that connect domains — regulatory to HR, scheduling to safety, financial to compliance. These are explicitly catalogued.

6. **Graph-native permissions: access = traversability.** Every operational node is reachable only through its owning Company. There is no separate ACL — if no path exists from an actor (Member or AgentIdentity) through a Company to the data, the query returns nothing. Regulatory nodes are shared across all tenants. See [Agentic Architecture](AGENTIC_ARCHITECTURE.md) §2 for permission traversal patterns.

   > *Historical note: v1.0 used `WHERE n.company_id = $cid` query-layer filtering. v2.0 replaces this with graph-native permissions where the domain relationships themselves enforce tenant isolation.*

7. **Temporal validity on relationships.** Assignments, deployments, and zones have `effective_from` / `effective_until` properties. The graph supports "what was true on date X" queries.

8. **No foreign key properties.** If a value references another node, it MUST be a relationship, not a stored property. The only `_id` properties allowed on a node are its own identifier, external system IDs (e.g., `subscription_id` for Stripe), and grouping keys that don't reference a graph node (e.g., `crew_entry_id`, `split_group_id`). This prevents the "relational thinking in a graph database" anti-pattern.

---

## Domain 1: Regulatory

The static knowledge base of construction regulations. Shared across all tenants within a jurisdiction.

**Population strategy: AI-encoded, not manually curated.** Regulatory source material (eCFR, state plan comparisons, OSHA Letters of Interpretation) is public, structured, and unambiguous. AI extracts rules as graph operations, every edge carries a `source` citation and `effective_date`, automated validation checks schema conformance and citation completeness, and 10% is spot-checked by a human. This is NOT a RAG system — the rules are encoded as deterministic graph structure, not retrieved as text for LLM interpretation. See [Agentic Architecture](AGENTIC_ARCHITECTURE.md) §8 for the full pipeline.

**Design principle: Jurisdiction-neutral core.** The graph uses generic node labels (`Regulation`, `ComplianceProgram`, `CertificationType`) that work across any country's regulatory framework. OSHA (US), HSE (UK), Safe Work Australia, CCOHS (Canada), and other jurisdictions plug into the same structure. Jurisdiction-specific properties (like CFR references or CDM regulation numbers) are stored as properties, not embedded in the schema.

### Jurisdiction

> The top-level regulatory authority for a country or sovereign territory.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `code` | string | Yes | Unique | ISO-style country code (US, UK, AU, CA, AE) |
| `name` | string | Yes | No | Full jurisdiction name (e.g. "United States") |
| `regulatory_body` | string | Yes | No | Primary regulatory agency (OSHA, HSE, SWA, CCOHS) |
| `primary_legislation` | string | No | No | Primary act or law (e.g. "OSH Act 1970", "HSWA 1974") |
| `enforcement_agency` | string | No | No | Agency that enforces regulations |
| `penalty_currency` | string | Yes | No | ISO currency code for penalties (USD, GBP, AUD) |
| `language_codes` | string[] | No | No | Supported language codes (e.g. ["en", "es"]) |

---

### Region

> A sub-national regulatory subdivision (state, province, devolved nation) that may impose additional requirements.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `code` | string | Yes | Unique | Compound code (US-CA, US-NY, UK-SCT, AU-NSW) |
| `name` | string | Yes | No | Region name (e.g. "California", "New South Wales") |
| `jurisdiction_code` | string | Yes | Lookup | Parent jurisdiction code |
| `agency_name` | string | No | No | Regional enforcement agency (e.g. "Cal/OSHA") |
| `has_own_plan` | boolean | Yes | No | Whether region has its own approved state plan (US) |

---

### RegulatoryGroup

> A grouping container for related regulations within a jurisdiction. Corresponds to OSHA Subparts, CDM Parts, or WHS Regulation chapters.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this group belongs to |
| `name` | string | Yes | No | Group name (e.g. "Subpart M - Fall Protection") |
| `description` | string | No | No | Description of the regulatory group |
| `sort_order` | integer | No | No | Display ordering within the jurisdiction |

---

### Regulation

> An individual regulation, standard, or code section. The `reference` format is jurisdiction-specific.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `reference` | string | Yes | Unique | Jurisdiction-specific reference (e.g. "1926.501", "CDM 2015 Reg 22", "WHS Reg 78") |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this regulation belongs to |
| `title` | string | Yes | No | Regulation title |
| `text_summary` | string | No | No | Plain-language summary of the regulation |
| `effective_date` | date | No | No | Date the regulation became effective |
| `version` | string | No | No | Version identifier for tracking changes |
| `valid_from` | date | No | No | Date this version of the regulation became effective |
| `valid_until` | date | No | No | Date this version was superseded (null = currently active) |

---

### ComplianceProgram

> A required written program triggered by a regulation. US: "Fall Protection Plan". UK: "Construction Phase Plan". AU: "Safe Work Method Statement".

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `name` | string | Yes | Unique | Program name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this program applies to |
| `regulation_trigger` | string | No | No | Regulation reference that triggers this program requirement |
| `severity` | string | Yes | Filter | Criticality level |
| `document_type_key` | string | No | No | Maps to a DocumentType for the program's written document |
| `search_terms` | string[] | No | No | Keywords for matching documents to this program |
| `required_for` | string | Yes | No | Applicability scope |
| `penalty_min` | integer | No | No | Minimum penalty amount in smallest currency unit |
| `penalty_max` | integer | No | No | Maximum penalty amount in smallest currency unit |
| `penalty_currency` | string | No | No | ISO currency code for penalties |

**Enums:**
- `severity`: critical | high | medium | low
- `required_for`: all | trade-specific

---

### CertificationType

> A credential definition that workers can obtain. OSHA-10 (US), CSCS Card (UK), White Card (AU). The type definition, not the instance.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (e.g. "OSHA_10", "CSCS_CARD", "WHITE_CARD") |
| `name` | string | Yes | No | Short name |
| `full_name` | string | No | No | Full official certification name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this cert type belongs to |
| `expires` | boolean | Yes | No | Whether the certification expires |
| `validity_years` | integer | No | No | Years until expiry (if expires = true) |
| `required_for` | string[] | No | No | Activities or roles requiring this cert |
| `issuing_body` | string | No | No | Organization that issues the certification |
| `exam_type` | string | No | No | Type of examination required |
| `international_equivalents` | string[] | No | No | CertificationType IDs recognised as equivalent in other jurisdictions |

---

### TradeType

> A construction trade classification. Universal across jurisdictions.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Trade name (e.g. "Electrician", "Plumber", "Ironworker") |
| `union_code` | string | No | No | Union trade code (if applicable) |

---

### Role

> A job function or responsibility level on a construction project. The role is universal; the title varies by jurisdiction.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (e.g. "foreman", "site_manager", "principal_contractor") |
| `name` | string | Yes | No | Universal role name |
| `risk_level` | string | No | No | Risk classification of the role |
| `jurisdiction_specific_title` | string | No | No | Title as used in the jurisdiction (e.g. "site supervisor" in UK/AU for "foreman" in US) |

---

### Activity

> A type of construction work activity. Universal across jurisdictions. Links trades to regulatory requirements.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Activity name (e.g. "excavation", "working at height", "hot work") |
| `description` | string | No | No | Activity description |
| `hazard_exposure` | string[] | No | No | HazardCategory IDs this activity exposes workers to |

---

### HazardCategory

> A category of workplace hazard. Universal: Falls, Struck-By, Caught-In/Between, Electrocution, Heat, Noise, Chemical.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Hazard category name |
| `description` | string | No | No | Description of the hazard category |

---

### Substance

> A regulated substance with occupational exposure limits. Limits vary by jurisdiction.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `name` | string | Yes | No | Substance name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction defining the exposure limits |
| `oel` | float | No | No | Occupational Exposure Limit (US: PEL, UK: WEL, AU: WES) |
| `action_level` | float | No | No | Action level triggering monitoring requirements |
| `unit` | string | No | No | Measurement unit (e.g. "mg/m3", "ppm", "f/cc") |
| `regulation_reference` | string | No | No | Regulation that defines this limit |

---

### DocumentType

> A type of safety/compliance document required by regulation. US: SSSP, JHA, Toolbox Talk. UK: CPP, Risk Assessment, Method Statement.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Document type name |
| `abbreviation` | string | No | No | Common abbreviation (e.g. "SSSP", "JHA", "CPP") |
| `regulation_reference` | string | No | No | Regulation requiring this document type |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this document type belongs to |
| `required_sections` | string[] | No | No | Required sections/chapters for this document type |

---

### InspectionType

> A type of safety or quality inspection. Largely universal with jurisdiction-specific regulatory basis.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Inspection type name |
| `description` | string | No | No | Description of what this inspection covers |

---

### RegionalRequirement

> A sub-national regulatory addition. US: Cal/OSHA heat rules. AU: NSW-specific codes. Extends national regulations.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `region_code` | string | Yes | Lookup | Region that imposes this requirement |
| `requirement_name` | string | Yes | No | Name of the regional requirement |
| `standard_reference` | string | No | No | Regional regulation reference |
| `severity` | string | No | No | Criticality level (critical/high/medium/low) |
| `national_equivalent` | string | No | No | Equivalent national regulation reference (if any) |
| `description` | string | No | No | Description of the regional requirement |

---

### ViolationType

> A classification of regulatory violation and its penalty structure. US: Serious/Willful/Repeat. UK: Improvement Notice/Prohibition Notice.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `code` | string | Yes | Unique | Violation type code |
| `name` | string | Yes | No | Violation type name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction defining this violation type |
| `min_penalty` | integer | No | No | Minimum penalty amount in smallest currency unit |
| `max_penalty` | integer | No | No | Maximum penalty amount in smallest currency unit |
| `currency` | string | No | No | ISO currency code |

---

### IncidentClassification

> How incidents are classified for regulatory reporting. US: OSHA recordable. UK: RIDDOR reportable. AU: WHS notifiable.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Classification name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction defining this classification |
| `recordable` | boolean | Yes | No | Whether incidents of this type are recordable |
| `reportable` | boolean | Yes | No | Whether incidents of this type must be reported to authorities |
| `report_deadline_hours` | integer | No | No | Hours within which the report must be filed |

---

### RecordForm

> A regulatory record-keeping form. US: OSHA 300/301/300A. UK: RIDDOR F2508. AU: WHS incident notification.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `form_id` | string | Yes | Unique | Form identifier |
| `name` | string | Yes | No | Form name |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction requiring this form |
| `frequency` | string | No | No | Filing frequency (annual, per-incident, etc.) |
| `retention_years` | integer | No | No | Required retention period in years |

---

### RegulatoryVersion

> Version tracking for regulatory changes within a jurisdiction.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `version_id` | string | Yes | Unique | Version identifier |
| `jurisdiction_code` | string | Yes | Lookup | Jurisdiction this version applies to |
| `effective_date` | date | Yes | Sort | Date the version became effective |
| `description` | string | No | No | Description of what changed |

---

### Relationships

```
(Jurisdiction)-[:HAS_REGION]->(Region)
(Jurisdiction)-[:ENFORCES]->(Regulation)
(Regulation)-[:PART_OF_GROUP]->(RegulatoryGroup)
(Regulation)-[:REQUIRES_PROGRAM]->(ComplianceProgram)
(Regulation)-[:REQUIRES_CERTIFICATION]->(CertificationType)
(Regulation)-[:GOVERNS_SUBSTANCE]->(Substance)
(Regulation)-[:ADDRESSES_HAZARD]->(HazardCategory)
(Regulation)-[:REQUIRES_DOCUMENT]->(DocumentType)
(Regulation)-[:REQUIRES_INSPECTION]->(InspectionType)
(Regulation)-[:CLASSIFIES_INCIDENT]->(IncidentClassification)
(Role)-[:REQUIRES_CERT {jurisdiction_code}]->(CertificationType)
(TradeType)-[:PERFORMS]->(Activity)
(Activity)-[:REGULATED_BY]->(Regulation)
(Activity)-[:EXPOSES_TO]->(HazardCategory)
(HazardCategory)-[:ADDRESSED_BY]->(Regulation)
(ComplianceProgram)-[:DOCUMENTED_AS]->(DocumentType)
(Region)-[:ADDS_REQUIREMENT]->(RegionalRequirement)
(RegionalRequirement)-[:EXTENDS]->(Regulation)
(Regulation)-[:EQUIVALENT_IN {jurisdiction_code}]->(Regulation)  // cross-jurisdiction equivalence
(CertificationType)-[:RECOGNISED_AS {jurisdiction_code}]->(CertificationType)  // international cert recognition
(RecordForm)-[:AGGREGATES]->(RecordForm)
(RegulatoryVersion)-[:SNAPSHOTS]->(Regulation)
(CertificationType)-[:QUALIFIES_FOR]->(InspectionType)
(Regulation)-[:SUPERSEDES]->(Regulation)  // links current version to the version it replaced
```

### Jurisdiction examples

**US (OSHA):** `Regulation.reference = "1926.501"`, `RegulatoryGroup.name = "Subpart M - Fall Protection"`, `ComplianceProgram.name = "Fall Protection Plan"`, `CertificationType.id = "OSHA_10"`

**UK (HSE):** `Regulation.reference = "CDM 2015 Reg 22"`, `RegulatoryGroup.name = "CDM Part 4 - Duties Relating to Health and Safety on Construction Sites"`, `ComplianceProgram.name = "Construction Phase Plan"`, `CertificationType.id = "CSCS_CARD"`

**Australia (SWA):** `Regulation.reference = "WHS Reg 78"`, `RegulatoryGroup.name = "WHS Regulations Chapter 6 - Construction Work"`, `ComplianceProgram.name = "Safe Work Method Statement"`, `CertificationType.id = "WHITE_CARD"`

The same graph query ("does this worker have the certs required for this activity?") works regardless of jurisdiction because the node labels and relationship types are the same — only the properties differ.

---

## Domain 2: Organisational

### Company

> A construction company operating on the platform. Can be a GC, subcontractor, or both depending on relationships.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`comp_{token_hex(8)}`) |
| `name` | string | Yes | No | Company legal name |
| `address` | string | No | No | Primary business address |
| `license_number` | string | No | No | Contractor license number |
| `trade_type` | string | No | No | Primary trade classification |
| `owner_name` | string | No | No | Company owner/principal name |
| `phone` | string | No | No | Primary phone number |
| `email` | string | No | No | Primary email address |
| `ein` | string | No | No | Employer Identification Number (US) |
| `jurisdiction_code` | string | Yes | Lookup | Primary jurisdiction of operation |
| `jurisdiction_region` | string | No | No | Primary region of operation |
| `subscription_status` | string | Yes | Filter | Platform subscription status |
| `subscription_id` | string | No | No | Stripe or payment provider subscription ID |
| `created_at` | datetime | Yes | Sort | Timestamp of company creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `subscription_status`: trial | active | past_due | cancelled

---

### Member

> A user account within a company, representing a person who can log in and perform actions on the platform.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`mem_{token_hex(8)}`) |
| `uid` | string | Yes | Unique | Firebase Auth UID |
| `email` | string | Yes | Lookup | Member email address |
| `display_name` | string | No | No | Display name |
| `role` | string | Yes | Filter | Platform role within the company |
| `joined_at` | datetime | No | No | When the member joined the company |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `role`: OWNER | ADMIN | EDITOR | VIEWER

---

### Project

> A construction project managed on the platform. Central hub node connecting workers, equipment, safety records, and schedule.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`proj_{token_hex(8)}`) |
| `name` | string | Yes | No | Project name |
| `address` | string | No | No | Project site address |
| `client_name` | string | No | No | Client/owner name |
| `project_type` | string | No | Filter | Type of construction project |
| `status` | string | Yes | Filter | Project lifecycle status |
| `start_date` | date | No | Sort | Project start date |
| `end_date` | date | No | No | Project end date |
| `estimated_workers` | integer | No | No | Estimated peak worker count |
| `description` | string | No | No | Project description |
| `special_hazards` | string | No | No | Known special hazards on site |
| `nearest_hospital` | string | No | No | Nearest hospital name and address |
| `emergency_contact_name` | string | No | No | Site emergency contact name |
| `emergency_contact_phone` | string | No | No | Site emergency contact phone |
| `compliance_score` | integer | No | No | Calculated compliance score (0-100) |
| `created_at` | datetime | Yes | Sort | Timestamp of project creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: active | completed | on_hold

---

### AgentIdentity

> An AI agent registered to act on behalf of a company. First-class graph citizen — the `BELONGS_TO` relationship to a Company IS the agent's permission boundary. An agent can only traverse to data reachable from its owning Company.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `agent_id` | string | Yes | Unique | Internal identifier (`agt_{token_hex(8)}`) |
| `name` | string | Yes | No | Human-readable agent name (e.g. "Compliance Checker", "Morning Brief Generator") |
| `agent_type` | string | Yes | Filter | Agent category |
| `status` | string | Yes | Filter | Agent lifecycle status |
| `scopes` | string[] | Yes | No | Permitted operation scopes (e.g. ["read:safety", "write:inspections"]) |
| `model_tier` | string | Yes | No | Default model tier for this agent |
| `daily_budget_cents` | integer | Yes | No | Maximum daily LLM spend in cents |
| `daily_spend_cents` | integer | No | No | Current day's accumulated LLM spend in cents (reset daily) |
| `created_at` | datetime | Yes | Sort | Timestamp of agent creation |
| `created_by` | string | Yes | No | Member who registered this agent |

**Enums:**
- `agent_type`: compliance | briefing | intake | forecast | external
- `status`: active | suspended | revoked
- `model_tier`: fast | standard | advanced

---

### Actor Provenance

> Every node that can be created or mutated carries these additional properties to distinguish human actions from agent actions. This applies to ALL operational nodes across ALL domains.

| Property | Type | Required | Description |
|---|---|---|---|
| `created_by` | string | Yes | Actor ID — Member UID or agent_id |
| `actor_type` | string | Yes | `"human"` or `"agent"` |
| `agent_id` | string | No | Agent ID if actor_type is "agent", null otherwise |
| `updated_by` | string | Yes | Actor ID of last updater |
| `updated_actor_type` | string | Yes | `"human"` or `"agent"` |
| `model_id` | string | No | Model ID used if actor_type is "agent" (for cost attribution) |
| `confidence` | float | No | Agent's declared confidence for this action (0.0-1.0), null for human actions |

> *These fields supersede the simple `created_by`/`updated_by` string fields defined on individual nodes. All operational nodes inherit this schema.*

---

### Relationships

```
(Company)-[:HAS_MEMBER]->(Member)
(Company)-[:OWNS_PROJECT]->(Project)
(Company)-[:OPERATES_IN]->(Jurisdiction)
(Company)-[:OPERATES_IN_REGION]->(Region)
(Company)-[:PERFORMS_TRADE]->(TradeType)
(Project)-[:INVOLVES_TRADE]->(TradeType)

(Company)-[:HAS_AGENT]->(AgentIdentity)
(AgentIdentity)-[:BELONGS_TO {scopes: [...], rate_limit_per_minute: N}]->(Company)
```

---

## Domain 3: Human Resources

### Worker

> An individual construction worker employed by a company. Workers are assigned to projects and hold certifications.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`wrk_{token_hex(8)}`) |
| `first_name` | string | Yes | No | Worker first name |
| `last_name` | string | Yes | No | Worker last name |
| `email` | string | No | Lookup | Worker email address |
| `phone` | string | No | No | Worker phone number |
| `trade` | string | No | Filter | Primary trade |
| `language_preference` | string | No | No | Preferred language code (e.g. "en", "es") |
| `emergency_contact_name` | string | No | No | Emergency contact name |
| `emergency_contact_phone` | string | No | No | Emergency contact phone number |
| `hire_date` | date | No | No | Date of hire |
| `status` | string | Yes | Filter | Employment status |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: active | inactive | terminated

---

### Certification

> A specific certification instance held by a worker. The instance, not the type definition.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`cert_{token_hex(8)}`) |
| `certification_type` | string | Yes | Lookup | CertificationType ID |
| `issued_date` | date | No | No | Date the certification was issued |
| `expiry_date` | date | No | Filter | Date the certification expires |
| `issuing_body` | string | No | No | Organization that issued the certification |
| `certificate_number` | string | No | No | Certification number |
| `proof_document_url` | string | No | No | URL to uploaded proof document |
| `status` | string | Yes | Filter | Certification validity status |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `status`: valid | expiring_soon | expired

---

### Relationships

```
(Company)-[:EMPLOYS]->(Worker)
(Worker)-[:HAS_ROLE]->(Role)
(Worker)-[:WORKS_TRADE]->(TradeType)
(Worker)-[:HOLDS_CERT]->(Certification)
(Certification)-[:OF_TYPE]->(CertificationType)
(Worker)-[:ASSIGNED_TO {role, start_date, end_date, status}]->(Project)
```

---

## Domain 4: Equipment

### Equipment

> A specific physical asset (vehicle, tool, machine) owned by a company and deployed to projects.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`equip_{token_hex(8)}`) |
| `name` | string | Yes | No | Equipment name/description |
| `equipment_type` | string | Yes | Filter | Equipment category |
| `make` | string | No | No | Manufacturer name |
| `model` | string | No | No | Model name/number |
| `year` | integer | No | No | Year of manufacture |
| `serial_number` | string | No | No | Manufacturer serial number |
| `vin` | string | No | No | Vehicle identification number (if applicable) |
| `license_plate` | string | No | No | License plate number (if applicable) |
| `status` | string | Yes | Filter | Equipment operational status |
| `inspection_frequency` | string | No | No | Required inspection frequency (daily/weekly/monthly/annual) |
| `next_inspection_due` | date | No | Filter | Date of next required inspection |
| `next_maintenance_due` | date | No | No | Date of next scheduled maintenance |
| `dot_number` | string | No | No | DOT number (if applicable) |
| `required_certifications` | string[] | No | No | CertificationType IDs required to operate this equipment |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: active | out_of_service | maintenance | retired

---

### EquipmentInspectionLog

> A record of a specific inspection performed on a piece of equipment.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`eqlog_{token_hex(8)}`) |
| `inspection_date` | date | Yes | Sort | Date of inspection |
| `inspector_name` | string | Yes | No | Name of the inspector |
| `inspection_type` | string | No | No | Type of inspection performed |
| `overall_status` | string | Yes | Filter | Inspection result |
| `deficiencies_found` | string | No | No | Description of deficiencies found |
| `corrective_action` | string | No | No | Corrective actions taken |
| `out_of_service` | boolean | No | No | Whether equipment was taken out of service |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `overall_status`: pass | fail | pass_with_notes

---

### Relationships

```
(Company)-[:OWNS_EQUIPMENT]->(Equipment)
(Equipment)-[:IS_TYPE]->(TradeType)  // equipment category mapping
(Equipment)-[:DEPLOYED_TO {start_date, end_date, status}]->(Project)
(Equipment)-[:HAS_INSPECTION_LOG]->(EquipmentInspectionLog)
(EquipmentInspectionLog)-[:FOR_PROJECT]->(Project)
(Equipment)-[:REQUIRES_OPERATOR_CERT]->(CertificationType)
(Worker)-[:OPERATES]->(Equipment)
```

---

## Domain 5: Safety

### Inspection

> A safety or quality inspection conducted on a project site.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`insp_{token_hex(8)}`) |
| `inspection_type` | string | Yes | Filter | Type of inspection |
| `category` | string | Yes | Filter | Inspection category |
| `inspection_date` | date | Yes | Sort | Date of inspection |
| `inspector_name` | string | Yes | No | Name of the inspector |
| `weather_conditions` | string | No | No | Weather at time of inspection |
| `temperature` | float | No | No | Temperature at time of inspection |
| `workers_on_site` | integer | No | No | Number of workers present |
| `overall_status` | string | Yes | Filter | Inspection result |
| `overall_notes` | string | No | No | General inspection notes |
| `corrective_actions_needed` | boolean | No | No | Whether corrective actions are required |
| `gps_latitude` | float | No | No | GPS latitude of inspection location |
| `gps_longitude` | float | No | No | GPS longitude of inspection location |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `category`: safety | quality
- `overall_status`: pass | fail | partial

---

### InspectionItem

> A single checklist item within an inspection.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `category` | string | No | Filter | Item category |
| `description` | string | Yes | No | Description of what was inspected |
| `status` | string | Yes | Filter | Item result |
| `notes` | string | No | No | Additional notes |
| `photo_url` | string | No | No | Photo evidence URL |

**Enums:**
- `status`: pass | fail | na

---

### Incident

> A safety incident that occurred on a project site.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`inc_{token_hex(8)}`) |
| `incident_date` | date | Yes | Sort | Date of the incident |
| `incident_time` | string | No | No | Time of the incident |
| `severity` | string | Yes | Filter | Incident severity level |
| `description` | string | Yes | No | Description of what happened |
| `location` | string | No | No | Location description (freeform; also links to Location node via edge) |
| `status` | string | Yes | Filter | Investigation status |
| `recordable` | boolean | No | Filter | Whether the incident is OSHA recordable |
| `reportable` | boolean | No | No | Whether the incident must be reported to authorities |
| `root_cause` | string | No | No | Identified root cause |
| `corrective_actions` | string | No | No | Corrective actions taken |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `severity`: fatality | hospitalization | medical_treatment | first_aid | near_miss | property_damage
- `status`: reported | investigating | corrective_actions | closed

---

### HazardReport

> An AI-assisted hazard identification report, typically generated from a photo of the work area.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`haz_{token_hex(8)}`) |
| `photo_url` | string | No | No | URL to the hazard photo |
| `description` | string | No | No | Overall hazard report description |
| `location` | string | No | No | Location description (freeform) |
| `hazard_count` | integer | No | No | Number of hazards identified |
| `highest_severity` | string | No | Filter | Highest severity among identified hazards |
| `status` | string | Yes | Filter | Report lifecycle status |
| `gps_latitude` | float | No | No | GPS latitude |
| `gps_longitude` | float | No | No | GPS longitude |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: open | in_progress | corrected | closed

---

### IdentifiedHazard

> A single hazard identified within a HazardReport, typically by AI analysis of a photo.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `description` | string | Yes | No | Description of the specific hazard |
| `severity` | string | Yes | Filter | Hazard severity |
| `osha_standard` | string | No | No | Relevant OSHA standard reference (or jurisdiction equivalent) |
| `category` | string | No | Filter | Hazard category |
| `recommended_action` | string | No | No | Recommended corrective action |
| `location_in_image` | string | No | No | Bounding box or description of location within the photo |

---

### ToolboxTalk

> A short safety briefing/training session conducted on site, typically at the start of a shift.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`tt_{token_hex(8)}`) |
| `topic` | string | Yes | No | Topic of the toolbox talk |
| `scheduled_date` | date | Yes | Sort | Scheduled date |
| `duration_minutes` | integer | No | No | Duration in minutes |
| `status` | string | Yes | Filter | Talk lifecycle status |
| `attendee_count` | integer | No | No | Number of attendees |
| `presented_at` | datetime | No | No | When the talk was presented |
| `presented_by` | string | No | No | Name or ID of the presenter |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: scheduled | in_progress | completed

---

### CorrectiveAction

> An action item generated from an inspection finding, incident, or hazard report that must be addressed.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`ca_{token_hex(8)}`) |
| `description` | string | Yes | No | Description of the required corrective action |
| `assigned_to` | string | No | Lookup | Worker or member ID assigned to complete the action |
| `due_date` | date | No | Sort | Target completion date |
| `status` | string | Yes | Filter | Action lifecycle status |
| `completed_at` | datetime | No | No | When the action was completed |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `status`: open | in_progress | completed | overdue

---

### ExposureRecord

> A monitoring record for worker exposure to a regulated substance.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`exp_{token_hex(8)}`) |
| `monitoring_type` | string | Yes | Filter | Type of exposure monitoring |
| `monitoring_date` | date | Yes | Sort | Date of monitoring |
| `result_value` | float | Yes | No | Measured exposure value |
| `result_unit` | string | Yes | No | Unit of measurement |
| `exceeds_action_level` | boolean | No | No | Whether result exceeds the action level |
| `exceeds_pel` | boolean | No | No | Whether result exceeds the permissible exposure limit |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

---

### MorningBrief

> A daily safety briefing summary for a project, including risk assessment and conditions.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`mb_{token_hex(8)}`) |
| `date` | date | Yes | Unique (per project) | Brief date |
| `risk_score` | integer | No | No | Calculated risk score |
| `risk_level` | string | No | Filter | Risk level classification |
| `weather` | JSON | No | No | Weather conditions data |
| `summary` | string | No | No | AI-generated brief summary |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

---

### MockInspectionResult

> Results from an AI-powered mock OSHA inspection simulation.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`mock_{token_hex(8)}`) |
| `inspection_date` | date | Yes | Sort | Date of the mock inspection |
| `overall_score` | integer | No | No | Score out of 100 |
| `grade` | string | No | No | Letter grade (A/B/C/D/F) |
| `total_findings` | integer | No | No | Total findings count |
| `critical_findings` | integer | No | No | Critical findings count |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

---

### Relationships

```
(Project)-[:HAS_INSPECTION]->(Inspection)
(Inspection)-[:CONTAINS_ITEM]->(InspectionItem)
(Inspection)-[:CONDUCTED_BY]->(Worker)
(Inspection)-[:AT_LOCATION]->(Location)
(Inspection)-[:IS_TYPE]->(InspectionType)

(Project)-[:HAS_INCIDENT]->(Incident)
(Incident)-[:INVOLVES_WORKER]->(Worker)
(Incident)-[:AT_LOCATION]->(Location)
(Incident)-[:CLASSIFIED_AS]->(IncidentClassification)
(Incident)-[:GENERATED_CORRECTIVE_ACTION]->(CorrectiveAction)

(Project)-[:HAS_HAZARD_REPORT]->(HazardReport)
(HazardReport)-[:CONTAINS_HAZARD]->(IdentifiedHazard)
(IdentifiedHazard)-[:IN_CATEGORY]->(HazardCategory)
(IdentifiedHazard)-[:VIOLATES]->(Regulation)
(HazardReport)-[:REPORTED_BY]->(Worker)

(Project)-[:HAS_TOOLBOX_TALK]->(ToolboxTalk)
(ToolboxTalk)-[:ATTENDED_BY]->(Worker)
(ToolboxTalk)-[:COVERS_TOPIC]->(HazardCategory)

(CorrectiveAction)-[:AT_LOCATION]->(Location)
(CorrectiveAction)-[:ASSIGNED_TO_WORKER]->(Worker)
(CorrectiveAction)-[:ADDRESSES]->(Regulation)

(ExposureRecord)-[:MONITORS]->(Substance)
(ExposureRecord)-[:FOR_WORKER]->(Worker)

(Project)-[:HAS_MORNING_BRIEF]->(MorningBrief)
(Project)-[:HAS_MOCK_INSPECTION]->(MockInspectionResult)

(Inspection)-[:GENERATED_CORRECTIVE_ACTION]->(CorrectiveAction)
(HazardReport)-[:GENERATED_CORRECTIVE_ACTION]->(CorrectiveAction)
(Project)-[:HAS_EXPOSURE_RECORD]->(ExposureRecord)
```

---

## Domain 6: Spatial / Location

### Location

> A physical location within a project site. Supports recursive spatial hierarchy for unlimited nesting.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`loc_{token_hex(8)}`) |
| `name` | string | Yes | No | Location name |
| `location_type` | string | Yes | Filter | Type of location |
| `tier_level` | integer | No | No | Depth in the spatial hierarchy (0 = top level) |
| `grid_ref` | string | No | No | Grid reference on site plan |
| `geo_latitude` | float | No | No | GPS latitude |
| `geo_longitude` | float | No | No | GPS longitude |
| `qr_code_id` | string | No | Unique | QR code identifier for field scanning |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `location_type`: site | building | storey | space | zone | area | staging

---

### SafetyZone

> A temporary or permanent safety zone overlaid on locations. Zones can overlap and have temporal validity.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`sz_{token_hex(8)}`) |
| `zone_type` | string | Yes | Filter | Type of safety zone |
| `regulation_ref` | string | No | No | Regulation reference governing this zone |
| `effective_from` | datetime | No | No | When the zone becomes active |
| `effective_until` | datetime | No | No | When the zone expires |
| `permit_id` | string | No | Lookup | Associated permit ID |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

**Enums:**
- `zone_type`: crane_swing | controlled_access | excavation | hot_work | fall_protection

---

### Relationships

```
(Project)-[:HAS_LOCATION]->(Location)
(Location)-[:CONTAINS]->(Location)  // recursive hierarchy
(SafetyZone)-[:COVERS]->(Location)  // many-to-many, overlapping
(SafetyZone)-[:GOVERNED_BY]->(Regulation)
(Project)-[:HAS_SAFETY_ZONE]->(SafetyZone)
```

All domain entities connect to Location via typed edges — see Domain 5 relationships above and cross-domain edges below.

---

## Domain 7: Documents

### Document

> A safety or compliance document created on the platform (SSSP, JHA, Toolbox Talk content, etc.).

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`doc_{token_hex(8)}`) |
| `title` | string | Yes | No | Document title |
| `document_type` | string | Yes | Filter | Document type key |
| `status` | string | Yes | Filter | Document lifecycle status |
| `content` | JSON | No | No | Structured document content |
| `project_info` | string | No | No | Project context for the document |
| `pdf_url` | string | No | No | URL to generated PDF |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: draft | final | archived

---

### OshaLogEntry

> An entry in the OSHA 300 log (or jurisdiction equivalent) recording a workplace injury or illness.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`osha_{token_hex(8)}`) |
| `case_number` | string | Yes | No | OSHA case number |
| `employee_name` | string | Yes | No | Name of the affected employee |
| `date_of_injury` | date | Yes | Sort | Date of injury or illness |
| `classification` | string | Yes | Filter | Injury/illness classification |
| `injury_type` | string | No | No | Type of injury or illness |
| `days_away_from_work` | integer | No | No | Days away from work |
| `days_of_restricted_work` | integer | No | No | Days of restricted work activity |
| `year` | integer | Yes | Filter | Calendar year for the entry |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

---

### EnvironmentalProgram

> An environmental compliance program tracked by the company.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`env_{token_hex(8)}`) |
| `program_type` | string | Yes | Filter | Type of environmental program |
| `title` | string | Yes | No | Program title |
| `status` | string | Yes | Filter | Program status |
| `last_reviewed` | date | No | No | Date of last review |
| `next_review_due` | date | No | Filter | Date of next required review |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |

---

### Relationships

```
(Company)-[:HAS_DOCUMENT]->(Document)
(Document)-[:IS_TYPE]->(DocumentType)
(Document)-[:SATISFIES]->(ComplianceProgram)  // matched by search_terms
(Document)-[:FOR_PROJECT]->(Project)

(Company)-[:HAS_OSHA_LOG]->(OshaLogEntry)
(OshaLogEntry)-[:CLASSIFIED_AS]->(IncidentClassification)
(OshaLogEntry)-[:ORIGINATED_FROM]->(Incident)

(Company)-[:HAS_ENV_PROGRAM]->(EnvironmentalProgram)
(EnvironmentalProgram)-[:APPLIES_TO_PROJECT]->(Project)
(EnvironmentalProgram)-[:GOVERNED_BY]->(Regulation)
```

---

## Domain 8: Daily Operations

### DailyLog

> A daily construction report documenting work performed, conditions, deliveries, and delays for a single day on a project.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`dlog_{token_hex(8)}`) |
| `log_date` | date | Yes | Unique (per project) | Calendar date of the log |
| `status` | string | Yes | Filter | Log lifecycle status |
| `weather` | JSON | No | No | Weather conditions (temp, conditions, wind, precipitation) |
| `crew_count_own` | integer | No | No | Own crew headcount |
| `crew_count_sub` | JSON | No | No | Sub crew counts by company |
| `equipment_on_site` | string[] | No | No | Equipment IDs present on site |
| `work_performed` | string | No | No | Description of work performed |
| `notes` | string | No | No | Additional notes |
| `submitted_at` | datetime | No | No | When the log was submitted |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: draft | submitted | approved

---

### MaterialDelivery

> A record of materials delivered to site, linked to a daily log.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `material` | string | Yes | No | Material description |
| `supplier` | string | No | No | Supplier name |
| `quantity` | string | No | No | Quantity delivered |
| `notes` | string | No | No | Delivery notes |

---

### DelayRecord

> A record of a delay event, linked to a daily log. Supports claims documentation.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `delay_type` | string | Yes | Filter | Category of delay |
| `hours_lost` | float | Yes | No | Hours of delay |
| `description` | string | Yes | No | Description of the delay event |
| `responsible_party` | string | No | No | Party responsible for the delay |

---

### VisitorRecord

> A record of a visitor to the project site, linked to a daily log.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier |
| `name` | string | Yes | No | Visitor name |
| `company` | string | No | No | Visitor company |
| `time_in` | datetime | Yes | No | Check-in time |
| `time_out` | datetime | No | No | Check-out time |
| `purpose` | string | No | No | Purpose of visit |

---

### VoiceSession

> An AI voice interaction session where a user dictates safety records hands-free.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`voice_{token_hex(8)}`) |
| `language` | string | No | No | Language code used in the session |
| `status` | string | Yes | Filter | Session lifecycle status |
| `started_at` | datetime | Yes | Sort | When the session started |
| `ended_at` | datetime | No | No | When the session ended |
| `turn_count` | integer | No | No | Number of conversational turns |
| `records_created` | string[] | No | No | IDs of records created during the session |

**Enums:**
- `status`: active | completed

---

### Relationships

```
(Project)-[:HAS_DAILY_LOG]->(DailyLog)
(DailyLog)-[:AUTHORED_BY]->(Worker)
(DailyLog)-[:INCLUDES_INSPECTION]->(Inspection)      // auto-populated
(DailyLog)-[:INCLUDES_TALK]->(ToolboxTalk)            // auto-populated
(DailyLog)-[:INCLUDES_INCIDENT]->(Incident)           // auto-populated
(DailyLog)-[:INCLUDES_HAZARD_REPORT]->(HazardReport)  // auto-populated
(DailyLog)-[:RECEIVED_MATERIAL]->(MaterialDelivery)
(DailyLog)-[:HAD_DELAY]->(DelayRecord)
(DailyLog)-[:HAD_VISITOR]->(VisitorRecord)

(VoiceSession)-[:FOR_PROJECT]->(Project)
(VoiceSession)-[:BY_USER]->(Member)
(VoiceSession)-[:CREATED_RECORD]->(Inspection)
(VoiceSession)-[:CREATED_RECORD]->(DailyLog)
(VoiceSession)-[:CREATED_RECORD]->(Incident)
```

---

## Domain 9: Sub Management

### GcRelationship

> A contractual relationship between a General Contractor and a Subcontractor, controlling data visibility permissions across the platform.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`gcrel_{token_hex(8)}`) |
| `gc_company_name` | string | No | No | Denormalized GC company display name |
| `sub_company_name` | string | No | No | Denormalized sub company display name |
| `project_name` | string | No | No | Denormalized project display name |
| `status` | string | Yes | Filter | Relationship lifecycle status |
| `can_view_documents` | boolean | Yes | No | GC permission to view sub's safety documents |
| `can_view_inspections` | boolean | Yes | No | GC permission to view sub's inspection records |
| `can_view_training` | boolean | Yes | No | GC permission to view sub's certification/training records |
| `can_view_incidents` | boolean | Yes | No | GC permission to view sub's incident reports |
| `can_view_osha_log` | boolean | Yes | No | GC permission to view sub's OSHA 300 log |
| `can_view_time` | boolean | Yes | No | GC permission to view sub's time entry data |
| `can_view_financials` | boolean | Yes | No | GC permission to view sub's pay apps and lien waivers |
| `invited_by` | string | No | No | Member ID who initiated the relationship |
| `accepted_by` | string | No | No | Member ID who accepted the invitation |
| `accepted_at` | datetime | No | No | Timestamp when the sub accepted the relationship |
| `created_at` | datetime | Yes | Sort | Timestamp of relationship creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: pending | active | inactive | terminated

---

### GcInvitation

> A pending invitation from a GC to a sub-contractor who may not yet have a Kerf account. Converts to a GcRelationship upon acceptance.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`gcinv_{token_hex(8)}`) |
| `gc_company_name` | string | No | No | Denormalized GC company display name |
| `sub_email` | string | Yes | Lookup | Email address the invitation was sent to |
| `project_name` | string | No | No | Project context for the invitation |
| `status` | string | Yes | Filter | Invitation lifecycle status |
| `token` | string | Yes | Unique | Secure token for the acceptance link |
| `expires_at` | datetime | Yes | No | Invitation expiry timestamp (default: 30 days from creation) |
| `accepted_at` | datetime | No | No | Timestamp of acceptance |
| `created_at` | datetime | Yes | Sort | Timestamp of invitation creation |

**Enums:**
- `status`: pending | accepted | declined | expired | revoked

---

### InsuranceCertificate

> An ACORD 25-format Certificate of Insurance (COI) documenting a subcontractor's insurance coverage. Fields align with standard ACORD 25 form sections.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`coi_{token_hex(8)}`) |
| `certificate_number` | string | No | No | ACORD certificate number |
| `certificate_date` | date | Yes | No | Date the certificate was issued |
| `producer_name` | string | No | No | Insurance broker/agent name (ACORD: PRODUCER) |
| `producer_contact` | string | No | No | Broker contact person |
| `producer_phone` | string | No | No | Broker phone number |
| `producer_email` | string | No | No | Broker email address |
| `insured_name` | string | Yes | No | Legal name of the insured party (ACORD: INSURED) |
| `insured_address` | string | No | No | Address of the insured party |
| `policy_type` | string | Yes | Filter | Type of coverage |
| `carrier_name` | string | Yes | No | Insurance carrier / underwriter name (ACORD: INSURER) |
| `carrier_naic` | string | No | No | NAIC number of the insurance carrier |
| `carrier_am_best_rating` | string | No | No | A.M. Best financial strength rating (e.g. A-VIII) |
| `policy_number` | string | Yes | No | Policy number |
| `effective_date` | date | Yes | Sort | Policy effective date |
| `expiration_date` | date | Yes | Filter | Policy expiration date |
| `each_occurrence_limit` | integer | No | No | Per-occurrence limit in cents |
| `general_aggregate_limit` | integer | No | No | General aggregate limit in cents |
| `products_comp_ops_limit` | integer | No | No | Products/completed operations aggregate limit in cents |
| `personal_adv_injury_limit` | integer | No | No | Personal and advertising injury limit in cents |
| `damage_rented_premises_limit` | integer | No | No | Damage to rented premises limit in cents |
| `medical_expense_limit` | integer | No | No | Medical expense (any one person) limit in cents |
| `auto_combined_single_limit` | integer | No | No | Combined single limit (auto policy) in cents |
| `auto_bodily_injury_per_person` | integer | No | No | Bodily injury per person (auto) in cents |
| `auto_bodily_injury_per_accident` | integer | No | No | Bodily injury per accident (auto) in cents |
| `auto_property_damage` | integer | No | No | Property damage per accident (auto) in cents |
| `umbrella_each_occurrence` | integer | No | No | Umbrella/excess each occurrence limit in cents |
| `umbrella_aggregate` | integer | No | No | Umbrella/excess aggregate limit in cents |
| `wc_statutory_limits` | boolean | No | No | Workers comp: statutory limits apply (Y/N) |
| `wc_el_each_accident` | integer | No | No | WC employer's liability each accident in cents |
| `wc_el_disease_each_employee` | integer | No | No | WC employer's liability disease per employee in cents |
| `wc_el_disease_policy_limit` | integer | No | No | WC employer's liability disease policy limit in cents |
| `additional_insured` | boolean | Yes | Filter | Whether the certificate holder is named as additional insured |
| `additional_insured_endorsement` | string | No | No | Endorsement number for additional insured coverage |
| `waiver_of_subrogation` | boolean | Yes | No | Whether waiver of subrogation is granted |
| `waiver_endorsement` | string | No | No | Endorsement number for waiver of subrogation |
| `per_project_aggregate` | boolean | No | No | Whether the aggregate limit applies per project |
| `certificate_holder_name` | string | Yes | No | Name of certificate holder (typically the GC) |
| `certificate_holder_address` | string | No | No | Address of certificate holder |
| `description_of_operations` | string | No | No | ACORD description of operations/locations/vehicles field |
| `source_document_url` | string | No | No | URL to the uploaded COI PDF/image |
| `parsed_by_ai` | boolean | No | No | Whether fields were extracted via AI/OCR |
| `parsing_confidence` | float | No | No | AI extraction confidence score (0.0-1.0) |
| `gc_min_each_occurrence` | integer | No | No | GC-required minimum per-occurrence limit in cents |
| `gc_min_general_aggregate` | integer | No | No | GC-required minimum aggregate limit in cents |
| `meets_gc_requirements` | boolean | No | Filter | Whether all limits meet or exceed GC minimums |
| `deficiencies` | string[] | No | No | List of specific non-compliance issues |
| `status` | string | Yes | Filter | Certificate lifecycle status |
| `alert_30_day_sent` | boolean | No | No | Whether 30-day expiry alert has been sent |
| `alert_14_day_sent` | boolean | No | No | Whether 14-day expiry alert has been sent |
| `alert_7_day_sent` | boolean | No | No | Whether 7-day expiry alert has been sent |
| `renewal_requested_at` | datetime | No | No | When renewal was requested from the sub |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who uploaded/created the record |

**Enums:**
- `policy_type`: commercial_general_liability | workers_compensation | commercial_auto | umbrella_excess | professional_liability | builders_risk | pollution_liability | inland_marine
- `status`: valid | expiring_soon | expired | non_compliant | pending_review

---

### PrequalPackage

> A prequalification submission package assembled for a specific platform (ISNetworld, Avetta, etc.), aggregating documents and questionnaire answers from across the platform.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`prequal_{token_hex(8)}`) |
| `platform` | string | Yes | Filter | Target prequalification platform |
| `client_name` | string | No | No | The GC or owner requesting prequalification |
| `submission_deadline` | date | No | Sort | Deadline for submission |
| `overall_readiness` | integer | Yes | No | Percentage of required documents ready (0-100) |
| `total_documents` | integer | Yes | No | Total document count in the package |
| `ready_documents` | integer | Yes | No | Documents with READY status |
| `outdated_documents` | integer | Yes | No | Documents with OUTDATED status |
| `missing_documents` | integer | Yes | No | Documents with MISSING status |
| `documents` | JSON | Yes | No | Array of PrequalDocument objects with name, category, status, source |
| `questionnaire` | JSON | No | No | Pre-filled questionnaire answers keyed by question ID |
| `created_at` | datetime | Yes | Sort | Timestamp of package creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Firebase UID of the creator |

**Enums:**
- `platform`: isnetworld | avetta | browz | generic

---

### LienWaiver

> A lien waiver document tracking the conditional/unconditional release of lien rights in exchange for payment. Follows the standard 2x2 matrix: conditional vs unconditional, progress vs final.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`lw_{token_hex(8)}`) |
| `waiver_type` | string | Yes | Filter | Position in the 2x2 lien waiver matrix |
| `claimant_name` | string | Yes | No | Legal name of the claimant |
| `payer_name` | string | No | No | Name of the party making payment (the GC or owner) |
| `project_name` | string | No | No | Denormalized project name for the waiver form |
| `project_address` | string | No | No | Project address as it appears on the waiver |
| `owner_name` | string | No | No | Property owner name |
| `through_date` | date | Yes | Sort | Work period end date covered by this waiver |
| `payment_amount` | integer | Yes | No | Amount in cents for which lien rights are being waived |
| `exceptions` | string | No | No | Exceptions to the waiver (conditional waivers only) |
| `disputed_claims` | string | No | No | Description of any disputed claims |
| `signed_by_name` | string | No | No | Name of the person who signed |
| `signed_by_title` | string | No | No | Title of the signer |
| `signed_date` | date | No | No | Date the waiver was signed |
| `notarized` | boolean | No | No | Whether the waiver was notarized (required in some states) |
| `notary_date` | date | No | No | Date of notarization |
| `payment_received` | boolean | Yes | No | Whether payment has been received (triggers conditional to unconditional conversion) |
| `payment_received_date` | date | No | No | Date payment was received |
| `payment_check_number` | string | No | No | Check/payment reference number |
| `source_document_url` | string | No | No | URL to the uploaded signed waiver PDF |
| `tier` | string | Yes | Filter | Which tier of the payment chain |
| `lower_tier_waivers_complete` | boolean | No | No | Whether all lower-tier waivers have been collected |
| `status` | string | Yes | Filter | Waiver lifecycle status |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the record |

**Enums:**
- `waiver_type`: conditional_progress | unconditional_progress | conditional_final | unconditional_final
- `tier`: prime | first_tier | second_tier | supplier
- `status`: pending | requested | received | approved | rejected | waived

---

### SubComplianceSummary

> A computed aggregate view of a subcontractor's compliance posture as seen by the GC. Not persisted as a node -- materialized at query time from underlying data.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `sub_company_id` | string | Yes | Lookup | The sub-contractor's company ID |
| `sub_company_name` | string | Yes | No | Display name of the sub company |
| `compliance_score` | integer | Yes | No | Weighted composite score (0-100) |
| `emr` | float | No | No | Current Experience Modification Rate |
| `trir` | float | No | No | Current Total Recordable Incident Rate |
| `dart_rate` | float | No | No | Days Away, Restricted, or Transferred rate |
| `active_workers` | integer | Yes | No | Count of workers currently assigned to GC projects |
| `total_certifications` | integer | No | No | Total certification count |
| `expired_certifications` | integer | Yes | No | Count of expired certifications |
| `expiring_certifications` | integer | Yes | No | Count of certifications expiring within 30 days |
| `insurance_status` | string | Yes | No | Aggregate insurance compliance status |
| `insurance_gaps` | string[] | No | No | List of missing or expired policy types |
| `last_inspection_date` | date | No | No | Date of most recent inspection |
| `inspection_pass_rate` | float | No | No | Percentage of inspections with pass status |
| `last_toolbox_talk_date` | date | No | No | Date of most recent toolbox talk |
| `toolbox_talk_frequency` | float | No | No | Average talks per week over rolling 30 days |
| `open_corrective_actions` | integer | No | No | Count of open corrective actions |
| `avg_corrective_action_days` | float | No | No | Average days to close a corrective action |
| `mock_inspection_score` | integer | No | No | Latest mock inspection score |
| `mock_inspection_grade` | string | No | No | Latest mock inspection letter grade |
| `lien_waivers_current` | boolean | No | No | Whether all required lien waivers are on file |
| `overall_status` | string | Yes | No | Compliance status indicator |

**Enums:**
- `insurance_status`: compliant | expiring_soon | non_compliant | missing
- `overall_status`: compliant | at_risk | non_compliant | suspended

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `GC_OVER` | Company | Company | `permissions` (JSON), `status`, `effective_from`, `effective_until` | GC-to-sub relationship with visibility permissions |
| `HAS_INSURANCE` | Company | InsuranceCertificate | | Company holds this insurance certificate |
| `INSURANCE_FOR_PROJECT` | InsuranceCertificate | Project | | Certificate scoped to a specific project |
| `CERTIFICATE_HELD_BY` | InsuranceCertificate | Company | | The certificate holder (GC) named on the COI |
| `SUBMITTED_PREQUAL` | Company | PrequalPackage | | Sub submitted this prequalification package |
| `PREQUAL_FOR_CLIENT` | PrequalPackage | Company | | PrequalPackage targeting this GC/owner |
| `WAIVER_FOR_PROJECT` | LienWaiver | Project | | Lien waiver scoped to this project |
| `WAIVER_SIGNED_BY` | LienWaiver | Company | | Sub/supplier who signed the lien waiver |
| `WAIVER_FOR_COMMITMENT` | LienWaiver | Commitment | | Lien waiver associated with this subcontract/PO |
| `WAIVER_FOR_PAY_APP` | LienWaiver | PaymentApplication | | Lien waiver accompanying this payment application |
| `INVITED_SUB` | GcInvitation | Company | `sub_email` | Invitation linked to the GC company |
| `GC_IS` | GcRelationship | Company | | The GC company |
| `SUB_IS` | GcRelationship | Company | | The sub company |
| `SCOPED_TO_PROJECT` | GcRelationship | Project | | Optional project scope |

---

## Domain 10: Time and Workforce

### TimeEntry

> A single clock-in/clock-out record for a worker on a project, charged to a cost code. Supports individual self-entry, foreman crew entry, and auto-detection from toolbox talk attendance.
>
> **Terminology note:** "Clock in / clock out" is the global standard in construction software. UK sites additionally maintain a **site register** (signing in/out) required under CDM 2015 for emergency evacuation accountability — this is a safety process separate from payroll time tracking.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`time_{token_hex(8)}`) |
| `date` | date | Yes | Filter | Calendar date of the work |
| `clock_in` | datetime | Yes | Sort | Clock-in timestamp |
| `clock_out` | datetime | No | No | Clock-out timestamp (null if still clocked in) |
| `clock_in_latitude` | float | No | No | GPS latitude at clock-in |
| `clock_in_longitude` | float | No | No | GPS longitude at clock-in |
| `clock_in_accuracy` | float | No | No | GPS accuracy in meters at clock-in |
| `clock_out_latitude` | float | No | No | GPS latitude at clock-out |
| `clock_out_longitude` | float | No | No | GPS longitude at clock-out |
| `clock_out_accuracy` | float | No | No | GPS accuracy in meters at clock-out |
| `clock_in_within_geofence` | boolean | No | No | Whether clock-in location was inside the project geofence |
| `clock_out_within_geofence` | boolean | No | No | Whether clock-out location was inside the project geofence |
| `geofence_violation_notes` | string | No | No | Explanation if clock-in/out was outside geofence |
| `hours_total` | float | No | No | Total hours worked (calculated from clock-in/out) |
| `hours_regular` | float | No | No | Regular hours (up to daily/weekly threshold) |
| `hours_overtime` | float | No | No | Overtime hours (beyond threshold) |
| `hours_double_time` | float | No | No | Double-time hours (jurisdiction/union specific) |
| `break_minutes` | integer | No | No | Break time deducted in minutes |
| `break_deducted_auto` | boolean | No | No | Whether break was auto-deducted per company policy |
| `pay_rate` | integer | No | No | Hourly pay rate in cents (for cost calculations, not payroll) |
| `pay_rate_overtime` | float | No | No | Overtime multiplier (e.g. 1.5) |
| `pay_rate_double_time` | float | No | No | Double-time multiplier (e.g. 2.0) |
| `total_cost` | integer | No | No | Calculated labour cost in cents |
| `trade` | string | No | No | Worker's trade for this entry (may differ from default trade) |
| `work_description` | string | No | No | Brief description of work performed |
| `source` | string | Yes | Filter | How this entry was created |
| `entered_by` | string | No | No | Member/worker ID who entered the time (foreman for crew entries) |
| `crew_entry_id` | string | No | Lookup | Groups entries created as part of a single crew time entry |
| `status` | string | Yes | Filter | Approval lifecycle status |
| `approved_by` | string | No | No | Member ID who approved the entry |
| `approved_at` | datetime | No | No | Timestamp of approval |
| `rejected_reason` | string | No | No | Reason for rejection |
| `payroll_exported` | boolean | No | Filter | Whether this entry has been included in a payroll export |
| `payroll_exported_at` | datetime | No | No | Timestamp of payroll export |
| `is_split` | boolean | No | No | Whether this is part of a split entry (worker changed cost codes) |
| `split_group_id` | string | No | Lookup | Groups split entries for the same worker/day |
| `notes` | string | No | No | Additional notes |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `source`: worker_self | foreman_entry | auto_detected | manual_adjustment | imported
- `status`: draft | submitted | approved | rejected | void

---

### CostCode

> A company-defined cost classification code following CSI MasterFormat divisions. Used to allocate labour, material, equipment, and subcontractor costs to specific work categories.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`cc_{token_hex(8)}`) |
| `code` | string | Yes | Unique (per company) | The cost code string (e.g. "03-300", "26-100") |
| `description` | string | Yes | No | Human-readable description (e.g. "Cast-in-Place Concrete") |
| `division` | string | No | Filter | MasterFormat division number (e.g. "03", "26") |
| `division_name` | string | No | No | MasterFormat division name (e.g. "Concrete", "Electrical") |
| `cost_type` | string | Yes | Filter | Type of cost this code tracks |
| `unit_of_measure` | string | No | No | Default unit (e.g. "CY", "SF", "LF", "EA", "HR") |
| `budgeted_unit_rate` | integer | No | No | Budgeted rate per unit in cents |
| `is_billable` | boolean | Yes | No | Whether time charged here is billable to the client |
| `active` | boolean | Yes | Filter | Whether the code is available for new entries |
| `sort_order` | integer | No | No | Display ordering within the cost code list |
| `project_ids` | string[] | No | No | Projects this cost code is assigned to (empty = all projects) |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `cost_type`: labour | material | equipment | subcontractor | other | overhead

---

### ProjectGeofence

> A geographic boundary defined around a project site. Used to validate GPS-based clock-in/out and equipment presence.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`geofence_{token_hex(8)}`) |
| `fence_type` | string | Yes | No | Shape of the geofence boundary |
| `center_latitude` | float | Conditional | No | Center latitude (required for radius type) |
| `center_longitude` | float | Conditional | No | Center longitude (required for radius type) |
| `radius_meters` | float | Conditional | No | Radius in meters (required for radius type) |
| `polygon_coordinates` | JSON | Conditional | No | Array of [lat, lng] pairs defining the polygon boundary (required for polygon type) |
| `buffer_meters` | float | No | No | Grace buffer added to the boundary (default: 50m) |
| `active` | boolean | Yes | No | Whether geofence validation is active |
| `enforce_clock_in` | boolean | Yes | No | Whether to enforce geofence on clock-in |
| `enforce_clock_out` | boolean | Yes | No | Whether to enforce geofence on clock-out |
| `alert_on_violation` | boolean | Yes | No | Whether to alert supervisors on geofence violations |
| `created_at` | datetime | Yes | No | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `fence_type`: radius | polygon

---

### PayrollExport

> A batch export of approved time entries for import into external payroll systems (QuickBooks, ADP, Sage, etc.).

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`payexp_{token_hex(8)}`) |
| `period_start` | date | Yes | Sort | Start of the pay period |
| `period_end` | date | Yes | No | End of the pay period |
| `export_format` | string | Yes | No | Target payroll system format |
| `total_entries` | integer | Yes | No | Count of time entries in this export |
| `total_hours_regular` | float | Yes | No | Sum of regular hours |
| `total_hours_overtime` | float | Yes | No | Sum of overtime hours |
| `total_hours_double_time` | float | No | No | Sum of double-time hours |
| `total_cost` | integer | No | No | Total labour cost in cents |
| `file_url` | string | No | No | URL to the generated export file (CSV) |
| `exported_by` | string | Yes | No | Member ID who generated the export |
| `created_at` | datetime | Yes | Sort | Timestamp of export generation |

**Enums:**
- `export_format`: csv_generic | quickbooks | adp | sage | paychex

---

### OvertimeRule

> Company-level configuration for how overtime is calculated. Supports daily, weekly, and jurisdiction-specific rules.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`otrule_{token_hex(8)}`) |
| `overtime_method` | string | Yes | No | How overtime threshold is determined |
| `daily_threshold_hours` | float | No | No | Hours per day before overtime (e.g. 8.0) |
| `weekly_threshold_hours` | float | No | No | Hours per week before overtime (e.g. 40.0) |
| `double_time_daily_threshold` | float | No | No | Hours per day before double time (e.g. 12.0, California) |
| `seventh_day_overtime` | boolean | No | No | Whether 7th consecutive day triggers overtime (California) |
| `overtime_multiplier` | float | Yes | No | Overtime pay multiplier (typically 1.5) |
| `double_time_multiplier` | float | No | No | Double-time pay multiplier (typically 2.0) |
| `auto_deduct_break` | boolean | Yes | No | Whether to auto-deduct break time |
| `break_deduction_minutes` | integer | No | No | Minutes to auto-deduct per shift |
| `break_threshold_hours` | float | No | No | Shift length in hours before break deduction applies |
| `created_at` | datetime | Yes | No | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `overtime_method`: daily | weekly | daily_and_weekly | california | union_custom

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `LOGGED_TIME` | Worker | TimeEntry | | Worker performed this time entry |
| `TIME_ON_PROJECT` | TimeEntry | Project | | Time was worked on this project |
| `CHARGED_TO` | TimeEntry | CostCode | | Time charged to this cost code |
| `HAS_COST_CODE` | Company | CostCode | | Company defined this cost code |
| `COST_CODE_PARENT` | CostCode | CostCode | | Hierarchical cost code relationship |
| `HAS_GEOFENCE` | Project | ProjectGeofence | | Project has this geofence boundary |
| `HAS_OVERTIME_RULE` | Company | OvertimeRule | | Company uses this overtime calculation rule |
| `INCLUDED_IN_EXPORT` | TimeEntry | PayrollExport | | Time entry was part of this payroll export |
| `ENTERED_BY_FOREMAN` | TimeEntry | Worker | | Foreman who entered this crew time entry |
| `SPLIT_WITH` | TimeEntry | TimeEntry | `split_order` (int) | Links split entries for same worker/day |
| `DETECTED_FROM_ATTENDANCE` | TimeEntry | ToolboxTalk | | Auto-detected time entry from toolbox talk check-in |

---

## Domain 11: Quality

### DeficiencyList

> A collection of deficiency items (US: punch list, UK/AU: snagging list) for a project or specific area, tracking resolution of outstanding work before substantial completion.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`dl_{token_hex(8)}`) |
| `name` | string | Yes | No | Descriptive name (e.g. "Building A - 3rd Floor Finishes") |
| `description` | string | No | No | Additional context about the deficiency list scope |
| `phase` | string | No | Filter | Construction phase (e.g. "rough-in", "finishes", "closeout") |
| `due_date` | date | No | Sort | Target completion date |
| `total_items` | integer | Yes | No | Total count of deficiency items |
| `items_identified` | integer | Yes | No | Items in `identified` status |
| `items_assigned` | integer | Yes | No | Items in `assigned` status |
| `items_corrected` | integer | Yes | No | Items in `corrected` status (awaiting verification) |
| `items_verified` | integer | Yes | No | Items in `verified` status |
| `items_closed` | integer | Yes | No | Items in `closed` status |
| `items_rejected` | integer | Yes | No | Items rejected during verification |
| `percent_complete` | float | Yes | No | Percentage of items closed (0.0-100.0) |
| `status` | string | Yes | Filter | Overall deficiency list lifecycle status |
| `submitted_at` | datetime | No | No | When the deficiency list was issued to the responsible party |
| `completed_at` | datetime | No | No | When all items reached closed status |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the deficiency list |

**Enums:**
- `status`: draft | open | in_progress | pending_verification | complete | closed

Note: Quality inspections reuse the `Inspection` node with `category: "quality"` and quality-specific templates. No separate node needed.

---

### DeficiencyItem

> A single deficiency (US: punch item, UK/AU: snag) within a deficiency list, tracking the full lifecycle from identification through correction, verification, and closure.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`di_{token_hex(8)}`) |
| `item_number` | integer | Yes | No | Sequential number within the deficiency list |
| `description` | string | Yes | No | Description of the deficiency |
| `location_description` | string | No | No | Freeform location text (e.g. "Room 312, east wall") |
| `trade` | string | No | Filter | Trade responsible (e.g. "electrical", "plumbing") |
| `category` | string | No | Filter | Deficiency category |
| `severity` | string | Yes | Filter | Impact severity |
| `responsible_company_name` | string | No | No | Denormalized responsible company name |
| `assigned_to_name` | string | No | No | Denormalized assigned worker name |
| `due_date` | date | No | Sort | Target correction date |
| `status` | string | Yes | Filter | Deficiency lifecycle status |
| `priority` | string | No | Filter | Urgency priority |
| `photo_url` | string | No | No | Photo of the deficiency when identified |
| `photo_urls` | string[] | No | No | Multiple photos documenting the deficiency |
| `markup_url` | string | No | No | Annotated plan/drawing showing the location |
| `correction_photo_url` | string | No | No | Photo after correction (before verification) |
| `correction_notes` | string | No | No | Sub's notes on how the deficiency was corrected |
| `corrected_at` | datetime | No | No | When the sub marked it as corrected |
| `corrected_by` | string | No | No | Worker/member who performed the correction |
| `verification_notes` | string | No | No | Inspector's notes during verification |
| `verified_at` | datetime | No | No | When the item was verified |
| `verified_by` | string | No | No | Member who verified the correction |
| `rejection_reason` | string | No | No | Why verification was rejected |
| `rejection_count` | integer | No | No | Number of times correction was rejected |
| `closed_at` | datetime | No | No | When the item reached closed status |
| `closed_by` | string | No | No | Member who closed the item |
| `cost_to_correct` | integer | No | No | Estimated or actual cost to correct in cents |
| `is_back_charge` | boolean | No | No | Whether the correction cost is a back-charge to the sub |
| `back_charge_amount` | integer | No | No | Back-charge amount in cents |
| `days_open` | integer | No | No | Calculated days since identification |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `status`: identified | assigned | in_progress | corrected | verified | closed | rejected | disputed
- `severity`: critical | major | minor | cosmetic
- `priority`: urgent | high | medium | low
- `category`: structural | mechanical | electrical | plumbing | hvac | fire_protection | finishes | sitework | doors_windows | roofing | waterproofing | insulation | other

---

### NonConformanceReport

> A formal report raised when work deviates from approved designs, specifications, or methodology. More serious than a deficiency — requires root cause analysis, remedy plan, and formal sign-off. Tracks the full NCR lifecycle: identification → investigation → remedy → verification → closure.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`ncr_{token_hex(8)}`) |
| `ncr_number` | integer | Yes | Unique (per project) | Sequential NCR number |
| `title` | string | Yes | No | Brief description of the non-conformance |
| `description` | string | Yes | No | Detailed description of how work deviates from requirements |
| `category` | string | Yes | Filter | Type of non-conformance |
| `severity` | string | Yes | Filter | Impact severity |
| `evidence_photos` | string[] | No | No | URLs to photographic evidence |
| `reference_drawing` | string | No | No | Drawing reference showing the required standard |
| `reference_spec` | string | No | No | Specification section reference |
| `root_cause` | string | No | No | Identified root cause |
| `root_cause_category` | string | No | Filter | Root cause classification |
| `remedy_description` | string | No | No | Approved remedy / corrective action plan |
| `preventive_action` | string | No | No | Actions to prevent recurrence |
| `cost_impact` | integer | No | No | Cost to remediate in cents |
| `schedule_impact_days` | integer | No | No | Schedule delay caused |
| `status` | string | Yes | Filter | NCR lifecycle status |
| `raised_date` | date | Yes | Sort | Date the NCR was raised |
| `closed_date` | date | No | No | Date the NCR was closed |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who raised the NCR |

**Enums:**
- `category`: design_deviation | material_non_conformance | workmanship | methodology | documentation | unapproved_substitution
- `severity`: critical | major | minor
- `root_cause_category`: design_error | material_defect | skill_gap | procedure_not_followed | unclear_specification | environmental | equipment_failure
- `status`: open | investigating | remedy_proposed | remedy_approved | correcting | verification | closed | void

---

### Observation

> A field-noted finding recorded DURING construction (not at closeout). Can be quality, safety, or positive. Proactive quality assurance tool — distinct from deficiency items which are closeout-phase. Observations may escalate to NCRs or corrective actions.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`obs_{token_hex(8)}`) |
| `observation_type` | string | Yes | Filter | Category of observation |
| `title` | string | Yes | No | Brief description |
| `description` | string | Yes | No | Detailed observation notes |
| `severity` | string | No | Filter | Severity (for negative observations) |
| `photo_urls` | string[] | No | No | Photographic evidence |
| `trade` | string | No | Filter | Trade responsible |
| `status` | string | Yes | Filter | Observation lifecycle status |
| `response_required` | boolean | Yes | No | Whether a response/action is required |
| `response_due_date` | date | No | Sort | Due date for response |
| `response_notes` | string | No | No | Response from responsible party |
| `resolved_at` | datetime | No | No | When the observation was resolved |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who recorded the observation |

**Enums:**
- `observation_type`: quality_defect | safety_hazard | positive | environmental | design_concern
- `severity`: critical | major | minor | informational
- `status`: open | response_required | in_progress | resolved | closed | escalated_to_ncr

---

### InspectionTestPlan

> An Inspection and Test Plan (ITP) defining what will be inspected, by whom, when, and against which acceptance criteria. Contains Hold Points (mandatory gates — work CANNOT proceed until released) and Witness Points (notification-based — authority invited but work may proceed). Foundational quality planning document.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`itp_{token_hex(8)}`) |
| `name` | string | Yes | No | ITP name (e.g. "Structural Concrete ITP") |
| `description` | string | No | No | Scope description |
| `revision` | integer | Yes | No | Document revision number |
| `status` | string | Yes | Filter | ITP lifecycle status |
| `approved_by` | string | No | No | Member who approved the ITP |
| `approved_at` | datetime | No | No | Approval timestamp |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the ITP |

**Enums:**
- `status`: draft | submitted | approved | superseded

---

### ITPCheckpoint

> A single inspection or test point within an ITP. Each checkpoint is classified as a Hold Point (H) or Witness Point (W), determining whether work must stop for approval.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`itpc_{token_hex(8)}`) |
| `checkpoint_number` | integer | Yes | No | Sequential number within the ITP |
| `description` | string | Yes | No | What is being inspected/tested |
| `checkpoint_type` | string | Yes | Filter | Hold Point or Witness Point |
| `acceptance_criteria` | string | Yes | No | Pass/fail criteria |
| `test_method` | string | No | No | Testing method or standard reference |
| `responsible_party` | string | No | No | Who performs the inspection/test |
| `authority` | string | No | No | Who releases the hold point or witnesses |
| `status` | string | Yes | Filter | Checkpoint execution status |
| `inspected_at` | datetime | No | No | When the inspection/test was performed |
| `inspected_by` | string | No | No | Member who performed the inspection |
| `released_at` | datetime | No | No | When the hold point was released (H only) |
| `released_by` | string | No | No | Member who released the hold point |
| `result` | string | No | Filter | Inspection/test result |
| `notes` | string | No | No | Inspection notes |
| `evidence_urls` | string[] | No | No | URLs to test reports, photos |

**Enums:**
- `checkpoint_type`: hold_point | witness_point
- `status`: pending | notified | inspected | released | skipped_by_authority
- `result`: pass | fail | conditional_pass

---

### MaterialTestRecord

> A record of a material quality test (concrete break test, soil compaction, asphalt core, structural steel mill cert). Links test results to specifications and acceptance criteria.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`mtr_{token_hex(8)}`) |
| `test_type` | string | Yes | Filter | Type of material test |
| `material_description` | string | Yes | No | Material being tested |
| `sample_id` | string | No | No | Sample identification number |
| `sample_date` | date | Yes | Sort | Date the sample was taken |
| `test_date` | date | No | No | Date the test was performed |
| `lab_name` | string | No | No | Testing laboratory name |
| `lab_report_number` | string | No | No | Lab report reference number |
| `spec_requirement` | string | No | No | Specification requirement (e.g. "4000 PSI @ 28 days") |
| `test_result_value` | float | No | No | Numeric test result |
| `test_result_unit` | string | No | No | Unit of measurement |
| `result` | string | Yes | Filter | Pass/fail determination |
| `result_notes` | string | No | No | Additional notes on the result |
| `report_url` | string | No | No | URL to the lab report document |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `created_by` | string | Yes | No | Member ID who recorded the test |

**Enums:**
- `test_type`: concrete_break | concrete_slump | soil_compaction | soil_moisture | asphalt_core | asphalt_density | steel_tensile | steel_mill_cert | rebar_tension | weld_inspection | aggregate_gradation | moisture_content
- `result`: pass | fail | retest_required | pending

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `HAS_DEFICIENCY_LIST` | Project | DeficiencyList | | Project contains this deficiency list |
| `CONTAINS_ITEM` | DeficiencyList | DeficiencyItem | | Deficiency list contains this deficiency item |
| `ITEM_AT_LOCATION` | DeficiencyItem | Location | | Deficiency is at this location |
| `ITEM_ASSIGNED_TO_COMPANY` | DeficiencyItem | Company | | Responsible sub-contractor |
| `ITEM_ASSIGNED_TO_WORKER` | DeficiencyItem | Worker | | Specific worker assigned to fix |
| `FOUND_IN_INSPECTION` | DeficiencyItem | Inspection | | Quality inspection that identified this item |
| `ITEM_LINKED_RFI` | DeficiencyItem | RFI | | RFI raised to clarify the deficiency |
| `ITEM_BACK_CHARGE` | DeficiencyItem | BudgetLineItem | `amount` (int) | Back-charge applied to budget |
| `VERIFIED_BY_MEMBER` | DeficiencyItem | Member | `verified_at` (datetime) | Member who verified the correction |
| `DEFICIENCY_LIST_FOR_LOCATION` | DeficiencyList | Location | | Deficiency list scoped to this location |
| `CREATED_FROM_INSPECTION` | DeficiencyList | Inspection | | Inspection that generated this deficiency list |
| `DEFAULT_RESPONSIBLE` | DeficiencyList | Company | | Default responsible sub-contractor |
| `FOUND_IN_ITEM` | DeficiencyItem | InspectionItem | | Specific inspection item that found this deficiency |
| `HAS_NCR` | Project | NonConformanceReport | | Project has this NCR |
| `NCR_AT_LOCATION` | NonConformanceReport | Location | | NCR relates to this location |
| `NCR_ASSIGNED_TO_COMPANY` | NonConformanceReport | Company | | Sub responsible for remediation |
| `NCR_REFERENCES_DRAWING` | NonConformanceReport | Drawing | | Drawing showing required standard |
| `NCR_REFERENCES_SPEC` | NonConformanceReport | SpecSection | | Spec section violated |
| `NCR_FROM_INSPECTION` | NonConformanceReport | Inspection | | Inspection that found the issue |
| `NCR_GENERATED_CA` | NonConformanceReport | CorrectiveAction | | Corrective action raised from NCR |
| `HAS_OBSERVATION` | Project | Observation | | Project has this observation |
| `OBSERVATION_AT_LOCATION` | Observation | Location | | Observation at this location |
| `OBSERVATION_ASSIGNED_TO_COMPANY` | Observation | Company | | Company responsible for response |
| `OBSERVATION_FROM_INSPECTION` | Observation | Inspection | | Found during this inspection |
| `OBSERVATION_ESCALATED_TO_NCR` | Observation | NonConformanceReport | | Observation escalated to formal NCR |
| `OBSERVATION_ESCALATED_TO_CA` | Observation | CorrectiveAction | | Observation escalated to corrective action |
| `HAS_ITP` | Project | InspectionTestPlan | | Project has this ITP |
| `ITP_FOR_SPEC` | InspectionTestPlan | SpecSection | | ITP covers this spec section |
| `ITP_FOR_TRADE` | InspectionTestPlan | TradeType | | ITP applies to this trade |
| `CONTAINS_CHECKPOINT` | InspectionTestPlan | ITPCheckpoint | | ITP contains this checkpoint |
| `CHECKPOINT_GATES_TASK` | ITPCheckpoint | ScheduleTask | | Hold point gates this schedule task |
| `HAS_MATERIAL_TEST` | Project | MaterialTestRecord | | Project has this material test |
| `TEST_AT_LOCATION` | MaterialTestRecord | Location | | Test sample taken at this location |
| `TEST_FOR_SPEC` | MaterialTestRecord | SpecSection | | Spec section being tested against |
| `TEST_FOR_CHECKPOINT` | MaterialTestRecord | ITPCheckpoint | | ITP checkpoint requiring this test |

---

## Domain 12: Schedule

### ScheduleTask

> A schedulable unit of work within a project, supporting CPM (Critical Path Method) scheduling with forward/backward pass calculations, float analysis, and dependency chains.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`stask_{token_hex(8)}`) |
| `wbs_code` | string | No | No | Work Breakdown Structure code (e.g. "1.2.3") |
| `name` | string | Yes | No | Task name/description |
| `description` | string | No | No | Detailed task description |
| `activity_type` | string | Yes | Filter | Type of schedule entry |
| `trade` | string | No | Filter | Primary trade for this task |
| `responsible_company_name` | string | No | No | Denormalized responsible company name |
| `location_description` | string | No | No | Freeform location text |
| `duration_planned` | integer | Yes | No | Planned duration in calendar days |
| `duration_remaining` | integer | No | No | Remaining duration in calendar days |
| `start_planned` | date | Yes | Sort | Planned (baseline) start date |
| `finish_planned` | date | Yes | No | Planned (baseline) finish date |
| `start_forecast` | date | No | No | Current forecast start date |
| `finish_forecast` | date | No | No | Current forecast finish date |
| `start_actual` | date | No | No | Actual start date |
| `finish_actual` | date | No | No | Actual finish date |
| `early_start` | date | No | No | CPM forward pass: earliest possible start |
| `early_finish` | date | No | No | CPM forward pass: earliest possible finish |
| `late_start` | date | No | No | CPM backward pass: latest allowable start |
| `late_finish` | date | No | No | CPM backward pass: latest allowable finish |
| `total_float` | integer | No | Filter | Total float in days (late_finish - early_finish) |
| `free_float` | integer | No | No | Free float in days (slack before impacting successor) |
| `is_critical` | boolean | No | Filter | Whether task is on the critical path (total_float <= 0) |
| `percent_complete` | float | No | No | Progress percentage (0.0-100.0) |
| `status` | string | Yes | Filter | Task execution status |
| `constraint_type` | string | No | No | Schedule constraint type |
| `constraint_date` | date | No | No | Date for the constraint |
| `calendar_id` | string | No | No | Work calendar (defines working/non-working days) |
| `crew_size` | integer | No | No | Planned crew size for the task |
| `planned_hours` | float | No | No | Planned total labour hours |
| `actual_hours` | float | No | No | Actual hours worked (from TimeEntry aggregation) |
| `budgeted_cost` | integer | No | No | Budgeted cost in cents |
| `actual_cost` | integer | No | No | Actual cost to date in cents |
| `earned_value` | integer | No | No | Earned value (budgeted_cost * percent_complete) in cents |
| `weather_sensitive` | boolean | No | No | Whether task is weather-dependent |
| `safety_conflicts` | JSON | No | No | Cached safety conflict flags (cert gaps, equipment issues) |
| `notes` | string | No | No | Task notes |
| `color` | string | No | No | Display color for the schedule view |
| `sort_order` | integer | No | No | Display ordering within the schedule |
| `level` | integer | No | No | Nesting level in WBS hierarchy (0 = top level) |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the task |

**Enums:**
- `activity_type`: task | milestone | summary | loa (level of activity) | hammock
- `status`: planned | ready | in_progress | complete | on_hold | blocked | cancelled
- `constraint_type`: as_soon_as_possible | as_late_as_possible | must_start_on | must_finish_on | start_no_earlier_than | start_no_later_than | finish_no_earlier_than | finish_no_later_than

---

### Milestone

> A key date marker in the project schedule representing a significant event, deliverable, or contractual obligation. Zero-duration schedule event.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`ms_{token_hex(8)}`) |
| `name` | string | Yes | No | Milestone name (e.g. "Substantial Completion") |
| `description` | string | No | No | Detailed description of what the milestone represents |
| `type` | string | Yes | Filter | Category of milestone |
| `date_planned` | date | Yes | Sort | Planned/baseline date |
| `date_forecast` | date | No | No | Current forecast date |
| `date_actual` | date | No | No | Actual achievement date |
| `is_contractual` | boolean | Yes | Filter | Whether this is a contractual obligation with penalties |
| `liquidated_damages_per_day` | integer | No | No | LD amount per day of delay in cents (if contractual) |
| `status` | string | Yes | Filter | Milestone status |
| `variance_days` | integer | No | No | Days ahead/behind plan (negative = behind) |
| `notes` | string | No | No | Additional notes |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the milestone |

**Enums:**
- `type`: contract | interim | payment | regulatory | owner | design | procurement | construction | commissioning
- `status`: upcoming | at_risk | achieved | missed | waived

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `HAS_TASK` | Project | ScheduleTask | | Project contains this schedule task |
| `DEPENDS_ON` | ScheduleTask | ScheduleTask | `type` (FS/SS/FF/SF), `lag_days` (int), `is_driving` (bool) | Task dependency with lag |
| `PARENT_TASK` | ScheduleTask | ScheduleTask | | Summary/WBS parent-child hierarchy |
| `TASK_AT_LOCATION` | ScheduleTask | Location | | Task is performed at this location |
| `TASK_ASSIGNED_TO_COMPANY` | ScheduleTask | Company | | Sub responsible for execution |
| `TASK_ASSIGNED_TO_FOREMAN` | ScheduleTask | Worker | | Foreman supervising the task |
| `REQUIRES_CERT` | ScheduleTask | CertificationType | | Workers on this task must hold this certification |
| `REQUIRES_EQUIPMENT` | ScheduleTask | Equipment | | Task requires this equipment |
| `TASK_CHARGED_TO` | ScheduleTask | CostCode | | Cost code for the task's labour and materials |
| `HAS_MILESTONE` | Project | Milestone | | Project has this milestone |
| `MILESTONE_AFTER` | Milestone | ScheduleTask | | Milestone is gated by completion of this task |
| `TASK_BLOCKED_BY_CA` | ScheduleTask | CorrectiveAction | | Open corrective action blocking this task |
| `TASK_DELAYED_BY_RFI` | ScheduleTask | RFI | | Open RFI causing schedule impact |
| `TASK_HAS_TIME` | ScheduleTask | TimeEntry | | Time entry logged against this task |
| `MILESTONE_RESPONSIBLE` | Milestone | Company | | Company responsible for achieving this milestone |

---

## Domain 13: Financial

### Budget

> A project-level financial plan organizing all anticipated costs by cost code. Serves as the baseline for cost tracking, forecasting, and variance analysis.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`budget_{token_hex(8)}`) |
| `name` | string | Yes | No | Budget name (e.g. "Original Contract Budget", "GMP Budget") |
| `description` | string | No | No | Budget description/notes |
| `contract_type` | string | Yes | Filter | Type of contract governing this budget |
| `original_contract_amount` | integer | Yes | No | Original contract value in cents |
| `approved_change_orders` | integer | Yes | No | Sum of approved change order amounts in cents |
| `revised_contract_amount` | integer | Yes | No | Original + approved changes in cents |
| `total_committed` | integer | No | No | Sum of all commitment values in cents |
| `total_actual_cost` | integer | No | No | Sum of all actual costs in cents |
| `total_forecast` | integer | No | No | Forecast total cost at completion in cents |
| `total_variance` | integer | No | No | Budget vs forecast variance in cents |
| `contingency_amount` | integer | No | No | Contingency reserve in cents |
| `contingency_used` | integer | No | No | Contingency consumed to date in cents |
| `status` | string | Yes | Filter | Budget lifecycle status |
| `approved_by` | string | No | No | Member who approved the budget |
| `approved_at` | datetime | No | No | Timestamp of budget approval |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the budget |

**Enums:**
- `contract_type`: lump_sum | gmp | cost_plus | time_and_materials | unit_price
- `status`: draft | active | revised | closed | archived

---

### BudgetLineItem

> A single row in the project budget, tied to a cost code. Tracks the full lifecycle from original budget through approved changes, commitments, actuals, and forecast.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`bli_{token_hex(8)}`) |
| `cost_code` | string | Yes | No | Denormalized cost code string |
| `description` | string | Yes | No | Line item description |
| `cost_type` | string | Yes | Filter | Category of cost |
| `original_budget_amount` | integer | Yes | No | Original budgeted amount in cents |
| `approved_cos` | integer | Yes | No | Sum of approved change orders in cents |
| `revised_budget` | integer | Yes | No | original_budget + approved_cos in cents |
| `pending_cos` | integer | No | No | Sum of pending change orders in cents |
| `projected_budget` | integer | No | No | revised_budget + pending_cos in cents |
| `committed_amount` | integer | No | No | Sum of commitments (subcontracts + POs) in cents |
| `committed_open` | integer | No | No | Committed amount not yet invoiced in cents |
| `actual_cost` | integer | No | No | Actual costs recorded to date in cents |
| `actual_cost_this_period` | integer | No | No | Actual costs in current reporting period in cents |
| `forecast_to_complete` | integer | No | No | Estimated remaining cost in cents |
| `estimated_at_completion` | integer | No | No | actual_cost + forecast_to_complete in cents |
| `variance` | integer | No | No | revised_budget - estimated_at_completion in cents |
| `variance_percent` | float | No | No | Variance as percentage of revised budget |
| `units_budgeted` | float | No | No | Budgeted quantity |
| `units_actual` | float | No | No | Actual quantity to date |
| `unit_of_measure` | string | No | No | Unit for quantity tracking |
| `unit_rate_budgeted` | integer | No | No | Budgeted rate per unit in cents |
| `unit_rate_actual` | integer | No | No | Actual average rate per unit in cents |
| `notes` | string | No | No | Line item notes |
| `sort_order` | integer | No | No | Display ordering |
| `created_at` | datetime | Yes | No | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `cost_type`: labour | material | equipment | subcontractor | other | overhead | fee | contingency

---

### Commitment

> A contractual financial obligation to a vendor/sub -- either a subcontract or a purchase order. Tracks original value through change orders and payment applications.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`commit_{token_hex(8)}`) |
| `commitment_number` | string | Yes | No | Sequential reference number |
| `type` | string | Yes | Filter | Commitment type |
| `title` | string | Yes | No | Contract/PO description |
| `vendor_company_name` | string | No | No | Denormalized vendor name |
| `scope_of_work` | string | No | No | Description of contracted scope |
| `original_value` | integer | Yes | No | Original contract/PO value in cents |
| `approved_cos` | integer | Yes | No | Sum of approved commitment change orders in cents |
| `pending_cos` | integer | No | No | Sum of pending commitment change orders in cents |
| `revised_value` | integer | Yes | No | original_value + approved_cos in cents |
| `invoiced_to_date` | integer | No | No | Total invoiced/applied for to date in cents |
| `paid_to_date` | integer | No | No | Total paid to date in cents |
| `retention_percentage` | float | Yes | No | Retention percentage withheld (e.g. 10.0) |
| `retention_held` | integer | No | No | Total retention held to date in cents |
| `retention_released` | integer | No | No | Retention released to date in cents |
| `balance_to_finish` | integer | No | No | Remaining contract balance in cents |
| `start_date` | date | No | No | Contract start date |
| `end_date` | date | No | No | Contract completion date |
| `insurance_required` | boolean | No | No | Whether COI is required from this vendor |
| `insurance_compliant` | boolean | No | No | Whether vendor's insurance meets requirements |
| `bonding_required` | boolean | No | No | Whether performance/payment bond is required |
| `bonding_amount` | integer | No | No | Bond amount in cents |
| `status` | string | Yes | Filter | Commitment lifecycle status |
| `executed_date` | date | No | No | Date the contract was executed |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the commitment |

**Enums:**
- `type`: subcontract | purchase_order | professional_service | rental_agreement
- `status`: draft | pending_execution | active | complete | closed | terminated | suspended

---

### PaymentApplication

> An AIA G702/G703-format payment application (pay app) submitted by a sub/supplier against a commitment. The G702 is the cover sheet; G703 is the continuation sheet with line-item detail.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`payapp_{token_hex(8)}`) |
| `application_number` | integer | Yes | No | Sequential pay app number for this commitment |
| `period_from` | date | Yes | No | Billing period start date |
| `period_to` | date | Yes | Sort | Billing period end date |
| `application_date` | date | Yes | No | Date the pay app was submitted |
| `g702_project_name` | string | No | No | AIA G702: Project name as shown on application |
| `g702_project_number` | string | No | No | AIA G702: Project number |
| `g702_contract_date` | date | No | No | AIA G702: Date of contract |
| `g702_contractor_name` | string | No | No | AIA G702: Contractor (applicant) name |
| `g702_architect_name` | string | No | No | AIA G702: Architect name |
| `g702_owner_name` | string | No | No | AIA G702: Owner name |
| `original_contract_sum` | integer | Yes | No | AIA G702 Line 1: Original contract sum in cents |
| `net_change_by_cos` | integer | Yes | No | AIA G702 Line 2: Net change by change orders in cents |
| `contract_sum_to_date` | integer | Yes | No | AIA G702 Line 3: Contract sum to date (line 1 + 2) in cents |
| `total_completed_and_stored` | integer | Yes | No | AIA G702 Line 4: Total completed and stored to date in cents |
| `retainage_on_completed` | integer | No | No | AIA G702 Line 5a: Retainage on completed work in cents |
| `retainage_on_stored` | integer | No | No | AIA G702 Line 5b: Retainage on stored materials in cents |
| `total_retainage` | integer | Yes | No | AIA G702 Line 5: Total retainage (5a + 5b) in cents |
| `total_earned_less_retainage` | integer | Yes | No | AIA G702 Line 6: Total less retainage (line 4 - 5) in cents |
| `less_previous_certificates` | integer | Yes | No | AIA G702 Line 7: Less previous certificates for payment in cents |
| `current_payment_due` | integer | Yes | No | AIA G702 Line 8: Current payment due (line 6 - 7) in cents |
| `balance_to_finish` | integer | Yes | No | AIA G702 Line 9: Balance to finish plus retainage in cents |
| `percent_complete` | float | Yes | No | Overall completion percentage (line 4 / line 3) |
| `line_items` | JSON | No | No | AIA G703 continuation sheet: array of line-item details |
| `has_stored_materials` | boolean | No | No | Whether the application includes stored materials not yet installed |
| `stored_materials_amount` | integer | No | No | Value of stored materials in cents |
| `lower_tier_waivers_complete` | boolean | No | No | Whether all required lower-tier lien waivers are on file |
| `compliance_hold` | boolean | No | No | Whether payment is held pending compliance (insurance, safety, etc.) |
| `compliance_hold_reason` | string | No | No | Reason for compliance hold |
| `status` | string | Yes | Filter | Pay app lifecycle status |
| `submitted_at` | datetime | No | No | Timestamp of submission |
| `submitted_by` | string | No | No | Member who submitted |
| `reviewed_at` | datetime | No | No | Timestamp of review |
| `reviewed_by` | string | No | No | Member who reviewed |
| `certified_at` | datetime | No | No | Timestamp of certification (architect/engineer sign-off) |
| `certified_by` | string | No | No | Member who certified |
| `paid_at` | datetime | No | No | Timestamp of payment |
| `paid_amount` | integer | No | No | Actual amount paid in cents (may differ from current_payment_due) |
| `payment_reference` | string | No | No | Check number or EFT reference |
| `notes` | string | No | No | Additional notes |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the record |

**Enums:**
- `status`: draft | submitted | under_review | certified | approved | paid | rejected | void

---

### PaymentApplicationLineItem

> A single row on the AIA G703 continuation sheet, tracking scheduled value, prior work completed, current period work, stored materials, and completion percentage for a specific item of work.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`pali_{token_hex(8)}`) |
| `item_number` | string | Yes | No | G703 item number (matches contract schedule of values) |
| `description` | string | Yes | No | Description of work |
| `scheduled_value` | integer | Yes | No | G703 Col C: Scheduled value in cents |
| `previous_applications` | integer | Yes | No | G703 Col D: Work completed from previous applications in cents |
| `this_period` | integer | Yes | No | G703 Col E: Work completed this period in cents |
| `materials_stored` | integer | No | No | G703 Col F: Materials presently stored in cents |
| `total_completed_and_stored` | integer | Yes | No | G703 Col G: Total completed and stored (D + E + F) in cents |
| `percent_complete` | float | Yes | No | G703 Col H: Percentage (G / C) |
| `balance_to_finish` | integer | Yes | No | G703 Col I: Balance to finish (C - G) in cents |
| `retainage` | integer | No | No | Retainage held on this line item in cents |
| `sort_order` | integer | No | No | Display ordering on the G703 |

---

### EMRRecord

> Experience Modification Rate record for a company, used by insurance carriers to adjust workers' compensation premiums. Based on a 3-year rolling window of loss history.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`emr_{token_hex(8)}`) |
| `year` | integer | Yes | Filter | Policy year the EMR applies to |
| `emr_value` | float | Yes | No | The EMR value (1.0 = industry average; < 1.0 = better; > 1.0 = worse) |
| `experience_period_start` | date | No | No | Start of the 3-year experience period |
| `experience_period_end` | date | No | No | End of the 3-year experience period |
| `prior_year_1_losses` | integer | No | No | Loss amount in year N-1 in cents |
| `prior_year_2_losses` | integer | No | No | Loss amount in year N-2 in cents |
| `prior_year_3_losses` | integer | No | No | Loss amount in year N-3 in cents |
| `prior_year_1_payroll` | integer | No | No | Payroll in year N-1 in cents |
| `prior_year_2_payroll` | integer | No | No | Payroll in year N-2 in cents |
| `prior_year_3_payroll` | integer | No | No | Payroll in year N-3 in cents |
| `expected_losses` | integer | No | No | Expected losses for the experience period in cents |
| `actual_losses` | integer | No | No | Actual incurred losses for the experience period in cents |
| `ncci_class_codes` | string[] | No | No | NCCI class codes used in the calculation |
| `state` | string | No | No | State jurisdiction for the EMR |
| `carrier_name` | string | No | No | Insurance carrier issuing the EMR |
| `effective_date` | date | Yes | Sort | Date the EMR takes effect |
| `expiration_date` | date | No | No | Date the EMR expires |
| `source_document_url` | string | No | No | URL to the uploaded EMR worksheet |
| `verified` | boolean | No | No | Whether the EMR has been verified against carrier records |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | No | No | Member ID who entered the record |

---

### ChangeEvent

> An internal record of a field condition, owner request, or design issue that may result in a cost/schedule change. The first stage in the change order pipeline: ChangeEvent leads to PCO leads to CO.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`ce_{token_hex(8)}`) |
| `event_number` | integer | Yes | No | Sequential number within the project |
| `title` | string | Yes | No | Brief description of the change event |
| `description` | string | No | No | Detailed description of the event and its impact |
| `origin` | string | Yes | Filter | What caused the change |
| `identified_date` | date | Yes | Sort | Date the change event was identified |
| `identified_by` | string | Yes | No | Member who identified the event |
| `estimated_cost_impact` | integer | No | No | Preliminary cost estimate in cents |
| `estimated_schedule_impact_days` | integer | No | No | Preliminary schedule impact in days |
| `status` | string | Yes | Filter | Change event lifecycle status |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `origin`: rfi | field_condition | owner_request | design_change | regulatory | differing_site_condition | value_engineering
- `status`: identified | evaluating | pco_created | void

---

### PotentialChangeOrder

> A Potential Change Order (PCO) -- a priced and scoped change proposal derived from one or more ChangeEvents. Awaiting owner/architect approval before becoming a formal Change Order.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`pco_{token_hex(8)}`) |
| `pco_number` | integer | Yes | No | Sequential PCO number within the project |
| `title` | string | Yes | No | PCO description |
| `description` | string | No | No | Detailed scope of the proposed change |
| `cost_impact` | integer | Yes | No | Proposed cost change in cents (positive = increase) |
| `schedule_impact_days` | integer | No | No | Proposed schedule change in days (positive = extension) |
| `markup_percentage` | float | No | No | Contractor markup/overhead percentage applied |
| `cost_breakdown` | JSON | No | No | Itemized cost breakdown (labour, material, equipment, sub, markup) |
| `submitted_to` | string | No | No | Party the PCO was submitted to (architect, owner) |
| `submitted_date` | date | No | No | Date submitted for review |
| `response_date` | date | No | No | Date response was received |
| `status` | string | Yes | Filter | PCO lifecycle status |
| `approved_amount` | integer | No | No | Amount approved (may differ from requested) in cents |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the PCO |

**Enums:**
- `status`: draft | submitted | under_review | approved | rejected | withdrawn | rolled_into_co

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `HAS_BUDGET` | Project | Budget | | Project has this budget |
| `HAS_LINE_ITEM` | Budget | BudgetLineItem | | Budget contains this line item |
| `LINE_ITEM_CHARGED_TO` | BudgetLineItem | CostCode | | Line item maps to this cost code |
| `HAS_COMMITMENT` | Project | Commitment | | Project has this subcontract/PO |
| `COMMITMENT_WITH_VENDOR` | Commitment | Company | | Vendor/sub for this commitment |
| `COMMITMENT_CHARGED_TO` | Commitment | CostCode | | Primary cost code for the commitment |
| `HAS_PAY_APP` | Commitment | PaymentApplication | | Commitment has this payment application |
| `PAY_APP_LINE_ITEM` | PaymentApplication | PaymentApplicationLineItem | | Pay app contains this G703 line item |
| `PAY_APP_LIEN_WAIVER` | PaymentApplication | LienWaiver | `waiver_type` (conditional/unconditional) | Lien waiver accompanying this pay app |
| `HAS_EMR` | Company | EMRRecord | | Company has this EMR record |
| `EMR_DERIVED_FROM` | EMRRecord | OshaLogEntry | | OSHA log entries that feed the EMR calculation |
| `EMR_AFFECTS_INSURANCE` | EMRRecord | InsuranceCertificate | | EMR impacts this WC insurance premium |
| `HAS_CHANGE_EVENT` | Project | ChangeEvent | | Project has this change event |
| `EVENT_BECAME_PCO` | ChangeEvent | PotentialChangeOrder | | Change event was priced as this PCO |
| `PCO_BECAME_CO` | PotentialChangeOrder | ChangeOrder | | PCO was approved and became this change order |
| `CO_ADJUSTS_BUDGET` | ChangeOrder | BudgetLineItem | `amount` (int) | Change order adjusts this budget line |
| `CO_MODIFIES_COMMITMENT` | ChangeOrder | Commitment | `amount` (int) | Change order modifies this commitment value |
| `PAY_APP_FOR_PROJECT` | PaymentApplication | Project | | Project this pay app is for |
| `LINE_ITEM_CHARGED_TO` | PaymentApplicationLineItem | CostCode | | Cost code for this line item |
| `LINE_ITEM_FROM_CO` | PaymentApplicationLineItem | ChangeOrder | | Change order that added this line item |
| `ORIGINATED_FROM_INSPECTION` | ChangeEvent | Inspection | | Inspection that found the condition |
| `HAS_PCO` | Project | PotentialChangeOrder | | Project has this potential change order |

---

## Domain 14: Project Coordination

### RFI

> A Request for Information following AIA G716 format. Formal documented question from the contractor to the architect/engineer/owner seeking clarification on contract documents. Tracks the full lifecycle with ball-in-court accountability and response threading.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`rfi_{token_hex(8)}`) |
| `rfi_number` | integer | Yes | Unique (per project) | Sequential RFI number |
| `subject` | string | Yes | No | Brief subject line |
| `question` | string | Yes | No | Full text of the question/request |
| `suggestion` | string | No | No | Contractor's suggested resolution |
| `response` | string | No | No | Official response from the respondent |
| `attachments` | JSON | No | No | Array of {filename, url, size_bytes} objects |
| `response_attachments` | JSON | No | No | Attachments included with the response |
| `status` | string | Yes | Filter | RFI lifecycle status |
| `priority` | string | Yes | Filter | Urgency level |
| `ball_in_court_name` | string | No | No | Denormalized name for display |
| `drawing_reference` | string | No | No | Reference to drawing number(s) |
| `spec_section_reference` | string | No | No | Reference to specification section(s) |
| `location_description` | string | No | No | Freeform location text |
| `cost_impact` | string | No | No | Cost impact assessment |
| `cost_impact_amount` | integer | No | No | Estimated cost impact in cents |
| `schedule_impact` | string | No | No | Schedule impact assessment |
| `schedule_impact_days` | integer | No | No | Estimated schedule impact in days |
| `issue_date` | date | Yes | Sort | Date the RFI was issued |
| `due_date` | date | No | Filter | Response due date |
| `date_required_on_site` | date | No | No | Date the information is needed on site |
| `response_date` | date | No | No | Date the response was received |
| `closed_date` | date | No | No | Date the RFI was officially closed |
| `days_open` | integer | No | No | Calculated days from issue to response/current |
| `is_overdue` | boolean | No | Filter | Whether the RFI is past its due date |
| `distribution_list` | string[] | No | No | Member IDs on the distribution list |
| `response_history` | JSON | No | No | Array of {responder, date, text, attachments} for multi-round Q&A |
| `linked_rfi_ids` | string[] | No | No | Related RFI IDs |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the RFI |

**Enums:**
- `status`: draft | open | pending_response | responded | closed | void
- `priority`: critical | urgent | high | medium | low | for_record

---

### Submittal

> A product data submission, shop drawing, sample, or other document submitted by a sub/supplier for review and approval by the architect/engineer. Tracks multi-step review workflows with revision history.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`sub_{token_hex(8)}`) |
| `submittal_number` | integer | Yes | Unique (per project) | Sequential submittal number |
| `revision` | integer | Yes | No | Revision number (starts at 0, increments on resubmission) |
| `title` | string | Yes | No | Submittal title/description |
| `type` | string | Yes | Filter | Type of submittal |
| `spec_section_number` | string | No | No | Denormalized spec section number (e.g. "09 2116") |
| `spec_section_title` | string | No | No | Denormalized spec section title |
| `drawing_ids` | string[] | No | No | Related drawing IDs |
| `drawing_references` | string | No | No | Freeform drawing reference text |
| `submitted_by_company_name` | string | No | No | Denormalized submitter company name |
| `submitted_by_id` | string | No | No | Member who submitted |
| `ball_in_court_name` | string | No | No | Denormalized name for display |
| `status` | string | Yes | Filter | Submittal review status |
| `date_submitted` | date | No | Sort | Date submitted for review |
| `date_required` | date | No | Filter | Date the approved submittal is needed |
| `date_required_on_site` | date | No | No | Date the material/product is needed on site |
| `lead_time_days` | integer | No | No | Manufacturing/delivery lead time after approval |
| `date_returned` | date | No | No | Date the review response was returned |
| `date_approved` | date | No | No | Date final approval was granted |
| `review_notes` | string | No | No | Reviewer's notes/comments |
| `review_stamps` | JSON | No | No | Array of review stamps with {reviewer, date, action, notes} |
| `attachments` | JSON | No | No | Array of {filename, url, size_bytes, pages} objects |
| `revision_history` | JSON | No | No | Array of {revision, date, status, notes} for each revision |
| `is_overdue` | boolean | No | Filter | Whether the submittal is past its due date |
| `distribution_list` | string[] | No | No | Member IDs on the distribution list |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the record |

**Enums:**
- `type`: product_data | shop_drawing | sample | mock_up | certification | test_report | design_mix | warranty | operation_manual | attic_stock | closeout
- `status`: pending_submission | submitted | under_review | approved | approved_as_noted | revise_and_resubmit | rejected | closed | void

---

### ChangeOrder

> A formal, approved change to the contract scope, cost, or schedule. The final stage of the change pipeline (ChangeEvent leads to PCO leads to ChangeOrder). May originate from RFIs, field conditions, owner requests, or design changes.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`co_{token_hex(8)}`) |
| `co_number` | integer | Yes | Unique (per project) | Sequential change order number |
| `title` | string | Yes | No | Change order title |
| `description` | string | No | No | Detailed scope description |
| `origin` | string | Yes | Filter | What initiated the change |
| `source_change_event_ids` | string[] | No | No | ChangeEvent(s) that originated this CO |
| `amount` | integer | Yes | No | Net cost change in cents (positive = increase, negative = decrease) |
| `cost_breakdown` | JSON | No | No | Itemized breakdown: {labour, material, equipment, sub, markup, total} |
| `markup_percentage` | float | No | No | Applied markup/overhead percentage |
| `schedule_impact_days` | integer | No | No | Net schedule impact in days (positive = extension) |
| `new_contract_sum` | integer | No | No | Revised contract sum after this CO in cents |
| `new_completion_date` | date | No | No | Revised substantial completion date |
| `status` | string | Yes | Filter | Change order lifecycle status |
| `submitted_date` | date | No | No | Date submitted for approval |
| `approved_date` | date | No | No | Date approved |
| `approved_by` | string | No | No | Person/entity who approved |
| `executed_date` | date | No | No | Date the change order was fully executed |
| `rejected_date` | date | No | No | Date rejected (if rejected) |
| `rejected_reason` | string | No | No | Reason for rejection |
| `affected_cost_code_ids` | string[] | No | No | Cost codes affected by this change |
| `affected_commitment_ids` | string[] | No | No | Commitments modified by this change |
| `affected_schedule_task_ids` | string[] | No | No | Schedule tasks impacted |
| `attachments` | JSON | No | No | Array of {filename, url, size_bytes} objects |
| `notes` | string | No | No | Additional notes |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the change order |

**Enums:**
- `origin`: rfi | field_condition | owner_request | design_change | regulatory | differing_site_condition | value_engineering | allowance_adjustment
- `status`: draft | pending_approval | approved | rejected | executed | void

---

### Drawing

> A construction drawing/plan sheet within the project document set. Tracks revisions and links to spec sections, RFIs, and submittals for full document traceability.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`dwg_{token_hex(8)}`) |
| `sheet_number` | string | Yes | Unique (per project) | Drawing sheet number (e.g. "A-201", "S-101", "M-401") |
| `discipline` | string | Yes | Filter | Design discipline |
| `title` | string | Yes | No | Drawing title |
| `description` | string | No | No | Additional description |
| `revision` | string | Yes | No | Current revision number/letter (e.g. "3", "C") |
| `revision_date` | date | Yes | Sort | Date of the current revision |
| `revision_description` | string | No | No | Description of changes in the current revision |
| `revision_history` | JSON | No | No | Array of {revision, date, description, issued_by} |
| `status` | string | Yes | Filter | Drawing status |
| `set_type` | string | No | No | Drawing set classification |
| `scale` | string | No | No | Drawing scale (e.g. "1/4\" = 1'-0\"") |
| `paper_size` | string | No | No | Paper size (e.g. "30x42", "24x36", "ARCH D") |
| `designed_by` | string | No | No | Designer name/initials |
| `drawn_by` | string | No | No | Drafter name/initials |
| `checked_by` | string | No | No | Checker name/initials |
| `file_url` | string | No | No | URL to the drawing file (PDF) |
| `thumbnail_url` | string | No | No | URL to a thumbnail preview |
| `location_ids` | string[] | No | No | Location nodes depicted on this drawing |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

**Enums:**
- `discipline`: architectural | structural | mechanical | electrical | plumbing | fire_protection | civil | landscape | interior | specialty
- `status`: for_construction | preliminary | issued_for_review | approved | as_built | superseded | void
- `set_type`: construction_documents | bid_set | permit_set | record_set | addendum

---

### SpecSection

> A specification section from the project manual, organized by CSI MasterFormat division. Links submittals and RFIs to the contract requirements they address.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`spec_{token_hex(8)}`) |
| `division` | string | Yes | Filter | MasterFormat division number (e.g. "03", "09") |
| `division_name` | string | No | No | MasterFormat division name (e.g. "Concrete", "Finishes") |
| `section_number` | string | Yes | Unique (per project) | Full section number (e.g. "03 3000", "09 2116") |
| `section_title` | string | Yes | No | Section title (e.g. "Cast-in-Place Concrete", "Gypsum Board Assemblies") |
| `description` | string | No | No | Brief scope description |
| `submittals_required` | string[] | No | No | Types of submittals required by this section |
| `total_submittals` | integer | No | No | Count of submittals linked to this section |
| `approved_submittals` | integer | No | No | Count of approved submittals |
| `applicable_drawings` | string[] | No | No | Drawing sheet numbers referenced by this section |
| `file_url` | string | No | No | URL to the specification document |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `HAS_RFI` | Project | RFI | | Project contains this RFI |
| `RFI_INITIATED_BY` | RFI | Company | | Company that initiated the RFI |
| `RFI_ASSIGNED_TO` | RFI | Company | | Company assigned to respond |
| `RFI_BALL_IN_COURT` | RFI | Member | | Member who currently needs to act |
| `RFI_REFERENCES_DRAWING` | RFI | Drawing | | Drawing referenced by the RFI |
| `RFI_REFERENCES_SPEC` | RFI | SpecSection | | Spec section referenced by the RFI |
| `RFI_AT_LOCATION` | RFI | Location | | Location relevant to the RFI |
| `RFI_TRIGGERS_CHANGE` | RFI | ChangeEvent | | RFI resulted in a change event |
| `RFI_IMPACTS_TASK` | RFI | ScheduleTask | | RFI affects this schedule task |
| `RFI_DOCUMENTED_IN_LOG` | RFI | DailyLog | | RFI delay documented in daily log |
| `HAS_SUBMITTAL` | Project | Submittal | | Project contains this submittal |
| `SUBMITTAL_SATISFIES_SPEC` | Submittal | SpecSection | | Submittal satisfies this spec requirement |
| `SUBMITTAL_REFERENCES_DRAWING` | Submittal | Drawing | | Submittal references this drawing |
| `SUBMITTAL_GATES_TASK` | Submittal | ScheduleTask | | Submittal approval gates this schedule task |
| `SUBMITTAL_BY_COMPANY` | Submittal | Company | | Sub/supplier that submitted |
| `SUBMITTAL_REVIEWED_BY` | Submittal | Member | `action`, `date`, `notes` | Review action by this member |
| `HAS_CHANGE_ORDER` | Project | ChangeOrder | | Project has this change order |
| `CO_FROM_RFI` | ChangeOrder | RFI | | Change order originated from this RFI |
| `CO_FROM_PCO` | ChangeOrder | PotentialChangeOrder | | Change order approved from this PCO |
| `CO_ADJUSTS_BUDGET` | ChangeOrder | BudgetLineItem | `amount` (int) | Change order adjusts this budget line |
| `CO_IMPACTS_TASK` | ChangeOrder | ScheduleTask | `days` (int) | Change order impacts schedule |
| `CO_MODIFIES_COMMITMENT` | ChangeOrder | Commitment | `amount` (int) | Change order modifies commitment value |
| `HAS_DRAWING` | Project | Drawing | | Project contains this drawing |
| `DRAWING_ISSUED_BY` | Drawing | Company | | Design firm that issued the drawing |
| `DRAWING_REFERENCES_SPEC` | Drawing | SpecSection | | Drawing implements this spec section |
| `DRAWING_AT_LOCATION` | Drawing | Location | | Drawing depicts this location |
| `HAS_SPEC` | Project | SpecSection | | Project has this spec section |
| `SPEC_RESPONSIBLE_COMPANY` | SpecSection | Company | | Sub responsible for this section |
| `SPEC_CHARGED_TO` | SpecSection | CostCode | | Cost code for this spec section |
| `RFI_INITIATED_BY_MEMBER` | RFI | Member | | Member who initiated the RFI |
| `RFI_ASSIGNED_TO_MEMBER` | RFI | Member | | Member assigned to respond |
| `RFI_BALL_IN_COURT_COMPANY` | RFI | Company | | Company who currently needs to act |
| `SUBMITTED_BY_MEMBER` | Submittal | Member | | Member who submitted |
| `REVIEWED_BY_COMPANY` | Submittal | Company | | Company currently reviewing |
| `SUBMITTAL_BALL_IN_COURT` | Submittal | Member | | Member who currently needs to act |
| `SUBMITTAL_CHARGED_TO` | Submittal | CostCode | | Associated cost code |

---

## Domain 15: Procurement

### PurchaseOrder

> A purchase order for materials, equipment rental, or supplies. Distinct from Commitment (which covers subcontracts and professional services). POs track the procurement lifecycle from requisition through delivery and invoicing.

| Property | Type | Required | Indexed | Description |
|---|---|---|---|---|
| `id` | string | Yes | Unique | Internal identifier (`po_{token_hex(8)}`) |
| `po_number` | string | Yes | Unique (per project) | Sequential PO number |
| `title` | string | Yes | No | PO description |
| `vendor_name` | string | Yes | No | Vendor/supplier name |
| `material_description` | string | No | No | Detailed material/product description |
| `quantity` | float | No | No | Quantity ordered |
| `unit_of_measure` | string | No | No | Unit (e.g. "CY", "EA", "TON", "LF") |
| `unit_price` | integer | No | No | Price per unit in cents |
| `total_amount` | integer | Yes | No | Total PO value in cents |
| `tax_amount` | integer | No | No | Tax amount in cents |
| `shipping_amount` | integer | No | No | Shipping/freight in cents |
| `delivery_date_required` | date | No | Sort | Required delivery date |
| `delivery_date_actual` | date | No | No | Actual delivery date |
| `delivery_location_description` | string | No | No | Delivery location text |
| `status` | string | Yes | Filter | PO lifecycle status |
| `approved_by` | string | No | No | Member who approved the PO |
| `approved_at` | datetime | No | No | Approval timestamp |
| `notes` | string | No | No | Additional notes |
| `created_at` | datetime | Yes | Sort | Timestamp of record creation |
| `updated_at` | datetime | Yes | No | Timestamp of last update |
| `created_by` | string | Yes | No | Member ID who created the PO |

**Enums:**
- `status`: draft | pending_approval | approved | ordered | partially_received | received | invoiced | closed | cancelled

---

### Relationships

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| `HAS_PO` | Project | PurchaseOrder | | Project has this purchase order |
| `PO_FOR_VENDOR` | PurchaseOrder | Company | | Vendor/supplier for this PO |
| `PO_CHARGED_TO` | PurchaseOrder | CostCode | | Cost code for this PO |
| `PO_FULFILLS_BUDGET` | PurchaseOrder | BudgetLineItem | | Budget line this PO charges against |
| `PO_FROM_SUBMITTAL` | PurchaseOrder | Submittal | | Submittal approval that enabled this PO |
| `PO_DELIVERED_TO` | PurchaseOrder | Location | | Delivery location |
| `PO_RECEIVED_IN_LOG` | PurchaseOrder | MaterialDelivery | | Daily log delivery record for this PO |
| `PO_GATES_TASK` | PurchaseOrder | ScheduleTask | | Schedule task waiting for this delivery |

---

## Cross-Domain Edge Catalogue

These are the edges that connect domains and enable multi-hop agent reasoning. Each one is annotated with the question it answers.

### Regulatory <> HR
```
# "Does this worker have the certs this regulation requires?"
(Regulation)-[:REQUIRES_CERTIFICATION]->(CertificationType)<-[:OF_TYPE]-(Certification)<-[:HOLDS_CERT]-(Worker)

# "What certs does this role require?"
(Worker)-[:HAS_ROLE]->(Role)-[:REQUIRES_CERT]->(CertificationType)
```

### HR <> Schedule
```
# "Can this worker do this task?"
(Worker)-[:HOLDS_CERT]->(Certification)-[:OF_TYPE]->(CertificationType)<-[:REQUIRES_CERT]-(ScheduleTask)

# "Are there enough certified workers for Friday's task?"
(ScheduleTask)-[:REQUIRES_CERT]->(CertificationType)<-[:OF_TYPE]-(Certification {status:'valid'})<-[:HOLDS_CERT]-(Worker)-[:ASSIGNED_TO {status:'active'}]->(Project)
```

### Equipment <> Schedule
```
# "Is this equipment available and inspected for the task?"
(ScheduleTask)-[:REQUIRES_EQUIPMENT]->(Equipment)-[:DEPLOYED_TO]->(Project)
(Equipment)-[:HAS_INSPECTION_LOG]->(EquipmentInspectionLog {overall_status, inspection_date})
```

### Safety <> Schedule
```
# "Does this area have open safety issues blocking work?"
(CorrectiveAction {status:'open'})-[:AT_LOCATION]->(Location)<-[:AT_LOCATION]-(ScheduleTask)

# "High incident area — elevated risk for the task"
(Incident)-[:AT_LOCATION]->(Location)<-[:AT_LOCATION]-(ScheduleTask)
```

### Safety <> Financial
```
# "How does safety performance affect insurance cost?"
(Incident)-[:ORIGINATED_FROM]->(:OshaLogEntry)-[:DERIVED_FROM]->(:EMRRecord)-[:AFFECTS]->(:InsuranceCertificate)

# "What is the financial impact of this incident?"
(Incident)-[:CLASSIFIED_AS]->(IncidentClassification {recordable: true})
  // feeds EMR calculation over 3-year window
```

### Daily Log <> Schedule <> RFI <> Change Order (claims chain)
```
# "What daily logs support this delay claim?"
(DailyLog)-[:HAD_DELAY]->(DelayRecord)-[:IMPACTS_TASK]->(ScheduleTask)
(DelayRecord)-[:CAUSED_BY_RFI]->(RFI)-[:TRIGGERS_CHANGE]->(ChangeOrder)

# Traversable in BOTH directions for forensic analysis
```

### Sub <> Safety <> Financial
```
# "What is this sub's risk profile?"
(Company)-[:GC_OVER]->(SubCompany)
(SubCompany)-[:EMPLOYS]->(Worker)-[:ASSIGNED_TO]->(Project)
(Project)-[:HAS_INSPECTION]->(Inspection {overall_status})
(Project)-[:HAS_INCIDENT]->(Incident {severity})
(SubCompany)-[:HAS_INSURANCE]->(InsuranceCertificate {expiration_date})
(SubCompany)-[:HAS_EMR]->(EMRRecord {emr_value})
```

### Procurement <> Schedule <> Financial
```cypher
# "Is material ordered for next week's task?"
(ScheduleTask)<-[:PO_GATES_TASK]-(PurchaseOrder)-[:PO_FOR_VENDOR]->(Company)

# "What's the procurement status for this submittal?"
(Submittal)-[:SUBMITTAL_SATISFIES_SPEC]->(SpecSection)
(PurchaseOrder)-[:PO_FROM_SUBMITTAL]->(Submittal)
```

### Location as hub (all domains)
```
(Inspection)-[:AT_LOCATION]->(Location)
(Incident)-[:AT_LOCATION]->(Location)
(ScheduleTask)-[:AT_LOCATION]->(Location)
(Equipment)-[:DEPLOYED_TO_LOCATION]->(Location)
(DeficiencyItem)-[:AT_LOCATION]->(Location)
(CorrectiveAction)-[:AT_LOCATION]->(Location)
(SafetyZone)-[:COVERS]->(Location)
(MaterialDelivery)-[:DELIVERED_TO]->(Location)
(HazardReport)-[:AT_LOCATION]->(Location)
```

---

## Scenario Validation

### Scenario 1: "Can we pour foundations Friday?"

Agent traversal:
```
1. MATCH (t:ScheduleTask {name: 'Foundation Pour', start_planned: Friday})
2. -[:REQUIRES_CERT]-> (ct:CertificationType) -- what certs are needed?
3. <-[:OF_TYPE]-(c:Certification)<-[:HOLDS_CERT]-(w:Worker)-[:ASSIGNED_TO]->(project)
     WHERE c.expiry_date >= Friday -- are they valid through Friday?
4. (t)-[:REQUIRES_EQUIPMENT]->(e:Equipment)-[:HAS_INSPECTION_LOG]->(log)
     WHERE log.next_inspection_due <= Friday -- equipment inspected?
5. (t)-[:AT_LOCATION]->(loc)<-[:AT_LOCATION]-(ca:CorrectiveAction {status:'open'})
     -- any open corrective actions in the pour area?
6. Weather API check for Friday
7. RETURN prerequisites met/unmet with specific gaps
```

### Scenario 2: "What's the compliance status of Sub X?"

Agent traversal:
```
1. MATCH (gc:Company)-[:GC_OVER]->(sub:Company {name: 'Sub X'})
2. (sub)-[:HAS_INSURANCE]->(cert:InsuranceCertificate)
     -- check expiry dates, limits, additional insured
3. (sub)-[:HAS_EMR]->(emr:EMRRecord) -- current EMR
4. (sub)-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO]->(p:Project)
     (w)-[:HOLDS_CERT]->(c:Certification) -- cert gaps?
5. (p)-[:HAS_INSPECTION]->(i:Inspection) WHERE i.created_by IN sub_workers
     -- inspection pass rates
6. (p)-[:HAS_INCIDENT]->(inc:Incident) WHERE inc.involved_worker_ids IN sub_workers
     -- incident frequency
7. RETURN composite compliance score
```

### Scenario 3: "Morning brief for Project Y"

Agent traversal:
```
1. MATCH (p:Project {name: 'Project Y'})
2. (p)<-[:ASSIGNED_TO {status:'active'}]-(w:Worker)-[:HOLDS_CERT]->(c:Certification)
     WHERE c.expiry_date <= date() + 14 days -- expiring certs
3. (p)-[:HAS_INSPECTION]->(i:Inspection)
     WHERE i.inspection_date >= date() - 2 days -- recent inspections
4. (p)-[:HAS_TOOLBOX_TALK]->(tt:ToolboxTalk)
     WHERE tt.scheduled_date >= date() - 7 days -- recent talks
5. (p)-[:HAS_INCIDENT]->(inc:Incident)
     WHERE inc.incident_date >= date() - 30 days -- recent incidents
6. (p)-[:INVOLVES_TRADE]->(t:TradeType)-[:PERFORMS]->(a:Activity)
     -[:REGULATED_BY]->(r:Regulation) -- applicable regulations
7. (p)<-[:DEPLOYED_TO]-(e:Equipment) WHERE e.next_inspection_due <= date()
     -- overdue equipment inspections
8. Weather API for project location
9. RETURN assembled brief context
```

---

## Node Count Estimates

### Regulatory (static, shared)
| Node | Estimated Count |
|---|---|
| Jurisdiction | 4 |
| Region | 5+ (expandable) |
| RegulatoryGroup | 27 |
| Regulation | ~100 (key sections, expandable) |
| ComplianceProgram | 17 |
| CertificationType | 40+ (26 base + NCCCO) |
| TradeType | 20 |
| Role | 15 |
| Activity | ~50 |
| HazardCategory | 10 |
| Substance | 4+ |
| DocumentType | 6 |
| InspectionType | 8 |
| RegionalRequirement | ~20 (expandable to 50 states) |
| **Subtotal** | **~330 nodes, ~1,500 edges** |

### Operational (per company, grows with usage)
A typical company with 50 workers, 5 projects, 6 months of data:
| Node | Estimated Count |
|---|---|
| Workers | 50 |
| Certifications | 200 (4 per worker avg) |
| Equipment | 20 |
| Inspections | 600 (daily x 5 projects x ~6 months) |
| Incidents | 10 |
| Toolbox Talks | 130 |
| Hazard Reports | 50 |
| Daily Logs | 600 |
| Locations | 50 |
| PurchaseOrders | 100 |
| NonConformanceReports | 20 |
| Observations | 200 |
| ITPs + Checkpoints | 50 |
| Material Tests | 100 |
| **Subtotal per company** | **~2,170 nodes, ~8,000 edges** |

At 1,000 companies: ~2.2M operational nodes + 330 shared regulatory nodes.

---

*This ontology is a living document. As new domains are implemented, their node and relationship definitions move from "schema now, build later" to active. The cross-domain edge catalogue grows as new connections between domains are discovered during implementation and usage.*
