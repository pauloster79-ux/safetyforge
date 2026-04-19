# WorkItem & WorkPackage UI — Design Plan

**Status:** Draft for review
**Author:** Claude + Paul
**Date:** 2026-04-17
**Scope:** Design the atomic UI surface where contractors build, track, and close out work — the WorkItem card, WorkPackage grouping, lifecycle view switching, and client-facing presentation. Applies across mobile and desktop, scales from solo (Jake) to commercial (Sarah). Delivers mockup specs, interaction specs, and a build sequence.
**Depends on:** [canonical-work-categories.md](canonical-work-categories.md) — for the category picker integration point. Methodology design is a companion doc running in parallel.
**Related:** [ESTIMATING_EXPERIENCE.md](../ESTIMATING_EXPERIENCE.md) (Jake + Sarah scenarios) | [estimating-intelligence.md](estimating-intelligence.md) (source cascade, Insight loop) | [preview/work-items.html](../preview/work-items.html) (mockups) | [specs/UI_RESTRUCTURE_SPEC.md](../specs/UI_RESTRUCTURE_SPEC.md) (navigation restructure)

---

## 1. The Problem

The WorkItem is the atomic unit of Kerf. Contractors will touch it every day, in every project, across the lifecycle — from conversational drafting through execution tracking to invoicing and variance reconciliation. The UI for WorkItem and WorkPackage is not incidental to the product; **it is the product** for most of the contractor's time in-app.

Three gaps exist today:

1. **[WorkTab.tsx](../../frontend/src/components/projects/WorkTab.tsx)** is a primitive read-only table — Description, Qty, Unit, Cost, State. No grouping, no expansion, no editing. The help text literally says "Use the chat to add work items."
2. **[ContractTab.tsx](../../frontend/src/components/projects/ContractTab.tsx)** has rich machinery — expandable rows, inline editing, full source provenance fields, Assumptions/Exclusions/Payment Milestones/Conditions/Warranty/Retention — but the UX hasn't been auditioned against competitive benchmarks and the WorkPackage grouping isn't rendered.
3. **No lifecycle view switching is implemented.** The Contract tab spec ([UI_RESTRUCTURE_SPEC.md](../specs/UI_RESTRUCTURE_SPEC.md)) specifies distinct Lead/Active/Closeout views, but the data-switching is partial.

Design direction exists in [preview/work-items.html](../preview/work-items.html) — card-as-atomic-unit, 5-state lifecycle, inline-editable values, emergent packages, phone-first with desktop builder, conversational drafting. That direction is correct. This doc synthesises it with competitive research and turns it into an actionable build.

---

## 2. Competitor Landscape (Key Findings)

Three research passes covered 28 competitors across AI-native estimating, traditional incumbents, and full-lifecycle platforms. Full per-competitor analysis is in the source agent outputs; this section distils the decisions Kerf must make.

### 2.1 What the category does well

| Pattern | Best example | Where it applies |
|---------|-------------|------------------|
| **Property → Item → Assembly + Variants** data model | Kreo | Clean atomic primitive for labour/material with multiple supplier options |
| **Recipe sidebar that expands into visible component rows** | Buildxact | Contractors see through the assembly — no black-box recipes |
| **Spine + columns lifecycle pattern** | Procore / ACC / Buildertrend | Same WorkItem, columns change per lifecycle stage (Estimated → Committed → Actual → Billed → Variance) |
| **Presentation Mode** — one-tap flip from internal to client view | ServiceTitan | Same data, different lens, zero extra authoring |
| **Line-item-level client approval** (per-line tick/X) | Houzz Pro | Explicit scope agreement; natural CO triggers |
| **Variance typing** (Builder Variance vs Customer Variance) | Buildertrend | Every overage attributed to cause, clean margin analysis |
| **Crew × production rate × duration** Labour primitive | B2W Estimate | Matches how crews actually work; enables retrievable ProductivityRates |
| **Passwordless magic-link client portal** | JobTread | Clients never manage credentials |
| **Good / Better / Best tiered proposals** | ServiceTitan | Three estimates bundled for contractor's upsell conversation |
| **Column flexibility** (show/hide, pin, reorder) | Sage / Procore | Commercial estimators demand this; it's muscle memory |

### 2.2 What the category does badly (Kerf's openings)

| Weakness | Prevalence | Kerf's differentiation |
|----------|-----------|------------------------|
| **No source provenance on numbers** | Universal | Our `rate_source_id` / `productivity_source_id` / `price_source_id` is already ahead of the entire category |
| **No AI-state visibility at line-item level** | Universal | Our Draft/Confirmed border treatment already designed |
| **Mobile is uniformly bad for pricing/estimating** | Procore, ACC, Sage, Accubid, McCormick, IntelliBid | Marco's 5:30 AM truck estimate is an open field |
| **Assemblies that "break confusingly"** (explicit G2 complaint re STACK) | Most | Make unit mismatches explainable + fixable in-place |
| **Dense 2002 grey Windows grids** | Sage, Accubid, McCormick, IntelliBid | Modern design language is table-stakes |
| **Modal-heavy editing** | Multiple | Inline edit or persistent side panel, never "click → dialog" |
| **Walled-garden assembly libraries behind category trees** | McCormick 25k, ConEst 500k, Accubid 9.5k | Natural-language search over assemblies |
| **Desktop-only estimating** | Procore, ACC, most traditional tools | Browser-first, phone-viable minimum |
| **Excel as the deliverable** | Togal, Beam AI, Bluebeam | Kerf's living estimate IS the artifact |

### 2.3 Entrenched conventions Kerf must respect

Ignoring these is a direct path to rejection by commercial estimators:

1. **The row is the atom on desktop.** Cards work for mobile and for drafts. The pricing estimate on desktop MUST offer a grid view with editable cells, sort, filter, group, column show/hide, and keyboard navigation.
2. **Assemblies expand into visible rows.** You cannot hide labour/material components inside an assembly card; estimators won't trust it.
3. **Columns are negotiable.** Sage exposes 100+. Expect contractors to want labour hrs, labour cost, material cost, equipment, subcontractor, markup, cost code, phase, alternate, etc.
4. **Cost codes / WBS / divisions are visible and groupable.** Our "WorkPackage" concept maps here — but the label is unfamiliar. Contractors call these "sections," "divisions," "phases," or "cost codes." Use their vocabulary in UI.
5. **Keyboard speed on desktop.** Tab/Enter/arrow navigation through cells, paste from Excel, bulk operations on columns.
6. **Pinned live total.** Estimate total updates as you edit — always visible, never scrolled out of view.
7. **Markup cascade.** Top-level overhead/margin that flows through and can be overridden per line.

---

## 3. Design Principles

Eight principles, each traceable to findings above.

1. **The card IS the work item.** On mobile and in chat, a WorkItem renders as a card with header, editable detail rows, and action bar. No separate "create form." The conversation extracts structured items; the card is the review surface. (Source: work-items.html existing design + universal competitor failure to make AI state visible)

2. **The grid IS the work item on desktop.** Sarah's pricing surface is a spreadsheet-feeling grid with editable cells, column flexibility, keyboard nav, paste-from-Excel. The card mode and the grid mode render the same data; contractors flip between them per task. (Source: Sage / Procore / B2W conventions)

3. **Every value is inline-editable.** Tap the value, edit it, commit on blur or Enter. No modal dialog to change a quantity. Dashed underline signals editability. (Source: work-items.html existing + universal competitor failure)

4. **Every number carries its source.** The card/row shows a source line — "Your avg across 14 jobs," "Graybar quote, 14 Mar," "RSMeans baseline flagged low confidence." Tap the source to see the evidence trail. (Source: universal gap; our existing provenance data model)

5. **Assemblies expand, never hide.** When the agent proposes an assembly or the estimator picks one, the component Labour and Item rows are visible and editable within the WorkItem card/grid. No black boxes. (Source: Buildxact + universal convention)

6. **Spine + columns for lifecycle switching.** The WorkItem is a stable spine. Columns and action bar change per project state: Estimating shows cost/margin/confirm, Active shows estimated/actual/% complete, Closeout shows invoiced/paid/variance. Same data, different lens. (Source: Procore / ACC / Buildertrend pattern)

7. **Packages emerge, never dominate.** Jake sees a flat list. Sarah sees collapsible packages with subtotals. The same data model. UI shows packages only when they exist. (Source: work-items.html existing + scale-appropriate complexity)

8. **The client view is the contractor view, filtered.** Presentation Mode (ServiceTitan) flips internal to client-facing in one tap. Same data, toggleable visibility. No separate proposal authoring. (Source: ServiceTitan + Houzz Pro + CoConstruct portal + JobTread magic link)

9. **Methodology is first-class on the WorkItem, not metadata.** Every WorkItem shows the construction method it's being built under — inherited from its WorkPackage, which inherits from the Project. The cascade is visible, editable at any level, and the reasoning (Insight chain) is tappable. Methodology is the layer that captures contractor judgment and compounds it across jobs. (Source: prior conversation + estimating-intelligence Principle 4 — patterns are learned, not authored)

---

## 4. The WorkItem Card (Mobile + Chat)

### 4.1 Anatomy

```
┌─ WorkItem Card ───────────────────────────────────────────┐
│ ⚡ Standard receptacle                      $396  [Draft] │  ← header: icon, title, computed cost, state badge
├───────────────────────────────────────────────────────────┤
│ Category    26 05 26  Grounding  ▼                        │  ← canonical category picker (from canonical plan)
│ Quantity    6 ea                                          │  ← editable
│ Material    $3.40/ea = $20.40                             │
│             ↳ City Electric Supply, 14 Mar · $0.89-$3.89  │  ← source line (muted, clickable)
│ Labour      2-hand crew × 0.25 hr/ea × 6 = 3.0 crew-hrs   │  ← crew × production × duration model
│             ↳ $65/hr loaded = $195                        │
│             ↳ Your avg across 14 jobs ±0.09, n=14         │  ← production source + confidence
│ Methodology In-wall conduit, finished walls  ▼            │  ← inherited from WorkPackage (see §10)
│ Total       $396.00                                       │  ← sum, pinned
├───────────────────────────────────────────────────────────┤
│ [✓ Confirm]  [Edit]  [✕ Remove]                           │  ← action bar (changes per state)
└───────────────────────────────────────────────────────────┘
```

### 4.2 States and visual treatment

| State | Visual | When |
|-------|--------|------|
| **Draft** | Yellow (machine `#F5B800`) 3px left border, "Draft" badge | Agent proposed, awaiting contractor review |
| **Estimated** | Green left border, "Estimated" badge | Confirmed by contractor, in the quote |
| **Scheduled** | Blue left border, dates + crew assignment visible | Post-award, pre-start |
| **In Progress** | Purple left border, shows estimated-vs-actual hours inline | Time entries logging |
| **Complete** | Muted (concrete-400) border, final actuals | Done |

Dashed underline on every editable value. Every source line is a tappable affordance to see provenance detail.

### 4.3 Inline edit patterns

- Tap a value → becomes an input, focus inside, current value selected
- Commit on blur, Enter, or Tab; Esc cancels
- Quantity/rate inputs accept fractions, unit-suffix-aware ("6 ea," "12 LF," "2.5 yd³")
- Labour rate edit shows three fields inline: crew size × rate/ea × $/hr
- Category edit opens the canonical picker (search-first, per canonical plan)
- Conversational alternative always available: "Change receptacles to 8" in chat updates the card

### 4.4 Mobile draft/confirm flow

From [work-items.html](../preview/work-items.html) mobile flow — validated by research:

1. Contractor narrates scope → agent extracts → cards appear in chat as Drafts (yellow border)
2. Per-card: `[✓ Confirm] [Edit] [✕]` buttons
3. Group action: `[✓ Confirm All X]` if multiple drafts
4. Confirmed cards flip to green border, stay in chat, accumulate in canvas
5. Contractor can always type a natural correction ("make receptacles 8 not 6") — card updates, shows diff ephemerally

### 4.5 Source provenance display

This is Kerf's single biggest differentiator. Research confirms no competitor shows this:

- Under each numeric line, a muted secondary row: "↳ [source reference], [timestamp if relevant], [confidence signal]"
- Tap the source line → expands to show:
  - Which node in the graph (ResourceRate / ProductivityRate / MaterialCatalogEntry / IndustryProductivityBaseline)
  - Evidence chain: "Derived from 14 completed panel upgrades, avg 6.2 hrs, σ 0.09, last job 12 Mar"
  - If an Insight applied: "+15% applied from 'Low ceiling renovations' Insight, created Aug 2025, confirmed 4x"
  - Buttons: [Accept] [Override] [See history]

---

## 5. The WorkItem Grid (Desktop)

### 5.1 Why the grid exists

Sarah is not building a 90-line commercial estimate on a stack of cards. She expects a spreadsheet — rows, columns, keyboard nav, paste from Excel, sort/filter/group. This is the entrenched convention.

The grid renders the same WorkItems as the card view. A contractor can flip modes per preference; mobile and chat always default to cards.

### 5.2 Layout

From [work-items.html Desktop Builder](../preview/work-items.html):

```
┌─ Chat sidebar (380px) ─────┬─ Canvas (fluid) ──────────────────────────────────────────┐
│ User: Reception: 6 recep...│ 4th Street Medical · 21 items · 5 packages    [Export]    │
│ Kerf: Added 6 items →      │                                          [+ Add] [Proposal]│
│ ...                        │ ┌─ Description ──── Qty · Unit · Mat$ · Lab hr · $/hr · $─┤
│                            │ │ 📦 Reception (expanded)            [Confirmed]          │
│                            │ │   Standard receptacle    8  ea   $3.40   3.04   $65  $225│
│                            │ │   Dedicated circuit      2  ea   $12.00  1.60   $65  $128│
│                            │ │   Floor box assembly     1  ea   $85.00  1.50   $65  $183│
│                            │ │   LED troffer 2×4        8  ea   $142    4.00   $65  $1,396│
│                            │ │   ... (all items visible, expanded)                     │
│                            │ │   ─── Reception Subtotal                       $3,567 ──│
│                            │ │ 📦 Exam Rooms ×10 (expanded)       [Confirmed]          │
│                            │ │   ...                                                   │
│                            │ │ 📦 Hallways & Common (collapsed — 5 items)    $12,340  │
│                            │ │                                                         │
│                            │ │ Direct Cost                                    $74,807  │
│                            │ │ Labour Adj (+12%) + OH (12%) + Profit (10%)    $73,393  │
│                            │ │ ─────────────────────────────────────────────────────── │
│                            │ │ BID TOTAL (pinned, yellow)                   $148,200   │
│                            │ └─────────────────────────────────────────────────────────┘
└────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

### 5.3 Grid features

Borrowed from Sage / Procore / B2W + modernised:

- **Column show/hide, pin, reorder.** Default set (Description, Qty, Unit, Mat $/ea, Lab hrs, $/hr, Total) + optional (Cost code, Category, Alt, Phase, Labour total, Material total, Variance, Notes, Created by)
- **Sort by any column.** Click header; shift-click for multi-sort
- **Group by:** Package (default), Category, Phase (once wired), Trade, State
- **Keyboard:** Tab/Shift-Tab across cells, Enter to commit and move down, arrows to navigate, Cmd/Ctrl-C/V for paste from Excel
- **Row expansion:** Click a row → expands in-place to show Labour and Item children (like ContractTab already does). Expand-all / collapse-all button in header
- **Bulk operations:** Select rows with checkbox, bulk change state / delete / apply markup
- **Right-click:** context menu for row-level actions (Confirm, Duplicate, Convert to Alternate, Link to package)

### 5.4 Pinned total card

Bottom-right of canvas, machine-yellow accent (from work-items.html):

```
┌─ BID TOTAL ───────────────────┐
│ 21 items in 5 packages        │
│ Direct cost         $74,807   │
│ Labour adj (+12%)   +$8,977   │
│ Overhead (12%)     +$10,054   │
│ Profit (10%)        +$9,384   │
│ ─────────────────────────────│
│ BID TOTAL         $148,200   │
│ Margin              14.2%    │
│                              │
│ [Generate Proposal]          │
│ [Adjust Margin]              │
└──────────────────────────────┘
```

Updates live on every edit. Never scrolls out of view (sticky bottom or docked right).

---

## 6. WorkPackage Grouping

### 6.1 When packages appear

- **0 packages** (Jake, small jobs): flat list of WorkItems, no grouping shown. No "Unassigned" bucket. Just items.
- **1+ packages**: each package is a collapsible group header with item count and subtotal. WorkItems without a package go into an "Other items" tail bucket (shown only if it has content).
- **Naturally emergent**: when the contractor says "Reception: 6 receptacles..." the agent creates the package and assigns the items. No manual "create package" step on first use.

### 6.2 Package header

```
▾ Reception                          6 items    $3,567  [Confirmed]
   [expanded WorkItem rows ...]
   ─── Reception Subtotal                       $3,567

▸ Exam Rooms ×10                    70 items   $30,980  [Confirmed]
   (collapsed — click to expand)

▸ Hallways & Common                  5 items   $12,340  [Confirmed]

▾ Fire Alarm                         2 items    $8,420  [Draft]      ← yellow border
   [expanded rows, still drafts]
```

- Collapsed by default for all but the currently active package during authoring
- Subtotal updates live
- State aggregates: if any WorkItem in the package is Draft, package shows Draft; if all Estimated, package shows Estimated
- Package can itself be renamed, deleted, or split

### 6.3 Package operations

- Drag-handle to reorder packages
- Right-click package → Rename / Duplicate (creates N copies for Sarah's "Exam Rooms ×10" pattern) / Delete / Merge with...
- Multi-select WorkItems → "Move to Package" action
- Package has its own notes field

---

## 7. Lifecycle View Switching — Spine + Columns

This is the most important architectural pattern borrowed from Procore / ACC / Buildertrend, adapted for Kerf.

### 7.1 The concept

The **WorkItem is a stable spine**. Its position, description, quantity, and category never change. What changes per lifecycle stage is which columns are shown, which action bar buttons appear, and what the pinned summary says.

Three lifecycle modes, triggered by `project.state`:

### 7.2 Lead / Quoting view

**Purpose:** Build the estimate. Agree margin. Generate proposal.

**Columns:**
- Description / Qty / Unit
- Material total, Labour total, Direct cost
- Margin % (per line, optional)
- Sell price

**Action bar:** [Confirm] / [Edit] / [Remove] per item. [+ Add Item] at top. [Generate Proposal] in header.

**Pinned total:** Direct / Markups / Bid Total / Margin % (as shown in §5.4)

**State badges visible:** Draft / Estimated

### 7.3 Active / In Progress view

**Purpose:** Track execution. Flag variance. Catch scope creep.

**Columns:**
- Description / Qty / Unit
- Estimated hours · Actual hours · % complete
- Estimated cost · Actual cost · **Forecast at complete**
- Variance $ · Variance %
- **Variance type** badge: Builder / Customer / None (borrowed from Buildertrend)

**Action bar:** [Log Time] / [Add Material] / [Report Delay] / [Request Variation]

**Pinned total:** Revised contract value · Spent · Forecast at complete · Forecast margin %

**State badges visible:** Scheduled / In Progress / Complete

**Row colour accents:**
- Line tracking to budget: default
- Line 10-25% over: yellow tint
- Line >25% over: red tint, Forecast column bold

### 7.4 Closeout / Invoicing view

**Purpose:** Bill what was done. Reconcile variance. Close out.

**Columns:**
- Description / Qty / Unit
- Contract value · Billed to date · Outstanding
- Actual cost · Variance
- Invoice number(s) the line has been billed on

**Action bar:** [Generate Invoice] / [Mark Complete] / [Dispute]

**Pinned total:** Total contract / Billed / Collected / Outstanding · Overall margin % (actual vs planned)

**State badges visible:** Complete / Invoiced

### 7.5 The switch mechanic

- View mode is driven by `project.state` by default
- A contractor can manually flip views via a segmented control at the top: `[Quote] [Active] [Closeout]`
- Switching views preserves filter/sort/group selections
- Canvas animates column changes (250ms ease) so the spine feels stable and the lens shifts

### 7.6 The Variance Type model (Builder vs Customer)

Borrowed from Buildertrend. Every variance (cost delta from estimate) gets tagged:

- **Customer Variance** — client-driven scope change → becomes a Variation (change order) candidate, invoiceable
- **Builder Variance** — internal mis-estimate or execution issue → reduces margin, not billable
- **Weather Variance** — (optional third type for civil/heavy) — EOT claim candidate

The tag drives downstream accounting: Customer Variances accumulate into draftable change orders; Builder Variances surface in post-mortem analytics.

---

## 8. Persona Scaling Rules

The same WorkItem data model, progressively denser UI per persona.

| Persona | Default mode | Packages? | Grid view? | Column density | Source lines |
|---------|--------------|-----------|------------|----------------|--------------|
| **Jake** (solo electrician) | Card / mobile | No | No (card list on desktop) | Minimal — description, total, source | One-line source |
| **Marco** (small-mid commercial crew, bilingual) | Card / mobile + grid on desktop | Optional, emergent when projects get complex | Yes on desktop | Medium — description, qty, lab hrs, total, source | One-line source + confidence signal |
| **Sarah** (45-person commercial contractor) | Grid-first on desktop, card on phone | Yes, typical | Yes primary | Full — all columns configurable | Full source chain, Insight attribution |

Rules:
- **Auto-detect persona from usage, not a toggle.** Project count, estimate complexity, device mix drive defaults. Contractor can manually promote/demote.
- **Progressive disclosure of features.** Jake never sees a column-show/hide menu until he needs it. Sarah sees it immediately.
- **Bilingual (ES/EN) UI is Marco-critical.** Not a translated-later afterthought. Card rows, action bars, chat all i18n-aware from day one.

---

## 9. Category Picker Integration

From [canonical-work-categories.md](canonical-work-categories.md), every WorkItem gets categorised. Picker design:

- **In the card:** Category row near top, shows current `code + name`, dropdown indicator `▼`
- **On tap/click:** Opens search-first picker modal (bottom sheet on mobile, dropdown on desktop)
- **Search-first UX:** Type-ahead over canonical name + code + synonyms. "panel upgrade" → surfaces MasterFormat 26 24 16 Panelboards as top match
- **Tree browse as fallback:** If search doesn't produce a match, "Browse tree" button opens hierarchical navigation
- **Recent categories row:** top of picker shows last 5-10 categories this contractor used, for one-tap selection
- **Jurisdiction-aware:** contractor's jurisdiction determines which canonical tree is shown (MasterFormat for US/CA, NRM 2 for UK/IE, NATSPEC for AU/NZ)
- **Aliases applied:** if contractor has aliased `26 24 16` to "Main Panels," it displays as "Main Panels" in this picker and everywhere else

No category = cannot save WorkItem. Enforced at the service layer per canonical plan.

---

## 10. Methodology Integration

The Methodology node captures construction-method decisions — how this job is being built, distinct from what kind of work it is (which is the WorkCategory). See the companion design doc `methodology.md` (authored in parallel with Phase 1 of this plan per canonical-categories Phase 0b) for the full data model and conversational authoring flow. This section defines the UI surface that integrates methodology as a first-class citizen from Phase 2 of the build.

### 10.1 What the contractor sees

Methodology is **visible on every WorkItem card and grid row** — not hidden behind an advanced menu. It's expressed as a short natural-language summary with the underlying structured `approach` map tappable for detail.

In the card:

```
Methodology   In-wall conduit, finished walls, Schluter waterproofing   ▼
              ↳ inherited from Reception package · 3 levels active
```

In the grid: a Methodology column (default visible) showing the same summary; cell expansion reveals the approach map.

### 10.2 The cascade

Methodology decisions cascade Project → WorkPackage → WorkItem. Each level can set methodology; child levels inherit and can override specific keys.

**Cascade visualisation** (from tapping the Methodology row/cell):

```
Project Methodology
┌───────────────────────────────────────────────────────┐
│ Residential renovation · Retain fixture layout · MEP   │
│ integration with existing · Schluter system preferred  │
│ Set by Marco · 14 Mar · cloned from "Johnson Kitchen" │
└───────────────────────────────────────────────────────┘
         ↓ inherited by
WorkPackage: Reception
┌───────────────────────────────────────────────────────┐
│ + Conduit in finished walls (not ceiling rough-in)    │
│ + Drop ceiling access above: no                        │
│ Overrides: none                                        │
└───────────────────────────────────────────────────────┘
         ↓ inherited by
WorkItem: Standard receptacle ×6
┌───────────────────────────────────────────────────────┐
│ No item-level overrides                                │
│ Labour productivity: baseline × 1.15                  │
│   ↳ from Insight "Finished-wall conduit, renovation"  │
│   ↳ confidence 0.85 · 12 validations                  │
└───────────────────────────────────────────────────────┘
```

### 10.3 Conversational authoring

First job of a kind (no prior similar project): the agent asks the questions needed to flush out methodology. "Is this a joist floor or slab? Existing waterproofing condition? Drain type preference?" Answers become the `approach` map on the Project methodology.

Subsequent similar job: the agent retrieves the nearest past matching methodology and shows it as a proposal. "Last time we did a joist-floor shower you used Schluter Kerdi with linear drain — still right?" Contractor confirms or tweaks; differences are recorded.

Key/value edits in dialogue:
- "I don't use that membrane on joist floors anymore, switch to sheet membrane" → creates or updates an `approach.waterproofing` value + an Insight with `applies_when: {substrate: "joist_floor"}`
- "Use standard everywhere this project" → inherits to all packages/items

### 10.4 UI interactions

- **Tap the Methodology row** → expand to show approach map and cascade
- **Tap any approach key** → edit inline, with autocomplete from past values on similar projects
- **Override button** per level → takes on a new approach, breaks inheritance for that key
- **"Apply to all" button** in Project methodology → cascades new values to all children
- **Insight attribution** — every productivity/price adjustment linked to an Insight shows the Insight chip; tap to see the evidence chain

### 10.5 Persona scaling

| Persona | Methodology surface |
|---------|---------------------|
| **Jake** (solo, simple jobs) | Methodology row hidden by default; appears only when agent detects a decision worth capturing. Most Jake jobs don't need explicit methodology beyond `approach.scope: "straightforward"` |
| **Marco** (bilingual, mid-commercial) | Methodology row visible on WorkPackage level. Item-level only when overrides exist. The cascade is a tappable affordance, not forced. |
| **Sarah** (commercial, technical spec) | Full methodology visible at Project, Package, Item. Grid has Methodology column on by default. Cascade is actively used to drive productivity adjustments. |

### 10.6 Integration points in the data model

- `(Project)-[:USES_METHODOLOGY]->(Methodology {scope_level: "project"})`
- `(WorkPackage)-[:USES_METHODOLOGY]->(Methodology {scope_level: "package"})`
- `(WorkItem)-[:USES_METHODOLOGY]->(Methodology {scope_level: "item"})`
- `(Methodology)-[:CHILD_OF]->(Methodology)` for cascade
- `(Methodology)-[:APPLIES_TO_CATEGORY]->(WorkCategory:Canonical)` — methodology is scoped to a category
- `(Insight)-[:APPLIES_TO_METHODOLOGY_WITH {approach: {...}}]->(Methodology)` — Insights match on category + methodology keys

### 10.7 Built, not stubbed

Methodology UI components ship in Phase 2 alongside card and grid rendering. The companion methodology design doc (landing in parallel with Phase 1) provides the data-model and authoring-dialogue specs that this UI connects to. **Methodology is not deferred to a post-v1 polish pass** — it's a load-bearing part of the conversational assembly vision and has to land with the core surface.

---

## 11. Client-Facing View (Presentation Mode)

Adapted from ServiceTitan + Houzz Pro + CoConstruct + JobTread.

### 11.1 One-tap flip

From the desktop canvas, a `[Client View]` toggle in the header flips the surface to a clean, customer-ready presentation of the same data. Per-field visibility toggles let the contractor show/hide:

- Item-level cost detail (cost per line vs. total only)
- Labour hours (often hidden for fixed-price residential)
- Source provenance (almost always hidden from client)
- Assumptions / Exclusions (always shown)
- Payment milestones (always shown)
- Variations & COs (always shown once active)

### 11.2 Client portal

Client gets a magic-link URL (no password, per JobTread). Lands on a branded proposal page:

- Project name, contractor logo, proposal date, valid-until
- Summary: Bid total, payment terms, timeline
- Scope: WorkPackages as expandable sections, WorkItems listed per package
- **Line-item approval** (from Houzz Pro): per-item `[✓]` or `[✕]` — client ticks the ones they accept, declines others
- Sign-off: single-button e-signature → contractor gets notification → project state advances to Quoted
- During Active: same URL shows progress %, current invoice status, change orders needing approval
- During Closeout: outstanding balance, payment history, final documents

### 11.3 Change orders flow

When Variance is tagged Customer during Active view, it auto-creates a Draft Change Order. Client gets a notification on their portal → reviews the new line items → approves or negotiates → signed → line item flips to Approved Variance and joins the contract. (Borrowed from CoConstruct selection-to-CO auto-conversion.)

---

## 12. Visual Language

Already locked by existing Kerf design — documenting for the build session.

| Token | Value |
|-------|-------|
| Primary accent | Machine yellow `#F5B800` (darker `#D9A200`, brighter `#FFCA18`) |
| Backgrounds | Concrete palette — `#f4f5f3` (bg), `#ffffff` (card), `#0d0e0c` (dark) |
| Text | `#0d0e0c` (primary), `#545951` (muted), `#71766b` (extra muted) |
| Borders | `#e6e8e3` (default), `#d4d7d0` (stronger) |
| State colours | Pass `#2d8a4e`, Fail `#c53030`, Warn `#b8860b`, Info `#2980b9`, Progress `#8e44ad` |
| Border radius | 3px (consistent, sharp) |
| Font (display/UI) | IBM Plex Sans — 400, 500, 600, 700 |
| Font (numbers, codes) | IBM Plex Mono — 400, 500, 600 |
| Card state border | 3px left border |
| Dense typography | 0.78rem (cards), 0.82rem (body), 0.95rem (headings), monospace for numbers |

**Deliberate stylistic choices:**
- Yellow is for in-progress / attention / brand accent — not status "warn"
- Small font sizes (by modern SaaS standards) — density is respected; dead space is not
- Mono for numbers everywhere — numeric alignment matters in estimates
- No drop shadows or gradients — flat, industrial, machine-room aesthetic
- 3px border-left for state is ubiquitous and load-bearing

---

## 13. Interaction Specs

### 13.1 Card edit flow

1. Tap a value with dashed underline → value becomes an input (text or number as appropriate)
2. Value pre-selected; typing replaces it
3. Tab moves to next editable field in card; Shift-Tab to previous
4. Enter or blur commits; Escape reverts
5. Card recalculates total live as edited
6. On commit, row flashes machine-yellow briefly (150ms) then returns to normal

### 13.2 Grid edit flow

Same as spreadsheet:
- Click cell to select; click again or Enter to enter edit mode
- Arrow keys to navigate; Tab/Shift-Tab horizontal; Enter/Shift-Enter vertical
- Paste from Excel into selected range (Cmd/Ctrl-V)
- Cmd/Ctrl-Z undo / Cmd/Ctrl-Shift-Z redo
- Type-ahead on category cell opens picker inline

### 13.3 Source line interaction

- Muted text below each numeric value
- Hover (desktop) / long-press (mobile) → tooltip with full source
- Click/tap → opens SourcesPanel (already exists in ContractTab) with evidence chain

### 13.4 Assembly expansion

When the agent creates or the contractor picks an assembly:

1. A new WorkItem appears in card/row
2. Automatically expanded to show all component Labour + Item rows
3. "This is an assembly" chip in the card header
4. Contractor can edit any component row, or collapse to see the roll-up, or break the assembly link (turns components into loose items)
5. If a component's unit doesn't match the takeoff measurement, a warning row inline with `[Fix unit mismatch]` button — addresses the STACK "assemblies break confusingly" complaint

### 13.5 Chat ↔ Canvas sync

- Confirming a card in chat reflects instantly in canvas grid (same React Query invalidation)
- Editing a row in canvas reflects instantly in chat (the corresponding card updates)
- Natural language corrections in chat ("change receptacles to 8") update both surfaces

### 13.6 Keyboard shortcuts (desktop)

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl-K` | Command palette (add item, change view, generate proposal, etc.) |
| `Cmd/Ctrl-Enter` | Confirm selected Drafts |
| `Cmd/Ctrl-Shift-A` | Add item (opens chat focused with "Add ") |
| `G` then `Q` | Go to Quote view |
| `G` then `A` | Go to Active view |
| `G` then `C` | Go to Closeout view |
| `/` | Focus search in picker |
| `Escape` | Close picker / cancel edit |

---

## 14. Open Questions

Resolve during Phase 1 (design pass) before Phase 2 build starts.

1. **Good / Better / Best tiered proposals.** Service trade pattern (ServiceTitan). Does Kerf support `Estimate` objects with three alternate tiers, or do we model tiers as three `Alternate` WorkItems within one Estimate? Affects Estimate schema.
2. **Crew × production × duration Labour model.** Borrow from B2W — upgrade Labour node to carry `crew_size`, `production_rate_per_unit`, and compute hours? Or keep `hours` as stored and treat crew/production as source metadata? Affects Labour schema.
3. **Variance typing.** Add `variance_type` enum (customer / builder / weather) to WorkItem execution records or to a separate Variance node? Affects job-cost data model.
4. **Kreo-style Variants.** Should an Item node support multiple price variants (Graybar $0.89, Home Depot $1.02, Lowes $0.95)? Or are variants handled via multiple MaterialCatalogEntry nodes? The latter is probably right.
5. **Grid view implementation priority.** Do we ship card-only first (mobile + chat + simple desktop list), then grid as Phase 3? Or grid is in Phase 2? Affects sequence for Sarah's usability.
6. **Client portal — separate build or part of this plan?** The magic-link client view is a significant UI surface; could slip from this plan if scope gets tight.
7. **Presentation Mode — what toggles exactly?** Per-field visibility configurability is powerful but complex. Is there a sensible default set, or fully configurable?
8. **Alternate / VE option handling in the UI.** `is_alternate` exists in the model. How does the card / grid distinguish an alternate from a base item? A visual toggle? A side-by-side tier display?

---

## 15. Implementation Phases

### Phase 1 — Design pass (1–2 weeks)

**Goal:** Final mockups and decisions locked before build.

Tasks:
- Review this doc with Paul; resolve open questions in §14
- Update [work-items.html](../preview/work-items.html) with:
  - Active / In Progress view (tracking columns, variance typing)
  - Closeout view (invoicing columns, variance reconciliation)
  - Desktop grid view (full column set, lifecycle switch)
  - Client Presentation Mode
  - Category picker flow (search-first, tree fallback, aliases)
  - **Methodology surface**: row in card, cascade visualisation modal, approach-map editor, Insight chip with evidence chain (not a placeholder — fully mocked in line with §10)
- Produce a Figma source for the above (or upgrade work-items.html to the sole source of truth)
- Write interaction specs for keyboard nav, assembly expansion, source line interaction
- Audit which existing `ContractTab.tsx` machinery can be reused; what needs refactor

**Deliverable:** Updated work-items.html + design decisions doc resolving §14 + audit note on existing code.

**Gate before Phase 2:** Paul has clicked through mockups and confirmed each persona's experience (Jake / Marco / Sarah) feels right.

### Phase 2 — Card + Grid rendering + Methodology (3–4 weeks)

**Goal:** The primary atomic surface works for Estimating (Lead / Quoting) state, with methodology as a first-class citizen.

- Refactor WorkTab.tsx → retire or repurpose (decision from Phase 1)
- Promote ContractTab.tsx to the primary lifecycle surface
- Implement WorkPackage grouping visual (expandable headers, subtotals, state aggregation)
- Implement pinned Bid Total card with live recalc
- Add grid view toggle (desktop) — leverage existing ContractTab row machinery
- Implement card states with correct border treatment per §4.2
- Implement source line display under every numeric value
- Implement category picker integration point (UI chrome; picker itself ships with canonical plan)
- **Implement methodology row + cascade visualisation (§10)** — Project / WorkPackage / WorkItem surfaces, inheritance display, approach-map edit, Insight attribution chips
- Mobile pass: card-first layout, touch-optimised, bottom action sheet

**Deliverable:** Estimating surface feels like the mockup across mobile and desktop. Jake's flat list, Marco's mid-density, Sarah's grid all work. Methodology cascade renders end-to-end when the backend has methodology data.

### Phase 3 — Lifecycle view switching (1–2 weeks)

**Goal:** Active and Closeout views work, driven by project state.

- Implement spine + columns pattern: view mode driver, column set per mode, smooth animation
- Active view: actual hours / cost tracking columns; Variance typing UI; row colour accents for over-budget
- Closeout view: invoice association columns; billed/outstanding; variance reconciliation
- Segmented control for manual view override

**Deliverable:** Same data, three lenses, switchable per project state.

### Phase 4 — Assembly expansion + Labour model + Insight retrieval (1–2 weeks)

**Goal:** Assemblies are transparent; Labour matches how crews actually work; Insights that drive methodology adjustments are actively surfaced.

- Implement assembly indicator chip in card
- Visible component expansion with edit inline
- Unit mismatch detection + inline fix UI
- Labour node UI upgrade: crew × production × duration display and edit (if §14.2 resolves in favour)
- Insight retrieval in methodology surface: when the agent applies an Insight-driven productivity adjustment, show the chip with confidence, validation count, evidence chain; allow contractor to confirm/correct/invalidate inline

**Deliverable:** Assembly experience beats Buildxact; Labour matches B2W model; methodology Insights drive visible adjustments with contractor-correction flow.

### Phase 5 — Client Presentation Mode (1–2 weeks)

**Goal:** One-tap flip to client-facing; magic-link portal.

- `[Client View]` toggle on canvas header
- Per-field visibility config
- Passwordless magic-link portal
- Line-item approval (tick/X per line, per Houzz Pro)
- E-signature flow
- Notification plumbing

**Deliverable:** Contractor can send a proposal to a client with a link; client approves or requests changes; no paper, no PDF.

### Phase 6 — Variance flow + Change Orders (1 week)

**Goal:** Customer Variance auto-drafts Change Orders; close the scope-creep loop.

- Detect Customer-tagged variances during Active view
- Draft CO auto-generated with the delta line items
- Client portal surface for CO review + approval
- Once approved, line items rejoin the contract at the new values

**Deliverable:** The selection-overage-to-CO pattern works end-to-end.

### Phase 7 — Polish + persona auto-detect (1 week)

- Bilingual (ES/EN) UI pass
- Persona auto-detect driver (project count, device mix, complexity)
- Keyboard shortcut polish on desktop
- Touch gesture polish on mobile (swipe to confirm/dismiss drafts, long-press for context)
- Animation pass (state transitions, view switches)

**Deliverable:** Feels done. Jake, Marco, Sarah each have been exploratory-tested per the [Kerf CLAUDE.md](../../CLAUDE.md) persona methodology.

### Total rough effort

| Phase | Weeks |
|-------|------:|
| 1 — Design pass | 1–2 |
| 2 — Card + Grid rendering | 2–3 |
| 3 — Lifecycle switching | 1–2 |
| 4 — Assembly + Labour model | 1 |
| 5 — Client Presentation | 1–2 |
| 6 — Variance + CO flow | 1 |
| 7 — Polish | 1 |
| **Total** | **8–12 weeks** |

Some phases parallelise with the canonical-work-categories build (the category picker integration). Methodology lands after Phase 4.

---

## 16. Deliverables per Phase

| Deliverable | Phase |
|-------------|-------|
| Updated `work-items.html` with Active/Closeout/Grid/Presentation Mode | 1 |
| Design decisions doc resolving §14 | 1 |
| Reusable WorkItemCard component (card mode) | 2 |
| WorkItemGrid component (desktop) | 2 |
| WorkPackageGroup component (collapsible) | 2 |
| PinnedTotal component (live recalc) | 2 |
| SourceLine component + expanded SourcesPanel | 2 |
| View-mode switcher (spine + columns) | 3 |
| Variance typing UI | 3 |
| AssemblyExpansion component | 4 |
| Labour crew/production/duration editor | 4 |
| ClientPresentationView | 5 |
| Magic-link portal + line-item approval | 5 |
| Change Order auto-draft flow | 6 |
| Persona detection heuristics | 7 |
| ES/EN i18n coverage | 7 |

---

## 17. Risks

| Risk | Mitigation |
|------|-----------|
| Design scope creep — grid + card + lifecycle + client portal is a lot | Phased build; each phase ships something usable on its own |
| Keyboard nav parity with Excel is hard to nail | Borrow from `react-data-grid` or `tanstack/react-table` rather than building from scratch |
| Persona auto-detect misclassifies | Explicit override always available in settings; sensible defaults first |
| Client portal adds auth/sharing complexity | Magic-link passwordless pattern proven (JobTread, Jobber); well-established |
| Bilingual UI adds translation ops overhead | Start with ES/EN only; established contractor-facing strings; machine-translate-then-review |
| Visual polish doesn't hold across all states | Design review at end of each phase; Paul persona-tests before merge |
| Variance typing is model change | Resolve in §14; if model changes, fold into canonical categories schema update |

---

## 18. Out of Scope (Deliberate)

- Takeoff on drawings (PlanSwift/Bluebeam pattern) — separate future plan
- BIM model import — Wave 2+
- Good/Better/Best tiered proposals — resolve in §14 if in scope
- Estimating from voice while walking the site (mobile pipeline feature — in [estimating-intelligence.md](estimating-intelligence.md) §5)
- Multi-jurisdiction proposals in one project
- Drawing annotation on photos
- Kreo-style Variants on Items — resolve in §14

---

## 19. Success Criteria

The plan is complete when:

1. Jake creates 4 WorkItems by saying one sentence to Kerf on his phone; cards appear as Drafts; he confirms all with one tap; the estimate total is live; he clicks `[Send to Client]` and the client gets a magic link — under 60 seconds end-to-end.
2. Marco walks his Phoenix slab job on his phone at 5:30 AM, narrates items into the agent, corrects a few labour rates inline, generates a proposal for the homeowner in under 5 minutes. Works bilingual ES/EN.
3. Sarah loads her 4th Street Medical estimate on desktop, sees a grid of ~90 items across 5 packages, sorts by package, reviews source provenance on one row, flips to Client View to preview what Peterson GC will see, sends. Her keyboard muscle memory from Sage carries over.
4. A project moves from Lead → Active → Closeout; the Contract tab automatically shows the appropriate columns for each phase; same WorkItems throughout, different lens.
5. A Customer Variance during Active auto-generates a draft Change Order; client approves on their portal with a tap; scope is reconciled; invoices update.
6. A WorkItem with no source citations on labour or materials cannot be saved — the provenance cascade is visibly enforced.
7. Methodology cascades visibly from Project to WorkPackage to WorkItem; a contractor can correct a methodology decision in conversation ("switch to Schluter on joist floors") and see the change reflected across all affected items plus a new Insight attribution chip within seconds.
8. The design feels like one coherent product across mobile and desktop; no "shrunk desktop grid" on mobile, no "simplified mobile card" on desktop — each is native to its surface.
9. Click-through of the mockups feels indistinguishable from a final product to a construction industry peer reviewing it cold.
