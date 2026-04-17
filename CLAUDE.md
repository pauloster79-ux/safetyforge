# Kerf — Project Development Guide

## Product North Star

Before building anything, read and internalise:
- `docs/PRODUCT_VISION.md` — what Kerf is, who it's for, how it works
- `docs/PRODUCT_STRATEGY.md` — market, positioning, pricing, competitive landscape
- `docs/architecture/DECISIONS.md` — every non-obvious technical decision we've made

These are not reference documents. They are the ground truth. Every feature, every UI choice, every technical decision should be traceable back to the product vision. If something you're about to build contradicts the vision, stop and raise it.

## The Three Personas

Every feature is built for real people. Know them:

- **Marco Gutierrez** — Concrete crew of 22, Phoenix. Bilingual (Spanish/English). Runs 3 active projects. Needs one tool instead of six. Morning starts at 5:30 AM. Everything happens on his phone, on the jobsite.
- **Sarah Chen** — Owns 45-person electrical firm, Atlanta. Juggles estimating, job costing, crew management, sub compliance. Used to spend Sundays reconciling. Needs financial intelligence derived from daily operations.
- **Jake Torres** — Solo electrician, recently independent. Estimates in his head, tracks hours on paper. Needs to look professional, bid with confidence, and build a safety program with zero effort.

When testing a feature, you are one of these people. Not a developer running assertions.

---

## Development Process

### How Features Get Built

```
Paul describes what he wants
    |
    v
Clarify evaluation criteria if unclear
    |
    v
Paul confirms what "done" looks like
    |
    v
Build it — full stack (backend + frontend + wired together)
    |
    v
Verify against criteria (run it, screenshot it, test it as a persona)
    |
    v
Paul confirms or adjusts
    |
    v
Record any architectural decisions made
```

### Evaluation Criteria Types

Paul defines these per feature. They vary in specificity:

| Type | When | Example |
|------|------|---------|
| **Behavioural** | Always | "A user can create an inspection and it persists" |
| **UI-specific** | When the interface matters | "The form has these exact fields, this layout, this validation" |
| **UI-flexible** | When existing patterns apply | "Build the list page, follow the inspection list pattern" |
| **Technical** | When implementation matters | "Compliance checks must traverse the graph, not use LLM inference" |

If Paul hasn't specified criteria clearly enough, ask before building. Don't guess at what "done" means.

---

## Hard Rules

### 1. No Mocks

Never use `Mock()`, `MagicMock()`, `@patch`, `unittest.mock`, `page.route()`, `page.intercept()`, `route.fulfill()`, MSW, or any form of mocking for internal services, APIs, or database interactions.

**What this means in practice:**
- Backend tests hit real Neo4j (or the test instance)
- API tests call real endpoints
- Frontend integration tests hit the real backend API
- If a dependency isn't ready, the test fails honestly — it does not pass with fabricated responses

**The only exception:** Genuinely external services (Anthropic API, Clerk auth) where running the real thing in tests is impractical. Even then, prefer a thin live wrapper over a mock where possible.

### 2. Full-Stack Completion

A feature is not done until a user can do the thing in the browser.

**Not done:**
- "The endpoint exists" (but no frontend)
- "The component renders" (but isn't wired to the API)
- "The service method works" (but isn't exposed as an endpoint)

**Done:**
- A user can perform the action end-to-end in the browser
- You've used it yourself and shown it working with a screenshot

If the frontend for a feature genuinely isn't ready (e.g., building backend-only infrastructure), say that upfront. Don't claim the feature is complete.

### 3. Persona-Based Exploratory Testing

When testing a feature, don't run minimal developer assertions. Instead:

1. **Pick a persona** — Marco, Sarah, or Jake (whichever fits the feature)
2. **Use a golden project** — real data, real complexity, not placeholder strings
3. **Act like the user** — what would they actually type? What would they expect to see? What would confuse them?
4. **Test the messy cases** — misspellings, partial inputs, switching between projects, using the feature twice in a row, the thing a real contractor would do at 5:30 AM on their phone

Report what the experience was like, not just whether it "worked."

### 4. Rich Golden Projects

The golden projects in `backend/fixtures/golden/` must have realistic data density:

- Multiple workers with varying certification states (valid, expiring soon, expired)
- Multiple inspections at different stages (draft, submitted, approved, failed)
- Realistic daily logs with actual construction narrative (not "did some work")
- Hazard reports, incidents, corrective actions in various states
- Toolbox talks covering different topics
- Sub-contractors with insurance and compliance data where applicable
- Data that exercises edge cases naturally (expired certs, failed inspections, open corrective actions)

When a golden project feels light, expand it before testing against it.

### 5. Record Architectural Decisions

When you make a non-obvious technical choice during development, record it in `docs/architecture/DECISIONS.md`. This includes:
- Technology choices (why Neo4j over Postgres for X)
- Pattern choices (why service-per-entity vs. orchestrator)
- Data model decisions (why this relationship direction)
- Integration choices (how frontend talks to backend for X)

The format is simple. The goal is that next session, this decision is known.

---

## Architecture Reference

Read these before making changes to the relevant area:

| Area | Document |
|------|----------|
| Backend structure | `docs/architecture/BACKEND_ARCHITECTURE.md` |
| Frontend structure | `docs/architecture/FRONTEND_ARCHITECTURE.md` |
| Knowledge graph / ontology | `docs/architecture/CONSTRUCTION_ONTOLOGY.md` |
| Agent architecture | `docs/architecture/AGENTIC_ARCHITECTURE.md` |
| Infrastructure / deployment | `docs/architecture/INFRASTRUCTURE.md` |
| Multi-jurisdiction | `docs/architecture/JURISDICTION_ABSTRACTION.md` |
| Decisions registry | `docs/architecture/DECISIONS.md` |

---

## Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, React Router, TanStack Query
- **Backend:** Python 3.12, FastAPI, Pydantic
- **AI:** Anthropic Claude API
- **Database:** Neo4j (knowledge graph + vector index)
- **Auth:** Clerk
- **PDF:** WeasyPrint
- **Hosting:** Cloud Run (backend), Vercel (frontend)

---

## What This Process Does NOT Include

The following are explicitly removed from the old process:
- Formal spec documents (Tier 1/2/3)
- Adversarial review sessions in separate Claude sessions
- Multi-phase gates (Red/Green/Quality/Verify)
- Mandatory test categories (HAPPY, ERROR, EDGE, etc.)
- Hook-enforced quality gates
- Spec write-back rules
- Design system hook enforcement

Tests are still written. Quality still matters. But the process is: Paul defines success criteria, I build to them, I verify they're met, I record decisions. That's it.
