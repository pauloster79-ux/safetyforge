# Build Sequence Session Prompt

Copy the below into a new Claude Code session to work out the build sequence from current state to go-live.

---

## Prompt

I need to work out the build sequence for Kerf — from where we are now to a go-live product. This is a critical planning session. Don't jump to producing a plan — discuss the approach with me first.

### Context

Read these documents to understand the current state:

1. `docs/PRODUCT_VISION.md` — the full product vision. Section 3 ("What Kerf Does") describes the 9 contractor processes + 3 cross-cutting concerns the platform supports. Section 4 describes the three-layer intelligence architecture (knowledge graph + vector + object storage).

2. `docs/PRODUCT_STRATEGY.md` — competitive positioning. Sections 3.3-3.5 cover the AI construction startup landscape (Handoff $25M, Hardline $2M, Brickanta $8M, Rebar $14M — all US-locked) and our 10 unfair advantages.

3. `docs/BUILD_PLAN_EXPANSION.md` — the existing build plan (v2.0). Phases 1-6 are fully specified (daily logs, quality, time tracking, sub management, RFIs, scheduling). Phases 7-9 (estimating, document intelligence, change orders) are referenced but TBD. NOTE: this plan was written before the product vision was rewritten to describe the full platform — the sequencing may need rethinking.

4. `docs/knowledge-graph/03-entities-relationships.md` — the revised KG ontology with ~73 entities including WorkItem (the atomic unit of deliverable work), WorkPackage (optional grouping), Estimate, Contract, Variation, TimeEntry, Conversation, Message, DocumentChunk, and the full regulatory domain. This ontology is being finalised in a separate session.

5. `backend/app/services/` — the existing codebase. The audit found that ALL existing infrastructure is functional (not skeleton): 8 MCP tools with real Neo4j queries, streaming chat with Claude tool-use loop, event bus, guardrails, briefing agent, compliance agent, voice service, cost tracking. The chat service includes a `query_graph` tool that lets Claude write arbitrary Cypher against Neo4j.

6. `docs/preview/ui-mockups.html` and `docs/preview/work-items.html` — UI mockups showing the conversational-first approach (chat home screen, cards from tool results, desktop split view with canvas, WhatsApp worker communication).

### What we need to figure out

1. **What is the right build sequence?** The existing plan (Phases 1-6) was written for a phased rollout over months. We now want to build the complete platform in approximately one month. The KG ontology redesign changes the schema, which means existing services need updating. New capabilities (estimating, job costing, invoicing, conversation recording, document intelligence) need building. The conversational interface needs to be the primary interaction model, not a sidebar.

2. **What goes first — schema or features?** The KG ontology is being redesigned (separate session). Should we wait for it to be finalised, or start building features against the current schema and migrate? The risk of building on the old schema is rework. The risk of waiting is lost time.

3. **What's the minimum for go-live?** The vision describes 9 processes + 3 cross-cutting. Not all need to be equally deep on day one. What's the minimum viable product that a contractor would pay for? What can be shallow vs what must be solid?

4. **How do we handle the existing code?** 21 backend services reference the current schema. Some entity names are changing (CostCode → WorkCategory, ChangeOrder → Variation, etc.). The existing 8 MCP tools work but are safety-focused. How much rework vs extension?

5. **Conversation recording and document intelligence — when?** These are cross-cutting infrastructure. The vision says every interaction should be recorded from day one. But building the full pipeline (embedding, vector indexes, entity extraction) is significant work. When does it need to exist?

6. **The UI question.** The mockups show a conversational-first approach — chat is the home screen, cards render from tool results, canvas workspace on desktop. But the current frontend is a traditional dashboard with forms. How much of the existing frontend survives? Do we rebuild the UI architecture or adapt it?

7. **Voice.** The research concluded: voice-as-text-input (Deepgram STT → text in chat) is the fast path. Real-time voice conversation (LiveKit) is 2-3 days of integration once chat works. When does each get built?

8. **Testing.** A separate session is designing a testing strategy with golden project seed data. How does this integrate with the build sequence?

### What I DON'T want

- A detailed task-by-task plan before we've agreed the approach
- Assumptions about phased rollout over months — this is a compressed build
- Features deferred to "Phase 2 someday" — everything in the vision gets built, the question is the ORDER and DEPTH

### What I DO want

- An honest discussion about dependencies, risks, and sequencing trade-offs
- Your assessment of what's genuinely hard vs what's straightforward given the existing codebase
- A clear recommendation on build order with reasoning
- Identification of any architectural decisions that need to be made before coding starts
