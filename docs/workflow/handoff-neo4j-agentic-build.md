# Handoff: Neo4j Knowledge Graph + Agentic Infrastructure Build

**Date:** 2026-04-09 (updated)
**From:** Ontology design + build planning session
**To:** Implementation session(s)

---

## Progress Tracker

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| **Phase 0: Foundation** | **DONE** | 2026-04-07 | base_service, Actor model, conftest Neo4j fixtures, schema.cypher trimmed |
| **Phase 1A: Organisational** | **DONE** | 2026-04-07 | company, project, member, invitation, project_assignment (5 services) |
| **Phase 1B: HR + Equipment** | **DONE** | 2026-04-08 | worker, equipment (2 services) |
| **Phase 1C: Safety** | **DONE** | 2026-04-08 | inspection, incident, hazard_report, toolbox_talk (4 services) |
| **Phase 1D: Regulatory + Docs** | **DONE** | 2026-04-09 | osha_log, environmental, document (3 services) |
| **Phase 2A: Tier 2 Composites** | **DONE** | 2026-04-09 | morning_brief, state_compliance, billing, gc_portal (4 services) |
| **Phase 2B: Tier 2 Composites** | **DONE** | 2026-04-09 | analytics, mock_inspection, prequalification (3 services) |
| **Phase 3: Firestore Removal** | **DONE** | 2026-04-09 | Full cleanup: removed google_cloud_project config, firestore.rules, firestore.indexes.json, FIRESTORE_EMULATOR_HOST refs, updated CI to Neo4j service, updated docker-compose/Makefile/README. 187/187 tests pass. |
| **Phase 2 (partial)** | NOT STARTED | — | context_assembler.py (new service: graph → structured LLM context) |
| **Phase 4: P0 Agentic Infra** | **DONE** | 2026-04-09 | AgentIdentity CRUD + graph-native perms + LLM service + cost control + circuit breaker + admin API. 230/230 tests pass. |
| **Phase 5: P1 Agentic Infra** | **DONE** | 2026-04-09 | Event backbone, MCP tools (8), guardrails (action taxonomy + approval queue) |
| **Phase 6: First Agents** | **DONE** | 2026-04-10 | Compliance Agent, Briefing Agent, Agent Orchestrator. 33 new tests. |

**Test status:** 334/334 passing
**Firestore references:** 0 anywhere in backend, CI, or infra config

---

## What This Session Did (Original)

1. **Ontology v2.3** — expanded the construction ontology across three files:
   - `docs/architecture/CONSTRUCTION_ONTOLOGY.md` — 15 domains, 78 node types, 204 relationships
   - `docs/architecture/construction-ontology.html` — interactive visualization
   - `backend/graph/schema.cypher` — 213 constraints/indexes (Neo4j DDL)

2. **Key ontology changes in v2.3:**
   - Removed all `company_id` properties from nodes (graph-native tenant isolation via relationships)
   - Removed all redundant FK `_id` properties (relationships replace joins)
   - Renamed PunchList/PunchItem → DeficiencyList/DeficiencyItem (jurisdiction-neutral)
   - Added 5 Quality nodes: NonConformanceReport, Observation, InspectionTestPlan, ITPCheckpoint, MaterialTestRecord
   - Added AgentIdentity cost control fields (model_tier, daily_budget_cents, daily_spend_cents)
   - Added Actor Provenance fields (model_id, confidence)
   - Added temporal validity (valid_from, valid_until) to Regulation nodes
   - Renamed Budget.budget_type → contract_type with enum values

3. **Build plan** — designed a 6-phase plan covering database migration + agentic infrastructure

---

## What's Been Built (Phases 0–3)

### Services rewritten: 21 of 24

All services now extend `BaseService` and use Neo4j graph traversals.

| Batch | Services | Tests |
|-------|----------|-------|
| Phase 0 | base_service.py, models/actor.py, conftest.py | Neo4j fixtures, per-test cleanup |
| 1A | company, project, member, invitation, project_assignment | All passing |
| 1B | worker, equipment | All passing |
| 1C | inspection, incident, hazard_report, toolbox_talk | All passing |
| 1D | osha_log, environmental, document | All passing |
| 2A | morning_brief, billing, gc_portal, state_compliance | All passing |
| 2B | analytics, mock_inspection, prequalification | All passing |

### Key patterns established
- Graph traversal: `MATCH (c:Company {id})-[:OWNS_PROJECT]->(p:Project)-[:HAS_*]->(entity)`
- JSON serialization: complex nested data stored as `_*_json` string properties
- Provenance: every mutation records `created_by, actor_type, agent_id, model_id, confidence`
- No `company_id` on child nodes — derived from graph path
- `_to_model()` static methods deserialize JSON fields back to Pydantic models

### Phase 4: P0 Agentic Infrastructure

| Component | File | Description |
|-----------|------|-------------|
| AgentIdentity model | `app/models/agent_identity.py` | Pydantic models: AgentIdentityCreate, AgentIdentity, AgentIdentityUpdate, AgentSpendReport |
| AgentIdentityService | `app/services/agent_identity_service.py` | CRUD, suspend/kill-switch, spend recording, budget enforcement, daily reset, spend reports, verify_agent_access |
| LLMService | `app/services/llm_service.py` | Anthropic wrapper with per-agent cost tracking, model tier routing, circuit breaker (5-min window, $5 threshold, 10-min cooldown) |
| Agent admin router | `app/routers/agents.py` | REST endpoints: register, list, get, update, suspend, spend report, reset spend |
| Extended permissions | `app/dependencies.py` | verify_company_access now supports both human users and agent identities via graph traversal |
| Agent exceptions | `app/exceptions.py` | AgentNotFoundError, AgentBudgetExceededError |

### Phase 5: P1 Agentic Infrastructure

| Component | File | Description |
|-----------|------|-------------|
| Event models | `app/models/events.py` | Event envelope (event_id, entity_id, actor, summary, graph_context), EventType enum (10 coarse types) |
| EventBus | `app/services/event_bus.py` | In-process pub/sub: typed subscriptions, filtered dispatch, retry with dead-letter, IdempotencyStore (TTL-based, swappable for Redis) |
| Guardrails models | `app/models/guardrails.py` | ActionClass enum (read_only/low_risk_write/high_risk_write), ApprovalRequest, GuardrailCheckResult |
| GuardrailsService | `app/services/guardrails_service.py` | Pre-execution guard: scope check, rate limiting (sliding window), budget check, approval queue (Neo4j-backed). Tool→action classification map. |
| MCPToolService | `app/services/mcp_tools.py` | 8 intent-based tools: check_worker_compliance, check_project_compliance, get_project_summary, get_worker_profile, generate_morning_brief, report_hazard, report_incident, get_changes_since. Unified invoke_tool dispatcher with guardrails integration. |
| Event bus tests | `tests/test_event_bus.py` | 23 tests: idempotency store, event model, subscribe/emit/filter, retry, dead-letter |
| Guardrails tests | `tests/test_guardrails.py` | 21 tests: classification, scope checking, rate limiter, pre-execution checks (Neo4j), approval queue CRUD |
| MCP tool tests | `tests/test_mcp_tools.py` | 17 tests: all 8 tools tested, event emission, invoke_tool dispatch, scope denial |

**Key design decisions in Phase 5:**
- In-process EventBus (not Cloud Pub/Sub) — sufficient for single-instance, production swaps dispatch only
- Tools write directly to Neo4j (not through existing services) to avoid circular dependencies
- Guardrails run BEFORE tool dispatch — scope/rate/budget checked first, then action class routing
- High-risk writes go to Neo4j ApprovalRequest nodes (not in-memory) — persistent queue
- Write tools (report_hazard, report_incident) emit domain events after mutation

### Phase 6: First Agents

| Component | File | Description |
|-----------|------|-------------|
| Agent output models | `app/models/agent_outputs.py` | ComplianceAlert (alert_type, severity, entity_id, message, details, graph_evidence) and BriefingSummary (project_id, date, alerts, llm_summary, cost_cents, model_id) |
| ComplianceAgent | `app/services/compliance_agent.py` | Read-only agent — handles 4 event types (inspection.completed, worker.assigned_to_project, certification.expiring, corrective_action.overdue). Uses check_worker_compliance and check_project_compliance via invoke_tool(). Produces ComplianceAlert nodes in Neo4j. No LLM calls — pure graph traversal. |
| BriefingAgent | `app/services/briefing_agent.py` | Low-risk write agent — generates morning briefs. Uses generate_morning_brief, get_project_summary, get_changes_since via invoke_tool(). Feeds structured data to LLMService for natural language summary. Persists BriefingSummary nodes in Neo4j. Cost-tracked via LLMService. |
| AgentOrchestrator | `app/services/agent_orchestrator.py` | Idempotent agent registration, EventBus subscription wiring, on-demand entry points (run_compliance_check, run_briefing). Graceful error handling — agent errors logged, never crash the service. |
| Mock allowlist | `tests/.mock-allowlist` | Declares anthropic.Anthropic as the only external dependency allowed to be mocked. |
| Agent tests | `tests/test_agents.py` | 33 tests across 10 test classes: ComplianceAgent event handlers (inspection, worker assignment, cert expiring, corrective action), on-demand checks, BriefingAgent generation + persistence + cost tracking, Orchestrator registration + idempotency + event wiring + on-demand + error handling, model serialization. |

**Key design decisions in Phase 6:**
- ComplianceAgent is intentionally read-only — no LLM, pure graph traversal for deterministic auditability
- BriefingAgent uses LLM for text generation only — structured data assembled from MCP tools first
- AgentOrchestrator uses idempotent registration — safe to call repeatedly without creating duplicates
- ComplianceAlerts stored as Neo4j nodes with (Company)-[:HAS_COMPLIANCE_ALERT]->(ComplianceAlert) relationship
- BriefingSummaries stored as Neo4j nodes with (Company)-[:HAS_BRIEFING]->(BriefingSummary) relationship
- Agent event handlers catch all exceptions internally — never propagate errors to the EventBus
- Anthropic API is the only mocked dependency (declared in .mock-allowlist)

### Services NOT requiring rewrite (7)
- `auth_service.py` — Clerk JWT (no DB)
- `neo4j_client.py` — already Neo4j
- `generation_service.py` — Anthropic API only
- `hazard_analysis_service.py` — Anthropic Vision API only
- `voice_service.py` — Twilio/transcription only
- `pdf_service.py` — PDF generation only
- `inspection_template_service.py` — stateless/hardcoded

---

## Current Codebase State

### What's WORKING
- **Neo4j driver** (`backend/app/services/neo4j_client.py`) — production-ready singleton
- **All 21 services** — fully migrated to Neo4j
- **Clerk auth** (`backend/app/services/auth_service.py`) — JWT verification via JWKS
- **Dependencies** (`backend/app/dependencies.py`) — Neo4j Driver injection + Clerk auth
- **170 tests** — all passing against Neo4j
- **Schema** (`backend/graph/schema.cypher`) — constraints across 7 implemented domains
- **Frontend Clerk** — ~95% complete, dual-mode (Clerk + demo fallback)
- **Jurisdictions** — 4 YAML packs (US, UK, CA, AU)
- **Demo mode** — works without Neo4j or Clerk configured

### What's NOT broken
- Zero Firestore references in services or tests
- Rate limiter disabled in test environment

---

## Remaining Work (Phases 4–6)

### Phase 2 (partial): Context Assembler
- New `context_assembler.py` service that traverses the graph to build structured context for LLM agents
- Prerequisite for Phase 5 (MCP server tools)

### Phase 4: P0 Agentic Infrastructure [3-5 days]
- AgentIdentity nodes + CRUD service
- Graph-native permissions (extend `verify_company_access()`)
- LLM service with cost control, budgets, circuit breaker
- Agent admin endpoints (register, suspend, kill switch, spend reports)

### Phase 5: P1 Agentic Infrastructure [5-8 days]
- Event backbone (coarse types, idempotent, in-process pub/sub)
- MCP server (8 intent-based tools)
- Guardrails (action classification, approval queue, rate limits)

### Phase 6: First Agents [3-5 days]
- Compliance Agent (read-only, watches for violations)
- Briefing Agent (low-risk write, generates morning briefs)

---

## Key Design Decisions

1. **Provenance from day one** — baked into service rewrites (Phase 1), not retrofitted. Every mutation records: `created_by, actor_type, agent_id, model_id, confidence, created_at`
2. **Graph-native permissions** — no ACL table. Permission = traversability through graph edges
3. **No FK properties** — all references are relationships, never `_id` properties on nodes (Design Principle #8 in ontology)
4. **No company_id on nodes** — tenant isolation via `(Company)-[:OWNS/HAS]->(Data)` graph paths (Design Principle #6)
5. **Intent-based MCP tools** — `check_compliance(project_id, worker_id)` not 5 separate CRUD calls
6. **Demo mode preserved** — app must work without Neo4j/Clerk configured
7. **Only 7 domains** — future domains validated before encoding

## Key Reference Files

| File | Purpose |
|------|---------|
| `docs/architecture/CONSTRUCTION_ONTOLOGY.md` | Source of truth for graph schema |
| `docs/architecture/AGENTIC_ARCHITECTURE.md` | Kerf-specific agentic design (events, MCP, agents) |
| `~/.claude/rules/AGENTIC_INFRASTRUCTURE.md` | Product-agnostic agentic playbook v2.1 |
| `backend/graph/schema.cypher` | Neo4j DDL |
| `backend/app/services/base_service.py` | BaseService with provenance helpers |
| `backend/app/models/actor.py` | Actor identity model |
| `backend/app/services/neo4j_client.py` | Transaction helpers every service uses |
| `backend/app/dependencies.py` | DI wiring |
| `backend/jurisdictions/` | 4 jurisdiction YAML packs for seed script |

## Start Here (for next phase)

**Phases 0–6 complete.** 334/334 tests passing. All services migrated to Neo4j, full agentic infrastructure deployed, first two production agents running.

Next steps (if continuing):
1. MCP server HTTP layer — expose `invoke_tool()` via FastMCP or SSE transport
2. Agent REST API — expose `run_compliance_check()` and `run_briefing()` as admin endpoints
3. Scheduled agent runs — cron for daily briefings and compliance sweeps
4. A2A Agent Cards — publish `.well-known/agent.json`
