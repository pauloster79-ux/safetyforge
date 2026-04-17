# Handoff: Layer 5 — Safety & Regulatory Compliance During Quoting

**Date:** 2026-04-17
**From:** Layer 4 (knowledge accumulation) session — layers 1-4 complete and validated
**To:** Layer 5 (compliance) session

---

## Where the build is

Phase 0 + layers 1-4 of the quote process are done. End-to-end working:

- **Phase 0 foundations** — audit events, provenance badges, activity stream, graph query canvas, architectural decision registry, process rules in `CLAUDE.md`
- **Layer 1** — plumbing fixes (cards show real numbers, auto-nav, assumption/exclusion CRUD, delete on work items)
- **Layer 2** — quote review surface with inline editing + contract terms (PaymentMilestone, Condition, Warranty, Retention all as graph nodes + editable UI sections)
- **Layer 3** — source cascade and citation. Every number in a quote has a verifiable source. Labour rates from ResourceRate, productivity from ProductivityRate/Insight/IndustryBaseline, materials from purchase history → catalog → search → ask. Source text shown inline on labour/item rows, full sources panel at bottom of estimate
- **Layer 4** — knowledge accumulation. Insights captured from contractor reasoning, surfaced on future quotes with confidence scoring, multiplicatively combined when multiple apply. Validated across 4 personas (Sarah, Marco, Jake, David). Semantic equivalence matching lets "warehouse_conversion" find a `renovation_electrical` scoped Insight.

Layer 4 validation concluded with full round of testing. Knowledge page exists at `/knowledge` with Insights/Rates/Productivity tabs.

---

## Layer 5 evaluation criteria (agreed with Paul)

The product vision's "safety is the connective tissue" belief made concrete. During quoting, Kerf traverses the regulatory graph and flags required certifications, inspections, PPE, and jurisdiction-specific requirements.

### Decisions locked in

**Activity structure:** Option (b) — add a structured `Activity` node type. `(WorkItem)-[:INVOLVES]->(Activity)-[:REGULATED_BY]->(Regulation)-[:REQUIRES_CERT]->(CertificationType)`. The vision explicitly says regulatory rules should be traversable graph structure, not text interpretation.

**Severity tiers:**
- **Fatal** — blocks quote from being sent as proposal. "You cannot legally do this work with current credentials."
- **Required** — warns prominently, does NOT block. "Legally required but contractor can override."
- **Advisory** — info only.

**UI surfaces (all of them):**
- Banner at top of Contract tab: "⚠ 3 compliance items need attention"
- Small indicator on each WorkItem row where issues exist
- Dedicated Compliance tab on project detail (full picture, resolve options)
- Compliance section on the generated proposal PDF (professionalism + liability protection)

**Kerf chat behaviour:** Always check compliance on every WorkItem creation. Always mention issues. This is the USP — no other construction tool does this from a quote context.

**Scope for Layer 5:** Trade/safety compliance only. Insurance and bonding (commercial terms) stay in Layer 2 territory. Prequalification is Phase 3 material.

**Multi-jurisdiction from day one.** Jurisdiction packs for US/UK/CA/AU already exist. Project reads its location (city/us_state/region — all added in Layer 3). Agent queries regulations scoped to jurisdiction.

### Persona test scenarios

**Round 1 — Marco (GP08, Austin TX):** Quote a foundation excavation job with trenching >5ft, utility-adjacent excavation, and concrete pour. Should surface OSHA 1926.651 competent-person-for-trenching cert, 811 one-call ticket requirement, silica exposure plan, heat illness plan.

**Round 2a — Sarah (GP02, Atlanta GA):** Medical office electrical fit-out. Should surface OSHA 30, arc flash training, electrical permit, hospital-grade outlet requirements.

**Round 2b — Ryan (GP06, Victoria BC Canada):** School renovation on 1985 building. Should surface WorkSafeBC requirements, asbestos risk assessment for pre-1990 construction, public-facility working-hours constraints.

Test as the persona. Report as product owner, not developer.

---

## What exists in the codebase

### Backend — ready to extend

`backend/graph/schema.cypher` already has these node types seeded by `backend/scripts/seed_regulatory_graph.py`:
- `Jurisdiction` (US, UK, CA, AU)
- `Region` (states/provinces within jurisdictions)
- `RegulatoryGroup` (OSHA, HSE, WorkSafeBC, etc.)
- `Regulation` (individual regulations with CFR/HSE codes)
- `CertificationType` (OSHA 10, OSHA 30, confined space, etc.)
- `ComplianceProgram` — aggregations
- `DocumentType` — required documents per jurisdiction

The regulatory graph is populated from YAMLs in `backend/jurisdictions/{US,UK,CA,AU}/`. Check those before re-creating data.

### What's missing (Layer 5 adds this)

- **`Activity` node type** — not yet in the graph. Needs schema.cypher entry + seed.
- **`WorkItem -[:INVOLVES]-> Activity` relationship** — the link from quote to compliance requirement.
- **`Activity -[:REGULATED_BY]-> Regulation` relationship** — probably needs seeding in jurisdiction packs.
- **Compliance check service** — traverses from WorkItem → Activity → Regulation → CertificationType, then checks which certs the company's workers hold.
- **MCP tools** — `check_work_item_compliance`, `check_project_compliance`, `get_applicable_regulations`, `explain_compliance_requirement`.
- **Severity classification** — currently Regulations don't have severity tagged. Need to add or derive.
- **UI** — ComplianceTab, inline indicators, banner.

### Existing compliance-adjacent code to learn from

- `backend/app/services/compliance_agent.py` — existing agent that checks worker compliance. Read before writing the new service. Some of this may be reusable.
- `backend/app/services/mock_inspection_service.py` — existing code that generates safety documents. Touches the regulatory graph.
- `backend/app/services/mcp_tools.py` — `check_worker_compliance`, `check_project_compliance`, `check_compliance` exist as MCP tools but they work on an existing project, not during quote. May need wrapping/extending rather than duplicating.

### Data model additions needed

```cypher
// Activity — a type of work that triggers regulatory requirements
CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.id IS UNIQUE;
CREATE INDEX activity_name IF NOT EXISTS FOR (a:Activity) ON (a.name);

// Activity examples: "excavation_trenching_over_5ft", "work_at_height", "confined_space_entry",
// "hot_work", "electrical_energized", "demolition", "asbestos_disturbance"

// WorkItem links to Activities (many-to-many)
// (WorkItem)-[:INVOLVES]->(Activity)

// Activity is regulated by Regulations (many-to-many, jurisdiction-scoped)
// (Activity)-[:REGULATED_BY {jurisdiction: 'US'}]->(Regulation)

// Severity on the REGULATED_BY edge or on the Regulation itself:
//   severity: 'fatal' | 'required' | 'advisory'
```

### Where to start data-wise

1. Seed a dozen common activities and their US-OSHA regulation links. Start with what the personas will hit: trenching, work at height, hot work, electrical, confined space, asbestos.
2. Add equivalents in UK/CA/AU jurisdiction packs.
3. Teach the agent (via MCP tool description) how to infer activities from WorkItem descriptions — or expose a tool `tag_activities(work_item_id, activities[])` that persists the relationship.

---

## Build sequence recommendation

1. **Data model + schema + seed** — Activity node, relationships, severity field, seed ~15-20 activities with OSHA links for the US. UK/CA/AU can follow but US first for MVP.
2. **Backend compliance service** — traverses WorkItem → Activity → Regulation → CertificationType → Worker holdings. Returns structured results with severity.
3. **MCP tools** — `check_work_item_compliance(work_item_id)`, `check_project_compliance(project_id)`, `tag_work_item_activities(work_item_id, [activities])` to link work items to activities.
4. **System prompt** — teach the agent: after create_work_item, always call tag_activities and check_compliance. Mention any Required or Fatal issues.
5. **Frontend** — ComplianceTab, banner on Contract tab, inline indicators on WorkItem rows.
6. **Proposal integration** — compliance section on generated proposal PDF.
7. **Persona test** — Marco trenching scenario, then the others.

---

## Critical files to read first (in this order)

1. `CLAUDE.md` (project root) — development process, persona-testing rule, no mocks
2. `docs/PRODUCT_VISION.md` — especially section 3.10 "Cross-Cutting: Safety and Compliance" and the beliefs block
3. `docs/architecture/DECISIONS.md` — ADR-017 (Regulation-Activity-Cert graph edges, not trade-based), ADR-015 (jurisdiction data packs), ADR-010 (compliance audit = graph traversal + Claude)
4. `backend/graph/schema.cypher` — full graph schema, includes existing regulatory nodes
5. `backend/scripts/seed_regulatory_graph.py` — how existing regs get loaded
6. `backend/jurisdictions/US/regulations.yaml` (and /UK, /CA, /AU) — existing regulatory data
7. `backend/app/services/compliance_agent.py` — existing compliance logic to learn from/extend
8. `backend/app/services/mcp_tools.py` — existing check_compliance tools to avoid duplicating
9. `backend/app/services/chat_service.py` — system prompt + tool registration patterns

---

## Testing protocol (MANDATORY)

Per `~/.claude/projects/.../memory/feedback_exploratory_testing.md` — persona-based testing is the ritual, not verify-mode.

- Switch to product-owner mode EXPLICITLY before calling anything done.
- Anchor on persona + goal ("I'm Marco, quoting a 15ft deep foundation trench in August Texas heat"), not "test compliance tool."
- Use the UI via browser preview, not just the API. Click, type like a tired human.
- Chain actions. Create the WI → check compliance surfaces → revise scope → check it updates → generate proposal → verify compliance section appears.
- Use ambiguous references ("the trenching one") not IDs.
- Report as product owner: cuts, bugs, UX issues, vision alignment. Not pass/fail.

---

## Known state of app

- Backend: FastAPI on port 8000 (`~/.claude` launch.json)
- Frontend: Vite on port 5174 (5173 is 5Seasons project — don't fight it)
- Neo4j: localhost:7687, user `neo4j`, password `fiveseasons2026` (in `backend/.env`)
- Demo users: `demo-token-gp01` through `demo-token-gp10` map to 10 seeded golden companies
- 5 Seasons and Kerf both run Vite, Kerf is configured to use port 5174 via `.claude/launch.json`

---

## Things to NOT break

- Layer 4's Insight matching — uses fuzzy token overlap with semantic equivalences in `backend/app/services/insight_service.py`. Don't revert.
- The source_reasoning fields on Labour/Item — they're the trust story. Preserve them.
- The project lifecycle enforcement (`_verify_has_work_items` in `project_service.py`) — projects can't go ACTIVE without work items.
- The golden data — 9 active projects have WorkItems, don't re-seed destructively.

---

## Open design questions (flag early in next session)

- **Severity assignment:** Where does severity live? On Regulation nodes (simplest), on the REGULATED_BY edge (allows context-specific severity), or derived by a rule? Probably edge-level so "working at 4ft" can be Advisory but "working at 12ft" is Fatal.
- **Activity inference:** Agent-inferred vs contractor-tagged vs both? Recommend both — agent suggests, contractor confirms/edits.
- **Unmet-cert handling:** When a work item requires OSHA 30 and no one on the crew holds it, what does the UI show? "Assign a certified worker" / "Add a sub with this cert" / "Generate a compliance gap action item"?
- **Proposal compliance section:** Should the client see unmet items or only the compliance framework ("this work follows OSHA 1926.x")? Contractor might not want to show their gaps to the client.

Do a quick plan-mode discovery before building to settle these.
