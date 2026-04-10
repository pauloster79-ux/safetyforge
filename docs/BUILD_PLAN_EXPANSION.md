# Kerf Build Plan — Platform Expansion

*Version 1.0 — 2026-04-07*

---

## OVERVIEW

This document is the execution plan for expanding Kerf from a safety compliance platform into a full construction operations platform. It assumes the Phase 1 safety foundation (Sprints 0-10 in `BUILD_PLAN.md`) is complete or near-complete, and builds on the existing data model, inspection engine, worker/equipment/project entities, and voice-first architecture.

The expansion follows the priority order determined by market research:
1. **Daily Logs** — highest data overlap with safety, makes the app the superintendent's daily driver
2. **Quality Inspections / Punch Lists** — reuses the existing inspection engine with different templates
3. **Time Tracking** — extends existing worker/project assignment data
4. **Expanded Sub Management** — extends existing GC portal
5. **RFIs / Submittals** — new coordination workflows
6. **Basic Scheduling** — weekly lookahead connected to safety data

---

## STRATEGIC CONTEXT

### Why this order

**Daily Logs are the Trojan horse.** The superintendent is already in the app for safety; daily logs make it the first thing they open every morning. 40-50% of daily log fields are already captured by safety workflows. This is the lowest-effort, highest-stickiness expansion.

**Quality Inspections reuse the same engine.** The inspection workflow (observe → photograph → assign corrective action → track → close) is technically identical for safety and quality. Procore already bundles them into one module, validating the approach. This is a template expansion, not a new product.

**Time Tracking has the strongest ROI case.** 38% of contractors still use paper timesheets. Time theft costs ~$52K/year per 50-person crew. The data bridge is real — toolbox talk attendance is already an implicit check-in. And no competitor connects time data to safety data (fatigue analysis).

**Sub Management extends what exists.** The GC portal, prequalification automation, and compliance visibility are built. The biggest gap — COI tracking — is the highest-pain item (7/10 COIs are non-compliant). Safety data creates a unique sub performance scoring moat.

**RFIs and Scheduling are platform stickiness plays.** They complete the "one tool" promise but are less urgent than the field-operations features above.

### Market opportunity per feature

| Feature | Addressable Market | Competitors at our price point | Our advantage |
|---|---|---|---|
| Daily Logs | ~$1.5-4B (815K firms, mostly on paper) | Raken ($15-49/user) | 40-50% auto-populated from safety data |
| Quality / Punch Lists | ~$1.2-1.3B → $2.5B by 2033 | Fieldwire ($39-94/user), FTQ360 ($249/mo) | Same inspection engine, no second app |
| Time Tracking | ~$540M-1.1B (8.1M workers) | ClockShark ($9-11/user), Busybusy (free-$10) | Safety+time correlation (fatigue), single worker record |
| Sub Management | ~$3.2B → $8.1B by 2033 | ISNetworld ($875+/yr sub-paid), Avetta | Safety data moat, GC-paid model (subs free) |
| RFIs | Part of $10.6B PM market | Procore ($$$), SubmittalLink ($150-250/mo) | Integrated with safety + daily logs + schedule |
| Scheduling | 38% of $10.6B PM market | Outbuild ($999/mo), MS Project ($30/user) | Cert expiry + equipment + incident connection |

---

## PHASE 1: DAILY LOGS (Weeks 13-15)

**Goal:** The superintendent's morning safety walk produces a complete daily log with 50% of fields auto-populated from existing data. Replaces the most legally important document a contractor produces.

### Dependencies
- Project entity (Sprint 2 ✅)
- Inspection engine with photos/GPS (Sprint 2 ✅)
- Worker tracking (Sprint 4 ✅)
- Equipment tracking (Sprint 7/8 ✅)
- Toolbox talks (Sprint 3 ✅)

### Data Model

```
companies/{company_id}/projects/{project_id}/daily_logs/{log_id}
```

#### DailyLog entity
```python
class DailyLog(BaseModel):
    id: str
    company_id: str
    project_id: str
    log_date: date
    status: Literal["draft", "submitted", "approved"]
    author_id: str  # worker/member who wrote it

    # Auto-populated from existing data
    weather: WeatherData  # from morning brief / weather API
    crew_count_own: int  # from worker assignments
    crew_count_sub: dict[str, int]  # sub company -> headcount
    equipment_on_site: list[str]  # from equipment assignments
    safety_observations: list[str]  # from today's inspection findings
    toolbox_talk_summary: str | None  # from today's talk
    incidents: list[str]  # incident IDs from today
    hazard_reports: list[str]  # hazard report IDs from today

    # Manual entry by superintendent
    work_performed: str  # narrative of tasks completed
    materials_received: list[MaterialDelivery]
    delays: list[DelayRecord]
    visitors: list[VisitorRecord]
    photos: list[str]  # additional progress photos
    notes: str | None

    # Audit
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    submitted_by: str | None
```

### Tasks

#### P1-T1: DailyLog backend model and service
- **What:** Create DailyLog Pydantic model, Firestore service with CRUD operations, and auto-population logic that pulls from today's inspections, toolbox talks, incidents, hazard reports, equipment assignments, and worker assignments.
- **Files to create:**
  - `backend/app/models/daily_log.py`
  - `backend/app/services/daily_log_service.py`
- **Key logic:** `create_draft()` method queries today's data across related collections and pre-fills the auto-populated fields. Weather data from the morning brief service or OpenWeatherMap API.
- **Effort:** 16 hours

#### P1-T2: DailyLog API endpoints
- **What:** CRUD routes for daily logs. `POST` creates a draft with auto-population. `PATCH` updates manual fields. `POST .../submit` finalises.
- **Routes:**
  - `GET /me/projects/{project_id}/daily-logs` — list by date range
  - `POST /me/projects/{project_id}/daily-logs` — create draft (auto-populates)
  - `GET /me/projects/{project_id}/daily-logs/{log_id}` — fetch
  - `PATCH /me/projects/{project_id}/daily-logs/{log_id}` — update manual fields
  - `POST /me/projects/{project_id}/daily-logs/{log_id}/submit` — finalise
  - `GET /me/daily-logs/missing` — projects without today's log
- **Files to create/modify:**
  - `backend/app/routers/daily_logs.py`
  - `backend/app/routers/me.py` — mount daily log router
- **Effort:** 10 hours

#### P1-T3: DailyLog voice input integration
- **What:** Extend the voice parsing service to extract daily log data from superintendent's narration. After the safety inspection is parsed from voice, remaining content (work performed, materials, delays) is extracted as daily log fields.
- **Files to modify:**
  - `backend/app/services/voice_service.py` — add `parse_daily_log()` prompt
- **Effort:** 8 hours

#### P1-T4: DailyLog frontend — list and detail views
- **What:** Daily log list page (by project, by date), detail/edit view with auto-populated fields shown as read-only and manual fields as editable. Clear visual distinction between "auto-captured" and "you need to add this."
- **Files to create:**
  - `frontend/src/components/daily-logs/DailyLogList.tsx`
  - `frontend/src/components/daily-logs/DailyLogDetail.tsx`
  - `frontend/src/components/daily-logs/DailyLogForm.tsx`
  - `frontend/src/hooks/useDailyLogs.ts`
- **Effort:** 20 hours

#### P1-T5: DailyLog PDF export
- **What:** Generate a professional PDF daily log report. Format follows AIA G703/industry standard layout. Includes all auto-populated and manual fields, attached photos, and linked inspection/incident/hazard references.
- **Files to modify:**
  - `backend/app/services/pdf_service.py` — add daily log template
- **Effort:** 8 hours

#### P1-T6: Dashboard integration
- **What:** Add "Daily Log Status" panel to the main dashboard showing which projects have/haven't submitted today's log. Missing logs surface as amber alerts.
- **Files to modify:**
  - `frontend/src/components/dashboard/DashboardPage.tsx`
  - `backend/app/services/analytics_service.py`
- **Effort:** 6 hours

**Phase 1 Total: ~68 hours (2-3 weeks)**

---

## PHASE 2: QUALITY INSPECTIONS & PUNCH LISTS (Weeks 16-18)

**Goal:** The same inspection engine that handles safety inspections also handles quality inspections and punch lists. One walk, two reports. No second app.

### Tasks

#### P2-T1: Quality inspection templates
- **What:** Create quality-specific checklist templates for common construction activities: concrete placement, framing, MEP rough-in, waterproofing, roofing, drywall, painting/finishes, landscaping/site work. Templates reference building codes (IBC/IRC) instead of OSHA standards.
- **Files to create:**
  - `backend/app/models/quality_inspection.py` — extend inspection model with `inspection_category: Literal["safety", "quality"]`
  - `backend/app/services/quality_template_service.py` — quality checklist templates
- **Effort:** 12 hours

#### P2-T2: Quality inspection backend
- **What:** Extend the existing inspection service to support quality-category inspections. Same CRUD operations, same corrective action workflow, different template set and different reporting category.
- **Files to modify:**
  - `backend/app/models/inspection.py` — add `category` field
  - `backend/app/services/inspection_service.py` — filter by category
  - `backend/app/routers/me.py` — add quality-specific query params
- **Effort:** 8 hours

#### P2-T3: Punch list workflow
- **What:** Create a punch list mode — a closeout-specific inspection type that tracks deficiencies through a status workflow: `identified → assigned → corrected → verified → closed`. Punch items can be created from quality inspections or standalone walkthroughs.
- **Files to create:**
  - `backend/app/models/punch_list.py`
  - `backend/app/services/punch_list_service.py`
- **Routes:**
  - `GET /me/projects/{project_id}/punch-lists` — list all punch lists
  - `POST /me/projects/{project_id}/punch-lists` — create punch list
  - `POST /me/projects/{project_id}/punch-lists/{list_id}/items` — add item
  - `PATCH /me/projects/{project_id}/punch-lists/{list_id}/items/{item_id}` — update status
  - `GET /me/projects/{project_id}/punch-lists/{list_id}/summary` — progress stats
- **Effort:** 14 hours

#### P2-T4: Quality inspection frontend
- **What:** Quality inspection UI — same layout as safety inspections but with quality-specific templates. Tab or toggle to switch between safety and quality views. Unified "Inspections" page with category filter.
- **Files to create/modify:**
  - `frontend/src/components/inspections/InspectionList.tsx` — add category filter
  - `frontend/src/components/quality/QualityTemplates.tsx`
- **Effort:** 12 hours

#### P2-T5: Punch list frontend
- **What:** Punch list UI — list of deficiency items with photo, location, assignee, status, and due date. Progress bar showing items by status. Bulk update capabilities.
- **Files to create:**
  - `frontend/src/components/quality/PunchListPage.tsx`
  - `frontend/src/components/quality/PunchListItem.tsx`
  - `frontend/src/hooks/usePunchList.ts`
- **Effort:** 16 hours

#### P2-T6: Quality metrics on dashboard
- **What:** Add quality deficiency rates, punch list aging, and FTQ (first-time quality) score to the analytics dashboard.
- **Files to modify:**
  - `backend/app/services/analytics_service.py`
  - `frontend/src/components/dashboard/DashboardPage.tsx`
- **Effort:** 8 hours

#### P2-T7: Daily log integration
- **What:** Quality observations from the morning walk auto-populate into the daily log alongside safety observations. One walk produces safety + quality + daily log.
- **Files to modify:**
  - `backend/app/services/daily_log_service.py` — pull quality inspection data
- **Effort:** 4 hours

**Phase 2 Total: ~74 hours (2-3 weeks)**

---

## PHASE 3: TIME TRACKING (Weeks 19-22)

**Goal:** GPS-verified clock-in/clock-out with cost code allocation, crew-based entry for foremen, and payroll export. Connected to safety data for fatigue analysis.

### Tasks

#### P3-T1: Time entry data model
- **What:** Create TimeEntry model supporting individual and crew-based clock-in/out. GPS-verified. Cost code allocation. Supports split entries (worker moves between cost codes or projects within a day).
- **Files to create:**
  - `backend/app/models/time_entry.py`
  - `backend/app/models/cost_code.py`
- **Key fields:** worker_id, project_id, cost_code, clock_in (datetime + GPS), clock_out (datetime + GPS), hours_regular, hours_overtime, status (draft/submitted/approved), source (worker_self/foreman_entry/auto_detected)
- **Effort:** 10 hours

#### P3-T2: Time tracking backend service
- **What:** Time entry CRUD with business logic: auto-calculate regular vs overtime (configurable per company: 8hr/day or 40hr/week), break deduction rules, GPS verification against project geofence, duplicate detection.
- **Files to create:**
  - `backend/app/services/time_tracking_service.py`
- **Routes:**
  - `POST /me/time/clock-in` — clock in (individual)
  - `POST /me/time/clock-out` — clock out (individual)
  - `POST /me/time/crew-entry` — foreman enters time for crew
  - `GET /me/projects/{project_id}/timesheets` — list by date range
  - `GET /me/timesheets/weekly-summary` — company-wide weekly summary
  - `POST /me/timesheets/approve` — batch approve timesheets
  - `GET /me/timesheets/export` — payroll export (CSV format)
- **Effort:** 20 hours

#### P3-T3: Cost code management
- **What:** Company-configurable cost codes. Common construction defaults provided. Cost codes assigned per project.
- **Routes:**
  - `GET /me/cost-codes` — list company cost codes
  - `POST /me/cost-codes` — create cost code
  - `GET /me/projects/{project_id}/cost-codes` — project-specific codes
- **Effort:** 6 hours

#### P3-T4: GPS geofencing service
- **What:** Define project geofences (polygon or radius from GPS coordinates). Validate clock-in/clock-out location against geofence. Flag out-of-range entries for review.
- **Files to create:**
  - `backend/app/services/geofence_service.py`
- **Effort:** 10 hours

#### P3-T5: Safety-time correlation engine
- **What:** The unique differentiator. Connect time tracking data with safety data to surface insights:
  - Flag workers on site 10+ hours (fatigue risk)
  - Correlate hours worked with incident rates per project
  - Verify only certified workers are clocked into tasks requiring certifications
  - Calculate OSHA incident rates (per 200,000 hours worked) using actual hours
- **Files to create:**
  - `backend/app/services/fatigue_analysis_service.py`
- **Effort:** 12 hours

#### P3-T6: Time tracking frontend — worker clock-in
- **What:** One-tap clock-in/out on mobile. Shows current project, current cost code, time elapsed. GPS indicator. Worker can switch cost codes without clocking out. Spanish-first interface for field workers.
- **Files to create:**
  - `frontend/src/components/time/ClockInWidget.tsx`
  - `frontend/src/components/time/CostCodeSelector.tsx`
  - `frontend/src/hooks/useTimeTracking.ts`
- **Effort:** 16 hours

#### P3-T7: Time tracking frontend — foreman crew entry
- **What:** Foreman can enter time for entire crew. Select workers from project roster, set common clock-in/out time and cost code, adjust individuals as needed. Batch entry for end-of-day.
- **Files to create:**
  - `frontend/src/components/time/CrewTimeEntry.tsx`
- **Effort:** 12 hours

#### P3-T8: Timesheet management frontend
- **What:** Weekly timesheet view for managers. Per-worker, per-project, per-cost-code breakdown. Approve/reject workflow. Export to CSV for payroll import.
- **Files to create:**
  - `frontend/src/components/time/TimesheetPage.tsx`
  - `frontend/src/components/time/TimesheetExport.tsx`
- **Effort:** 16 hours

#### P3-T9: Dashboard integration
- **What:** Add time tracking summary to dashboard: total hours this week, labour cost by project, overtime alerts, fatigue risk flags, timesheet submission status.
- **Files to modify:**
  - `frontend/src/components/dashboard/DashboardPage.tsx`
  - `backend/app/services/analytics_service.py`
- **Effort:** 8 hours

#### P3-T10: Daily log integration
- **What:** Auto-populate daily log manpower section from time tracking data. Crew count, hours by trade, and sub headcounts pulled from clock-in records.
- **Files to modify:**
  - `backend/app/services/daily_log_service.py`
- **Effort:** 4 hours

**Phase 3 Total: ~114 hours (3-4 weeks)**

---

## PHASE 4: EXPANDED SUB MANAGEMENT (Weeks 23-25)

**Goal:** Extend the existing GC portal with automated COI tracking, insurance expiry alerts, sub performance scoring, and lien waiver management.

### Tasks

#### P4-T1: COI tracking and AI parsing
- **What:** Upload insurance certificates (COIs). AI/OCR extracts: carrier, policy number, coverage limits, additional insured status, effective/expiry dates. Validate against GC requirements. Flag non-compliant certificates.
- **Files to create:**
  - `backend/app/models/insurance_certificate.py`
  - `backend/app/services/coi_service.py`
- **Effort:** 16 hours

#### P4-T2: Insurance expiry monitoring
- **What:** Automated alerts at 30/14/7 days before expiry. Email to sub contact requesting renewal. Escalation to GC if not renewed. Dashboard showing insurance status across all subs.
- **Files to modify:**
  - `backend/app/services/coi_service.py`
  - `backend/app/services/notification_service.py`
- **Effort:** 10 hours

#### P4-T3: Sub performance scoring
- **What:** Generate a performance score for each sub based on data already in the system: inspection pass rates, incident frequency, toolbox talk completion, corrective action closure time, training currency. Score weighted by severity.
- **Files to create:**
  - `backend/app/services/sub_performance_service.py`
- **Effort:** 12 hours

#### P4-T4: Lien waiver management
- **What:** Track conditional/unconditional lien waivers per payment application. Generate waiver forms. Track sub-tier waiver compliance.
- **Files to create:**
  - `backend/app/models/lien_waiver.py`
  - `backend/app/services/lien_waiver_service.py`
- **Effort:** 10 hours

#### P4-T5: Sub management frontend
- **What:** Enhanced sub compliance dashboard. Per-sub cards showing: insurance status, safety score, training currency, inspection activity, lien waiver status. Drill-down to detail. Bulk actions.
- **Files to create/modify:**
  - `frontend/src/components/gc-portal/SubComplianceDashboard.tsx`
  - `frontend/src/components/gc-portal/COIUpload.tsx`
  - `frontend/src/components/gc-portal/SubPerformanceCard.tsx`
  - `frontend/src/components/gc-portal/LienWaiverTracker.tsx`
- **Effort:** 24 hours

**Phase 4 Total: ~72 hours (2-3 weeks)**

---

## PHASE 5: RFIs & SUBMITTALS (Weeks 26-29)

**Goal:** Structured RFI and submittal logs with assignment, tracking, audit trail, and PDF export. Replaces email + Excel for the 50-person GC.

### Tasks

#### P5-T1: RFI data model and service
- **What:** RFI entity with auto-numbering, assignment, status workflow (draft → submitted → responded → closed), ball-in-court tracking, due dates, and file attachments.
- **Files to create:**
  - `backend/app/models/rfi.py`
  - `backend/app/services/rfi_service.py`
- **Routes:**
  - `GET /me/projects/{project_id}/rfis` — list with filters
  - `POST /me/projects/{project_id}/rfis` — create
  - `GET /me/projects/{project_id}/rfis/{rfi_id}` — detail with history
  - `PATCH /me/projects/{project_id}/rfis/{rfi_id}` — update/respond
  - `POST /me/projects/{project_id}/rfis/{rfi_id}/respond` — record response
  - `GET /me/rfis/overdue` — cross-project overdue RFIs
- **Effort:** 16 hours

#### P5-T2: Submittal data model and service
- **What:** Submittal log with multi-step review workflow (submitted → reviewed → approved/rejected/revise-and-resubmit). Spec section linking. File attachments.
- **Files to create:**
  - `backend/app/models/submittal.py`
  - `backend/app/services/submittal_service.py`
- **Effort:** 14 hours

#### P5-T3: Change order tracking
- **What:** Change order log linked to RFIs and project. Track proposed/approved/rejected changes with cost and schedule impact description.
- **Files to create:**
  - `backend/app/models/change_order.py`
  - `backend/app/services/change_order_service.py`
- **Effort:** 10 hours

#### P5-T4: Email notifications for RFI/submittal workflows
- **What:** Auto-notify assignees on creation, remind on approaching due dates, escalate on overdue items. Email responses can be captured and threaded.
- **Files to modify:**
  - `backend/app/services/notification_service.py`
- **Effort:** 8 hours

#### P5-T5: RFI/Submittal frontend
- **What:** RFI log page with filters (status, assignee, overdue). Submittal log with review workflow. Change order log. Dashboard widgets showing overdue counts and response time metrics.
- **Files to create:**
  - `frontend/src/components/rfis/RFIList.tsx`
  - `frontend/src/components/rfis/RFIDetail.tsx`
  - `frontend/src/components/rfis/RFIForm.tsx`
  - `frontend/src/components/submittals/SubmittalList.tsx`
  - `frontend/src/components/submittals/SubmittalDetail.tsx`
  - `frontend/src/components/change-orders/ChangeOrderList.tsx`
  - `frontend/src/hooks/useRFIs.ts`
  - `frontend/src/hooks/useSubmittals.ts`
- **Effort:** 30 hours

#### P5-T6: PDF export for RFIs
- **What:** Generate industry-standard RFI forms as PDF. Include full thread history, attachments, and response.
- **Effort:** 6 hours

**Phase 5 Total: ~84 hours (3-4 weeks)**

---

## PHASE 6: BASIC SCHEDULING (Weeks 30-32)

**Goal:** A weekly lookahead — a 2-4 week rolling task board that superintendents manage from their phone. Connected to safety data: cert expiries block scheduling, equipment maintenance blocks usage, incidents trigger delay documentation.

### Tasks

#### P6-T1: Schedule task data model
- **What:** Task entity: name, project, trade/crew assignment, planned dates (start/end), status (planned/in-progress/complete/blocked), dependencies (simple finish-to-start), notes.
- **Files to create:**
  - `backend/app/models/schedule_task.py`
  - `backend/app/services/scheduling_service.py`
- **Effort:** 10 hours

#### P6-T2: Safety-schedule conflict detection
- **What:** The differentiator. When a task is scheduled, check:
  - Do assigned workers have required certifications valid through the task dates?
  - Is assigned equipment due for maintenance/inspection during the task?
  - Are there open corrective actions on the work area?
  - Has there been a recent incident in the work area?
  Flag conflicts before they become violations.
- **Files to create:**
  - `backend/app/services/schedule_conflict_service.py`
- **Effort:** 14 hours

#### P6-T3: Schedule API
- **Routes:**
  - `GET /me/projects/{project_id}/schedule` — full schedule
  - `GET /me/projects/{project_id}/schedule/lookahead` — 2-4 week rolling view
  - `POST /me/projects/{project_id}/schedule/tasks` — create task
  - `PATCH /me/projects/{project_id}/schedule/tasks/{task_id}` — update
  - `GET /me/projects/{project_id}/schedule/conflicts` — safety-schedule conflicts
  - `GET /me/schedule/today` — cross-project today view
- **Effort:** 10 hours

#### P6-T4: Schedule frontend — lookahead board
- **What:** Mobile-first weekly lookahead. Column per day, cards per task with trade/crew assignment, status colour coding. Drag-and-drop to reschedule. Conflict indicators (amber/red badges). Swipe to complete.
- **Files to create:**
  - `frontend/src/components/schedule/LookaheadBoard.tsx`
  - `frontend/src/components/schedule/TaskCard.tsx`
  - `frontend/src/components/schedule/ConflictBadge.tsx`
  - `frontend/src/hooks/useSchedule.ts`
- **Effort:** 24 hours

#### P6-T5: Schedule-daily log integration
- **What:** Planned vs actual. The daily log captures work completed; the schedule shows what was planned. Auto-generate variance notes where planned tasks were not completed.
- **Files to modify:**
  - `backend/app/services/daily_log_service.py`
- **Effort:** 6 hours

#### P6-T6: Morning brief integration
- **What:** The morning brief now includes today's scheduled tasks, flagged conflicts, and key milestones approaching.
- **Files to modify:**
  - `backend/app/services/morning_brief_service.py`
- **Effort:** 6 hours

**Phase 6 Total: ~70 hours (2-3 weeks)**

---

## SUMMARY TIMELINE

| Phase | Feature | Weeks | Effort | Cumulative |
|-------|---------|-------|--------|------------|
| Phase 1 | Daily Logs | Weeks 13-15 | ~68 hrs | 68 hrs |
| Phase 2 | Quality / Punch Lists | Weeks 16-18 | ~74 hrs | 142 hrs |
| Phase 3 | Time Tracking | Weeks 19-22 | ~114 hrs | 256 hrs |
| Phase 4 | Sub Management (expanded) | Weeks 23-25 | ~72 hrs | 328 hrs |
| Phase 5 | RFIs / Submittals | Weeks 26-29 | ~84 hrs | 412 hrs |
| Phase 6 | Basic Scheduling | Weeks 30-32 | ~70 hrs | 482 hrs |

**Total expansion effort: ~482 hours over 20 weeks (Weeks 13-32)**

This extends the original 12-week Phase 1 build plan by 20 weeks, for a total of 32 weeks from project start to full construction operations platform. At the end of Week 32, Kerf will handle:

- ✅ Safety compliance (inspections, incidents, toolbox talks, hazard reports, OSHA logs, mock inspections, environmental, prequalification, state compliance)
- ✅ Daily logs (auto-populated from safety data)
- ✅ Quality inspections and punch lists
- ✅ Time tracking with GPS verification and cost codes
- ✅ Expanded sub management (COI tracking, performance scoring, lien waivers)
- ✅ RFIs, submittals, and change orders
- ✅ Basic scheduling (weekly lookahead with safety-schedule conflict detection)

---

## CROSS-CUTTING CONCERNS

### Naming and branding
All user-facing strings, API documentation, email templates, and marketing content should use "Kerf" not "Kerf." The codebase rename can happen incrementally — backend module names and database collections do not need to change immediately, but all new code should use the Kerf name.

### Pricing evolution
The current per-project pricing ($99/$299/$599) may need revision as the platform scope expands. Consider:
- Base platform fee (safety + daily logs + quality) at existing tiers
- Add-on modules: time tracking ($4-6/worker/month), sub management, RFIs, scheduling
- Bundle pricing for "full platform" at a premium tier

### Mobile-first design
Every expansion feature must work on mobile first. The superintendent is on a jobsite, not at a desk. Time tracking clock-in, daily log review, punch list walkthrough, schedule lookahead — all must be designed for a phone in direct sunlight with dirty gloves.

### Voice-first where applicable
Daily logs, quality observations, and incident reports should all support voice input. RFIs and scheduling are primarily typed/tapped workflows and do not need voice support initially.

### Data integration points
Each new feature must connect to existing data — this is the "one tool" promise:
- Daily logs auto-populate from safety + time + equipment data
- Quality inspections use the same engine as safety inspections
- Time tracking connects to worker records and project assignments
- Schedule connects to certifications, equipment, and incidents
- Sub management uses safety data for performance scoring
- Morning brief incorporates schedule, time, quality, and sub data

### Testing strategy
- Backend: pytest with Firestore emulator, same pattern as Phase 1
- Frontend: Vitest + Testing Library, same pattern as Phase 1
- E2E: Playwright journeys for each new workflow
- Integration: IS-X scenarios for cross-feature data flow (daily log auto-population, safety-schedule conflicts, fatigue analysis)

---

*This plan is a living document. Effort estimates are based on the existing codebase patterns and assume one developer. Actual timelines may vary. The priority order is firm — daily logs before quality before time tracking — but individual tasks within each phase may be reordered based on discovery during implementation.*
