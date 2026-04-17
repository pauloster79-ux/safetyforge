# Design Decisions

Each decision is presented with options, trade-offs, and a recommendation. These are explicit architectural choices that affect the entire schema.

---

## DD-01: Naming Conventions

### Node Labels
**Choice: PascalCase**
`WorkItem`, `DailyLog`, `CertificationType`
Rationale: Neo4j convention, tool compatibility, widely understood.

### Relationship Types
**Choice: UPPER_SNAKE_CASE**
`HAS_WORK_ITEM`, `ASSIGNED_TO`, `LOGGED_BY`
Rationale: Neo4j convention, readable in Cypher queries.

### Properties
**Choice: snake_case**
`clock_in`, `expiry_date`, `jurisdiction_code`
Rationale: Aligns with Python backend (Pydantic models). Existing schema already uses this convention.

### ID Format
**Choice: `{prefix}_{random_hex}`**
`wkr_a1b2c3d4e5f6g7h8`, `proj_b2c3d4e5f6g7h8i9`
Rationale: Human-readable prefix identifies entity type at a glance. Already established in the existing codebase.

New prefixes for new entities:

| Entity | Prefix |
|--------|--------|
| WorkItem | `wi` |
| WorkPackage | `wp` |
| WorkCategory | `wcat` |
| ~~Estimate~~ | ~~`est`~~ | *(removed — no Estimate entity)* |
| Contract | `ctr` |
| TimeEntry | `te` |
| Variation | `var` |
| Invoice | `inv` |
| InvoiceLine | `invl` |
| Payment | `pay` |
| PaymentApplication | `papp` |
| Crew | `crew` |
| Contact | `cont` |
| ProjectQuery | `pq` |
| QueryResponse | `qr` |
| ReviewSubmission | `rsub` |
| Warranty | `warr` |
| Milestone | `ms` |
| Conversation | `conv` |
| Message | `msg` |
| Decision | `dec` |
| Insight | `ins` |
| DocumentChunk | `dchk` |
| AccessGrant | `ag` |
| DeficiencyList | `dfl` |
| DeficiencyItem | `dfi` |
| HazardObservation | `hobs` |
| IncidentLogEntry | `ile` |

---

## DD-02: Inheritance vs Composition

**Choice: Multi-label for flat categories + category property for subtypes**

- Use Neo4j multi-labels for broad type grouping where useful (e.g., `:Inspection:SafetyInspection` is NOT used — instead `Inspection` with `category: "safety"`)
- Use a `category` or `type` property field for subtypes within an entity (Inspection category, Document type)
- Do NOT use deep IS_A hierarchies — they add traversal cost and complexity for limited benefit in this domain

Rationale: The domain has mostly flat type distinctions (a safety inspection vs quality inspection), not deep hierarchies. A property field is simpler to query, filter, and index than a multi-label or relationship-based hierarchy.

Exceptions:
- **WorkCategory** uses a parent-child relationship (`PARENT_CATEGORY`) for hierarchical classification (e.g., Electrical → Electrical Rough-In → Receptacles). This is a genuine tree structure that benefits from traversal.
- **Regulatory** nodes use `BELONGS_TO_GROUP` and `HAS_REGION` relationships for their natural hierarchies.

---

## DD-03: Temporal Modelling

**Choice: `valid_from` / `valid_until` with sentinel dates on regulatory entities. Audit timestamps on all mutable entities.**

Three different temporal patterns for three different needs:

### Regulatory facts (Regulation, CertificationType, etc.)
- `valid_from: date("2024-07-01")`
- `valid_until: date("9999-12-31")` — sentinel for currently active
- `SUPERSEDES` relationship links to previous version
- Never delete — invalidate by setting `valid_until`
- Supports CQ-A03: "What regulations applied on date X?"

### Mutable business entities (WorkItem, Estimate, Invoice, etc.)
- `created_at`, `updated_at` timestamps
- `created_by`, `updated_by` actor fields (provenance — see DD-09)
- `status` field tracks lifecycle state
- Status change history tracked via application logs, not graph nodes (the graph stores current state; the audit log stores the full history)

Why not StatusChange nodes? For entities with frequent status changes (WorkItem moving through draft → scheduled → in-progress → complete), status change nodes would proliferate rapidly and add traversal cost. The current status is what queries need 99% of the time. Historical status is an audit/reporting concern handled by the application audit log.

### Certifications and insurance
- `expiry_date` on Certification and InsuranceCertificate
- Query pattern: `WHERE c.expiry_date < date() + duration({days: 30})` for expiring-soon alerts
- Expired certs are not deleted — status changes to "expired"

---

## DD-04: Multi-Tenancy

**Choice: Graph-native isolation via Company node as traversal root**

Already established in the existing schema. All tenant-scoped data connects through:
```
(:Company)-[:OWNS_PROJECT]->(:Project)
(:Company)-[:EMPLOYS]->(:Worker)
(:Company)-[:HAS_EQUIPMENT]->(:Equipment)
(:Company)-[:HAS_MEMBER]->(:Member)
(:Company)-[:HAS_CONVERSATION]->(:Conversation)
```

If there is no traversal path from Company A to Entity X, Company A cannot see Entity X. No `WHERE company_id = $id` filter needed.

Exceptions:
- **Regulatory nodes** (Jurisdiction, Regulation, CertificationType, etc.) are shared across all tenants. They do not connect to any Company node.
- **GC-Sub relationships** cross tenant boundaries intentionally via `GC_OVER` relationship between two Company nodes, scoped by AccessGrant.

---

## DD-05: WorkItem Lifecycle — State + Status

**Choice: `state` for lifecycle position, `status` for current condition**

`state` — where the work item is in its lifecycle (always set):


```
draft → scheduled → in_progress → complete → invoiced
```

With additional terminal states:
- `cancelled` — work item removed from scope
- `on_hold` — work item paused (blocked, waiting)

`status` — current condition within the state (optional, nullable, free text):
Set by the agent from conversation. Examples: "Waiting on materials", "Blocked by framing", "Ready for inspection". Null when progressing normally.

Properties are progressively enriched as the WorkItem moves through states:

| State | Properties populated |
|-------|---------------------|
| draft | description, labour_hours, labour_rate, materials_allowance |
| scheduled | + planned_start, planned_end, assigned workers/crew |
| in_progress | + actual_start, time entries accumulating |
| complete | + actual_end |
| invoiced | + invoice references |

Not all WorkItems pass through every state. Jake's "fix the leak" might go straight from estimated to in_progress to complete. Sarah's commercial fit-out work items go through the full progression.

**Transition rules are enforced in application code, not in the graph.** The graph stores the current state. The service layer validates that transitions are legal (e.g., can't go from estimated to complete without passing through in_progress).

---

## DD-06: No Separate Estimate Entity

**Choice: The work items on a project at "quoted" status ARE the estimate. No separate Estimate node.**

The contractor builds WorkItems on a Project. When they send a quote, the Project status moves to "quoted". The WorkItems and their costs at that point are the estimate. No separate entity, no version chain, no duplication.

When costs change (client requests adjustments, contractor revises pricing), the WorkItems are updated directly. Change history is captured by:
- Provenance fields (updated_by, updated_at) — who changed it and when
- Conversation memory — the Conversation and Message nodes record why it changed
- The Project's `quoted_at` timestamp records when the quote was sent

For simple contractors (Jake): Project with WorkItems, quoted as a lump sum.
For complex projects (Sarah): Project with WorkPackages and detailed WorkItems, same structure.

This eliminates: version tracking nodes, cached totals that go stale, INCLUDES/SUPERSEDES relationships, and the confusion of costs living in two places.

---

## DD-07: Flexible Work Hierarchy

**Choice: WorkPackage is optional. WorkItem can connect directly to Project or to WorkPackage.**

Two valid graph patterns:

```cypher
// Simple (Jake): Project → WorkItem directly
(p:Project)-[:HAS_WORK_ITEM]->(wi:WorkItem)

// Complex (Sarah): Project → WorkPackage → WorkItem
(p:Project)-[:HAS_WORK_PACKAGE]->(wp:WorkPackage)-[:CONTAINS]->(wi:WorkItem)
```

A WorkItem ALWAYS belongs to exactly one Project (either directly or through a WorkPackage). The service layer ensures this invariant.

WorkPackage properties:
- `name` — "electrical rough-in", "ground floor fit-out"
- `description`
- `sort_order` — display ordering
- Totals are calculated by summing contained WorkItems

WorkPackages can be nested one level deep (WorkPackage containing WorkPackages) for larger projects, but this is optional and not the default. Maximum depth enforced at application level, not graph level.

---

## DD-08: WorkCategory Hierarchy

**Choice: Tree structure with PARENT_CATEGORY relationship**

```cypher
(wc:WorkCategory {name: "Receptacles"})
  -[:PARENT_CATEGORY]->
(wc2:WorkCategory {name: "Electrical Rough-In"})
  -[:PARENT_CATEGORY]->
(wc3:WorkCategory {name: "Electrical"})
```

WorkCategory is company-scoped (each company defines their own classification). But we provide default templates per trade when a company is created.

WorkCategory connects to the regulatory graph:
```cypher
(wc:WorkCategory)-[:LINKS_TO_ACTIVITY]->(a:Activity)-[:REGULATED_BY]->(r:Regulation)
```

This enables CQ-055 and CQ-056: the system can determine what regulations and certifications apply based on the work category.

---

## DD-09: Provenance — Who Did What

**Choice: Actor fields on all mutable entities. Same pattern for humans and agents.**

Every entity that can be created or modified carries:

| Property | Type | Description |
|----------|------|-------------|
| `created_by` | String | Member ID or AgentIdentity ID |
| `created_by_type` | String | `"human"` or `"agent"` |
| `created_at` | DateTime | Creation timestamp |
| `updated_by` | String | Last modifier ID |
| `updated_by_type` | String | `"human"` or `"agent"` |
| `updated_at` | DateTime | Last modification timestamp |

For agent-created entities, additional fields:
| Property | Type | Description |
|----------|------|-------------|
| `agent_version` | String | Version of the agent that created this |
| `model_id` | String | Which LLM model was used |
| `confidence` | Float | Agent's declared confidence (for interpretive actions) |

This is the same provenance model used by both humans and agents. The `created_by_type` field distinguishes them. This supports CQ-A01: "Which agent or human performed this action?"

---

## DD-10: Permission Model — Relationship + Role Depth

**Choice: Graph traversability determines WHAT you can reach. Access role determines HOW DEEP you can go. AccessGrant handles exceptions.**

Three layers:

1. **Traversability** — if there's no path from Member to Entity through the graph, the Member can't see it. This is structural, enforced by the graph itself.

2. **Role depth** — the Member's `access_role` determines which entity types they can traverse to:

| Role | Can traverse to |
|------|----------------|
| owner / admin | Everything within the company |
| manager | Full depth on assigned projects (including commercial: estimates, margins, invoices, payments) |
| foreman | Assigned projects → work items, time entries, inspections, deficiencies. NOT estimates, margins, invoices |
| worker | Own assignments, own time entries, safety data (inspections, hazards, toolbox talks) |

3. **AccessGrant** — explicit exceptions to the default role-based depth:
- GC accessing sub compliance data on shared projects
- Client seeing progress and invoices
- Architect participating in project queries
- Temporary role elevation

**Enforcement:** Service layer, not graph structure. Every data access query checks:
(a) Does a graph path exist from the requesting user to the target data? (traversability)
(b) Is the target entity type within the user's role depth? (role check)
(c) Does an AccessGrant override the default? (exception check)

---

## DD-11: Vector Embedding Strategy

**Choice: Neo4j native vector indexes on Message and DocumentChunk nodes. Embedding model selected at deployment.**

Two vector indexes:

| Index | Node | Dimensions | Similarity | Purpose |
|-------|------|-----------|-----------|---------|
| `message_embeddings` | Message | 1536 (configurable) | cosine | Semantic search over conversation history |
| `chunk_embeddings` | DocumentChunk | 1536 (configurable) | cosine | Semantic search over document content |

Embedding model is a deployment configuration, not a schema decision. Options:
- OpenAI `text-embedding-3-small` (1536 dims, cheap, well-tested)
- Voyage AI (1024 dims, good for technical/construction content)
- Open-source (e.g., BGE, Nomic) for self-hosted deployments

The schema stores the embedding as a `LIST<FLOAT>` property on the node. The vector index is created on that property. The embedding model can be swapped without schema changes — only the dimension count on the index changes.

Hybrid retrieval pattern (from Neo4j reference):
```cypher
// Semantic search + graph context in one query
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $queryEmbedding)
YIELD node AS chunk, score
MATCH (chunk)-[:CHUNK_OF]->(doc:Document)-[:HAS_DOCUMENT]-(p:Project)
WHERE p.id = $projectId  // scope to project
RETURN chunk.text, score, doc.title
```

---

## DD-12: Currency and Measurement

**Choice: All monetary values stored with currency code. Jurisdiction provides defaults. No automatic conversion.**

- Every monetary property is paired with a currency context inherited from the Company's `default_currency`
- Monetary values are stored as integers in the smallest currency unit (cents/pence) to avoid floating-point issues
- The Company's currency is set once and applies to all its data
- No automatic currency conversion — the platform operates in the company's local currency
- If a company operates across currencies (rare for target market), this is a future extension

Measurement system:
- `measurement_system` on Jurisdiction and Company: `"metric"` or `"imperial"`
- WorkItem quantities use the company's measurement system
- Regulatory values (e.g., "guardrails must be 1.1m / 42 inches") are stored in the jurisdiction's system with the regulation

---

## DD-13: Soft Delete

**Choice: Soft delete via `status` or `archived` flag. Never hard delete tenant data.**

- Entities are never physically deleted from the graph
- Deletion sets `status: "archived"` or `archived: true`
- Archived entities are excluded from default queries but remain accessible for audit
- Regulatory entities use temporal invalidation (`valid_until`) instead of deletion
- Physical deletion only for: test data cleanup, GDPR/privacy right-to-erasure requests (handled by a dedicated process with audit trail)

---

## DD-14: Knowledge Graph Depth — Layer 3 for Safety Rules

**Choice: Layer 3 (rules as traversable structure) for safety and regulatory rules. Layer 2 for everything else.**

Layer 3 encoding (conditional logic in the graph) is used where:
- Wrong answer = real-world harm (safety compliance)
- The answer must be deterministic and auditable
- The rule is referenced by multiple consumers (agents, UI, reports)

Entities encoded at Layer 3:
```
Activity -[:REGULATED_BY]-> Regulation -[:REQUIRES_CONTROL {when: "height > 1.8m"}]-> CertificationType
```

The `when` property on REQUIRES_CONTROL edges carries the condition. The traversal is deterministic: given an Activity and a Jurisdiction, the graph returns exactly which certifications are required, with citation to the source regulation.

Everything else (financial calculations, scheduling logic, invoicing rules) stays in application code — these are business rules that change frequently and don't need the auditability of graph-encoded rules.

---

## Summary

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| DD-01 | Naming | PascalCase nodes, UPPER_SNAKE_CASE rels, snake_case props, prefix_hex IDs | Neo4j convention, existing pattern |
| DD-02 | Inheritance | Category property, not multi-label or IS_A chains | Flat type distinctions, simpler queries |
| DD-03 | Temporal | valid_from/valid_until + sentinel for regulations; timestamps + status for business entities | Different needs for different entity classes |
| DD-04 | Multi-tenancy | Graph-native via Company traversal root | Established pattern, structural isolation |
| DD-05 | WorkItem lifecycle | State (lifecycle position) + status (current condition). Progressive enrichment | Supports both simple and complex contractors |
| DD-06 | No Estimate entity | Work items at "quoted" status ARE the estimate. No separate node | No duplication, no stale caches, simpler model |
| DD-07 | Work hierarchy | WorkPackage optional; WorkItem can connect directly to Project | No mandatory structure for simple projects |
| DD-08 | WorkCategory | Tree with PARENT_CATEGORY; links to regulatory graph via Activity | Hierarchical classification + regulatory connection |
| DD-09 | Provenance | Actor fields on all mutable entities; same pattern for humans and agents | Audit trail from day one |
| DD-10 | Permissions | Traversability + role depth + AccessGrant exceptions | Graph-native, flexible, auditable |
| DD-11 | Vector embeddings | Neo4j native indexes on Message and DocumentChunk | Single database, hybrid retrieval |
| DD-12 | Currency/measurement | Integer cents with currency code; measurement system per jurisdiction | No floating-point issues; jurisdiction defaults |
| DD-13 | Soft delete | Status/archived flag; never hard delete | Audit trail preserved |
| DD-14 | KG depth | Layer 3 for safety/regulatory rules; Layer 2 for everything else | Deterministic auditability where wrong = harm |
