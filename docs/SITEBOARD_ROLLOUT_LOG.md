# Site Board Rollout Log

Tracking decisions, deferrals, and findings as the Site Board design system rolls across the app. Source brief: `design_handoff_siteboard/CLAUDE_CODE_BRIEF.md`.

## Wave 1 — Foundation (2026-04-17)

### Completed

| Step | File(s) | Notes |
|------|---------|-------|
| 1.1 — Replace `index.css` | `frontend/src/index.css` | Full drop-in replacement with `SITEBOARD_TOKENS.css`. Adds `--sb-ink-*`, `--sb-hairline`, `--sb-plate-*`, type tokens, 8px scrollbar, hover-lift/row-tint/panel-beat/typing-dots animations. Light `:root` preserved for print. |
| 1.2 — Force dark mode | `frontend/index.html` | Set `<html lang="en" class="dark">` directly rather than wiring `next-themes` ThemeProvider. `next-themes` isn't currently wrapping the tree (only sonner consumes `useTheme`), so the static class is simpler and zero-flicker. Can be swapped for a ThemeProvider later if we need user-facing light toggle. |
| 1.3 — Upgrade primitives | `ui/button.tsx`, `ui/card.tsx`, `ui/badge.tsx`, `ui/table.tsx` | No props removed. Additions: Badge gains `pass/fail/warn/info` variants; Card gains `hoverLift` prop (default true). |
| 1.4 — New primitives | `ui/num-plate.tsx`, `ui/sb-panel.tsx`, `ui/kerf-mark.tsx`, `chat/typing-indicator.tsx` | All four added as copies of the handoff references. |
| 1.5 — Smoke test | `/`, `/login` | Landing + login render cleanly, no console errors, dark mode active (bg `#0d0e0c`, `html.dark`), machine yellow intact, calibrated `--muted-foreground` applied. |

### Verified tokens at runtime

```
html.className        = "dark"
body background       = rgb(13, 14, 12)  // --sb-ink-0
body color            = rgb(232, 233, 230)
--muted-foreground    = #a3a79c   (calibrated ↑ from #71766b)
--sb-ink-2            = #191b17
--sb-ink-4            = #2e312b
--sb-hairline         = rgba(255, 255, 255, 0.06)
--sb-plate-highlight  = rgba(255, 255, 255, 0.04)
--machine             = #F5B800
```

### Findings / deferrals

- **`LoginPage.tsx:194`** — The email/password submit button uses `bg-[var(--concrete-800)] hover:bg-[var(--concrete-700)]`. `--concrete-*` tokens aren't defined anywhere in the codebase (neither the old `index.css` nor the new tokens file). Result: button renders with transparent background and "Sign In" text is nearly invisible on the card surface. Pre-existing bug, not a Wave 1 regression. **Defer to Wave 3** when auth screens are touched.
- **Tailwind JIT + new utility classes** — `text-kicker`, `bg-sb-ink-*` etc. are defined in `@theme inline` but Tailwind only generates utilities that appear in source. They are currently unused (new primitives use arbitrary `bg-[var(--sb-ink-2)]` syntax which works regardless). Once Wave 2 pages start importing `NumPlate` / `SbPanel`, these utilities will materialise in the compiled CSS.
- **No primitives are wired into any page yet.** Wave 1 is foundation-only; expect zero visual change outside of the already-dark tokens calibration.

### Rules not yet applied (by design — Wave 2/3)

- No page is using `<SbPanel>` or `<NumPlate>` yet
- No `<KerfMark>` in the AppShell top bar
- Chat `<TypingIndicator>` not wired into `ChatPanel.tsx`
- Inspection/daily-log/hazard pages still use raw status strings rather than semantic `<Badge variant="pass|fail|warn">`

### Suggested commit

```
feat(design): Site Board foundation — tokens + primitives
```

Files touched:
- `frontend/src/index.css` (replaced)
- `frontend/index.html` (+`class="dark"`)
- `frontend/src/components/ui/button.tsx` (upgraded)
- `frontend/src/components/ui/card.tsx` (upgraded)
- `frontend/src/components/ui/badge.tsx` (upgraded, +`pass/fail/warn/info` variants)
- `frontend/src/components/ui/table.tsx` (upgraded)
- `frontend/src/components/ui/num-plate.tsx` (new)
- `frontend/src/components/ui/sb-panel.tsx` (new)
- `frontend/src/components/ui/kerf-mark.tsx` (new)
- `frontend/src/components/chat/typing-indicator.tsx` (new)
- `docs/SITEBOARD_ROLLOUT_LOG.md` (new)
