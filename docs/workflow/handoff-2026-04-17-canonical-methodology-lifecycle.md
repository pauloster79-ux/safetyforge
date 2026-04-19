# Handoff — Canonical Categories, Methodology, Lifecycle Flow

**Date:** 2026-04-17
**From:** Long working session covering research + canonical categories build + methodology schema + pre-work for project lifecycle state machine
**Next session picks up:** Collaborative lifecycle state machine design (Paul wants persona walkthrough approach)

---

## TL;DR for the next session

1. **Read first, in this order** (each is self-contained):
   - `docs/design/canonical-work-categories.md` — the plan for the canonical category work
   - `docs/design/methodology.md` — the methodology cascade + approach-map design
   - `docs/design/research/lifecycle-01-contract-conventions.md`
   - `docs/design/research/lifecycle-02-competitor-state-handling.md`
   - `docs/design/research/lifecycle-03-variation-and-payment.md`
   - `C:\Users\paulo\.claude\projects\C--Users-paulo-Documents-GitHub-safetyforge\memory\MEMORY.md` (feedback files + jurisdiction scope)

2. **Backend canonical categories work is ~80% done.** Schema changes, validation queries, loader script, service extensions, router, and `CATEGORISED_AS` wiring are all in place. Remaining: Methodology service/MCP tools (schema is ready), runtime source enforcement tightening on `create_labour`/`create_item`, Knowledge page frontend enhancements, and a live Neo4j test.

3. **Paul's next move is the lifecycle state machine.** He's chosen option 2 from the last message: **persona walkthrough**. Trace Jake through a residential kitchen remodel end-to-end (lead → quote → signed → active → variations → complete → invoiced → closed → warranty → fully closed). Every state change is an explicit decision. Paul drives; Claude facilitates with research grounding.

4. **Open research questions for the walkthrough** — see §6 below.

---

## 1. What is done

### Design docs
- `docs/design/canonical-work-categories.md` — full plan (jurisdictions, three-layer model, schema changes, phases, risks)
- `docs/design/methodology.md` — Methodology node data model, cascade, Insight attachment, conversational authoring, UI integration
- `docs/design/work-item-ui.md` — WorkItem/WorkPackage UI plan (methodology as first-class §10 after the strengthening pass)
- `docs/design/estimating-intelligence.md` — prior design, the source cascade and Insight loop (unchanged this session)

### Research outputs (persisted)
- `docs/design/research/lifecycle-01-contract-conventions.md` — universal states, roles, lock points across AIA/CCDC/JCT/NEC4/RIAI/AS 4000/NZS 3910
- `docs/design/research/lifecycle-02-competitor-state-handling.md` — Procore, Buildertrend, CoConstruct, JobTread, Knowify, Contractor Foreman, Houzz Pro, ServiceTitan, Jobber, JobNimbus, ACC, CMiC state models
- `docs/design/research/lifecycle-03-variation-and-payment.md` — variation mechanics, progress payments, retention, close-out, immutability rules per jurisdiction

### Canonical work categories — backend
- `backend/graph/schema.cypher` — added `:Canonical` label indexes (jurisdiction_code, code, level), Methodology node constraints + indexes
- `backend/fixtures/golden/validation-tests.cypher` — appended V-CAT-01..05 (canonical integrity), V-METH-01..05 (methodology integrity), V-SRC-01..04 (source enforcement)
- `backend/jurisdictions/us/work_categories.yaml` — 617 MasterFormat categories
- `backend/jurisdictions/ca/work_categories.yaml` — inherits_from US stub
- `backend/jurisdictions/uk/work_categories.yaml` — 295 NRM 2 categories
- `backend/jurisdictions/ie/work_categories.yaml` — inherits_from UK stub with label_overrides scaffolding
- `backend/jurisdictions/au/work_categories.yaml` — 180 NATSPEC categories
- `backend/jurisdictions/nz/work_categories.yaml` — inherits_from AU stub (NATSPEC fallback; long-term Masterspec)
- `backend/scripts/load_canonical_work_categories.py` — idempotent loader, supports inherits_from and label_overrides
- `backend/app/services/work_category_service.py` — extended with `list_canonical`, `list_for_company`, `add_alias`, `add_extension`, `resolve_for_work_item`
- `backend/app/routers/work_categories.py` — new router exposing `/me/work-categories/canonical`, `/me/work-categories`, `/me/work-categories/aliases`, `/me/work-categories/extensions`, `/me/work-categories/{category_id}`
- `backend/app/dependencies.py` — added `get_work_category_service`
- `backend/app/main.py` — router wired at `/api/v1`

### CATEGORISED_AS wiring
- `backend/app/services/work_item_service.py` — `create()` accepts `work_category_id`, writes `CATEGORISED_AS` atomically with the node, validates access (Canonical global, Extension scoped to company)
- `backend/app/services/mcp_tools.py` — `create_work_item` accepts `work_category_id` and writes the relationship; dispatch registry updated
- `backend/app/services/chat_service.py` — `create_work_item` tool schema updated with `work_category_id` param + description encouraging its use

### Memory
- `memory/product_jurisdiction_scope.md` — all countries long-term; Wave 1 = US/CA/UK/IE/AU/NZ; NZ correction (uses Masterspec not NATSPEC; short-term NATSPEC fallback)
- `memory/feedback_no_duration_estimates.md` — don't give duration estimates

### Preview updates (earlier in the session, persisted)
- `docs/preview/work-items.html` — added Source Detail tab, Active Tracking tab, Category + Methodology rows on cards, Items (not Material) terminology, side-by-side With/Without Methodology anatomy

### Verified
- All modified Python files parse cleanly
- All 6 YAMLs parse, category counts confirmed (617 US, 295 UK, 180 AU)
- Loader flattening logic tested — parent_code wiring is correct for all three canonical trees

---

## 2. What is pending (backend)

Not blocking the lifecycle design work. Do in parallel or after.

### Methodology service + MCP tools
Schema is in place (`Methodology` node, `USES_METHODOLOGY`, `CHILD_OF`, `APPLIES_TO_CATEGORY`, `APPLIES_TO_METHODOLOGY_WITH`, validation queries). Need to build:
- `backend/app/services/methodology_service.py` — `create`, `get`, `resolve_cascade`, `update`, `supersede`, `list_for_project`
- `backend/app/routers/methodology.py` — REST surface
- `backend/app/services/mcp_tools.py` — MCP tools: `create_methodology`, `resolve_methodology`, `update_methodology_approach`, `retrieve_past_methodologies_for_category`

Driver data model is in `docs/design/methodology.md` §3.

### Runtime source enforcement tightening
Current state:
- Schema validation queries `V-SRC-01..04` exist in `validation-tests.cypher` (will fail CI if violated)
- `create_labour` and `create_item` accept source_* fields but don't enforce them at runtime

Change needed in `mcp_tools.create_labour` and `mcp_tools.create_item`:
- If `rate_source_id` is provided, verify it references an active ResourceRate owned by the company (reject if not)
- If `price_source_id` is provided, verify it references a MaterialCatalogEntry
- If neither source_id nor `contractor_stated` tag is provided, add a WARNING log (not reject — BC concern)

See `docs/design/estimating-intelligence.md` §9 (BR-EST-030, BR-EST-050, etc.) for the full spec. Phase 1a.

### Knowledge page enhancements
Frontend work in `frontend/src/components/knowledge/KnowledgePage.tsx`:
- Usage reverse-lookup on rate rows ("used on these 12 past quotes" when clicked)
- Category filter (once canonical categories are loaded, filter rates by category)
- Material catalog browser (today only a count card — need a list view)
- Fix mobile nav — KnowledgePage isn't reachable on mobile; `frontend/src/components/shell/IconRail.tsx` `MOBILE_ITEMS` only shows the first 4 entries + a "More" button that hardcodes AnalyticsPage. Wire "More" to a real overflow sheet including Knowledge.

### Live Neo4j test
Run against a Neo4j test instance:
```bash
cd backend
# apply schema
cypher-shell < graph/schema.cypher
# load canonical categories
python -m scripts.load_canonical_work_categories
# run validation queries
cypher-shell < fixtures/golden/validation-tests.cypher
```

Then hit the API:
- `GET /api/v1/me/work-categories/canonical?jurisdiction_code=us` — expect 617 categories
- `POST /api/v1/me/work-categories/aliases` with `{canonical_id, display_name}` — expect 201 + alias metadata
- Create a WorkItem via MCP with `work_category_id` → verify `CATEGORISED_AS` edge in graph

---

## 3. Key decisions locked this session

1. **Canonical-first taxonomy per jurisdiction.** MasterFormat for US/CA, NRM 2 for UK/IE, NATSPEC for AU (fallback for NZ until Masterspec). Companies can alias canonical names and extend with private leaves, but cannot create top-level custom categories. See `docs/design/canonical-work-categories.md`.

2. **Licensing: deferred purchase.** Implementation proceeds using publicly-documented taxonomy structure. CSI/RICS/NATSPEC licences to be reviewed when customer volume justifies. See jurisdiction scope memory file.

3. **Methodology emergent, not authored.** No pre-built methodology library — `approach` map keys emerge from contractor conversations. Cascades Project → WorkPackage → WorkItem. Insights attach to methodology via `APPLIES_TO_METHODOLOGY_WITH {approach_match: {...}}`. See `docs/design/methodology.md`.

4. **Items, not Materials.** Per data model: WorkItem's children are `Labour` + `Item` (where "Item" covers materials, equipment, subs). UI + docs corrected to this terminology.

5. **Search-first category picker.** Not per-node residential flags. Full canonical tree available; search surfaces the right node.

6. **NZ uses Masterspec canonically**, but NATSPEC AU tree is the Wave 1 fallback (no public Masterspec code data available).

7. **No duration estimates in status updates** (see `feedback_no_duration_estimates.md`).

---

## 4. Tech state references

- `docs/architecture/DECISIONS.md` — 30 ADRs (canonical categories ADR not yet added; worth adding)
- `docs/architecture/CONSTRUCTION_ONTOLOGY.md` — full ontology reference (also pre-dates canonical-category additions)
- `docs/architecture/JURISDICTION_ABSTRACTION.md` — jurisdictional content pattern
- `docs/PRODUCT_VISION.md`, `docs/PRODUCT_STRATEGY.md` — product north star

---

## 5. Next session — lifecycle state machine (primary focus)

Paul has chosen the **persona walkthrough** approach. The plan:

### How we'll do it
Trace Jake Torres through a residential kitchen remodel, end to end. Each state change is an explicit decision we make together — not a diagram dropped into a doc.

Journey outline:
1. Lead comes in (client calls Jake)
2. Jake creates project, gets to site, narrates scope
3. Kerf drafts WorkItems with categories (using the canonical tree we just built)
4. Jake reviews, tweaks, confirms
5. Quote generated, sent to client
6. Client accepts — **the immutability transition** (contract sum locks, scope becomes variation-only)
7. Work starts — time entries log against WorkItems
8. Client asks for extras mid-job — variation created
9. Builder variance detected on one WorkItem (running over) — flagged
10. Substantial/Practical Completion — half retention releases, DLP starts
11. Final invoice, final payment
12. DLP runs; a defect is raised and fixed
13. Retention fully released, project goes to CLOSED
14. Warranty period continues as overlay; eventually expires

At each transition Paul decides:
- What triggers it (user / agent / time / external event)
- Who has authority
- Automatic vs user-confirmed
- What becomes read-only
- What's added, what's removed
- What the client sees via magic-link portal

### Open research questions to have at hand
- Universal states: `DRAFT → TENDER → AWARDED → COMMENCED → IN_PROGRESS → PRACTICAL_COMPLETION → DEFECTS_LIABILITY → FINAL_COMPLETION → CLOSED` (from research #1)
- Three universal roles: Owner/Principal, Contract Administrator/Certifier, Contractor (abstract, per-jurisdiction concrete names)
- Three universal change mechanisms: mutual change / unilateral directive / minor de minimis
- Immutability rules at each lock point (from research #3 §6)
- Overlays: Suspended / Disputed / On Hold (typed reasons — Kerf opportunity)
- Sub-object state independence (WorkItem states vs Project state)

### Edge cases Paul wants to pin down
- LOST revived (client returns months later — fresh record, or revive with context? Research suggests no one handles this well; Kerf opportunity)
- ACTIVE paused to On Hold with typed reason + re-engagement timer
- Variation during active — approved before vs after work done (quantum meruit risk in US; curtailed in AU post-*Mann v Paterson*)
- Close-out reconciliation with timed auto-close ("SC + 30 days unless open items")
- Abandoned mid-execution — distinct from closed-complete for margin reporting

### Deliverable
`docs/design/project-lifecycle-flow.md` co-authored as we go. Not a one-shot document.

### Suggested session opening prompt
> "Let's do the lifecycle walkthrough. Start with Jake. Client just called him about a kitchen remodel. What's the state, what's possible, what's next?"

---

## 6. Product context reminder

Three personas:
- **Marco Gutierrez** — 22-person concrete crew, Phoenix, bilingual (ES/EN), 3 active projects, runs everything from phone
- **Sarah Chen** — 45-person electrical firm, Atlanta, commercial GC sub, needs financial intelligence from daily ops
- **Jake Torres** — solo electrician, newly independent, estimates in his head today, needs to look professional

Kerf development process per `CLAUDE.md`:
- No mocks for internal services/APIs/DB
- Full-stack completion before declaring done
- Persona-based exploratory testing with rich golden data
- Test end-to-end before declaring done
- Don't commit — human commits

Jurisdictional scope: all countries long-term; Wave 1 = US/CA/UK/IE/AU/NZ.

---

## 7. Open repo state (for the fresh session)

Git status when handing off:
- Many modified files (backend services + routers, schema, validation, YAMLs, preview HTML, design docs)
- New files: research outputs, methodology design, handoff doc
- None committed (CLAUDE.md rule: human commits)

Fresh session should:
1. Read this handoff + the 6 reference files listed in TL;DR §1
2. Read `MEMORY.md` (feedback + jurisdiction scope)
3. Open a terse chat: "Ready to start the persona walkthrough — Jake gets a kitchen remodel call. Kick us off."
