# Schema Definition

Complete property-level specification of every entity and relationship in the Kerf ontology. This is the source of truth for generating the Cypher DDL in Phase 7.

**Conventions:**
- All monetary values: integers in smallest currency unit (cents/pence)
- All IDs: `{prefix}_{secrets.token_hex(8)}`
- All mutable entities carry provenance fields (DD-09)
- snake_case properties (DD-01)
- Temporal: valid_from/valid_until on regulatory entities; created_at/updated_at on business entities (DD-03)

**Provenance fields (on every mutable tenant-scoped entity):**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| created_by | String | Yes | Member ID or AgentIdentity ID |
| created_by_type | String | Yes | "human" or "agent" |
| created_at | DateTime | Yes | Creation timestamp |
| updated_by | String | Yes | Last modifier ID |
| updated_by_type | String | Yes | "human" or "agent" |
| updated_at | DateTime | Yes | Last modification timestamp |

Agent-specific provenance (when created_by_type = "agent"):

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| agent_version | String | No | Version of the agent |
| model_id | String | No | Which LLM model was used |
| confidence | Float | No | Agent's declared confidence |

---

## Organisational

### Company

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `comp_{hex}` |
| name | String | Yes | No | Company name |
| type | String | Yes | No | "contractor", "gc", "sub", "client" |
| jurisdiction_code | String | Yes | Yes | Links to Jurisdiction |
| region_code | String | No | Yes | Links to Region (state/province) |
| default_currency | String | Yes | No | ISO 4217 (GBP, USD, AUD, CAD, EUR) |
| measurement_system | String | Yes | No | "metric" or "imperial" |
| default_language | String | Yes | No | ISO 639-1 (en, es, pl, fr, zh, vi) |
| additional_languages | List\<String\> | No | No | Other workforce languages |
| status | String | Yes | Yes | "active", "suspended", "archived" |
| created_at | DateTime | Yes | No | |
| updated_at | DateTime | Yes | No | |

### Member

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `mem_{hex}` |
| uid | String | Yes | Yes | Firebase/auth UID |
| email | String | Yes | Yes | |
| name | String | Yes | No | |
| access_role | String | Yes | Yes | "owner", "admin", "manager", "foreman", "worker" |
| preferred_language | String | No | No | ISO 639-1 |
| status | String | Yes | No | "active", "invited", "suspended" |
| created_at | DateTime | Yes | No | |
| updated_at | DateTime | Yes | No | |

### Contact

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `cont_{hex}` |
| name | String | Yes | No | |
| email | String | No | Yes | |
| phone | String | No | No | |
| company_name | String | No | No | External company (not a Company node unless they're also a tenant) |
| role_description | String | No | No | "architect", "GC project manager", "client", "inspector" |
| + provenance fields | | | | |

---

## Project Lifecycle

### Project

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `proj_{hex}` |
| name | String | Yes | No | |
| description | String | No | No | |
| status | String | Yes | Yes | "lead", "quoted", "active", "complete", "closed", "lost" |
| type | String | No | Yes | "residential", "commercial", "industrial", "infrastructure", "renovation", etc. |
| pricing_model | String | No | No | "fixed_price", "cost_plus", "time_and_materials". Affects client visibility |
| address | String | No | No | Site address |
| latitude | Float | No | No | |
| longitude | Float | No | No | |
| jurisdiction_code | String | No | Yes | Override company jurisdiction for this project. Null = inherit from Company |
| currency | String | No | No | Override company currency for this project. ISO 4217. Null = inherit from Company |
| planned_start | Date | No | No | |
| planned_end | Date | No | No | |
| actual_start | Date | No | No | |
| actual_end | Date | No | No | |
| contract_value | Integer | No | No | Agreed price, smallest currency unit |
| margin_pct | Float | No | No | Overall margin. Can be overridden at WorkPackage or WorkItem level |
| quoted_at | DateTime | No | No | When the quote was sent |
| won_at | DateTime | No | No | When the project was won |
| + provenance fields | | | | |

### WorkPackage

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `wp_{hex}` |
| name | String | Yes | No | "Electrical rough-in", "Ground floor fit-out" |
| description | String | No | No | |
| sort_order | Integer | No | No | Display ordering |
| status | String | Yes | No | "active", "complete", "archived" |
| + provenance fields | | | | |

### WorkItem

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `wi_{hex}` |
| description | String | Yes | No | "Install 84 standard receptacles" or "Strip out old bathroom" |
| state | String | Yes | Yes | Lifecycle position: "draft", "scheduled", "in_progress", "complete", "invoiced", "on_hold", "cancelled" |
| status | String | No | No | Current condition within the state. Free text, set by agent from conversation. E.g., "Waiting on materials", "Blocked by framing", "Ready for inspection". Null when progressing normally |
| labour_hours | Float | No | No | Estimated hours |
| labour_rate | Integer | No | No | Per hour, smallest currency unit |
| materials_allowance | Integer | No | No | Lump sum for sundries/minor items |
| margin_pct | Float | No | No | Optional, may be at WorkPackage or Project level |
| planned_start | Date | No | Yes | Populated when scheduled. Indexed for schedule queries |
| planned_end | Date | No | Yes | |
| actual_start | Date | No | No | Populated when work begins |
| actual_end | Date | No | No | Populated when work finishes |
| notes | String | No | No | |

Note: All calculated values are computed at query time, not stored:
- Labour cost = labour_hours × labour_rate
- Materials cost = sum of USES_ITEM relationship costs
- Total = labour cost + materials cost + materials_allowance
- Actual labour hours = sum of linked TimeEntries
- Actual materials cost = sum of actual_cost on USES_ITEM relationships
| + provenance fields | | | | |

### WorkCategory

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `wcat_{hex}` |
| name | String | Yes | No | "Electrical", "Electrical Rough-In", "Receptacles" |
| description | String | No | No | |
| level | Integer | No | No | Hierarchy depth (0 = root) |
| + provenance fields | | | | |

---

## Commercial

Note: There is no separate Estimate entity. The work items on a project at "quoted" status ARE the estimate. Change history is tracked by provenance fields and conversation memory.

### Contract

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ctr_{hex}` |
| status | String | Yes | Yes | "draft", "active", "complete", "terminated" |
| value | Integer | Yes | No | Contract value, smallest currency unit |
| currency | String | No | No | ISO 4217. Null = inherit from Project/Company |
| retention_pct | Float | No | No | Retention percentage (e.g., 5.0 = 5%) |
| payment_terms | String | No | No | "30 days", "net 14", etc. |
| payment_schedule | String | No | No | "monthly progress", "on completion", "staged" |
| scope_description | String | No | No | |
| start_date | Date | No | No | |
| end_date | Date | No | No | |
| + provenance fields | | | | |

---

## Items (Global Shared Catalogue)

### Item

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `item_{hex}` |
| name | String | Yes | Yes | "Leviton 5320-W receptacle", "12/2 NM-B cable", "Roca Continental bath" |
| description | String | No | No | |
| category | String | No | Yes | For future split: "material", "product", "consumable". Null for now |
| default_unit | String | Yes | No | "each", "m", "m2", "kg", "roll", "box", etc. |
| created_at | DateTime | Yes | No | |

Note: Item is NOT tenant-scoped. It's a shared global catalogue like regulatory entities. No company_id, no provenance fields. Items are created as contractors use them and grow the catalogue over time.

---

## Financial

### TimeEntry

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `te_{hex}` |
| clock_in | DateTime | Yes | Yes | |
| clock_out | DateTime | No | No | Null if still clocked in |
| hours_regular | Float | No | No | Calculated |
| hours_overtime | Float | No | No | Calculated |
| break_minutes | Integer | No | No | Break time deducted |
| source | String | Yes | No | "worker_self", "foreman_entry", "auto_detected" |
| status | String | Yes | Yes | "draft", "submitted", "approved" |
| clock_in_latitude | Float | No | No | GPS at clock-in |
| clock_in_longitude | Float | No | No | |
| clock_out_latitude | Float | No | No | GPS at clock-out |
| clock_out_longitude | Float | No | No | |
| notes | String | No | No | |
| + provenance fields | | | | |

### Variation

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `var_{hex}` |
| number | Integer | Yes | No | Sequential per project |
| description | String | Yes | No | What changed and why |
| status | String | Yes | Yes | "draft", "submitted", "approved", "rejected" |
| amount | Integer | No | No | Cost impact, smallest currency unit |
| + provenance fields | | | | |

### Invoice

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `inv_{hex}` |
| direction | String | Yes | Yes | "outbound" (to client) or "inbound" (from sub) |
| number | String | Yes | Yes | Invoice number (company-formatted) |
| status | String | Yes | Yes | "draft", "sent", "paid", "partially_paid", "overdue", "cancelled" |
| amount | Integer | Yes | No | Total, smallest currency unit |
| due_date | Date | Yes | Yes | |
| sent_date | Date | No | No | |
| paid_date | Date | No | No | |
| notes | String | No | No | |
| + provenance fields | | | | |

### InvoiceLine

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `invl_{hex}` |
| description | String | Yes | No | |
| amount | Integer | Yes | No | Smallest currency unit |
| + provenance fields | | | | |

### Payment

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `pay_{hex}` |
| amount | Integer | Yes | No | Smallest currency unit |
| received_date | Date | Yes | Yes | |
| method | String | No | No | "bank_transfer", "cheque", "card", "cash" |
| reference | String | No | No | Transaction reference |
| + provenance fields | | | | |

### PaymentApplication

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `papp_{hex}` |
| period | String | Yes | No | Billing period description |
| amount_requested | Integer | Yes | No | |
| amount_approved | Integer | No | No | |
| retention_held | Integer | No | No | |
| status | String | Yes | Yes | "draft", "submitted", "approved", "paid" |
| + provenance fields | | | | |

---

## Workforce

### Worker

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `wkr_{hex}` |
| name | String | Yes | No | |
| email | String | No | Yes | |
| phone | String | No | No | |
| status | String | Yes | Yes | "active", "inactive", "archived" |
| preferred_language | String | No | No | ISO 639-1 |
| + provenance fields | | | | |

### Certification

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `cert_{hex}` |
| status | String | Yes | Yes | "active", "expired", "revoked" |
| issue_date | Date | No | No | |
| expiry_date | Date | Yes | Yes | |
| certificate_number | String | No | No | |
| issuing_body | String | No | No | |
| + provenance fields | | | | |

### Crew

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `crew_{hex}` |
| name | String | Yes | No | "Marco's crew", "Night shift" |
| status | String | Yes | No | "active", "archived" |
| + provenance fields | | | | |

---

## Equipment

### Equipment

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `eq_{hex}` |
| name | String | Yes | No | |
| type | String | Yes | No | "crane", "forklift", "excavator", "vehicle" |
| serial_number | String | No | Yes | |
| status | String | Yes | Yes | "active", "maintenance", "decommissioned" |
| + provenance fields | | | | |

### EquipmentInspectionLog

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `eqinsp_{hex}` |
| inspection_date | Date | Yes | Yes | |
| result | String | Yes | No | "pass", "fail", "conditional" |
| next_due | Date | No | No | |
| inspector | String | No | No | |
| notes | String | No | No | |
| + provenance fields | | | | |

---

## Safety & Quality

### Inspection

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `insp_{hex}` |
| category | String | Yes | Yes | "safety", "quality", "environmental", "equipment", "simulated" |
| inspection_date | Date | Yes | Yes | |
| overall_status | String | Yes | Yes | "pass", "fail", "conditional", "in_progress" |
| score | Float | No | No | Percentage or points |
| notes | String | No | No | |
| + provenance fields | | | | |

### InspectionItem

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `inspi_{hex}` |
| description | String | Yes | No | |
| status | String | Yes | No | "pass", "fail", "na", "not_inspected" |
| notes | String | No | No | |
| photo_urls | List\<String\> | No | No | |
| + provenance fields | | | | |

### Incident

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `inc_{hex}` |
| incident_date | DateTime | Yes | Yes | |
| severity | String | Yes | Yes | "first_aid", "recordable", "lost_time", "fatality", "near_miss", "property_damage" |
| classification | String | No | No | Links to IncidentClassification per jurisdiction |
| status | String | Yes | Yes | "reported", "investigating", "closed" |
| description | String | Yes | No | |
| root_cause | String | No | No | |
| + provenance fields | | | | |

### HazardReport

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `haz_{hex}` |
| status | String | Yes | Yes | "reported", "under_review", "resolved", "archived" |
| severity | String | Yes | No | "low", "medium", "high", "critical" |
| description | String | Yes | No | |
| photo_urls | List\<String\> | No | No | |
| + provenance fields | | | | |

### HazardObservation

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `hobs_{hex}` |
| description | String | Yes | No | |
| risk_level | String | No | No | "low", "medium", "high", "critical" |
| control_recommendation | String | No | No | |
| + provenance fields | | | | |

### CorrectiveAction

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ca_{hex}` |
| description | String | Yes | No | |
| status | String | Yes | Yes | "open", "in_progress", "complete", "overdue", "verified" |
| due_date | Date | Yes | Yes | |
| completed_date | Date | No | No | |
| priority | String | No | No | "low", "medium", "high", "critical" |
| + provenance fields | | | | |

### ToolboxTalk

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `talk_{hex}` |
| topic | String | Yes | No | |
| date | Date | Yes | No | |
| status | String | Yes | Yes | "draft", "delivered", "archived" |
| content | String | No | No | Generated content |
| language | String | No | No | Primary language of delivery |
| + provenance fields | | | | |

### ExposureRecord

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `exp_{hex}` |
| exposure_date | Date | Yes | No | |
| duration_minutes | Integer | No | No | |
| measured_level | Float | No | No | |
| measurement_unit | String | No | No | |
| notes | String | No | No | |
| + provenance fields | | | | |

### MorningBrief

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `brief_{hex}` |
| date | Date | Yes | Yes | |
| content | String | No | No | Generated briefing content |
| risk_score | Float | No | No | |
| + provenance fields | | | | |

### DeficiencyList

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `dfl_{hex}` |
| name | String | Yes | No | |
| status | String | Yes | No | "open", "in_progress", "complete" |
| + provenance fields | | | | |

### DeficiencyItem

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `dfi_{hex}` |
| description | String | Yes | No | |
| status | String | Yes | Yes | "identified", "assigned", "corrected", "verified", "closed" |
| due_date | Date | No | No | |
| location | String | No | No | Where on site |
| photo_urls | List\<String\> | No | No | |
| + provenance fields | | | | |

### IncidentLogEntry

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ile_{hex}` |
| entry_date | Date | Yes | Yes | |
| case_number | String | No | Yes | |
| year | Integer | Yes | Yes | Reporting year |
| form_type | String | No | No | Links to RecordForm per jurisdiction |
| details | String | No | No | |
| + provenance fields | | | | |

---

## Daily Operations

### DailyLog

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `dlog_{hex}` |
| log_date | Date | Yes | Yes | |
| status | String | Yes | Yes | "draft", "submitted", "approved" |
| weather_summary | String | No | No | |
| temperature_high | Float | No | No | |
| temperature_low | Float | No | No | |
| wind_conditions | String | No | No | |
| precipitation | String | No | No | |
| crew_count_own | Integer | No | No | |
| ~~crew_count_sub~~ | — | — | — | REMOVED: replaced by HAS_SUB_CREW relationship (DailyLog → Company with headcount property) |
| work_performed | String | No | No | Narrative |
| notes | String | No | No | |
| submitted_at | DateTime | No | No | |
| submitted_by | String | No | No | |
| + provenance fields | | | | |

### MaterialDelivery

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `mdel_{hex}` |
| date | Date | Yes | No | |
| description | String | Yes | No | |
| supplier | String | No | No | |
| received_by | String | No | No | |
| + provenance fields | | | | |

### DelayRecord

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `delay_{hex}` |
| cause | String | Yes | No | |
| duration_hours | Float | No | No | |
| impact | String | No | No | |
| responsible_party | String | No | No | |
| + provenance fields | | | | |

### VisitorRecord

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `vis_{hex}` |
| name | String | Yes | No | |
| company | String | No | No | |
| purpose | String | No | No | |
| time_in | DateTime | No | No | |
| time_out | DateTime | No | No | |
| + provenance fields | | | | |

---

## Scheduling

### Milestone

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ms_{hex}` |
| name | String | Yes | No | |
| planned_date | Date | Yes | Yes | Indexed for schedule queries |
| actual_date | Date | No | No | |
| status | String | Yes | No | "upcoming", "met", "missed" |
| + provenance fields | | | | |

---

## Project Coordination

### ProjectQuery

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `pq_{hex}` |
| number | Integer | Yes | No | Sequential per project |
| subject | String | Yes | No | |
| description | String | Yes | No | |
| status | String | Yes | Yes | "draft", "submitted", "responded", "closed" |
| due_date | Date | No | Yes | |
| priority | String | No | No | "low", "normal", "high", "urgent" |
| + provenance fields | | | | |

### QueryResponse

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `qr_{hex}` |
| content | String | Yes | No | |
| response_date | Date | Yes | No | |
| + provenance fields | | | | |

### ReviewSubmission

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `rsub_{hex}` |
| title | String | Yes | No | |
| spec_section | String | No | No | |
| status | String | Yes | Yes | "submitted", "under_review", "approved", "rejected", "revise_resubmit" |
| + provenance fields | | | | |

### Warranty

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `warr_{hex}` |
| scope | String | Yes | No | What's covered |
| start_date | Date | Yes | No | |
| end_date | Date | Yes | Yes | |
| terms | String | No | No | |
| + provenance fields | | | | |

---

## Sub Management

### GcRelationship

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `gcrel_{hex}` |
| status | String | Yes | No | "active", "inactive" |
| + provenance fields | | | | |

### InsuranceCertificate

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `icert_{hex}` |
| carrier | String | No | No | Insurance company |
| policy_number | String | No | No | |
| coverage_type | String | No | No | "general_liability", "workers_comp", "auto", "umbrella" |
| coverage_limit | Integer | No | No | Smallest currency unit |
| effective_date | Date | No | No | |
| expiration_date | Date | Yes | Yes | |
| status | String | Yes | Yes | "active", "expiring_soon", "expired", "non_compliant" |
| additional_insured | Boolean | No | No | |
| + provenance fields | | | | |

### PrequalPackage

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `prq_{hex}` |
| status | String | Yes | No | "draft", "submitted", "approved", "rejected" |
| submitted_date | Date | No | No | |
| + provenance fields | | | | |

### PaymentRelease

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `lw_{hex}` |
| type | String | Yes | No | "conditional", "unconditional" |
| status | String | Yes | No | "pending", "received", "verified" |
| amount | Integer | No | No | |
| + provenance fields | | | | |

---

## Conversation & Memory

### Conversation

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `conv_{hex}` |
| mode | String | Yes | No | "chat", "voice" |
| title | String | No | No | Auto-generated or user-set |
| started_at | DateTime | Yes | No | |
| ended_at | DateTime | No | No | |
| transcript_url | String | No | No | Full transcript in object storage |
| + provenance fields | | | | |

### Message

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `msg_{hex}` |
| role | String | Yes | No | "user", "assistant", "system" |
| content | String | Yes | No | Message text |
| timestamp | DateTime | Yes | Yes | |
| embedding | List\<Float\> | No | Vector | Vector embedding for semantic search |

Note: Messages do NOT carry provenance fields. The SENT_BY relationship identifies the author. Messages are immutable once created.

### Decision

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `dec_{hex}` |
| description | String | Yes | No | What was decided |
| reasoning | String | No | No | Why it was decided |
| confidence | Float | No | No | How certain the extraction is |
| created_at | DateTime | Yes | No | |

### Insight

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ins_{hex}` |
| content | String | Yes | No | "I use 0.38 hours per receptacle in renovations" |
| confidence | Float | No | No | How certain the extraction is |
| applicability_tags | List\<String\> | No | No | "renovation", "receptacles", "labour_rate" |
| created_at | DateTime | Yes | No | |

---

## Documents & Intelligence

### Document

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `doc_{hex}` |
| title | String | Yes | No | |
| type | String | Yes | Yes | "safety_plan", "risk_assessment", "method_statement", "environmental_compliance", "contract", "specification", "drawing", "insurance_certificate", "permit", "report", etc. |
| status | String | Yes | Yes | "draft", "active", "archived", "superseded" |
| file_url | String | No | No | Object storage URL |
| file_type | String | No | No | "pdf", "docx", "xlsx", "image" |
| ingestion_status | String | No | No | "pending", "processing", "complete", "failed" |
| chunk_count | Integer | No | No | Number of DocumentChunks created |
| + provenance fields | | | | |

### DocumentChunk

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `dchk_{hex}` |
| text | String | Yes | No | Chunk text content |
| page | Integer | No | No | Source page number |
| position | Integer | No | No | Position within page |
| chunk_index | Integer | Yes | No | Order within document |
| embedding | List\<Float\> | No | Vector | Vector embedding for semantic search |
| created_at | DateTime | Yes | No | |

---

## Spatial

### Location

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `loc_{hex}` |
| address_line_1 | String | No | No | |
| city | String | No | No | |
| region | String | No | No | State/province |
| postal_code | String | No | No | |
| country | String | No | No | |
| latitude | Float | No | No | |
| longitude | Float | No | No | |
| location_type | String | No | Yes | "project_site", "office", "storage" |
| qr_code_id | String | No | Yes | |

### SafetyZone

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `sz_{hex}` |
| name | String | Yes | No | |
| zone_type | String | Yes | Yes | "permit_required", "fall_hazard", "restricted" |
| description | String | No | No | |

---

## Access & Permissions

### AccessGrant

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `ag_{hex}` |
| scopes | List\<String\> | Yes | No | "compliance", "progress", "invoices", "queries", "safety" |
| granted_at | DateTime | Yes | No | |
| granted_by | String | Yes | No | Member ID who granted |
| expires_at | DateTime | No | No | Null = no expiry |
| status | String | Yes | No | "active", "expired", "revoked" |

---

## Agentic

### AgentIdentity

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `agt_{hex}` |
| name | String | Yes | No | "Compliance Checker", "Briefing Agent" |
| agent_type | String | Yes | Yes | "compliance", "briefing", "estimating", "costing" |
| agent_version | String | Yes | No | "1.0.0" |
| status | String | Yes | Yes | "active", "suspended", "revoked" |
| scopes | List\<String\> | Yes | No | "read:safety", "write:inspections", etc. |
| model_tier | String | No | No | "fast", "standard", "advanced" |
| daily_budget_cents | Integer | No | No | |
| daily_spend_cents | Integer | No | No | Reset daily |
| created_at | DateTime | Yes | No | |

### ComplianceAlert

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `calert_{hex}` |
| alert_type | String | Yes | Yes | |
| severity | String | Yes | Yes | "info", "warning", "critical" |
| message | String | Yes | No | |
| created_at | DateTime | Yes | Yes | |

### BriefingSummary

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| id | String | Yes | Unique | `bsum_{hex}` |
| date | Date | Yes | Yes | |
| content | String | No | No | |
| created_at | DateTime | Yes | Yes | |

---

## Regulatory (Shared — existing, properties confirmed)

Properties for regulatory entities are not repeated in full here as they are established in the existing schema. Key additions:

**Jurisdiction enrichment:**

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| languages | List\<String\> | Yes | No | ISO 639-1 codes for this jurisdiction |
| default_currency | String | Yes | No | ISO 4217 |
| measurement_system | String | Yes | No | "metric" or "imperial" |
| date_format | String | No | No | Locale date convention |

**Regulation temporal properties (DD-03):**

| Property | Type | Required | Indexed | Description |
|----------|------|----------|---------|-------------|
| valid_from | Date | Yes | Yes | When this regulation took effect |
| valid_until | Date | Yes | Yes | Sentinel 9999-12-31 for current. Enables temporal queries |

All other regulatory entities (Region, RegulatoryGroup, CertificationType, TradeType, Role, Activity, HazardCategory, Substance, DocumentType, InspectionType, RegionalRequirement, ViolationType, IncidentClassification, RecordForm, RegulatoryVersion, ComplianceProgram) retain their existing property structures.

---

## Relationship Specification

### Organisational

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| OWNS_PROJECT | Company → Project | 1:N | — | Yes (Company.id) |
| EMPLOYS | Company → Worker | 1:N | hire_date, status | — |
| HAS_MEMBER | Company → Member | 1:N | — | — |
| HAS_CONTACT | Company → Contact | 1:N | relationship_type | — |
| HAS_EQUIPMENT | Company → Equipment | 1:N | — | — |
| HAS_WORK_CATEGORY | Company → WorkCategory | 1:N | — | — |
| IN_JURISDICTION | Company → Jurisdiction | N:1 | — | — |
| IN_REGION | Company → Region | N:1 | — | — |
| GC_OVER | Company → Company | N:M | via GcRelationship | — |

### Work Model

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_WORK_PACKAGE | Project → WorkPackage | 1:N | — | — |
| HAS_WORK_ITEM | Project → WorkItem | 1:N | — | — |
| CONTAINS | WorkPackage → WorkItem | 1:N | sort_order | — |
| CLASSIFIED_AS | WorkItem → WorkCategory | N:1 | — | — |
| PRECEDED_BY | WorkItem → WorkItem | N:M | dependency_type | — |
| ASSIGNED_TO_WORKER | WorkItem → Worker | N:M | — | — |
| ASSIGNED_TO_CREW | WorkItem → Crew | N:1 | — | — |
| USES_EQUIPMENT | WorkItem → Equipment | N:M | — | — |
| USES_ITEM | WorkItem → Item | N:M | quantity, unit, unit_cost, actual_cost | — |
| PERFORMED_BY | WorkItem → Company | N:1 | — | — |
| AT_LOCATION | WorkItem → Location | N:1 | — | — |

### Commercial

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_CONTRACT | Project → Contract | 1:N | — | — |
| CLIENT_IS | Project → Contact | N:1 | — | — |
| CLIENT_COMPANY | Project → Company | N:1 | — | — |

### Financial

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_TIME_ENTRY | WorkItem → TimeEntry | 1:N | — | — |
| LOGGED_BY | TimeEntry → Worker | N:1 | — | — |
| FOR_PROJECT | TimeEntry → Project | N:1 | — | — |
| HAS_VARIATION | Project → Variation | 1:N | — | — |
| EVIDENCED_BY | Variation → DailyLog/TimeEntry/Document | N:M | — | — |
| VARIES | Variation → WorkItem | N:M | — | — |
| HAS_INVOICE | Project → Invoice | 1:N | — | — |
| HAS_LINE | Invoice → InvoiceLine | 1:N | — | — |
| COVERS | InvoiceLine → WorkItem | N:M | — | — |
| PAID_BY | Invoice → Payment | 1:N | — | — |
| HAS_PAYMENT_APP | Project → PaymentApplication | 1:N | — | — |
| WAIVED_BY | PaymentApplication → PaymentRelease | 1:N | — | — |

### Workforce

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| ASSIGNED_TO_PROJECT | Worker → Project | N:M | role, start_date | — |
| HOLDS_CERT | Worker → Certification | 1:N | — | — |
| OF_TYPE | Certification → CertificationType | N:1 | — | — |
| HAS_TRADE | Worker → TradeType | N:M | — | — |
| MEMBER_OF | Worker → Crew | N:M | — | — |
| LED_BY | Crew → Worker | N:1 | — | — |
| MANAGES | Member → Project | N:M | — | — |

### Safety & Quality

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_INSPECTION | Project → Inspection | 1:N | — | — |
| CONDUCTED_BY | Inspection → Worker/Member | N:1 | — | — |
| HAS_ITEM | Inspection → InspectionItem | 1:N | — | — |
| HAS_INCIDENT | Project → Incident | 1:N | — | — |
| INVOLVED_IN | Worker → Incident | N:M | role (injured_party, witness, first_responder) | — |
| HAS_HAZARD_REPORT | Project → HazardReport | 1:N | — | — |
| REPORTED_BY | HazardReport → Worker/Member | N:1 | — | — |
| HAS_OBSERVATION | HazardReport → HazardObservation | 1:N | — | — |
| HAS_CORRECTIVE_ACTION | (multiple) → CorrectiveAction | 1:N | — | — |
| RESOLVE_BY | CorrectiveAction → Worker/Company | N:1 | — | — |
| HAS_TOOLBOX_TALK | Project → ToolboxTalk | 1:N | — | — |
| ATTENDED_BY | ToolboxTalk → Worker | N:M | — | — |
| HAS_EXPOSURE | Worker → ExposureRecord | 1:N | — | — |
| EXPOSURE_TO | ExposureRecord → Substance | N:1 | — | — |
| HAS_INCIDENT_LOG | Company → IncidentLogEntry | 1:N | — | — |
| RECORDS | IncidentLogEntry → Incident | N:1 | — | — |
| HAS_DEFICIENCY_LIST | Project → DeficiencyList | 1:N | — | — |
| HAS_DEFICIENCY | DeficiencyList → DeficiencyItem | 1:N | — | — |
| RESOLVE_BY | DeficiencyItem → Worker/Company | N:1 | — | — |

### Daily Operations

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_DAILY_LOG | Project → DailyLog | 1:N | — | — |
| RECORDED_ON | TimeEntry → DailyLog | N:1 | — | — |
| RECORDED_ON | Inspection → DailyLog | N:1 | — | — |
| RECORDED_ON | Incident → DailyLog | N:1 | — | — |
| HAS_SUB_CREW | DailyLog → Company | N:M | headcount | — |
| HAS_DELIVERY | DailyLog → MaterialDelivery | 1:N | — | — |
| HAS_DELAY | DailyLog → DelayRecord | 1:N | — | — |
| HAS_VISITOR | DailyLog → VisitorRecord | 1:N | — | — |

### Spatial

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| LOCATED_AT | Project → Location | N:1 | — | — |
| INSPECTION_FREQUENCY | Project → InspectionType | N:M | frequency (override, must be >= regulatory minimum) | — |
| HAS_SAFETY_ZONE | Project → SafetyZone | 1:N | — | — |

### Scheduling

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_MILESTONE | Project → Milestone | 1:N | — | — |

### Project Coordination

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_QUERY | Project → ProjectQuery | 1:N | — | — |
| HAS_RESPONSE | ProjectQuery → QueryResponse | 1:N | — | — |
| ASSIGNED_TO_RESPONDER | ProjectQuery → Contact/Member | N:1 | — | — |
| HAS_SUBMISSION | Project → ReviewSubmission | 1:N | — | — |
| HAS_WARRANTY | Project → Warranty | 1:N | — | — |

### Sub Management

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_INSURANCE | Company → InsuranceCertificate | 1:N | — | — |
| HAS_PREQUAL | Company → PrequalPackage | 1:N | — | — |
| SUB_ON | Company → Project | N:M | — | — |

### Conversation & Memory

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_CONVERSATION | Company → Conversation | 1:N | — | — |
| ABOUT_PROJECT | Conversation → Project | N:M | — | — |
| PART_OF | Message → Conversation | N:1 | — | — |
| FOLLOWS | Message → Message | 1:1 | — | — |
| SENT_BY | Message → Member/AgentIdentity | N:1 | — | — |
| REFERENCES | Message → (any entity) | N:M | entity_type | — |
| PRODUCED_DECISION | Conversation → Decision | 1:N | — | — |
| AFFECTS | Decision → (any entity) | N:M | — | — |
| EXPRESSED_KNOWLEDGE | Conversation → Insight | 1:N | — | — |

### Documents & Intelligence

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_DOCUMENT | Project → Document | 1:N | — | — |
| CHUNK_OF | DocumentChunk → Document | N:1 | — | — |
| NEXT_CHUNK | DocumentChunk → DocumentChunk | 1:1 | — | — |
| MENTIONS | DocumentChunk → (any entity) | N:M | entity_type | — |

### Regulatory (Layer 3)

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_REGION | Jurisdiction → Region | 1:N | — | — |
| BELONGS_TO_GROUP | Regulation → RegulatoryGroup | N:1 | — | — |
| REGULATED_BY | Activity → Regulation | N:M | — | — |
| REQUIRES_CONTROL | Regulation → CertificationType | N:M | when (condition) | — |
| REQUIRES_INSPECTION | Regulation → InspectionType | N:M | frequency (daily/weekly/monthly/per_use) | — |
| REQUIRES_DOCUMENT | Regulation → DocumentType | N:M | — | — |
| REQUIRES_ROLE | Regulation → Role | N:M | — | — |
| HAS_CLASSIFICATION | Jurisdiction → IncidentClassification | 1:N | — | — |
| HAS_VIOLATION_TYPE | Jurisdiction → ViolationType | 1:N | — | — |
| HAS_RECORD_FORM | Jurisdiction → RecordForm | 1:N | — | — |
| SUPERSEDES | Regulation → Regulation | 1:1 | — | — |
| INVOLVES_SUBSTANCE | Activity → Substance | N:M | — | — |
| LINKS_TO_ACTIVITY | WorkCategory → Activity | N:M | — | — |
| PARENT_CATEGORY | WorkCategory → WorkCategory | N:1 | — | — |

### Access & Permissions

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| HAS_ACCESS_GRANT | Member/Contact → AccessGrant | 1:N | — | — |
| GRANT_FOR | AccessGrant → Project/Company | N:1 | — | — |

### Agentic

| Relationship | From → To | Cardinality | Properties | Indexed |
|-------------|-----------|-------------|------------|---------|
| BELONGS_TO | AgentIdentity → Company | N:1 | — | — |
| HAS_GRANT | AgentIdentity → Company | N:M | scopes, granted_at, granted_by | — |
| GENERATED_BY | ComplianceAlert/BriefingSummary → AgentIdentity | N:1 | — | — |

---

## Vector Indexes

```cypher
CREATE VECTOR INDEX message_embeddings IF NOT EXISTS
FOR (m:Message)
ON (m.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}

CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:DocumentChunk)
ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

---

## CQ Validation Queries

Sample Cypher queries proving key CQs are answerable:

### CQ-023: What work remains on this job?
```cypher
MATCH (p:Project {id: $projectId})-[:HAS_WORK_ITEM|HAS_WORK_PACKAGE*1..2]->(wi:WorkItem)
WHERE wi.status IN ['draft', 'scheduled', 'in_progress', 'on_hold']
RETURN wi.description, wi.status,
       wi.labour_hours * wi.labour_rate + coalesce(wi.materials_allowance, 0) AS estimated_cost
ORDER BY wi.status
```

### CQ-036: Is this job on budget?
```cypher
// Estimated cost: computed from WorkItem properties + USES_ITEM relationships
MATCH (p:Project {id: $projectId})-[:HAS_WORK_ITEM|HAS_WORK_PACKAGE*1..2]->(wi:WorkItem)
OPTIONAL MATCH (wi)-[ui:USES_ITEM]->()
WITH wi, sum(ui.quantity * ui.unit_cost) AS item_costs
WITH
  sum(wi.labour_hours * wi.labour_rate + coalesce(wi.materials_allowance, 0) + item_costs) AS estimated,
  // Actual cost: sum of time entries + actual item costs
  // (requires separate MATCH for TimeEntry aggregation — simplified here)
  0 AS actual  // placeholder — full query joins TimeEntry data
RETURN estimated, actual, estimated - actual AS variance
```

### CQ-055: What regulations apply to this activity in this jurisdiction?
```cypher
MATCH (a:Activity {id: $activityId})
      -[:REGULATED_BY]->(reg:Regulation)
WHERE reg.jurisdiction_code = $jurisdictionCode
  AND reg.valid_until > date()
RETURN reg.reference, reg.title, reg.source
```

### CQ-062: Semantic search over past conversations
```cypher
CALL db.index.vector.queryNodes('message_embeddings', 5, $queryEmbedding)
YIELD node AS msg, score
WHERE score > 0.75
MATCH (msg)-[:PART_OF]->(conv:Conversation)-[:ABOUT_PROJECT]->(p:Project)
MATCH (msg)-[:REFERENCES]->(entity)
RETURN msg.content, conv.title, collect(entity) AS discussed, score
ORDER BY score DESC
```

### CQ-074: What can this user see? (permission check)
```cypher
// Check: can Member X reach Project Y?
MATCH (m:Member {id: $memberId})-[:HAS_MEMBER]-(c:Company)-[:OWNS_PROJECT]->(p:Project {id: $projectId})
RETURN p, m.access_role
// If no result: no access. If result: check access_role depth in service layer.
```
