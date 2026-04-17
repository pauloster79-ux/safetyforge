# Session Prompt: Backend Implementation — Quoting Entities

## Context

The Kerf construction ontology has been expanded with two new domains:
- **Domain 16: Work Structure** — WorkItem, Labour, Item, WorkPackage, WorkCategory
- **Domain 17: Quoting** — Assumption, Exclusion, ResourceRate, ProductivityRate

The ontology, schema, and design decisions are documented. This session implements the backend: Pydantic models, Neo4j services, and API endpoints.

## Before You Start

Read these files in order:

1. `docs/workflow/handoff-quoting-ontology.md` — what was decided and why
2. `docs/architecture/CONSTRUCTION_ONTOLOGY.md` — Domain 16 and Domain 17 sections (search for "Domain 16: Work Structure" and "Domain 17: Quoting")
3. `backend/graph/schema.cypher` — the constraints and indexes already added
4. `backend/app/services/base_service.py` — the base class pattern (ID generation, provenance, transactions)
5. `backend/app/services/work_item_service.py` — the existing WorkItem service that needs refactoring
6. `backend/app/services/estimating_service.py` — the existing estimating service that needs extending
7. `backend/app/models/actor.py` — the Actor model used for provenance

## What to Build

### Phase 1: New Pydantic Models

Create models following the existing pattern in `backend/app/models/` (Create/Update/Full pattern):

1. `backend/app/models/labour.py` — LabourCreate, LabourUpdate, Labour
2. `backend/app/models/item.py` — ItemCreate, ItemUpdate, Item (check if this conflicts with existing Item model)
3. `backend/app/models/assumption.py` — AssumptionCreate, AssumptionUpdate, Assumption
4. `backend/app/models/exclusion.py` — ExclusionCreate, ExclusionUpdate, Exclusion
5. `backend/app/models/resource_rate.py` — ResourceRateCreate, ResourceRateUpdate, ResourceRate
6. `backend/app/models/productivity_rate.py` — ProductivityRateCreate, ProductivityRateUpdate, ProductivityRate

Also update:
- `backend/app/models/work_item.py` — add quantity, unit, is_alternate, alternate_label fields
- `backend/app/models/project.py` — add state field, change status meaning, add estimate_confidence, target_margin_percent, contract_type, quote_valid_until, quote_submitted_at

### Phase 2: New Services

Create services extending BaseService:

1. `backend/app/services/labour_service.py` — CRUD for Labour nodes under WorkItems
2. `backend/app/services/assumption_service.py` — CRUD + template copy + trigger checking
3. `backend/app/services/exclusion_service.py` — CRUD + template copy
4. `backend/app/services/resource_rate_service.py` — CRUD + derive from actuals
5. `backend/app/services/productivity_rate_service.py` — CRUD + derive from actuals

### Phase 3: Refactor Existing Services

1. **work_item_service.py** — WorkItem creation now creates Labour and Item child nodes instead of storing flat properties. The `labour_hours`, `labour_rate`, `materials_allowance` properties are replaced by traversal to Labour and Item children.
2. **estimating_service.py** — `search_historical_rates()` now queries ResourceRate and ProductivityRate nodes instead of aggregating WorkItem properties.
3. **job_costing_service.py** — Cost rollup traverses `(WorkItem)-[:HAS_LABOUR]->(Labour)` and `(WorkItem)-[:HAS_ITEM]->(Item)` instead of reading flat properties.
4. **proposal_service.py** — Include Assumptions and Exclusions from graph when generating proposals.

### Phase 4: API Endpoints

Add routes in `backend/app/routers/` following existing patterns:

- Labour: nested under work items (`/me/projects/{pid}/work-items/{wid}/labour`)
- Items: nested under work items (`/me/projects/{pid}/work-items/{wid}/items`)
- Assumptions: nested under projects (`/me/projects/{pid}/assumptions`) + company templates (`/me/assumption-templates`)
- Exclusions: nested under projects (`/me/projects/{pid}/exclusions`) + company templates (`/me/exclusion-templates`)
- ResourceRates: company level (`/me/rates`)
- ProductivityRates: company level (`/me/productivity-rates`)

## Key Constraints

- All monetary values as integers in cents
- All IDs as `{prefix}_{token_hex(8)}`
- Actor provenance on all creates and updates
- No foreign key properties — all references via Neo4j relationships
- Follow existing service patterns exactly (read `daily_log_service.py` as the gold standard)
- Company scope on all queries: `(Company {id: $company_id})-[:OWNS_PROJECT]->(Project)`

## What NOT to Do

- Do NOT create Quote, Estimate, or CostLine entities — WorkItem moves through states
- Do NOT store Labour/Item data as JSON properties — they are graph nodes
- Do NOT change existing WorkItem state enum values — only add `superseded`
- Do NOT modify the ontology or schema files — they are already correct
- Do NOT build frontend — that's a separate session
