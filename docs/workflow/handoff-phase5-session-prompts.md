# Phase 5: Session Prompts (3 Parallel Sessions)

Phases 1-4 are complete:
- Phase 1: Full ontology migration (73 entities, 54 services, new schema.cypher)
- Phase 2: Conversation persistence (every chat message → Neo4j, embeddings, Decision/Insight extraction)
- Phase 3: Document pipeline (upload → chunk → embed → search)
- Phase 4: Fresh frontend shell (three-pane: icon rail + chat pane + canvas pane, card rendering system)

Phase 5 builds the 7 contractor processes. Each process needs: MCP tools (intent-based), service logic with graph queries, and chat card rendering in the frontend.

---

## Session D: Execute & Document + Manage Money

These two are linked — Execute produces the data that Manage Money consumes.

```
You are building Phase 5 of Kerf — the contractor processes. Phases 1-4 are complete: full ontology migration, conversation persistence, document pipeline, and a conversational-first frontend shell.

Your job: build two linked processes — "Execute & Document" and "Manage Money".

### Execute & Document (the core daily operation)

This is the highest-value daily interaction. A contractor's crew shows up, works, and the system captures everything.

**MCP tools to create** (add to backend/app/services/mcp_tools.py):
- `create_daily_log` — creates a DailyLog node for a project on a given date
- `auto_populate_daily_log` — queries the graph for the day's safety inspections, time entries, incidents, toolbox talks, equipment usage, and weather, then populates the daily log fields automatically
- `record_time` — creates a TimeEntry (clock in/out for a worker on a work item)
- `report_quality_observation` — creates an Inspection with category "quality"

**Service work:**
- Update `backend/app/services/daily_log_service.py` — add auto-population logic that queries related entities for the day
- `backend/app/services/time_entry_service.py` already exists from Phase 1 — wire it into MCP tools
- Add a quality observation flow to `backend/app/services/inspection_service.py` (category: "quality")

**Frontend cards** (add to frontend/src/components/cards/):
- `DailyLogCard` — date, status, crew count, work performed summary, auto-populated percentage
- `TimeEntryCard` — worker name, clock in/out, hours, work item description
- `QualityCard` — inspection date, category, pass/fail, score

### Manage Money (job costing + variations)

**MCP tools to create:**
- `get_job_cost_summary` — traverses Project → WorkItems → TimeEntries + USES_ITEM to calculate actual vs estimated costs
- `detect_variation` — compares daily log work descriptions against original WorkItem scope to flag potential out-of-scope work
- `create_variation` — creates a Variation node linked to affected WorkItems with evidence chain
- `get_financial_overview` — project-level financial summary: contract value, estimated cost, actual cost, variations, invoiced, paid

**Service work:**
- Create `backend/app/services/job_costing_service.py` — graph traversal for cost rollup (labour from TimeEntries, materials from USES_ITEM relationships, calculated at query time per ontology DD)
- `backend/app/services/variation_service.py` exists from Phase 1 — add detection logic using LLM comparison of daily log narratives vs WorkItem descriptions

**Frontend cards:**
- `JobCostCard` — estimated vs actual cost, margin, burn rate
- `VariationCard` — description, status, amount, evidence chain
- `FinancialOverviewCard` — contract value, costs, variations, profit/loss

**Key files to read first:**
- backend/app/services/mcp_tools.py (existing 9 tools — add new ones following the same pattern)
- backend/app/services/daily_log_service.py
- backend/app/services/time_entry_service.py
- backend/app/services/work_item_service.py
- backend/app/services/variation_service.py
- backend/app/services/guardrails_service.py (register new tools in TOOL_ACTION_MAP and TOOL_SCOPE_MAP)
- frontend/src/components/cards/ (existing card components from Phase 4 — follow the same pattern)
- docs/knowledge-graph/03-entities-relationships.md (full ontology reference)

Register all new MCP tools in the guardrails TOOL_ACTION_MAP (read-only tools as READ_ONLY, create_variation as LOW_RISK_WRITE) and TOOL_SCOPE_MAP.

Use maximum effort.
```

---

## Session E: Estimate & Price + Propose & Win + Get Paid

The quoting-to-payment workflow.

```
You are building Phase 5 of Kerf — the contractor processes. Phases 1-4 are complete: full ontology migration, conversation persistence, document pipeline, and a conversational-first frontend shell.

Your job: build three processes in the quoting-to-payment workflow — "Estimate & Price", "Propose & Win", and "Get Paid".

### Estimate & Price

Estimating in Kerf = creating WorkItems via conversation on a project in "quoted" status. There is NO Estimate entity — the WorkItems on a quoted project ARE the estimate.

**MCP tools to create** (add to backend/app/services/mcp_tools.py):
- `create_work_item` — creates a WorkItem on a project (or within a WorkPackage). Accepts: description, labour_hours, labour_rate, materials_allowance. Sets state to "draft".
- `update_work_item` — updates a WorkItem's properties
- `get_estimate_summary` — traverses Project → WorkItems, calculates: total labour cost, total materials cost (from USES_ITEM), total with margin. Returns itemised breakdown.
- `search_historical_rates` — searches past completed projects for similar WorkItems to suggest labour hours and rates. Uses WorkCategory matching and optional semantic search on descriptions.
- `add_item_to_work_item` — adds a USES_ITEM relationship (material/product) to a WorkItem with quantity, unit, unit_cost

**Service work:**
- `backend/app/services/work_item_service.py` exists from Phase 1 — wire into MCP tools
- Create `backend/app/services/estimating_service.py` — historical rate lookup via graph traversal across past projects' WorkItems grouped by WorkCategory
- `backend/app/services/work_package_service.py` exists — wire into tools for grouped estimates

**Frontend cards:**
- `WorkItemCard` — description, state, labour hours/rate, materials, total cost
- `EstimateSummaryCard` — project name, total items, labour total, materials total, margin, grand total

### Propose & Win

Converting an estimate into a proposal document and tracking project status through the sales pipeline.

**MCP tools to create:**
- `generate_proposal` — uses LLM to generate a proposal document from the project's WorkItems. Includes: scope summary, itemised pricing, terms, timeline. Creates a Document node with type "report".
- `update_project_status` — transitions project status (lead → quoted → active → complete → closed). Validates allowed transitions.

**Service work:**
- Create `backend/app/services/proposal_service.py` — assembles WorkItem data, calls LLM to generate formatted proposal text, stores as Document

**Frontend cards:**
- `ProposalCard` — project name, total value, status, generated date

### Get Paid

Invoice generation and payment tracking.

**MCP tools to create:**
- `generate_invoice` — creates an Invoice node from selected WorkItems or a percentage of project progress. Calculates amounts from WorkItem costs. Direction: "receivable".
- `track_payment_status` — lists outstanding invoices for a project with aging (days overdue)
- `record_payment` — records a Payment against an Invoice

**Service work:**
- `backend/app/services/invoice_service.py` exists from Phase 1 — wire into MCP tools
- Add invoice generation logic: select WorkItems by state, calculate amounts, create InvoiceLines with COVERS relationships

**Frontend cards:**
- `InvoiceCard` — invoice number, amount, status, due date, days until/overdue
- `PaymentStatusCard` — project invoiced total, paid total, outstanding, overdue amount

**Key files to read first:**
- backend/app/services/mcp_tools.py (existing tools — add new ones following same pattern)
- backend/app/services/work_item_service.py
- backend/app/services/work_package_service.py
- backend/app/services/invoice_service.py
- backend/app/services/contract_service.py
- backend/app/services/guardrails_service.py (register new tools)
- frontend/src/components/cards/ (existing card pattern from Phase 4)
- docs/knowledge-graph/03-entities-relationships.md (full ontology reference)

Register all new MCP tools in guardrails TOOL_ACTION_MAP and TOOL_SCOPE_MAP. create_work_item, update_work_item, add_item_to_work_item, generate_invoice, record_payment = LOW_RISK_WRITE. update_project_status = LOW_RISK_WRITE. All get/search tools = READ_ONLY.

Use maximum effort.
```

---

## Session F: Find & Qualify + Plan & Mobilise + Sub Management

Lead pipeline, scheduling, and subcontractor management.

```
You are building Phase 5 of Kerf — the contractor processes. Phases 1-4 are complete: full ontology migration, conversation persistence, document pipeline, and a conversational-first frontend shell.

Your job: build three areas — "Find & Qualify Work", "Plan & Mobilise", and cross-cutting "Sub Management" updates.

### Find & Qualify Work

Converting incoming leads into qualified projects.

**MCP tools to create** (add to backend/app/services/mcp_tools.py):
- `capture_lead` — creates a Project node with status "lead". Accepts: name, description, type, address, client contact info (creates Contact node if needed, links via CLIENT_IS).
- `qualify_project` — checks: does the company have workers with required certs for this project type? Is there crew capacity (no scheduling conflicts)? What's the GC's payment history (if known)?
- `check_capacity` — looks at current active projects, assigned workers, and upcoming schedule to assess whether the company can take on new work

**Service work:**
- Create `backend/app/services/lead_service.py` — lead capture, qualification checks via graph traversal
- `backend/app/services/contact_service.py` exists from Phase 1 — wire into lead capture

**Frontend cards:**
- `LeadCard` — project name, type, client, address, qualification status
- `CapacityCard` — active projects count, workers utilisation, upcoming availability

### Plan & Mobilise

Lightweight scheduling — 2-4 week rolling lookahead.

**MCP tools to create:**
- `get_schedule` — returns WorkItems with planned_start/end dates for a project, grouped by week
- `assign_workers` — assigns workers or crews to WorkItems (ASSIGNED_TO_WORKER / ASSIGNED_TO_CREW relationships)
- `detect_conflicts` — checks assigned workers' certifications expire before planned_end, equipment maintenance windows overlap, worker double-booked across projects

**Service work:**
- Create `backend/app/services/scheduling_service.py` — lookahead view assembly, conflict detection via graph traversal (Worker → ASSIGNED_TO_PROJECT → Project → HAS_WORK_ITEM → WorkItem with date ranges + Worker → HOLDS_CERT → Certification with expiry)
- `backend/app/services/work_item_service.py` has assign_worker/assign_crew — wire into tools

**Frontend cards:**
- `ScheduleCard` — week view, work items with assigned workers, status indicators
- `ConflictAlertCard` — conflict type, affected worker/equipment, dates, resolution suggestion

### Sub Management (cross-cutting updates)

The existing sub management services need new MCP tools for conversational access.

**MCP tools to create:**
- `check_sub_compliance` — for a sub company, checks: insurance certificates valid? Certs current? Safety performance score?
- `get_sub_performance` — calculates sub performance from graph: inspection pass rates, incident frequency, corrective action closure rates
- `list_subs` — lists subcontractor companies linked via GC_OVER relationship with compliance summary

**Service work:**
- `backend/app/services/gc_portal_service.py` exists — add performance scoring logic
- Insurance certificate status is already tracked — wire into compliance check tool

**Frontend cards:**
- `SubComplianceCard` — sub name, insurance status, cert status, performance score
- `SubPerformanceCard` — pass rates, incident rate, response times

**Key files to read first:**
- backend/app/services/mcp_tools.py (existing tools — add new ones following same pattern)
- backend/app/services/project_service.py
- backend/app/services/contact_service.py
- backend/app/services/work_item_service.py
- backend/app/services/worker_service.py
- backend/app/services/gc_portal_service.py
- backend/app/services/guardrails_service.py (register new tools)
- frontend/src/components/cards/ (existing card pattern from Phase 4)
- docs/knowledge-graph/03-entities-relationships.md (full ontology reference)

Register all new MCP tools in guardrails TOOL_ACTION_MAP and TOOL_SCOPE_MAP. capture_lead, assign_workers = LOW_RISK_WRITE. All check/get/list/detect tools = READ_ONLY.

Use maximum effort.
```
