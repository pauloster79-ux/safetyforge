# Handoff: Batch 1A Complete → Batch 1B (or Test Verification)

**Date:** 2026-04-09
**From:** Batch 1A (Organisational services rewrite) session
**To:** Next session (test verification once Neo4j running, or Batch 1B)

---

## What Batch 1A Delivered

### 5 Services Rewritten (Firestore → Neo4j, extending BaseService)

| Service | File | Key Pattern |
|---------|------|-------------|
| **CompanyService** | `backend/app/services/company_service.py` | Root node, no parent relationship. `c {.*} AS company` |
| **ProjectService** | `backend/app/services/project_service.py` | `(Company)-[:OWNS_PROJECT]->(Project)`. company_id derived from traversal, NOT stored on node |
| **MemberService** | `backend/app/services/member_service.py` | `(Member)-[:MEMBER_OF]->(Company)`. company_id derived from traversal |
| **InvitationService** | `backend/app/services/invitation_service.py` | `(Invitation)-[:FOR_COMPANY]->(Company)`. accept_invitation creates Member in same transaction |
| **ProjectAssignmentService** | `backend/app/services/project_assignment_service.py` | `(Company)-[:HAS_ASSIGNMENT]->(ProjectAssignment)`. project_id/resource_id as node properties |

### Router Updated

| Router | File | Changes |
|--------|------|---------|
| **companies** | `backend/app/routers/companies.py` | Now uses DI `get_company_service` + `run_sync` instead of inline `CompanyService(driver)` |

### Tests Updated

| Test file | Changes |
|-----------|---------|
| `backend/tests/test_api_companies.py` | `test_company: Company` → `test_company: dict`. Added validation error test, get-by-id tests, update-no-company test |
| `backend/tests/test_api_projects.py` | Fixed `test_company.id` → `test_company["id"]` (dict access) |

---

## Design Decisions Made

1. **company_id NOT on child nodes**: Project, Member, Invitation nodes don't store company_id as a property. It's derived from the graph traversal in RETURN clauses: `RETURN p {.*, company_id: c.id} AS project`. This follows Design Principle #6 (tenant isolation via edges).

2. **ProjectAssignment as nodes, not relationship properties**: The handoff suggested assignments create `[:ASSIGNED_TO]` edges, but the existing API surface (CRUD with IDs, pagination, soft delete) is better served by nodes. Linked via `(Company)-[:HAS_ASSIGNMENT]->(ProjectAssignment)` with project_id/resource_id as properties. Deep graph relationships (Worker→Project edges for compliance traversal) can be added later.

3. **delete pattern**: `DETACH DELETE` returns 0 rows, so existence check is done first in a separate read, then delete in a write. Company uses this two-step pattern; soft-delete services (Project, Assignment) use a single `SET deleted = true` write.

4. **Invitation.accept_invitation**: Creates Member node AND updates Invitation status in a single Cypher write transaction (atomicity). No longer needs MemberService dependency.

5. **Members router unchanged**: The `members.py` router already uses DI-injected services. It calls service methods synchronously in async handlers (pre-existing pattern, not fixed in this batch).

---

## Verification Status

- **Import check**: All 5 services import cleanly ✓
- **Router import**: companies.py, members.py import cleanly ✓
- **App load**: 151 routes, no import errors ✓
- **Tests**: NOT RUN — Neo4j not available locally. Need Docker Desktop or Neo4j Desktop installed.

### To verify tests

```bash
# Option 1: Docker
docker run -d --name neo4j-test -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:5

# Option 2: Set custom connection
export NEO4J_TEST_URI=bolt://localhost:7687
export NEO4J_TEST_USER=neo4j
export NEO4J_TEST_PASSWORD=password

# Run Batch 1A tests
python -m pytest tests/test_api_companies.py tests/test_api_projects.py -v
```

---

## Remaining test fixes needed (later batches)

These test files still use `test_company.id` (model attribute access) instead of `test_company["id"]` (dict access). Fix when rewriting those services:

- `test_api_documents.py`
- `test_api_osha_log.py`
- `test_api_mock_inspection.py`
- `test_api_gc_portal.py`
- `test_api_workers.py`
- `test_billing.py`

---

## What's Next: Batch 1B (HR + Equipment)

- **worker_service.py** — `(Company)-[:EMPLOYS]->(Worker)`. Largest service by LOC.
- **equipment_service.py** — `(Company)-[:OWNS_EQUIPMENT]->(Equipment)`.

### Start here for Batch 1B

1. Read `backend/app/services/worker_service.py`
2. Read `backend/app/services/equipment_service.py`
3. Follow same rewrite pattern from Batch 1A (extend BaseService, derive company_id from traversal)
4. Fix `test_api_workers.py` (dict access for test_company)
