# Architecture Decisions Registry

*Every non-obvious technical decision made in Kerf. Read this before building anything significant.*

*Format: What we decided, why, and any context that matters.*

---

## Data Architecture

### ADR-001: Neo4j as primary database (not Postgres)

Knowledge graph with permissions enforced through traversability. If no path exists from Company to Project to Data, that data is invisible — no separate ACL layer needed. Enables auditable compliance queries: regulations, activities, certifications, worker assignments form a traversal chain, not a JOIN. Replaces the v1 approach of `WHERE company_id = $cid` on every query.

### ADR-002: Vector embeddings stored as native Neo4j properties (not Pinecone/separate vector store)

Conversations, documents, photos stored as vector embeddings on the same graph nodes that link them to entities. Hybrid queries (semantic similarity + graph traversal) execute in single Cypher against a single database. No sync burden between systems. Neo4j 5.11+ capability.

### ADR-003: ID format is `{prefix}_{random_hex}`

IDs like `comp_a1b2c3d4`, `proj_b2c3d4e5` using cryptographic randomness. Avoids B-tree hot-spot collisions at scale (sequential IDs create write contention). Prefix makes IDs self-describing in logs and debugging.

---

## Authentication & Authorization

### ADR-004: Clerk for authentication

Delegated sign-up, login, token refresh to Clerk. Frontend communicates directly with Clerk, backend validates Bearer tokens. Zero GDPR/compliance liability for credential storage. SOC 2 Type II certified. Passwordless options without building it.

### ADR-005: Graph-native permissions (no ACL table)

Permission enforcement via graph structure: `(Member)-[:BELONGS_TO]->(Company)-[:OWNS_PROJECT]->(Project)-[:HAS_INSPECTION]->(Inspection)`. Same model for humans and agents. Every query originates from the authenticated user's Company node. If data is unreachable, query returns null — no error, no leak. Auditable: every access decision has a traversal path.

---

## Service Architecture

### ADR-006: BaseService pattern with Neo4j driver injection

All domain services extend BaseService with `_read_tx`, `_write_tx` helpers. Driver is singleton injected via dependency. Consistent transaction handling and provenance (every mutation gets created_by/updated_by). Cypher queries parameterized — no string interpolation.

### ADR-007: Service-per-entity pattern

One service class per primary domain entity (CompanyService, ProjectService, WorkerService). Mirrors domain boundaries, keeps domain logic cohesive, dependencies explicit. Exceptions: GenerationService, AnalyticsService are operation-oriented because they read across domains.

### ADR-008: Pydantic Create/Update/Read model pattern

Three models per entity: `CompanyCreate` (no ID, no audit fields), `CompanyUpdate` (all fields optional), `Company` (full with audit). Prevents audit field mutation from user input. FastAPI rejects invalid payloads before the service layer.

---

## AI & Document Generation

### ADR-009: Prompts loaded from jurisdiction packs (YAML), not hardcoded

System prompts for document generation live in `jurisdictions/{code}/prompts/*.md`, loaded by JurisdictionContext. Adding a new country = adding a data pack, not modifying Python code. v1.0 hardcoded US; v2.0 extracted US pack; v2.1+ added UK, CA, AU.

### ADR-010: Compliance audit = graph traversal + Claude, not questionnaire

Gathers data from connected nodes (Project, Inspection, Incident, Worker, Certification), checks against regulatory graph (Regulation, RequiresCert, CertificationType), generates findings per citation style, scores by category. Outputs are auditable — every citation traces to a specific regulation node.

### ADR-011: Every Claude call logs model, tokens, latency, cost

Generation metadata recorded on every LLM interaction for agent budget enforcement (daily_spend_cents vs daily_budget_cents), cost attribution per company, and LLM provider risk monitoring.

---

## Agentic Infrastructure

### ADR-012: Agents are first-class graph citizens (AgentIdentity nodes)

Agents stored as `(:AgentIdentity)-[:BELONGS_TO]->(:Company)` with budget fields, scopes, rate limits. Same permission model as humans (traversability enforces access). Cost isolation per company. Explicit agent identity in audit logs.

### ADR-013: Event backbone via Pub/Sub (not in-process queue)

Events emitted from service layer to topics. Agents subscribe to event types (e.g., Compliance Agent watches `certification.expiring`). Decouples agent scheduling from request path. Survives service restarts. In-process event bus for MVP, upgrades to Pub/Sub at scale.

### ADR-014: MCP tools for agent-to-backend (not REST)

Agents interact through intent-based MCP tools (`check_compliance`, `generate_briefing`), not raw API endpoints. LLMs reason better over tools than HTTP contracts. Guardrails enforced at tool level. Tool `check_worker_compliance` accepts project_id + worker_id, returns structured compliance gaps with citations.

---

## Multi-Jurisdiction

### ADR-015: Jurisdiction abstraction via data packs, zero conditional code

Every jurisdiction-specific value (certifications, regulations, document formats, field labels, measurement units) lives in YAML under `jurisdictions/{code}/`. Adding a new country = 3-5 days of data pack creation. Service renames: `OshaLogService` became `IncidentRecordService`, `MockInspectionService` became `ComplianceAuditService`.

### ADR-016: Regulatory graph populated by AI, not manual curation

Source material (eCFR, HSE, SWA) fetched, Claude extracts rules as Cypher, automated structural validation, risk-stratified spot-checking. Every edge has `source` and `effective_date`. Rules are deterministic graph structure, not text retrieved for LLM reinterpretation (not RAG).

### ADR-017: Regulation-Activity-Cert graph edges (not trade-based)

`Activity -[REGULATED_BY]-> Regulation -[REQUIRES_CERT]-> CertificationType`, never `Trade -[REQUIRES_CERT]-> Certification`. OSHA regulates activities, not trades. A welder on a fall-protection task needs fall protection regardless of their trade. Graph mirrors regulatory intent.

---

## Infrastructure

### ADR-018: Cloud Run for backend (not ECS/Kubernetes)

Stateless FastAPI on Cloud Run. Zero ops (no cluster management). Natural for I/O-bound workload. Concurrency=80 handles typical load with 1 instance. Lazy imports reduce cold start from ~4s to ~1.5s.

### ADR-019: Vercel for frontend (not Firebase Hosting)

First-class Vite/React support, built-in Web Vitals, PR preview deployments. $20/month Pro vs Firebase free tier — offset by improved DX and automatic PR previews.

### ADR-020: Lemon Squeezy for billing (not Stripe)

SaaS payments with auto-renewal, invoicing, native VAT/GST calculation. Stripe overkill for 100-1000 customer range. Changed from Paddle due to better international support.

### ADR-021: GCP project-per-environment with isolated billing

Three separate GCP projects (kerf-dev, kerf-staging, kerf-prod). Prevents production secrets leaking to dev. Billing isolation. Different quotas/rate limits per environment.

---

## Frontend

### ADR-022: JurisdictionProvider React Context

Jurisdiction config (certifications, document types, labels, formatting) injected via React Context, not fetched per component. Country selector drives everything downstream — labels swap automatically (OSHA Log to RIDDOR Log when jurisdiction changes).

### ADR-023: Offline-first as architectural requirement (not Phase 2)

All field operations (voice, photos, inspection checklist, time clock) queue locally and reconcile on sync. Jobsites have ~40% spotty connectivity. IndexedDB for queuing, sync on background task, conflict resolution favours local changes.

---

## Data Flows

### ADR-024: One site walk populates multiple reports

Site walk with narration + photos produces DailyLog, SafetyInspection, QualityObservation via single graph mutation. "Documentation is a byproduct of doing work" operationalised.

### ADR-025: WorkItem flows through lifecycle (no re-entry)

WorkItem entity: estimated (quantity x rate) -> scheduled (add dates/crew) -> tracked (% complete) -> closed (actual vs budget). One data structure, zero re-entry. When bid is won, estimate lines become schedulable tasks automatically.

### ADR-026: Conversations are graph mutations, not just logs

Every conversation produces a Conversation node linked to entities: ABOUT_PROJECT, ABOUT_ENTITY, PRODUCED_DECISION, EXPRESSED_KNOWLEDGE. Contractor's institutional knowledge accumulates in graph. Future queries can retrieve relevant past conversations.

---

## Cost & Performance

### ADR-027: Aggressive prompt caching for Claude calls

System prompts (jurisdiction regulations, ontology schema, historical context) sent with `cache_control`. Jurisdiction pack is 5-10KB, ontology schema 20KB — caching saves ~90% of input tokens on repeat queries from same company. 5-minute TTL aligns with Anthropic cache window.

### ADR-028: Model routing — Haiku for simple tasks, Sonnet for reasoning

Hazard classification, daily log auto-fill use Haiku. Document generation, variation detection use Sonnet. Haiku is ~10x cheaper. At 5K API calls/day, routing 60% to Haiku saves ~$400/month.

---

## Provenance & Audit

### ADR-029: Full provenance on every mutable node

Every create/update records: who (human UID or agent_id), type (human vs agent), which LLM model (for agent mutations), confidence score. Insurance carrier can verify "this corrective action was human-assigned, not AI-guessed." Required for regulatory compliance.

### ADR-030: Audit trail via EventBus (not separate audit table)

All mutations emit events capturing actor, timestamp, entity before/after, reason. Same infrastructure as agent subscriptions. Events in Pub/Sub for 7 days, extracted summaries live permanently in graph.

---

## Phase 0 Foundations (2026-04-16)

### ADR-031: AuditEvent as graph node (not separate log store)

Audit events are Neo4j nodes linked to entities via `EMITTED` edges. Activity streams are graph traversals — a Project's stream aggregates events across all child entities (WorkItems, Inspections, Incidents, DailyLogs, ToolboxTalks, HazardReports) via UNION traversals. 300 events backfilled from existing entities. This keeps everything in one system and avoids a separate log database to sync.

### ADR-032: Direct REST endpoint for estimate summary (not SSE chat roundtrip)

Replaced the fragile SSE-based estimate fetch (sent a chat message, waited for tool_result stream) with a direct `GET /me/projects/{pid}/estimate-summary` endpoint. The SSE approach was slow, unreliable, and blocked the renderer. Standard useQuery hook now handles fetching and cache invalidation.

### ADR-033: Contract auto-creation on first term operation

When the first contract term is added to a project (payment milestone, condition, warranty, retention), the service auto-creates a draft Contract node if one doesn't exist. This avoids a separate "create contract" step that would confuse users — the contract materialises naturally as terms are defined.

### ADR-034: Quote and contract as lifecycle of the same data (not separate entities)

The Contract tab shows QuotingView (LEAD/QUOTED state) and ActiveContractView (ACTIVE state) from the same underlying data. WorkItems created during quoting are the same WorkItems tracked during delivery. Contract terms defined during quoting become the monitoring baseline during execution. No data migration on project state transition.

### ADR-035: LLM project matching over fuzzy search tool

When a user references a project by name ("the Peachtree job"), the LLM matches it to an existing project from the list already in its context, rather than calling a fuzzy search tool. The system prompt instructs Claude to use existing projects and only create new ones with capture_lead when the user is clearly describing something new. This avoids unnecessary tool calls and leverages the LLM's natural language understanding.

### ADR-036: max_tokens 8192 for tool-heavy chat responses

Increased from 2048 to 8192 to allow Claude to complete a full quote (5+ work items with labour/item breakdowns) in a single conversation turn. At 2048, complex quotes required 3 turns of "keep going" which broke the conversational flow.
