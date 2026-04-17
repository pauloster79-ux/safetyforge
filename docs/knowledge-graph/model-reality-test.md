# Model vs Reality Testing

Testing the ontology against real contractor scenarios. Looking for:
- Friction: where does the model force structure the contractor doesn't naturally use?
- Gaps: where does the contractor's reality not fit the model?
- Complexity: what entities/properties are irrelevant for simpler contractors?
- Confusion: where would a contractor not know what to do?

---

## Scenario 1: Jake — Solo Electrician, Residential

**Profile:** One person. Does panel upgrades, kitchen remodels, small tenant fit-outs. Revenue ~£130K/year. No employees. Works alone or with one helper.

**A typical job: Kitchen remodel electrical — rewire, new consumer unit, 12 circuits**

### How Jake actually works:
1. Client calls. Jake drives over, looks at the kitchen, talks through what's needed
2. Standing in the kitchen, he works out the price in his head: "That's about two days, plus the consumer unit, cable, sockets, switches... call it £2,400"
3. He texts the client: "Kitchen electrics, £2,400 including materials"
4. Client says yes
5. He buys materials from the wholesaler on the way to the job
6. Does the work over 2-3 days
7. Sends an invoice via text/email
8. Gets paid by bank transfer

### How this maps to the model:

| Jake's reality | Model entity | Friction? |
|---|---|---|
| "Got a call about a kitchen job" | Project (status: lead) | Fine — but Jake wouldn't think of it as a "project". He'd say "job" |
| "£2,400 including materials" | WorkItem? WorkPackage? | **FRICTION.** Jake doesn't break work into items. It's one job, one price. Does he create one WorkItem called "Kitchen remodel electrics, £2,400"? That works but feels over-structured. He doesn't separately track labour_hours and materials_allowance — it's a lump sum |
| "Client said yes" | Project status → active | Fine |
| "Bought materials at the wholesaler" | Item + USES_ITEM? | **FRICTION.** Jake bought a consumer unit, 100m of cable, 12 sockets, some switches, a roll of tape. He's not going to itemise these against work items. He just spent £600 on materials. Could he just record "materials: £600" as the materials_allowance? |
| "Did the work" | TimeEntry? | **FRICTION.** Jake doesn't clock in and out. He worked Monday and Tuesday. Does he need to create TimeEntries? For what purpose — he's not tracking hours against an estimate, he quoted a fixed price |
| "Sent an invoice" | Invoice | Fine — but it's one line: "Kitchen electrics — £2,400" |
| "Got paid" | Payment | Fine |

### Friction points identified:

1. **Work breakdown is overkill.** Jake has one job, one price. Creating WorkItems with labour_hours and labour_rate and then linking Items with quantities is the OPPOSITE of how he works. He needs: "Kitchen electrics, £2,400, lump sum." One WorkItem, no sub-structure.

2. **Time tracking is irrelevant for fixed-price small jobs.** Jake doesn't bill by the hour. He quoted a price. Time entries add no value unless he wants to learn whether he's pricing correctly (which is a "Learn" phase benefit, not an execution need).

3. **Materials tracking is too granular.** Jake spent £600 at the wholesaler. He doesn't need to link individual items. He just needs to know his cost was £600 against a £2,400 job.

### Does the model handle this?

**Mostly yes, but we need to make sure the minimum viable path is:**
- One Project (or "job")
- One WorkItem: "Kitchen remodel electrics" with materials_allowance: £600
- No WorkPackage, no Items linked, no TimeEntries
- Status: lead → quoted → active → complete → closed
- One Invoice, one Payment

**The model supports this** — WorkItems are flexible (no mandatory quantity, no mandatory Item links, no mandatory TimeEntries). But the question is whether the UI/agent makes this easy or whether it presents all the fields and makes Jake feel like he's using enterprise software.

---

## Scenario 2: Sarah — 45-Person Electrical Contractor, Commercial

**Profile:** Electrical subcontractor. 45 employees. Does commercial fit-outs, medical offices, retail. Revenue ~$8M/year. 6-8 active projects.

**A typical job: Medical office electrical fit-out, $148,000 contract**

### How Sarah actually works:
1. GC invites her to bid. She gets plans and specs
2. She does a takeoff — counts every receptacle, switch, light, panel. 847 items rolled into 23 cost groups
3. She prices it: labour rates per item type × quantities + material costs + markup = $148,200
4. She sends a formal proposal
5. She wins, signs the contract (5% retention, net 30, monthly progress billing)
6. She assigns crews, schedules the work in phases (rough-in, trim, final)
7. Her crews clock in daily, work is tracked by phase
8. Monthly she submits a payment application to the GC
9. She tracks actuals vs budget weekly
10. She captures variations when the architect changes things

### How this maps to the model:

| Sarah's reality | Model entity | Friction? |
|---|---|---|
| "847 items rolled into 23 cost groups" | WorkPackages (cost groups) containing WorkItems | **Good fit.** This is exactly why WorkPackage exists |
| "Labour rates per item type" | WorkItem.labour_hours + labour_rate | **Good fit.** But she prices by item type, not per individual work item. "84 standard receptacles × 0.35 hrs × $85/hr" is one work item, not 84 |
| "Material costs per item" | USES_ITEM on WorkItems | **Good fit.** She does track specific materials at this scale — receptacles, wire, panels are individually priced |
| "5% retention, net 30" | Contract with retention_pct, payment_terms | **Good fit** |
| "Monthly progress billing" | PaymentApplication | **Good fit** |
| "Crews clock in daily" | TimeEntry per worker per day | **Good fit** |
| "Track actuals vs budget weekly" | WorkItem estimated vs TimeEntry actuals | **Good fit** — but requires computed totals to be fast |
| "Architect changes things" | Variation with evidence chain | **Good fit** |

### Friction points:

1. **Mostly works well.** Sarah's workflow is what the model was designed for.
2. **Potential issue: too many WorkItems?** 847 individual items might mean 847 WorkItems. That's a lot of nodes. But in practice she'd group them: "84 standard receptacles" is one WorkItem with quantity on USES_ITEM, not 84 separate WorkItems. Wait — we removed quantity from WorkItem. The quantity is on USES_ITEM. So the WorkItem is "Install standard receptacles in reception" and the USES_ITEM says "84 × Leviton 5320-W". That works.
3. **Takeoff quantities.** Sarah's takeoff produces quantities per item type. These map naturally to WorkItems with USES_ITEM quantities. No friction.

---

## Scenario 3: Marco — Concrete Crew Lead, 22 Workers

**Profile:** Runs a concrete crew of 22 for a mid-size GC. He's not the business owner — he's the field lead. He does the safety walks, time tracking, daily logs.

### What Marco actually does daily:
1. Morning: opens the app, checks today's brief
2. Delivers toolbox talk to crew
3. Does the site walk — safety and quality observations
4. His crew clocks in
5. He records what work was done (daily log)
6. He reports any hazards or incidents
7. End of day: verifies timesheets, submits daily log

### How this maps:

| Marco's reality | Model entity | Friction? |
|---|---|---|
| Morning brief | MorningBrief | Fine |
| Toolbox talk | ToolboxTalk, ATTENDED_BY | Fine |
| Safety walk | Inspection (category: safety) | Fine |
| Quality observations | Inspection (category: quality) | Fine — same walk, two categories |
| Crew clocks in | TimeEntry per worker | Fine, but Marco enters for his crew (foreman_entry) |
| Daily log | DailyLog auto-populated | Fine — this is the core value |
| Hazard report | HazardReport, HazardObservation | Fine |

### Friction points:

1. **Marco doesn't touch WorkItems, Estimates, Contracts, Invoices, Payments.** He's a foreman, not the business owner. His access_role = "foreman" means he shouldn't even see those entities. The permission model handles this — but it means the model needs to work perfectly without the financial layer. Marco's world is: Projects, Workers, Inspections, TimeEntries, DailyLogs, Safety. That subset must feel complete on its own.

2. **No friction for Marco.** The safety/operations layer is already built and tested. The expansion doesn't complicate his experience.

---

## Scenario 4: Dave — GC Building a House

**Profile:** General contractor, 8 employees. Builds custom homes. Revenue ~$3M/year. 3-4 houses at a time. Manages 10-15 subs per project.

### A typical job: Custom home build, $650K contract

### How Dave actually works:
1. Client comes via referral. Dave visits the site, reviews the architect's plans
2. He creates a budget by trade: foundations $45K, framing $78K, electrical $52K, plumbing $38K, HVAC $41K, roofing $28K, drywall $22K, painting $18K, flooring $24K, landscaping $15K, etc.
3. He does some work with his own crew (project management, some carpentry). Everything else is subcontracted
4. He marks up each trade, adds his margin, arrives at $650K
5. He signs a contract with the homeowner
6. He manages the subs — scheduling, compliance, quality, payment
7. He submits monthly draws to the client (or the construction lender)
8. He tracks change orders when the client wants upgrades
9. He manages sub invoices and lien waivers before paying subs

### How this maps:

| Dave's reality | Model entity | Friction? |
|---|---|---|
| "Budget by trade" | WorkPackages by trade (Electrical, Plumbing, etc.) | **Good fit** |
| "Each trade is a sub" | Company (sub) → SUB_ON → Project | **Good fit.** But how does Dave link a WorkPackage to a sub? |
| "Sub compliance" | InsuranceCertificate, PrequalPackage, GcRelationship | **Good fit** — existing entities |
| "Monthly draws" | PaymentApplication | **Good fit** |
| "Client wants upgrades" | Variation | **Good fit** |
| "Sub invoices" | ??? | **GAP.** Dave receives invoices FROM subs. Our Invoice entity is for invoices TO clients. We need to track inbound sub invoices too |
| "Lien waivers before paying subs" | LienWaiver | **Good fit** |
| "Scheduling subs" | WorkItem.planned_start/end by trade | Workable but Dave thinks in terms of "electrical rough-in is week 4-5", not individual work items |

### Friction points:

1. **SUB ↔ WORK PACKAGE link missing.** Dave's WorkPackage "Electrical - $52K" is performed by Sub "ABC Electric." The model doesn't have a direct relationship between WorkPackage and a sub Company. We need: `PERFORMED_BY` (WorkPackage → Company) or similar.

2. **Inbound invoices (from subs to Dave).** Our Invoice entity is designed for invoices Dave sends TO clients. Dave also receives invoices FROM subs. He needs to track: what the sub billed, whether it's approved, whether it's been paid, and whether the lien waiver was received before payment. This might be a separate entity (`SubInvoice`?) or the same Invoice entity with a direction indicator.

3. **Dave doesn't create detailed WorkItems for sub work.** His "Electrical" WorkPackage is $52K with ABC Electric. He doesn't break it into 847 items — that's ABC Electric's problem. He tracks it as a lump sum by trade. The model needs to support WorkPackages WITHOUT WorkItems — just a package with a name, a cost, and a sub assignment. Currently a WorkPackage CONTAINS WorkItems. If Dave never creates WorkItems for subbed trades, the WorkPackage is empty.

4. **Construction lender draws.** The monthly payment application might go to a construction lender, not just the client. The lender has their own requirements (inspection before draw, specific documentation). This is a variant of PaymentApplication — the entity works but the workflow is different.

---

## Scenario 5: Small Plumber — Emergency Callouts

**Profile:** 3-person plumbing company. 80% of work is emergency callouts (burst pipes, blocked drains, boiler repairs). 20% is planned work (bathroom installations).

### A typical job: Emergency callout — burst pipe under kitchen sink

### How this works:
1. Customer calls at 7pm. "There's water everywhere"
2. Plumber drives over. Fixes the pipe. 2 hours on site
3. Charges the customer: £180 callout + £95/hour × 2 + £30 materials = £370
4. Customer pays on the spot (card)

### How this maps:

| Reality | Model entity | Friction? |
|---|---|---|
| Customer calls | Project (status: lead) | **OVERKILL.** This is a 2-hour callout, not a "project." Creating a Project with all its fields for a burst pipe feels absurd. But... it IS a job. Just a very small one |
| Fix the pipe | WorkItem? | Same issue — "Fix burst pipe, £370" is the entire scope |
| Callout + hourly rate + materials | How to price? | **FRICTION.** The plumber prices as: callout fee + hourly rate × hours + materials. This is three components, not a single lump sum. But it's not "work items" either — it's a pricing structure (callout fee is not a work item, it's a fee). Does this map to: one WorkItem with labour_hours: 2, labour_rate: 9500 (£95), materials_allowance: 3000 (£30), plus... where does the callout fee go? |
| Customer pays on spot | Invoice → Payment | Fine, but the "invoice" is a receipt, not a formal document sent in advance |

### Friction points:

1. **Callout fee / fixed fees don't fit neatly.** The model has labour_hours × labour_rate + materials. A callout fee is neither — it's a fixed charge. Options:
   - Add a `fixed_fees` property on WorkItem or Project
   - Treat the callout fee as a separate WorkItem with no labour ("Callout fee, £180, lump sum")
   - Ignore it — the contractor just quotes £370 total as one lump sum WorkItem

2. **The overhead of "Project" for a 2-hour callout.** Every emergency job becomes a Project node. Over a year, this plumber might have 800 callouts = 800 Projects. That's fine for the database (trivial scale). But does the UI make creating a "project" for a burst pipe feel lightweight? This is a UX concern, not a data model concern — the model handles it.

3. **Instant payment.** The customer pays immediately. The invoice and payment happen simultaneously. The model supports this (create Invoice, create Payment, done) but the workflow should be: "job done, customer paid £370" = one action, not three entities created manually.

---

## Scenario 6: Landscape Contractor — Seasonal, Project-Based

**Profile:** 12 employees. Residential landscaping. Revenue ~$1.5M. Highly seasonal (March-November). Does hardscaping (patios, retaining walls), planting, irrigation.

### A typical job: Back garden redesign — patio, retaining wall, planting, irrigation. $35K.

### How this works:
1. Client meeting, walk the garden, discuss ideas
2. Produce a proposal with phases: hardscaping ($18K), planting ($9K), irrigation ($5K), lighting ($3K)
3. Client approves, pays 30% deposit
4. Different crews do different phases (hardscaping crew, planting crew)
5. Materials are significant: stone, soil, plants, pipes, lights
6. Job takes 2-3 weeks
7. Final payment on completion

### How this maps:

| Reality | Model entity | Friction? |
|---|---|---|
| Phases: hardscaping, planting, irrigation | WorkPackages | **Good fit** |
| Different crews per phase | Crew assigned to WorkPackage | **Good fit** — but the relationship is ASSIGNED_TO_CREW on WorkItem, not WorkPackage. Do we need crew assignment at the package level too? |
| 30% deposit | ??? | **GAP.** Deposits/advance payments don't map cleanly. A deposit isn't an invoice for completed work — it's a payment before work starts. Could be a PaymentApplication or Invoice with a note, but neither feels right |
| Significant materials (stone by tonnage, plants by species) | Item + USES_ITEM | **Good fit** for large items. But "2.5 tonnes of Cotswold stone" — is "Cotswold stone" an Item in the global catalogue with default_unit "tonne"? Yes, that works |
| Seasonal business | No model issue | The model doesn't care about seasonality. Projects just happen when they happen |

### Friction points:

1. **Deposits / advance payments.** Common in construction. The client pays 30% before work starts, then staged payments or on completion. Our model has Invoice → Payment for completed work, and PaymentApplication for progress billing. A deposit is neither. Options:
   - An Invoice with a type "deposit" sent before work starts
   - A Payment linked directly to the Project (not to an Invoice)
   - Simplest: Invoice the deposit. It IS an invoice — "Deposit for garden redesign, £10,500." Normal invoice, just issued before work starts

2. **Crew assignment at WorkPackage level.** The hardscaping crew does the whole hardscaping package. Assigning the crew to each individual WorkItem within the package is tedious. Add ASSIGNED_TO_CREW on WorkPackage? Or just assign at WorkItem level and accept the repetition? For a landscaper with 5-10 work items per package, assigning per item is manageable. For Sarah with 200 items in a package, it's not.

---

## Summary of Issues Found

### Gaps (model doesn't cover):

| # | Issue | Scenario | Severity | Proposed Fix |
|---|-------|----------|----------|-------------|
| G1 | Sub invoices (inbound) — Dave receives invoices from subs | Scenario 4 | Medium | Add direction to Invoice or create SubInvoice. Or: Invoice.direction = "outbound" / "inbound" |
| G2 | WorkPackage → Sub company link | Scenario 4 | Medium | Add PERFORMED_BY relationship (WorkPackage → Company) |
| G3 | Deposits / advance payments | Scenario 6 | Low | Handle as Invoice with type "deposit". No model change needed |
| G4 | Crew assignment at WorkPackage level | Scenarios 4, 6 | Low | Add ASSIGNED_TO_CREW on WorkPackage. Simple relationship addition |
| G5 | Fixed fees (callout fee, mobilisation fee) | Scenario 5 | Low | Treat as a WorkItem with no labour. Or add fixed_fees to Project |

### Friction (model works but feels wrong):

| # | Issue | Scenario | Severity | Resolution |
|---|-------|----------|----------|------------|
| F1 | "Project" feels heavy for a 2-hour callout | Scenario 5 | Medium | UX/terminology concern, not data model. Agent/UI should make project creation feel like "logging a job" |
| F2 | WorkItem structure overkill for simple lump-sum jobs | Scenarios 1, 5 | Medium | The model supports one WorkItem with just a description and materials_allowance. But does the UI present it simply enough? |
| F3 | WorkPackage empty when work is subbed out | Scenario 4 | Low | Allow WorkPackage with no WorkItems — just a name, cost, and PERFORMED_BY link to a sub. This is a lump-sum subcontract |
| F4 | Time tracking irrelevant for fixed-price small contractors | Scenario 1 | Low | TimeEntry is optional. No friction if the contractor doesn't use it. But the system shouldn't push it |

### Validation: What works well

| Scenario | What works | Why |
|---|---|---|
| Sarah (commercial sub) | Nearly everything | The model was designed for this complexity level |
| Marco (foreman) | Safety + operations subset | Permission model correctly isolates his view |
| Dave (GC/house builder) | Project structure, sub management, payment applications | WorkPackage by trade maps well |
| Landscaper | Phased work, material tracking, crew assignment | WorkPackage by phase works naturally |
| Jake (solo) | Minimal path: one project, one work item, one invoice | Model supports simplicity — but UI must present it simply |
| Plumber (callouts) | Minimal path works if "project" doesn't feel heavy | Data model is fine. Naming/UX is the concern |

### Key Recommendations

1. **Add PERFORMED_BY (WorkPackage → Company)** for sub-assigned work packages
2. **Add ASSIGNED_TO_CREW on WorkPackage** for crew assignment at package level
3. **Allow WorkPackages to exist without WorkItems** (lump-sum sub packages)
4. **Add direction to Invoice** ("outbound" to client, "inbound" from sub) — or keep as two query paths from the same entity
5. **Terminology is presentation, not data model** — "project" vs "job" vs "callout" is a UI concern. The data model uses Project
6. **The minimum viable path must be dead simple:** Project → one WorkItem → Invoice → Payment. No mandatory WorkPackage, Items, TimeEntries, or anything else for the Jake/plumber path
