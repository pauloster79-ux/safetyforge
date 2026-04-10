# Handoff: Batch 1C Complete → Batch 1D

**Date:** 2026-04-09
**From:** Batch 1C session
**To:** Batch 1D (remaining services)

---

## What Batch 1C Delivered

### 4 Services Rewritten

| Service | File | Key Pattern |
|---------|------|-------------|
| **InspectionService** | `backend/app/services/inspection_service.py` | `(Project)-[:HAS_INSPECTION]->(Inspection)`. Items stored as `_items_json`. Soft-delete pattern. Overall status calculated from items. |
| **IncidentService** | `backend/app/services/incident_service.py` | `(Project)-[:HAS_INCIDENT]->(Incident)`. Lists (photo_urls, involved_worker_ids) as JSON strings. Hard delete via DETACH DELETE. AI investigation preserved. |
| **HazardReportService** | `backend/app/services/hazard_report_service.py` | `(Project)-[:HAS_HAZARD_REPORT]->(HazardReport)`. AI analysis + identified hazards as JSON strings. Hard delete. Takes `(driver, analysis_service)`. |
| **ToolboxTalkService** | `backend/app/services/toolbox_talk_service.py` | `(Project)-[:HAS_TOOLBOX_TALK]->(ToolboxTalk)`. Content dicts, attendees, custom_points as JSON strings. Soft-delete. Read-modify-write for attendee append. |

---

## Design Decisions

1. **JSON strings for complex nested data**: All services use `_*_json` property pattern (same as Batch 1B). Neo4j doesn't support maps/list-of-maps as properties. Fields prefixed with `_` are internal — `_to_model()` deserializes them before returning Pydantic models.

2. **Consistent graph traversal pattern**: All queries use `MATCH (c:Company {id})-[:OWNS_PROJECT]->(p:Project {id})-[:HAS_*]->(entity)` — company_id is always derived from the graph path, never stored on child nodes.

3. **Hard delete vs soft delete**: Incidents and HazardReports use DETACH DELETE (matching original Firestore behavior). Inspections and ToolboxTalks use soft delete (`deleted = true`), also matching original behavior.

4. **IncidentService keeps `(driver, settings)` constructor**: Settings needed for Anthropic API key in `generate_investigation()`. HazardReportService keeps `(driver, analysis_service)` for the same reason.

5. **No test changes needed**: Batch 1C tests already used `test_company` only as a fixture dependency (not accessing `.id`), and created projects via API. No dict-access fixes required.

---

## Verification

- **101/101 tests pass** (Batch 1A: 18, Batch 1B: 21, Batch 1C: 48, Analytics: 14)
- **39 Batch 1A+1B tests** still pass (no regressions)
- **48 Batch 1C tests** all pass
- Remaining 62 failures + 7 errors are all in services not yet rewritten (Batch 1D+)
- Full test run: 41.79s

---

## What's Next: Batch 1D (Remaining Services)

Services still on Firestore (sorted by test count / complexity):

| Service | Tests | Notes |
|---------|-------|-------|
| **osha_log_service.py** | 16 tests | OSHA 300/300A log, TRIR/DART calculations |
| **mock_inspection_service.py** | 15 tests | Depends on many other services (document, worker, project, inspection, toolbox_talk, osha_log) |
| **document_service.py** | ~10 tests | Already partially working? Check `test_api_documents.py` |
| **morning_brief_service.py** | 4 tests | Depends on worker, inspection, toolbox_talk services |
| **environmental_service.py** | 5 tests | Programs, exposure monitoring, SWPPP |
| **gc_portal_service.py** | 5+ tests | GC-sub relationships |
| **prequalification_service.py** | 4 tests | Depends on company, document, osha_log, worker, mock_inspection |
| **state_compliance_service.py** | 1 test | Depends on company, document, worker |
| **billing_service.py** | ~6 tests | Already partially rewritten in Batch 1B (side-fix) |

### Recommended order
1. `osha_log_service.py` (standalone, many tests)
2. `document_service.py` (needed by mock_inspection and prequalification)
3. `environmental_service.py` (standalone)
4. `morning_brief_service.py` (deps already rewritten in 1B/1C)
5. `mock_inspection_service.py` (complex, many deps — do after its deps are done)
6. `gc_portal_service.py`
7. `prequalification_service.py`
8. `state_compliance_service.py`
9. `billing_service.py` (finish what 1B started)
