# Session Prompt: UI Restructure — Full Contractor Lifecycle

## Context

The backend quoting infrastructure is complete. Pydantic models, Neo4j services, API endpoints, and MCP chat tools all exist and are tested. The chat can create work items, labour, items, assumptions, exclusions, and generate proposals. But the frontend hasn't caught up — there's no visual UI for any of this. The approved UI restructure spec defines what to build.

## Before You Start

Read these files in order:

1. `docs/specs/UI_RESTRUCTURE_SPEC.md` — the approved spec (implementation order, file list, all details)
2. `docs/mockups/ui-restructure.html` — open in browser, this is the visual target
3. `docs/workflow/handoff-quoting-ontology.md` — design decisions (state vs status, entities as graph nodes, no separate Quote entity)
4. `docs/architecture/CONSTRUCTION_ONTOLOGY.md` — Domain 16 (Work Structure) and Domain 17 (Quoting) for entity details

Then read these existing files to understand current patterns:

5. `frontend/src/components/shell/IconRail.tsx` — current icon rail (to restructure)
6. `frontend/src/components/shell/CanvasPane.tsx` — canvas registry (to add new pages)
7. `frontend/src/components/projects/ProjectDetailPage.tsx` — current 10-tab layout (to restructure into 7 tabs)
8. `frontend/src/hooks/useShell.ts` — RailItem type union (to update)
9. `frontend/src/components/shell/ChatPane.tsx` — quick actions (to update)
10. `frontend/src/lib/constants.ts` — Project interface (already updated with state/status split)
11. `frontend/src/hooks/useProjects.ts` — project hooks (already updated with state param)

## What Was Built in the Previous Session (Backend)

### New API Endpoints (all working, tested)

**Labour** (nested under work items):
- `GET/POST /me/projects/{pid}/work-items/{wid}/labour`
- `GET/PATCH/DELETE /me/projects/{pid}/work-items/{wid}/labour/{lid}`

**Items** (nested under work items):
- `GET/POST /me/projects/{pid}/work-items/{wid}/items`
- `GET/PATCH/DELETE /me/projects/{pid}/work-items/{wid}/items/{iid}`

**Assumptions** (project-scoped + company templates):
- `GET/POST /me/projects/{pid}/assumptions`
- `GET/PATCH/DELETE /me/projects/{pid}/assumptions/{aid}`
- `POST /me/projects/{pid}/assumptions/from-template/{tid}`
- `GET/POST /me/assumption-templates`

**Exclusions** (project-scoped + company templates):
- `GET/POST /me/projects/{pid}/exclusions`
- `GET/PATCH/DELETE /me/projects/{pid}/exclusions/{eid}`
- `POST /me/projects/{pid}/exclusions/from-template/{tid}`
- `GET/POST /me/exclusion-templates`

**Resource Rates** (company level):
- `GET/POST /me/rates`
- `GET/PATCH /me/rates/{rid}`
- `POST /me/rates/{rid}/deactivate`
- `GET /me/rates/derive/{resource_type}`

**Productivity Rates** (company level):
- `GET/POST /me/productivity-rates`
- `GET/PATCH /me/productivity-rates/{rid}`
- `POST /me/productivity-rates/{rid}/deactivate`

### Updated MCP Chat Tools

These tools work via the chat panel and create real graph data:
- `create_work_item` — creates WorkItem with quantity/unit (no flat labour props)
- `create_labour` — creates Labour child node (rate_cents, hours, cost_cents)
- `create_item` — creates Item child node (quantity, unit_cost_cents, total_cents)
- `update_work_item` — updates and recalculates totals from children
- `add_assumption` — creates Assumption on project (category, statement, variation_trigger)
- `add_exclusion` — creates Exclusion on project (category, statement)
- `list_assumption_templates` — browse company templates
- `list_exclusion_templates` — browse company templates
- `get_estimate_summary` — returns Labour/Item cost rollup + assumption/exclusion counts
- `generate_proposal` — assembles proposal with work items + assumptions + exclusions
- `update_project_status` / `update_project_state` — transition lifecycle state
- `search_historical_rates` — returns historical items + ResourceRates + ProductivityRates

### Project Model Change (Already Done)

The Project model now has two fields:
- **`state`**: lifecycle stage — lead | quoted | active | completed | closed | lost
- **`status`**: operating condition — normal | on_hold | delayed | suspended

The `Project` interface in `frontend/src/lib/constants.ts` is already updated. The project list page filter sends `?state=` (not `?status=`). The `StateBadge` component uses `project.state`. All existing Neo4j data has been migrated.

### Golden Project Seed Data (GP04)

GP04 (Hillside Custom Residence) has realistic quoting data:
- 5 WorkItems with 11 Labour tasks and 13 Items (electrical work)
- 10 ResourceRates (journeyman $150/hr, apprentice $120/hr, materials)
- 3 ProductivityRates (conduit, receptacles, panels)
- 6 Assumption templates + 5 Exclusion templates (company library)

Other golden projects (GP01-GP03, GP05-GP10) have `state: active, status: normal` but no quoting data.

### All Monetary Values Are in Cents

The backend stores everything in integer cents. The frontend must format for display:
- `rate_cents: 15000` → display as `$150.00`
- `cost_cents: 180000` → display as `$1,800.00`
- `total_cents: 85000` → display as `$850.00`
- `sell_price_cents: 448500` → display as `$4,485.00`

## What to Build

Follow the implementation order from the spec:

### Phase 1: Icon Rail + useShell Type
- Replace RAIL_ITEMS in `IconRail.tsx` with the new 10-item lifecycle navigation
- Update `useShell.ts` RailItem type union
- Register placeholder pages in `CanvasPane.tsx`

### Phase 2: Project Detail Tab Restructure
- Replace 10 tabs with 7: Overview, Contract, Work, Daily Logs, Safety, Team, Documents
- Create `SafetyTab.tsx` — move inspections, toolbox talks, hazards, incidents content
- Create `TeamTab.tsx` — move workers + equipment content
- Keep Overview and Documents as-is
- Keep Daily Logs as-is

### Phase 3: Contract Tab (Highest Business Value)
- Create `ContractTab.tsx` with three stage views:
  - **Stage A (lead/quoted)**: Work items table with labour/items breakdown, summary bar, "Generate Proposal" button
  - **Stage B (active)**: Contract value, progress tracking, est vs actual
  - **Stage C (completed)**: Invoice list, payment tracking, job cost comparison
- Work items table columns: Description, Qty, Unit, Labour Cost, Items Cost, Margin %, Sell Price
- Expandable rows showing Labour and Item children
- Bottom summary bar: Total Labour | Total Items | Margin | Quote Total
- Assumptions and Exclusions sections below the work items table

### Phase 4: Work Tab
- Work items as a schedule view
- Worker assignments
- This can be simpler initially — a table view is fine

### Phase 5: Overview Pages
- `ScheduleOverviewPage.tsx` — cross-project work items this week
- `DailyLogOverviewPage.tsx` — today's log status per project
- `SafetyOverviewPage.tsx` — open hazards, upcoming inspections, expiring certs

### Phase 6: Contextual Action Buttons
- Project header actions change based on `project.state`
- Lead: "New Quote" | Quoted: "Follow Up" | Active: "Record Time" | Completed: "Generate Invoice"

### Phase 7: Chat Quick Actions
- Update quick actions: New project, New quote, Daily log, Money

## New React Hooks Needed

Create these hooks to fetch data from the new endpoints:

```typescript
// useWorkItems(projectId) — GET /me/projects/{pid}/work-items (already exists but needs Labour/Item children)
// useLabour(projectId, workItemId) — GET /me/projects/{pid}/work-items/{wid}/labour
// useItems(projectId, workItemId) — GET /me/projects/{pid}/work-items/{wid}/items
// useAssumptions(projectId) — GET /me/projects/{pid}/assumptions
// useExclusions(projectId) — GET /me/projects/{pid}/exclusions
// useResourceRates() — GET /me/rates
// useProductivityRates() — GET /me/productivity-rates
// useEstimateSummary(projectId) — calls the MCP tool endpoint or direct API
```

## Key Constraints

- All monetary display: divide cents by 100, format with `$` and 2 decimal places
- Follow existing component patterns (shadcn/ui, Tailwind, design tokens from index.css)
- The Contract tab switches content based on `project.state`, NOT `project.status`
- The demo token (`Bearer demo-token`) authenticates as `demo_user_001` on company `comp_gp04`
- GP04 project ID is `proj_gp04` — this is the project with quoting data for testing
- Read the mockup HTML file for visual reference before writing any components

## What NOT to Do

- Do NOT change backend models, services, or API endpoints — they are complete
- Do NOT modify MCP tools or chat service — they are working
- Do NOT change the golden project seed data
- Do NOT remove any existing functionality — only reorganise
- Do NOT build new backend endpoints — all data is already available

## Verification

After implementation, test by:
1. Opening http://localhost:5174 — icon rail should show 10 lifecycle items
2. Click into Hillside Custom Residence project — should show 7 tabs
3. Click Contract tab — should show Stage A (quoting) view with 5 work items
4. Expand a work item row — should show Labour and Item children with costs
5. Bottom summary bar should show total ~$39,910
6. Assumptions and Exclusions sections should be visible (empty until added via chat)
7. Open chat, type "Add an assumption that the programme is 19 weeks" — assumption should appear in Contract tab
8. Safety tab should consolidate inspections, toolbox talks, hazards, incidents
9. Team tab should show workers and equipment
