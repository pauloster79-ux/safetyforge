# UI Restructure Spec: Full Contractor Lifecycle

**Status:** Approved for implementation
**Mockup:** `docs/mockups/ui-restructure.html` (open directly in browser)
**Date:** 2026-04-14

---

## Problem

Kerf expanded from a safety-focused app to a full contractor platform (lead → quote → execute → get paid). The backend and chat tools support the full lifecycle with 37 MCP tools, but the UI hasn't caught up:

1. **Icon rail is safety-heavy** — 4 of 10 items are safety (Inspections, Equipment, Incidents, Compliance). No entries for Schedule, Daily Logs, or Money.
2. **Project detail has no business tabs** — 10 tabs all focused on safety/execution. No way to see or manage work items, quotes, proposals, invoices, or schedule within a project.
3. **Financial workflows are chat-only** — Quotes, proposals, invoices, payments only surface as chat tool result cards. No dedicated UI pages.
4. **The "Contract" lifecycle is invisible** — A project goes from lead → quoted → active → close-out, but there's no tab that tracks this commercial journey.

---

## Changes

### 1. Restructure Icon Rail

Replace the current safety-centric navigation with a balanced lifecycle navigation.

**Current:**
Chat, Projects, Workers, Inspections, Equipment, Incidents, Documents, Compliance, Reports, Settings

**New:**

| # | ID | Label | Icon | Canvas Component | Change |
|---|-----|-------|------|-----------------|--------|
| 1 | chat | Chat | MessageSquare | (focuses chat) | Unchanged |
| 2 | projects | Projects | FolderKanban | ProjectListPage | Unchanged |
| 3 | schedule | Schedule | CalendarDays | ScheduleOverviewPage | **NEW** |
| 4 | daily-logs | Daily Logs | ClipboardList | DailyLogOverviewPage | **NEW** |
| 5 | workers | Workers | Users | WorkerListPage | Unchanged |
| 6 | equipment | Equipment | Wrench | EquipmentPage | Unchanged (no longer buried under safety) |
| 7 | safety | Safety | ShieldCheck | SafetyOverviewPage | **CONSOLIDATED** — replaces Inspections + Incidents + Compliance |
| 8 | documents | Documents | FileText | DocumentListPage | Unchanged |
| 9 | reports | Reports | BarChart3 | AnalyticsPage | Unchanged |
| 10 | settings | Settings | Settings | CompanySettingsPage | Unchanged |

**Key changes:**
- Inspections, Incidents, Compliance → collapsed into one "Safety" entry
- Added: Schedule, Daily Logs as top-level items
- Equipment stays standalone (it's operational, not just safety)
- Same 10 items, now reflecting the full product

**File:** `frontend/src/components/shell/IconRail.tsx`

### 2. Restructure Project Detail Tabs

Replace the 10 safety-centric tabs with 7 lifecycle-aware tabs.

**Current tabs:**
Overview, Inspections, Toolbox Talks, Hazards, Daily Logs, Incidents, Workers, Equipment, Documents, (Settings)

**New tabs:**

| Tab | Contents | Status |
|-----|----------|--------|
| **Overview** | KPI cards, project details, morning brief, recent activity | Keep (existing) |
| **Contract** | Lifecycle-aware tab — content changes based on project status (see below) | **NEW** |
| **Work** | Work items as schedule, worker assignments, conflict detection | **NEW** |
| **Daily Logs** | Daily log entries + time tracking | Keep (existing content) |
| **Safety** | Sub-sections: Inspections, Toolbox Talks, Hazards, Incidents | **CONSOLIDATED** from 4 tabs |
| **Team** | Workers + Equipment assigned to project | **CONSOLIDATED** from 2 tabs |
| **Documents** | Project documents | Keep (existing) |

**File:** `frontend/src/components/projects/ProjectDetailPage.tsx`

### 3. The Contract Tab (Key Design)

This is the most important new element. The Contract tab adapts its content based on the project's lifecycle stage:

#### Stage A: Lead / Quoting (status = lead)

Content:
- Work items table: description, hours, rate, materials cost, total, state badge (draft/approved)
- "Add Work Item" button
- Work package grouping (collapsible sections, optional)
- Bottom summary bar: Total Labour | Total Materials | Margin % | Quote Total
- "Generate Proposal" button (prominent, primary colour)

Purpose: Build the quote from work items, then generate a proposal to send to the client.

#### Stage B: Active / In Progress (status = active)

Content:
- Accepted Proposal card (date, reference, client)
- Contract Value displayed prominently
- Progress bar showing overall % complete
- Work items table with tracking columns: Est Hours | Actual Hours | % Complete | Est Cost | Actual Cost
- "Generate Progress Invoice" button

Purpose: Track execution against the quoted scope. See where you're over/under budget per work item.

#### Stage C: Close-out / Invoicing (status = completed or when invoices exist)

Content:
- Payment summary cards: Total Invoiced | Paid | Outstanding
- Invoice list table: Invoice # | Date | Amount | Status (draft/sent/paid/overdue) | Action
- Job cost comparison: Estimated vs Actual per work item with variance
- Variations/change orders section

Purpose: Get paid. Track what's been invoiced, what's been paid, what's outstanding.

**Implementation note:** The tab content switches based on `project.status` and the presence of invoices/proposals in the data. All three views use data from existing MCP tools (`get_estimate_summary`, `get_job_cost_summary`, `get_financial_overview`, `generate_invoice`, `track_payment_status`).

### 4. New Overview Pages (for Icon Rail)

These are cross-project dashboard views opened from the icon rail.

#### ScheduleOverviewPage
- This week's work items across all projects
- Worker assignments and availability
- Upcoming milestones

#### DailyLogOverviewPage  
- Today's log status for each active project (submitted / draft / missing)
- Crew counts and total hours
- Quick "Create Log" action per project

#### SafetyOverviewPage
- Open hazards count across all projects
- Upcoming inspections
- Recent incidents
- Expiring certifications
- Compliance scores by project

**These pages call existing backend endpoints** — no new API work needed. They aggregate data that currently exists per-project.

### 5. Update Chat Quick Actions

**Current:** New project, Daily log, Compliance, Projects
**New:** New project, New quote, Daily log, Money

**File:** `frontend/src/components/shell/ChatPane.tsx`

### 6. Contextual Action Buttons in Project Header

The action buttons in the top-right of the project detail should change based on project status:

| Status | Primary Action | Secondary Actions |
|--------|---------------|-------------------|
| Lead | New Quote | Qualify Lead |
| Quoted | — | Follow Up, Edit Proposal |
| Active | Record Time | New Inspection, Daily Log, Report Hazard |
| Completed | Generate Invoice | Close Out |

Currently all projects show safety-focused actions (New Inspection, Toolbox Talk, etc.) regardless of status.

---

## Files to Create / Modify

### Modify existing:
| File | Change |
|------|--------|
| `frontend/src/components/shell/IconRail.tsx` | Replace RAIL_ITEMS array |
| `frontend/src/components/shell/CanvasPane.tsx` | Register new page components |
| `frontend/src/components/projects/ProjectDetailPage.tsx` | Replace tab structure, add Contract/Work/Safety/Team tabs |
| `frontend/src/components/shell/ChatPane.tsx` | Update quick action buttons |
| `frontend/src/hooks/useShell.ts` | Update RailItem type union |

### Create new:
| File | Purpose |
|------|---------|
| `frontend/src/components/projects/ContractTab.tsx` | The lifecycle-aware Contract tab |
| `frontend/src/components/projects/WorkTab.tsx` | Schedule/assignment view |
| `frontend/src/components/projects/SafetyTab.tsx` | Consolidated safety (inspections + toolbox talks + hazards + incidents) |
| `frontend/src/components/projects/TeamTab.tsx` | Workers + equipment |
| `frontend/src/components/schedule/ScheduleOverviewPage.tsx` | Cross-project schedule dashboard |
| `frontend/src/components/daily-logs/DailyLogOverviewPage.tsx` | Daily log status dashboard |
| `frontend/src/components/safety/SafetyOverviewPage.tsx` | Safety dashboard |

### No backend changes needed
All data is already available via existing API endpoints and MCP tools. The frontend restructure is purely a UI/navigation change.

---

## Implementation Order

1. **Icon rail + useShell type** — quickest, sets the navigation structure
2. **Project detail tab restructure** — move existing tab content into Safety/Team consolidations
3. **Contract tab** — highest business value, the core lifecycle view
4. **Work tab** — schedule/assignment view
5. **Overview pages** — cross-project dashboards for new icon rail items
6. **Contextual action buttons** — status-aware header actions
7. **Chat quick actions** — minor update

---

## Verification

1. Icon rail shows 10 items with new labels and icons
2. Clicking each icon rail item opens the correct canvas page
3. Project detail shows 7 tabs: Overview, Contract, Work, Daily Logs, Safety, Team, Documents
4. Contract tab shows appropriate content for lead/active/completed projects
5. Safety tab consolidates inspections, toolbox talks, hazards, incidents with sub-navigation
6. Team tab shows workers and equipment side by side
7. All existing functionality is still accessible — nothing removed, only reorganised
8. Mockup at `docs/mockups/ui-restructure.html` matches the implementation

---

## Reference

- **Visual mockup:** `docs/mockups/ui-restructure.html` — interactive HTML, open in browser
- **Design system:** `frontend/src/index.css` — CSS custom properties
- **Current icon rail:** `frontend/src/components/shell/IconRail.tsx`
- **Current project detail:** `frontend/src/components/projects/ProjectDetailPage.tsx`
- **Canvas registry:** `frontend/src/components/shell/CanvasPane.tsx`
- **MCP tools (37):** `backend/app/services/mcp_tools.py`
- **Work item service:** `backend/app/services/work_item_service.py`
- **Work package service:** `backend/app/services/work_package_service.py`
