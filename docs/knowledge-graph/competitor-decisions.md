# Competitor Gap Decisions

Summary of how each competitor-identified gap was resolved.

| # | Gap | Competitor approach | Our decision | Rationale |
|---|-----|-------------------|--------------|-----------|
| R1 | Upstream/downstream contracts | Separate PrimeContract + Commitment entities | **Single Contract entity, direction implied by relationships** | Same structure both directions. Client contract links to Project, sub contract links to WorkItems. Split later if divergence demands it |
| R2 | Schedule of Values | Separate SOV entity as billing bridge | **WorkPackage IS the billing unit** | No realistic divergence between billing structure and work structure for our market |
| R3 | Selections & Allowances | Dedicated Selection/Allowance entities | **Handled by existing WorkItem + USES_ITEM + Variation** | Budget on USES_ITEM, choice is the specific Item linked, overage becomes a Variation. Workflow details later |
| R4 | Recurring inspection schedules | InspectionSchedule entity | **Frequency on REQUIRES_INSPECTION relationship + project-level INSPECTION_FREQUENCY override** | Regulatory graph already knows what's required. Agent monitors. Contractor can set higher frequency than regulatory minimum |
| R5 | Item pricing library | Company-scoped catalog with saved prices | **No pricing on Item. Agent surfaces historical pricing from USES_ITEM data** | More accurate than stale defaults. Future: live local pricing via agents |
| R6 | Change Event | Separate entity preceding Variation | **No Change Event entity.** Trigger captured in Variation evidence chain + conversation memory | Single Variation with evidence is sufficient for our market |
| R7 | Drawing/Plan management | Versioned drawings with spatial pinning | **No Drawing entity now.** Document with type "drawing" for storage. Future: DrawingSet/Sheet/SpatialPin entities when feature built | WorkItem → AT_LOCATION → Location provides the foundation for future spatial linking |
| R8 | Daily log sub-types | 12+ typed sections (Procore) | **No additional sub-types.** Daily log is an assembled view of the day's graph data, not a form with sections | Agent extracts structured data from narration. No hardcoded sub-types |
| R9 | Conditional inspection logic | Template rules with if/then conditions | **No template logic entity.** Agent traverses the regulatory graph dynamically based on answers and context | Better than static rules — the graph IS the conditional logic |
| R10 | Custom task statuses | Up to 20 configurable statuses per project | **State (lifecycle) + status (condition).** Fixed state progression, free-text status for current condition | Clean lifecycle, flexible condition capture without custom status management |
| R11 | Project financial structure | Project-level fixed_price/cost_plus setting | **Added `pricing_model` property on Project** | Affects client visibility. Agent/UI uses it to determine what to show |
| R12 | Payment/bill schedules | Dedicated schedule entities | **Milestones + Contract.payment_schedule + agent intelligence** | Agent knows billing milestones and prompts at the right time. No separate entity |

## Key Insight

In every case, our graph architecture handles the underlying need without adding entities. Competitors built separate entities because relational databases require explicit join tables to connect concepts. Our graph handles these through relationships and traversals. The agent's ability to traverse the graph dynamically replaces static template logic, version tracking nodes, and separate billing structures.

## What's Validated

- Two-layer model (Project → WorkItem) — universal pattern
- Bottom-up costing — universal pattern
- No separate Estimate entity — confirmed by competitor approaches
- Global-first naming — genuine differentiator
- Regulatory knowledge graph — completely unique
- Conversation memory — completely unique
- Graph-native permissions — no competitor uses this
