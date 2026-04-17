# Handoff: Quoting Ontology Expansion Complete — Ready for Backend Implementation

**Date:** 2026-04-14
**Session:** YouTube estimating analysis → ontology design → implementation
**Next step:** Backend models + services for Domain 16 (Work Structure) and Domain 17 (Quoting)

---

## What Was Done This Session

### 1. Estimating Domain Research
- Analysed a comprehensive YouTube construction estimating course (Tim / Operum)
- Researched competitors: Handoff, JobTread, Buildertrend, ProEst, Buildxact, STACK
- **Key finding:** No small-contractor tool does structured assumptions/exclusions, learns from historical job data, or connects quote terms to variation detection. This is open whitespace.
- Full analysis in `docs/ESTIMATING_EXPERIENCE.md` with two complete scenarios (Jake solo electrician, Sarah 45-person commercial sub) including full quote/proposal output documents

### 2. Ontology Expansion — Two New Domains
Added to `docs/architecture/CONSTRUCTION_ONTOLOGY.md`:

**Domain 16: Work Structure** — formalises entities that existed in code but not in the ontology:
- **WorkItem** (`wi_`) — atomic unit of deliverable work, flows through lifecycle states
- **Labour** (`lab_`) — discrete labour task within a WorkItem (work done by people)
- **Item** (`item_`) — discrete item used by a WorkItem (materials, equipment, fixtures, rentals)
- **WorkPackage** (`wp_`) — optional grouping of WorkItems into divisions
- **WorkCategory** (`wcat_`) — hierarchical taxonomy for classifying work types
- 19 relationships

**Domain 17: Quoting** — commercial intelligence layer:
- **Assumption** (`asmp_`) — structured qualification with variation trigger monitoring
- **Exclusion** (`excl_`) — structured scope boundary, reusable via company templates
- **ResourceRate** (`rr_`) — company rate knowledge (labour/material/equipment), manual or derived from actuals
- **ProductivityRate** (`pr_`) — company productivity knowledge, condition-specific
- 14 relationships

### 3. Extended Project Entity
- **`state`** (NEW field): lead | quoted | active | completed | closed | lost — the lifecycle stage
- **`status`** (CHANGED meaning): normal | on_hold | delayed | suspended — operating condition within a state
- **New properties:** estimate_confidence, target_margin_percent, contract_type, quote_valid_until, quote_submitted_at

### 4. Schema Updated
`backend/graph/schema.cypher` — constraints and indexes added for all new entities.

### 5. HTML Visualisation Updated
`docs/architecture/construction-ontology.html` — v2.4 with new domains, all changes marked with green NEW tags.

### 6. Spec Written
`specs/SPEC-001-quoting.md` — Tier 1 complete (product requirements, business rules, validation rules, Gherkin scenarios, user journeys). Tiers 2-3 are skeleton for Stage 2.

### 7. Remotion Prototype
`quoting-prototype/` — animated walkthrough of the Jake quoting flow in Kerf's actual design system. Run with `cd quoting-prototype && npm start`.

### 8. UI Restructure Spec
`docs/specs/UI_RESTRUCTURE_SPEC.md` — approved spec for restructuring the icon rail and project detail tabs. References the Project state/status model. The Contract tab adapts based on project state (lead=quoting, active=tracking, completed=invoicing).

---

## Key Design Decisions

### Entities move through states, not into new entities
- "Quote" is NOT a separate entity — it's a Project in `state: quoted` with WorkItems + Assumptions + Exclusions attached
- "Proposal document" is NOT a separate entity — it's a Document of type "proposal"
- "Estimate line" is NOT separate from "task" or "cost line" — it's a WorkItem in different states (draft → scheduled → complete)
- Alternates are WorkItems with `ALTERNATE_TO` relationship, not separate entities

### Everything is a graph node — no JSON blobs
- Labour tasks are **Labour nodes** with `(WorkItem)-[:HAS_LABOUR]->(Labour)` — not a JSON array on WorkItem
- Items are **Item nodes** with `(WorkItem)-[:HAS_ITEM]->(Item)` — not a materials_allowance integer
- This enables: cross-project querying, PurchaseOrder linking, rate derivation from actuals, productivity tracking per labour task

### Project has state + status (two fields)
- **state** = lifecycle stage: lead | quoted | active | completed | closed | lost
- **status** = operating condition: normal | on_hold | delayed | suspended
- A project can be `state: active, status: on_hold` (active project temporarily paused)
- This aligns with the UI restructure spec's Contract tab which adapts by state

### WorkItem.quantity is scope quantity
- The number shown to the client: "2 EA floor boxes", "15 LF cable"
- Standard industry pattern: quantity × unit (EA, LF, SF, CY, LS, etc.)
- Different from Item.quantity which is procurement count

### Assumptions and Exclusions are reusable via templates
- Company-level templates (`is_template: true`) owned by Company node
- Copied to projects via `ASSUMPTION_FROM_TEMPLATE` / `EXCLUSION_FROM_TEMPLATE` relationships
- Templates accumulate from lessons learned — the system never forgets a scope gap

### ResourceRates and ProductivityRates derive from actuals
- `source: derived_from_actuals` with `sample_size` and `std_deviation`
- The learning loop: completed job → compare estimated vs actual → update rates
- Rates improve with every completed job

---

## What Exists in Code Already

These services exist and need updating to match the expanded ontology:

| Service | Current State | Needed Change |
|---|---|---|
| `work_item_service.py` | Uses flat properties (labour_hours, labour_rate, materials_allowance) | Refactor to use Labour and Item child nodes |
| `work_package_service.py` | Basic CRUD | Minimal changes — mostly correct |
| `work_category_service.py` | Basic CRUD | Minimal changes — mostly correct |
| `estimating_service.py` | Historical rate search, estimate summary | Extend to use ResourceRate and ProductivityRate nodes |
| `job_costing_service.py` | Aggregates WorkItem properties | Refactor to traverse Labour and Item nodes |
| `proposal_service.py` | Generates proposal document | Extend to include Assumptions and Exclusions from graph |
| `variation_service.py` | Simplified Variation nodes | Connect to Assumption trigger system |
| `project_assignment_service.py` | Uses `status` field | Update to use `state` + `status` fields |

New services needed:
- `assumption_service.py` — CRUD + template management + trigger checking
- `exclusion_service.py` — CRUD + template management
- `resource_rate_service.py` — CRUD + derivation from actuals
- `productivity_rate_service.py` — CRUD + derivation from actuals
- `labour_service.py` — CRUD for Labour nodes under WorkItems
- `item_service.py` — may need refactoring (Item already exists in schema but as a "global shared catalogue" — now it's per-WorkItem)

---

## Files Modified This Session

| File | Change |
|---|---|
| `docs/architecture/CONSTRUCTION_ONTOLOGY.md` | Added Domain 16 + 17, extended Project entity |
| `docs/architecture/construction-ontology.html` | Updated to v2.4 with new domains |
| `backend/graph/schema.cypher` | Added constraints/indexes for 6 new entities + Project.state |
| `docs/ESTIMATING_EXPERIENCE.md` | Full scenario document with Jake + Sarah examples |
| `docs/preview/ontology-expansion.html` | Focused preview of ontology changes |
| `docs/preview/estimating-experience.html` | HTML version of estimating experience doc |
| `specs/SPEC-001-quoting.md` | Tier 1 spec for quoting feature |
| `quoting-prototype/` | Remotion animated prototype of quoting flow |

---

## What NOT to Do

- Do NOT create separate Quote, Estimate, or CostLine entities — WorkItem moves through states
- Do NOT store Labour or Item breakdowns as JSON on WorkItem — they are graph nodes
- Do NOT use `status` for Project lifecycle — use `state` for lifecycle, `status` for operating condition
- Do NOT add foreign key properties — all references are relationships (Design Principle #8)
- Do NOT change existing WorkItem state values — add `superseded` but keep all others
