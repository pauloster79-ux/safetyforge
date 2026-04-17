# Phase 0 — Platform Foundations (Design Doc)

**Status**: Draft for review
**Author**: Claude + Paul
**Date**: 2026-04-15
**Scope**: Foundational cross-cutting capabilities that every subsequent feature depends on. Not a formal TDD spec — intentionally lightweight. No adversarial review. Acceptance by Paul's sign-off.

---

## 1. Purpose

Phase 0 delivers four platform capabilities that every other feature leverages:

| # | Capability | What it unlocks |
|---|-----------|-----------------|
| 0.1 | Activity Stream | Any entity detail page shows a chronological timeline of everything that happened to it |
| 0.2 | Actor & Provenance Display | Every UI surface shows who did what (human vs agent, with confidence/model/cost where relevant) |
| 0.3 | Audit Trail | Every mutation and state transition is captured as an immutable event in the graph |
| 0.4 | Graph Query Canvas | Saved queries page that surfaces the graph's intelligence (compliance, cost, schedule, safety) without a custom page per question |

These are built **before** Phase 1 (chat quoting) so every subsequent feature emits audit events from day one and benefits from the reusable UI primitives. Retrofitting later means migrating data across 15+ domains.

---

## 2. Why now

Current symptoms that Phase 0 addresses:

- Provenance fields (`actor_type`, `agent_id`, `confidence`, `model_id`) are stamped on every node via [BaseService](../../backend/app/services/base_service.py) but **never surfaced to the UI**. Users cannot tell "Compliance Agent (0.92)" from "John (human)" on any page.
- `model_id` and `confidence` are stamped as `None` in `_provenance_create()` — agent-produced entities don't actually record which model or what confidence. Cost attribution is impossible today.
- State changes on WorkItems, Projects, DailyLogs, Incidents are invisible. A project moves LEAD → QUOTED → ACTIVE → COMPLETED with zero record of when, why, or who triggered each transition.
- The graph holds answers to questions like "workers without current OSHA-10 on a project with trenching scheduled next week" but there's no UI to ask them, so the intelligence is invisible.
- Every entity detail page today is a static form. Opening a Worker shows certifications but not the incidents they were involved in, toolbox talks they attended, inspections they appeared on, or time entries they logged.

---

## 3. Design Decisions

### 3.1 AuditEvent as a graph node (not separate log store)

Decision: **Model audit events as nodes in Neo4j**, not as rows in a separate log DB.

```
(Entity)-[:EMITTED]->(AuditEvent)-[:PERFORMED_BY]->(AgentIdentity?)
         [:AFFECTED_BY]         [:CAUSED_BY]->(AuditEvent?)
```

**Why**:
- Queries like "show everything that happened to this WorkItem" become single traversals
- Activity streams for a Project can aggregate events across all child entities via existing relationships
- Consistent with the rest of the architecture (graph-native permissions, no parallel data store)
- Supports future A2A event emission — each AuditEvent can be published to an event backbone if/when we add one (Phase 4+)

**Trade-offs**:
- Neo4j is not optimised for append-only high-volume event storage. At scale (hundreds of events/minute across tenants) we may need to archive old events. Not a concern until we hit that volume — add a retention job later.
- Indexed properly, queries for "last 30 days of events for entity X" are fast.

**Rejected alternative**: Separate Postgres/ClickHouse event store. Adds a second system to keep consistent, complicates cross-domain queries, doesn't benefit us until event volume is much higher.

### 3.2 AuditEvent schema

```cypher
(:AuditEvent {
  id: string,                      // evt_<16hex>
  event_type: string,              // "entity.created" | "entity.updated" | "state.transitioned" | "entity.archived" | "field.changed"
  entity_id: string,               // ID of the entity this event concerns
  entity_type: string,             // "WorkItem" | "Project" | "Inspection" | ...
  occurred_at: datetime,           // UTC timestamp
  company_id: string,              // denormalised for tenant-scoped queries

  // Actor (who did it)
  actor_type: "human" | "agent",
  actor_id: string,                // user_id or agent_id
  agent_id: string?,               // set when actor_type = "agent"
  agent_version: string?,
  model_id: string?,
  confidence: float?,              // 0.0-1.0 for agent actions
  cost_cents: integer?,            // token cost for agent actions

  // Payload (what changed)
  summary: string,                 // human-readable one-liner ("Moved to Active", "Updated margin from 15% to 18%")
  changes: json?,                  // { "field": { "from": X, "to": Y } } — nullable for non-update events
  prev_state: string?,             // for state.transitioned events
  new_state: string?,              // for state.transitioned events

  // Causal chain (optional)
  caused_by_event_id: string?,     // links to the AuditEvent that triggered this one (e.g. agent action → cascading updates)

  // Related entities
  related_entity_ids: [string]?    // additional entities referenced (e.g. a WorkItem.assignWorker event references the Worker)
})
```

Relationships:
- `(Entity)-[:EMITTED]->(AuditEvent)` — primary relationship, one per event
- `(AuditEvent)-[:PERFORMED_BY]->(AgentIdentity)` — when actor is an agent
- `(AuditEvent)-[:AFFECTED {role: "secondary"}]->(Entity)` — for events touching multiple entities
- `(AuditEvent)-[:CAUSED_BY]->(AuditEvent)` — causal chain

Indexes:
- `AuditEvent(entity_id, occurred_at DESC)` — primary query path
- `AuditEvent(company_id, occurred_at DESC)` — company-wide timelines
- `AuditEvent(event_type)`
- `AuditEvent(actor_id, occurred_at DESC)` — "everything Agent X did"

### 3.3 Emission strategy: BaseService hook

Decision: **Add `_emit_audit()` to BaseService**, call it from every mutation method in subclasses. Explicit, not magic.

```python
# In BaseService
def _emit_audit(
    self,
    event_type: str,
    entity_id: str,
    entity_type: str,
    company_id: str,
    actor: Actor,
    summary: str,
    changes: dict | None = None,
    prev_state: str | None = None,
    new_state: str | None = None,
    related_entity_ids: list[str] | None = None,
    caused_by_event_id: str | None = None,
) -> str:
    """Emit an AuditEvent node linked to the entity. Returns event_id."""
```

**Why explicit over a magic interceptor**:
- Each service knows what "summary" means for its domain ("Moved WorkItem to in_progress", not "Updated WorkItem.state")
- Prevents emitting events for non-semantic updates (e.g. `updated_at` touch)
- Simpler to debug — the emit call is visible in the service code
- Easier to get the changes payload right without reflection hacks

**Cost**: adds one write per mutation. Acceptable — Neo4j transactions can batch the entity write and the event write in a single Cypher query.

**Rejected alternative**: Auto-emission via a Neo4j trigger or a repository pattern that captures all writes. Too much magic; would generate noise for internal-only field updates.

### 3.4 Activity Stream: one component, per-entity adapter

Decision: **A single `<ActivityStream entityType entityId />` React component** that:

1. Calls a single endpoint: `GET /entities/{type}/{id}/activity?limit=50&before=<timestamp>`
2. Backend endpoint executes a domain-aware traversal (different entity types have different "related" events to aggregate — e.g. a Project stream includes events on its child WorkItems, Inspections, Incidents, DailyLogs)
3. Returns a unified event list with consistent schema
4. Component renders as a vertical timeline with:
   - Entity icon + event summary
   - Actor badge (human/agent with confidence chip if agent)
   - Relative timestamp
   - Expandable details (diff view for field changes, full payload for state transitions)

**Domain-aware traversal examples**:
- Project activity = AuditEvents directly on Project + AuditEvents on Project's WorkItems + Inspections + Incidents + DailyLogs + ToolboxTalks
- WorkItem activity = AuditEvents directly on WI + AuditEvents on child Labour/Item nodes + TimeEntries logged against it
- Worker activity = AuditEvents directly on Worker + Inspections they appeared on + Incidents involving them + Certifications added/expired + TimeEntries logged

These traversals live in a new `audit_service.py` with one method per entity type. Keeps the Cypher in one place; frontend is dumb.

**First integrations**: Project, Worker, WorkItem detail pages (in that order). The other 4 existing detail pages (Equipment, Incident, Inspection, ToolboxTalk, DailyLog) follow as small additions.

### 3.5 Provenance Display: three variants

Decision: **Single `<ProvenanceBadge />` component with three visual variants**, used everywhere an entity or event appears.

```tsx
<ProvenanceBadge
  actorType="agent"          // "human" | "agent"
  actorId="agent_compliance"
  actorName="Compliance Agent"   // resolved display name
  agentVersion="1.2.0"            // optional
  confidence={0.92}               // optional, agents only
  modelId="claude-sonnet-4-6"     // optional, agents only
  timestamp="2026-04-15T14:30:00Z"
  variant="inline | card | full"
/>
```

**Variants**:
- `inline` — single-line chip next to entity names in list rows. "🤖 Compliance Agent · 0.92"
- `card` — two-line version on detail page headers. Shows "Created by X at Y" + "Last updated by Z at W".
- `full` — expanded panel on hover or in a detail drawer. All provenance fields + cost + duration if available.

**Color coding**: humans = neutral gray; agents = brand accent (blue/teal). Confidence < 0.7 renders a warning icon.

**Provenance field population** (critical fix as part of this work):
- `model_id` and `confidence` are currently `None` placeholders. Agents that produce outputs must record them.
- Add an `AgentActor` variant to `Actor` with `model_id` and `confidence` fields.
- Audit: every service that creates entities via agent input currently calls `Actor.human(user_id)` when the actual actor is the agent — must be corrected to `Actor.agent(agent_id, ...)` with model/confidence.

### 3.6 Graph Query Canvas: server-defined saved queries

Decision: **Saved queries are Python functions on the server**, exposed via `GET /queries` (list) and `POST /queries/{id}/run` (execute). Not user-authored Cypher — we don't expose Cypher injection risk.

**Canvas UX**:
- Route: `/queries`
- Left panel: saved queries grouped by category (Compliance, Cost, Schedule, Safety, Subs, Workforce)
- Right panel: selected query's description, parameter form, "Run" button
- Results render as a sortable/filterable data table
- Each row has click-through to the relevant entity detail page

**Query definition (server side)**:
```python
@register_query(
    id="compliance.workers_missing_cert",
    category="compliance",
    title="Workers missing a required certification",
    description="List workers on active projects who lack a certification required for their assigned trade.",
    parameters=[
        {"name": "cert_type_id", "type": "certification_type", "required": True},
        {"name": "project_id", "type": "project", "required": False},
    ],
)
def workers_missing_cert(company_id: str, cert_type_id: str, project_id: str | None):
    # Returns list of dicts with worker_id, worker_name, trade, last_cert_expiry, project_name
    ...
```

**Starter query set** (ship with 20-25 queries covering):
- **Compliance**: workers missing cert type, certs expiring in N days, open corrective actions past due, projects with overdue safety reviews
- **Cost**: work items over estimate, projects by margin variance, top 10 most expensive work items, labour cost by trade
- **Schedule**: work items starting this week, overdue work items, work items with no assigned worker/crew, next 7 days lookahead
- **Safety**: incidents in last 30 days by severity, hazard reports unclosed > 7 days, inspections with any failed items, workers in multiple incidents
- **Subs (for GCs)**: subs with COI expiring in 30 days, subs with lowest inspection pass rate, subs with open payment releases
- **Workforce**: workers approaching fatigue threshold (10+ hrs), workers with no time entry in N days, crews without a foreman

Each query's definition includes the columns it returns and their types so the table can be rendered without per-query UI code.

---

## 4. Data Schema Changes

### New node labels
- `AuditEvent` (schema in §3.2)

### Updated fields on existing nodes
- None — provenance fields already exist on all tenant-scoped entities

### New relationships
- `(Entity)-[:EMITTED]->(AuditEvent)`
- `(AuditEvent)-[:PERFORMED_BY]->(AgentIdentity)`
- `(AuditEvent)-[:AFFECTED]->(Entity)`
- `(AuditEvent)-[:CAUSED_BY]->(AuditEvent)`

### New indexes
```cypher
CREATE CONSTRAINT constraint_audit_event_id IF NOT EXISTS
  FOR (n:AuditEvent) REQUIRE n.id IS UNIQUE;
CREATE INDEX index_audit_event_entity IF NOT EXISTS
  FOR (n:AuditEvent) ON (n.entity_id, n.occurred_at);
CREATE INDEX index_audit_event_company IF NOT EXISTS
  FOR (n:AuditEvent) ON (n.company_id, n.occurred_at);
CREATE INDEX index_audit_event_type IF NOT EXISTS
  FOR (n:AuditEvent) ON (n.event_type);
CREATE INDEX index_audit_event_actor IF NOT EXISTS
  FOR (n:AuditEvent) ON (n.actor_id);
```

### Backfill strategy for existing entities
- Existing entities have `created_by` / `created_at` / `updated_by` / `updated_at` already stamped
- One-time script: for each existing entity, emit an `entity.created` AuditEvent using the stamped fields. Gives us a starting timeline.
- Only worth running for tenant-scoped entities (not regulatory nodes).

---

## 5. Backend Implementation Outline

### New files
- `backend/app/models/audit_event.py` — Pydantic models
- `backend/app/services/audit_service.py` — emission + query traversals (per-entity-type methods)
- `backend/app/services/query_canvas_service.py` — registered saved queries + execution
- `backend/app/routers/audit.py` — `/entities/{type}/{id}/activity` endpoint
- `backend/app/routers/queries.py` — `/queries` list and `/queries/{id}/run` execute
- `backend/graph/migrations/add_audit_events.cypher` — schema additions
- `backend/graph/migrations/backfill_audit_events.cypher` — one-time backfill

### Changes to existing files
- `backend/app/services/base_service.py` — add `_emit_audit()` helper
- Every service that mutates entities — add `_emit_audit()` calls at the end of each mutation method. Primarily `work_item_service`, `project_service`, `inspection_service`, `incident_service`, `daily_log_service`, `toolbox_talk_service`, `hazard_report_service`, `equipment_service`, `worker_service`. ~15 services, 1-3 call sites each.
- `backend/app/models/actor.py` — add optional `model_id` and `confidence` fields for agent actors
- Services that create entities via agent input — switch from `Actor.human()` to `Actor.agent()` with recorded model_id/confidence

### Not building in Phase 0
- Event backbone / pub-sub (Kafka/Redis Streams) — not needed until we have reactive agents consuming events from other agents. Add in Phase 4 when warranted.
- Tenant-partitioned audit retention/archival — add when event volume requires it.

---

## 6. Frontend Implementation Outline

### New files
- `frontend/src/components/shared/ActivityStream.tsx` — timeline component
- `frontend/src/components/shared/ProvenanceBadge.tsx` — three-variant badge
- `frontend/src/components/queries/QueryCanvasPage.tsx` — main page
- `frontend/src/components/queries/QueryList.tsx` — left panel
- `frontend/src/components/queries/QueryRunner.tsx` — parameter form + results table
- `frontend/src/hooks/useActivityStream.ts`
- `frontend/src/hooks/useSavedQueries.ts`

### Changes to existing files
- `ProjectDetailPage.tsx` — embed `<ActivityStream />` + `<ProvenanceBadge />` in header
- `WorkerDetailPage.tsx` — same
- `InspectionDetailPage.tsx`, `IncidentDetailPage.tsx`, `ToolboxTalkDetailPage.tsx`, `EquipmentDetailPage.tsx`, `DailyLogDetailPage.tsx` — add `<ActivityStream />` + provenance badges
- Every list page (~20 list pages) — add `<ProvenanceBadge variant="inline" />` to each row
- App routing — add `/queries` route to the main nav

---

## 7. Acceptance Criteria

Phase 0 is done when:

1. **Audit emission**: Every mutation on tenant-scoped entities (create/update/state-change/archive) creates an AuditEvent node in Neo4j. Verified by running a smoke test that creates/updates/archives one of each entity type and asserting the AuditEvent count.
2. **Activity stream**: Opening the detail page of Project / Worker / WorkItem / Inspection / Incident / ToolboxTalk / Equipment / DailyLog shows a chronological activity timeline with at least the last 50 events. Clicking an event in the stream expands its details.
3. **Provenance display**: Every entity list row and detail page header shows a provenance badge. Agent-created entities are visually distinguishable from human-created. Confidence < 0.7 shows a warning indicator.
4. **Agent provenance wired**: Services that produce entities via agent action (compliance agent, briefing agent, hazard intake, etc.) record `model_id` and `confidence` on the created node and on the emitted AuditEvent.
5. **Graph query canvas**: `/queries` page loads with ≥20 starter queries grouped by category. User can select a query, fill parameters, run it, see a sortable data table, click through from a result row to the entity's detail page.
6. **Performance**: Activity stream query for a Project with 500+ child events returns in <500ms P95. Query canvas queries return in <2s P95 with realistic data volumes (one company, 10 projects, 500 work items, 5000 audit events).
7. **No regressions**: Existing detail pages still render all information they rendered before.

---

## 8. Open Questions

- **Retention**: Do we cap AuditEvent age? Propose: keep forever for now; revisit when total event count exceeds ~10M per tenant.
- **Sensitive field redaction in diffs**: If a user changes their phone number, should the AuditEvent record both old and new? Propose: redact nothing for now; we're a contractor app, not HR. Revisit if we add SSNs/pay rates.
- **Event volume in tests**: Should tests assert specific AuditEvents were emitted? Propose: yes, but only for integration tests — unit tests should not be coupled to audit side effects.
- **Query canvas authorship**: Can users eventually save their own queries? Propose: no, not in Phase 0. Admin-only server-defined is safer. Revisit in Phase 5+.
- **Activity stream filter controls**: Should users filter by event type, actor, or date range? Propose: ship without filters; add if Paul or users ask.

---

## 9. Explicit non-goals

- Event backbone / pub-sub infrastructure (Phase 4+)
- Authorization gateway (OPA/Cedar) — permission enforcement stays in service layer for now
- OpenTelemetry trace integration
- Agent cost attribution dashboard — cost is captured in AuditEvent but no rollup UI in Phase 0
- User-authored saved queries
- Multi-tenant audit archival / cold storage
- Activity stream search or full-text filtering
- Conversation/Decision/Insight linkage to entities (separate concern; exists in graph but not wired here)

---

## 10. Task breakdown (for plan-mode implementation)

Rough sequence — actual task boundaries may shift during implementation:

| # | Task | Rough size | Unlocks |
|---|------|------------|---------|
| 1 | AuditEvent schema + migration + indexes | S | Everything downstream |
| 2 | BaseService._emit_audit + audit_service.py emission methods | S | Task 3 |
| 3 | Wire _emit_audit into all existing service mutations (~15 services) | M | Audit trail captures everything going forward |
| 4 | Backfill script for existing entities (one-time) | S | Activity streams not empty on day one |
| 5 | Audit traversal methods per entity type (Project, Worker, WorkItem, ...) | M | Activity stream endpoint |
| 6 | `/entities/{type}/{id}/activity` router + API | S | Task 7 |
| 7 | ActivityStream React component + useActivityStream hook | M | Embedding in detail pages |
| 8 | Embed ActivityStream in 7 existing detail pages | S | Users see timelines |
| 9 | Agent provenance wiring: update Actor, update agent services to record model_id/confidence | S | Badges show accurate agent info |
| 10 | ProvenanceBadge component (3 variants) | S | Embeddable everywhere |
| 11 | Embed ProvenanceBadge in all detail page headers + list row renderers | M | Visibility of actor everywhere |
| 12 | query_canvas_service.py + register_query decorator + 20 starter queries | M | Queries are callable |
| 13 | `/queries` router endpoints | S | Task 14 |
| 14 | QueryCanvasPage + QueryList + QueryRunner components | M | Users can run queries |
| 15 | Smoke test: create each entity type, verify audit events, verify activity stream, verify one query per category runs | S | Acceptance criteria 1-6 verified |

S = ≤1 day, M = 1-3 days. Total ~3-4 weeks of focused work.

---

## 11. Approval

Pending Paul's review. If approved, move straight to plan-mode implementation starting with Task 1.
