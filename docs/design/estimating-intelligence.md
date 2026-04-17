# Estimating Intelligence — Design Document

**Status**: Draft for review
**Author**: Claude + Paul
**Date**: 2026-04-16
**Scope**: The intelligence layer that powers Kerf's conversational estimating — how every number gets onto an estimate line, where it comes from, how the system learns, and how we ensure the vision actually delivers.
**Depends on**: [Phase 0 — Platform Foundations](phase-0-foundations.md) (audit events, provenance display)
**Related**: [Product Vision §3.2, §3.13, §7](../PRODUCT_VISION.md) | [Estimating Experience scenarios](../ESTIMATING_EXPERIENCE.md) | [Ontology Domains 16-17](../architecture/CONSTRUCTION_ONTOLOGY.md)

---

## 1. The Problem

Today, when a contractor asks Kerf to draft an estimate, the agent calls `create_work_item`, `create_labour`, and `create_item` with values it supplies directly. Those tools accept any positive number — no validation, no lookup, no source required.

Where do the numbers come from?

- **If the contractor has completed similar jobs**: the agent may call `search_historical_rates` (keyword match over past WorkItems) and use what comes back. But this is optional — the system prompt lists it as an available tool, not a mandatory step. The LLM can skip it.
- **If the contractor has no history, or the LLM skips the lookup**: every number — labour hours, hourly rates, material prices — comes from the LLM's pre-training knowledge. These are plausible guesses drawn from the internet at large. They are uncited, un-versioned, non-auditable, and wrong for any specific contractor in any specific market.

This violates the product vision's core promise: *"Every recommendation Kerf makes must trace back to a specific standard, regulation, or data point."* (Product Vision, §2 — Principle 4). A kitchen installation estimate grounded in Claude's training corpus cannot cite anything. The contractor has no way to know where the numbers came from, and neither does Kerf.

---

## 2. Design Principles

Six principles govern how estimating intelligence works. Every design decision in this document traces back to one or more of these.

1. **Every number must be cited.** No value enters a Labour or Item node without a reference to the graph node it came from — a ResourceRate, a ProductivityRate, a MaterialCatalogEntry, a PurchaseOrder, or a contractor-stated override. LLM pre-training knowledge is never a valid source.

2. **Labour rates are never estimated.** The system asks the contractor for their rates and stores them permanently. No industry baseline for $/hour is useful to a specific contractor — the variance between markets, trades, and company structures is too large.

3. **The contractor's own data is the primary intelligence source.** Industry baselines exist for cold start only. As the contractor completes jobs, their data overlays and replaces baselines automatically. The system never prefers a generic number over a contractor-specific one.

4. **Patterns are learned, not authored.** Kerf does not maintain a template library. Recurring patterns in the contractor's own estimates are derived by semantic similarity and co-occurrence analysis over their graph. What questions to ask, what items typically co-occur, what adjustments to apply — all learned from their history.

5. **The system asks only when it must.** If the graph has the answer, use it. If an external source can be fetched, fetch it. Only genuinely missing information becomes a question. The conversational interface stays fast because the agent brings context, not a form.

6. **Rationale is data.** When the agent adjusts a productivity rate or selects a price, the reasoning is captured as an Insight node — not discarded as chat ephemera. Rationale is retrievable, correctable, and reusable on future estimates.

---

## 3. The Source Cascade

Every value on an estimate line follows a priority cascade. The agent tries each level in order and stops at the first that produces a cited answer.

```
Level 1: Contractor's own graph data
         (completed jobs, rate library, PO history)
              │
              ▼ nothing found
Level 2: Contractor's encoded principles
         (Insight nodes matching the current context)
              │
              ▼ nothing applicable
Level 3: External sourced data
         (agent-searched supplier prices, industry baselines)
              │
              ▼ nothing available
Level 4: Ask the contractor
         (capture once, store permanently, reuse forever)
```

Different value types collapse to different levels:

| Value type | Level 1 | Level 2 | Level 3 | Level 4 |
|---|---|---|---|---|
| **Labour rate** ($/hr) | ResourceRate from rate library | — | — | **Always ask** (never estimate) |
| **Labour productivity** (hrs/unit) | ProductivityRate from completed jobs | Insight nodes with matching context | IndustryProductivityBaseline (flagged) | Ask if completely novel scope |
| **Material price** ($/unit) | PO history / MaterialCatalogEntry | — | Agent-searched supplier price | Ask if unsearchable |
| **Material quantity** | — | — | — | Derived from scope (voice, drawings, plans) — not part of this cascade |

### Labour rates: never estimated, always asked

Labour rates are company-specific decisions. A journeyman electrician bills $85/hr in Phoenix, $140/hr in San Francisco, $45/hr in rural Ohio. No industry baseline is useful.

**Onboarding flow:** First estimate session, the agent asks for the contractor's key roles and rates. "What do you charge for yourself? Your helper? Your apprentice?" Each answer creates a `ResourceRate` node with `source: "contractor_stated"`, confidence 1.0, timestamped.

**Just-in-time capture:** First time an estimate needs a role that has no stored rate, the agent asks one question. Captured once, reused on every future estimate. Not a form — a conversation.

**Tool contract enforcement:** `create_labour` requires `rate_source_id` pointing at a `ResourceRate` node. If no rate exists for the needed role, the tool rejects the call. The LLM must either find an existing rate or trigger the capture flow. It cannot fabricate a number.

### Labour productivity: estimated with stated rationale

Productivity rates (hours per unit of work) are estimable from both the contractor's history and industry data. Unlike $/hr rates, there are meaningful baselines — "EMT conduit in drop ceilings: 30-40 LF/hour" is defensible as a starting point.

**When the contractor has history:** The agent retrieves `ProductivityRate` nodes derived from their own completed jobs (TimeEntry actuals aggregated by WorkCategory). These carry sample size and standard deviation — confidence improves with every completed job.

**When the contractor has principles:** The agent queries `Insight` nodes whose `applies_when` criteria match the current project context (building type, ceiling height, renovation vs new construction, etc.) and applies them. Example: *"adjusted +15% based on your note from the Peachtree job about low-ceiling renovations."*

**When neither exists:** The agent falls back to `IndustryProductivityBaseline` nodes — seeded values from authoritative sources (RSMeans, trade-body publications), explicitly flagged as baseline with low confidence. The estimate line shows: *"Source: industry baseline (RSMeans 2026). No company history for this scope yet."*

**Rationale is always stated and captured:** Every productivity value the agent proposes comes with a source citation and a stated rationale. The rationale is persisted as an `Insight` node linked to the WorkItem (see Section 4).

### Material prices: history, then agent search, then ask

**When the contractor has history:** Past PurchaseOrders in the graph contain real prices from real suppliers, timestamped. "Sarah's firm bought 200ft of 12 AWG THHN at $0.89/ft from Graybar Atlanta on 2026-03-14." This is cited and used.

**When the contractor has a catalog entry but no recent PO:** The `MaterialCatalogEntry` (populated from past confirmed agent searches or manual entry) provides a price with `captured_at`. If older than 60 days, the agent flags: *"price captured 4 months ago — confirm or refresh?"*

**When nothing exists (agent search):** The agent searches for the item — structured supplier APIs (Graybar, Ferguson, Home Depot Pro) where available, web search as fallback. Returns 2-3 real options with real prices, source URLs, and timestamps. The contractor confirms or selects one. The confirmed selection creates a `MaterialCatalogEntry` node with full provenance — reusable on future estimates. Preferred supplier is learned via a `PREFERRED_SUPPLIER` relationship on the Company node and weighted in future searches.

**Practical constraints:**
- **Staleness**: every `MaterialCatalogEntry` has `captured_at`. Re-check if older than configurable threshold (default 60 days).
- **Prefer structured APIs over scraping**: supplier APIs and parseable quote attachments are the primary sources. Web scraping is a fallback.
- **Cost discipline**: agent search costs tokens and web calls. Cache results per contractor per item for 30 days. Batch searches when multiple items are unknown on the same estimate.
- **Who picks**: the agent selects a default and shows alternatives. The contractor overrides with one tap. The override preference is learned.

---

## 4. The Insight Learning Loop

This is the mechanism by which the contractor's reasoning — not just their numbers — becomes encoded in the graph and applied to future estimates.

### How Insights are created

When the agent proposes a productivity adjustment with a rationale, that rationale is persisted as an `Insight` node:

```
(Insight {
  id: "ins_a1b2c3d4",
  reasoning: "Low ceiling renovation: +15% labour time due to ladder work and confined space",
  adjustment_type: "productivity_multiplier",
  adjustment_value: 1.15,
  applies_when: {
    building_type: "renovation",
    ceiling_height_category: "low"
  },
  confidence: 0.7,
  validation_count: 0,
  source: "agent_proposed",
  created_at: datetime()
})
```

The Insight is linked to:
- The `WorkItem` it was applied to (`:APPLIED_INSIGHT`)
- The `ProductivityRate` it modified (`:ADJUSTS`)
- The `Conversation` where it was discussed (`:DISCUSSED_IN`)

### How Insights are retrieved

Before any productivity value is proposed in a new estimate, `context_assembler` queries Insights whose `applies_when` criteria match the current project context. Matching Insights are injected into the LLM's system context as a structured block — not listed as "available to query," but surfaced as "here is what applies right now."

The agent then says: *"Last time I added 15% for low-ceiling renovations — still apply that, or adjust?"*

### How Insights are updated

When the contractor confirms: `validation_count` increments, `confidence` increases.

When the contractor corrects ("make it 20%"): `adjustment_value` updates, `source` changes to `"contractor_corrected"`, `confidence` resets to 0.8 (higher than agent-proposed, because the contractor said so).

When the contractor inverts ("actually we're faster in renovations now"): the Insight is invalidated (`valid_until` set to now) and a new Insight is created with the new reasoning, linked to the old one via `SUPERSEDES`.

### How Insights compound

After 5-10 interactions, the contractor's renovation reasoning is encoded as retrievable graph logic. The agent doesn't re-derive the adjustment from scratch each time — it retrieves the Insight, shows its provenance, and asks to confirm. Over time, `validation_count` and `confidence` increase, and the agent can apply high-confidence Insights without asking (confidence-gated autonomy).

### How Insights feed back to the graph

Validated corrections (high confidence, multiple validations) are candidates for promotion to the knowledge graph itself. A correction like "scaffolding supervision requires OSHA 30, not OSHA 10" can feed back into the regulatory ontology via the standard ontology population pipeline with human spot-checking.

---

## 5. Voice and Mobile Estimating

Voice is the primary input modality for estimating, not a companion feature. The full estimating workflow is completable from a phone, standing on a jobsite.

### Walking estimate capture

The contractor taps "start estimate" and walks the site narrating. Each utterance is processed by the LLM in near-real-time, producing provisional `WorkItem` cards shown on screen. Each card is timestamped to the audio segment and linked to any photo taken in the same window. The contractor corrects as they go ("no, 2 circuits not 3") and the card updates. The proposal lands in the client's inbox before they leave.

### Learned-pattern prompting

When the contractor says "200-amp panel upgrade," the agent does not consult a template library. Instead, it retrieves the contractor's own past similar estimates via semantic similarity over their graph and asks only about parameters that have actually varied across those jobs. If every panel upgrade used the same meter main, the agent doesn't ask. If distance-to-panel varied and correlated with labour hours, that's the one parameter it prompts for.

For cold-start contractors with no history, the agent uses its general knowledge to propose an initial scope structure — but every number on that structure is sourced from the cascade (Section 3), not from LLM pre-training.

### One utterance, many graph writes

A single voice session on a site walk populates the daily log, safety inspection, quality observations, time entries, and estimate progress simultaneously. Each extracted claim is a separate graph mutation. "Pour went fine this morning, 40 yards placed, noticed the rebar spacing on the west pier looks wider than spec" generates a DailyLog entry, a QualityObservation linked to a CorrectiveAction, and potentially a variation draft.

### Offline-first

Voice recordings, photos, and provisional graph writes queue locally on the device and reconcile on sync. This is an architectural constraint from day one. The contractor in a basement mechanical room or on a rural site cannot be told the app doesn't work.

### Drawing + voice for geometric trades

For fencing, paving, decking, and site concrete, drawing on a satellite overlay or scale sketch is faster than counting by voice. Kerf pairs both: draw the shape, narrate the spec. Neither modality is forced.

---

## 6. Cold Start

A new contractor on day 1 has no completed jobs, no rate library, no PO history.

**What's immediately available:**
- `Regulation` and `CodeArticle` nodes (Domain 1 — already populated) for compliance requirements by jurisdiction and trade
- `IndustryProductivityBaseline` nodes (seeded from authoritative sources) for rough labour-hour estimates, flagged as low confidence
- Agent web search for material prices from real suppliers

**What's captured in the first session:**
- Labour rates (asked, stored as ResourceRate nodes — reused forever)
- Material preferences (confirmed from agent search results — stored as MaterialCatalogEntry nodes)
- First Insights (any rationale the contractor provides — "I'm slower in renovations" — captured immediately)

**What accumulates with each completed job:**
- Actual labour hours (TimeEntry → ProductivityRate refinement, sample size grows)
- Actual material costs (PurchaseOrder → MaterialCatalogEntry updates)
- Validated Insights (confirmation or correction of past rationale)

The transition from baseline to contractor-owned data is automatic. As `ProductivityRate.sample_size` increases, the derived confidence exceeds the baseline's fixed low confidence, and the system switches. The contractor never configures this.

---

## 7. Ontology Changes

### 7.1 New nodes

**Insight**

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | `ins_{token_hex(8)}` |
| `reasoning` | string | Yes | Human-readable rationale |
| `adjustment_type` | string | Yes | What kind of adjustment (productivity_multiplier, price_adjustment, scope_addition) |
| `adjustment_value` | float | No | Numeric adjustment (e.g. 1.15 for +15%) |
| `applies_when` | map | Yes | Structured conditions for retrieval matching |
| `confidence` | float | Yes | 0.0-1.0, increases with validation |
| `validation_count` | integer | Yes | Times confirmed by contractor |
| `source` | string | Yes | agent_proposed, contractor_stated, contractor_corrected |
| `valid_from` | datetime | Yes | When this Insight became active |
| `valid_until` | datetime | No | Sentinel 9999-12-31 if active, set on invalidation |
| `supersedes` | string | No | ID of Insight this replaces |
| + Actor Provenance fields | | | |

**MaterialCatalogEntry**

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | `mce_{token_hex(8)}` |
| `description` | string | Yes | What the item is |
| `product` | string | No | Specific product name/model/SKU |
| `unit` | string | Yes | Unit of measurement (EA, LF, SF, etc.) |
| `unit_cost_cents` | integer | Yes | Price per unit in cents |
| `supplier` | string | No | Supplier name |
| `source_url` | string | No | Where the price was found |
| `captured_at` | datetime | Yes | When the price was captured |
| `source` | string | Yes | agent_searched, contractor_stated, po_derived |
| + Actor Provenance fields | | | |

**IndustryProductivityBaseline**

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | `ipb_{token_hex(8)}` |
| `description` | string | Yes | What scope this covers |
| `trade_type` | string | Yes | Electrical, concrete, HVAC, etc. |
| `output_per_hour` | float | Yes | Units of output per labour hour |
| `unit` | string | Yes | Unit (LF, EA, SF, etc.) |
| `context` | map | No | Conditions (new_construction, renovation, ceiling_type, etc.) |
| `source_reference` | string | Yes | Citation (e.g. "RSMeans 2026, Division 26") |
| `effective_date` | date | Yes | When this baseline was published |
| `confidence` | float | Yes | Fixed low value (0.3) — always below contractor-derived rates |
| + Actor Provenance fields | | | |

### 7.2 Modified nodes

**Labour** — add source tracking:

| New Property | Type | Required | Description |
|---|---|---|---|
| `rate_source_id` | string | Yes | ResourceRate.id that sourced the rate_cents |
| `productivity_source_id` | string | No | ProductivityRate.id or IndustryProductivityBaseline.id that determined hours |
| `productivity_source_type` | string | No | company_historical, industry_baseline, contractor_override |

**Item** — add source tracking:

| New Property | Type | Required | Description |
|---|---|---|---|
| `price_source_id` | string | No | MaterialCatalogEntry.id or PurchaseOrder line that sourced the price |
| `price_source_type` | string | No | po_history, catalog_entry, agent_searched, contractor_stated |

### 7.3 New relationships

| Relationship | From | To | Description |
|---|---|---|---|
| `APPLIED_INSIGHT` | Labour | Insight | This labour line was adjusted by this Insight |
| `HAS_INSIGHT` | Company | Insight | Company owns this Insight |
| `ABOUT_WORK_CATEGORY` | Insight | WorkCategory | Insight applies to this type of work |
| `SOURCED_FROM_CATALOG` | Item | MaterialCatalogEntry | Item price came from this catalog entry |
| `HAS_CATALOG_ENTRY` | Company | MaterialCatalogEntry | Company's material catalog |
| `PREFERRED_SUPPLIER` | Company | Contact | Company prefers this supplier (learned) |
| `SUPERSEDES_INSIGHT` | Insight | Insight | This Insight replaces the older one |

---

## 8. Tool Contract Changes

### 8.1 `create_labour` — require sources

Current contract accepts `rate_cents` and `hours` as raw values. New contract:

```
create_labour(
  work_item_id: str,        # required
  task: str,                 # required — what the labour is
  rate_source_id: str,       # REQUIRED — ResourceRate.id
  hours: float,              # required — estimated hours
  productivity_source_id: str | None,  # recommended — what determined the hours
  productivity_source_type: str | None, # company_historical | industry_baseline | contractor_override
  applied_insight_ids: list[str],       # Insight IDs applied to adjust hours
  notes: str | None
)
```

**Enforcement:** The service layer resolves `rate_cents` from `rate_source_id` by graph lookup. If the ResourceRate doesn't exist, the tool returns an error: *"No rate found for [role]. Use capture_labour_rate to ask the contractor."* The LLM cannot supply a raw dollar value.

If `hours` diverges from `productivity_source_id`'s baseline and `applied_insight_ids` is empty, the service requires a new Insight to be created explaining the adjustment — atomically in the same transaction.

### 8.2 `create_item` — require sources

```
create_item(
  work_item_id: str,         # required
  description: str,          # required
  quantity: float,           # required
  unit: str,                 # required
  price_source_id: str | None,    # MaterialCatalogEntry.id or PO line ref
  price_source_type: str | None,  # po_history | catalog_entry | agent_searched | contractor_stated
  unit_cost_cents: int | None,    # only accepted if price_source_type = "contractor_stated"
  notes: str | None
)
```

**Enforcement:** If `price_source_id` is provided, `unit_cost_cents` is resolved from the graph. If neither `price_source_id` nor `unit_cost_cents` is provided, the tool returns an error: *"No price source. Use search_materials to find supplier pricing, or provide a contractor-stated price."* Raw LLM-generated prices are rejected unless explicitly tagged as `contractor_stated`.

### 8.3 `search_historical_rates` — structural injection

No longer an optional tool call. Before any estimating conversation, `context_assembler` calls `search_historical_rates` with the project's work description and injects results into the system context. The LLM receives: *"Company historical data for similar work: [results]. Applicable Insights: [results]. Company rate library: [results]."*

This removes the opt-in failure mode — the LLM always has the contractor's history in context when it starts estimating.

### 8.4 New tools

| Tool | Purpose |
|---|---|
| `capture_labour_rate` | Ask the contractor for a rate, create a ResourceRate node. Called when create_labour fails due to missing rate. |
| `search_materials` | Agent searches supplier APIs / web for material pricing. Returns 2-3 options. Contractor confirms to create MaterialCatalogEntry. |
| `confirm_material_price` | Contractor selects from search_materials results. Creates MaterialCatalogEntry and optionally sets PREFERRED_SUPPLIER. |
| `create_insight` | Persist an agent's rationale as an Insight node. Called atomically with create_labour when productivity is adjusted. |
| `update_insight` | Update an Insight's value, confidence, or validity based on contractor feedback. |

---

## 9. Enforcement

### 9.1 Behavior contracts (BR-X rules)

These are the testable claims that bind the vision to the implementation.

**Source cascade enforcement:**
- **BR-EST-030**: `create_labour` MUST reject calls where `rate_source_id` does not reference an existing, active `ResourceRate` node owned by the contractor's company.
- **BR-EST-031**: `create_item` MUST reject calls where `unit_cost_cents` is provided without `price_source_type = "contractor_stated"`.
- **BR-EST-032**: Before any estimating conversation begins, `context_assembler` MUST query and inject: (a) matching historical WorkItems, (b) applicable Insights, (c) company ResourceRates and ProductivityRates.

**Insight loop enforcement:**
- **BR-EST-041**: When `create_labour` applies a productivity adjustment that diverges from the source baseline, the rationale MUST be persisted as an `Insight` node with structured `applies_when` criteria — atomically in the same transaction.
- **BR-EST-042**: Before any productivity value is proposed, matching `Insight` nodes MUST be retrieved and included in the LLM's working context.
- **BR-EST-043**: When a contractor's chat response confirms, corrects, or contradicts an Insight, the Insight MUST be updated (confidence, value, or invalidation) before the response is considered complete.

**Labour rate enforcement:**
- **BR-EST-050**: No `Labour` node may be created with a `rate_cents` value that was not resolved from a `ResourceRate` node via graph lookup. The LLM never supplies a dollar value directly.
- **BR-EST-051**: When no `ResourceRate` exists for a required labour role, the agent MUST ask the contractor (via `capture_labour_rate`) rather than estimating.

**Material price enforcement:**
- **BR-EST-060**: Material prices sourced via `search_materials` MUST include `source_url` and `captured_at` in the resulting `MaterialCatalogEntry`.
- **BR-EST-061**: Material prices older than the configurable threshold (default 60 days) MUST be flagged to the contractor as potentially stale before use.

### 9.2 Cross-session UJ-X journey sketches

These journeys exercise the full behavioral loop across sessions and simulated time. No mocks.

**UJ-EST-001: Cold-start first estimate.**
- New contractor, no history, no rate library.
- Agent asks for labour rates (captured as ResourceRate).
- Agent searches for material prices (created as MaterialCatalogEntry).
- Productivity uses IndustryProductivityBaseline (flagged).
- Assert: every cost line has a cited source. No LLM-fabricated values.

**UJ-EST-007: Learning loop over 3 estimates.**
- Session 1: Contractor estimates renovation, agent proposes baseline productivity, contractor says "add 15% for low ceilings." Assert: Insight created with correct `applies_when`.
- [Simulated: job closes, context cleared]
- Session 2: New renovation estimate. Assert: Insight retrieved, surfaced in conversation, applied to proposed productivity. Contractor says "make it 20%." Assert: Insight updated.
- [Simulated: context cleared]
- Session 3: New renovation estimate. Assert: 20% adjustment is what's proposed, cited to the updated Insight.

**UJ-EST-012: Estimate to execution to next estimate (the moat loop).**
- Estimate a job with baseline productivity.
- Simulate job execution: create TimeEntries against WorkItems.
- Close the job.
- Start a new similar estimate. Assert: ProductivityRate now reflects actuals from the completed job, not the original baseline. Sample size incremented.

**UJ-EST-015: Voice walking estimate, offline, sync.**
- Start estimate via voice on mobile.
- Capture 5+ WorkItems from narration with photos.
- Simulate offline (queue writes).
- Simulate reconnection (sync).
- Assert: all WorkItems present in graph with correct timestamps, photos linked, source citations intact.

### 9.3 Telemetry

Metrics that detect when the system "works" but the behavior is dead.

| Metric | What it measures | Alert band |
|---|---|---|
| **Citation coverage** | % of Labour/Item nodes with a valid source reference | Must be 100%. Any drop = structural regression. |
| **Insight creation rate** | Insights created per estimating session | Should rise with active contractors. Zero for 7+ days = loop broken. |
| **Insight retrieval rate** | % of estimating sessions with applicable Insights where at least one was surfaced | >90% when applicable Insights exist. |
| **Insight validation rate** | % of surfaced Insights where contractor engaged (confirmed/corrected) | Track for product learning. No hard threshold. |
| **Source cascade distribution** | % of values from each cascade level (own history / Insight / external / asked) | Own-history share should increase over time per contractor. Flat = learning loop broken. |
| **Rate capture rate** | % of missing-rate situations resolved by asking vs. errored | Should be ~100%. Low = UX failure in capture flow. |
| **Material search success** | % of agent material searches that produced usable results | Track and improve. Low = supplier API coverage gap. |
| **Baseline displacement** | Time from first estimate to >50% of values sourced from own history | Track per contractor. Shorter = faster value delivery. |

---

## 10. Phasing

This design depends on Phase 0 (audit events, provenance display) being complete. Within estimating intelligence, the work phases as:

| Phase | Scope | Unlocks |
|---|---|---|
| **1a: Source cascade + tool contracts** | Modify `create_labour` and `create_item` to require source IDs. Add `capture_labour_rate`. Modify `context_assembler` to inject historical rates. Add `Insight` schema + `create_insight` tool. | Every estimate is cited. Labour rates are always asked. Insight loop begins. |
| **1b: Material intelligence** | Add `MaterialCatalogEntry` schema. Build `search_materials` and `confirm_material_price` tools. Supplier API integrations (start with 1-2 major suppliers). | Material prices are grounded in real supplier data. Catalog builds from contractor use. |
| **1c: Voice estimate capture** | Voice-to-WorkItem extraction pipeline. Real-time card UI on mobile. Offline queue. | Walking estimate workflow as described in vision §3.13 and §7. |
| **1d: Learned-pattern prompting** | Semantic similarity search over past estimates. Co-occurrence analysis for scope suggestion. Variable-parameter detection for smart prompting. | The agent asks fewer questions with each estimate. Scope suggestions improve with history. |
| **2: Productivity feedback loop** | TimeEntry → ProductivityRate aggregation on job close. Automatic confidence recalculation. Baseline displacement tracking. | The moat loop: estimates improve with every completed job. |
| **3: Advanced** | Confidence-gated Insight autonomy. Cross-project portfolio queries. Drawing + voice for geometric trades. IndustryProductivityBaseline seeding from authoritative sources. | Full vision maturity. |

Phase 1a is the structural foundation — without it, every other phase builds on the hallucination problem. Ship it first.
