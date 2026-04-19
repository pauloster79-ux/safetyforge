# Research: Industry Contract Lifecycle Conventions

**Purpose:** Input for `docs/design/project-lifecycle-flow.md` (to be co-authored with Paul).
**Method:** Synthesis across AIA, ConsensusDocs, CCDC, JCT, NEC4, RIAI, AS 4000, AS 4902, ABIC, NZS 3910.
**Date:** 2026-04-17

---

## Universal Load-Bearing States

Every contract family recognises these states:

```
DRAFT → TENDER → AWARDED → COMMENCED → IN_PROGRESS
   → PRACTICAL_COMPLETION (a.k.a. Substantial Completion / Performance)
      → DEFECTS_LIABILITY (a.k.a. Rectification / Correction / DNP / Warranty)
         → FINAL_COMPLETION → CLOSED
```

Terminal branches from nearly any state: `SUSPENDED`, `TERMINATED`, `DISPUTED` (usually an overlay, not a replacement state).

---

## Three Universal Roles (named differently per family)

| Universal role | AIA | JCT | NEC4 | CCDC | AS 4000 | NZS 3910 (2023) | RIAI |
|---|---|---|---|---|---|---|---|
| **Owner/Principal** | Owner | Employer | Client | Owner | Principal | Principal | Employer |
| **Contract Administrator / Certifier** | Architect | Contract Administrator | Project Manager (+ Supervisor) | Consultant | Superintendent | Contract Administrator + Independent Certifier | Architect |
| **Contractor** | Contractor | Contractor | Contractor | Contractor | Contractor | Contractor | Contractor |

**Implication for Kerf:** model as abstract roles with per-jurisdiction concrete mappings. Transition permissions attach to abstract roles.

---

## Universal Lock Points

| Event | What gets locked |
|---|---|
| **Award** | Contract sum baseline, scope baseline, time baseline |
| **Practical/Substantial Completion** | LD clock stops; major retention release; warranty starts; risk-of-loss often transfers; contract sum frozen except for outstanding claims |
| **Final Certificate / Final Completion** | Contract sum final; release of all remaining retention; most claims extinguished (subject to limited exceptions) |

PC/SC is the single most important transition across all jurisdictions.

---

## Three Universal Change Mechanisms

| Type | Examples | Characteristics |
|------|----------|-----------------|
| **Mutual change** (both parties sign) | AIA CO, JCT Variation by quotation, NEC4 CE with accepted quote, CCDC CO, AS 4000 agreed variation | Adjusts contract sum/time; signed |
| **Unilateral directive** (owner/CA-side, contractor must proceed, price settled later) | AIA CCD, JCT AI without quotation, NEC4 PM's Instruction, CCDC CD, AS 4000 Superintendent's Direction | Protects scope flexibility; valuation per contract formula |
| **Minor / de minimis** (no cost/time impact) | AIA Minor Change, JCT clause 3.11 instruction, AS 4000 trivial directions | No CO required |

**Unsigned work rule (universal):** Work performed without any mechanism → contractor's risk. No automatic entitlement (though quantum meruit may apply in disputes).

---

## Per-Family Stage Summaries

### AIA (US)
Pre-award → Award → Commencement (Date of Commencement / NTP) → Construction (monthly G702/G703) → Substantial Completion (G704) → 1-year Correction Period → Final Completion (G706/G707) → Close-out.

Key clauses: A201 §9.8 (SC), §9.10 (Final), §7 (Changes), §12.2.2 (Correction), §15 (Disputes).

Variants: A102/A103 (Cost+/GMP), A133 (CM at-risk — two-phase with GMP Amendment), A401 (Subcontract).

### ConsensusDocs (US alternative)
Similar states; Owner often is certifier; explicit collaborative dispute ladder (Project Neutral, DRB, mediation, binding).

### CCDC (Canada)
Award → Commencement → Construction → **Substantial Performance** (statutory concept, starts lien period) → Total Performance / Ready-for-Takeover → 1-year warranty → Final payment after statutory lien period.

Ontario Construction Act (2019): mandatory prompt payment (28 days) + adjudication. Statutory 10% holdback separate from contractual retainage.

Variants: CCDC 2 (lump sum), CCDC 14 (D&B), CCDC 17 (trade), CCDC 19 (CM).

### JCT (UK)
Award → Possession of Site → Interim Certificates → Practical Completion → Rectification Period (6–12 months) → Certificate of Making Good → Final Certificate (conclusive per clause 1.10).

Variations via Architect's Instruction or Schedule 2 Quotation procedure. HGCRA 1996 mandatory Payment Notice / Pay Less Notice regime. Statutory adjudication right (28 days).

Variants: SBC, Intermediate (IC), Minor Works (MW), Design & Build (DB).

### NEC4 (UK — public infra)
Award → Access to Site → Starting Date → Completion (PM certifies) → Defects Date (~52 weeks) → Defects Certificate → Final Assessment (13 weeks after).

Distinctive: Early Warning System (clause 15), Compensation Events (clause 60) as unified mechanism for all changes, 8-week notice bar (61.3), Options A/B/C/D/E/F determine pricing model, not state model.

Variants: ECC, ECS (subcontract), PSC, TSC, SC.

### RIAI (Ireland)
Award → Commencement → Monthly Interim Certificates → Practical Completion → 12-month DLP → Final Certificate.

Public Works Contracts (PWC) are separate mandatory framework for all public Irish projects — fixed price, Employer-risk-heavy.

Construction Contracts Act 2013 IE: adjudication right + payment claim/response mechanism (HGCRA equivalent).

### AS 4000 (Australia — construct only)
Award → Commencement → Monthly Progress Claims → Practical Completion → 12-month DLP → Final Certificate (conclusive per clause 37.4).

Superintendent role (not Architect). State-by-state Security of Payment Acts (NSW, VIC, QLD, WA, SA, TAS, ACT, NT) with slightly different regimes — critical for Kerf to be state-aware.

AS 4902: Design & Construct variant. AS 2124 (1992): legacy, still in some gov contracts.

### ABIC (Australia — private/architect-administered)
Similar to AS 4000 but Architect is certifier. Commonly for high-end residential. Consumer-friendlier.

### NZS 3910 (New Zealand — 2023 edition)
Award → Commencement → Monthly Payment Claims → Practical Completion → Defects Notification Period (12 months, renamed from DLP) → Final Completion.

2023 edition split Engineer role into **Contract Administrator** (Principal's agent) + **Independent Certifier** (impartial). Kerf should model these as two distinct roles with distinct permissions.

CCA 2002 + Retentions Regime (trust account for retentions). CCA statutory adjudication.

---

## Jurisdictional Nuances (the variation layer)

| Concern | Jurisdictions affected | Impact |
|---------|------------------------|--------|
| **Statutory adjudication** | UK (HGCRA), IE (CCA 2013), AU (state SoP Acts), NZ (CCA 2002), Ontario (Construction Act 2019). US: no federal — state-by-state. | Must be modelled per-jurisdiction |
| **Retention trust** | NZ (CCA 2017/2023), Ontario (Construction Act holdback trust) | Separate bank account required |
| **Statutory holdback** | Canada: 10% mandated by provincial Lien Acts. Separate from contractual retainage. Release tied to lien period. | Adds a state overlay |
| **Substantial Completion as legal trigger** | Canada: statutory definition, triggers lien period. UK/AU/NZ: contractual. US: mostly contractual. | Affects auto-state-transition logic |
| **Certifier impartiality** | NZS 3910:2023 splits role. Others maintain single certifier with contractual impartiality duty. | Kerf UI should support both |
| **Payment notice regime** | UK/IE mandatory. Missing = applied sum payable. | Deadline-critical |
| **Notice bars** | NEC4: 8-week bar on CEs. Missing = loss of entitlement. | Strict, auditable |
| **Dispute pathway** | UK/AU/NZ/IE/ON: statutory adjudication any time. US: mediation → arbitration/litigation. | State machine varies |

---

## Design Implications for Kerf's State Machine

1. **Abstract state model** using universal states (DRAFT through CLOSED). Each state has metadata: `is_locked`, `can_vary`, `can_invoice`, `retention_release_pct`.

2. **Role abstraction layer**. Permissions attach to abstract roles; concrete role names render per-jurisdiction.

3. **Change Order as first-class entity** with three subtypes (mutual / unilateral-directive / minor) and a jurisdictional valuation strategy.

4. **Overlays, not states, for:**
   - Defects/Rectification/DNP period (runs parallel to post-PC states, doesn't replace close-out)
   - Disputes (can overlay any active state)
   - Statutory adjudication (a process overlay, not a state)

5. **Jurisdiction-specific hooks:**
   - Statutory holdback calculation (Canada)
   - Retention trust requirements (NZ, Ontario)
   - Payment notice deadlines (UK, IE)
   - Notice-bar enforcement (NEC4)
   - Adjudication pathways (UK, IE, AU per state, NZ, ON)

6. **Provenance on every lock-point transition** — record actor (human/agent), timestamp, contract citation reference (e.g., "AIA A201 §9.8"), effective date. Legally load-bearing.

7. **Practical/Substantial Completion is the pivot transition.** Every family models it. Full audit-trail provenance and citation to governing clause.

8. **Do not model AS 4000 vs AIA as separate state machines.** Universal model + role abstraction + overlay system handles variation. Jurisdictional differences are in captured data, transition authority, and side-effects — not in fundamental states.
