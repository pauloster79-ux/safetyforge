# Handoff — Competitor Market Scan (US, Canada, UK, Europe)

**Date:** 2026-04-18
**From:** Lifecycle walkthrough session (persona-based state-machine design for project lifecycle)
**Purpose:** Conduct a proper competitor scan across US, Canada, UK, and the whole of Europe. Extend / replace fragmentary competitor content currently spread across multiple docs. Verify several unverified competitor citations that crept in during this session.

---

## TL;DR for the fresh session

1. **Read first, in this order** (each is self-contained):
   - `docs/PRODUCT_VISION.md` — what Kerf is (note new §3.14 Email-as-Client-Channel, and §6 principle #15 Operator-controls-transitions, both added today)
   - `docs/PRODUCT_STRATEGY.md` — current competitive positioning and market framing; competitor coverage begins around line 127
   - `docs/knowledge-graph/competitor-data-models.md` — existing data-model comparison (JobTread §1.2; comparison tables at end)
   - `docs/design/research/lifecycle-02-competitor-state-handling.md` — state-machine competitor research generated in the prior session. **Treat with skepticism — see §2 below.**
   - `docs/GTM_STRATEGY.md`, `docs/PRICING_STRATEGY.md`, `docs/MESSAGING_STRATEGY.html` — for positioning context
   - `memory/MEMORY.md` — jurisdiction scope (Wave 1 = US/CA/UK/IE/AU/NZ), product scope (full contractor platform, not safety-only)

2. **Deliverable:** a proper competitor scan for **US, Canada, UK, and all of Europe**, measured against Kerf's product vision. Single source of truth replacing fragmentary competitor references across multiple docs.

3. **Scope of product coverage:** safety, project management, estimating, daily reporting, financial management / job costing, scheduling, time tracking, sub compliance, quality, RFIs, client portals. Both point-tools and platforms.

4. **Method:** live documentation, product tour videos, pricing pages, case studies. Cite sources. Where details aren't publicly documented, say so — don't fill in plausible guesses.

---

## 1. What's already in research (baseline, trust)

Names that have appeared across `PRODUCT_STRATEGY.md`, `competitor-data-models.md`, and other strategic docs:

**North America:**
- **JobTread** — featured heavily. Residential / small commercial PM. Estimate-to-budget flow. ~$199/mo.
- **Procore** — enterprise PM. $30K+/yr.
- **Buildertrend** (merged with CoConstruct) — residential PM.
- **Handoff** — AI estimating. $25M funded.
- **Hardline** — voice capture. ~$2M.
- **Fieldwire** — PM.
- **SafetyCulture** — inspection checklist engine. 1.5M users globally (originated AU).
- **SALUS** — Canada provincial safety.

**Europe:**
- **PlanRadar** — documentation; Austria-based, claims 65+ country footprint.
- **Capmo** — Germany; basic AI.
- **Brickanta** — Sweden; enterprise pre-construction.

These are accepted as verified. Extend coverage rather than re-verify from scratch.

---

## 2. Names cited this session without verification — PRIORITY TO VALIDATE

These appeared in `docs/design/research/lifecycle-02-competitor-state-handling.md` with detailed state-machine descriptions, generated in-session. **Verify specifics against each product's live documentation before treating any claim as load-bearing.**

- **Knowify** — claimed states: Lead → Bidding → Out for Signature → Active → Pending Changes → Completed. Described as "clearest state machine of any researched product."
- **JobNimbus** — strong in roofing allegedly. Claimed stages: Lead / Estimating / Sold / In Production / Accounts Receivable / Completed + Lost. "Days In Status" counter claimed.
- **Contractor Foreman** — claimed Pending / In Progress / Completed at project level; Open / Estimating / Submitted / Approved / Completed at work-order level.
- **Houzz Pro** — claimed lead stages (New / Followed Up / Connected / Meeting Scheduled / Proposal Sent / Won) and proposal states with immutability rules on approved/paid/invoiced.
- **Jobber** — service trades. Claimed Quote states (Draft / Awaiting Response / Changes Requested / Approved / Converted / Archived) and Job states (Active / Late / Unscheduled / Action Required / Requires Invoicing / Archived).
- **ServiceTitan** — service trades. Claimed three-entity model (Appointment / Job / Project / Invoice) with posted-lock invoices and hold-at-every-layer.
- **ACC / Autodesk Build** — claimed thin Active + Archived model with first-class Budget Snapshots.
- **CMiC** — claimed enterprise ERP with fully customisable workflow engine per tenant.

The **aggregate claim** (SMB residential tools often skip first-class warranty states; service trades model warranty work as new jobs) is probably correct. The **granular state-name and enum details** are the risk — LLM-generated research frequently produces plausible-sounding specifics that aren't quite right for niche products.

---

## 3. Scope of scan

### Markets

- **US, Canada, UK, Ireland**
- **Germany, France, Netherlands, Belgium, Switzerland, Austria**
- **Nordics:** Sweden, Norway, Denmark, Finland
- **Southern Europe:** Spain, Italy, Portugal
- **Central/Eastern Europe:** Poland, Czechia (only if notable contractor tooling exists)
- Any other EU country with contractor tooling of scale

### Comparison axes (measured against Kerf's product vision)

1. **Scope of product** — which of {safety, PM, estimating, daily reporting, financial, scheduling, time, sub compliance, quality, RFIs, client portal} does the competitor cover? 
2. **Target market** — solo / small (≤20) / mid (21-100) / enterprise. Residential / commercial / industrial. Trade-specific or general.
3. **Architecture signals** — relational vs graph vs other. AI-native vs bolted-on. Voice / mobile first vs desktop-primary. Offline-first posture.
4. **Conversational/AI capability** — what does their agent / AI actually do? Intent-based tools, chat, voice, document extraction, knowledge-graph-like features.
5. **State / data model** — project lifecycle, contract acceptance, variation/change-order handling, completion, warranty, closed. Where observable.
6. **Pricing** — per-user, per-project, flat-tier. Entry price, typical mid-tier price, enterprise price.
7. **Jurisdictional support** — languages, regulatory coverage, currencies, regional data residency.
8. **Integration surface** — email, calendar, accounting (QuickBooks / Xero / Sage / local equivalents), supplier APIs, GC portals, document signing, drawing/BIM, survey hardware.
9. **Gaps vs Kerf vision** — what would a contractor lose switching from this tool to Kerf? What would they gain? Where does Kerf's vision (safety-first architecture, graph intelligence, voice-first, one-tool-not-six) produce meaningful differentiation versus this competitor?

---

## 4. Deliverable

### Primary output
- **New file:** `docs/research/competitor-market-scan-2026-04.md` — the full scan. Markdown tables plus per-competitor narrative profile.

### Integrations back into existing docs
- `docs/PRODUCT_STRATEGY.md` — rewrite the competitor section (currently from ~line 127) to reference the new scan as the source of truth; keep strategic framing, remove redundant competitor detail
- `docs/knowledge-graph/competitor-data-models.md` — extend to include any new entrants with interesting data-model decisions
- `docs/design/research/lifecycle-02-competitor-state-handling.md` — correct entries inline where specifics were wrong; explicitly flag any claim that couldn't be verified ("not publicly documented — inferred from X")

### Per-competitor profile structure

```markdown
## {Competitor Name}

**Market:** {US / UK / etc.}
**Target:** {solo / small / mid / enterprise}, {residential / commercial / ...}
**Pricing:** {entry – mid – enterprise}
**Product scope:** {safety | PM | estimating | ...}
**Verified:** {Y / partial / N — what was and wasn't verified}
**Sources:** {URLs + date accessed}

**1-paragraph summary.**

**Architecture signals:** ...
**Conversational/AI capability:** ...
**State / data model (where observable):** ...
**Integrations:** ...

**Kerf comparison:** {what Kerf does differently, what would be gained/lost by switching}
```

---

## 5. Method guardrails

- Live sources only — product docs, marketing pages, YouTube tour videos, case studies, Capterra / G2 reviews for user-facing state-machine behaviour, investor decks if public.
- Cite every non-obvious claim with a URL and date-of-access.
- If a claim cannot be verified from public sources, say **"not publicly documented"** — do not fill in plausible-sounding specifics.
- Screenshots of relevant UI can be saved to `docs/research/screenshots/` and referenced.
- Distinguish first-party claims (vendor marketing) from third-party assessment (analyst reports, independent reviews).

---

## 6. Out of scope

- Primary user research (interviews, surveys, focus groups) — separate effort
- Deep data-model reverse-engineering beyond what's publicly documented
- Pricing sensitivity analysis — a commercial exercise, not research
- Any recommendation on Kerf positioning, roadmap, or pricing — this is **observational research**, not strategy output
- AU, NZ, Middle East, Asia, Africa, LATAM — not in scope for this pass (prior research covers AU/NZ baseline; other regions deferred)

---

## 7. Open repo state

Modified files across multiple areas (backend services, frontend, design docs, product vision, memory). `git status` shows the full picture. **Do not commit — Paul commits.**

---

## Suggested opening prompt for the fresh session

> "Start the competitor market scan per `docs/workflow/handoff-2026-04-18-competitor-market-scan.md`. Begin with §2 (unverified names from the prior session) — those are the highest-priority to validate or correct, because they've already influenced a design decision. Then broaden to the full US / Canada / UK / Europe sweep per §3. Deliverable in §4. Cite every claim."
