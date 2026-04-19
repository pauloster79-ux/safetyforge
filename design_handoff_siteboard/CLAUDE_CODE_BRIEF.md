# Claude Code Brief — Site Board Rollout

**Target repo:** `pauloster79-ux/safetyforge`
**Target branch:** create `siteboard-rollout` off `main`
**Goal:** roll the Site Board design system across the full app in three waves. Each wave is independently shippable.

> **Context:** `safetyforge` is the Kerf app. Stack is React 19 + TypeScript + Vite + Tailwind 4 + shadcn/ui (w/ Base UI primitives). The codebase already has ~90% of the Site Board foundation — this is a calibration + completion pass, not a rewrite. Read `../SITEBOARD_DESIGN.md` before starting.

---

## Rules of engagement

1. **One wave per PR.** Don't mix waves.
2. **Verify in the browser after each file change.** `npm run dev`, load the affected page, eyeball it.
3. **Don't skip the reference files.** The `components/` folder in this handoff contains exact drop-in replacements and new primitives. Start by reading them, then adapt to the actual file at the same path in the repo.
4. **Use the existing tokens where possible.** `--machine`, `--pass`, `--fail`, `--warn` are already perfect. New tokens are additive.
5. **Report ambiguity, don't invent.** If a screen has no mock and the pattern isn't obvious, pause and ask Paul. Don't ship judgment calls silently.

---

## Wave 1 — Foundation

**Scope:** tokens + `components/ui/` primitives + new Site Board primitives.
**Expected diff:** ~15 files modified, ~4 new files, ~600 LOC touched.
**Verification:** every existing page in the app still renders; new primitives work in Storybook or a scratch route.

### Step 1.1 — Replace `index.css`

Copy the contents of `SITEBOARD_TOKENS.css` into `frontend/src/index.css`. It preserves your existing tokens and print styles, adds `--sb-ink-*`, `--sb-hairline`, `--sb-plate-*`, type tokens, the new 8px scrollbar, hover-lift animation, row-tint, and the typing-indicator keyframes.

### Step 1.2 — Force dark mode by default

In `frontend/src/main.tsx`, ensure `<html class="dark">` is set at mount. If you're using `next-themes` (it's in `package.json`), set `defaultTheme="dark"` and `forcedTheme="dark"` on the provider for now. Light mode only runs in `@media print`.

### Step 1.3 — Upgrade existing primitives

For each of the following, **read the reference file in `components/ui/`** in this handoff, diff against the actual file in `frontend/src/components/ui/`, and apply the changes:

| Ref file | Target file |
|----------|-------------|
| `components/ui/button.tsx` | `frontend/src/components/ui/button.tsx` |
| `components/ui/card.tsx` | `frontend/src/components/ui/card.tsx` |
| `components/ui/badge.tsx` | `frontend/src/components/ui/badge.tsx` |
| `components/ui/table.tsx` | `frontend/src/components/ui/table.tsx` |

After each file, grep the codebase for any usage that relied on now-removed variants/props. The badge changes add `pass/fail/warn/info` variants — no existing variants are removed.

### Step 1.4 — Add new primitives

Copy these into the repo **as new files**:

| Ref file | Destination |
|----------|-------------|
| `components/ui/num-plate.tsx` | `frontend/src/components/ui/num-plate.tsx` |
| `components/ui/sb-panel.tsx` | `frontend/src/components/ui/sb-panel.tsx` |
| `components/ui/kerf-mark.tsx` | `frontend/src/components/ui/kerf-mark.tsx` |
| `components/chat/typing-indicator.tsx` | `frontend/src/components/chat/typing-indicator.tsx` |

### Step 1.5 — Smoke test

Run `npm run dev`, visit `/`, `/projects`, `/dashboard`, `/inspections`. Expected result: the app looks *slightly* crisper — darker surfaces, smaller table headers, tighter badges. Nothing should be broken.

Commit: `feat(design): Site Board foundation — tokens + primitives`

---

## Wave 2 — High-traffic screens

**Scope:** 4 reference-implementation screens that set the pattern for the sweep.
**Expected diff:** ~10 files, ~1500 LOC.

### Step 2.1 — AppShell (`components/shell/AppShell.tsx` + `IconRail.tsx`)

- Add the `<KerfMark variant="full" size="sm" />` to the top of `IconRail` (or a new top bar if the rail is too narrow — 48px won't fit the wordmark; use `variant="mark"` there)
- IconRail items: active state is a 2px left yellow accent bar + yellow icon, inactive is muted grey
- Add the 2px machine-yellow hairline at the bottom of any global header bar, fading to transparent at the edges: `bg-[linear-gradient(90deg,transparent,var(--machine)_20%,var(--machine)_80%,transparent)] h-[2px]`

### Step 2.2 — DashboardPage (`components/dashboard/DashboardPage.tsx`)

- Replace ad-hoc card layouts with `<SbPanel num="01" kicker="Today" title="Morning Brief" />` style
- All numerics (counts, percentages, hours) in `.font-mono` with `tabular-nums`
- Badges for status chips must use the semantic `pass/fail/warn` variants
- Stagger panel mount with `beat={i}` prop (already wired)

### Step 2.3 — ContractTab (`components/projects/ContractTab.tsx`)

- This file is 37KB — the largest. Paul already has a full mock of this page.
- **Read `reference_mocks/siteboard-contract.jsx` before starting.** That file is the target.
- Structure: chat-left (40%) / canvas-right (60%) is already the app pattern — the contract canvas content needs the NumPlate + SbPanel treatment
- Work Items table is the key pattern here: `TableHead` tiny uppercase, cells monospace for qty/price, yellow row hover

### Step 2.4 — InspectionListPage (`components/inspections/InspectionListPage.tsx`)

- Pure table pattern. Yellow hover on rows. Status column uses semantic `Badge` variants.
- Filter bar above: ghost buttons for each filter with active state using `aria-expanded="true"` styling
- Empty state: single line of muted text, no illustration

Commit: `feat(design): Site Board — reference screen implementations`

---

## Wave 3 — Sweep

**Scope:** apply Wave 2 patterns to the remaining ~25 page files.
**Expected diff:** large, but mostly find-and-replace style.
**Verification:** Paul walks through the app with you.

### Approach

Work through `frontend/src/components/` in this priority order:
1. `components/projects/*` (ProjectDetailPage, SafetyTab, TeamTab, WorkTab, contract/*)
2. `components/daily-logs/*`, `components/inspections/*`, `components/hazards/*`
3. `components/workers/*`, `components/equipment/*`
4. `components/documents/*`, `components/toolbox-talks/*`
5. `components/auth/*` (login/signup — dark, minimal, KerfMark-anchored)
6. `components/landing/LandingPage.tsx` — **see `LandingPage.notes.md`**
7. Remaining pages

For each file:
- List all `<Card>`, table, and badge usages
- Convert cards that are "sections" to `<SbPanel>`
- Ensure all numerics are `.font-mono tabular-nums`
- Replace raw status string rendering with `<Badge variant="pass|fail|warn|info">`

### Edge cases — stop and ask Paul

These deserve a design conversation before you touch them:
- `components/voice-inspection/VoiceInspectionPage.tsx` — voice UI is its own pattern
- `components/shell/ChatPane.tsx` — chat bubble design is opinionated; Paul has the mock
- `components/onboarding/CompanyOnboarding.tsx` — onboarding flow tone
- Mobile views specifically (breakpoint="mobile" branches in AppShell) — Marco-persona, different ergonomics

Commit: `feat(design): Site Board — sweep across remaining pages`

---

## If you get stuck

1. **Ambiguity about a pattern:** pause, read `SITEBOARD_DESIGN.md` again. If still unclear, leave the screen unchanged and log it in `/docs/SITEBOARD_ROLLOUT_LOG.md`.
2. **Broken screen after your change:** revert that file, not the whole wave.
3. **Conflict with existing Tailwind classes:** the new primitives are self-contained; if a consumer was relying on a specific class that the new primitive doesn't emit, wrap don't rewrite.
4. **TypeScript error:** most likely a prop API changed. Check the ref file's prop signature.

## Done criteria per wave

**Wave 1 done:** every page in the app renders, nothing crashes, primitives are importable and work in isolation. Visual uplift visible to Paul.

**Wave 2 done:** Dashboard, ContractTab, InspectionList, AppShell look indistinguishable from the mocks at `reference_mocks/siteboard-contract.jsx`. Paul signs off.

**Wave 3 done:** full app walkthrough with Paul, no Site Board misses logged. Edge cases have their own tickets open.
