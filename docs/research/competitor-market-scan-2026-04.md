# Competitor Market Scan — US, Canada, UK, and Europe

**Date of scan:** 2026-04-18
**Scope:** US, Canada, UK, Ireland, and all of Europe
**Purpose:** Single source of truth on the construction software landscape, measured against Kerf's product vision, to inform competitive positioning and strategy.
**Status:** Observational research. This document does not recommend strategy — it provides the map.

---

## TL;DR

The construction software market is more crowded than Kerf's existing strategy docs suggest. The §2 verification pass surfaced a dense tier of **SMB-focused contractor platforms** (Knowify, JobNimbus, Contractor Foreman, Houzz Pro, Jobber, ServiceTitan) that the earlier `PRODUCT_STRATEGY.md` §3.4 summary compressed into "point solutions." Europe has a similarly dense landscape, with several national champions (Bygglet SE, Batappli FR, HERO DE, Dalux DK, LetsBuild BE/FR, Access Coins UK) and a Nordic consolidator (SmartCraft ASA) that is buying market share across Sweden, Norway, and Finland.

Five strategic observations drop out of this scan:

1. **Kerf's "graph-based, conversational-first, safety-first, global" positioning remains genuinely distinctive.** No competitor has all four. But the individual pieces are being built by different players, and the gap is narrower than the strategy doc implied.
2. **Conversational AI is no longer Kerf-exclusive in enterprise.** Access Coins Evo (UK) shipped a native "Copilot" conversational assistant in 2025-2026. Autodesk, Procore, and CMiC are all adding AI assistants. The moat is not conversation itself — it is conversation **over a connected graph that spans safety + operations + finance**.
3. **Every "AI estimating" competitor is catalog-trained, not contractor-trained.** Handoff, Togal, Kreo, BuildGets learn from aggregate data (supplier APIs, historical bids across all users, market rates). Kerf's vision of learning from the **contractor's own completed jobs** — labour productivity, panel-upgrade averages, rate patterns — is not matched by any product found in this scan.
4. **Contract structure advisory is a gap in the market.** AI contract tools (Document Crunch, Mastt AI, Sirion) review existing contracts for risk. Nobody advises a contractor on what to put in a payment schedule, how to structure assumptions and exclusions, or what retention percentage to use for this job type in this jurisdiction. This is an unclaimed territory.
5. **Europe is structurally more fragmented than the strategy doc assumes.** There is no "JobTread for Europe" — there is a JobTread for France (Batappli), a JobTread for Germany (HERO/plancraft/WINWORKER), a JobTread for Sweden (Bygglet), and a JobTread for Spain (Presto/Arquímedes). None cross borders. A cross-jurisdiction platform is an actual whitespace, not just a narrative.

---

## Methodology

- **Sources:** vendor help centres (help.getjobber.com, help.servicetitan.com, kb.contractorforeman.com, pro.houzz.com, support.jobnimbus.com, knowify.zendesk.com, buildertrend.com/help-article, jobtread.com, handoff.ai, smartcraft.com, dalux.com, letsbuild.com, coins-global.com, eque2.co.uk, sitesamurai.co.uk), vendor marketing pages, independent comparison sites (G2, Capterra, SoftwareWorld, SelectHub, SoftwareAdvice), industry press, investor decks (where public), and national-language product pages (DE, FR, IT, ES, PL).
- **Citations:** every non-obvious claim has a URL and date-of-access. Where a claim could not be verified from a primary source, it is flagged **"not publicly documented"**.
- **Vendor marketing vs third-party assessment:** vendor-sourced claims are marked as such; third-party capability claims (G2, Capterra) are preferred for state-machine and UX behaviour.
- **Out of scope:** AU, NZ, Middle East, Asia, Africa, LATAM. Pricing-sensitivity analysis. Roadmap recommendations.
- **Date of access for all URLs:** 2026-04-18 unless otherwise noted.

---

## 1. Landscape Map

Competitors are clustered on two axes: **product scope breadth** (horizontal — how many of the 11 contractor process areas they cover) and **target segment** (vertical — solo through enterprise).

### The 11 process areas

safety • PM • estimating • daily reporting • financial / job costing • scheduling • time tracking • sub compliance • quality / punch • RFIs / submittals • client portal / comms

### Where competitors cluster

| | **Solo / micro (1-5)** | **Small (6-20)** | **Mid (21-100)** | **Enterprise (100+)** |
|---|---|---|---|---|
| **Safety-only (1-2 areas)** | SafetyCulture (free tier), HandsHQ entry | swiftRMS, Safesite | HammerTech, SALUS (provincial) | HammerTech, ISNetworld, Avetta |
| **Point-tool (1-3 areas)** | Raken entry, CompanyCam, ClockShark, Jobber entry | Raken, Busybusy, ExakTime, Fieldwire, Jobber | Fieldwire, PlanRadar, SafetyCulture mid | ACC Build (single module), Procore single product |
| **Narrow platform (3-5 areas)** | Houzz Pro solo, Contractor Foreman solo | Contractor Foreman, Houzz Pro, Knowify, JobNimbus, Jobber Connect, Projul, Bolster, Batappli, HERO | Knowify, JobNimbus, Buildertrend, JobTread, HERO, WINWORKER, plancraft, Bygglet | — |
| **Broad platform (6-9 areas)** | — | Buildertrend entry, JobTread entry | **JobTread, Buildertrend, ServiceTitan, Dalux, LetsBuild, Site Samurai** | ServiceTitan (FS), Dalux, PlanRadar enterprise |
| **Full ERP (9-11 areas)** | — | — | Eque2, Access Coins mid, CMiC mid | **Procore, ACC Build, CMiC, Access Coins Evo, Viewpoint/Trimble, Sage 300 CRE, TeamSystem, COINS** |

### Where Kerf sits

**Target:** Small → Mid (1-100 employees) — the row where contractors outgrow point tools but cannot afford Procore/ACC/CMiC.

**Scope:** Broad platform → Full ERP ambition (safety + operations + financial + estimating + quality + scheduling + subs + RFIs + client portal). The only competitors in the "Broad platform / Small-Mid" cell today are **JobTread, Buildertrend, ServiceTitan, Dalux, LetsBuild, Site Samurai** — and none are graph-based, conversational-first, or safety-first.

**Entry wedge:** Safety (bottom row). Crosses diagonally up through operations toward full platform.

---

## 2. Category Synthesis

### Category A — Enterprise GC Platforms

| Competitor | HQ | Price | Product shape |
|---|---|---|---|
| **Procore** | US | ~$30K+/yr | Full platform, 100+ modules. Purpose-built for GCs. |
| **Autodesk Construction Cloud (ACC / Autodesk Build)** | US | Enterprise quote | Full platform. Strong Cost Management (Budget Snapshots, released Dec 2024). Thin project state model (Active/Archived). |
| **CMiC** | Canada (Toronto) | Enterprise quote | Single Database ERP. Fully customisable workflow engine. PMI-style marketing narrative (Initiation → Planning → Execution → Monitoring/Control → Closeout) — but out-of-box state enum depends on tenant configuration, not a hardcoded machine. |
| **Viewpoint / Trimble Construction One** | US | Enterprise | ERP + field. Strong in heavy civil. |
| **Sage 300 Construction and Real Estate** | US | Enterprise | Accounting-led ERP. Incumbent for larger US contractors. |
| **TeamSystem Construction** | Italy | Enterprise | Italian enterprise ERP for larger firms. |
| **Access Coins Evo** | UK | Enterprise | UK+IE construction ERP. **Native Copilot conversational assistant, Feed proactive alerts, Analytics dashboards** — most mature AI layer in European enterprise construction ERP. |
| **COINS (original Construction Industry Solutions)** | UK | Enterprise | UK/IE enterprise. Predates Access Coins Evo. |
| **Causeway Technologies** | UK | Enterprise | Acquired LetsBuild in Dec 2025 — extends reach into BE/FR/NL/LU. |

**Kerf overlap:** None of these target the 1-100 employee segment at Kerf price points. They are sources of **downmarket pressure** (Procore constantly trying to move down) rather than direct competitors. Access Coins Evo's Copilot is the first non-US enterprise to ship a conversational AI layer — worth monitoring, but their target (UK/IE enterprise GCs) does not overlap Kerf's SMB segment.

**Gap vs Kerf:** All are relational. None is safety-first. None operates in multiple languages as a first-class concern. None has graph-based rule encoding. All price out the Kerf target segment.

### Category B — SMB Residential & General Contractor Platforms (US)

| Competitor | Price | Target | Key capabilities |
|---|---|---|---|
| **JobTread** | ~$199/mo | Residential GC | Strong estimate-to-budget. Cost Catalog (contractor builds). Workflow automations (2025). Customer portal. QuickBooks sync. |
| **Buildertrend** (with CoConstruct) | ~$99-499/mo | Residential GC | Leads + estimates + schedules + client portal + daily logs + warranty. Third-party AI integrations for proposal formatting. |
| **Houzz Pro** | ~$99-399/mo | Residential designers + contractors | 6-stage lead pipeline (New/Followed Up/Connected/Meeting Scheduled/Proposal Sent/Won). 8-state proposal machine with strict immutability on Approved/Paid/Invoiced. Snooze-lead action. |
| **Knowify** | ~$149-349/mo | Small-mid trade contractors | Contract state machine (Lead/Bidding/Out for Signature/Active/Pending Changes/Rejected/Closed). Cost templates (contractor builds). QuickBooks 2-way sync. |
| **Contractor Foreman** | ~$49-249/mo | Small-mid general contractors | Broad feature checklist (60+ modules). Thin state model (Pending/In Progress/Completed at project; Open/Estimating/Submitted/Approved/Completed at work-order). |
| **JobNimbus** | ~$30-70/user/mo | Contractors (strong in roofing) | Fixed 6-stage pipeline (Lead/Estimating/Sold/In Production/Accounts Receivable/Completed + Lost at any point). Days-in-Status counter. Customisable sub-statuses within stages. |
| **Projul** | ~$4,788+/yr | Small contractors | Mobile-first. 1-2 week deployment. Broader than Fieldwire. |
| **Bolster** | Varies | Residential builders | Sales-focused. Competes with JobTread. |

**Kerf overlap:** This is the **most direct competitive tier**. These are the tools a 15-person electrical sub or a 45-person residential GC would shortlist today. JobTread and Buildertrend are the entrenched incumbents; Knowify is the best match for Kerf's trade-contractor persona (Sarah Chen).

**Gap vs Kerf:**
- **No safety.** None of these ship safety inspections, OSHA 300, certification tracking, or toolbox talks as core. They may integrate with a safety point tool.
- **No conversational-first interface.** All are form-heavy. Houzz Pro has a chatbot for lead qualification; none has a general-purpose agent.
- **Catalog-based learning, not contractor-trained.** JobTread, Knowify, Buildertrend all rely on the contractor manually building a cost library and referencing history. Kerf's vision of auto-derived learning (learned-pattern prompting from the contractor's own past jobs) is **not matched** by any product in this tier.
- **Relational architecture.** No knowledge graph. Rules live in application code or user-defined workflows.
- **US-locked.** JobTread, Knowify, Contractor Foreman, JobNimbus are US-only. Buildertrend has UK/AU presence but product is US-shaped.

### Category C — Service Trades Platforms

| Competitor | Price | Target | Key capabilities |
|---|---|---|---|
| **ServiceTitan** | Enterprise-leaning | Service trades + emerging new construction | 4-entity model (Appointment/Job/Project/Invoice). Invoice posted-lock. Appointment Hold is state-restricted. |
| **Jobber** | $35-249/mo | Small service businesses | Quote 6-state (Draft/Awaiting Response/Changes Requested/Approved/Converted/Archived). Job 6-state (Active/Late/Unscheduled/Action Required/Requires Invoicing/Archived). Invoice 5-state. |
| **Housecall Pro** | ~$49-249/mo | Small service businesses | Dispatch, scheduling, invoicing. |

**Kerf overlap:** Partial. Some Kerf trade-contractor personas (Jake Torres — solo electrician) might evaluate Jobber. But service trades model doesn't fit commercial construction or large residential jobs. ServiceTitan is pushing into project-based work but remains appointment-rooted.

**Gap vs Kerf:** Same list as Category B, plus: no project lifecycle (estimate → schedule → track → close), no construction-specific safety, no WorkItem abstraction.

### Category D — Safety-Only Platforms

| Competitor | HQ | Price | Shape |
|---|---|---|---|
| **SafetyCulture (iAuditor)** | AU | $0-34/user/mo + enterprise | Horizontal across 50 industries. 1.5M users globally. Checklist engine, not construction-specific. No graph, no financial link. |
| **Safesite** | US | $0-$240/mo | Construction safety. Thin. |
| **HandsHQ** | UK | ~£20-60/user/mo | UK RAMS (Risk Assessment Method Statements) document generator. |
| **swiftRMS** | UK | ~£24-60/user/mo | UK RAMS alternative to HandsHQ. |
| **HammerTech** | AU/global | Enterprise-leaning | Construction-specific EHS. Integrates with Procore. |
| **SALUS** | Canada | SMB-enterprise | Provincial OHS compliance. Canadian specialty. |
| **Safeti** | UK | SMB | UK H&S consultancy + software. |

**Kerf overlap:** Direct competitors for the entry wedge (SafetyCulture, Safesite at SMB; HammerTech at mid-large). SafetyCulture is the global safety leader but has no construction depth — it's a checklist engine that runs horizontally across 50 industries (hospitality, mining, healthcare). Kerf's safety is construction-specific with OSHA traversal and auto-generation.

**Gap vs Kerf:** Safety only. No operations expansion. No estimating, daily logs (beyond inspections), time, quality, subs, RFIs, financial. They cannot become a contractor's one tool.

### Category E — AI Estimating & Voice Startups

| Competitor | HQ | Funding | Learning model |
|---|---|---|---|
| **Handoff AI** | US | $25M+ | Trained on 100K+ completed estimates + 60M+ SKUs. Home Depot/Lowe's/regional supplier pricing. ZIP-based labour rates. **Aggregate catalog-trained**, not contractor-trained. |
| **Hardline** | US | $2M pre-seed | Voice capture from phone calls + site walks. Real-time transcription, task extraction. Pushes to Procore/Fieldwire. Documentation layer, not platform. |
| **Togal.ai** | US | Series A | AI takeoff from drawings. |
| **Kreo** | UK/EU | Series | AI takeoff + estimating. |
| **Renalto** | US | Very early | Voice → proposals. |
| **BuildGets** | ES | Early | AI for Spanish BC3 estimates + PDF conversion. |
| **Brickanta** | SE | $8M seed | Hundreds of construction-specific AI agents for pre-construction. Enterprise only. |

**Kerf overlap:** Handoff is the closest direct AI-platform competitor for the SMB segment, though residential-only and US-only. Hardline validates voice-first but is a layer on top of Procore/Fieldwire, not a platform. Brickanta is architecturally sophisticated but enterprise + pre-construction only.

**Gap vs Kerf (critical finding):**
- Every product in this category learns from **aggregate / market data**, not from the **individual contractor's own history**.
- Handoff's database is impressive (60M SKUs) but it is the same database for every user. A contractor in Phoenix and a contractor in Dallas get different regional prices from the same catalog — but both contractors' actual past-job performance (their specific crew productivity, their supplier relationships, their rate patterns) is not the basis for future estimates.
- Kerf's vision — "after 10 jobs this is more accurate than any catalog" — is genuinely unclaimed territory in the AI estimating space.
- None does conversational-first voice with real-time WorkItem extraction on a site walk. Handoff has "Audio-to-Docs" batch voice (record then process). Hardline captures passively. Renalto is the closest but early.

### Category F — Daily Log, Field, Photo Point Tools

| Competitor | HQ | Price | Shape |
|---|---|---|---|
| **Raken** | US | $15-49/user/mo | Daily logs, time, photos. Widely adopted. |
| **CompanyCam** | US | $24-37/user/mo | Photos with GPS + project context. |
| **Fieldwire** (by Hilti) | US/UK/DE | $0-94/user/mo | Tasks, drawings, daily logs. Owned by Hilti (Liechtenstein-based tool manufacturer). |
| **PlanRadar** | AT | ~€30-100/user/mo | Inspections, defects, documentation. 65+ countries, strong EU footprint. |
| **Dalux Field** | DK | Varies | Snagging + issue capture. Part of Dalux platform. |
| **LetsBuild (LB Aproplan + LB Geniebelt)** | BE | €30-80/user/mo | Quality/safety/planning. 10K active users in 35+ countries. Acquired by Causeway Dec 2025. |

**Kerf overlap:** Direct competitors for the daily-log expansion (Phase 2 of Kerf's roadmap). Raken is the incumbent for US contractors. PlanRadar is the EU equivalent. LetsBuild is strong in Benelux + France.

**Gap vs Kerf:** Single-purpose or narrow platform. No estimating, no financial, no safety depth. PlanRadar's 65+ country footprint is impressive but product is documentation-first, not operations-first. LetsBuild/Causeway is becoming a pan-European player via acquisitions but is still snagging-and-tracking, not a full platform.

### Category G — Time Tracking

| Competitor | Price | Shape |
|---|---|---|
| **ClockShark** | $40/mo + $9-11/user | Construction time tracking, GPS. |
| **Busybusy** | Free-$10/user | Construction time tracking. |
| **ExakTime** | $9/user | Construction time tracking + integrations. |
| **CrewTracks** | Varies | Mobile-first crew time. |

**Kerf overlap:** Phase 2 add-on market. Kerf price is $4-6/worker — undercuts standalone tools.

**Gap vs Kerf:** Time only. No connection to safety (fatigue analysis), no auto-derived job costing, no estimate-to-actual comparison.

### Category H — UK-Specific Commercial Contractor Tools

| Competitor | Product focus | UK-specific |
|---|---|---|
| **Site Samurai** | Full SMB platform | CIS deduction management, NEC4/JCT applications for payment, subcontractor portal, Xero integration |
| **Eque2** | SME ERP — 25+ years | Construction Manager (Sage/Xero) + EVision (Dynamics 365) |
| **Integrity Software** (Evolution Mx) | Accounting + job costing | RCT-compliant (Ireland) |
| **Access Coins Evo** | Full ERP + AI | Native Copilot conversational assistant, Feed alerts, Analytics |
| **Causeway Technologies** | Enterprise | Now owns LetsBuild (BE) for EU field expansion |

**Kerf overlap:** UK SMB is Kerf's wave-1 target market. Site Samurai is the most directly comparable UK-SMB product. Eque2 is more accounting-led.

**Gap vs Kerf:** No safety depth. No graph. No conversational-first except Access Coins Evo (enterprise). No AI learning from contractor history. No multi-jurisdiction — all UK-locked.

### Category I — European National-Champion SMB Platforms

| Country | Competitor | Shape |
|---|---|---|
| **Germany (Handwerker segment)** | HERO Software, WINWORKER, plancraft, pds, openHandwerk, Lexware handwerk | Trade-contractor focus. Cost calculation (Kalkulation), order management (Auftragsverwaltung), site planning. Strong German-language products. None is English-international. |
| **France (BTP segment)** | Batappli, EBP Bâtiment, Costructor, ProGBat (31K users), Obat, Lio, Hemea | 2026 French e-invoicing compliance is a forcing function. Quote/invoice-centric. Retenue de garantie (retention), sous-traitance (subcontracting), factures de situation (progress invoices) are standard. |
| **Nordics** | Dalux (DK, 140 countries, BIM+field+FM), SmartCraft group — **Bygglet (SE, 75K users), HomeRun (FI), Coredination (SE)**. 189K users total across SmartCraft. | Dalux is BIM-led; SmartCraft is consolidated SME platform play. |
| **Spain** | Presto (RIB Spain, BIM-oriented cost + budget), Arquímedes (CYPE, budgets + measurements + certifications), BuildGets (AI for BC3) | Technical/BIM-heavy. Presto vs Arquímedes is the dominant Spanish market debate. |
| **Italy** | TeamSystem Construction (enterprise), MyAEDES, Edison (exeprogetti), Cantieri Intelligenti 4.0, ERGO Mobile Enterprise | Fragmented. Cantieri documentation is the common thread. |
| **Benelux** | LetsBuild (BE, now Causeway), Vertuoza (BE), Build-Software (NL/BE) | Field management + quality heavy. |
| **Poland** | Norma, Winbud Kosztorys, Connecto, PROGPOL | Cost estimation (kosztorys) heavy. Older desktop-style products. No AI, no conversational, no mobile-first. |

**Kerf overlap:** None of these cross borders. Each is a national champion in a specific regulatory and language environment. **The European market is genuinely fragmented.**

**Gap vs Kerf:**
- All relational.
- All single-language (except Dalux and LetsBuild which ship in multiple languages but cover narrow functionality — snagging, field).
- None has AI-native architecture.
- None covers safety as first-class (in Germany, safety is a separate specialism; in France, QHSE tooling is separate; in UK, HandsHQ/swiftRMS are separate RAMS tools).
- None connects safety to financial outcomes.
- **Cross-jurisdiction is genuine whitespace.** A contractor in Madrid using Presto and a contractor in Munich using HERO are running fundamentally different software stacks. A pan-European graph-based platform does not exist.

---

## 3. Threat Assessment — against Kerf's 9 Moat Layers

Rated from the attacker's perspective: which moat layers does each competitor threaten, and how soon?

**Legend:**
- ⚫ Direct threat to this moat layer (credibly can match)
- ⚪ Partial threat (can match in a specific sub-segment)
- — No threat

| Competitor | 1 Graph arch | 2 Safety-first | 3 Conv memory | 4 Cross-feature | 5 Global arch | 6 Multilingual | 7 WhatsApp | 8 Workflow embed | 9 GC/sub network |
|---|---|---|---|---|---|---|---|---|---|
| **Procore** | — | — | — | ⚫ | ⚪ | ⚪ | — | ⚫ | ⚫ |
| **ACC / Autodesk Build** | — | — | — | ⚫ | ⚪ | ⚪ | — | ⚫ | ⚪ |
| **Access Coins Evo** | — | — | ⚪ | ⚫ | — | — | — | ⚫ | — |
| **CMiC** | — | — | — | ⚫ | — | — | — | ⚫ | — |
| **JobTread** | — | — | — | ⚪ | — | — | — | ⚪ | — |
| **Buildertrend** | — | — | — | ⚪ | — | — | — | ⚫ | ⚪ |
| **Knowify** | — | — | — | ⚪ | — | — | — | ⚪ | — |
| **JobNimbus** | — | — | — | ⚪ | — | — | — | ⚪ | — |
| **Houzz Pro** | — | — | — | ⚪ | — | — | — | ⚪ | — |
| **ServiceTitan** | — | — | — | ⚫ | — | — | — | ⚫ | ⚪ |
| **Handoff AI** | — | — | — | — | — | — | — | — | — |
| **Hardline** | — | — | ⚪ | — | — | — | — | — | — |
| **SafetyCulture** | — | ⚪ | — | — | ⚫ | ⚫ | — | ⚪ | — |
| **HammerTech** | — | ⚪ | — | — | ⚪ | — | — | ⚪ | ⚪ |
| **PlanRadar** | — | — | — | — | ⚫ | ⚫ | — | ⚪ | — |
| **LetsBuild / Causeway** | — | — | — | ⚪ | ⚪ | ⚪ | — | ⚪ | — |
| **Dalux** | — | — | — | ⚪ | ⚫ | ⚫ | — | ⚪ | — |
| **SmartCraft group (Bygglet etc.)** | — | — | — | ⚫ | ⚪ | ⚫ | — | ⚫ | — |
| **Brickanta** | — | — | — | — | ⚪ | ⚪ | — | — | — |

### Reading the matrix

- **No competitor threatens Layer 1 (Graph architecture).** All are relational. This is Kerf's deepest structural moat.
- **No competitor threatens Layer 2 (Safety-first architecture).** Even SafetyCulture is horizontal across 50 industries, not construction-deep. This is the second-deepest structural moat.
- **No competitor threatens Layer 3 (Conversation memory across the graph).** Hardline has conversation capture but not graph-linked memory. Access Coins Copilot is new; depth unknown.
- **Layer 4 (Cross-feature data network) is threatened by enterprise players** — Procore, ACC, CMiC, Access Coins already connect modules on a relational backbone. They cannot do it with graph-level richness, but for contractors who do not need regulatory traversal, the functional difference is not always visible.
- **Layer 5 (Global architecture) is Kerf's biggest exposure.** SafetyCulture (AU → global, 1.5M users), PlanRadar (AT → 65+ countries), Dalux (DK → 140+ countries) have proven cross-border deployment at scale. They are not graph-based, but they have done the operational and regulatory work of shipping across jurisdictions. **Kerf's "inherently global architecture" is true as a claim; the operational reality of supporting 20+ jurisdictions with regulatory encoding, language review, and local compliance is unproven.**
- **Layer 6 (Multilingual) is partially claimed by SafetyCulture, PlanRadar, Dalux, Bygglet (Nordic multi-country), Brickanta.** Kerf's advantage is conversational interface in language, not just static UI translation.
- **Layer 7 (WhatsApp distribution) is Kerf-exclusive.** No competitor found has WhatsApp as a crew-side channel.
- **Layer 8 (Workflow embedding) is threatened by every broad platform.** Once a contractor's workflows run through any tool, switching costs are real. Buildertrend and ServiceTitan have this today for their segments.
- **Layer 9 (GC/sub network + insurance) is not yet anyone's. Procore's prequalification feature is closest but it's a procurement-side tool. ISNetworld/Avetta own the sub-compliance hub but subs pay — the economic model is wrong.**

### Top strategic threats (ranked)

**1. Procore's downmarket pressure.** Procore has the product breadth, the brand, and the enterprise cash to attempt a cheaper tier. Their per-seat architecture constrains this, but "Procore Lite" is the single highest-risk scenario.

**2. Buildertrend + third-party AI integrations.** Buildertrend is the residential incumbent at Kerf's price point. If they ship a native AI estimating + safety add-on, they own the residential segment by default.

**3. Handoff AI expansion into commercial + operations.** They have $25M and Sequoia. They will not stay in residential-remodeling estimating. If they add job tracking + daily logs + safety, they become a direct competitor — subject to their US-locked architecture constraint.

**4. Access Coins Evo's Copilot moving downmarket.** UK enterprise ERP is a different segment, but the Copilot conversational layer is a signal that conversation in construction ERP is now mainstream. If Access moves down-market (or Eque2 / Site Samurai copy the pattern), Kerf's "no one is conversational" claim erodes fast in UK.

**5. SmartCraft group consolidating more Nordic brands.** 189K users across Bygglet/HomeRun/Coredination. If they acquire a UK or DE national champion, they become the EU version of ServiceTitan's roll-up play.

**6. SafetyCulture adds construction depth.** They have 1.5M users globally, proven multi-country operations, and construction is a major vertical. If they ship construction-specific templates + OSHA traversal, their safety-only wedge becomes a construction platform entry.

**7. Causeway rolling up European field tools.** They just bought LetsBuild. More acquisitions likely. A Causeway-branded pan-European field platform is a credible 18-month scenario.

**8. Hardline + a platform partner.** Hardline's voice capture layered onto a partner's platform (JobTread? Houzz Pro?) becomes "conversational residential PM" without either party needing to build it alone.

### Moats where Kerf has 18-24 months of runway

- Graph architecture (no replication in progress found)
- Safety-first architecture (no competitor is building from safety outward)
- Graph-connected conversation memory (no competitor has the substrate)
- Contractor-trained learning (see §5 — no competitor learns from the user's own history)
- Contract structure advisory (see §6 — unclaimed territory)

---

## 4. Deep Profiles — High-Threat & High-Distinction Competitors

Full §4-format profiles for the 12 competitors most relevant to Kerf's positioning.

---

### Procore

**Market:** US primary; UK/CA/AU/global for enterprise.
**Target:** Mid-to-large GCs and commercial subs (100+ employees). Some specialty contractors.
**Pricing:** $30,000+ per year, quote-based. Per-user plus per-project complexity.
**Product scope:** All 11 areas — full platform. 100+ modules. [procore.com](https://www.procore.com/)
**Verified:** Y — extensively documented; §2 verification covered state model.
**Sources:** [procore.com](https://www.procore.com/), [procore.com/project-management](https://www.procore.com/project-management), [support.procore.com](https://support.procore.com/) (2026-04-18).

Procore is the enterprise-construction incumbent. They have the broadest product footprint in the market (safety, PM, financial, quality, subs, RFIs, client portal) and the largest installed base among commercial GCs. Their pricing is the central fact of their market position — $30K+ per year excludes virtually every contractor under 100 employees, which is the entire Kerf target market. Attempts to move downmarket have repeatedly failed because their per-seat + per-module pricing architecture requires enterprise-scale deployments to be profitable.

**Architecture signals:** Relational database (reportedly Microsoft SQL Server historically). Module-based feature flags. Web + mobile, desktop-primary.
**Conversational / AI capability:** AI Copilot launched 2024. Document AI for specs and drawings. Not conversational-first — chat is an overlay on a forms-based product.
**State / data model:** Two-layer project state (Active/Inactive binary + Stage of Construction customisable). Change Order immutability on approval. No first-class On Hold.
**Integrations:** Everything — 300+ integrations via Procore Marketplace.
**AI learning from user:** Limited. Suggestions from aggregate user patterns; not contractor-trained.
**Contract advisory:** No. Contract and change-order tracking is strong, but no advisory at proposal stage.
**Kerf comparison:** Procore has every feature but costs 30-50× more. For Kerf's target segment, the conversation is Procore vs. the paper-and-spreadsheet alternative, not Procore vs. Kerf. The competitive vector is Procore-Lite scenarios and downmarket pressure, not head-to-head today.

---

### JobTread

**Market:** US (expanding). Canada limited.
**Target:** Residential GCs and small commercial (10-75 employees).
**Pricing:** $199/month base. [jobtread.com/pricing](https://www.jobtread.com/)
**Product scope:** PM, estimating, financial/job costing, scheduling, daily logs (basic), client portal, sub management, document management.
**Verified:** Y — strategy doc + help-centre corroboration.
**Sources:** [jobtread.com](https://www.jobtread.com/), [jobtread.com/features/cost-catalog](https://www.jobtread.com/features/cost-catalog), [jobtread.com/blog/construction-job-costing-faqs-and-tips](https://www.jobtread.com/blog/construction-job-costing-faqs-and-tips) (2026-04-18).

JobTread is the strongest SMB financial-management competitor in the US residential segment. 11,944% revenue growth. Estimate-to-budget flow is clean. Contractor-built Cost Catalog (a structured library of cost items and assemblies). Workflow automation engine (2025) triggers pipeline advancement, to-dos, schedule templates on events. Customer portal shows signed contract after proposal acceptance. Auto-decline on proposal expiry is unusual and thoughtful.

**Architecture signals:** Relational (not confirmed, but standard for the category). Web + mobile.
**Conversational / AI capability:** No conversational interface. Workflow automations are event-triggered, not agent-driven.
**State / data model:** Pipeline-based rather than fixed states. Common pipeline: Lead → Estimate → Proposal Sent → Signed → Pre-Construction → Production → Closeout → Completed.
**Integrations:** QuickBooks sync is primary. Some document signing integrations.
**AI learning from user:** **Structured but manual.** Contractor builds the Cost Catalog and manually references historical data. The platform "facilitates" learning by letting the contractor organise their own cost data over time — but does not automatically learn patterns or re-estimate from history.
**Contract advisory:** Proposal templates and custom terms. No AI advisory on payment schedules, assumptions, or retention.
**Kerf comparison:** JobTread is the closest product-fit incumbent for the residential GC Kerf persona. Kerf's differentiation: (a) safety-first architecture (JobTread has none), (b) graph-based learning (JobTread has a manual cost catalog), (c) conversational-first voice capture (JobTread is forms-based), (d) global architecture (JobTread is US-locked). Direct head-to-head in US residential is Kerf's toughest competitive vector for the first 2-3 years.

---

### Buildertrend (with CoConstruct)

**Market:** US primary; UK presence; AU presence.
**Target:** Residential GCs (5-75 employees).
**Pricing:** ~$99-499/month [buildertrend.com](https://buildertrend.com/).
**Product scope:** Leads, estimates, schedules, client portal, daily logs, warranty (first-class), subs, time tracking, documents.
**Verified:** Y.
**Sources:** [buildertrend.com](https://buildertrend.com/), [buildertrend.com/help-article/estimate-overview](https://buildertrend.com/help-article/estimate-overview/), [buildertrend.com/blog/difference-proposal-estimate](https://buildertrend.com/blog/difference-proposal-estimate/) (2026-04-18).

Buildertrend is the residential-construction PM incumbent. Merged with CoConstruct in 2022 (now one product). Distinctive first-class Warranty state with dedicated tab and Claim workflow — residential-industry best practice. Strong client portal with builder-controlled feature visibility per job state.

**Architecture signals:** Relational. Web + mobile. Desktop-primary for estimating.
**Conversational / AI capability:** Third-party AI integrations (Good Smart Idea, others) can format estimates into branded client-ready proposals. No native conversational interface. No native AI agent.
**State / data model:** Job states: Pre-Sale (Lead) / Open (Active) / Warranty / Closed. Lead Opportunity separate.
**Integrations:** QuickBooks, Xero (UK), Sage, accounting systems.
**AI learning from user:** Minimal. Estimate templates are contractor-built and reusable. No auto-learning from past job outcomes.
**Contract advisory:** Payment schedule fields in proposals. Draw schedule, deposits, payment windows are structured. No advisory on what values to set.
**Kerf comparison:** Buildertrend owns residential. Kerf's entry is the same 4 differentiators as vs JobTread, plus Kerf's unified WorkItem lifecycle (Buildertrend has leads, estimates, schedule, and cost report as separate modules requiring re-entry).

---

### Knowify

**Market:** US primary.
**Target:** Small-to-mid trade contractors (electrical, mechanical, specialty subs). 5-50 employees.
**Pricing:** $149-349/month [knowify.com/pricing](https://knowify.com/pricing/).
**Product scope:** PM, estimating, job costing, scheduling, time tracking, sub management (light), client portal, change orders.
**Verified:** Y — §2 verification covered state model in detail.
**Sources:** [knowify.com](https://knowify.com/), [knowify.com/construction-estimating-software](https://knowify.com/construction-estimating-software/), [knowify.zendesk.com/hc/en-us/articles/360025900352](https://knowify.zendesk.com/hc/en-us/articles/360025900352-Tracking-jobs-by-contract-status) (2026-04-18).

Knowify is the closest product-fit incumbent for Sarah Chen (45-person electrical sub) — trade-contractor-focused, commercial-leaning, QuickBooks-integrated, with a rigorous state machine: Lead → Bidding → Out for Signature → Active → Pending Changes → Rejected / Closed. "Pending Changes" sub-state is elegant — jobs still track costs and revenue but cannot invoice the full contract until change orders resolve. Change orders enforce scope discipline.

**Architecture signals:** Relational. Web + mobile. Desktop-primary.
**Conversational / AI capability:** No conversational interface. No native AI agent.
**State / data model:** Clearest contract state machine in the SMB segment. Auto-transitions on events (draft saved, sent, signed). Strong line-item lock on signature — changes MUST go through CO.
**Integrations:** QuickBooks Online 2-way sync is the anchor integration. Payroll and time integrations.
**AI learning from user:** Cost templates (contractor builds, reusable). Historical data access via QB sync — reference, not learning. "Review similar projects over time" is analytical not generative.
**Contract advisory:** No. Change order workflow is strong but no advisory on initial contract structure.
**Kerf comparison:** Knowify has the rigour; Kerf has the architecture. Knowify's state machine philosophy should inform Kerf's lifecycle design (already noted in lifecycle-02 research). But Kerf wins on: safety, conversational interface, auto-learning, global architecture, graph-based everything.

---

### Houzz Pro

**Market:** US primary, some UK and IE.
**Target:** Interior designers, architects, residential contractors. Solo through 50-person.
**Pricing:** $99-399/month.
**Product scope:** CRM/leads, proposals, invoicing, project tracking, client portal, sourcing (product library).
**Verified:** Y — §2 verification covered state model.
**Sources:** [pro.houzz.com](https://pro.houzz.com/for-pros/feature-sales-crm), [pro.houzz.com/pro-help/r/status-breakdown-for-proposals-invoices-and-purchase](https://pro.houzz.com/pro-help/r/status-breakdown-for-proposals-invoices-and-purchase), [pro.houzz.com/pro-help/r/how-to-customize-your-lead-stages](https://pro.houzz.com/pro-help/r/how-to-customize-your-lead-stages) (2026-04-18).

Houzz Pro has the cleanest residential-designer CRM in the market. Strong lead pipeline (New → Followed Up → Connected → Meeting Scheduled → Proposal Sent → Won), strict proposal immutability (Approved/Declined/Paid/Partially Paid/Invoiced/Partially Invoiced cannot be deleted), Snooze-a-lead action for deferring cold leads. Sub-object state auto-flips (product added to project → Project Tracker updates).

**Architecture signals:** Relational. Web + mobile.
**Conversational / AI capability:** Chat-based lead qualification bot. No general agent.
**State / data model:** Best-in-class immutability enforcement. Reopen-for-editing is the unlock mechanism — strong audit trail.
**Integrations:** QuickBooks, Houzz marketplace product catalog (large).
**AI learning from user:** Minimal. No learning from past jobs.
**Contract advisory:** Proposal templates. No advisory.
**Kerf comparison:** Houzz Pro is not a construction operations platform — it's a sales/CRM/proposal tool for designers. Limited overlap with Kerf, except at the solo-contractor entry point (Jake Torres would compare). Kerf's edge: field-first, safety, operations.

---

### JobNimbus

**Market:** US primary.
**Target:** Contractors with pipeline-rot problem. Strong in roofing, storm restoration, exteriors.
**Pricing:** $30-70/user/mo.
**Product scope:** CRM/leads, estimates, pipeline, invoicing, basic PM.
**Verified:** Y — §2 verification.
**Sources:** [support.jobnimbus.com/what-are-stages](https://support.jobnimbus.com/what-are-stages), [jobnimbus.com/blog/feature-updates-days-in-status-automation](https://www.jobnimbus.com/blog/feature-updates-days-in-status-automation/) (2026-04-18).

JobNimbus is the most rigorous pipeline-tracking tool for US contractors with long sales cycles (roofing, insurance-restoration, storm work). Fixed 6-stage pipeline (Lead / Estimating / Sold / In Production / Accounts Receivable / Completed + Lost at any point). Stage names not customisable — by design, for accurate cross-tenant reporting. Sub-statuses within stages are customisable. Days-in-Status counter on every card — explicit rot detection.

**Architecture signals:** Relational. Web + mobile.
**Conversational / AI capability:** Insights workflow dashboards. No conversational interface.
**State / data model:** Cleanest fixed-stage implementation. Lost → re-entry (partially verified — resets some fields for revive-as-fresh-deal analytics).
**Integrations:** QuickBooks, various.
**AI learning from user:** Minimal.
**Contract advisory:** No.
**Kerf comparison:** JobNimbus is a CRM + light PM tool, not a construction platform. Limited overlap with Kerf's target work types (Kerf targets trades with daily operations; JobNimbus targets trades with long sales cycles).

---

### ServiceTitan

**Market:** US primary; moving into construction.
**Target:** Service trades (HVAC, plumbing, electrical service); emerging new-construction.
**Pricing:** Enterprise-leaning; typically $400-1,500+/month.
**Product scope:** Dispatch, scheduling, invoicing, project tracking, CRM, call center, marketing, payroll integration.
**Verified:** Y — §2 verification.
**Sources:** [help.servicetitan.com/how-to/statuses-actions](https://help.servicetitan.com/how-to/statuses-actions), [help.servicetitan.com/how-to/job-hold](https://help.servicetitan.com/how-to/job-hold) (2026-04-18).

ServiceTitan is the service-trades leader. Four-entity model (Appointment / Job / Project / Invoice) with Invoice posted-lock. Appointment Hold is state-restricted (only Scheduled appointments can go on hold). Automatic transitions from field events. Project is the container for multi-day or multi-job work.

**Architecture signals:** Relational. Web + mobile + call-center integrations.
**Conversational / AI capability:** Titan Intelligence AI (2024+) for scheduling optimisation, pricing suggestions. Not conversational-first.
**State / data model:** Strongest invoice-lock pattern in the market.
**Integrations:** Accounting (QB, Sage), payroll, marketing.
**AI learning from user:** Some — pricing suggestions use aggregate data. Not contractor-history-driven in the Kerf sense.
**Contract advisory:** Quote templates. No advisory on structure.
**Kerf comparison:** ServiceTitan targets service trades with dispatch-first workflows. Kerf targets construction with project-first workflows. Partial overlap at Jake Torres (solo) end; no overlap at Sarah Chen or Marco ends.

---

### Handoff AI

**Market:** US only.
**Target:** Residential remodelers, handymen.
**Pricing:** $119-299/month.
**Product scope:** Estimating (AI-generated), proposals, some project tracking. Not a platform.
**Verified:** Y — strategy doc + vendor docs + help-centre confirmation.
**Sources:** [handoff.ai](https://handoff.ai/), [handoff.ai/pricing](https://handoff.ai/pricing/), [help.handoff.ai/en/articles/9564039-ai-understand-pricing-data](https://help.handoff.ai/en/articles/9564039-ai-understand-pricing-data), [handoff.ai/blog/ai-estimating-software-the-ultimate-guide-for-contractors-2026](https://handoff.ai/blog/ai-estimating-software-the-ultimate-guide-for-contractors-2026/) (2026-04-18).

Handoff is the most-funded AI-construction-estimating startup. $25M from YC, Sequoia, Initialized, Nemetschek. 10K MAU, $6B project volume. AI trained on 100K+ completed estimates and 60M+ SKUs. Pricing data from Home Depot, Lowe's, regional distributors, with location-specific labour rates. Audio-to-Docs voice feature shipped January 2026.

**Architecture signals:** Supplier-API integrations are the foundation of their pricing engine — this locks them to US. US-trained models. English only (with Spanish reportedly roadmapped).
**Conversational / AI capability:** AI generates estimates from plans, photos, or voice input. Batch voice (Audio-to-Docs — record then process), not conversational-first. No agent with memory across jobs.
**State / data model:** Not publicly documented in detail.
**Integrations:** QuickBooks, accounting. Supplier APIs are the distinctive integration.
**AI learning from user (CRITICAL):** **Aggregate catalog-trained, not contractor-trained.** The 100K past estimates come from all users; the pricing comes from supplier APIs and market labour rates. A contractor in Phoenix gets prices for Phoenix but does not get their own rates from their own past jobs. This is the central differentiator Kerf's vision targets.
**Contract advisory:** Proposal templates. No structural advisory.
**Kerf comparison:** Handoff is the leading AI estimating product and an architectural risk — if they expand into full platform, they win on the "AI-native" narrative. But their architecture is US-locked (supplier APIs, US catalog, English) and catalog-trained (not contractor-trained). Kerf's bet on (a) global architecture, (b) contractor's-own-data learning, (c) full platform not just estimating, is the direct counter-position.

---

### Hardline

**Market:** US only.
**Target:** Residential + small commercial contractors using Procore / Fieldwire.
**Pricing:** ~$99+/month (not publicly priced in detail).
**Product scope:** Voice capture layer. Pushes tasks, notes, RFIs into Procore or Fieldwire.
**Verified:** Partial — vendor marketing + investor info.
**Sources:** Strategy doc; vendor information. Not deeply verified from vendor docs in this scan.

Hardline captures contractor phone calls and site walks passively — no behaviour change required. Real-time transcription. Task extraction from conversations. Co-Pilot search over past conversations. EN/ES with code-switching. Offline capable. $2M pre-seed from Suffolk Technologies.

**Architecture signals:** Integration layer, not a platform. Depends on Procore / Fieldwire for data model.
**Conversational / AI capability:** Voice capture + search. Not a full conversational agent.
**AI learning from user:** Searchable conversation history. Not generative re-use.
**Contract advisory:** No.
**Kerf comparison:** Hardline validates voice-first. Kerf's vision is voice-first on top of a knowledge graph, which Hardline does not have (they depend on Procore / Fieldwire's data). Hardline is a feature, not a platform — and the feature is narrower than Kerf's conversational interface.

---

### SafetyCulture (iAuditor)

**Market:** Global — originated AU, strong in US/UK/EU.
**Target:** Any industry. 50+ industries, not construction-specific. 1.5M users globally.
**Pricing:** $0 free tier, $19-34/user/mo premium, enterprise quote.
**Product scope:** Inspection checklists, issue tracking, training, documents.
**Verified:** Y — public vendor data.
**Sources:** [safetyculture.com](https://safetyculture.com/) (2026-04-18).

SafetyCulture is the global inspection-checklist leader. Huge user base. Excellent mobile-first UX. Multi-language (global team). Not construction-specific — the same product runs in hospitality, mining, healthcare, retail, and construction. No graph, no regulatory traversal, no financial link, no operations expansion.

**Architecture signals:** Relational. Horizontal across verticals.
**Conversational / AI capability:** Some AI for issue summarisation (2024+). Not conversational-first.
**State / data model:** Inspection-driven — not project-lifecycle-driven.
**AI learning from user:** Aggregate patterns across tenants.
**Contract advisory:** N/A — safety only.
**Kerf comparison:** SafetyCulture is the safety incumbent Kerf must differentiate from on the entry wedge. Kerf's wins: (a) construction-specific regulatory depth (OSHA traversal, jurisdiction-specific), (b) integrated into operations (daily logs, time, quality use the same inspection engine), (c) conversational interface over a graph. SafetyCulture's advantage: proven global scale, huge existing base, lower price at the bottom.

---

### Access Coins Evo (UK)

**Market:** UK, Ireland.
**Target:** Enterprise GCs.
**Pricing:** Enterprise quote.
**Product scope:** Full ERP — finance, projects, field, safety (light).
**Verified:** Partial — vendor-documented Copilot launch; depth of capability not fully verified.
**Sources:** [coins-global.com](https://www.coins-global.com/), [theaccessgroup.com/en-us/construction/](https://www.theaccessgroup.com/en-us/construction/) (2026-04-18).

Access Coins Evo is the most aggressive AI-feature shipper in European enterprise construction ERP. Three integrated AI capabilities: **Copilot** (conversational assistant), **Feed** (30+ proactive alerts — business monitoring 24/7), **Analytics** (construction-specific dashboards). This is the first conversational AI layer I have found in any construction ERP at this depth.

**Architecture signals:** Relational ERP. UK-centric. Not graph-based.
**Conversational / AI capability:** **Active threat.** Copilot is positioned as a general-purpose construction assistant. Depth of graph traversal and regulatory reasoning unclear from vendor marketing — the claim is "construction-specific AI" but whether it approaches Kerf's graph-based reasoning is not publicly documented.
**State / data model:** Enterprise ERP — customisable workflow engine per tenant (similar to CMiC).
**Integrations:** Full enterprise stack.
**AI learning from user:** Not publicly documented in detail. Copilot likely uses aggregate data + tenant-specific data, pattern unclear.
**Contract advisory:** Full contract management module. Advisory capability not publicly documented.
**Kerf comparison:** Access Coins Evo targets UK enterprise — a segment above Kerf. But if the Copilot pattern moves down-market (either Access's own product or copied by Eque2 / Site Samurai), Kerf's "no one is conversational in UK" claim erodes. **Worth monitoring closely.**

---

### Site Samurai (UK)

**Market:** UK primary, some Ireland.
**Target:** UK SME contractors (main contractors, specialty contractors, subcontractor managers). Estimated 5-100 employees.
**Pricing:** £83/mo Starter / £166/mo Professional / £699/mo Enterprise. **Unlimited users on every tier** (per-company pricing — same philosophy as Kerf). 14-day free trial. Add-ons: CIS Resource £8.25/mo, LazyQs £126.58/mo.
**Product scope:** ~8/11 process areas — Commercial (tenders, applications for payment, valuations, variations, cashflow), Safety (RAMS, toolbox talks, incidents), Fleet (vehicle/plant tracking, inspections, defects, utilisation), Subcontractors (onboarding, CIS, compliance, supply chain). Plus team chat, holiday management, document storage.
**Verified:** Y — extensive public coverage. Live demo not accessed (interactive demo at `/login?demo=true` is read-only behind a login gate not accessible via WebFetch).
**Sources:** [sitesamurai.co.uk](https://www.sitesamurai.co.uk/), [solutions](https://www.sitesamurai.co.uk/solutions), [pricing](https://www.sitesamurai.co.uk/pricing), [applications-for-payment-software](https://www.sitesamurai.co.uk/solutions/applications-for-payment-software), [cis-management-software](https://www.sitesamurai.co.uk/solutions/cis-management-software), [subcontractor-onboarding-software](https://www.sitesamurai.co.uk/solutions/subcontractor-onboarding-software), [rams-generator](https://www.sitesamurai.co.uk/rams-generator), [resources](https://www.sitesamurai.co.uk/resources) (all 2026-04-19).

Site Samurai is the strongest UK-specific SME construction platform found in this scan. Purpose-built for UK regulatory workflows: NEC4/JCT payment applications with Construction Act notices, CIS verification and deduction management (20%/30%/gross), CDM-era RAMS, HMRC-aligned tracking. Founder-led (Rich), with positioning ("Cut Through The Bullshit™") explicitly pitched at UK SME contractor fatigue with enterprise tools. UK GDPR compliant, data stored in UK data centres only. Free 14-day trial on every tier. **No G2 or Capterra reviews published yet** — indicates early-stage market presence despite mature feature set.

**Architecture signals:** Relational. Web + mobile. UK-hosted. Not graph-based. UK data residency as a positioning asset.

**Conversational / AI capability:** AI is **narrow and feature-specific, not platform-wide**. Site Samurai AI (Professional tier and up) does three things: (1) generate RAMS documents from inputs, (2) generate toolbox talks, (3) parse BOQs for estimating (document intelligence). Enterprise tier unlocks "unlimited AI generations." **No conversational interface, no voice, no chat-first UX anywhere in the product.** AI is a document-generation feature on a forms-based platform. The standalone RAMS Generator (£4.99/doc) is explicitly template-based with "5 AI tweaks" included — not truly generative from scratch. Cannot be operated by chat alone.

**State / data model:** Applications for Payment has a 5-stage workflow (Build → Review → Submit → Certify & respond → Generate notices). Configurable deadline tracking with notice periods for UK Construction Act compliance. Applied-vs-certified tracking with line-item queries. CIS verification is timestamped with evidence storage. Clean role-based access (QS, directors, site teams).

**Integrations:** Xero and Sage (Professional tier+) — UK accounting stack. API access (Professional tier+). No QuickBooks integration (not UK-mainstream).

**AI learning from user:** BOQ parsing is document-intelligence, not job-history learning. No evidence of AI learning from the contractor's own historical estimates, rates, or job outcomes. Cost data is user-entered (manually or via BOQ parse), not derived from completed jobs.

**Contract advisory:** None at proposal authoring. Tender management module handles bid preparation; Applications for Payment handles UK regulatory execution of payment. No advisory on what to include in contracts, payment schedule structure, assumptions, or retention beyond UK defaults.

**Kerf comparison:**

- **Site Samurai's UK-specific advantages:** CIS deduction workflows, NEC4/JCT applications for payment, Construction Act notice automation, UK GDPR data residency, UK compliance vocabulary. Kerf would need to build all of this from scratch to compete head-on in UK SME commercial segment.
- **Site Samurai's scope advantages over Kerf's current roadmap:** **Fleet management** (vehicle/plant tracking with MOT/tax alerts and DVSA compliance) — not currently in Kerf's scope. Represents a 12th process area Kerf hasn't planned for.
- **Kerf's architectural advantages:** Graph-based substrate. Conversational-first with voice. Contractor-own-data learning for estimates. Multi-jurisdictional (Site Samurai is UK-locked — every contract workflow, every regulatory reference, every tax module is UK-specific). Safety as a cross-cutting architectural layer vs Site Samurai's safety-as-sibling-module.
- **Where Kerf wins head-to-head:** Operations layer — daily logs (Site Samurai has none), quality inspections / punch lists (Site Samurai has none), time tracking for labour costing (Site Samurai has holiday management, not labour-hours-to-projects), voice-first field capture (none), conversational interface (none), contractor-own-data estimate learning (none), document intelligence beyond BOQ parsing (Site Samurai has only BOQ).
- **Where Site Samurai wins head-to-head:** UK-specific commercial workflows (NEC4/JCT applications for payment, Construction Act notices), CIS management, fleet/plant management, UK data residency trust narrative, UK-contractor-specific positioning.
- **Threat level for UK entry:** Medium-high. Site Samurai is the direct incumbent Kerf will face in UK SME commercial contractor segment. AI is narrow, architecture is relational, positioning is commercial-execution-focused — meaning Kerf can enter via operations (daily logs, quality, time, voice-first safety) where Site Samurai is thin. But to win commercial-execution customers head-on, Kerf would need to ship UK-specific applications-for-payment + CIS workflows, which are non-trivial builds. Realistic UK entry strategy: compete on operations depth and conversational interface, partner or build toward UK commercial workflows over 12-18 months. Do not attempt head-on NEC4/JCT/CIS feature parity in year 1.

---

### Dalux

**Market:** Denmark HQ, offices in NO/SE/FR/UK/NL/CZ/SI/LT. 140+ countries.
**Target:** Mid-large GCs, architects, owners.
**Pricing:** Free tier + paid tiers (not publicly detailed).
**Product scope:** BIM model viewer, field (snagging / issue capture), facilities management.
**Verified:** Y — vendor docs.
**Sources:** [dalux.com](https://www.dalux.com/), [dalux.com/about-dalux](https://www.dalux.com/about-dalux/) (2026-04-18).

Dalux is the strongest Nordic BIM-led field platform. World-class 3D BIM visualisation engine. Proven global deployment (Statsbygg Norway — 2.8M m² of buildings). AR technology deployed with AF Gruppen (35,000 workers in Norway). Free tier drives adoption.

**Architecture signals:** BIM-centric. Relational. Mobile-first for field.
**Conversational / AI capability:** Some AI for defect classification. Not conversational.
**State / data model:** Issue-centric. Not project-lifecycle-centric.
**Integrations:** BIM tools (Revit, ArchiCAD), project management tools.
**AI learning from user:** Minimal.
**Contract advisory:** No.
**Kerf comparison:** Dalux is a BIM + field platform, not a contractor operations platform. Partial overlap only — they have the Nordic cross-country reach that Kerf's global architecture bets on, but they cover 3-4 of the 11 process areas, not all 11. **Proven cross-border model** — this is what Kerf must replicate.

---

### SmartCraft group (Bygglet, HomeRun, Coredination)

**Market:** Sweden, Norway, Finland, UK.
**Target:** SME craftsmen (Nordic "hantverk" = Handwerker equivalent) and construction SMEs.
**Pricing:** Varies per brand; Bygglet around SEK 500-2,500/mo/user.
**Product scope:** Broad platform for Nordic SME — quoting, time, materials, PM, resourcing, invoicing.
**Verified:** Y — SmartCraft investor + vendor docs.
**Sources:** [smartcraft.com](https://smartcraft.com/), [smartcraft.com/solutions/tools/bygglet](https://smartcraft.com/solutions/tools/bygglet/), [news.cision.com/smartcraft-asa](https://news.cision.com/smartcraft-asa/r/smartcraft-asa--smcrt----acquiring-coredination-and-strengthening-nordic-construction-software-leade,c3806352) (2026-04-18).

SmartCraft is the Nordic contractor-software consolidator, Oslo Stock Exchange listed (June 2021). 270+ employees, 189,000+ users across Sweden, Norway, Finland, and UK. Bygglet is the SME market leader in Sweden with 75K active users. Portfolio acquisitions: HomeRun (2021, Finland, renovations/apartment communication), Coredination (2023, Sweden). This is the European SMB platform with the largest user base.

**Architecture signals:** Relational. Web + mobile. Nordic language-first.
**Conversational / AI capability:** Not prominent in vendor marketing. Not documented as a current capability.
**State / data model:** Not publicly documented in detail.
**Integrations:** Nordic accounting systems, payroll.
**AI learning from user:** Not publicly documented.
**Contract advisory:** Quoting → invoicing flow handles standard Nordic contract patterns. No AI advisory.
**Kerf comparison:** SmartCraft is the prototype of what a cross-country SMB contractor platform looks like. **They are already operating where Kerf wants to operate in Europe.** Their architecture constraints (relational, no safety depth, no conversational, no graph) are Kerf's openings. But their user base (189K) and consolidation strategy mean they are the EU competitor Kerf cannot ignore — either as a competitor, a potential acquirer, or a model for the operational work of running across 4 countries and 4 languages.

---

## 5. The AI-Learning Question

### What Kerf's vision claims

From `PRODUCT_VISION.md` §3.2, §3.13:
- After 10 jobs, learning from the contractor's own data is "more accurate than any catalog."
- Learned-pattern prompting: the agent asks only about parameters that have varied across the contractor's past jobs (distance-to-existing-panel varied from 8-40 ft and correlated with labour hours → prompt for it; meter-main-type always the same → don't).
- No template library to author; patterns derived from completed work.

### What competitors actually do

| Competitor | Approach | Type |
|---|---|---|
| **Handoff AI** | 100K+ estimates + 60M SKUs. Home Depot/Lowe's. ZIP-based labour rates. | **Aggregate catalog-trained.** Same database for every user. |
| **Togal.ai** | AI takeoff from plans. | Aggregate training across all drawings. |
| **Kreo** | AI takeoff + estimating. | Aggregate training. |
| **BuildGets (Spain)** | AI for BC3 estimates. | Catalog-based. |
| **JobTread** | Contractor builds Cost Catalog. Historical data accessible. | **Manual library.** Contractor must maintain it. |
| **Knowify** | Cost templates with custom units of measurement. QB sync gives historical access. | **Manual templates.** Reference, not learning. |
| **Buildertrend** | Estimate templates, cost items. Third-party AI for proposal formatting. | **Manual templates** + post-hoc proposal formatting. |
| **Procore** | AI Copilot. | Aggregate + tenant data. Not contractor-history-driven for estimates. |
| **ServiceTitan** | Titan Intelligence — pricing suggestions. | Aggregate pricing + some local data. |

### What's genuinely unclaimed

- **Automatic learning from the individual contractor's own completed jobs** — rates, productivity, labour patterns, supplier relationships — as the primary source for future estimate generation.
- **Learned-pattern prompting** — agent asks only what has varied. No competitor does this.
- **Cross-estimate learning with confidence** — "you have done 17 panel upgrades; your average is 4.2 labour hours and this one has typical features, suggested estimate = $1,460" with the graph traversal citing every job.

**Kerf's differentiation here is genuine and architecturally defensible.** The reason nobody does it is that it requires:
1. A graph that connects every job, line item, time entry, and actual cost
2. An ontology that lets the agent ask "what's similar to this"
3. Conversation memory that remembers why the contractor chose certain rates
4. A UX that presents learned suggestions alongside rationale, not as a black box

Relational-database competitors cannot build this without architectural change. AI-first competitors (Handoff, Togal) are locked into aggregate-training models that are harder to pivot away from than to start fresh.

### Caveat

**Kerf has not yet shipped this capability at depth.** The vision is sound; the competitive advantage is real; execution is the constraint. A competitor who ships "we learn from your own jobs" before Kerf does could claim the narrative.

---

## 6. The Contract Advisory Question

### What Kerf's vision implies

From `PRODUCT_VISION.md` §3.3, §3.8:
- The system parses signed contracts for key terms (retention, payment schedule, milestones).
- The system generates proposals referencing versioned Estimates.
- The agent drafts proposals and parses contracts into the graph.

### What the vision does not yet explicitly claim

The user's question today: **"how does the application advise the user on how to structure a contract, such as staged payments, and assumptions."**

Advisory at **proposal authoring time** — not just capture after the fact. The contractor says "I'm writing a quote for a 12-week commercial fit-out"; the agent suggests:
- Payment schedule pattern (30% deposit / 30% mid-completion / 35% practical completion / 5% retention @ 12 months) appropriate to job size + client relationship + jurisdiction
- Standard assumptions to include ("quote based on access during standard hours", "does not include asbestos remediation", "electrical certifications by client's subcontractor")
- Exclusions appropriate to trade + jurisdiction
- Warranty period standard for this work type
- Escalation clauses if project exceeds X weeks
- Variation handling terms

### What competitors actually do

**Contract review / analysis (post-signature):**
- **Document Crunch** ([documentcrunch.com](https://www.documentcrunch.com/)) — AI analyses uploaded contracts for clause risk. Good for spotting bad clauses in GC-supplied contracts. Not for authoring contractor's own contracts.
- **Mastt AI** ([mastt.com/software/contract-management-software-ai](https://www.mastt.com/software/contract-management-software-ai)) — Contract management + AI risk detection. Tracks retention, milestones, claim timelines. Enterprise-focused. Not advisory at proposal stage.
- **Sirion** ([sirion.ai](https://www.sirion.ai/library/clm-platform/construction-contract-management-software/)) — CLM platform with construction vertical. Post-execution management.
- **Ment Tech** ([ment.tech](https://www.ment.tech/ai-construction-contract-management-software/)) — AI construction contract management.

**Proposal / contract generation (no advisory):**
- **Knowify, Buildertrend, JobTread, Houzz Pro** — all have proposal templates with payment schedule fields. Contractor fills in values manually. Templates are reusable but not AI-suggested.
- **Site Samurai (UK)** — NEC4/JCT timeline support + applications for payment. Executes the standard UK workflow; does not advise on contract structure.

**UK-specific structural handling:**
- **Site Samurai** ([sitesamurai.co.uk/solutions/applications-for-payment-software](https://www.sitesamurai.co.uk/solutions/applications-for-payment-software)) — NEC4 / JCT applications for payment, Construction Act notices, applied vs certified tracking, variations, retention. The UK regulatory regime is baked in.
- **Lio (France)** — retenue de garantie (retention), sous-traitance (subcontracting), factures de situation (progress invoices). French regulatory regime baked in.

**ERP advisory features:**
- **CMiC / Access Coins Evo / Procore** — customisable contract templates per tenant. No AI advisory on structure.

### What's genuinely unclaimed

- **AI advisory on payment schedule structure at proposal authoring time**, grounded in:
  - Job size + duration
  - Commercial / residential / cost-plus / fixed-price
  - Jurisdiction standards (UK NEC4 / JCT; French retenue de garantie; US progress billing; etc.)
  - Client relationship history (new client → more conservative terms; repeat client → looser)
- **AI advisory on assumptions and exclusions**, grounded in:
  - Trade (electrical defaults ≠ concrete defaults ≠ HVAC defaults)
  - Jurisdiction (UK: asbestos survey assumption; US: different set; France: different set)
  - Job type (new construction ≠ renovation ≠ fit-out)
- **Contractor-specific learned defaults** — "you always include X assumption; you have never used an escalation clause; your typical retention for this GC is 5%".

**This is whitespace.** No competitor found in this scan advises at proposal-authoring time. The closest analogues are:
- **Legal-tech contract generators** (Ironclad, LinkSquares) — general-purpose, not construction-specific.
- **Document Crunch** — reviews GC-supplied contracts, does not advise contractor-written ones.

**Caveat:** Advisory on contract structure is high-consequence — a wrong suggestion could cost a contractor significantly on the job. Per Kerf's principle #15 ("Advise, highlight, keep logical, do what you're told"), the agent's role is advisory, not prescriptive, and the contractor approves everything. Per principle #4 ("Every AI output must cite the specific standard"), every suggestion needs a citation (industry norm, past job, jurisdictional default). The safety-critical disclaimer pattern Kerf already uses for safety content applies here.

---

## 7. Exhaustive Competitor Table

Every competitor identified in this scan, with key attributes. Deep profiles in §4 are marked ⭐.

| # | Competitor | Region | Target | Price tier | Scope | Safety? | Conv AI? | Graph? | Multi-ctry? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Procore ⭐ | US/global | Mid-Ent GC | $30K+/yr | 11/11 | ⚪ | ⚪ | ✗ | ⚪ |
| 2 | ACC / Autodesk Build | US/global | Mid-Ent | Ent quote | 10/11 | ⚪ | ⚪ | ✗ | ⚪ |
| 3 | CMiC | CA/US | Ent | Ent quote | 11/11 | ⚪ | ✗ | ✗ | ✗ |
| 4 | Viewpoint / Trimble Construction One | US | Ent | Ent quote | 10/11 | ⚪ | ⚪ | ✗ | ✗ |
| 5 | Sage 300 CRE | US | Ent | Ent quote | 8/11 | ✗ | ✗ | ✗ | ✗ |
| 6 | TeamSystem Construction | IT | Ent | Ent quote | 10/11 | ⚪ | ✗ | ✗ | ✗ |
| 7 | Access Coins Evo ⭐ | UK/IE | Ent | Ent quote | 10/11 | ⚪ | ⚫ | ✗ | ✗ |
| 8 | COINS (original) | UK | Ent | Ent quote | 10/11 | ⚪ | ✗ | ✗ | ⚪ |
| 9 | Causeway Technologies | UK + EU via LetsBuild | Ent | Ent quote | 6/11 | ✗ | ✗ | ✗ | ⚪ |
| 10 | Eque2 | UK | SME-Mid | ~£50-200/user/mo | 7/11 | ✗ | ✗ | ✗ | ✗ |
| 11 | Integrity Software / Evolution Mx | UK + IE | SME-Mid | ~£70-250/user/mo | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 12 | Site Samurai | UK | SME | ~£30-100/user/mo | 7/11 | ✗ | ✗ | ✗ | ✗ |
| 13 | JobTread ⭐ | US | Resi GC SMB | $199/mo | 7/11 | ✗ | ✗ | ✗ | ✗ |
| 14 | Buildertrend ⭐ | US (+ UK/AU) | Resi GC SMB | $99-499/mo | 8/11 | ✗ | ⚪ | ✗ | ⚪ |
| 15 | Houzz Pro ⭐ | US + UK/IE | Designers + resi | $99-399/mo | 5/11 | ✗ | ⚪ | ✗ | ⚪ |
| 16 | Knowify ⭐ | US | Trade contractor SMB | $149-349/mo | 7/11 | ✗ | ✗ | ✗ | ✗ |
| 17 | Contractor Foreman | US | GC SMB | $49-249/mo | 9/11 | ⚪ | ✗ | ✗ | ✗ |
| 18 | JobNimbus ⭐ | US | Roofing/contractor | $30-70/user/mo | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 19 | Projul | US + UK | SMB | $4,788+/yr | 5/11 | ✗ | ✗ | ✗ | ⚪ |
| 20 | Bolster | US | Resi | Varies | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 21 | ServiceTitan ⭐ | US | Service trades | Ent-leaning | 9/11 | ✗ | ⚪ | ✗ | ✗ |
| 22 | Jobber | US/CA | Service SMB | $35-249/mo | 7/11 | ✗ | ✗ | ✗ | ⚪ |
| 23 | Housecall Pro | US | Service SMB | $49-249/mo | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 24 | Handoff AI ⭐ | US | Resi remodeler | $119-299/mo | 3/11 | ✗ | ⚪ | ✗ | ✗ |
| 25 | Hardline ⭐ | US | Resi + sm commercial | ~$99+/mo | 2/11 (layer) | ✗ | ⚫ | ✗ | ✗ |
| 26 | Togal.ai | US | Estimators | Series A pricing | 2/11 | ✗ | ✗ | ✗ | ✗ |
| 27 | Kreo | UK/EU | Takeoff + estimating | Varies | 2/11 | ✗ | ✗ | ✗ | ⚪ |
| 28 | Renalto | US | Voice-to-proposal | Early | 2/11 | ✗ | ⚪ | ✗ | ✗ |
| 29 | BuildGets | ES | AI BC3 estimating | Early | 2/11 | ✗ | ✗ | ✗ | ✗ |
| 30 | Brickanta | SE | Enterprise pre-construction | $8M seed | 3/11 | ✗ | ⚪ | ⚪ | ⚫ |
| 31 | Raken | US | Daily logs SMB | $15-49/user/mo | 3/11 | ⚪ | ✗ | ✗ | ✗ |
| 32 | CompanyCam | US | Photos SMB | $24-37/user/mo | 1/11 | ⚪ | ✗ | ✗ | ✗ |
| 33 | Fieldwire (by Hilti) | US/UK/DE | Field tasks SMB-Mid | $0-94/user/mo | 4/11 | ⚪ | ✗ | ✗ | ⚫ |
| 34 | PlanRadar ⭐ | AT / 65+ ctries | Docs + defects SMB-Ent | €30-100/user/mo | 3/11 | ⚪ | ✗ | ✗ | ⚫ |
| 35 | Dalux ⭐ | DK / 140+ ctries | BIM + field Mid-Ent | Free + paid | 3/11 | ⚪ | ✗ | ✗ | ⚫ |
| 36 | LetsBuild (Causeway) | BE + EU | Field SMB-Mid | €30-80/user/mo | 4/11 | ⚪ | ✗ | ✗ | ⚪ |
| 37 | SafetyCulture ⭐ | AU/global | Horizontal safety | $0-34/user/mo | 1/11 | ⚫ | ⚪ | ✗ | ⚫ |
| 38 | Safesite | US | Construction safety SMB | $0-240/mo | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 39 | HandsHQ | UK | UK RAMS SMB | £20-60/user/mo | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 40 | swiftRMS | UK | UK RAMS SMB | £24-60/user/mo | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 41 | HammerTech | AU/global | EHS Mid-Ent | Ent-leaning | 2/11 | ⚫ | ✗ | ✗ | ⚪ |
| 42 | SALUS | CA | Provincial OHS SMB | SMB | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 43 | Safeti | UK | UK H&S SMB | SMB | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 44 | ISNetworld | US | Sub compliance | Subs pay | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 45 | Avetta | US | Sub compliance | Subs pay | 1/11 | ⚫ | ✗ | ✗ | ✗ |
| 46 | ClockShark | US | Time SMB | $40 + $9-11/user | 1/11 | ✗ | ✗ | ✗ | ✗ |
| 47 | Busybusy | US | Time SMB | Free-$10/user | 1/11 | ✗ | ✗ | ✗ | ✗ |
| 48 | ExakTime | US | Time SMB | $9/user | 1/11 | ✗ | ✗ | ✗ | ✗ |
| 49 | CrewTracks | US | Mobile crew time | Varies | 1/11 | ✗ | ✗ | ✗ | ✗ |
| 50 | FTQ360 | US | Construction quality | $249/mo | 1/11 | ⚪ | ✗ | ✗ | ✗ |
| 51 | HERO Software | DE | Handwerker SMB | ~€40-100/user/mo | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 52 | WINWORKER | DE | Handwerker SMB | Varies | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 53 | plancraft | DE | Handwerker SMB | ~€30-80/user/mo | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 54 | pds | DE | Handwerker SMB-Mid | Varies | 7/11 | ✗ | ✗ | ✗ | ✗ |
| 55 | openHandwerk | DE | Handwerker SMB | Varies | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 56 | Lexware handwerk | DE | Handwerker SMB | Low | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 57 | Capmo | DE | Construction PM SMB-Mid | ~€50-150/user/mo | 4/11 | ✗ | ⚪ | ✗ | ✗ |
| 58 | Costructor | FR | BTP SMB | Freemium | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 59 | Batappli | FR | BTP SMB | ~€40-120/user/mo | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 60 | EBP Bâtiment | FR | BTP SMB-Mid | Varies | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 61 | ProGBat | FR | BTP SMB | ~€30-80/user/mo | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 62 | Obat | FR | BTP SMB | SaaS low-mid | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 63 | Lio | FR | BTP SMB | SaaS low-mid | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 64 | Hemea | FR | BTP SMB | SaaS | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 65 | Vertuoza | BE | Construction SMB | Varies | 5/11 | ✗ | ✗ | ✗ | ✗ |
| 66 | Build-Software | NL/BE | Construction SMB-Mid | Varies | 6/11 | ✗ | ✗ | ✗ | ✗ |
| 67 | Bygglet (SmartCraft) ⭐ | SE/NO/FI | SME | ~SEK 500-2,500/user/mo | 7/11 | ✗ | ✗ | ✗ | ⚫ |
| 68 | HomeRun (SmartCraft) | FI | Renovation comms | Part of SmartCraft | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 69 | Coredination (SmartCraft) | SE | Construction SaaS | Part of SmartCraft | 4/11 | ✗ | ✗ | ✗ | ✗ |
| 70 | Presto (RIB Spain) | ES | Budgets + cost BIM | Mid-high | 4/11 | ✗ | ✗ | ✗ | ⚪ |
| 71 | Arquímedes (CYPE) | ES | Budgets + measurements | Mid | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 72 | MyAEDES | IT | Cantiere documentation SMB | Varies | 3/11 | ⚪ | ✗ | ✗ | ✗ |
| 73 | Edison (exeprogetti) | IT | Preventivo + cantiere | Low-mid | 4/11 | ✗ | ✗ | ✗ | ✗ |
| 74 | Cantieri Intelligenti 4.0 | IT | Cantiere control SMB | Varies | 4/11 | ✗ | ✗ | ✗ | ✗ |
| 75 | ERGO Mobile Enterprise | IT | ERP construction | Enterprise | 7/11 | ⚪ | ✗ | ✗ | ✗ |
| 76 | Norma (Athenasoft) | PL | Kosztorys | Low-mid | 1/11 | ✗ | ✗ | ✗ | ✗ |
| 77 | Winbud Kosztorys | PL | Kosztorys | Low | 2/11 | ✗ | ✗ | ✗ | ✗ |
| 78 | Connecto | PL | Kosztorys + PM | Varies | 3/11 | ✗ | ✗ | ✗ | ✗ |
| 79 | PROGPOL | PL | Cost control | Low-mid | 2/11 | ✗ | ✗ | ✗ | ✗ |

**Legend:**
- Scope: `N/11` = coverage across 11 process areas (safety, PM, estimating, daily reporting, financial, scheduling, time, sub, quality, RFIs, client portal).
- Safety? / Conv AI? / Graph? / Multi-ctry?: ⚫ strong, ⚪ partial, ✗ none or not publicly documented.

---

## 8. Strategic Implications for Kerf

This section is observational framing, not recommendation. The open question is how Kerf competes given this landscape.

### 8.1 Where Kerf's existing positioning holds

- **Graph-based architecture** — unmatched.
- **Safety-first entry wedge** — only Kerf builds from safety outward to platform. SafetyCulture is horizontal; everyone else bolts safety on.
- **Contractor-trained AI learning** — no competitor in this scan learns from the individual contractor's own completed jobs. The AI-estimating startups (Handoff, Togal, Kreo, BuildGets) all use aggregate / market data.
- **Contract structure advisory at proposal time** — unclaimed whitespace.
- **Conversational-first interface over a full platform** — Access Coins Evo's Copilot is the first credible enterprise attempt and only covers ERP, not safety. Hardline is voice-capture on top of others. Nobody has conversation + graph + full scope.
- **WhatsApp distribution for crew comms** — Kerf-exclusive.

### 8.2 Where Kerf's claims may need softening

- **"No competitor has any AI / conversational capability"** is no longer true. Access Coins Evo, Procore, ACC, CMiC, ServiceTitan have all shipped AI assistants in 2024-2026. The differentiated claim is "conversational AI **over a connected graph that spans safety + operations + finance + estimating**" — longer, but defensible.
- **"Every AI construction startup is architecturally US-locked"** — true for Handoff, Hardline, Togal, Renalto. Not true for Kreo (UK/EU) or Brickanta (SE, 11 countries, 4 continents). Softening: "every AI construction startup targeting US residential contractors is US-locked."
- **"No equivalent to JobTread in UK / Canada / AU / Europe"** — partially true. Site Samurai (UK) is the closest UK equivalent; Bygglet / SmartCraft group (Nordics) is the closest Nordic equivalent; HERO / plancraft (DE) are the closest German equivalents. The **cross-jurisdiction** claim holds — none of them crosses borders. The **"no equivalent"** claim is too strong.

### 8.3 Where Kerf is exposed

- **Procore downmarket pressure** — highest-severity threat.
- **Buildertrend + AI integration** — residential segment risk.
- **Handoff expansion into commercial / operations** — funded, US-constrained, but architecturally aggressive.
- **Access Coins Evo Copilot moving downmarket in UK** — if the conversational ERP pattern moves into the Site Samurai / Eque2 / BuildersAI tier, Kerf's UK conversational claim erodes in 12-18 months.
- **SmartCraft consolidating a UK or DE national champion** — could become the pan-European player Kerf's strategy anticipates being.
- **SafetyCulture + construction depth** — if they ship construction-specific OSHA traversal + templates, the safety wedge is contested at the low end.

### 8.4 Unclaimed territory Kerf can anchor

- **Contractor-trained AI learning** — ship before Handoff or a JobTread competitor copies the pattern. Kerf's graph architecture makes this faster to build than a relational competitor can retrofit.
- **Contract structure advisory at proposal time** — first-mover in an unclaimed space. Requires careful disclaimer pattern (per principle #15 — advise, don't prescribe) and jurisdictional knowledge (per principle #4 — every output cites a standard).
- **Integrated safety-to-finance connection** — no competitor connects daily safety inspection outcomes to EMR modelling to premium reduction to bid eligibility to revenue impact. Kerf's "show ROI in dollars" principle (#9) aligns with an unclaimed analytic story.
- **Cross-jurisdiction SMB platform for Europe** — SmartCraft is the Nordic version of this. An English-first-but-multilingual SMB platform for UK / IE / DE / FR / ES / IT / NL / BE / Nordic SMEs is genuine whitespace.

### 8.5 Open questions this scan does not answer

- **Access Coins Evo Copilot depth** — vendor marketing claims "conversational construction AI" but technical depth (graph traversal, regulatory reasoning, memory across sessions) is not publicly documented. Worth a demo before the next strategic planning cycle.
- **SmartCraft acquisition pipeline** — they are an active consolidator. Knowing what they are shopping for (UK? DE?) would materially change Kerf's UK/DE entry timing.
- **Handoff's operations-expansion roadmap** — they will not stay in residential estimating. When they move into job tracking / daily logs / safety, the competitive picture in US residential changes materially.
- **European regulatory encoding cost** — the scan covers 10+ European countries. The operational cost of encoding each jurisdiction's regulations into the graph with 100% life-safety human verification (per Kerf's agentic infrastructure playbook) is not scoped in this research.

---

## Appendix A — Methodology Limitations

1. **Language bias.** Searches in English returned richer results than searches in DE/FR/IT/ES/PL. German / French / Italian / Spanish / Polish competitors may have been undercounted. Dutch / Flemish products likely underrepresented.
2. **Vendor-documentation depth varies.** Access Coins Evo and CMiC have thin public docs (enterprise sales motion). Capability claims are less well-sourced than for Procore or JobTread.
3. **Pricing is a snapshot.** Many vendors do not list pricing publicly; quoted ranges are best-effort.
4. **"Scope coverage" is interpretive.** The 11 process areas are Kerf's taxonomy; a competitor that bundles "safety + quality + inspections" as one module scores differently than one that ships them as three.
5. **This scan does not reflect private or unreleased capability.** Startups in stealth, unreleased product roadmaps, and enterprise features not publicly documented are absent.
6. **AU / NZ / ROW** intentionally excluded per handoff scope.

---

## Appendix B — Sources Summary

All URLs accessed 2026-04-18 unless noted.

**Strategy + vision context:**
- `docs/PRODUCT_STRATEGY.md` §3 (competitive positioning)
- `docs/PRODUCT_VISION.md` §3, §5, §6, §9 (what Kerf does, personas, principles, moat)

**Vendor help centres (primary sources):**
- [knowify.zendesk.com](https://knowify.zendesk.com/hc/en-us/articles/360025900352-Tracking-jobs-by-contract-status)
- [support.jobnimbus.com/what-are-stages](https://support.jobnimbus.com/what-are-stages)
- [kb.contractorforeman.com](https://kb.contractorforeman.com/)
- [pro.houzz.com/pro-help](https://pro.houzz.com/pro-help/r/status-breakdown-for-proposals-invoices-and-purchase)
- [help.getjobber.com](https://help.getjobber.com/hc/en-us/articles/115012715008-Quote-Approvals)
- [help.servicetitan.com](https://help.servicetitan.com/how-to/statuses-actions)
- [buildertrend.com/help-article](https://buildertrend.com/help-article/estimate-overview/)
- [jobtread.com/features/cost-catalog](https://www.jobtread.com/features/cost-catalog)

**Vendor marketing (primary claims):**
- [procore.com](https://www.procore.com/), [handoff.ai](https://handoff.ai/), [knowify.com](https://knowify.com/), [jobtread.com](https://www.jobtread.com/), [buildertrend.com](https://buildertrend.com/), [safetyculture.com](https://safetyculture.com/), [planradar.com](https://www.planradar.com/), [dalux.com](https://www.dalux.com/), [letsbuild.com](https://www.letsbuild.com/), [smartcraft.com](https://smartcraft.com/), [coins-global.com](https://www.coins-global.com/), [theaccessgroup.com/construction](https://www.theaccessgroup.com/en-us/construction/), [eque2.co.uk](https://www.eque2.co.uk/), [integrity-software.net](https://www.integrity-software.net/), [sitesamurai.co.uk](https://www.sitesamurai.co.uk/)

**Independent comparison + industry coverage:**
- [g2.com](https://www.g2.com/), [capterra.com](https://www.capterra.com/), [softwareworld.co](https://www.softwareworld.co/), [selecthub.com](https://www.selecthub.com/), [softwareadvice.com](https://www.softwareadvice.com/)

**Regional / national-language:**
- **DE:** [hero-software.de](https://hero-software.de/), [plancraft.com/de-de](https://plancraft.com/de-de), [winworker.de](https://www.winworker.de/), [pds.de](https://pds.de/), [openhandwerk.de](https://openhandwerk.de/), [handwerk-digitalisieren.de](https://www.handwerk-digitalisieren.de/handwerkersoftware-test/)
- **FR:** [costructor.co](https://costructor.co/), [batappli.fr](https://www.batappli.fr/), [ebp.com](https://www.ebp.com/logiciel-devis-facture-batiment/), [progbat.com](https://www.progbat.com/), [obat.fr](https://www.obat.fr/), [lio-app.com](https://lio-app.com/logiciel-facturation/btp/), [axonaut.com/blog/logiciel-btp](https://axonaut.com/blog/logiciel-btp/)
- **ES:** [presto-software.com](https://presto-software.com/), [rib-software.es](https://www.rib-software.es/), [buildgets.com](https://www.buildgets.com/), [banktrack.com/blog/programas-presupuestos-obra](https://banktrack.com/blog/programas-presupuestos-obra)
- **IT:** [factorial.it/blog/i-migliori-software-per-la-gestione-dei-cantieri](https://factorial.it/blog/i-migliori-software-per-la-gestione-dei-cantieri/), [cantieri-intelligenti.it](https://www.cantieri-intelligenti.it/gestionale_cantiere), [exeprogetti.it](https://www.exeprogetti.it/prodotti/software-gestionale-edison-edile)
- **PL:** [connecto.pl](https://www.connecto.pl/oprogramowanie-dla-budownictwa/), [penta.com.pl/software/oprogramowanie-dla-budownictwa](https://penta.com.pl/software/oprogramowanie-dla-budownictwa/program-winbud-kosztorys/), [programy-kosztorysowe.pl](https://programy-kosztorysowe.pl/), [progpol.com](https://progpol.com/home/kontrola-kosztow-budowy/)

**AI + contract management tooling:**
- [documentcrunch.com](https://www.documentcrunch.com/), [mastt.com/software/contract-management-software-ai](https://www.mastt.com/software/contract-management-software-ai), [sirion.ai/library/clm-platform/construction-contract-management-software](https://www.sirion.ai/library/clm-platform/construction-contract-management-software/), [ment.tech/ai-construction-contract-management-software](https://www.ment.tech/ai-construction-contract-management-software/)

**Investor / corporate:**
- [news.cision.com/smartcraft-asa](https://news.cision.com/smartcraft-asa/r/smartcraft-asa--smcrt----acquiring-coredination-and-strengthening-nordic-construction-software-leade,c3806352) (SmartCraft acquisition)
- [causeway.com/news/causeway-acquires-letsbuild-aproplan](https://www.causeway.com/news/causeway-acquires-letsbuild-aproplan) (Causeway acquiring LetsBuild)

---

*Scan complete. 79 competitors documented across US / Canada / UK / Ireland / Germany / Austria / France / Belgium / Netherlands / Denmark / Sweden / Norway / Finland / Spain / Italy / Poland.*
