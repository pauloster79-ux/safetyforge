# Canonical Work Categories — Design & Implementation Plan

**Status:** Draft for review
**Author:** Claude + Paul
**Date:** 2026-04-17
**Scope:** Replace the current company-scoped `WorkCategory`-only model with a canonical-first taxonomy per jurisdiction, seeded from industry-standard taxonomies (MasterFormat, NRM 2, NATSPEC), with thin company overlays for aliases and private leaf extensions. Wire `CATEGORISED_AS` into WorkItem creation. Connect the commercial work graph to the regulatory graph.
**Depends on:** None — this is P0 foundational work for estimating intelligence.
**Related:** [estimating-intelligence.md](estimating-intelligence.md) | [../architecture/CONSTRUCTION_ONTOLOGY.md](../architecture/CONSTRUCTION_ONTOLOGY.md) | [../knowledge-graph/04-design-decisions.md](../knowledge-graph/04-design-decisions.md) (DD-08)

---

## 1. The Problem

Two issues compound:

**1. `CATEGORISED_AS` is never written.** Four services (`estimating_service.py`, `mcp_tools.py`, `resource_rate_service.py`) `OPTIONAL MATCH` the relationship, but nothing in the codebase creates it. Every WorkItem is uncategorised. This breaks:

- Regulatory bridge: `WorkCategory -[:LINKS_TO_ACTIVITY]-> Activity -[:REGULATED_BY]-> Regulation`
- `ProductivityRate` lookup via `PRODUCTIVITY_FOR_CATEGORY`
- Any cross-project comparison of similar work

**2. The design is fully company-scoped.** [DD-08](../knowledge-graph/04-design-decisions.md) specifies "each company defines their own classification." This gives up:

- Cross-tenant benchmarking — "other contractors like you take X hours/LF for EMT" requires "EMT" to mean the same thing across tenants
- `IndustryProductivityBaseline` seeding — must be done per-company instead of once for everyone
- `LINKS_TO_ACTIVITY` regulatory mappings — duplicated per company
- Interoperability with external estimating software, GC cost codes, BIM exports — all speak in standard taxonomies

Industry has already solved this. MasterFormat, NRM, and NATSPEC are the lingua franca of construction. Adopt them as canonical, with thin per-company overlays for aliasing and specialisation.

---

## 2. Design

### 2.1 Three-layer model

**Layer 1 — Canonical** (shared, system-maintained, per-jurisdiction)

- Sourced from industry-standard taxonomies
- Labelled `:WorkCategory:Canonical`
- Property `jurisdiction_code` indexes by country (`us`, `uk`, `ca`, `au`)
- All `IndustryProductivityBaseline` attaches here
- All `LINKS_TO_ACTIVITY` regulatory mappings attach here
- Cross-tenant benchmarks aggregate here
- Contractors cannot create or delete canonical nodes

**Layer 2 — Company overlay** (tenant-specific, optional)

- `(Company)-[:HAS_ALIAS {display_name}]->(cat:WorkCategory:Canonical)` — rename for contractor's vocabulary without forking the taxonomy
- `(Company)-[:HAS_EXTENSION]->(ext:WorkCategory:Extension)-[:PARENT_CATEGORY]->(cat:WorkCategory:Canonical)` — add private leaf categories under a canonical parent
- Companies cannot create top-level categories

**Layer 3 — Per-project overlay** (optional, for bid submissions)

- `(Project)-[:USES_CODE_MAP]->(CodeMap)` — when a GC requires specific cost codes (e.g. a schedule of 01–05 codes), map canonical IDs to GC codes for this project only
- Does not alter categorisation — affects bid output formatting only
- **Schema-allowed only, not wired in this plan.** Follow-on work.

### 2.2 Jurisdictions and taxonomies

**Wave 1 (in scope for this plan):**

| Jurisdiction | Canonical taxonomy | Rationale |
|--------------|-------------------|-----------|
| US (`us`) | **MasterFormat 2020** (CSI) | De facto US commercial standard; dominant in architect specs and GC cost codes |
| Canada (`ca`) | **MasterFormat 2020** (CSC) | Co-owned by CSC; essentially identical tree to US |
| UK (`uk`) | **NRM 2** (RICS) | Current RICS standard for detailed measurement; CAWS is older and being phased out |
| Ireland (`ie`) | **NRM 2** (with IE deltas) | Inherits UK NRM practice; minor regional differences in units and terminology |
| Australia (`au`) | **NATSPEC Worksections** | National standard; close to MasterFormat in structure |
| New Zealand (`nz`) | **NATSPEC NZ** | Shares NATSPEC with AU with a small NZ-specific delta |

Ireland and New Zealand are near-free extensions of UK and AU respectively — same root taxonomy with small jurisdiction-specific overlays. Both get their own `jurisdiction_code` and full seed YAML, but the research effort is incremental on top of the parent jurisdiction.

**Wave 2 (out of scope for this plan, mechanical to add later when demand materialises):**

| Jurisdiction | Likely canonical | Effort signal |
|--------------|------------------|---------------|
| Germany (`de`) | DIN 276 + StLB | Genuinely distinct taxonomy; larger research effort |
| France (`fr`) | CCTG / CCTP patterns | Less standardised; taxonomy-light |
| Singapore (`sg`), Hong Kong (`hk`) | SMM7 (British-derived) | Could alias UK tree initially |
| UAE / Saudi Arabia (`ae`, `sa`) | POMI or MasterFormat-ish | Depends on regional firm practice |
| South Africa (`za`) | ASAQS Standard System | Distinct but small |
| Nordic countries (`se`, `no`, `dk`, `fi`) | AMA (SE), NS 3420 (NO), etc. | Each requires its own research |

Adding a Wave 2 jurisdiction requires both a WorkCategory seed and jurisdictional regulatory data. The schema supports them without modification; the limit is content-loading effort.

### 2.3 Taxonomy depth

All four taxonomies are 3–4 levels in practice. Model 4 levels (Level 4 optional), display 3 by default.

| Taxonomy | Levels | Example |
|----------|--------|---------|
| MasterFormat | 4 | `26 · 24 · 16 · .13` (Electrical → Service & Distribution → Panelboards → Lighting and Appliance) |
| NRM 2 | 3 | `Group 8 → Sub-group 8.2 → Item 8.2.1` |
| NATSPEC | 3 | `Group 2 → Worksection 0432 → Subheading` |

---

## 3. Schema Changes

Additions to [../../backend/graph/schema.cypher](../../backend/graph/schema.cypher):

```cypher
// -- WorkCategory additions --
CREATE INDEX index_work_category_jurisdiction IF NOT EXISTS
  FOR (n:WorkCategory) ON (n.jurisdiction_code);
CREATE INDEX index_work_category_code IF NOT EXISTS
  FOR (n:WorkCategory) ON (n.code);
CREATE INDEX index_work_category_level IF NOT EXISTS
  FOR (n:WorkCategory) ON (n.level);
```

### 3.1 WorkCategory properties

| Property | Required | Canonical | Extension |
|----------|----------|-----------|-----------|
| `id` | yes | `wcat_{hex}` | `wcat_{hex}` |
| `code` | canonical-only | official code (e.g. `26 24 16`) | — |
| `name` | yes | official title | contractor-chosen |
| `level` | yes | 1–4 | parent + 1 |
| `jurisdiction_code` | canonical-only | `us`, `ca`, `uk`, `ie`, `au`, `nz` | — |
| `source_reference` | canonical-only | e.g. `"MasterFormat 2020"` | — |

### 3.2 Relationships

New / used:

| Relationship | From | To | Notes |
|--------------|------|-----|-------|
| `HAS_WORK_CATEGORY` | Company | `WorkCategory:Extension` | Existing — scope narrowed to extensions only |
| `HAS_ALIAS` | Company | `WorkCategory:Canonical` | NEW — carries `display_name`, `added_at` |
| `HAS_EXTENSION` | Company | `WorkCategory:Extension` | NEW |
| `PARENT_CATEGORY` | WorkCategory | WorkCategory | Existing — Extension must point to Canonical parent |
| `CATEGORISED_AS` | WorkItem | WorkCategory | Existing in schema; wired for the first time in Phase 4 |
| `LINKS_TO_ACTIVITY` | `WorkCategory:Canonical` | Activity | Existing; loaded as part of Phase 5 |
| `PRODUCTIVITY_FOR_CATEGORY` | ProductivityRate | WorkCategory | Existing — now meaningfully populated |

### 3.3 Validation queries (CI-enforced)

Append to `backend/fixtures/golden/validation-tests.cypher`:

```cypher
// Every Canonical must have code, jurisdiction_code, and level
MATCH (c:WorkCategory:Canonical)
WHERE c.code IS NULL OR c.jurisdiction_code IS NULL OR c.level IS NULL
RETURN c.id AS violation, "Canonical missing required property" AS reason

// Every Extension must have a PARENT_CATEGORY pointing at a Canonical
MATCH (c:WorkCategory:Extension)
WHERE NOT (c)-[:PARENT_CATEGORY]->(:WorkCategory:Canonical)
RETURN c.id AS violation, "Extension must have Canonical parent" AS reason

// No two Canonicals share the same jurisdiction_code + code
MATCH (c1:WorkCategory:Canonical), (c2:WorkCategory:Canonical)
WHERE c1.id < c2.id AND c1.jurisdiction_code = c2.jurisdiction_code AND c1.code = c2.code
RETURN [c1.id, c2.id] AS violation, "Duplicate canonical code" AS reason

// No Company creates a top-level canonical (they should only extend)
MATCH (c:Company)-[:HAS_WORK_CATEGORY]->(cat:WorkCategory)
WHERE NOT cat:Extension
RETURN cat.id AS violation, "Company-owned category must be Extension" AS reason
```

---

## 4. Decisions (Resolved)

### 4.1 Licensing — Approach A, deferred purchase

Build as if licensing Approach A (use official titles, codes, and structure). **Actual licence purchase is deferred until US customer volume justifies the spend.** In the interim, implementation proceeds using the publicly-documented MasterFormat / NRM / NATSPEC structures as factual references. This is a commercial-procurement decision, not a technical one — the implementation work is identical under either path.

Budget line to watch: once MasterFormat licensing is triggered, CSI's commercial licence covers US + CA. NRM and NATSPEC licensing decisions follow market-by-market.

### 4.2 UI depth — Variable per jurisdiction, 3 levels default

Each YAML specifies its own depth. MasterFormat goes to Level 4; NRM 2 and NATSPEC stop at Level 3. The UI picker displays 3 levels by default and exposes Level 4 via an "expand" interaction where the tree supports it.

### 4.3 Residential handling — Search-first, no residential flag

Do NOT add `residential_applicable` flags. Full MasterFormat (and equivalents) for everyone, with a search-first picker. Jake types "panel upgrade" and the picker surfaces the match regardless of whether his trade touches 47 other MasterFormat divisions. Tree-browse remains available as fallback.

Revisit if residential UX proves problematic — at that point, the simplest fix would be a per-company "preferred divisions" shortlist rather than node-level flags.

### 4.4 Methodology — Design in parallel, build sequentially

Methodology (the "how the job is being built" layer — see the prior design conversation) depends on canonical categories for `APPLIES_TO_CATEGORY`, so it cannot ship first. But designing it now, alongside this plan, prevents canonical decisions that turn out to constrain methodology.

**Plan:**
- Methodology design doc (`docs/design/methodology.md`) is authored in parallel with Phase 1 of this plan.
- Canonical categories ship first (Phases 2–6 of this plan).
- Methodology build begins immediately after Phase 6, with design complete and no rework needed.
- Any schema changes needed for methodology get reviewed against this plan's schema during the methodology design pass.

### 4.5 Existing production data — Audit in Phase 0

Still to resolve in Phase 0. If production has existing `WorkCategory` or `HAS_WORK_CATEGORY` data, Phase 3 adds a migration step that re-labels existing company-owned categories as `:Extension` and points them at the nearest canonical parent.

---

## 5. Implementation Phases

### Phase 0 — Data audit (0.5 day)

**Goal:** Confirm the only remaining open decision (existing production data).

- Audit: how many `WorkCategory` and `HAS_WORK_CATEGORY` records exist in production? Any `CATEGORISED_AS`? Any company-specific category trees?
- If any data exists, draft the migration approach for Phase 3 (re-label existing company-owned categories as `:Extension`, point at nearest canonical parent).

All other decisions (licensing, depth, residential, methodology parallel design, jurisdictions) are resolved per §4.

**Deliverable:** short audit note + migration approach if needed.

**Gate before Phase 1:** audit complete.

### Phase 0b — Methodology companion design (parallel with Phase 1)

**Goal:** Methodology design lands alongside canonical research so both can integrate cleanly.

- Author `docs/design/methodology.md` covering: `Methodology` node shape, `approach` map structure, `APPLIES_TO_CATEGORY` relationship, hierarchy (`CHILD_OF` for Project → Package → Item cascade), temporal versioning, insight matching, UI for conversational authoring.
- Open design questions from the prior discussion to resolve: controlled vocab vs free keys in `approach`; contractor-scoped vs project-scoped methodology; how Insights match when methodology is partial; when methodology nodes are created vs inherited.
- Review against canonical categories schema to confirm no conflicts.

**Deliverable:** methodology design doc ready to drive build immediately after Phase 6 of this plan.

**Does not gate** Phases 1–6 of this plan.

### Phase 1 — Research and YAML authoring (1–2 weeks, parallelisable)

**Goal:** Produce complete seed data for all four jurisdictions.

Per jurisdiction, produce `backend/jurisdictions/{code}/work_categories.yaml` containing the full taxonomy tree to Level 3 (Level 4 where well-defined), with:

- Official codes and titles
- One-line scope description per category
- `activity_refs`: list of regulatory `Activity` IDs this category `LINKS_TO_ACTIVITY` (cross-reference against existing regulatory data under `backend/jurisdictions/{code}/`)

Example structure:

```yaml
jurisdiction: us
source: MasterFormat 2020
version: "2020-edition"
categories:
  - code: "26"
    name: "Electrical"
    level: 1
    children:
      - code: "26 05 00"
        name: "Common Work Results for Electrical"
        level: 2
        children:
          - code: "26 05 19"
            name: "Low-Voltage Electrical Power Conductors and Cables"
            level: 3
            activity_refs:
              - act_electrical_wiring
              - act_low_voltage_work
```

Parallelisable — one agent per jurisdiction. One agent reviews all six before merging, to catch structural inconsistencies.

Effort:

| Jurisdiction | Days | Notes |
|--------------|-----:|-------|
| US (MasterFormat) | 3–4 | 50 divisions, deep tree |
| CA (MasterFormat) | 0.5 | Clones US with small delta |
| UK (NRM 2) | 2–3 | |
| IE (NRM 2) | 1 | Clones UK with IE-specific delta |
| AU (NATSPEC) | 2–3 | |
| NZ (NATSPEC NZ) | 0.5 | Clones AU with small delta |

**Deliverable:** six YAML files passing structural validation, spot-checked by Paul against real taxonomy references.

**Gate before Phase 2:** YAMLs merged.

### Phase 2 — Schema and validation (1 day)

**Goal:** Schema supports canonical + extension + alias structure.

- Apply indexes per §3.1 to [../../backend/graph/schema.cypher](../../backend/graph/schema.cypher)
- Append validation queries per §3.3 to `backend/fixtures/golden/validation-tests.cypher`
- Run schema migration against test Neo4j

**Deliverable:** schema reflects the new model; validation passes against empty graph.

### Phase 3 — Loader and service updates (2–3 days)

**Goal:** Load canonical data; expose via API.

- Write `backend/scripts/load_canonical_work_categories.py` — reads each YAML, upserts Canonical nodes and `PARENT_CATEGORY` hierarchy, links to existing `Activity` nodes; idempotent, safe to re-run
- Update [../../backend/app/services/work_category_service.py](../../backend/app/services/work_category_service.py):
  - `list_canonical(jurisdiction_code, level=None, residential_only=False)` — NEW
  - `list_for_company(company_id)` — NEW, returns canonical + that company's aliases/extensions merged
  - `add_alias(company_id, canonical_id, display_name)` — NEW
  - `add_extension(company_id, parent_canonical_id, name)` — NEW, guarded so parent must be Canonical
  - `create()` — narrowed to only produce extensions; seed loader bypasses via a system flag
- Update [../../backend/app/routers/work_categories.py](../../backend/app/routers/work_categories.py) — expose the above
- Run loader against test, demo, and production graphs

**Deliverable:** every jurisdiction's canonical tree loaded; `list_for_company` returns the merged view.

### Phase 4 — Wire CATEGORISED_AS on WorkItem (2–3 days)

**Goal:** Every WorkItem gets categorised on creation.

- Update [../../backend/app/models/work_item.py](../../backend/app/models/work_item.py) `WorkItemCreate` to require `work_category_id`
- Update `work_item_service.create()` to write `(wi)-[:CATEGORISED_AS]->(cat)` atomically with WorkItem creation
- Update [../../backend/app/services/mcp_tools.py](../../backend/app/services/mcp_tools.py) `create_work_item` tool contract
- Frontend: add category picker to [../../frontend/src/components/projects/WorkTab.tsx](../../frontend/src/components/projects/WorkTab.tsx) and related forms — **search-first** with type-ahead over canonical names and codes; tree-browse as fallback for exploration
- Backfill: categorise all WorkItems in golden fixtures and demo data; no-op if production has no WorkItems

**Deliverable:** new WorkItems cannot be created without a category; existing fixtures have categories assigned; UI picker functional.

### Phase 5 — Regulatory bridge wiring (2–3 days)

**Goal:** Traversing from a WorkItem reaches the regulatory graph.

- For each jurisdiction, load `LINKS_TO_ACTIVITY` relationships from the YAML `activity_refs` fields
- Start with safety-regulated categories (fall protection, scaffolding, electrical work, excavation, hot work) — full coverage of other categories is out-of-scope for this phase
- Validate: traverse from a categorised WorkItem through `CATEGORISED_AS → LINKS_TO_ACTIVITY → REGULATED_BY` and confirm relevant regulations return

**Deliverable:** compliance queries from a WorkItem return applicable regulations and required certifications.

### Phase 6 — Verification (1–2 days)

**Goal:** Persona-based exploratory testing per Kerf [../../CLAUDE.md](../../CLAUDE.md).

Scenarios (use rich golden projects, no mocks):

- **Jake** creates "200A panel upgrade" WorkItem → types "panel upgrade" into search → picker surfaces MasterFormat `26 24 16` Panelboards as top match → selects it → regulatory bridge returns applicable NEC sections and required electrician certifications
- **Sarah**'s `ProductivityRate` for EMT in drop ceilings attaches to canonical `26 05 33` Raceways → queryable across all her projects in that category → cross-tenant anonymised aggregation returns a benchmark from `IndustryProductivityBaseline`
- **UK contractor** creating a "suspended ceiling" WorkItem → picker shows NRM 2 tree; search surfaces the NRM 2 match, not MasterFormat → jurisdiction scoping verified
- **Irish contractor** sees NRM 2 tree (IE variant) with any IE-specific deltas applied
- **NZ contractor** sees NATSPEC NZ; **AU contractor** sees NATSPEC AU — shared root, jurisdiction-specific leaves
- Contractor creates an alias (`Panelboards` → `Main Panels`) → it displays throughout the UI; canonical node unchanged
- Contractor extends (`Receptacles > Hospital-Grade`) → extension node appears only for that contractor; `PARENT_CATEGORY` chain intact

**Deliverable:** verification notes + screenshots. Ready for Paul to review against Jake/Sarah/Marco personas.

---

## 6. Total Effort

| Phase | Days | Can parallelise? |
|---|---:|:---:|
| 0 — Data audit | 0.5 | — |
| 0b — Methodology design (parallel) | 3–5 elapsed | Runs alongside Phase 1 |
| 1 — Research (6 jurisdictions) | 5–10 elapsed | Yes, 6 agents |
| 2 — Schema | 1 | No |
| 3 — Loader & service | 2–3 | No |
| 4 — Wire `CATEGORISED_AS` | 2–3 | No |
| 5 — Regulatory bridge | 2–3 | Partial |
| 6 — Verification | 1–2 | No |
| **Total (canonical)** | **14–23 days** | 2–3 weeks calendar with parallel research |

Methodology design adds no elapsed time (runs in parallel). Methodology build is a separate follow-on effort beginning immediately after Phase 6.

---

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| Licensing triggers before revenue justifies it | Deferred-purchase approach; use publicly-documented structure in the interim; re-evaluate when first US customer signs |
| MasterFormat too deep for Jake's residential flow | Search-first picker; tree-browse as fallback. Revisit with per-company "preferred divisions" shortlist if needed |
| CSI/RICS/NATSPEC update their taxonomies | Version the seed YAMLs (`version` field); maintenance task |
| Production data forces migration | Audit in Phase 0; add migration to Phase 3 if needed |
| Research inconsistent across six jurisdictions | Shared YAML schema + structural validation; one reviewer across all six |
| Many categories have no regulatory `Activity` to link | Accept partial coverage; extend as regulatory data grows |
| Contractor rejects "another taxonomy" | Heavy investment in aliasing UX; search-first picker; don't show codes unless asked |
| Methodology design surfaces canonical schema changes | Methodology design doc reviews canonical schema before Phase 2; any changes fold back into this plan |

---

## 8. Out of Scope (Deliberate)

- **Methodology build** — design runs in parallel (Phase 0b), build starts after Phase 6 of this plan
- **Wave 2 jurisdictions** (DE, FR, Nordics, GCC, SG/HK, SA, etc.) — schema-ready, added when demand justifies
- Per-project GC code maps (`USES_CODE_MAP`) — schema allowed, not wired in this plan
- OmniClass tables beyond work results
- UniFormat (elemental) support — may be added later for early-stage conceptual estimates
- Full regulatory coverage — Phase 5 targets safety-regulated categories only; broader coverage follows as regulatory data grows
- Multi-jurisdiction projects — a Project has one `jurisdiction_code`; cross-border projects are out-of-scope for v1
- Per-node residential flags — search-first UI makes them unnecessary; revisit only if UX research shows residential contractors struggle

---

## 9. Success Criteria (Phase 6 Outcomes)

The plan is complete when:

1. Every new WorkItem created through the API or MCP tool has a `CATEGORISED_AS` relationship, enforced at the service layer.
2. A contractor in any of the six Wave 1 jurisdictions (US, CA, UK, IE, AU, NZ) sees their jurisdiction's canonical tree when picking a category.
3. Search-first picker: typing a natural description ("panel upgrade", "suspended ceiling") surfaces the correct canonical node within the top 3 matches.
4. `search_historical_rates` and `ProductivityRate` lookup now meaningfully filter by category across projects.
5. A traversal from a categorised WorkItem through the regulatory bridge returns applicable regulations and required certifications for the safety-regulated categories.
6. A contractor can alias a canonical category or add a private leaf extension via the API; the UI displays aliases; validation queries prevent top-level custom categories.
7. All six jurisdictions' YAML seeds pass structural validation; the loader is idempotent.
8. Data audit from Phase 0 is complete, and any production migration has run successfully.
9. Methodology design doc (`docs/design/methodology.md`) is complete and ready to drive the next build phase.
