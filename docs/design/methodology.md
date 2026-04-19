# Methodology — Design & Data Model

**Status:** Draft for review
**Author:** Claude + Paul
**Date:** 2026-04-17
**Scope:** The data model and conversational authoring flow for **Methodology** — the layer that captures *how* a contractor is building something, distinct from *what kind* of work it is (which is WorkCategory). Methodology cascades Project → WorkPackage → WorkItem, drives productivity adjustments via Insights, and is emergent from conversation rather than authored as templates.
**Depends on:** [canonical-work-categories.md](canonical-work-categories.md) — Methodology references the WorkCategory it applies to.
**Related:** [estimating-intelligence.md](estimating-intelligence.md) Principle 4 (patterns learned not authored) | [work-item-ui.md](work-item-ui.md) §10 (UI surface) | [preview/work-items.html](../preview/work-items.html) Source Detail tab

---

## 1. The Problem

Two questions exist on every WorkItem:

1. **What kind of work is this?** — answered by WorkCategory (canonical taxonomy — MasterFormat, NRM 2, NATSPEC)
2. **How are we doing it, this time?** — answered by Methodology (contractor's specific approach)

WorkCategory is industry-standard classification: "26 24 16 Panelboards." Shared across contractors. Relatively static.

Methodology is the opposite: contractor-specific, per-project, emergent from the conversation between the contractor and the agent. Two contractors doing the same kind of work (both installing walk-in showers under MasterFormat 22 42 00) can have wildly different methodologies:

- Contractor A: mortar bed + sheet membrane + point drain + frameless glass
- Contractor B: pre-formed pan + liquid membrane + linear drain + framed glass

Both are valid. Both produce different labour rates, material lists, sequencing, risks. Neither is "right" in the abstract — but *this contractor for this job* has a methodology, and capturing it is what makes Kerf's estimates defensible.

Today Kerf has no representation of methodology. All methodology-sensitive information (adjustments, risks, contractor preferences) lives either in free-text notes or in Insight nodes without structural anchoring. The result: the agent can't reliably retrieve past methodology decisions, can't cascade them, and can't attribute productivity adjustments to specific approach choices.

---

## 2. Design Principles

Eight principles, each traceable to constraints from the product vision and prior design work.

1. **Methodology is emergent, not authored.** No library of pre-built methodology templates. Each project's methodology is created by the conversation between contractor and agent, potentially cloned from a matching past project. This preserves [estimating-intelligence.md](estimating-intelligence.md) Principle 4: patterns are learned, not authored.

2. **Methodology is structured, not free text.** The conversational output is captured as an `approach` map — a set of key/value pairs that are queryable, composable, and retrievable. Not a single blob of prose.

3. **Keys are open-vocabulary but coalesce over time.** The first shower-install conversation might produce `approach.waterproofing = "Schluter Kerdi"`. The fifth produces the same key. The agent learns that "waterproofing" is a recurring key for this category and surfaces it proactively in future conversations. Keys don't need a fixed schema; they emerge from repeated use.

4. **Methodology cascades hierarchically.** A Project has methodology. A WorkPackage inherits and can override specific keys. A WorkItem inherits from its Package and can override at item level. Overrides are per-key, not wholesale — an item can override just `waterproofing` while inheriting everything else from its package.

5. **Methodology is scoped to a WorkCategory.** A methodology for "walk-in shower install" doesn't apply to "panel upgrade." The category link is the retrieval anchor — when the agent looks up past methodologies, it filters by the current item's category first.

6. **Insights attach to methodology, not to free-floating conditions.** When a contractor says "renovation shower installs on joist floors take 15% longer," that becomes an Insight with `applies_when` keyed on methodology approach values (`substrate: "joist_floor"`) — not a vague condition string. This makes Insights queryable and composable.

7. **Methodology is versioned temporally.** Contractor changes their approach over time (callback on a membrane → switch to different product). Old methodology is preserved (`valid_until` set to sentinel or invalidation date); historical estimates remain reconstructible.

8. **Methodology is first-class in the UI.** Shown on every WorkItem where it exists (not hidden behind advanced menus). Inheritance is visible. Overrides are visible. The contractor can see at a glance: "this item is using Package-level methodology with one override."

---

## 3. The Methodology Node

```cypher
(:Methodology {
  id: "meth_a1b2c3d4",
  scope_level: "project" | "package" | "item",   // where in the cascade
  approach: {                                     // structured key/value map
    substrate: "cement_board_on_sistered_joists",
    waterproofing: "schluter_kerdi",
    drain_type: "linear_tile_insert",
    glass: "frameless_fixed_plus_hinge"
  },
  rationale: "Joist floor, past callbacks on liquid membrane — switched approach",
  authored_at: datetime(),
  authored_by: "user_marco",                      // actor provenance
  cloned_from: "meth_xyz",                        // if derived from past project
  valid_from: datetime(),
  valid_until: date("9999-12-31"),                // sentinel = currently active
  // + standard provenance fields
})
```

### 3.1 Property details

| Property | Type | Required | Purpose |
|----------|------|----------|---------|
| `id` | string | Yes | `meth_{token_hex(8)}` |
| `scope_level` | enum | Yes | `project` / `package` / `item` — which tier of the cascade |
| `approach` | map | Yes | Open-vocabulary key/value pairs capturing methodology choices |
| `rationale` | string | No | Free-text narrative on why this approach (contractor-authored) |
| `authored_at` | datetime | Yes | When created |
| `authored_by` | string | Yes | User or agent ID |
| `cloned_from` | string | No | Parent methodology ID if cloned from a past project |
| `valid_from` | datetime | Yes | When this methodology became active |
| `valid_until` | datetime | Yes | Sentinel `9999-12-31` if active |
| + Actor Provenance fields | | | Consistent with other tenant-scoped entities |

### 3.2 Relationships

```cypher
// Cascade attachment — one methodology per tier
(Project)-[:USES_METHODOLOGY]->(Methodology {scope_level: "project"})
(WorkPackage)-[:USES_METHODOLOGY]->(Methodology {scope_level: "package"})
(WorkItem)-[:USES_METHODOLOGY]->(Methodology {scope_level: "item"})

// Hierarchy within a project
(Methodology {scope_level: "package"})-[:CHILD_OF]->(Methodology {scope_level: "project"})
(Methodology {scope_level: "item"})-[:CHILD_OF]->(Methodology {scope_level: "package"})

// Category anchoring — methodology is scoped to a category
(Methodology)-[:APPLIES_TO_CATEGORY]->(WorkCategory:Canonical)

// Insight attachment — Insights match on methodology + approach keys
(Insight)-[:APPLIES_TO_METHODOLOGY_WITH {
  approach_match: {substrate: "joist_floor"}    // which approach keys trigger this insight
}]->(Methodology)

// Supersession for temporal versioning
(Methodology)-[:SUPERSEDES]->(Methodology)      // new methodology replaces an older one
```

### 3.3 Indexes and constraints

```cypher
// Required indexes
CREATE INDEX index_methodology_scope_level IF NOT EXISTS
  FOR (n:Methodology) ON (n.scope_level);
CREATE INDEX index_methodology_valid IF NOT EXISTS
  FOR (n:Methodology) ON (n.valid_until);

// Constraints
CREATE CONSTRAINT constraint_methodology_id IF NOT EXISTS
  FOR (n:Methodology) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT constraint_methodology_id_exists IF NOT EXISTS
  FOR (n:Methodology) REQUIRE n.id IS NOT NULL;
CREATE CONSTRAINT constraint_methodology_scope_exists IF NOT EXISTS
  FOR (n:Methodology) REQUIRE n.scope_level IS NOT NULL;
```

### 3.4 Structural validation

Added to `backend/fixtures/golden/validation-tests.cypher`:

```cypher
// Every Methodology must have an approach map (can be empty but present)
MATCH (m:Methodology)
WHERE m.approach IS NULL
RETURN m.id AS violation, "Methodology missing approach map" AS reason

// Every non-project Methodology must have a CHILD_OF parent
MATCH (m:Methodology)
WHERE m.scope_level IN ["package", "item"]
  AND NOT (m)-[:CHILD_OF]->(:Methodology)
RETURN m.id AS violation, "Non-project methodology missing parent" AS reason

// Every Methodology must APPLIES_TO_CATEGORY
MATCH (m:Methodology)
WHERE NOT (m)-[:APPLIES_TO_CATEGORY]->(:WorkCategory:Canonical)
RETURN m.id AS violation, "Methodology missing category anchor" AS reason

// CHILD_OF must go up the scope_level chain (item → package → project)
MATCH (m1:Methodology)-[:CHILD_OF]->(m2:Methodology)
WHERE NOT (
  (m1.scope_level = "package" AND m2.scope_level = "project")
  OR (m1.scope_level = "item" AND m2.scope_level = "package")
)
RETURN [m1.id, m2.id] AS violation, "Invalid CHILD_OF hierarchy" AS reason
```

---

## 4. The Cascade Model

### 4.1 Three tiers

Methodology applies at three levels, each inheriting from its parent:

```
Project methodology
  "Residential renovation · Retain fixture layout · MEP integration with existing"
  approach: {
    project_scope: "renovation",
    fixture_layout: "retain_existing",
    mep_approach: "integrate_with_existing"
  }
    ↓ inherited by
WorkPackage methodology (Reception)
  "+ Conduit in finished walls (not ceiling rough-in)"
  approach: {
    // inherits project keys
    conduit_placement: "finished_walls",     // new at package level
    ceiling_access: "none"                    // new at package level
  }
    ↓ inherited by
WorkItem methodology (Standard receptacle ×6)
  No item-level overrides
  (inherits all package keys, which inherit all project keys)
```

### 4.2 Inheritance resolution

Given a WorkItem, its *effective methodology* is computed by merging the cascade:

1. Start with Project methodology's `approach` map
2. Merge in Package methodology's `approach` (Package keys override Project keys if same name)
3. Merge in Item methodology's `approach` (Item keys override Package keys)

Example:
- Project: `{project_scope: "renovation", fixture_layout: "retain_existing"}`
- Package (Reception): `{conduit_placement: "finished_walls"}`
- Item (Floor box): `{conduit_placement: "slab_core_drill"}`  *(override)*

Effective methodology for Floor box item:
```
{
  project_scope: "renovation",              // from Project
  fixture_layout: "retain_existing",         // from Project
  conduit_placement: "slab_core_drill"       // overridden at Item
}
```

The `source_level` of each key is tracked for display purposes — so the UI can show which level contributed each key.

### 4.3 When tiers are written

- **Project methodology** is authored in the first estimating conversation for a new project. The agent asks high-level setup questions ("Is this a renovation or new build? Existing fixture layout retained?") and the answers become the Project-level approach map.
- **Package methodology** is authored when the contractor or agent introduces a scope that has specific methodology implications ("Reception area — conduit in finished walls"). Often inherits most keys from Project and adds 1-3 new ones.
- **Item methodology** is authored only when a specific item needs a different approach than its Package dictates ("This floor box is slab-on-grade, we need to core-drill — unlike the rest of Reception"). Rare — most items inherit cleanly.

### 4.4 Empty methodology

A Project / Package / Item can have NO methodology attached. Jake's solo-contractor jobs often work this way — the WorkItems are simple enough that no methodology choices are material. The UI surfaces methodology only when it's attached; empty methodology = no UI row.

### 4.5 Methodology without a linked WorkItem

Methodology nodes can exist on a Project or Package without any item-level attachments (common for early-stage quoting). The cascade is still resolvable for any WorkItems subsequently added.

---

## 5. The Approach Map

### 5.1 Open-vocabulary keys

The `approach` map is intentionally schemaless. There's no global list of valid keys. Keys emerge from the conversations contractors actually have.

Examples of keys that might appear for different trades:

| Category | Common approach keys |
|----------|---------------------|
| Electrical (26) | `conduit_material`, `conduit_placement`, `panel_brand`, `wire_gauge_spec`, `breaker_type`, `service_disconnect_coordination` |
| Plumbing (22) | `pipe_material`, `fitting_type`, `venting_approach`, `water_heater_type`, `fixture_grade` |
| Tile/finishes (09) | `substrate`, `waterproofing`, `tile_size`, `grout_type`, `sealer` |
| Framing (06) | `lumber_grade`, `nailing_schedule`, `sheathing_spec`, `weather_barrier` |
| Shower install | `substrate`, `waterproofing`, `drain_type`, `glass`, `curb_approach` |

New keys appear as contractors describe new approaches. The system doesn't reject them; it records them and uses them in future retrievals.

### 5.2 Values

Values are also open — but with conventions:

- **Slug-style strings for categorical choices:** `"schluter_kerdi"`, `"cement_board_on_joists"`, `"linear_tile_insert"`. Easier for matching across projects than free prose.
- **Numeric or unit values for quantified approach:** `{rebar_schedule: "#4 @ 12oc"}`, `{pour_depth_inches: 4}`
- **Multi-value arrays for lists:** `{fall_restraint_methods: ["guardrail", "warning_line"]}`

### 5.3 Key coalescence over time

Over many projects, the system builds an implicit taxonomy of which keys appear for which categories. When a new Project is started under category "walk-in shower install," the agent proactively asks about keys that have appeared in >N past projects of that category.

This is a retrieval optimisation, not a schema enforcement. Contractors can always introduce new keys; the system just doesn't prompt for them until they've seen a few uses.

### 5.4 Key synonyms

Different contractors might use different names for the same concept:
- Contractor A: `approach.waterproofing = "schluter_kerdi"`
- Contractor B: `approach.membrane = "schluter_kerdi"`

The agent handles this via **semantic matching** during retrieval — "waterproofing" and "membrane" are close enough to merge for query purposes. Over time, suggest key unification to contractors who use both. No forced canonicalisation.

---

## 6. Insight Attachment

### 6.1 The binding

Insights that adjust productivity, price, or scope are attached to Methodology via:

```cypher
(Insight)-[:APPLIES_TO_METHODOLOGY_WITH {
  approach_match: {              // partial approach map
    substrate: "joist_floor",
    conduit_placement: "finished_walls"
  }
}]->(Methodology)
```

The `approach_match` map is a partial: it specifies which keys must match for this Insight to fire. A Methodology with `{substrate: "joist_floor", conduit_placement: "finished_walls", drain_type: "linear"}` would match the above (both specified keys present with specified values), even though it has more keys.

### 6.2 Matching at query time

When computing a WorkItem's labour productivity, the agent:

1. Resolves the effective methodology (cascade merge)
2. Queries Insights linked via `APPLIES_TO_METHODOLOGY_WITH` where:
   - `APPLIES_TO_CATEGORY` matches the WorkItem's category
   - Every key in `approach_match` is present in the effective methodology with the matching value
3. Applies matching Insights (multiplicatively for productivity multipliers, additively for qualitative notes)
4. Records the applied Insights on the Labour node via `applied_insight_ids`

### 6.3 Insight creation

When a contractor states a methodology-specific adjustment during conversation ("finished-wall renovation is 15% slower"), the agent creates:

1. An `Insight` node with the adjustment details
2. An `APPLIES_TO_METHODOLOGY_WITH` relationship keyed on the specific approach values that triggered the insight ("renovation" + "finished_walls")
3. Links to the current Methodology and its ancestors via the cascade

The Insight is Company-scoped and applies to **all future methodologies** that match the approach keys — not just this project.

### 6.4 Confidence evolution

Each time an Insight fires and the contractor confirms (or doesn't dispute) the adjustment, `validation_count` increments and `confidence` rises. Contractor corrections decrement confidence and can invalidate the Insight (new Insight supersedes).

See [estimating-intelligence.md](estimating-intelligence.md) §4 for the full Insight lifecycle.

---

## 7. Conversational Authoring

### 7.1 First job of a kind

The contractor's first walk-in shower install with Kerf — no past projects of this category:

```
Contractor: "Starting an estimate. Walk-in shower install, 1930s bathroom, 2nd floor."

Agent: [creates Project, categorises "22 42 00 Commercial Showers" or equivalent]
       "Few things to set up before I estimate:
        - Joist floor or slab? (I'm guessing joist on 1930s 2nd floor but confirm)
        - Existing waterproofing condition?
        - Drain type preference — point drain, linear, or tileable?"

Contractor: "Joist. Nothing existing, stripping to the studs. Linear drain."

Agent: [writes Project methodology with approach keys: substrate=joist, 
        starting_condition=gut_to_studs, drain_type=linear]
       "Got it. Any preference on waterproofing system?"

Contractor: "I use Schluter Kerdi now. Had callbacks on liquid membrane."

Agent: [appends waterproofing=schluter_kerdi to approach; creates Insight
        with rationale "past callbacks on liquid membrane"]
       "Switching to Schluter going forward. I'll apply this to any
        similar jobs from now on unless you tell me otherwise."
```

### 7.2 Subsequent similar job

Tenth walk-in shower install:

```
Contractor: "Walk-in shower install, ranch-style, slab floor."

Agent: [retrieves past methodologies matching category=walk_in_shower_install;
        merges most-common approach values + recent contractor-confirmed Insights]
       "Proposing: Schluter Kerdi on cement board (your standard since Aug 2025),
        linear drain tile-insert, frameless fixed + hinge glass. Slab floor this
        time — no joist adjustment. 
        Want me to apply this or adjust?"

Contractor: "Yes, apply. And add the ADA grab bar."

Agent: [writes Project methodology cloned_from last similar project, 
        overriding substrate=slab and adding ada_grab_bar=true]
```

### 7.3 Item-level override via dialogue

Mid-project:

```
Contractor: "The floor box in Reception — that's slab-on-grade so it needs
             to be core-drilled, not like the rest of the package."

Agent: [creates WorkItem-level methodology for the floor box with override
        approach.conduit_placement=slab_core_drill]
       "Noted. Floor box methodology overrides package default — added
        +80% labour for core-drilling. All other Reception items still use
        the package methodology."
```

### 7.4 What the agent captures automatically

Any time the contractor describes a methodology choice, the agent attempts to extract an `approach` key/value and either:

- Add it to the current-scope Methodology, or
- Propose a new Insight if the statement is about a general pattern ("I always use Schluter on joist floors" vs "I'm using Schluter here")

The distinction is made by the agent's parsing of temporal/scope language. Contractors can always review and correct the agent's interpretation in the Source Detail panel (see [work-item-ui.md](work-item-ui.md) §10 and [preview/work-items.html](../preview/work-items.html) Source Detail tab).

---

## 8. Integration with WorkCategory

Methodology is scoped to a WorkCategory via `APPLIES_TO_CATEGORY`. The relationship is many-to-one from Methodology to Category, and one-to-many from Category to Methodology (many different methodologies for the same category).

### 8.1 Retrieval anchoring

When the agent needs to retrieve past methodologies for a new item:

```cypher
MATCH (wi:WorkItem {id: $new_item_id})
      -[:CATEGORISED_AS]->(cat:WorkCategory:Canonical)
MATCH (past_meth:Methodology)-[:APPLIES_TO_CATEGORY]->(cat)
MATCH (past_item:WorkItem)-[:USES_METHODOLOGY]->(past_meth)
MATCH (past_proj:Project)-[:HAS_WORK_ITEM]->(past_item)
WHERE past_proj.company_id = $company_id
  AND past_proj.state IN ['completed', 'closed']    // only completed jobs
RETURN past_meth, past_proj
ORDER BY past_proj.completed_at DESC
LIMIT 10
```

The returned past methodologies are ranked by recency and similarity of current context (Project location, season, client type — whatever's available).

### 8.2 Category-driven key suggestions

As a category accumulates methodology data (e.g., 20 past walk-in-shower methodologies), the agent builds a ranked list of `approach` keys that appear most frequently:

- `waterproofing` — 18/20 projects
- `substrate` — 17/20
- `drain_type` — 16/20
- `glass` — 12/20
- `curb_approach` — 8/20
- `niche_placement` — 4/20

The top keys are the ones the agent proactively asks about on new projects of this category. Lower-frequency keys are only asked if the contractor volunteers them.

---

## 9. UI Surface (Cross-Reference)

The visual design for methodology is specified in [work-item-ui.md §10](work-item-ui.md) and rendered in [preview/work-items.html](../preview/work-items.html) (Card Anatomy and Source Detail tabs).

Summary of integration points:

- **WorkItem card:** second row (conditional — shown only if methodology exists), displays summary + inheritance source
- **WorkPackage header (grid):** methodology chip shown when package has methodology
- **Project context:** project-level methodology shown under the Scope Tracking header
- **Source Detail panel:** full cascade visualisation with level-of-origin highlighting; tap approach keys to edit; Insight attribution chips
- **Mobile edit view:** inline Methodology editor with "View cascade" and "Override for this item" actions

---

## 10. Temporal Versioning

Methodology changes over time. Contractor learns (usually via callbacks or completed job data) that a previous approach was wrong, and switches. The old methodology must remain valid for historical estimates; new methodology takes over for new work.

### 10.1 Invalidation pattern

When a methodology is superseded:

```cypher
// Old methodology retained; valid_until flipped
(old:Methodology {id: "meth_xyz"})
SET old.valid_until = datetime($now)

// New methodology created
CREATE (new:Methodology {id: "meth_abc", ...})

// Supersession link
CREATE (new)-[:SUPERSEDES]->(old)
```

### 10.2 Historical queries

"What methodology was active for this project on date X?"

```cypher
MATCH (proj:Project {id: $project_id})-[:USES_METHODOLOGY]->(meth:Methodology)
WHERE meth.valid_from <= $date AND meth.valid_until > $date
RETURN meth
```

### 10.3 What triggers supersession

- Explicit contractor action: "From now on, use sheet membrane not liquid on joist floors"
- Insight correction with confidence collapse: an Insight that drove a methodology choice gets invalidated repeatedly → methodology pattern is flagged for review
- Regulatory change: updated building code makes the prior approach non-compliant (e.g., new waterproofing standard)

---

## 11. Open Questions

Resolve during build or in dialogue with Paul:

1. **Approach key canonicalisation** — should the system eventually promote frequently-used keys to a "canonical keys" registry per category? Or stay fully open-vocab forever? Current leaning: fully open, with retrieval-time semantic matching handling synonyms.

2. **Methodology comparison UI** — when retrieving past methodologies, should the UI show a diff view ("Proposed: same as Johnson Kitchen except linear instead of point drain")? Probably yes — strong design pattern for clarity.

3. **Cross-contractor methodology sharing** — could anonymised methodology patterns become an industry benchmark (like the canonical categories benchmark)? Long-term opportunity; out of scope for v1.

4. **Methodology on alternates** — a WorkItem can be marked `is_alternate`. Does the alternate get its own methodology (e.g., VE option swaps Schluter for pre-formed pan)? Probably yes — each alternate's methodology is independent from the base.

5. **Agent-proposed vs. contractor-authored methodology** — when the agent proposes methodology from retrieval, is the resulting node marked as "proposed" until contractor confirms? Or does confirmation happen at a coarser level (accepting the whole estimate)? Leaning: the methodology node is created in "draft" status pending contractor confirmation; explicit Confirm action promotes it to active.

6. **What counts as a methodology override vs a new line?** If a WorkItem has `approach.conduit_placement=slab_core_drill` while its Package has `approach.conduit_placement=finished_walls`, is that an override of the same WorkItem, or should it actually be a different WorkItem ("slab floor box" as a distinct scope)? Probably both are valid — contractor's choice. The data model supports either.

---

## 12. Success Criteria

The methodology layer is working when:

1. Every categorised WorkItem can resolve its effective methodology (cascade merge) deterministically via graph traversal.
2. The agent proactively asks methodology-setting questions on the first project of a new category, and retrieves + proposes methodology on subsequent projects of the same category.
3. Insights attached via `APPLIES_TO_METHODOLOGY_WITH` fire correctly at estimate time, adjusting productivity rates with visible attribution.
4. A contractor can override methodology at any cascade level (project, package, item) and the UI shows the override clearly.
5. Methodology supersession preserves historical estimates — a quote from 6 months ago still resolves to the methodology active at that time.
6. The approach map is open-vocabulary; new keys appear without schema changes.
7. Validation queries in CI catch structural violations (missing parent, missing category anchor, invalid hierarchy).
8. Retrieving "all past methodologies for this category" returns results ordered by recency + relevance, and the agent uses this to propose new project methodology.

---

## 13. Out of Scope

- Cross-contractor methodology sharing (anonymised industry benchmarks)
- Automatic approach-key canonicalisation
- Visual methodology comparison / diff tooling (beyond basic cascade view)
- Methodology templates library (deliberate — violates Principle 1)
- Non-construction methodology (this design is construction-domain-specific; don't generalise prematurely)
