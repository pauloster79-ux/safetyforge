# Research: Variation / Change Order / Payment / Close-Out Mechanics

**Purpose:** Input for `docs/design/project-lifecycle-flow.md`. Focus on operational mechanics across US/UK/IE/AU/NZ/CA.
**Date:** 2026-04-17

---

## 1. Variation / Change Order Mechanics

### 1.1 Trigger threshold

No universal monetary threshold. Trigger is **scope change** — any instruction that alters contractor's obligations (what/when/how/to what standard). Contractual, not statutory.

Deemed-approval windows:
- **AIA**: contractor proceeding without objection on a CCD = deemed accepted in method, cost open
- **JCT cl 3.12**: oral instructions have no effect unless confirmed in writing within 7 days
- **NEC4 cl 62**: PM must reply to quotation within 2 weeks; silence may trigger acceptance
- **AS 4000**: 14 days typical for Superintendent response

### 1.2 How variations attach

**Universal**: amendment in place. Variations are numbered addenda incorporated by reference. Original contract stays live; variation adjusts sum, time, scope definitions. Supplemental agreements reserved for changes so large they effectively create new work.

### 1.3 Who signs

| Contract family | Signatures required |
|---|---|
| AIA G701 (CO) | Owner + Architect + Contractor |
| AIA G714 (CCD) | Owner + Architect only; Contractor signs later |
| JCT | Architect/CA issues instruction; Contractor doesn't sign acceptance; Employer signs at final account |
| NEC4 | PM issues; Contractor submits quote; PM accepts or instructs |
| AS 4000 | Superintendent issues; Principal + Contractor sign |
| NZS 3910 | Engineer issues; Principal + Contractor sign |
| CCDC 2 | Owner + Consultant + Contractor |
| Residential | Owner + Contractor only (consumer protection: written before work starts) |

### 1.4 Legal consequence of unsigned work (JURISDICTIONAL)

- **US**: Written CO clauses generally enforceable, but quantum meruit available (70-85% recovery typical) under waiver / course-of-dealing / unjust enrichment
- **UK**: Quantum meruit for work outside any express contract; narrow exception for waiver of written-instruction requirement
- **Australia**: Significantly curtailed by *Mann v Paterson Constructions* (HCA 2019) — contract on foot means contract rules; quantum meruit only post-termination
- **NZ**: Following Australian narrowing
- **Ireland**: Follows English common law
- **Canada**: Quantum meruit available; courts look at owner knowledge/acceptance
- **Residential (consumer protection statutes)**: Written variation required; unwritten variations may be non-recoverable entirely (NSW HBA, Victorian DBCA, QBCC, PA HICPA, NJ HIPA)

### 1.5 Builder Variance vs Customer Variance

Not a legal term — proprietary to Buildertrend and mirrors in some SaaS. But the concept is universal:
- Client-requested change → recoverable variation
- Latent conditions / design error → potentially recoverable CE
- Contractor error / productivity miss → builder-borne

Kerf can use this UX split but map internally to canonical concepts.

---

## 2. Progress Payment Mechanics

### 2.1 Content of claims

| Jurisdiction | Term | Core contents |
|---|---|---|
| US | Progress Payment / Payment Application | AIA G702 (application + architect cert) + G703 (SOV with % per line), stored materials, retainage calc |
| UK | Interim Application for Payment | Value of work + materials + variations + L&E, less payments, less retention; with supporting measure |
| AU | Progress Claim | Under SOP Acts: identify work, contract ref, claimed amount, state made under the Act |
| NZ | Payment Claim | CCA 2002: identify work, period, amount, calculation basis, statement under Act |
| Canada | Proper Invoice (ON) | Prescribed content under Construction Act s.6.1 |
| Ireland | Payment Claim Notice | CCA 2013 s.4: amount, period, calculation basis |

### 2.2 Schedule of Values structure

- 20-200 line items depending on project size
- Each line: description, scheduled value, work completed previous/this period, materials stored, total to date, %, balance, retention
- AIA G703 is de facto US standard
- **Line items are contractually binding once approved** — changes require a Change Order

### 2.3 Milestone vs measured progress

| Model | Used in |
|---|---|
| Measured % complete | Commercial globally |
| Milestone payments | Residential (AU HIA 5-6 fixed stages, QLD QBCC mandated) |
| Hybrid | Many mid-size (measured for main, milestone for deposit + completion) |

Australia's state domestic-building statutes prescribe progress payment structure for residential.

### 2.4 Retention

| Jurisdiction | Typical % | Release triggers | Notes |
|---|---|---|---|
| US federal | 10% reducing to 5% at 50% complete | Half at SC, balance at final | Some states escrow |
| US NY (Nov 2023) | **Capped at 5%** | 30 days from final approval; 1% monthly interest | Private contracts ≥$150k |
| US CA | 5% (public cap) | 60 days from completion | Prompt Payment Act |
| UK | 3-5% (1.5-2.5% after PC) | Half at PC, balance end DLP | Post-Carillion shift to retention bonds |
| AU | 5% up to cap | Half at PC, half after DLP | NSW/QLD require trust accounts |
| NZ | 5-10% | CCA Amendment Act 2015 — trust from 2017 | Criminal liability for misuse (2023) |
| Canada ON | 10% | 45-day lien period after pub of SC | Prompt payment cuts across |
| Ireland | 5-10% | Contract + CCA 2013 | |

Trend: held in trust (NZ, AU NSW/QLD, ON, proposed UK, US escrow statutes). Kerf should model retention as tracked liability with `held_in_trust` boolean per jurisdiction.

### 2.5 Security of Payment / Prompt Payment legislation

**These override contract terms — floors, not ceilings, apply automatically.**

| Jurisdiction | Statute | Key rights |
|---|---|---|
| UK | HGCRA 1996 | Stage payments; payment notice 5 days; pay-less notice to withhold; default payment notice if payer silent; right to suspend non-payment; adjudication any time |
| AU (all states) | State SoP Acts | Progress claim statutory right; respondent must issue schedule in 10-15 bus days or pay in full; adjudication 10 days |
| NZ | CCA 2002 | Default 20 wd payment; payment schedule requirement; adjudication 30 wd |
| Canada (ON, fed, AB, SK, NS, NB, MB) | Construction Act 2019 + equivalents | 28 days to pay proper invoice or 14 to dispute; 7-day pay-through to subs; adjudication via ODACC |
| Ireland | CCA 2013 | Payment claim notice; 30-day default; adjudication 28 days |
| US | No federal; **Prompt Payment Acts per state** | Interest penalties; retention release windows |

**Kerf implications**: statutes introduce unwaivable deadlines + automatic state transitions. Jurisdictional rules layer must encode: claim content requirements, response deadlines, adjudication triggers, pay-through obligations (Canada), suspension rights.

### 2.6 Disputed claims (universal pattern)

1. Payee submits claim
2. Payer issues payment schedule/notice with reasons
3. If no schedule in deadline: full claimed amount due (NZ/AU/UK via default notice)
4. Payee may refer to adjudication (UK/IE/AU/NZ/CA) — binding interim decision 28-45 days
5. Adjudicator's decision **binding until overturned** by arbitration/litigation
6. US: contract-specified DR (often arbitration); no statutory fast-track in most states

---

## 3. Close-Out Mechanics

### 3.1 Practical / Substantial Completion

| Term | Jurisdiction |
|---|---|
| Practical Completion | UK, AU, NZ, IE |
| Substantial Completion | US, Canada |
| Taking Over | NEC4 |

**Who certifies**: UK Architect/CA (JCT) or PM (NEC4); US Architect (AIA G704); AU Superintendent; NZ Engineer; CA Consultant; Residential = builder declaration + owner inspection + occupancy cert.

**Operational consequences**:
- Risk of damage → owner
- Insurance shifts
- LDs stop
- Retention half-release
- DLP starts
- Contractor off-site (except defects)

### 3.2 Punch list / Snagging / Defects list

| Term | Jurisdiction |
|---|---|
| Punch list | US, Canada |
| Snagging list | UK, IE |
| Defects list | AU, NZ |

Two classes: items required before PC (prevent certificate) vs items to be done in DLP.

Modern practice: rolling punch list throughout construction. Kerf model: defects as entity with location, description, category (cosmetic/functional/safety), status, due date, responsible party, closure evidence.

### 3.3 Final Account / Final Certificate

- UK: Final Certificate (JCT) / Final Payment Certificate (NEC4) — conclusive subject to 60-90 day challenge window
- US: G706 (Contractor's Affidavit of Payment of Debts and Claims) + G706A (lien release) + Final Certificate for Payment
- AU/NZ: Final Payment Schedule after DLP ends
- Canada: Certificate of Completion + holdback release
- IE: Final Certificate similar to UK

### 3.4 Defects Liability Period (DLP)

**Contractual**:
- UK/AU/NZ/IE: typically 12 months (6-24 range); NEC4: defects date + correction period
- US AIA §12.2.2: 1-year call-back / correction period
- Canada: 12 months warranty (CCDC)
- Residential: often 13 weeks non-structural (HIA), 6 years structural (AU NSW)

**Statutory warranties** (cannot be contracted away):
- UK: 6yr simple contract / 12yr deed; Defective Premises Act (now 30yr post-Grenfell for dwellings)
- AU: 6yr structural / 2yr non-structural (NSW); 10yr statutory limitation most states
- NZ: 10yr from completion (Building Act 2004)
- US: state-varies, typically 1-10yr statute of repose; implied warranty of habitability for residential
- Ireland: 6yr simple / 12yr seal
- Canada: province-varies; 2-7yr statutory, long-stop 10-15yr

### 3.5 "Completed" vs "Closed" distinction

**Completed** = SC/PC certificate issued, works in beneficial use.

**Closed** = all of:
- Final account settled
- All retention released
- DLP expired
- All punch list closed
- O&M manuals, as-builts, warranty docs handed over
- All invoices paid, no disputes outstanding
- Lien/claim windows expired (US/Canada)

Transition Completed → Closed can take 12-24 months. During this window, project in "warranty / post-completion" state with limited transactions (defect fixes, retention release, warranty claims).

### 3.6 Post-close deliverables (universal)

O&M manuals, as-built drawings, warranty docs, commissioning records, test certs (electrical/fire), spare parts, training records, Building Regs sign-off, occupancy certificate.

UK Building Safety Act 2022 imposes **Golden Thread** for higher-risk buildings — maintained post-occupancy.

---

## 4. Dispute and Suspension States

### 4.1 Distinct legal states

| State | Legal meaning | Effect |
|---|---|---|
| On hold | Informal pause by agreement | Work stops; clock may continue |
| Suspended | Formal exercise of statutory/contractual right | Work stops; specific legal consequences (EoT, cost recovery) |
| Terminated (convenience) | Contract ended without breach | Contractor paid for work + reasonable profit on balance |
| Terminated (cause/default) | Material breach | Damages claims, bond calls, lien actions possible |

### 4.2 Suspension triggers

- Non-payment: UK s.112 (7 days), AU SOP (after adjudication failure), NZ CCA s.24, AIA §9.7 (7+7 days)
- Breach by other party
- Force majeure
- Pending large variations (contractual renegotiation)
- Public-health / regulatory (COVID jurisprudence)

### 4.3 Termination rights

- UK JCT: Employer (cl 8.4), Contractor (cl 8.9), neutral causes (cl 8.11)
- US AIA A201: Owner for cause/insolvency; contractor for non-payment/stoppages/owner default
- AU/NZ: similar + SOP Act suspension rights
- Residential: cooling-off periods (5 bus days VIC/QLD, similar US home-solicitation)

### 4.4 Adjudication

Parallel state track. A project can be "Active + In Adjudication" — doesn't stop works unless a party also suspends.

---

## 5. Residential vs Commercial

### 5.1 Consumer protections (key statutes)

| Jurisdiction | Statute | Protections |
|---|---|---|
| US | State-by-state (PA HICPA, NJ HIPA, NY GBL 770, CA B&P §7159) | Mandatory written contract, 3-day rescission home-solicitation, licensing, bond |
| UK | Consumer Rights Act 2015 + Building Safety Act 2022 | Implied terms, unfair terms, 14-day cancellation distance contracts |
| AU | Domestic Building Contracts Act (VIC), Home Building Act (NSW), QBCC Act, ACL | Mandatory content, cooling-off, licensing, Home Warranty Insurance |
| NZ | Building Act 2004 + Consumer Guarantees Act | Implied warranties, 12-month post-completion warranty notice |
| Ireland | SGSS Act + EU consumer law | Similar implied terms |
| Canada | Provincial (ON Tarion, BC licensing) | Mandatory warranty coverage |

### 5.2 Deposit caps (residential)

| Jurisdiction | Cap |
|---|---|
| UK | No statutory; ≤25% industry norm |
| AU NSW | 10% (HBA s.8) |
| AU QLD | 10% (level 1), 5% (level 2), 20% (prefab exception) |
| AU VIC | 5% if ≥$20k; 10% if <$20k |
| US PA | 1/3 for contracts >$1,000 |
| US MD | 1/3 at signing |
| US CA | $1,000 or 10%, whichever less |
| NZ | No statutory; 10% norm |
| Canada ON | No statutory; Tarion up to $60k |

### 5.3 Residential lifecycle simplifications

Residential is simpler in form but more protected in substance:
- Usually no separate architect certifier
- Milestone payments rather than measured
- Cooling-off at formation
- Mandatory written variations (most)
- Mandatory warranty insurance (AU, parts of CA, UK NHBC)
- Occupancy certificate as closeout trigger
- Consumer dispute pathway (VCAT, NCAT, small claims)

---

## 6. Immutability Rules (CRITICAL for Kerf)

### 6.1 At quote acceptance (contract formation)

**MUST become immutable:**
- Contract sum (initial)
- Contract documents — hashed reference
- Contract dates (start, planned PC)
- Parties (principal, contractor, certifier)
- Retention regime (% and release rules)
- LD rate
- Payment terms/schedule
- Jurisdiction and applicable legislation

**Can still change (via variation only):** scope, sum, time, specifications

**Pattern**: snapshot contract into immutable `ContractVersion` node at acceptance; all subsequent modifications create `Variation` nodes linked to current version. Never mutate in place.

### 6.2 At each approved variation

**MUST become immutable:**
- Variation number (sequential, gap-free — auditors check)
- Variation sum
- Scope description
- Time impact
- Approval signatures and dates
- Attached instruction/CCD/CE

### 6.3 At each progress payment certification

**MUST become immutable:**
- Payment application/claim as submitted
- Payer's response (schedule, certificate, pay-less notice)
- % complete per SOV line at that moment
- Retention calculated and held
- Amount paid with payment date
- Pay-through records (Canada)

Why: SOP disputes turn on exactly what was claimed, when, response. Amending past claims is forgery. Corrections via new claim/credit note, not history edit.

### 6.4 At practical/substantial completion

**MUST become fixed:**
- PC/SC Certificate date (drives insurance, risk, LDs, DLP start, retention release, limitation clocks)
- Punch list snapshot at PC (DLP baseline)
- Half-retention release
- All variations prior to PC in "approved" or "rejected" state (none "in draft")
- Final completion date projection

### 6.5 At final account / final certificate

**MUST become immutable:**
- Final contract sum (contract + approved variations + claims - deductions)
- All progress payments reconciled
- Retention balance
- Final certificate date
- Defects closed evidence
- Closeout deliverables attached

### 6.6 At project close

**MUST become immutable:**
- Everything above + final retention release date, DLP expiry date, all invoice statuses, outstanding claims isolated

### 6.7 When can you go backwards?

Almost never, and only via audit-trailed reversal, not edit:

| Scenario | Kerf approach |
|---|---|
| PC certificate issued in error | "Revocation of PC" event with reason/timestamp/approver; original stays marked superseded |
| Final certificate challenged in statutory window (UK: 60-90 days) | Formal challenge event; project re-opens to "In Dispute (post-final)" |
| Retention released in error | Clawback claim tracked as new transaction |
| Progress claim wrong amount | New claim with correction |
| Variation approved incorrectly | Revocation variation (new number, negative value) |

**Pattern**: temporal invalidation, not deletion. `valid_from` / `valid_until` / `superseded_by`. Aligns with agentic-infrastructure playbook's temporal fact management and what SOP Acts + auditors expect.

### 6.8 State machine summary

```
Draft → Quoted → Accepted → Active →
  (Active loops: Variation, Progress Claim, Adjudication, Suspended, On Hold)
  → Practical Completion →
  Defects Liability Period →
  Final Account →
  Closed

Parallel tracks during Active:
  - Payments (Claim Submitted → Scheduled → Paid)
  - Variations (Requested → Approved/Rejected → Attached)
  - Disputes (Raised → Adjudicated/Settled → Resolved)
```

Every state transition = immutable event with actor, timestamp, supporting document. States can be revoked (new event) but never silently changed.

---

## 7. Jurisdictional rules-engine matrix

| Feature | US | UK | IE | AU | NZ | CA |
|---|---|---|---|---|---|---|
| Statutory payment right | State-level only | Yes (HGCRA 1996) | Yes (CCA 2013) | Yes (state SOP) | Yes (CCA 2002) | Yes (ON 2019 + fed + prov) |
| Adjudication | No (contract) | 28 days | 28 days | ~10 days | 30 wd | Via ODACC |
| Retention cap | State (NY 5%) | Contractual | Contractual | Contractual w/ trust | Trust from 2017 | Contractual 10% typical |
| Written variation required | Contract + residential | Yes JCT 3.12 | Yes | Yes | Yes | Yes |
| CCD / unilateral instruction | Yes AIA G714 | Limited JCT | Yes NEC | Yes AS | Yes NZS | Yes CCDC |
| Residential deposit cap | State-varies | None | None | State-varies (5-10%) | None | Province-varies |
| Cooling-off period | Varies 3-10 days | 14 days (distance) | EU rules | 5 bus days | 5 wd | Province-varies |
