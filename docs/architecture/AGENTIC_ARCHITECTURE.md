# Kerf Agentic Architecture

*Version 1.0 — 2026-04-08*

This document specifies Kerf's agentic infrastructure — the systems that enable AI agents (both internal and third-party) to interact with the platform. It sits alongside the [Construction Ontology](CONSTRUCTION_ONTOLOGY.md) which defines the knowledge graph schema, and the [Backend Architecture](BACKEND_ARCHITECTURE.md) which defines the human-facing API.

For product-agnostic principles, see the [Agentic Infrastructure Playbook](~/.claude/rules/AGENTIC_INFRASTRUCTURE.md).

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  KERF AGENTS (MCP clients)                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │ Compliance  │ │ Briefing   │ │ Intake (voice/ │   │
│  │ Agent       │ │ Agent      │ │ photo/form)    │   │
│  └──────┬─────┘ └──────┬─────┘ └───────┬────────┘   │
│         │              │               │             │
│  ┌──────┴──────────────┴───────────────┴──────────┐  │
│  │  KERF MCP SERVER                               │  │
│  │  Intent-based tools (check_compliance,         │  │
│  │  generate_briefing, parse_voice_input, ...)    │  │
│  └──────────────────┬─────────────────────────────┘  │
├─────────────────────┼────────────────────────────────┤
│  ┌──────────────────┴─────────────────────────────┐  │
│  │  EVENT BACKBONE (Google Cloud Pub/Sub)          │  │
│  │  inspection.completed, incident.reported, ...   │  │
│  └──────────────────┬─────────────────────────────┘  │
├─────────────────────┼────────────────────────────────┤
│  ┌──────────────────┴─────────────────────────────┐  │
│  │  SERVICE LAYER (operation-oriented)             │  │
│  │  ComplianceOps, BriefingOps, IntakeOps, ...     │  │
│  └──────────────────┬─────────────────────────────┘  │
├─────────────────────┼────────────────────────────────┤
│  ┌──────────────────┴─────────────────────────────┐  │
│  │  NEO4J KNOWLEDGE GRAPH                          │  │
│  │  14 domains + AgentIdentity + graph-native ACL  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

  EXTERNAL:
  ┌────────────┐  ┌─────────────┐
  │ REST API   │  │ Third-party │
  │ (frontend) │  │ MCP clients │
  └──────┬─────┘  └──────┬──────┘
         │               │
         └───────┬───────┘
                 ▼
         Service Layer (shared)
```

---

## 2. Graph-Native Permissions

### Design

Kerf does not maintain a separate ACL. The domain relationships in the knowledge graph ARE the permissions. An agent (or user) can only reach data that is traversable from their identity node.

### Permission traversals

```cypher
// Agent access: Can Agent X see Inspection Y?
MATCH (a:AgentIdentity {agent_id: $agent_id})-[:BELONGS_TO]->(c:Company)
MATCH (i:Inspection {id: $inspection_id})-[:BELONGS_TO]->(p:Project)
WHERE (c)-[:OWNS_PROJECT|WORKS_ON]->(p)
RETURN i

// GC agent sees sub data: Can GC Agent see Sub's workers on GC's project?
MATCH (a:AgentIdentity {agent_id: $agent_id})-[:BELONGS_TO]->(gc:Company)
MATCH (gc)-[:GC_OVER]->(sub:Company)-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO]->(p:Project)
WHERE (gc)-[:OWNS_PROJECT]->(p)
RETURN w

// Human access follows same pattern via Member node:
MATCH (m:Member {uid: $firebase_uid})-[:MEMBER_OF]->(c:Company)
MATCH (i:Inspection {id: $inspection_id})-[:BELONGS_TO]->(p:Project)
WHERE (c)-[:OWNS_PROJECT|WORKS_ON]->(p)
RETURN i
```

### Scoped permissions

```cypher
// Agent scopes are stored on the BELONGS_TO relationship
(AgentIdentity)-[:BELONGS_TO {
  scopes: ["read:safety", "read:workers", "write:inspections"],
  rate_limit_per_minute: 60
}]->(Company)
```

The query layer checks scopes after traversal succeeds. Traversal determines *whether* access exists. Scopes determine *what kind* of access.

---

## 3. Actor Provenance

### Schema additions

Every node that can be created or mutated carries actor provenance fields:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `created_by` | string | Yes | Actor ID — user UID or agent_id |
| `actor_type` | string | Yes | `"human"` or `"agent"` |
| `agent_id` | string | No | Agent ID if actor_type is "agent", null otherwise |
| `updated_by` | string | Yes | Actor ID of last updater |
| `updated_actor_type` | string | Yes | `"human"` or `"agent"` |

These fields are in addition to the existing `created_at` and `updated_at` timestamps.

### Service layer enforcement

The service layer receives an `Actor` context on every operation:

```python
@dataclass
class Actor:
    id: str                    # user UID or agent_id
    type: str                  # "human" | "agent"
    agent_id: str | None       # agent_id if type == "agent"
    company_id: str            # tenant scope
    scopes: list[str]          # permission scopes
```

No service method executes without an Actor. This is enforced by the service base class.

---

## 4. Event Backbone

### Infrastructure

Google Cloud Pub/Sub with:
- One topic per event domain (safety, hr, equipment, daily_ops)
- Per-agent-type subscriptions with message filters
- Dead-letter topics for failed processing
- 7-day message retention

### Event types

| Event | Domain Topic | Trigger | Agent consumers |
|-------|-------------|---------|-----------------|
| `inspection.completed` | safety | Inspection submitted | Compliance, Briefing |
| `inspection.item_failed` | safety | Inspection has critical failures | Compliance |
| `incident.reported` | safety | Incident created | Compliance (OSHA 24hr check), Briefing |
| `hazard.reported` | safety | Hazard report created | Compliance |
| `corrective_action.overdue` | safety | CA past due date | Compliance, Escalation |
| `certification.expiring` | hr | Cert within 30/14/7/1 days of expiry | Compliance, Briefing |
| `worker.assigned_to_project` | hr | Worker-Project assignment created | Compliance (cert validation) |
| `worker.removed_from_project` | hr | Worker-Project assignment ended | Briefing |
| `equipment.inspection_due` | equipment | Equipment past inspection interval | Compliance, Briefing |
| `equipment.deployed` | equipment | Equipment moved to project | Briefing |
| `document.generated` | daily_ops | Document created (safety plan, report) | QA |
| `daily_log.submitted` | daily_ops | Daily log completed | Briefing |
| `insurance.expiring` | sub_mgmt | Sub insurance within 30 days of expiry | Compliance, GC Portal |

### Event envelope

```json
{
  "event_id": "evt_a1b2c3d4",
  "event_type": "inspection.completed",
  "version": "1.0",
  "entity_id": "insp_abc123",
  "entity_type": "Inspection",
  "project_id": "proj_xyz",
  "company_id": "comp_456",
  "actor": {
    "type": "human",
    "id": "user_789",
    "agent_id": null
  },
  "timestamp": "2026-04-08T14:30:00Z",
  "summary": {
    "total_items": 24,
    "passed": 20,
    "failed": 3,
    "na": 1,
    "critical_failures": ["fall_protection", "scaffolding"]
  },
  "graph_context": {
    "project_jurisdiction": "US-GA",
    "related_regulations": ["29CFR1926.501", "29CFR1926.451"],
    "affected_workers": ["wkr_111", "wkr_222"],
    "affected_locations": ["loc_floor3_east"]
  }
}
```

### Event emission

Events are emitted from the service layer after successful mutations. The service layer is the single point of event emission — not the API layer, not the MCP layer.

```python
class InspectionService:
    def complete_inspection(self, inspection_id: str, actor: Actor) -> Inspection:
        # 1. Business logic
        inspection = self._complete(inspection_id, actor)

        # 2. Emit event with graph context
        graph_context = self._build_graph_context(inspection)
        self.event_bus.emit(InspectionCompleted(
            entity_id=inspection.id,
            project_id=inspection.project_id,
            company_id=actor.company_id,
            actor=actor,
            summary=inspection.summary(),
            graph_context=graph_context
        ))

        return inspection
```

---

## 5. MCP Server

### Tool inventory

Mapped to existing services. Each tool is an operation, not a CRUD endpoint.

#### Safety Operations
| Tool | Description | Service | Risk level |
|------|-------------|---------|------------|
| `check_worker_compliance` | Check if a worker meets all cert/training requirements for a project in its jurisdiction | ComplianceOps | Read-only |
| `check_project_compliance` | Full compliance status for a project — certs, programs, equipment, inspections | ComplianceOps | Read-only |
| `get_inspection_results` | Get inspection results with regulatory context | InspectionService | Read-only |
| `create_inspection` | Create a new inspection from structured data | InspectionService | Low-risk write |
| `report_hazard` | Create a hazard report | HazardReportService | Low-risk write |
| `report_incident` | Create an incident report | IncidentService | Low-risk write |
| `create_corrective_action` | Create a corrective action from an inspection or incident | CorrectiveActionService | Low-risk write |
| `resolve_corrective_action` | Mark a corrective action as resolved | CorrectiveActionService | High-risk write |

#### Briefing & Generation
| Tool | Description | Service | Risk level |
|------|-------------|---------|------------|
| `generate_morning_brief` | Generate a morning safety briefing for a project | BriefingOps | Read-only |
| `generate_toolbox_talk` | Generate a toolbox talk for specific topics/hazards | GenerationService | Low-risk write |
| `generate_safety_plan` | Generate a project safety plan | DocumentService | Low-risk write |

#### Intake & Interpretation
| Tool | Description | Service | Risk level |
|------|-------------|---------|------------|
| `parse_voice_input` | Parse voice transcript into structured safety data | IntakeOps | Read-only |
| `parse_document` | Extract structured data from uploaded document (insurance cert, OSHA log) | IntakeOps | Read-only |

#### Query & Search
| Tool | Description | Service | Risk level |
|------|-------------|---------|------------|
| `query_graph` | Natural language query against the knowledge graph (NL → Cypher) | SemanticQueryService | Read-only |
| `get_project_summary` | Current state of a project — workers, equipment, recent safety activity | ProjectService | Read-only |
| `get_worker_profile` | Worker's certs, training, assignment history, incident involvement | WorkerService | Read-only |
| `get_regulatory_requirements` | What regulations apply to a given activity in a given jurisdiction | RegulatoryService | Read-only |
| `get_changes_since` | Delta query — what changed on a project since a given timestamp | DeltaService | Read-only |

#### Administration
| Tool | Description | Service | Risk level |
|------|-------------|---------|------------|
| `assign_worker_to_project` | Assign a worker to a project (triggers compliance check) | WorkerService | Low-risk write |
| `update_worker_certification` | Add or update a worker's certification | CertificationService | High-risk write |
| `override_compliance_flag` | Override a compliance warning (requires justification) | ComplianceOps | High-risk write |

### Guardrails

| Risk level | Agent behaviour |
|------------|-----------------|
| Read-only | Always allow. No approval needed. Full audit log. |
| Low-risk write | Allow with audit trail. Rate-limited per agent. Reversible within 24 hours. |
| High-risk write | Agent proposes action → approval queue → human reviews → agent executes if approved. Approval recorded in provenance. |

---

## 6. Agent Types

### Internal agents (built by Kerf)

| Agent | Purpose | Event subscriptions | MCP tools used |
|-------|---------|--------------------|--------------------|
| **Compliance Agent** | Watches for regulatory violations, cert gaps, overdue CAs | certification.expiring, worker.assigned_to_project, inspection.completed, corrective_action.overdue | check_worker_compliance, check_project_compliance, get_regulatory_requirements |
| **Briefing Agent** | Generates morning briefs from overnight changes | inspection.completed, incident.reported, certification.expiring, equipment.inspection_due, daily_log.submitted | generate_morning_brief, get_project_summary, get_changes_since |
| **Intake Agent** | Parses voice notes, photos, and forms into graph nodes | (invoked on-demand, not event-driven) | parse_voice_input, parse_document, report_hazard, report_incident, create_inspection |
| **Forecast Agent** | Predicts cert gaps, equipment maintenance needs, compliance risk trends | (scheduled, not event-driven — runs daily) | check_project_compliance, get_worker_profile, query_graph |

### External agents (third-party MCP clients)

Third-party agents connect via the same MCP server with:
- Their own `AgentIdentity` node in the graph
- Company-scoped permissions via `BELONGS_TO` relationship
- Restricted scopes (typically read-only for external agents)
- Separate rate limits

---

## 7. Semantic Query Layer

### Design

Natural language → Cypher translation, using the ontology schema as context.

```
User/Agent: "Which workers on Project Alpha have fall protection certs expiring in the next 30 days?"

→ SemanticQueryService receives NL query
→ Sends to Claude with ontology schema as system context
→ Claude generates Cypher:

MATCH (w:Worker)-[:ASSIGNED_TO]->(p:Project {name: 'Project Alpha'})
MATCH (w)-[:HOLDS_CERT]->(c:Certification)-[:OF_TYPE]->(ct:CertificationType)
WHERE ct.name CONTAINS 'fall protection'
  AND c.expiry_date <= date() + duration({days: 30})
  AND c.expiry_date >= date()
RETURN w.first_name, w.last_name, ct.name, c.expiry_date
ORDER BY c.expiry_date

→ Execute against Neo4j with tenant scope
→ Return structured results with source citations
```

### Safety rails

- Generated Cypher is validated before execution (no mutations, tenant-scoped)
- Query timeout enforced (5 seconds max)
- Result set size limited (1000 rows max)
- Schema introspection endpoint lets agents discover available node types and relationships

---

## 8. AI-Powered Regulatory Population

### Strategy

The regulatory graph (Domain 1 of the ontology) is populated by AI, not manually encoded.

### Pipeline

```
eCFR API (29 CFR 1926)          → Fetch regulation text
State plan comparison docs      → Fetch jurisdiction variations
OSHA Letters of Interpretation  → Fetch interpretive guidance
                ↓
        AI Extraction (Claude)
        - Parse regulation text
        - Extract rules as graph operations
        - Identify cross-references
        - Tag with source citations
                ↓
        Cypher Generation
        - CREATE/MERGE statements for nodes and edges
        - Every edge carries: source, effective_date, version
                ↓
        Automated Validation
        - Schema conformance check
        - Dangling reference detection
        - Duplicate detection
        - Citation completeness check
                ↓
        Spot-Check (10% sample)
        - Human reviews sample for systematic errors
                ↓
        Commit to Graph
        - Versioned, with rollback capability
```

### Monitoring

- Subscribe to Federal Register API for regulatory amendments
- When a regulation in the graph is amended, re-run the extraction pipeline for affected sections
- Flag downstream compliance checks that may be affected by the change

---

## 9. Implementation Priority

| Phase | What | Depends on | Estimated effort |
|-------|------|-----------|-----------------|
| **Phase A** | AgentIdentity nodes + provenance fields in ontology | Ontology v2 | 1 week |
| **Phase A** | Graph-native permission query patterns | AgentIdentity | 1 week |
| **Phase B** | Event backbone (Pub/Sub setup, event emission from services) | Service layer | 2 weeks |
| **Phase B** | Actor context in service layer | AgentIdentity | 1 week |
| **Phase C** | MCP server (core tools) | Service layer, permissions | 3 weeks |
| **Phase C** | Guardrails (action classification, approval queue) | MCP server | 1 week |
| **Phase D** | Compliance Agent | MCP server, events | 2 weeks |
| **Phase D** | Briefing Agent | MCP server, events | 1 week |
| **Phase E** | Semantic query layer | Populated graph | 2 weeks |
| **Phase E** | Regulatory population pipeline | Domain 1 ontology | 2 weeks |
| **Phase F** | Intake Agent (voice/photo/form) | MCP server | 2 weeks |
| **Phase F** | Forecast Agent | MCP server, populated graph | 1 week |

Phases A-B are foundation (do first, regardless of feature priority).
Phases C-D are the first agents.
Phases E-F are intelligence amplifiers.

---

*This document is updated as agentic infrastructure is implemented. The Construction Ontology remains the source of truth for graph schema; this document specifies the infrastructure around it.*
