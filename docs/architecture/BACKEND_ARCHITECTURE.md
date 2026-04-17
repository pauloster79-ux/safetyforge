# Kerf Backend Architecture

*Version 2.0 -- 2026-04-10 (Neo4j migration)*

This document is the definitive backend blueprint for Kerf. Engineers build from this. Every schema, endpoint, and service is specified to the level of detail needed to write code.

---

## 1. DATA MODEL (Neo4j Graph Database)

### 1.1 Graph Structure Overview

The data model is a Neo4j property graph defined in `backend/graph/schema.cypher`. The schema is idempotent (safe to re-run) and uses `CREATE CONSTRAINT IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` throughout.

The graph is organised into 9+ domains:

```
Domain 1: Regulatory    (shared across all tenants)
Domain 2: Organisational (Company, Member, Project)
Domain 3: Human Resources (Worker, Certification)
Domain 4: Equipment      (Equipment, EquipmentInspectionLog)
Domain 5: Safety         (Inspection, Incident, HazardReport, ToolboxTalk, CorrectiveAction, etc.)
Domain 6: Spatial        (Location, SafetyZone)
Domain 7: Documents      (Document, OshaLogEntry, EnvironmentalProgram)
Domain 8: Daily Operations (DailyLog, MaterialDelivery, VoiceSession, etc.)
Domain 9: Sub Management (GcRelationship, InsuranceCertificate, PrequalPackage, LienWaiver)
Agentic:  Agent Identity + Agent Outputs (AgentIdentity, ComplianceAlert, BriefingSummary)
```

### 1.2 Tenant Isolation (Graph-Native)

Tenant isolation is structural, not filter-based. All tenant-scoped data connects to the graph through Company:

```
(:Company)-[:OWNS_PROJECT]->(:Project)
(:Company)-[:EMPLOYS]->(:Worker)
(:Company)-[:HAS_EQUIPMENT]->(:Equipment)
(:Company)-[:HAS_MEMBER]->(:Member)
```

If there is no traversal path from a Company to a piece of data, that data is invisible to that tenant. No `WHERE company_id = $id` filter needed -- the graph structure enforces isolation.

Regulatory nodes (Jurisdiction, Regulation, CertificationType, etc.) are shared across all tenants and are not connected to any Company node.

### 1.3 Node Identity and ID Format

Every node has a unique `.id` property (or equivalent like `.code`, `.reference`, `.agent_id`) enforced by Neo4j uniqueness constraints.

ID format: `{prefix}_{secrets.token_hex(8)}`

| Entity | Prefix | Example |
|--------|--------|---------|
| Company | `comp` | `comp_a1b2c3d4e5f6g7h8` |
| Project | `proj` | `proj_b2c3d4e5f6g7h8i9` |
| Worker | `wkr` | `wkr_c3d4e5f6g7h8i9j0` |
| Inspection | `insp` | `insp_f6g7h8i9j0k1l2m3` |
| Incident | `inc` | `inc_i9j0k1l2m3n4o5p6` |
| Document | `doc` | `doc_e5f6g7h8i9j0k1l2` |
| Equipment | `eq` | `eq_k1l2m3n4o5p6q7r8` |
| Agent | `agt` | `agt_x1y2z3a4b5c6d7e8` |
| ToolboxTalk | `talk` | `talk_g7h8i9j0k1l2m3n4` |
| HazardReport | `haz` | `haz_h8i9j0k1l2m3n4o5` |
| CorrectiveAction | `ca` | `ca_001` |
| Member | `mem` | `mem_p6q7r8s9t0u1v2w3` |

### 1.4 Key Relationship Types

```cypher
// Organisational
(:Company)-[:OWNS_PROJECT]->(:Project)
(:Company)-[:HAS_MEMBER]->(:Member)
(:Company)-[:EMPLOYS]->(:Worker)
(:Company)-[:HAS_EQUIPMENT]->(:Equipment)
(:Worker)-[:ASSIGNED_TO]->(:Project)
(:Member)-[:MANAGES]->(:Project)

// Safety
(:Project)-[:HAS_INSPECTION]->(:Inspection)
(:Inspection)-[:HAS_ITEM]->(:InspectionItem)
(:Project)-[:HAS_INCIDENT]->(:Incident)
(:Project)-[:HAS_HAZARD_REPORT]->(:HazardReport)
(:Project)-[:HAS_TOOLBOX_TALK]->(:ToolboxTalk)
(:ToolboxTalk)-[:ATTENDED_BY]->(:Worker)
(:Worker)-[:HOLDS]->(:Certification)
(:Certification)-[:OF_TYPE]->(:CertificationType)

// Equipment
(:Equipment)-[:HAS_INSPECTION_LOG]->(:EquipmentInspectionLog)
(:Equipment)-[:ASSIGNED_TO]->(:Project)

// Documents
(:Project)-[:HAS_DOCUMENT]->(:Document)
(:Company)-[:HAS_OSHA_LOG]->(:OshaLogEntry)

// Regulatory (shared)
(:Jurisdiction)-[:HAS_REGION]->(:Region)
(:Jurisdiction)-[:HAS_GROUP]->(:RegulatoryGroup)
(:RegulatoryGroup)-[:CONTAINS]->(:Regulation)
(:Regulation)-[:REQUIRES_PROGRAM]->(:ComplianceProgram)
(:Activity)-[:REGULATED_BY]->(:Regulation)
(:Regulation)-[:REQUIRES_CERT]->(:CertificationType)

// Spatial
(:Project)-[:HAS_LOCATION]->(:Location)
(:Project)-[:HAS_SAFETY_ZONE]->(:SafetyZone)

// Sub Management
(:Company)-[:GC_OVER]->(:Company)
(:Company)-[:HAS_INSURANCE]->(:InsuranceCertificate)
(:Company)-[:HAS_PREQUAL]->(:PrequalPackage)

// Agentic
(:AgentIdentity)-[:BELONGS_TO]->(:Company)
(:AgentIdentity)-[:GENERATED]->(:ComplianceAlert)
(:AgentIdentity)-[:GENERATED]->(:BriefingSummary)

// Daily Operations
(:Project)-[:HAS_DAILY_LOG]->(:DailyLog)
(:DailyLog)-[:HAS_DELIVERY]->(:MaterialDelivery)
(:DailyLog)-[:HAS_DELAY]->(:DelayRecord)
(:DailyLog)-[:HAS_VISITOR]->(:VisitorRecord)
```

### 1.5 Constraints and Indexes

All constraints and indexes are defined in `backend/graph/schema.cypher`. Key patterns:

- **Uniqueness constraints** on every node's identity property (e.g., `Company.id`, `Regulation.reference`, `AgentIdentity.agent_id`)
- **NOT NULL constraints** on identity properties
- **Composite indexes** on frequently queried properties (e.g., `Worker.status`, `Inspection.inspection_date`, `Incident.severity`)
- **Jurisdiction indexes** on regulatory nodes for jurisdiction-scoped queries

Example constraints:

```cypher
CREATE CONSTRAINT constraint_company_id IF NOT EXISTS
  FOR (n:Company) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_company_id_exists IF NOT EXISTS
  FOR (n:Company) REQUIRE n.id IS NOT NULL;
CREATE INDEX index_company_jurisdiction IF NOT EXISTS
  FOR (n:Company) ON (n.jurisdiction_code);
```

### 1.6 Provenance Fields

Every mutable node carries provenance fields set by `BaseService._provenance_create()` and `BaseService._provenance_update()`:

| Field | Type | Description |
|-------|------|-------------|
| `created_by` | string | Actor ID (user ID or agent ID) |
| `actor_type` | string | `"human"` or `"agent"` |
| `agent_id` | string or null | Agent ID if actor is agent |
| `model_id` | string or null | LLM model used (for agent actions) |
| `confidence` | float or null | Agent confidence (for interpretive actions) |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `updated_by` | string | Last updater's actor ID |
| `updated_actor_type` | string | Last updater's type |
| `updated_at` | string (ISO 8601) | Last update timestamp |

### 1.7 Agent Identity Nodes

Agents are first-class graph citizens with cost control fields. Permission = traversability.

```cypher
(:AgentIdentity {
  agent_id: "agt_x1y2z3a4b5c6d7e8",
  name: "Compliance Checker",
  agent_type: "compliance",
  status: "active",
  scopes: '["read:safety", "write:inspections"]',   // JSON string
  daily_budget_cents: 10000,
  daily_spend_cents: 0
})-[:BELONGS_TO]->(:Company {id: "comp_..."})
```

If there is no `BELONGS_TO` path from agent to company, the agent cannot access that company's data.

---

## 2. API DESIGN

All endpoints are prefixed with `/api/v1`. Authentication is required on all endpoints except `/health`, `/api/v1/auth/signup`, and `/api/v1/billing/webhook`.

### 2.1 Auth Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/signup` | Register a new user (creates Clerk user + company) | None |
| GET | `/auth/me` | Get current user profile and company association | Bearer |
| POST | `/auth/refresh` | Validate and refresh session | Bearer |

### 2.2 Company Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/companies` | Create company |
| GET | `/companies/{cid}` | Get company |
| PATCH | `/companies/{cid}` | Update company |
| DELETE | `/companies/{cid}` | Soft-delete company |
| GET | `/companies/{cid}/settings` | Get company settings |
| PATCH | `/companies/{cid}/settings` | Update settings |

### 2.3 Project Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects` | Create project |
| GET | `/me/projects` | List projects (with status filter) |
| GET | `/me/projects/{pid}` | Get project |
| PATCH | `/me/projects/{pid}` | Update project |
| DELETE | `/me/projects/{pid}` | Soft-delete project |
| POST | `/me/projects/{pid}/workers` | Assign workers |
| DELETE | `/me/projects/{pid}/workers/{wid}` | Remove worker |

### 2.4 Document Generation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/documents/generate` | Generate safety document |
| GET | `/me/projects/{pid}/documents` | List documents |
| GET | `/me/projects/{pid}/documents/{did}` | Get document |
| PATCH | `/me/projects/{pid}/documents/{did}` | Update document |
| POST | `/me/projects/{pid}/documents/{did}/review` | Mark reviewed |

### 2.5 Inspections

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/inspections` | Create inspection |
| GET | `/me/projects/{pid}/inspections` | List inspections |
| GET | `/me/projects/{pid}/inspections/{iid}` | Get inspection |
| POST | `/me/projects/{pid}/inspections/{iid}/items` | Add checklist item |
| POST | `/me/projects/{pid}/inspections/{iid}/complete` | Complete inspection |
| GET | `/me/projects/{pid}/inspections/checklist-template` | Get checklist template |

### 2.6 Toolbox Talks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/toolbox-talks` | Create talk |
| POST | `/me/projects/{pid}/toolbox-talks/generate` | AI-generate talk |
| GET | `/me/projects/{pid}/toolbox-talks` | List talks |
| GET | `/me/projects/{pid}/toolbox-talks/{tid}` | Get talk |
| POST | `/me/projects/{pid}/toolbox-talks/{tid}/attendance` | Record attendance |
| POST | `/me/projects/{pid}/toolbox-talks/{tid}/complete` | Complete talk |
| GET | `/me/projects/{pid}/toolbox-talks/suggest-topic` | Suggest topic |

### 2.7 Hazard Reporting

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/hazard-reports` | Create report |
| GET | `/me/projects/{pid}/hazard-reports` | List reports |
| GET | `/me/projects/{pid}/hazard-reports/{rid}` | Get report |
| POST | `/me/projects/{pid}/hazard-reports/{rid}/photos` | Add photo |
| POST | `/me/projects/{pid}/hazard-reports/{rid}/voice` | Add voice note |
| POST | `/me/projects/{pid}/hazard-reports/{rid}/resolve` | Resolve |

### 2.8 Incident Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/incidents` | Create incident |
| GET | `/me/projects/{pid}/incidents` | List incidents |
| GET | `/me/projects/{pid}/incidents/{iid}` | Get incident |
| POST | `/me/projects/{pid}/incidents/{iid}/investigate` | Start investigation |
| PATCH | `/me/projects/{pid}/incidents/{iid}/investigation` | Update investigation |
| POST | `/me/projects/{pid}/incidents/{iid}/osha-forms` | Generate OSHA forms |
| GET | `/me/osha-300-log` | Get OSHA 300 log |

### 2.9 Worker/Certification Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/workers` | Create worker |
| GET | `/me/workers` | List workers |
| GET | `/me/workers/{wid}` | Get worker |
| PATCH | `/me/workers/{wid}` | Update worker |
| POST | `/me/workers/{wid}/certifications` | Add certification |
| GET | `/me/workers/training-matrix` | Training matrix |
| GET | `/me/workers/expiring-certs` | Expiring certifications |

### 2.10 Equipment Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/equipment` | Create equipment |
| GET | `/me/equipment` | List equipment |
| GET | `/me/equipment/{eid}` | Get equipment |
| PATCH | `/me/equipment/{eid}` | Update equipment |
| POST | `/me/equipment/{eid}/inspections` | Log inspection |

### 2.11 Mock OSHA Inspection

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/mock-inspections` | Start mock inspection (async) |
| GET | `/me/mock-inspections/{mid}` | Get status |
| GET | `/me/mock-inspections/{mid}/results` | Get results |

### 2.12 Morning Safety Brief

| Method | Path | Description |
|--------|------|-------------|
| POST | `/me/projects/{pid}/morning-brief` | Generate brief |
| GET | `/me/projects/{pid}/morning-brief/today` | Get today's brief |

### 2.13 Analytics/Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/me/dashboard` | Dashboard summary |
| GET | `/me/analytics/compliance-trend` | Compliance trend |
| GET | `/me/analytics/incident-rate` | Incident rate |

### 2.14 Agent Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents` | Register agent |
| GET | `/agents/{aid}` | Get agent |
| PATCH | `/agents/{aid}` | Update agent |
| POST | `/agents/{aid}/suspend` | Suspend agent |
| GET | `/agents/{aid}/spend` | Get spend report |

---

## 3. SERVICE ARCHITECTURE

### 3.1 BaseService Pattern

All domain services extend `BaseService` (defined in `backend/app/services/base_service.py`), which provides:

```python
class BaseService:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def _generate_id(self, prefix: str) -> str:
        """Generate '{prefix}_{secrets.token_hex(8)}'."""

    def _provenance_create(self, actor: Actor) -> dict[str, Any]:
        """Provenance fields for new entities (created_by, actor_type, etc.)."""

    def _provenance_update(self, actor: Actor) -> dict[str, Any]:
        """Provenance fields for updates (updated_by, updated_at, etc.)."""

    def _session(self, **kwargs) -> Session:
        """Open a Neo4j session."""

    def _read_tx(self, query: str, parameters: dict | None = None) -> list[dict]:
        """Execute a read query in a managed transaction."""

    def _write_tx(self, query: str, parameters: dict | None = None) -> list[dict]:
        """Execute a write query in a managed transaction."""

    def _read_tx_single(self, query: str, parameters: dict | None = None) -> dict | None:
        """Execute a read query, return single result or None."""

    def _write_tx_single(self, query: str, parameters: dict | None = None) -> dict | None:
        """Execute a write query, return single result or None."""
```

Services use Cypher queries within these transaction helpers:

```python
class CompanyService(BaseService):
    def create(self, data: CompanyCreate, user_id: str) -> Company:
        actor = Actor.human(user_id)
        company_id = self._generate_id("comp")
        props = {
            "id": company_id,
            "name": data.name,
            ...
            **self._provenance_create(actor),
        }
        result = self._write_tx_single(
            "CREATE (c:Company $props) RETURN c {.*} AS company",
            {"props": props},
        )
        return Company(**result["company"])
```

### 3.2 Service Inventory

```
app/services/
  base_service.py              -- BaseService with Neo4j driver, tx helpers, ID generation
  company_service.py           -- Company CRUD
  project_service.py           -- Project CRUD, compliance scoring
  member_service.py            -- Member CRUD, role management
  invitation_service.py        -- Invitation workflow
  project_assignment_service.py -- Worker-project assignment edges
  worker_service.py            -- Worker CRUD, cert tracking, training matrix
  equipment_service.py         -- Equipment CRUD, inspection logs
  inspection_service.py        -- Inspection CRUD, checklist management
  inspection_template_service.py -- Checklist template management
  incident_service.py          -- Incident CRUD, investigation workflow, OSHA forms
  hazard_report_service.py     -- Hazard report CRUD, photo management
  toolbox_talk_service.py      -- Talk CRUD, attendance, training record creation
  osha_log_service.py          -- OSHA 300/301 log management
  document_service.py          -- Document CRUD, versioning
  environmental_service.py     -- Environmental program management
  morning_brief_service.py     -- Brief assembly from multiple data sources
  mock_inspection_service.py   -- Mock inspection orchestration and scoring
  gc_portal_service.py         -- GC portal and sub management
  prequalification_service.py  -- Sub prequalification automation
  analytics_service.py         -- Dashboard and analytics aggregation
  generation_service.py        -- AI document generation (Claude)
  hazard_analysis_service.py   -- Claude Vision hazard analysis
  voice_service.py             -- Whisper transcription + structuring
  state_compliance_service.py  -- State-specific compliance engine
  template_service.py          -- Template management
  pdf_service.py               -- PDF generation (WeasyPrint)
  billing_service.py           -- Subscription management (Lemon Squeezy)
  auth_service.py              -- Authentication (Clerk)
  agent_identity_service.py    -- Agent CRUD, budget management
  agent_orchestrator.py        -- Agent task coordination
  compliance_agent.py          -- Compliance checking agent
  briefing_agent.py            -- Morning brief generation agent
  llm_service.py               -- LLM call wrapper with cost tracking
  guardrails_service.py        -- Agent guardrails and action classification
  event_bus.py                 -- In-process event backbone
  mcp_tools.py                 -- MCP server tool definitions
```

### 3.3 Service Dependency Graph

```
                            +------------------+
                            |  FastAPI Routers  |
                            +--------+---------+
                                     |
            +------------------------+------------------------+
            |                        |                        |
     +------v------+         +------v------+         +------v------+
     |  Company     |         |  Project     |         |  Billing    |
     |  Service     |         |  Service     |         |  Service    |
     +------+------+         +------+------+         +-------------+
            |                        |
   +--------+----------+------------+----------+-----------+
   |        |          |            |           |           |
+--v--+  +--v--+  +---v---+  +----v----+  +---v---+  +---v---+
|Doc  |  |Insp |  |Toolbox|  |Hazard   |  |Inci-  |  |Worker |
|Svc  |  |Svc  |  |Talk   |  |Report   |  |dent   |  |Svc    |
+--+--+  +--+--+  |Svc    |  |Svc      |  |Svc    |  +---+---+
   |        |     +---+---+  +----+----+  +---+---+      |
   |        |         |           |            |          |
   |     +--+---------|-----------|------------|--+       |
   |     |       Neo4j Driver (shared)         |  |       |
   |     |  +----------+  +-------------+      |  |       |
   +-----|  |Generation|  |Hazard       |      |  |       |
   |     |  |Service   |  |Analysis Svc |      |  +-------+
   |     |  +----------+  +-------------+      |
   |     |  +----------+  +-------------+      |
   |     |  |Voice     |  |Event Bus    |      |
   |     |  |Service   |  |(in-process) |      |
   |     |  +----------+  +-------------+      |
   |     +-------------------------------------+
   |
+--v----------+     +----------------+     +-----------+
| PDF Service |     |Mock Inspection |     |Morning    |
|             |     |Service         |     |Brief Svc  |
+-------------+     +----------------+     +-----------+
```

**Key dependency rules:**
- Domain services depend on the Neo4j driver (via BaseService) and shared infrastructure services.
- Mock Inspection Service reads from ALL domain services.
- Morning Brief Service reads from: project, worker, certification, inspection, hazard report, incident, weather, and toolbox talk services.
- No circular dependencies. Services never depend on routers.

### 3.4 Pydantic Model Pattern

Every entity follows the Create/Update/Read pattern:

```python
from pydantic import BaseModel, Field, field_validator

class CompanyCreate(BaseModel):
    """Input model -- no ID, no audit fields."""
    name: str = Field(..., min_length=2, max_length=128)
    address: str | None = None
    trade_type: TradeType = TradeType.GENERAL

class CompanyUpdate(BaseModel):
    """Partial update model -- all fields optional."""
    name: str | None = None
    address: str | None = None

class Company(BaseModel):
    """Full model with ID and audit fields."""
    id: str
    name: str
    address: str | None = None
    trade_type: str
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str
```

### 3.5 FastAPI Router Pattern

Routers use `Depends()` injection for services and auth:

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_company_service, get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("", response_model=Company, status_code=201)
def create_company(
    data: CompanyCreate,
    user: dict = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service),
) -> Company:
    return service.create(data, user["uid"])
```

The `get_neo4j_driver()` dependency provides the shared Neo4j `Driver` instance. Each service factory (e.g., `get_company_service`) injects the driver via `Depends(get_neo4j_driver)`.

### 3.6 The AI Generation Pipeline

```
GenerationService
  +-- PromptRegistry           (loads versioned prompts from files)
  +-- DocumentGenerator        (generates safety documents)
  +-- ToolboxTalkGenerator     (generates talks with bilingual support)
  +-- InspectionChecklistGen   (generates trade/project-specific checklists)
  +-- IncidentReportGenerator  (structures voice/text into formal report)
  +-- MockInspectionGenerator  (analyzes data, produces findings)
  +-- MorningBriefGenerator    (assembles risk factors into brief)
  +-- OshaFormGenerator        (generates 300/301 form content)
```

Each generator:
1. Loads the prompt template from `PromptRegistry`
2. Assembles context from relevant services (via Neo4j graph queries)
3. Calls Claude API with appropriate model and parameters
4. Validates the response against a JSON schema
5. Logs the generation metadata (model, prompt version, token usage, latency)

### 3.7 The Mock Inspection Engine

The mock inspection is the most complex AI operation. It:

1. **Gathers data** via graph traversals from all domain nodes connected to the target scope (project or company)
2. **Checks against regulatory standards** by traversing `(:Activity)-[:REGULATED_BY]->(:Regulation)-[:REQUIRES_CERT]->(:CertificationType)` paths
3. **Generates findings** via Claude in OSHA citation style
4. **Scores the inspection** with weighted category scoring
5. **Stores results** as graph nodes and triggers notification

### 3.8 The Morning Brief Engine

Assembles data from multiple graph traversals:
- Weather forecast for project coordinates
- Expiring certifications (workers assigned to project)
- Yesterday's inspection findings and open corrective actions
- Recent hazard reports and incidents
- Today's scheduled toolbox talk
- Project risk score

---

## 4. EVENT BACKBONE

### 4.1 EventType Enum

Defined in `backend/app/models/events.py`:

```python
class EventType(str, Enum):
    INSPECTION_COMPLETED = "inspection.completed"
    INSPECTION_ITEM_FAILED = "inspection.item_failed"
    INCIDENT_REPORTED = "incident.reported"
    HAZARD_REPORTED = "hazard.reported"
    CERTIFICATION_EXPIRING = "certification.expiring"
    EQUIPMENT_INSPECTION_DUE = "equipment.inspection_due"
    WORKER_ASSIGNED = "worker.assigned_to_project"
    WORKER_REMOVED = "worker.removed_from_project"
    CORRECTIVE_ACTION_OVERDUE = "corrective_action.overdue"
    DOCUMENT_GENERATED = "document.generated"
```

### 4.2 Event Envelope

```python
class Event(BaseModel):
    event_id: str
    event_type: EventType
    version: str = "1.0"
    entity_id: str
    entity_type: str
    project_id: str | None = None
    company_id: str
    actor: EventActor           # type + id + agent_id
    timestamp: str              # ISO 8601
    summary: dict[str, Any]     # rich payload for consumer filtering
    graph_context: dict[str, Any]  # pre-computed graph neighbourhood
```

### 4.3 EventBus

Defined in `backend/app/services/event_bus.py`. In-process implementation with:
- **IdempotencyStore**: In-memory (swappable for Redis) with TTL-based expiry
- **Subscription filters**: Handlers subscribe to specific EventTypes
- **Dead-letter handling**: Failed events after 3 retries go to dead-letter queue
- **Actor tracking**: Prevents agent-to-event-to-agent infinite loops

Production swap: Replace in-process EventBus with Pub/Sub, IdempotencyStore with Redis.

---

## 5. AGENTIC INFRASTRUCTURE

### 5.1 Agent Identity Service

`AgentIdentityService` manages agent lifecycle:
- **register()**: Creates AgentIdentity node + BELONGS_TO edge to Company
- **get() / list()**: Query agent nodes
- **update()**: Update agent configuration
- **suspend()**: Set status to "suspended"
- **record_spend()**: Increment daily spend counter
- **check_budget()**: Raise `AgentBudgetExceededError` if daily budget exceeded

### 5.2 Graph-Native Permissions

Permission is traversability. An agent can only access data reachable via graph traversal from its Company:

```cypher
MATCH (a:AgentIdentity {agent_id: $agent_id})
      -[:BELONGS_TO]->(c:Company)
      -[:OWNS_PROJECT]->(p:Project)
      <-[:HAS_INSPECTION]-(i:Inspection {id: $inspection_id})
RETURN i
// No path = no result = permission denied
```

### 5.3 MCP Tools

Defined in `backend/app/services/mcp_tools.py`. Intent-based tools:
- `check_compliance(project_id, worker_id)` -- traverses regulation graph
- `get_regulations(activity_type)` -- queries regulatory domain
- `generate_report(project_id, report_type)` -- orchestrates generation

### 5.4 Guardrails

Defined in `backend/app/services/guardrails_service.py`. Action classification:

| Category | Description | Agent behaviour |
|----------|-------------|-----------------|
| Read-only | Queries, lookups | Always allow |
| Low-risk write | Creating records | Allow with audit trail |
| High-risk write | Deleting, overriding safety flags | Require human approval |

---

## 6. FILE STORAGE

### 6.1 Cloud Storage Buckets

| Bucket | Contents | Access |
|--------|----------|--------|
| `kerf-documents` | Generated PDFs | Company members via signed URLs |
| `kerf-photos` | Hazard/inspection photos | Company members via signed URLs |
| `kerf-audio` | Voice recordings | Company members via signed URLs |
| `kerf-signatures` | Attendance signatures | Company members via signed URLs |

### 6.2 Naming Conventions

```
{bucket}/{company_id}/{entity_type}_{entity_id}/{filename}
```

Example: `kerf-photos/comp_a1b2c3d4e5f6g7h8/insp_f6g7h8i9j0k1l2m3/chk_002_001.jpg`

### 6.3 Upload Limits

| Type | Max Size | Formats |
|------|----------|---------|
| Photos | 10 MB | JPEG, PNG, HEIC, WebP |
| Voice | 25 MB | WebM, M4A, WAV, MP3 |
| Documents | 50 MB | PDF |
| Signatures | 2 MB | PNG |

---

## 7. SECURITY

### 7.1 Auth Architecture

```
Client (React SPA)
  -> Clerk Auth (signup, login, token refresh)
    -> Clerk Session Token (JWT)
      -> API request with Authorization: Bearer <token>
        -> Backend: verify token via Clerk SDK
          -> Extract uid, email
          -> Check company membership via graph traversal:
             MATCH (m:Member {uid: $uid})-[:BELONGS_TO]->(c:Company {id: $cid})
          -> Proceed or 401/403
```

### 7.2 Company-Level Data Isolation (Multi-Tenancy)

- All data access goes through graph traversals originating from the authenticated user's Company node.
- The graph structure enforces isolation: no `(:Company {id: "A"})` node has any edge to data owned by `(:Company {id: "B"})`.
- Cloud Storage paths are prefixed with `company_id`.
- No cross-company queries are possible from the API layer.

### 7.3 API Rate Limiting

| Scope | Limit | Window |
|-------|-------|--------|
| Per user (auth token) | 100 requests | 1 minute |
| Per user AI generation | 10 requests | 1 minute |
| Per user file upload | 20 requests | 1 minute |
| Per IP (unauthenticated) | 20 requests | 1 minute |

### 7.4 Audit Logging

Every write operation records provenance directly on the graph node (via `_provenance_create` / `_provenance_update`). The actor type (human vs agent), actor ID, and timestamp are stored on the node itself.

For detailed audit trails, the EventBus emits events for all significant mutations, providing a time-ordered log of all changes with actor attribution.

---

## 8. SCALABILITY

### 8.1 Neo4j Scaling Considerations

**Hot spot prevention:**
- Node IDs use `{prefix}_{random_hex}` pattern, distributing writes evenly across the B-tree.
- Avoid monotonically increasing IDs (no auto-increment, no timestamp-prefix IDs).

**Index strategy:**
- Uniqueness constraints on identity properties provide implicit indexes.
- Composite indexes on frequently filtered properties (status, date fields).
- All indexes defined in `schema.cypher` and applied via CI.

**Query patterns:**
- All list queries are paginated (SKIP/LIMIT).
- Use parameterised Cypher queries (never string interpolation).
- Read queries use `session.execute_read()`, write queries use `session.execute_write()` for correct routing in a cluster.

**Estimated node counts at scale:**

| Node Label | Per Company (avg) | At 1,000 Customers | At 10,000 Customers |
|------------|-------------------|--------------------|--------------------|
| Company | 1 | 1,000 | 10,000 |
| Project | 5 | 5,000 | 50,000 |
| Document | 50 | 50,000 | 500,000 |
| Inspection | 500/year | 500,000 | 5,000,000 |
| ToolboxTalk | 250/year | 250,000 | 2,500,000 |
| HazardReport | 50/year | 50,000 | 500,000 |
| Incident | 5/year | 5,000 | 50,000 |
| Worker | 30 | 30,000 | 300,000 |
| Certification | 120 | 120,000 | 1,200,000 |

### 8.2 LLM API Rate Limits and Queuing

- Cloud Tasks queues enforce rate limits per queue.
- The `ai-generation` queue limits to 20 requests/minute, under API limits.
- Exponential backoff on 429 responses (built into the Anthropic SDK).

---

*This document is the source of truth for backend architecture decisions. All implementation work must trace to the schemas, endpoints, and service signatures defined here. If something needs to change, update this document first, then implement.*
