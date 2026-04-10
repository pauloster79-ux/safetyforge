# Handoff: Phase 0 Complete → Phase 1 Batch 1A

**Date:** 2026-04-09
**From:** Phase 0 (Foundation) session
**To:** Phase 1 (Tier 1 Service Rewrites) session(s)

---

## What Phase 0 Delivered

### 0A. Schema trimmed — `backend/graph/schema.cypher`
- Removed Domains 10-15 (66 constraints gone)
- Kept Domains 1-9 + Spatial + Documents
- Added 4 AgentIdentity constraints (P0 agentic infra)
- Result: 147 constraints/indexes (down from 213)

### 0B. Neo4j test fixtures — `backend/tests/conftest.py`
- Session-scoped `neo4j_driver` fixture (creates once, shared across tests)
- Auto-applies `schema.cypher` on session start
- Per-test cleanup: `MATCH (n) DETACH DELETE n`
- `test_company` creates Company node with full provenance
- `test_project` creates Project node linked to Company via `[:OWNS_PROJECT]`
- `client` fixture overrides `get_neo4j_driver` (not Firestore)
- Test settings via `TEST_SETTINGS` with Neo4j env var support

### 0C. Service base — `backend/app/services/base_service.py`
- Constructor: `__init__(self, driver: Driver)`
- `_generate_id(prefix)` → `{prefix}_{secrets.token_hex(8)}`
- `_provenance_create(actor)` → 9 fields: created_by, actor_type, agent_id, model_id, confidence, created_at, updated_by, updated_actor_type, updated_at
- `_provenance_update(actor)` → 3 fields: updated_by, updated_actor_type, updated_at
- `_read_tx(query, params)` → list[dict]
- `_write_tx(query, params)` → list[dict]
- `_read_tx_single(query, params)` → dict | None
- `_write_tx_single(query, params)` → dict | None
- `_session(**kwargs)` → Session

### 0D. Actor model — `backend/app/models/actor.py`
- Frozen dataclass: `Actor(id, type, agent_id, company_id, scopes)`
- `Actor.human(uid, company_id=None)` — factory for human actors
- `Actor.agent(agent_id, company_id=None, scopes=())` — factory for agent actors

### 0E. Seed script — `backend/scripts/seed_regulatory_graph.py`
- Reads 4 jurisdiction YAMLs (US, UK, CA, AU)
- Creates: Jurisdiction, Region, RegulatoryGroup, Regulation, CertificationType, ComplianceProgram, DocumentType
- MERGE-based idempotency, `source` property on every node
- CLI: `python -m scripts.seed_regulatory_graph --uri bolt://localhost:7687`

---

## Phase 1 Plan: Tier 1 Service Rewrites

### Rewrite pattern (apply to every service)

```
1. Constructor: db: firestore.Client → extends BaseService (driver: Driver)
2. Collection access:
   self.db.collection("companies").document(cid).collection("entities")
   → MATCH (c:Company {id: $cid})-[:HAS_ENTITY]->(e:Entity) RETURN e
3. Create: doc_ref.set(data) → CREATE (e:Entity $props) + MERGE relationship to Company/Project
4. Update: doc_ref.update(data) → MATCH (e:Entity {id: $id}) SET e += $props
5. Delete: doc_ref.delete() → MATCH (e:Entity {id: $id}) DETACH DELETE e
6. List: collection.stream() → MATCH traversal with ORDER BY + LIMIT
7. Every create/update includes provenance via _provenance_create/_provenance_update
8. Actor comes from the user dict (Actor.human(user_id)) — routers create the Actor
```

### Graph relationships per service (from ontology)

| Service | Primary node | Relationship to Company/Project |
|---------|-------------|-------------------------------|
| company_service | Company | IS the root node |
| project_service | Project | (Company)-[:OWNS_PROJECT]->(Project) |
| member_service | Member | (Member)-[:MEMBER_OF]->(Company) |
| invitation_service | Invitation | (Invitation)-[:FOR_COMPANY]->(Company) |
| project_assignment_service | — | Creates (Worker)-[:ASSIGNED_TO]->(Project) edges |
| worker_service | Worker | (Company)-[:EMPLOYS]->(Worker) |
| equipment_service | Equipment | (Company)-[:OWNS_EQUIPMENT]->(Equipment) |
| inspection_service | Inspection | (Project)-[:HAS_INSPECTION]->(Inspection), items as (Inspection)-[:HAS_ITEM]->(InspectionItem) |
| incident_service | Incident | (Project)-[:HAS_INCIDENT]->(Incident) |
| hazard_report_service | HazardReport | (Project)-[:HAS_HAZARD_REPORT]->(HazardReport) |
| toolbox_talk_service | ToolboxTalk | (Project)-[:HAS_TOOLBOX_TALK]->(ToolboxTalk) |
| osha_log_service | OshaLogEntry | (Company)-[:HAS_OSHA_LOG]->(OshaLogEntry) |
| environmental_service | EnvironmentalProgram | (Company)-[:HAS_ENV_PROGRAM]->(EnvironmentalProgram) |
| document_service | Document | (Company)-[:HAS_DOCUMENT]->(Document) |

### Batch order

- **1A: Organisational** — company, project, member, invitation, project_assignment (5 services)
- **1B: HR + Equipment** — worker, equipment (2 services, but largest by LOC)
- **1C: Safety** — inspection, incident, hazard_report, toolbox_talk (4 services)
- **1D: Regulatory + Documents** — osha_log, environmental, document (3 services)

Each batch includes rewriting the corresponding `test_api_*.py` file.

### Dependencies wiring (already done in `dependencies.py`)

All Tier 1 service providers already pass `driver: Driver`. Example:
```python
def get_company_service(driver: Annotated[Driver, Depends(get_neo4j_driver)]) -> CompanyService:
    return CompanyService(driver)
```

### Key reference files

| File | Purpose |
|------|---------|
| `backend/app/services/base_service.py` | BaseService class all services extend |
| `backend/app/models/actor.py` | Actor model for provenance |
| `backend/app/dependencies.py` | DI wiring (already Neo4j) |
| `backend/app/services/neo4j_client.py` | Low-level driver helpers (BaseService wraps these) |
| `backend/tests/conftest.py` | Neo4j test fixtures |
| `backend/graph/schema.cypher` | Constraints/indexes |
| `docs/architecture/CONSTRUCTION_ONTOLOGY.md` | Full ontology reference |

### Important notes

- **Demo mode:** Services must still work when Neo4j is not configured. Check `dependencies.py` for how this is handled.
- **No FK properties:** All references are relationships, never `_id` properties on nodes (Design Principle #8)
- **No company_id on nodes:** Tenant isolation via graph edges, not properties (Design Principle #6)
- **Provenance on every mutation:** Use `_provenance_create(actor)` and `_provenance_update(actor)`
- **Test fixtures:** `test_company` returns a dict (not a Pydantic model) with `id='comp_test_000001'`
- **Test project:** `test_project` returns a dict with `id='proj_test_000001'`, linked to test_company via `[:OWNS_PROJECT]`

### Start here for Batch 1A

1. Read `backend/app/services/company_service.py` — this is the template for all others
2. Read `backend/tests/test_api_companies.py` — understand test patterns
3. Rewrite company_service extending BaseService
4. Rewrite test_api_companies using Neo4j fixtures
5. Repeat for project, member, invitation, project_assignment
