# Kerf Integration Testing — Full Contractor Lifecycle via Chat

## Session Purpose

Run a complete end-to-end exploratory test of Kerf's chat interface, simulating a real contractor using the system. Test every process from lead capture through to getting paid. Fix issues as you find them.

## Current State (as of 2026-04-13)

### What's Running
- **Backend**: FastAPI on :8000, auto-reload enabled, Neo4j bolt://localhost:7687 (neo4j/password)
- **Frontend**: Vite on :5173, HMR enabled
- **Neo4j**: Docker container `neo4j-test`, 949 nodes, 10 golden companies seeded
- **Demo mode**: Login → "Try Demo" → sets demo-token + company comp_gp04 (Pacific Coast Construction)

### What's Been Fixed This Session
1. Documents sort crash (Cypher `-updated_at` → `updated_at:desc`)
2. Project card navigation (now uses `shell.openCanvas()` instead of `navigate()`)
3. ProjectDetailPage accepts `projectId` as prop for canvas rendering
4. Optional chaining on `trade_types`, `alerts`, `attendees`, `items`
5. Inspection/toolbox talk/hazard report Cypher ORDER BY bugs
6. Toolbox talk `custom_points` list→string conversion
7. **27 missing MCP tool schemas added to GENERAL_TOOLS** (37/37 tools now callable)
8. ProjectStatus enum expanded: added `lead`, `quoted`, `closed`
9. StatusBadge supports all project statuses with colour coding
10. Icon rail expanded: 10 items (Chat, Projects, Workers, Inspections, Equipment, Incidents, Documents, Compliance, Reports, Settings)
11. `query_graph` tool results hidden from chat cards (debug noise)
12. Conversation context recovery from Neo4j (survives backend restarts)
13. Deprecated `claude-3-5-haiku` model → `claude-haiku-4-5-20251001`

### Known Issues Going In
- **Backend `--reload` wipes in-memory sessions** — conversation recovery from Neo4j is now implemented but hasn't been fully tested
- **Chat system prompt scoping** — Claude sometimes uses `query_graph` for open questions instead of intent-based tools. The system prompt in `_build_system_prompt()` should tell Claude to prefer the 37 intent-based tools and only fall back to `query_graph` for truly ad-hoc queries
- **`query_graph` doesn't scope to company** — Claude's ad-hoc Cypher queries don't always include `company_id` filter, so results may leak across tenants. The `_handle_query_graph` method should inject the company filter.
- **Memory extraction service** uses LLM to extract decisions/insights — may fail if API is overloaded
- **Test database shared** — running `pytest` will wipe all golden data. Don't run tests during this session.

### Key Files
- `backend/app/services/chat_service.py` — Claude integration, GENERAL_TOOLS (37 tools), stream_response, system prompt
- `backend/app/services/mcp_tools.py` — all 37 MCP tool implementations
- `backend/app/services/guardrails_service.py` — tool action/scope classification
- `frontend/src/components/shell/ChatPane.tsx` — chat UI, card rendering, markdown
- `frontend/src/components/cards/CardRenderer.tsx` — maps tool names → card components
- `frontend/src/hooks/useShell.ts` — shell state, canvas navigation
- `frontend/src/components/shell/IconRail.tsx` — navigation rail (10 items)

---

## How to Start

```bash
# Neo4j should already be running. If not:
make neo4j-up

# Check golden data exists:
cd backend && python -c "
from app.services.neo4j_client import get_sync_driver
d = get_sync_driver()
with d.session() as s:
    r = s.run('MATCH (n) RETURN count(n) AS total')
    print(f'Total nodes: {r.single()[\"total\"]}')
"
# Should be ~949. If 0, run: cd .. && python -m backend.fixtures.golden.seed_all

# Start servers (use preview_start for both):
# backend config and frontend config are in .claude/launch.json
```

Open http://localhost:5173, click "Try Demo — No Account Needed".

---

## Test Script: Full Contractor Lifecycle

You are Marco, owner of Pacific Coast Construction (comp_gp04). You have one active project (Hillside Custom Residence) and one lead (Oster Kitchen). Test each step via the chat interface. After each chat message:

1. Check backend logs for errors (`preview_logs` with `level: error`)
2. Check that the right MCP tool was called (look for tool badge in chat)
3. Check that a card renders (or text response is correct)
4. Check no JS console errors
5. If something breaks, fix it before moving on

### Phase 1: Verify Existing Data

Send these chat messages one by one:

1. **"Show me a project summary for Hillside"**
   - Expected tool: `get_project_summary`
   - Expected card: ProjectSummaryCard with project name, workers, status
   - Check: real data from Neo4j (12 workers, active, residential)

2. **"How many workers do we have?"**
   - Expected: Should use `query_graph` or respond from context
   - Check: 12 workers for GP04

3. **"Check compliance for the Hillside project"**
   - Expected tool: `check_project_compliance`
   - Expected card: ComplianceStatusCard
   - Check: lists worker compliance status, cert gaps

4. **"Give me the morning brief for Hillside"**
   - Expected tool: `generate_morning_brief`
   - Expected card: MorningBriefCard with risk score, alerts
   - Check: real inspection/incident data populates

5. **"Show me today's daily log status for Hillside"**
   - Expected tool: `get_daily_log_status`
   - Check: shows which dates have/haven't been submitted

### Phase 2: Lead → Qualified Project

6. **"I've got a new lead — the Wilson Deck project. It's a deck extension at 23 Maple Drive for Sarah Wilson. Residential job."**
   - Expected tool: `capture_lead`
   - Expected card: LeadCard with project name, client, address, status "Lead"
   - Check: project created in Neo4j, visible in Projects list

7. **"Qualify the Wilson Deck project"**
   - Expected tool: `qualify_project`
   - Check: qualification assessment (certs, capacity, etc.)

8. **"Do we have capacity to take on new work?"**
   - Expected tool: `check_capacity`
   - Expected card: CapacityCard
   - Check: shows active project count, worker utilisation

### Phase 3: Estimate & Price

9. **"Create a work item for Wilson Deck: Remove existing deck structure, 16 hours at $75/hr"**
   - Expected tool: `create_work_item`
   - Expected card: WorkItemCard
   - Check: work item created with correct hours/rate

10. **"Add another work item: Build new composite deck, 40 hours at $85/hr, $3200 materials"**
    - Expected tool: `create_work_item`
    - Check: second work item created

11. **"Show the estimate summary for Wilson Deck"**
    - Expected tool: `get_estimate_summary`
    - Expected card: EstimateSummaryCard with labour + materials + total
    - Check: totals match (16×75 + 40×85 + 3200 = $7,800)

12. **"Search for historical rates on deck work"**
    - Expected tool: `search_historical_rates`
    - Check: returns results (may be empty if no past deck projects)

### Phase 4: Propose & Win

13. **"Generate a proposal for the Wilson Deck project"**
    - Expected tool: `generate_proposal`
    - Expected card: ProposalCard
    - Check: includes scope, pricing, terms

14. **"Update Wilson Deck status to quoted"**
    - Expected tool: `update_project_status`
    - Check: status changes from "lead" to "quoted"
    - Then: **"Update it to active"** — check transition works

### Phase 5: Plan & Mobilise

15. **"Show the schedule for Wilson Deck"**
    - Expected tool: `get_schedule`
    - Expected card: ScheduleCard
    - Check: shows work items with dates (may be empty initially)

16. **"Check for scheduling conflicts on Wilson Deck"**
    - Expected tool: `detect_conflicts`
    - Expected card: ConflictAlertCard (or "no conflicts" message)

### Phase 6: Execute & Document

17. **"Create a daily log for Wilson Deck for today"**
    - Expected tool: `create_daily_log`
    - Expected card: DailyLogCard
    - Check: daily log created with today's date

18. **"Auto-populate today's daily log for Wilson Deck"**
    - Expected tool: `auto_populate_daily_log`
    - Check: pulls in any available data (may be sparse for new project)

19. **"Record time: Omar Vasquez clocked in at 7am, out at 3:30pm on the deck removal work item"**
    - Expected tool: `record_time`
    - Expected card: TimeEntryCard
    - This requires knowing the work item ID — Claude should look it up or ask

20. **"Report a quality observation: deck framing is square and level, all connections tight"**
    - Expected tool: `report_quality_observation`
    - Expected card: QualityCard

### Phase 7: Manage Money

21. **"Show job cost summary for Wilson Deck"**
    - Expected tool: `get_job_cost_summary`
    - Expected card: JobCostCard
    - Check: shows actual vs estimated costs

22. **"Are there any variations on Wilson Deck?"**
    - Expected tool: `detect_variation`
    - Expected card: VariationCard (or "no variations" message)

23. **"Show the financial overview for Wilson Deck"**
    - Expected tool: `get_financial_overview`
    - Expected card: FinancialOverviewCard

### Phase 8: Get Paid

24. **"Generate an invoice for Wilson Deck — 50% progress"**
    - Expected tool: `generate_invoice`
    - Expected card: InvoiceCard
    - Check: amount = 50% of estimate total

25. **"Show payment status for Wilson Deck"**
    - Expected tool: `track_payment_status`
    - Expected card: PaymentStatusCard

### Phase 9: Sub Management

26. **"List our subcontractors"**
    - Expected tool: `list_subs`
    - Expected card: SubComplianceCard (or "no subs" message)

### Phase 10: Conversation Context

27. **Start a new conversation flow (click "New chat"):**
    - "Show me the Hillside project" → get_project_summary
    - "How many workers are on it?" → should use context (Hillside) without re-asking
    - "Any expiring certs?" → should scope to Hillside workers
    - "What about the Wilson Deck project?" → should switch context
    - "Compare the two projects" → should have both in context

### Phase 11: Cross-Cutting Safety

28. **"Check worker compliance for Omar Vasquez"**
    - Expected tool: `check_worker_compliance`
    - Needs project context — should ask or use active project

29. **"Report a hazard on Hillside: loose scaffolding brackets on level 2, north face"**
    - Expected tool: `report_hazard`
    - Check: hazard created in Neo4j

### Phase 12: Canvas Integration

30. Navigate via icon rail to each section and verify real data loads:
    - Projects → both Hillside and Wilson Deck visible
    - Workers → 12 GP04 workers
    - Inspections → GP04 inspections listed
    - Equipment → GP04 equipment
    - Incidents → GP04 incidents
    - Documents → empty (correct)

---

## What to Fix as You Go

Common failure patterns and how to fix:

| Symptom | Likely cause | Fix location |
|---------|-------------|--------------|
| Claude asks for project_id instead of using context | System prompt doesn't tell Claude about conversation context | `chat_service.py:_build_system_prompt()` |
| Tool returns error about missing company_id | MCP tool not receiving company_id | `chat_service.py:_handle_tool_call()` or `mcp_tools.py` method signature |
| Card shows "—" for all fields | Card component reads wrong property names | `frontend/src/components/cards/{ToolCard}.tsx` |
| "Unknown tool" error | Tool name not in dispatch map | `mcp_tools.py:invoke_tool()` dispatch dict |
| Pydantic validation error | Model doesn't match Neo4j data shape | `backend/app/models/*.py` or service `_to_model()` |
| query_graph used instead of intent tool | System prompt not specific enough | `chat_service.py:_build_system_prompt()` — add explicit preference |
| Conversation context lost | Backend restarted (--reload) | Should auto-recover from Neo4j now |
| Card type mismatch | CardRenderer doesn't map tool name | `frontend/src/components/cards/CardRenderer.tsx` |

## Deliverable

After completing all test phases, update `docs/workflow/go-live-test-results.md` with:
- Each test step: PASS / FAIL / FIXED (with what was fixed)
- List of remaining issues that couldn't be fixed
- Updated go/no-go recommendation

## Important Reminders

- **Do NOT run pytest** — it will wipe the Neo4j database
- **Backend --reload** will clear in-memory sessions, but conversation recovery from Neo4j should restore context
- If Anthropic API returns `overloaded_error`, wait and retry — it's transient
- The frontend is at http://localhost:5173 — use preview_start for both "backend" and "frontend" from .claude/launch.json
- Golden data must exist: ~949 nodes. If it's 0, run `python -m backend.fixtures.golden.seed_all` from the repo root
