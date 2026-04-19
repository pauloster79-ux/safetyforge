# Landing Page — Site Board (Dark) Spec

The landing page is marketing, not tool. It sells Kerf to Jake, Sarah, and Marco. Keep the tokens, expand the scale, allow a touch more motion. Still no slop.

## Constraints

- **Same tokens as the app.** `--sb-ink-*`, `--machine`, Plex Sans/Mono.
- **Dark only.** Page background `var(--sb-ink-0)` (#0d0e0c).
- **Container:** max-width 1240px, horizontal padding 24px mobile / 48px desktop.

## Hero

- **Eyebrow** — `font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--machine)]`, e.g. "SAFETY SOFTWARE FOR BUILDERS"
- **Headline** — `font-sans text-[56px] lg:text-[72px] leading-[1.02] font-medium`, max 2 lines. Body concrete-grey `#d4d7cf`, one key phrase in `var(--machine)` for emphasis (max 3 words yellow).
- **Subhead** — `text-[18px] leading-[1.4] text-muted-foreground`, max 320px wide
- **Primary CTA** — `<Button size="lg" variant="default">`. Single button. "Start a project" or similar.
- **Secondary** — ghost button with underline. "Watch a demo" or "See how it works".

## Proof strip

Row of 4-6 logos (customers) or stats (projects managed, hours logged, crews). Monospace numerics. Grey, not white. Muted. No grid card background — just a thin `--sb-hairline` above and below.

## Feature sections

Three sections, each is a persona story (Marco / Sarah / Jake). Structure per section:

- **Left:** `<SbPanel>` with a fake screenshot of the relevant app view. Not a real screenshot — an HTML-composed dashboard snippet using real tokens. 360×480 typical.
- **Right:** persona name, headline, body copy, 3-4 feature bullets with small machine-yellow check icons

Sections alternate left/right orientation. Gap 96px between sections.

## Trust section

- Brief section with 2-3 compliance logos (OSHA-related, but keep it minimal), 1 testimonial quote in large italic Plex Sans.
- No star ratings. No "trusted by" tropes.

## Closing CTA

- Single large heading: "Start building safer."
- One primary button.
- Nothing else.

## Footer

- `<KerfMark variant="full" />` top-left
- 3-column link list: Product, Company, Resources
- Small print row at bottom: © 2025 Kerf, Terms, Privacy
- `--sb-hairline` divider above the copyright row

## Motion

Allowed motion on the landing page (all `@media (prefers-reduced-motion: no-preference)`):

1. **Fade + rise on scroll** — sections fade in + translateY(12px→0) once they hit 30% viewport. 400ms ease-out.
2. **Hero headline** — staggered word reveal on mount. 60ms between words. 400ms per word.
3. **Feature screenshots** — very subtle 3D tilt on mouse move (±3° max). Disable on touch.
4. **Ticker** — the proof strip slowly scrolls horizontally (8px/sec) on mobile, static on desktop.

**Not allowed:**
- Parallax backgrounds
- Gradient animations
- Cursor-follow effects
- Confetti / particles / glowing orbs
- Marquee testimonials
- Video autoplay

## Components used

All components for the landing page come from the shared `components/ui/` library — Button, Card, SbPanel, KerfMark, Badge. The landing should compose these, not define its own primitives. If something genuinely only belongs on the landing (e.g. a feature-section layout), put it in `components/landing/` but make it thin.

## File target

`frontend/src/components/landing/LandingPage.tsx` currently 46KB. Expect to rewrite ~70% of it. Keep the routing integration (`useNavigate`, Clerk hooks) intact.
