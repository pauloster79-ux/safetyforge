# Site Board Design System — Handoff for `safetyforge`

## Overview

This handoff rolls the **Site Board** design direction across the entire Kerf app.

The good news: your codebase **already has 90% of the foundation**. `frontend/src/index.css` already defines `--machine`, `--pass/--fail/--warn`, IBM Plex, a `0.1875rem` radius, and a dark mode. This handoff is a **calibration + completion** exercise, not a ground-up rewrite.

## About the Design Files

The HTML files in `reference_mocks/` are **design references** — static prototypes created in plain HTML/React/Babel showing the intended look, density, and micro-interactions. They are **not** production code to copy-paste.

Your job (or Claude Code's) is to **express these references through the Kerf codebase's existing Tailwind 4 + shadcn/ui + Base UI stack**, following the patterns already established in `frontend/src/components/ui/`.

## Fidelity

**High-fidelity.** Colors, typography, spacing, hover states, and micro-interactions are finalized and pixel-accurate. When a mock shows an 8px scrollbar with 6% white thumb, build it that way.

## What this handoff contains

| File | What it is | Who reads it |
|------|-----------|--------------|
| `README.md` | You are here — orientation | Everyone |
| `CLAUDE_CODE_BRIEF.md` | Wave-by-wave execution plan, commands to run, files to touch | Claude Code |
| `SITEBOARD_DESIGN.md` | Why the system looks this way — rules, do's & don'ts, rationale | Paul + any human reviewing |
| `SITEBOARD_TOKENS.css` | The new `index.css` contents — token deltas, new vars, scrollbar, animations | Drop-in replacement |
| `components/` | Reference rewrites of existing shadcn primitives + new Site Board primitives | Source of truth for components |
| `reference_mocks/` | The original HTML/React mocks for visual reference | Open in a browser to see the target |

## Execution model

**Paul does not execute this directly.** Claude Code running locally in `safetyforge/` does the execution, following `CLAUDE_CODE_BRIEF.md`.

Three waves:

1. **Foundation** — swap tokens, upgrade `components/ui/` primitives, add new Site Board primitives. Every page in the app gets a visual upgrade for free.
2. **High-traffic screens** — restyle `AppShell`, `DashboardPage`, `ContractTab`, `InspectionListPage` as reference implementations for their patterns.
3. **Sweep** — remaining pages adopt the Wave 2 patterns. Edge cases (mobile, dense forms, voice UI) come back to Paul's design conversation for judgment calls.

Waves 1 and 2 are mechanical. Wave 3 is where judgment is needed.

## The three personas (reminder from CLAUDE.md)

- **Marco** — phone, jobsite, 5:30 AM, one-handed
- **Sarah** — desk, Sunday reconciliation, dense data
- **Jake** — solo, wants to look professional

The design system has to land on all three. Dashboard density is Sarah. Mobile bottom sheets are Marco. The landing page is Jake.

## Quick-start for Claude Code

```bash
cd safetyforge/frontend
# Read the brief
cat ../design_handoff_siteboard/CLAUDE_CODE_BRIEF.md

# Wave 1 starts by replacing index.css
cp ../design_handoff_siteboard/SITEBOARD_TOKENS.css src/index.css
# then update the primitives one at a time against reference files in components/
```

---

*Handoff built by: Claude, via design conversation. The mocks live at: `Kerf Directions.html` in the source design project — specifically direction 05 (Site Board) and 06 (Site Board Contract).*
