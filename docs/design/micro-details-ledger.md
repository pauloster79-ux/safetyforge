# Micro-Details Ledger

**Status:** Living document. Extract of visual and interaction details from the Site Board previews that are easy to lose during implementation.
**Date:** 2026-04-19
**Source mockups:**
- `docs/preview/project-screen-lifecycle.html` (six full state screens)
- `docs/preview/project-screen-mockups.html` (structural A/B/C options)
- `docs/preview/quoting-detail-mockups.html` (six drill-down screens)
- `quoting-prototype/src/scenes/LifecycleFlow.tsx` + `QuotingDetailFlow.tsx`
- `quoting-prototype/src/components/ProjectFrame.tsx` + `dark-styles.ts`

**Purpose:** Things that get re-interpreted or forgotten when a ticket says *"build the Project header"* and the developer doesn't have the preview in a second window. Each entry is a fidelity requirement, not a suggestion.

**How to use:** Implementers read this before a PR. Reviewers open the preview alongside the real app and check against this list. If a detail here isn't on the screen, it's a bug.

**How to extend:** Anything you notice during design review that would otherwise vanish → add it here. Grows. Never shrinks except by explicit decision.

---

## 1. Layout Shell

### 1.1 Icon rail (left, 48px wide)
- **Width: exactly 48px** — narrower feels cramped, wider eats content.
- **Background: `--ink-1` (#141511)** — one step lighter than page ground. Creates a subtle rail-vs-canvas split.
- **Right border: 1px hairline** — matches `--hairline` (`rgba(255,255,255,0.06)`). Not a harsh line.
- **Logo tile at top: 28×28px, machine yellow background, white "K" glyph.** 10px margin below before the first rail button starts.
- **Rail buttons: 32×32px, 6px gap between.** Active button has `--ink-3` background + machine-yellow icon stroke. Inactive is `--fg-dim` stroke on transparent.
- **No labels on desktop** — icons only. Label appears as tooltip on hover.
- **On mobile:** rail becomes a bottom nav (not a left rail). 4 visible + overflow sheet.

### 1.2 Agent panel (chat + voice)
- **Desktop width: 300–320px.** Below that feels cramped for voice messages.
- **Background: `--ink-1`.** Same as icon rail — reads as one continuous left-side chrome.
- **Three regions stacked:** header (12×14 padding) · body (flex-1, overflow-y-auto) · input (10×14 padding).
- **Header shows:** `◎ Conversation` kicker (mono, 10px, uppercase, muted colour) on the left + context label on the right (e.g. `Contract · Maple Ridge`). The context label hints *what the current conversation is scoped to* — it changes as Jake navigates, not per session.
- **Input bar:** text field + `◉ HOLD` button + `SEND` button. The `◉` glyph is a filled circle — voice affordance. `HOLD` is the secondary (ink-3 bg); `SEND` is the primary (machine-yellow bg).
- **On mobile:** agent panel is a floating action button (bottom-right). Tapping expands to fullscreen chat. Voice-hold engages on press-and-hold the FAB.

### 1.3 Project canvas (right of agent panel)
- **Background: `--ink-0` (#0d0e0c)** — the page ground. Contrasts subtly with `--ink-1` agent panel.
- **Header + tab bar are fixed; canvas body scrolls underneath.** Agent panel and icon rail do not scroll with the canvas.
- **Canvas body padding: 22px on all sides.**

---

## 2. Top Header (Project-identity bar)

- **Height ≈ 54px** (14px padding top/bottom + content).
- **Background: `--ink-2` (#191b17)** — slightly lifted from the canvas body beneath.
- **Bottom border: 1px hairline.**
- **Logo tile: 22×22px, machine yellow, white "K"** — same treatment as icon-rail logo but smaller.
- **Project title: 15px semibold** — prominent but not a display heading. Left of the project code.
- **Project code (e.g. `MRP-2024-118`):** mono, 11px, 0.06em letter-spacing, machine-yellow text on `--machine-wash` background, 2×6px padding, 3px border-radius. Feels like a stamped part number.
- **Dot separators (`·`) between header elements:** mono, 11px, `--fg-dim` colour.
- **Client name:** mono, 11px uppercase, `--fg-muted`. Not a headline — it's metadata.
- **State chip:** full-strength per-state styling (see §4). Sits right of the metadata.
- **Overlay chips:** directly right of state chip. See §5.
- **Right cluster: total + CTA.** Total has a 2-line structure — label (mono kicker, 10px muted) above value (mono, 16px machine-yellow, right-aligned). CTA button on the right of that.
- **CTA:** 10×16px padding, machine-yellow bg, ink-0 text, 11px uppercase mono 0.06em tracking, semibold. If alt variant (secondary action), bg is `--ink-3` with `--fg` text.

---

## 3. Tab Bar

- **Background: `--ink-1`** — same family as agent panel.
- **Horizontal padding: 22px** (matches canvas body).
- **Bottom border: 1px hairline.**
- **Tab padding: 12px top, 14px horizontal, 11px bottom.** The bottom is 1px less to leave room for the active-state underline without shifting content.
- **Tab typography: mono, 11px, 0.06em letter-spacing, uppercase, 500 weight.** Not headline-weight.
- **Active tab:**
  - Text color → `--machine`.
  - Background → `--ink-0` (canvas colour — reads as cut-out into the content below).
  - Bottom border → 2px machine-yellow.
- **Inactive tab:** text `--fg-muted`, no background, transparent 2px border.
- **Disabled tab:** text `--fg-dim`, opacity 0.4. Not clickable. Used when the state doesn't have that data yet (e.g. `Variations` is disabled in `LEAD`).
- **Count badges** (e.g. `7`, `1`): small inline pill at 10px mono, `--ink-3` bg on inactive tabs, `--machine-wash` bg on active. Keep count compact — `7`, `12`, `87` — never `7 items`.
- **Do not add icons inside tabs** — the tab name starts with its glyph already (`◉`, `⚒`, `⬒`, `◎`, `$`, `▤`, `⚘`, `⚐`). The glyph IS the icon.

---

## 4. State Chips (per lifecycle state)

State chips carry semantic colour weight — the state is readable at a glance from the chip alone.

| State | Background | Text | Border | Semantic |
|---|---|---|---|---|
| `LEAD` | `--ink-3` | `--fg-muted` | hairline | Neutral; barely a project yet |
| `QUOTED` | `--machine` (solid) | `--ink-0` | `--machine` | Loud — a quote is a commitment; it stands out |
| `ACCEPTED` | `--machine-wash` (10% yellow) | `--machine` | `--machine` | Yellow-tinted but not solid; signed but not yet moving |
| `ACTIVE` | `--pass-bg` | `--pass` | `--pass` | Green — work is underway |
| `PC` (Practical Completion) | `--warn-bg` | `--warn` | `--warn` | Amber — transitional period, not done-done |
| `CLOSED` | `--ink-4` | `--fg-muted` | hairline | Neutral — archived, not active |

**Rule:** never change these colours per context. The state is always readable from the chip.

**Chip shape:** 3px border-radius, 3×8px padding, 10px mono 0.08em uppercase 600-weight text.

**State suffix** (e.g. `Day 14`, `Draft A`): optional, same-font, appended with `·`. Keep suffix short — it's supplementary, not primary.

**State transition animation:** when the state changes (e.g. accept → `QUOTED → ACCEPTED`), the chip pulses once (scale 1 → 1.08 → 1 over ~500ms) *after* the colour swap. The pulse calls attention; the colour does the communication.

---

## 5. Overlay Chips

Overlays sit right of the state chip in the header. Colour semantics:

| Overlay | Background | Text | Border | When it shows |
|---|---|---|---|---|
| `PAUSED` (on_hold / suspended) | `--warn-bg` | `--warn` | `--warn` | Whenever paused — typed reason appended |
| `DLP_OPEN` | `--ink-3` | `--fg-muted` | hairline | Muted — contextual, not urgent |
| `RETENTION_HELD` | `--ink-3` | `--fg-muted` | hairline | Muted |
| `DISPUTE_OPEN` | `--fail-bg` | `--fail` | `--fail` | Loud — red; dispute demands attention |

**PAUSED chip content:** `⏸ Paused · on hold` or `⏸ Paused · suspended`. The `⏸` glyph is always present. Reason is text, not colour-coded separately.

**PAUSED also renders a body band:** when `PAUSED`, a coloured band (warn-bg with warn border) appears above the meta-tab body content, stating: the reason, the paused-at date, who paused, expected resume, cure deadline (if suspension). This is a first-class detail Paul emphasised — don't collapse it into the chip alone.

**DISPUTE_OPEN:** count appears on the Contract tab (`⚠ Contract · 1`) in addition to the header chip. The tab-level signal is additive to the header.

---

## 6. Metric Tiles (top of Dashboard panels)

The 4-tile metrics row at the top of state dashboards has specific rules.

- **Grid:** 4 equal columns, 12px gap.
- **Tile shape:** 4px border-radius, 1px hairline border, `--ink-2` background, 14×16px padding.
- **Primary tile (first):** `--machine` background, `--ink-0` text — always the "most important metric for this state" (Quote Total in QUOTED, Complete % in ACTIVE, PC date in PC, Planned start in ACCEPTED).
- **Secondary tiles:** `--ink-2` bg, value colour varies by semantic:
  - `--fg` default
  - `--pass` for positive / good
  - `--warn` for attention
  - `--fail` for over-budget / negative
- **Tile anatomy (3 vertical elements):**
  - Kicker (10px mono 0.12em uppercase, `--fg-muted`) — 6px margin below.
  - Value (22px mono, 600 weight, 1.05 line-height). For text values (e.g. `Mon May 5`), drop to 16–18px.
  - Sub (optional; 11px mono, `--fg-muted`, 4px margin above). When a variance is flagged, sub colour becomes `--fail` or `--pass`.
- **Primary tile kicker uses `--ink-0` with 0.75 opacity** — preserves the "inset-against-yellow" readability.
- **Primary tile sub uses `--ink-0` with 0.7 opacity.**

---

## 7. Section Cards

General card pattern used for all grouped content.

- **Background: `--ink-2`.**
- **Border: 1px hairline.** Variants:
  - `accent` → border becomes `--machine` (used for "Needs your call" panel).
  - `warn` → border becomes `--warn` (used for paused bands, warning sections).
- **Corner radius: 4px.**
- **Margin bottom: 14px.**

### 7.1 Section head (strip at top of each section)
- Padding 12×16px; bottom hairline border.
- Horizontal layout: `num · title · chip-mini (optional) · spacer · action button(s)`.
- **Num:** mono, 10px, 0.08em, `--fg-dim`, 600. Format: `01`, `02`, … Zero-padded.
- **Title:** mono, 11px, 0.08em uppercase, 600. Colour is `--fg` by default; `--machine` when `accent`; `--warn` when `warn`.
- **Chip-mini:** small pill. Common variants:
  - default → `--machine-wash` bg, `--machine` text
  - `pass` → `--pass-bg` bg, `--pass` text
  - `warn` → `--warn-bg` bg, `--warn` text
  - `neutral` → `--ink-3` bg, `--fg-muted` text
- **Action button:** 5×10px padding, 10px mono uppercase 0.06em 600. Primary variant (`actionPrimary`) uses `--machine-wash` bg + `--machine` text + `--machine-wash` border. Standard uses `--ink-3` bg + `--fg` text + hairline border.

### 7.2 Common section glyphs
Glyphs are part of the title — implementers should not omit them.

| Glyph | Section type |
|---|---|
| `⚒` | Work Items, Scope |
| `⬒` | Variations |
| `⚠` | Assumptions (caution because variation-eligible) |
| `⊘` | Exclusions |
| `⚭` | Payment Schedule (chain) |
| `❑` | Warranty |
| `▤` | Retention / Terms / Contract reference |
| `⚙` | Sources / Items (material) |
| `◉` | Today / Dashboard / Overview |
| `◎` | Conversation / Timeline |
| `⚑` | Insight applied / Reference |
| `⚡` | Needs your call / Next action |
| `⛏` | Labour (task) |
| `✧` | Methodology |
| `⚬` | Provenance |
| `⟲` | Revive |

---

## 8. Work Item Table

- **Header row:** mono 10px 0.06em uppercase `--fg-muted` 500-weight on `--ink-1` background.
- **Data row padding: 9×16px.**
- **Row separator: 1px hairline; last row has no border-bottom.**
- **Numeric cells:** `font-family: mono`, right-aligned.
- **Description cell:** default `--fg` color. Can carry **sub-chip tags** (see 8.1).
- **Sell column:** `--machine` colour, 500 weight — the "sell price" is always yellow, a visual anchor for the money decision.
- **Margin column:** `--pass` colour, 500 weight.
- **Spent/over columns (in ACTIVE):** `--fg` if on-budget, `--fail` if over.
- **Selected row:** `--machine-wash` background, 3px machine-yellow left-border, padding-left reduced by 3 to compensate — row depth doesn't change.
- **Row hover:** subtle yellow wash via `color-mix(--machine 6%, transparent)`. No layout shift.

### 8.1 Sub-chip tags (on description cells)
Inline tags appended to a description. Two variants seen:

- **Default sub-chip:** `--ink-3` bg, 9px mono 0.06em, `--fg-muted`, 1×5px padding, 2px radius. Used for "← Peachtree" (inherited from past project) and similar neutral references.
- **Insight sub-chip:** `--machine-wash` bg, `--machine` text. Used when an insight has been applied (e.g. `⚑ +15% insight`). Signals that this row has a non-standard adjustment.

### 8.2 State chips within WorkItem rows
- `Ready` / `Complete` → `--pass-bg` + `--pass`
- `In progress` → `--machine-wash` + `--machine`
- `Not started` → `--ink-3` + `--fg-muted`
- Pill-style: 9px mono 0.08em uppercase 600-weight, 2×7px padding, 3px radius.

---

## 9. Progress Bars

- **Track:** 4px tall, `--ink-3`, 2px radius.
- **Fill default:** `--machine`.
- **Fill at 100%:** flip to `--pass` (green). Explicit colour change at completion — visually rewards the "done" state.
- **Fill at 0%:** the bar appears empty; track alone is visible.
- **Percentage label:** mono 10px `--fg-muted` 30px min-width right-aligned. Never drops the `%` sign.
- **Min container width:** 110px. Below that the label crowds the track.

---

## 10. Chat Pane — micro-details (Paul's specific concern)

This is the area Paul flagged as the class of detail that gets lost. **Every element below is required.**

### 10.1 Timestamp separator
Centered row between message groups: mono 10px 0.08em uppercase `--fg-dim`, 8px top margin, 10px bottom margin, format `— Tue · Apr 17 · 05:48 —`. The em-dashes are significant — they visually bracket the time.

### 10.2 Message "who" line
Above every bubble. Format: `[avatar] Name · timestamp` (e.g. `[S] Sarah · 05:48`).
- Mono 10px 0.08em uppercase, `--fg-dim` colour, 600-weight.
- **4px margin below** before the bubble starts.
- Avatar: 16×16px, 3px radius, 10px mono bold initial. Machine-yellow bg + `--ink-0` text for Kerf; `--ink-4` bg + `--fg` text for user.

### 10.3 Message bubbles

- **User bubble:** `--machine` bg, `--ink-0` text, 500 weight. No border.
- **Kerf bubble:** `--ink-2` bg, `--fg` text, 1px hairline border.
- **Padding: 10×12px. Radius: 6px. Line-height: 1.45.**
- **Strong text inside bubbles:** machine-yellow in Kerf bubbles; darker ink-0 in user bubbles. Used for key entities and highlighted values.

### 10.4 Event markers (Paul's specific concern — "events coming up in chat with their own icon")

Events are **not messages**. They're a distinct element in the chat stream. This is the thing Paul flagged as easy to lose.

**Appearance:**
- **Dashed border instead of solid** — `1px dashed --hairline`.
- **Background: `--ink-2`** — same as Kerf bubbles, but the dashed border visually separates them as a distinct class.
- **Padding: 8×10px.**
- **Typography: mono 10.5px 0.04em letter-spacing, `--fg-muted`.** Explicitly smaller than messages.
- **No avatar, no "who" line** — events are system-generated, not authored.
- **Always prefixed with `◈`** — the diamond glyph is the visual class marker. Present on every event.
- **Strong text** (entity names, sums, keywords) uses `--machine` colour inside events.

Examples:
```
◈ Event · Gary accepted via magic link · 16:22 · signed as Gary Pemberton
◈ Event · ContractVersion v1 locked · $121,200 · 5% · 30d · AZ
◈ DLP expired · retention released $6,152
```

**Implementation note:** events are their own component, not a styled variant of ChatBubble. Do not reuse the ChatBubble component with a prop — build `ChatEvent` separately so the visual contract can't regress.

### 10.5 Inline cards within messages
When Kerf references a multi-entity result (e.g. "I pulled 7 items"), the bubble can carry an inline card below the prose:
- 1px hairline border, `--ink-2` bg, 4px radius.
- 10×12px padding, 11.5px font.
- Mono kicker label at top (10px 0.08em uppercase `--fg-muted`) describing the payload.

### 10.6 Chat input
- Text field background: `--ink-2`. Placeholder colour: `--fg-dim`.
- `◉ HOLD` button — 10px mono 0.08em uppercase 600. The `◉` is a filled circle — reads as "press-and-hold to speak".
- `SEND` button — machine-yellow bg, ink-0 text, same typography.
- **Enter submits** (but respects newline with Shift-Enter).
- **Press-and-hold on HOLD** captures voice; releasing sends the transcription.
- **On mobile:** HOLD becomes larger and more prominent — voice is the default input on mobile.

---

## 11. Inspector Panel (split canvas)

When an entity opens for detail, a right-side inspector panel slides in.

- **Width: 440px** (desktop). On mobile it's a full-screen push.
- **Background: `--ink-2`.**
- **Border: 1px hairline, 4px radius.**
- **Slide-in direction: from the right, with fade.** Not from below, not from above.
- **The main list (WorkItems, variations, etc.) does NOT unmount when the inspector opens.** It dims to 0.5 opacity and stays visible. The user can click another row and the inspector re-populates. This preserves context.
- **Header region is sticky:** 14×18px padding, `--ink-3` background (slightly lifted from panel body), bottom hairline.
- **Header structure:**
  - Left: kicker (10px mono 0.12em uppercase `--machine` 600) above title (14px `--fg` 500).
  - Right: `✕` close glyph — `--fg-dim` colour, mono 12px. One tap closes the inspector (not the whole screen).
- **Body padding: 14×18px.**

---

## 12. Quick-Action Cards (Dashboard bottom rows)

Referenced by Paul's screenshot highlight.

- **Grid:** 4 equal columns, 10px gap (small rows), or 12px gap (larger).
- **Each card:** `--ink-2` bg, 1px hairline border, 4px radius, 12–14px padding.
- **Hover:** bg → `--ink-3`, border → `--machine-wash`. Subtle.
- **Card anatomy (3 stacked elements):**
  - Icon (`--machine` stroke, 16–18px, block display) — 6–8px margin below.
  - Label (11px mono 0.06em uppercase 600, `--fg`).
  - Sub (11px mono, `--fg-muted`, 3px margin above) — current state hint, e.g. "Thu 09:00 set" or "4 clocked in now".

**Behaviour** (per IA audit §7): tapping a card dispatches a chat intent to the agent. The card is a shortcut label; the action flows through the standard conversational path.

**Card set varies per state.** LEAD has 4, ACTIVE has 4, PC has different ones. See `project-screen-ia-audit.md §7` for the full matrix.

---

## 13. "Needs Your Call" Panel (ACTIVE state signature element)

The most important surface on the ACTIVE Dashboard. Contains only things requiring Sarah's decision.

- **Section border: 1px `--machine`** (not hairline — this section is distinguished).
- **Section title: `⚡ Needs your call` in `--machine` colour** (not `--fg` like other sections).
- **Content grid: 2 columns, 14px gap, 14×16px padding.**
- **Each card inside:**
  - `--ink-3` background.
  - **3px left-border in colour that signals the urgency type:** `--machine` for action-required, `--warn` for warning/awareness.
  - 12×14px padding.
  - Mono kicker at top (10px 0.08em uppercase 600) coloured to match the left-border.
  - 13px title, `--fg`, 500 weight.
  - 11.5px body, `--fg-muted`, 1.5 line-height.
  - Optional buttons row at bottom (8px gap), 5×10px padding each.

**Rule:** the number of cards is bounded — too many and the signal dilutes. If there are >4 items that need Sarah's call, they go into a collapsed "more" expansion. Bias toward showing only the top 2–3 by urgency.

---

## 14. Insight Cards (Yellow-on-Dark)

When an insight has fired on a WorkItem or task, a prominent insight card renders in the inspector.

- **Background: `--machine-strong` (`rgba(245, 184, 0, 0.20)`)** — stronger than the normal machine-wash so the card reads as its own object.
- **Border: 1px `--machine`.**
- **Padding: 14px. Radius: 4px.**
- **Top row (`flex justify-between`):**
  - Left: kicker, e.g. `⚑ Insight applied · +15% labour` — mono 10px 0.12em uppercase 600, `--machine-bright` (#FFCA18).
  - Right: confidence + sample, e.g. `Confidence 92% · n=3` — mono 10px 0.08em, `--machine-bright`.
- **Body: 13px, `--fg`, 1.55 line-height.** Mentions evidence projects by name (`Alder St`, `Peachtree Ph I`) in machine-yellow semibold.
- **Footer grid (2 columns, 10px gap):** "First observed" and "Last confirmed" dates. Mono 10px 0.04em, `--fg-muted` with `--fg` strong accents.

**Rule:** insight cards are always in machine-yellow strong variant — they're the thing Kerf learned, and they stand out even against the yellow-heavy design.

---

## 15. Methodology Cascade Visualisation

Renders in Scope → WorkItem inspector or in a dedicated Methodology view.

- **Three vertical levels** (Project · Package · Item), each with a **left border in level-specific colour:**
  - Project: `--machine` (yellow, strongest)
  - Package: `--fg-muted` (dim grey)
  - Item: `--fg-dim` (dimmer grey)
- **Level head:** glyph + label + title. Label is mono 10px 0.12em uppercase 600 in the level colour. Title is 13px 500 weight in `--fg`.
- **Keys rendered in a 2-column grid** — 8px gap.
- **Each key pill:**
  - `--ink-3` bg, hairline border, 3px radius, 8×10px padding.
  - Left: mono 10px 0.06em uppercase `--fg-muted` (the key name).
  - Right: mono 11px 500 `--fg` (the value).
- **Override key (set at a lower level):**
  - Border becomes `--machine`.
  - Bg becomes `--machine-wash`.
  - Value colour becomes `--machine`.
  - Key label includes a `⚑` prefix, e.g. `⚑ Ceiling height`.

### 15.1 Effective methodology block
At the bottom of the cascade view (or in a right rail), renders the merged "effective" map:
- `--ink-3` bg, 1px `--machine-wash` border, 4px radius, 12×14px padding.
- Kicker at top: `approach map (N keys)` in mono 10px 0.12em uppercase `--machine` 600.
- Each row: `key · value · origin` (where origin is `proj` / `pkg` / `item`).
- Override rows render with `--machine` value text — visual consistency with the override pill in the cascade above.

---

## 16. Lineage Equation

Specific to the labour-detail provenance drill.

- **Background:** `--ink-3`, 4px radius, 14–20px padding.
- **Head:** mono 10px 0.12em uppercase 600 `--fg-muted`, e.g. "How 18.4 hours was computed", 16px margin below.
- **Equation row:** flex, 8px gap, mono 12px.
- **Node variants:**
  - **Default:** `--ink-4` bg, `--fg` text, hairline border. E.g. `12 holes`, `16.0 hrs`.
  - **Base:** `--pass-bg` bg, `--pass` text, `--pass` border. The known-good starting rate. E.g. `1.33 hr/hole`.
  - **Insight:** `--machine-wash` bg, `--machine` text, `--machine` border. The adjustment source. E.g. `low-ceiling`.
  - **Final:** `--machine` bg (solid), `--ink-0` text, `--machine` border, 600 weight. The computed answer. E.g. `18.4 hrs`.
- **Arrows between nodes:** `--fg-dim` text, mono 12px. Can be `→`, `×`, `=`, `+15%`.

**Animation (Remotion):** nodes slide-in-and-fade left-to-right, with each arrow appearing *before* the node it points to. Pacing: ~18 frames between nodes at 30fps (0.6s). Final node arrives last and often gets a subtle extra beat.

---

## 17. Provenance Tree

ASCII-style tree rendering for the "where did this number come from?" view.

- **Mono typography, 12px, 1.9 line-height** for airy readability.
- **Tree characters: `├─`, `│`, `└─`** — drawn in `--fg-dim`.
- **Indentation per level: 16px** — enough to read but compact.
- **Node values** (e.g. `$9,800`, `$4,560`) in `--machine` or `--pass` as per semantic:
  - Top-level sell in `--machine` 600.
  - Cost and margin rollups in `--machine` or `--pass` 500.
- **Trailing label text** in `--fg-muted` for description.
- **Inline source tags** (using the `src-tag` styling — see §18) embedded within the descriptive line.

**Animation (Remotion):** rows cascade in top-to-bottom, ~14 frames stagger. Feels like the tree is drawing itself.

---

## 18. Source Tags

Source tags label every number in the quote/estimate with its provenance.

| Variant | Colour | Bg | Meaning |
|---|---|---|---|
| `catalog` | `--pass` | `--pass-bg` | Current price from rate table / supplier feed. High certainty. |
| `history` | `--machine` | `--machine-wash` | Derived from past job data. Label includes sample size: `Past · 3×`. |
| `insight` | `--machine-bright` | `--machine-strong` | A learned adjustment has fired. Loud yellow — brightest variant. |
| `stated` | `--warn` | `--warn-bg` | Contractor-stated, not yet an insight. Amber — invites capture. |
| `default` | `--fg-muted` | `--ink-3` | Neutral / no specific source tracked. |

**Shape:** 2×7px padding, 3px radius, 9px mono 0.08em uppercase 600 weight, inline-block.

**Never display a number without its source tag** in provenance-surfacing contexts. The tag is load-bearing for trust.

---

## 19. Confidence Meter

Used to surface how confident Kerf is in a number, sample, or insight.

- **Horizontal bar, embedded in a `--ink-3` wrapper (12px padding, 4px radius).**
- **Layout:** `label · track · value` (flex, 14px gap, align-center).
- **Label:** mono 10px 0.08em uppercase `--fg-muted` 600, min-width 80px.
- **Track:** flex-1, 6px height, `--ink-0` bg, 3px radius.
- **Fill bands** (colour by confidence level):
  - High (≥85%): `--pass`
  - Med (50–85%): `--machine`
  - Low (<50%): `--warn`
- **Value label:** mono 12px 500, matching fill colour, min-width 60px, right-aligned.

**Appears in:** WorkItem inspector (overall confidence), Labour task detail (rate source confidence), Provenance tree (per-dimension confidence).

---

## 20. Timeline Entries

Used in: main Dashboard's "Today" panel, dedicated Timeline tab, closeout archive views.

- **Grid per row: `120px 1fr` (when/what).**
- **Padding: 9px top/bottom.**
- **Row separator: 1px hairline; last row none.**
- **When column:** mono 10px 0.06em uppercase `--fg-muted`, 1.5 line-height.
- **What column:** `--fg`, 1.5 line-height.
  - Key entities in the prose use `--machine` 500 weight.
  - Actor suffix at the end of the line: mono 10px 0.06em uppercase `--fg-dim`, prefixed with 6px left-margin. Examples: `Kerf · from chat`, `Mike · voice`, `GPS · auto`.

**Rule:** every timeline entry has an actor suffix. Never omit — it's what makes the record audit-worthy.

---

## 21. Contract-Reference Strip (ACTIVE state)

When in ACTIVE, the contract details compress into a single strip above the metrics row. Easy to lose — implementers will want to put it in a tab. **Don't.**

- **Background: `--ink-1`, hairline border, 4px radius.**
- **Padding: 10×16px.**
- **Flex row, 20px gap, align-center, 11.5px font.**
- **Starts with kicker `▤ Contract v1 locked`** in mono 10px 0.12em uppercase `--fg-muted` 600.
- **Items are mono 11px 0.02em in `--fg-muted`**, with **key values bolded in `--fg`**. Examples: `$121,200 lump sum`, `Retention 5%`, `Warranty 12mo`, `Payment 30d net`, `Signed Mon 16:22`.
- **"Expand ▾" at the right**, mono 10px 0.08em uppercase `--machine` — taps to expand to the full Contract view (or opens the Contract meta-tab).

---

## 22. PC-state Close-Summary Tiles

The PC Dashboard uses a 3-column mini-tile grid for close-out summary values (different rhythm from the 4-tile metrics row).

- **3 equal columns, 10px gap, 14×16px padding.**
- **Each tile:** `--ink-3` bg, 4px radius, no border (unlike metric tiles).
- **Kicker + value only — no sub line.**
- **Pass-variant values** (e.g. "Clear", "0 open") render in `--pass`.

---

## 23. Revive Card (CLOSED state)

- **Background: `--ink-2`, 1px `--machine` border, 4px radius, 20px padding.**
- **Centered text alignment.**
- **Kicker: `⟲ Revivable with full context`** in `--fg-muted`, 8px margin below.
- **Title: 16px `--fg` 500.**
- **Body: 12.5px `--fg-muted`.** 12px margin below.
- **Two buttons side by side, 0 4px margin:**
  - Primary (`Revive this project`): `--machine` bg, `--ink-0` text.
  - Alt (`New linked Project`): `--ink-3` bg, `--machine` text, `--machine-wash` border.

**Animation (Remotion):** the card pulses subtly (scale 1 → 1.015 → 1) at a slow beat. Communicates "latent, revivable, still here." Do not make it flash — that would feel like a notification.

---

## 24. Empty States (often missing)

The mockups don't fully render empty states but they matter. For each meta-tab tab-body:

- Empty is NOT a blank space. It's a small, helpful prompt.
- Pattern: centered icon (24px, `--fg-dim`), one-line label (`--fg-muted`, 13px), optional action button.
- Examples:
  - Work → Variations (LEAD/QUOTED): *"No variations yet. One will appear here when the agent detects or you draft one."*
  - Site → Safety (LEAD/QUOTED): *"Site safety plan drafts at acceptance. Nothing to track until then."*
  - Money (LEAD): *"Projected value from drafted WorkItems appears here once scope is captured."*
- Never show a loader spinner that lives more than 250ms. Prefer skeleton rows (shimmer at 800ms).

---

## 25. State-Aware Variations (cross-cutting rule)

Every component rendered on the Project screen should consider per-state behaviour. Checklist:

- Does this component appear in `LEAD`? If yes, with what data? If no, what's its empty/disabled state?
- Does it change prominence at a particular state (e.g. Variations tab prominent in ACTIVE, empty in LEAD)?
- Does the primary CTA on this component change per state? E.g. "Send quote" (LEAD) → "View quote" (QUOTED) → "Contract reference" (ACTIVE) → "Archive quote" (CLOSED).

Per-state variation is an implementation *requirement*, not a polish item.

---

## 26. Animations & Transitions (Remotion-specific but mirror on web)

- **State chip pulse on transition:** scale 1 → 1.08 → 1 over ~500ms. Colour change is instant; pulse is the attention beat.
- **Section mount cascade:** when a dashboard loads, sections fade-in-and-slide-up with ~40ms stagger between siblings. The `data-sb-beat` CSS primitive already exists in `frontend/src/index.css` — use it.
- **Inspector slide-in from the right:** spring-based, ~320ms. Main list simultaneously dims to 0.5 opacity.
- **Row highlight on interaction:** yellow wash (6% machine) on hover, no layout shift.
- **Typing indicator (Kerf thinking):** 3-dot pulse with stagger, 1.2s cycle. Already in `index.css` as `.sb-typing-dots`.
- **Typing caret ("KERF IS TYPING_"):** blinking underscore, 1.2s. Already in `index.css` as `.sb-caret`.

---

## 27. Typography System (canonical)

Defined in `frontend/src/index.css`. **Never inline custom sizes** — use tokens.

| Token | Size | Letter-spacing | Weight | Transform | Usage |
|---|---|---|---|---|---|
| `text-kicker` | 10px | 0.12em | 600 | uppercase | Section labels, tile kickers |
| `text-label` | 11px | 0.06em | 500 | uppercase | Tab labels, button text |
| `text-body` | 12.5px | — | 400 | — | Chat bubbles, standard prose |
| `text-prose` | 14px | — | 400 | — | Intro paragraphs, explanatory text |
| `text-title` | 15px | — | 500 | — | Section titles, inspector titles |
| `text-display` | 20px | — | 500 | — | Tile primary values, hero numbers |

Mono is used for: numbers (always), kickers/labels, timestamps, entity IDs, event log entries. Sans for prose, titles, message bubbles.

---

## 28. Colour Semantics (quick reference)

| Token | Used for |
|---|---|
| `--machine` (#F5B800) | Sell prices, primary actions, machine-yellow brand emphasis, QUOTED state |
| `--pass` (#38a169) | Completed, paid, on-time, margin-positive, high-confidence |
| `--warn` (#d69e2e) | Paused (PC state), DLP, "needs attention but not broken" |
| `--fail` (#e53e3e) | Over-budget, dispute open, lost, terminated-for-cause |
| `--fg-muted` (#a3a79c) | Metadata, kickers, non-interactive labels |
| `--fg-dim` (#71766b) | Subordinate text, tree lines, dimmed indicators |

**Do not invent new colour variations.** If a new semantic emerges, extend the token set in `index.css`, don't inline it.

---

## 29. Voice / Chat Equivalence

Every tap-interactive element on the Project screen must have a voice equivalent. If a user can do it by tap, they can do it by voice. The voice-phrase mapping is documented alongside each MCP tool in `project-screen-ia-audit.md §7`.

**Implementation guard:** if a PR adds a new button and doesn't cite its voice equivalent in the PR description, that's a missing-fidelity blocker.

---

## 30. Mobile-specific adjustments

The mockups are desktop (1440×820/900). Mobile rules:

- Icon rail → bottom nav.
- Agent panel → FAB (bottom-right). Tapping expands to fullscreen.
- Meta-tabs → horizontally-scrolling chip row, or compressed into a dropdown "More" if space-constrained.
- Metric tiles → 2-per-row on phone, 4-per-row on tablet.
- Inspector panel → push-from-right full-screen rather than side-by-side.
- Quick-action cards → one-per-row with a larger tap target, icon + label side-by-side.

**Offline-first is non-negotiable.** Voice captures queue locally if the network is down. Photos queue locally. Graph writes queue locally. Everything reconciles on sync.

---

## 31. Things Explicitly Missing from This Ledger (to Add Later)

- **Canvas rendering patterns** (deferred — separate design pass as canvas matures).
- **Home screen** (see `project-screen-ia-audit.md §12` — its own design doc).
- **Mobile gesture grammar** (swipe to dismiss, pull to refresh, etc. — needs its own pass).
- **Empty-state illustrations** (if we decide to have them; currently text-only).
- **Print styles for generated proposals, invoices, PC certificates** — partially in `index.css @media print` but not fully specified per artefact.

---

*End of ledger. Living document — extend on every design review.*
