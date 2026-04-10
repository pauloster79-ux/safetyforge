# Handoff: Batch 1B Complete → Batch 1C

**Date:** 2026-04-09
**From:** Batch 1A+1B session
**To:** Batch 1C (Safety services)

---

## What Batch 1B Delivered

### 2 Services Rewritten + 1 Side-Fix

| Service | File | Key Pattern |
|---------|------|-------------|
| **WorkerService** | `backend/app/services/worker_service.py` | `(Company)-[:EMPLOYS]->(Worker)`. Certifications stored as JSON string (`_certifications_json`) on Worker node. Computed fields (total_certifications, expiring_soon, expired) calculated at read time. |
| **EquipmentService** | `backend/app/services/equipment_service.py` | `(Company)-[:OWNS_EQUIPMENT]->(Equipment)`. Inspection logs as `(Equipment)-[:HAS_INSPECTION_LOG]->(EquipmentInspectionLog)` nodes. Log items stored as `_items_json`. |
| **BillingService** | `backend/app/services/billing_service.py` | Side-fix from Batch 1A — was blocking project tests. Now extends BaseService, uses Cypher for plan_name/billing_period storage. Webhook events stored as `WebhookEvent` nodes. |

### Tests Updated
- `test_api_workers.py`: Fixed `test_company.id` → `test_company["id"]`

---

## Design Decisions

1. **Certifications as JSON, not graph nodes**: Worker certifications are stored as `_certifications_json` (a JSON string property) on the Worker node. Neo4j doesn't support lists of maps as properties. This is a pragmatic compromise — when compliance traversals are needed later, certifications can be promoted to `(Worker)-[:HOLDS_CERT]->(Certification)` nodes.

2. **Equipment inspection logs as nodes**: Unlike certifications (which are a simple embedded list), inspection logs are full entities with their own IDs and CRUD — modeled as `(Equipment)-[:HAS_INSPECTION_LOG]->(EquipmentInspectionLog)`. The `items` checklist on each log is stored as `_items_json`.

3. **BillingService side-fix**: BillingService was creating `CompanyService(db)` internally with Firestore client. Updated to `CompanyService(driver)`, now extends BaseService. Webhook idempotency uses `WebhookEvent` nodes instead of Firestore collection.

---

## Verification

- **39/39 tests pass** (Batch 1A: 18, Batch 1B: 21) in 3.44s
- Remaining 105 failures are all in Batch 1C/1D services (still Firestore)
- App loads with 151 routes

---

## What's Next: Batch 1C (Safety)

4 services to rewrite:
- **inspection_service.py** — `(Project)-[:HAS_INSPECTION]->(Inspection)`, items as `(Inspection)-[:HAS_ITEM]->(InspectionItem)`
- **incident_service.py** — `(Project)-[:HAS_INCIDENT]->(Incident)`
- **hazard_report_service.py** — `(Project)-[:HAS_HAZARD_REPORT]->(HazardReport)`
- **toolbox_talk_service.py** — `(Project)-[:HAS_TOOLBOX_TALK]->(ToolboxTalk)`

### Start here
1. Read each service file + its model file
2. Follow same pattern (extend BaseService, derive company_id from traversal)
3. Fix corresponding test files (dict access for test_company)
