# Site Board — Design System Rationale

## The one-line pitch

**The app is a clipboard on a jobsite trailer wall.** Dark, utilitarian, information-dense. Yellow only for machine-critical actions. Typography does the heavy lifting.

## Why this direction

Marco, Sarah, and Jake don't want "beautiful software." They want **equipment**. A tool that looks serious, reads fast, and doesn't waste their attention. The Site Board visual language is borrowed from:

- **Stamped metal plates** on industrial equipment (the NumPlate, the KERF wordmark)
- **Jobsite clipboards** (the chat scrollbar, the slab-serif numerics)
- **Ledger books** (table density, Plex Mono for all numerics)
- **Safety signage** (machine yellow #F5B800 as the single action color)

## Non-negotiable rules

### 1. Yellow is precious
`--machine: #F5B800` (your existing token) appears only on:
- Primary action buttons (max one per screen)
- Active nav state (underline or background wash)
- The 2px hairline under the project strip
- Yellow badges for in-progress/active states
- Hover-tint on interactive table rows (max 6% opacity)

If a screen has 3+ yellow elements, something is wrong.

### 2. Dark is the app, light is for PDFs
The **app is dark-mode-first**. Light mode exists because it's already built, and because some users may print screens, but the intended experience is dark. The landing page is also dark.

### 3. Monospace for all numerics
Quantities, prices, percentages, timestamps, dates, IDs — all `font-mono` (IBM Plex Mono). Prose and labels are `font-sans` (IBM Plex Sans). This creates the ledger rhythm that makes dense tables readable.

### 4. Density is a feature
Sarah reconciles 45 people on Sunday afternoons. She doesn't want whitespace; she wants to see everything at once. Table rows are 32–36px tall, not 48. Card padding is 16px, not 24. Inputs are 32px, not 44. The exception is **Marco's mobile screens**, where hit targets must be ≥44px.

### 5. Chrome is stamped, not drawn
Panel headers, card titles, toolbar bars — these look **engraved/debossed**, not floated. Subtle inset shadows, faint top highlights, no drop shadows. The only drop shadow allowed is the 1px hover lift on cards (`translateY(-1px) + deeper shadow, 160ms ease`).

### 6. Empty is earned
No hero illustrations. No "Welcome!" headers. No decorative SVG. If a section is empty, fill it with data or cut it. If there's truly nothing to show, use a single-line muted message — never a full empty-state illustration.

## Key primitives (what to build)

| Primitive | What it is | Where it lives | New or upgrade? |
|-----------|-----------|----------------|-----------------|
| **Button** | Primary/outline/ghost/destructive | `ui/button.tsx` | Upgrade — add press-in state, hover darken |
| **Card** | Dark surface with stamped header | `ui/card.tsx` | Upgrade — add hover-lift, inset top highlight |
| **Badge** | Status pills (pass/fail/warn/info) | `ui/badge.tsx` | Upgrade — tighter, use semantic tokens |
| **Table** | Ledger-style dense rows | `ui/table.tsx` | Upgrade — smaller header text, yellow row hover |
| **Input / Select** | Dark 32px tall, 1px border | `ui/input.tsx`, `ui/select.tsx` | Upgrade — border-inset look |
| **NumPlate** | Stamped `01 / 02 / 03` section markers | **NEW** — `ui/num-plate.tsx` | New primitive |
| **SbPanel** | Dark panel with stamped header bar | **NEW** — `ui/sb-panel.tsx` | New primitive |
| **SbScrollbar** | 8px transparent-track, 6% thumb | CSS only — global in `index.css` | Upgrade current scrollbar styles |
| **KerfMark** | K-monogram stamped plate | **NEW** — `ui/kerf-mark.tsx` | New primitive |
| **TypingIndicator** | "KERF IS TYPING_" with caret + dots | **NEW** — `chat/typing-indicator.tsx` | New primitive |

## Typography scale (for Tailwind 4 `@theme inline`)

| Token | Size / Line / Weight | Use |
|-------|----------------------|-----|
| `text-kicker` | 10px / 1 / 600, tracking 0.12em, uppercase | NumPlate, section kickers |
| `text-label` | 11px / 1.2 / 500, tracking 0.06em, uppercase | Table headers, badge text, form labels |
| `text-body` | 12.5px / 1.4 / 400 | Table cells, card body |
| `text-prose` | 14px / 1.5 / 400 | Chat messages, descriptions |
| `text-title` | 15px / 1.3 / 500 | Card titles, panel headers |
| `text-display` | 18–22px / 1.1 / 500 | Page titles (one per screen) |
| `text-num` | Plex Mono + tabular-nums | ALL numerics everywhere |

## Color system (delta against existing)

Your existing tokens in `index.css` are mostly right. The handoff tokens file (`SITEBOARD_TOKENS.css`) makes these adjustments:

- **Add:** `--sb-ink-*` scale for dark-mode surface depth (ink-0 through ink-6)
- **Add:** `--sb-hairline` (1px divider, 8% white on dark / 8% black on light)
- **Add:** `--sb-plate-highlight` and `--sb-plate-recess` for the stamped NumPlate look
- **Calibrate:** `--muted-foreground` to `#a3a79c` (slightly lighter than current `#71766b` for dark mode readability)
- **Retain:** `--machine`, `--pass/fail/warn`, the brand palette — all correct

## Motion system

| Interaction | Behavior |
|-------------|----------|
| Card hover | `translateY(-1px)`, shadow depth doubles, 160ms ease-out |
| Table row hover | Background → `color-mix(in oklab, var(--machine) 6%, transparent)`, 120ms |
| Button hover | Darken 8%, 120ms |
| Button active | `translateY(1px)`, 80ms (already in existing Button CVA) |
| Panel mount | Opt-in `.sb-beat` — fade+slide up 8px, 320ms ease-out, stagger 40ms per panel |
| Typing indicator | 3 dots pulse, staggered 150ms. Caret blinks at 1.2s |

## What NOT to do

- **No gradient backgrounds.** Flat surfaces only. The NumPlate "gradient" is actually two inset shadows faking metal.
- **No drop shadows on buttons.** They're stamped, not floated. Border + subtle color depth, not elevation.
- **No emoji.** Ever. Use icons from lucide-react (already installed).
- **No rounded-full badges.** Current radius is `var(--radius-4xl)` on badges — that's fine, keep it small pill shape, not circular.
- **No light dividers between every row.** Let whitespace separate data; only use hairlines where scannability demands it.
- **No "AI"-branded visual slop.** No gradient starbursts, no shimmer effects, no glass blur. Kerf is a tool, not an AI product.

## The landing page

The landing page needs a separate pass because it's marketing, not tool. The rules:

- Same tokens, same dark base (`#0d0e0c`)
- Yellow is *slightly* more expressive here — one large machine-yellow heading element allowed
- Motion is allowed (fades, subtle parallax) — but no carousels, no hero illustrations
- Typography can go larger: `text-display` up to 56px for hero headline
- Keep the "K" monogram + KERF wordmark as the only brand expression
- Screenshots of the product (dark themed) are the hero imagery

See `components/LandingPage.notes.md` for the full spec.

---

*For the full execution order, see `CLAUDE_CODE_BRIEF.md`.*
