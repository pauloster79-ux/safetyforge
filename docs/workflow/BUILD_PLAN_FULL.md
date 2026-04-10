# SafetyForge (Kerf) — Full Build Plan

## Context

SafetyForge has a working backend (FastAPI + Neo4j, 334 tests, 154 endpoints) and a fully functional frontend (React + Vite + shadcn/ui, 71 components, demo mode). The agentic infrastructure (ComplianceAgent, BriefingAgent, EventBus, 8 MCP tools) is tested but not wired into the running app. The expansion plan adds 6 major feature areas across ~482 hours. Goal: demo-ready first, then systematic expansion through all 6 phases.

---

## Phase 0: Stabilisation (Demo-Ready)

Fix all gaps so the platform works end-to-end — agents triggerable, events flowing, frontend connected.

### 0-A: Schema Constraints for Agent Nodes
Add `ComplianceAlert` and `BriefingSummary` constraints to `backend/graph/schema.cypher` (uniqueness on alert_id/briefing_id, NOT NULL, indexes on alert_type/severity/date). Follow existing `IF NOT EXISTS` pattern.

### 0-B: Wire EventBus + AgentOrchestrator on Startup
- Modify `backend/app/main.py` lifespan: instantiate EventBus, AgentIdentityService, MCPToolService, LLMService, AgentOrchestrator. Call `wire_subscriptions()`. Store on `app.state`.
- Add `get_event_bus()` and `get_agent_orchestrator()` to `backend/app/dependencies.py`.

### 0-C: Event Emission from REST Layer
Add event emission to key router endpoints so agents actually get triggered:
- Inspection creation → `EventType.INSPECTION_COMPLETED`
- Incident creation → `EventType.INCIDENT_REPORTED`
- Hazard report creation → `EventType.HAZARD_REPORTED`
- Worker assignment → `EventType.WORKER_ASSIGNED`

Modify the relevant `me.py` router handlers. Import EventBus via `Depends(get_event_bus)`.

### 0-D: Agent On-Demand REST Endpoints
Add to `backend/app/routers/agents.py`:
- `POST /me/agents/compliance/check` → `orchestrator.run_compliance_check()`
- `GET /me/agents/compliance/alerts` → query ComplianceAlert nodes
- `POST /me/agents/briefing/generate` → `orchestrator.run_briefing()`
- `GET /me/agents/briefings` → query BriefingSummary nodes

### 0-E: Frontend Environment Setup
- Create `frontend/.env.example` with `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY`
- Verify demo mode toggle works (session flag `kerf_demo`)
- Confirm real API calls work when Clerk is configured and demo mode is off

### 0-F: Fix Stale Docs
- Rewrite `docs/architecture/BACKEND_ARCHITECTURE.md` to reference Neo4j graph model
- Fix Firestore references in `docs/BUILD_PLAN_EXPANSION.md`

### 0-G: CI Schema Validation
Add explicit `cypher-shell` step in `.github/workflows/ci.yml` to apply `schema.cypher` with error checking before pytest runs.

**Execution order:** 0-A + 0-F (independent) → 0-B + 0-C (coupled) → 0-D (depends on orchestrator) → 0-E + 0-G (independent)

---

## Phase 1: Daily Logs

Auto-populated daily construction logs — the #1 expansion feature (40-50% auto-fill from safety data).

### Backend
| Task | File | Description |
|------|------|-------------|
| 1.1 | `models/daily_log.py` | DailyLog, DailyLogCreate, DailyLogUpdate, WeatherData, MaterialDelivery, DelayRecord, VisitorRecord. Status: draft → submitted → approved |
| 1.2 | `services/daily_log_service.py` | BaseService. `create_draft()` auto-populates from today's inspections, toolbox talks, incidents, worker assignments, equipment. Graph: `(Project)-[:HAS_DAILY_LOG]->(DailyLog)` |
| 1.3 | `routers/daily_logs.py` | CRUD + submit + missing-logs endpoint. Register in main.py, add DI in dependencies.py |
| 1.4 | `services/voice_service.py` | Add `parse_daily_log()` — extends existing Claude audio pattern |
| 1.5 | `services/pdf_service.py` | Daily log PDF template (AIA G703 format) |
| 1.6 | `schema.cypher` | Domain 8 constraints already exist — verify and extend if needed |
| 1.7 | `tests/test_api_daily_logs.py` | Full test suite, real Neo4j |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 1.8 | `hooks/useDailyLogs.ts` | TanStack Query hook following useInspections pattern |
| 1.9 | `components/daily-logs/` | DailyLogListPage, DailyLogDetailPage, DailyLogForm |
| 1.10 | `App.tsx` + `api.ts` | Routes + demo data handlers |
| 1.11 | `DashboardPage.tsx` | "Daily Log Status" widget — which projects have/haven't submitted today |

### Agent Integration
- Add `EventType.DAILY_LOG_SUBMITTED` to events.py
- Emit from router on submission
- BriefingAgent includes daily log data in morning brief
- Add `get_daily_log_status` MCP tool to mcp_tools.py

---

## Phase 2: Quality Inspections & Punch Lists

Reuses the existing inspection engine with a quality category. Adds punch list workflow.

### Backend
| Task | File | Description |
|------|------|-------------|
| 2.1 | `models/inspection.py` | Add `category: Literal["safety", "quality"]` field (default "safety") |
| 2.2 | `services/quality_template_service.py` | Quality checklist templates (concrete, framing, MEP, waterproofing, roofing) |
| 2.3 | `services/inspection_service.py` | Add category filter to list/query methods |
| 2.4 | `schema.cypher` | Domain 11 constraints (DeficiencyList, DeficiencyItem, NCR, ITP, MaterialTest) |
| 2.5 | `models/punch_list.py` + `services/punch_list_service.py` | Punch list CRUD with status workflow: identified → assigned → corrected → verified → closed |
| 2.6 | `routers/punch_lists.py` + tests | CRUD endpoints |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 2.7 | Inspection pages | Add category toggle (safety vs quality) to existing inspection create/list |
| 2.8 | `components/quality/` | PunchListPage, PunchListItemCard |
| 2.9 | `hooks/usePunchList.ts` | TanStack Query hook |

### Agent Integration
- `EventType.DEFICIENCY_IDENTIFIED`, `EventType.DEFICIENCY_OVERDUE`
- ComplianceAgent monitors deficiency aging
- Quality metrics feed BriefingAgent

---

## Phase 3: Time Tracking

GPS-verified time entries with safety-time correlation (the key differentiator).

### Backend
| Task | File | Description |
|------|------|-------------|
| 3.1 | `models/time_entry.py`, `models/cost_code.py` | TimeEntry, CostCode models. Schema Domain 10 constraints |
| 3.2 | `services/time_tracking_service.py` | Clock in/out, regular vs overtime, break deduction, GPS verification, duplicate detection |
| 3.3 | `services/geofence_service.py` | Point-in-polygon GPS check against project boundaries |
| 3.4 | `services/cost_code_service.py` | Company-configurable cost codes with construction defaults |
| 3.5 | `services/fatigue_analysis_service.py` | Flag 10+ hr workers, correlate hours with incidents, verify certs for time-tracked tasks, OSHA rates per 200K hours |
| 3.6 | `routers/time_tracking.py` + tests | Clock in/out, crew entry, timesheet management |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 3.7 | `components/time/` | ClockInWidget, CostCodeSelector, CrewTimeEntry, TimesheetPage, TimesheetExport |
| 3.8 | `hooks/useTimeTracking.ts` | TanStack Query hook |

### Agent Integration
- `EventType.WORKER_FATIGUE_RISK`
- Time data feeds OSHA rate calculation
- BriefingAgent includes labour summary

---

## Phase 4: Expanded Sub Management

COI tracking with AI/OCR, sub performance scoring, lien waivers.

### Backend
| Task | File | Description |
|------|------|-------------|
| 4.1 | `services/coi_service.py` | Claude API for OCI image extraction (carrier, policy #, coverage, expiry). Schema already has InsuranceCertificate constraints |
| 4.2 | `services/sub_performance_service.py` | Aggregate safety data into performance scores (inspection pass rates, incident frequency, talk completion) |
| 4.3 | `services/lien_waiver_service.py` | Schema already has LienWaiver constraints |
| 4.4 | `routers/sub_management.py` + tests | CRUD + performance dashboard data |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 4.5 | `components/gc-portal/` | COIUpload, SubPerformanceCard, LienWaiverTracker |
| 4.6 | `hooks/useSubManagement.ts` | TanStack Query hook |

### Agent Integration
- `EventType.INSURANCE_EXPIRING`
- ComplianceAgent monitors insurance expiry across all subs

---

## Phase 5: RFIs & Submittals

Coordination workflows with ball-in-court tracking and email notifications.

### Backend
| Task | File | Description |
|------|------|-------------|
| 5.1 | `models/rfi.py`, `models/submittal.py`, `models/change_order.py` | RFI status: draft → submitted → responded → closed. Submittal: submitted → reviewed → approved/rejected |
| 5.2 | `schema.cypher` | Domain 14 constraints (RFI, Submittal, ChangeOrder) |
| 5.3 | `services/rfi_service.py`, `services/submittal_service.py`, `services/change_order_service.py` | CRUD + workflow transitions + auto-numbering |
| 5.4 | `services/notification_service.py` | Email notifications for RFI/submittal lifecycle events |
| 5.5 | `routers/rfis.py`, `routers/submittals.py` + tests | CRUD + workflow endpoints |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 5.6 | `components/rfis/`, `components/submittals/`, `components/change-orders/` | List/detail/create pages with status tracking |
| 5.7 | `hooks/useRFIs.ts`, `hooks/useSubmittals.ts` | TanStack Query hooks |

### Agent Integration
- `EventType.RFI_OVERDUE`, `EventType.SUBMITTAL_PENDING_REVIEW`
- BriefingAgent includes overdue RFIs in morning brief

---

## Phase 6: Basic Scheduling

Rolling 2-4 week lookahead with safety-schedule conflict detection.

### Backend
| Task | File | Description |
|------|------|-------------|
| 6.1 | `models/schedule_task.py` | ScheduleTask with status, trade, dates, dependencies. Schema Domain 12 |
| 6.2 | `services/scheduling_service.py` | Task CRUD, rolling lookahead generation |
| 6.3 | `services/schedule_conflict_service.py` | Check cert validity through task dates, equipment maintenance, open corrective actions, recent incidents in work area |
| 6.4 | `routers/scheduling.py` + tests | CRUD + lookahead + conflict check |
| 6.5 | Modify `morning_brief_service.py` + `daily_log_service.py` | Include today's tasks in brief, planned vs actual variance in daily log |

### Frontend
| Task | File | Description |
|------|------|-------------|
| 6.6 | `components/schedule/` | LookaheadBoard (mobile-first), TaskCard, ConflictBadge |
| 6.7 | `hooks/useSchedule.ts` | TanStack Query hook |

### Agent Integration
- `EventType.SCHEDULE_CONFLICT_DETECTED`
- ComplianceAgent monitors conflicts proactively
- BriefingAgent includes schedule in morning brief

---

## Patterns to Follow (Every Phase)

| Concern | Convention | Reference File |
|---------|-----------|---------------|
| Model | Pydantic with Create/Update variants | `models/inspection.py` |
| Schema | `IF NOT EXISTS` constraints | `graph/schema.cypher` |
| Service | Extend BaseService, `_read_tx`/`_write_tx`, provenance | `services/base_service.py` |
| Router | FastAPI with `Depends()` injection | `routers/agents.py` |
| DI | Factory function in dependencies.py | `dependencies.py` |
| Tests | Real Neo4j, no internal mocks | `tests/conftest.py` |
| Frontend hook | TanStack Query | `hooks/useInspections.ts` |
| Demo data | Constants + handler in api.ts | `lib/api.ts` |
| Events | Add to EventType enum, emit from router | `models/events.py` |
| MCP tools | Add to mcp_tools.py dispatch | `services/mcp_tools.py` |

---

## Effort Summary

| Phase | Scope | Sessions |
|-------|-------|----------|
| 0: Stabilisation | Schema, wiring, endpoints, frontend env, docs, CI | 6-8 |
| 1: Daily Logs | Backend + frontend + voice + PDF + agents | 8-10 |
| 2: Quality/Punch Lists | Extend inspection engine + punch list workflow | 8-10 |
| 3: Time Tracking | GPS, cost codes, fatigue analysis | 12-14 |
| 4: Sub Management | COI AI, performance scoring, lien waivers | 8-10 |
| 5: RFIs/Submittals | Coordination workflows + email notifications | 10-12 |
| 6: Scheduling | Lookahead board + conflict detection | 8-10 |
| **Total** | | **~61-74 sessions** |

## Verification

After each phase:
1. Run `pytest -v` — all tests must pass (existing + new)
2. Start backend with `uvicorn app.main:app` — verify health endpoint
3. Hit new endpoints via Swagger docs at `/docs`
4. For frontend work: verify both demo mode and real backend mode
5. For agent work: trigger an event and verify alert/briefing appears in Neo4j
