# Domain Scope

## Domain

Construction business operations — the complete lifecycle of a contractor running projects, from finding work through getting paid and learning from the outcome. Covers all contractor sizes (solo tradesperson to 100+ person firms) across all construction trades. The data structures are scale-invariant; complexity and concurrency increase with firm size.

The universal contractor lifecycle:

| Stage | What happens |
|---|---|
| 1. Find & qualify | Lead comes in, decide if it's worth pursuing |
| 2. Estimate & price | Figure out cost and markup |
| 3. Propose & win | Send quote, negotiate, get agreement |
| 4. Plan & mobilise | Schedule, assign crew, order materials |
| 5. Execute & document | Do the work, record what happens daily |
| 6. Manage money | Track costs, process change orders, invoice |
| 7. Close out | Punch list, final inspection, warranty |
| 8. Get paid | Collect money |
| 9. Learn | Did we make money? What went wrong? |

Cross-cutting across all stages: Safety, Quality, Compliance, Communication, Documents.

## Boundaries

**In scope:**
- All 9 lifecycle stages above
- Cross-cutting concerns: safety, quality, compliance, communication, documents
- Conversation memory (every interaction, verbatim + semantic via vector embeddings)
- Document intelligence (uploaded files chunked, embedded, entity-linked)
- Agentic infrastructure (agent identity, provenance, cost tracking, permissions)
- Multi-jurisdiction regulatory knowledge (rules as traversable graph structure)
- Multi-tenancy with graph-native isolation
- Basic invoicing (generate and send from the platform)

**Out of scope:**
- UI/frontend architecture
- Deployment/infrastructure
- Auth system internals
- Full accounting (sync to QuickBooks/Xero, don't replace)
- BIM/3D modelling
- Full procurement/supply chain management

## Consumers

- [x] AI Agents (MCP tools) — compliance checking, briefing generation, cost analysis, conversation context retrieval, change order detection, estimating intelligence
- [x] Human UI — dashboards, forms, reports, conversational interface
- [x] REST/GraphQL API — serving the frontend and external integrations
- [x] Analytics — reporting, benchmarking, trend analysis

## Target Database

Neo4j (Cypher) with native vector indexes for hybrid graph+vector retrieval (Neo4j 5.11+)

## Existing Data Sources

- **Current graph schema**: 52 node types across 9 domains (safety, organisational, HR, equipment, daily ops, documents, spatial, sub management, agentic). Defined in `backend/graph/schema.cypher`
- **Jurisdiction YAML files**: 50 US states + AU/CA/UK regulatory data
- **No live customer data yet** — greenfield for data model changes

## Scale

- Thousands of tenant companies (target: 5,000 within 3 years)
- Each company: tens to hundreds of projects over time
- Millions of nodes within 2-3 years (conversations, document chunks, time entries accumulate fast)
- Vector indexes on Message and DocumentChunk nodes (embeddings up to 4096 dimensions)

## Relevant Public Ontologies

- **schema.org**: Basic organisational entities (Organization, Person, Place) — reusable for contact/company modelling
- **OSHA/regulatory standards**: Already encoded in jurisdiction YAML files as domain-specific structure
- **IFC (Industry Foundation Classes)**: BIM standard — out of scope but worth noting for future interop
- **No existing construction business operations ontology covers this full scope** — most construction ontologies focus on BIM or asset management, not the contractor's operational lifecycle

## Agentic Overlay

**ACTIVE** — AI agents will read and write the KG. Agentic patterns (provenance, permissions, temporal facts, cost tracking) will be surfaced at each design phase.
