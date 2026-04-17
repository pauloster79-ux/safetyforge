# Kerf Estimating Experience — Conversational Flow & Output Examples

*Reference document for product design. Two complete scenarios showing how the agent adapts guidance depth to contractor scale, and the full client-facing outputs produced.*

---

## SCENARIO 1: Jake Torres — Solo Electrician

**Profile:** Licensed electrician, works alone or with one helper. Revenue ~$180K/year. Residential and light commercial — panel upgrades, kitchen remodels, small tenant fit-outs. Estimates in his head. No written proposals. Tracks nothing.

**Job:** Panel upgrade and circuit additions for a homeowner renovation in Phoenix, AZ.

**What Kerf knows about Jake (after 15 completed jobs):**
- His actual panel upgrade labour averages 6.2 hours (he used to guess 4-5)
- His receptacle install rate is 0.38 hours/outlet in renovations (0.28 in new construction)
- He marks up materials 15% and targets 20% margin on labour
- He always forgets to include permit fees
- He undercharges for attic work (his actual rate is 40% slower than standard ceiling work)
- His helper costs him $28/hour loaded
- He lost $1,400 on the Greenfield job because the homeowner added 4 circuits mid-job and he didn't document it as extra work
- City Electric Supply is his regular supplier; he has current pricing from his last PO

---

### The Conversation

**Jake** *(standing in the client's kitchen)*: Starting an estimate. Maria Gonzalez, 1847 East Meadow Drive. She wants a 200-amp panel upgrade — existing panel is a Federal Pacific, needs to come out. Then she's adding circuits for a kitchen remodel. Let me walk through it.

**Kerf**: Got it. New project created — Maria Gonzalez, 1847 E Meadow Drive, Phoenix. Panel replacement plus kitchen circuits. I'll capture items as you go. Is this a homeowner direct, or are you subbing to a GC?

**Jake**: Direct to homeowner.

**Kerf**: OK. Walk me through what you're seeing.

**Jake**: Main panel is in the garage, 150-amp Federal Pacific Stab-Lok. Replacing with 200-amp, 40-space. Service entrance cable from the meter is maybe 15 feet, it's on the other side of the wall. I'll need to coordinate the utility disconnect with APS.

**Kerf**: Noted. On your last three panel swaps, APS coordination averaged a 2-hour wait on disconnect day. Want me to include that wait time?

**Jake**: Yeah, good call.

**Kerf**: Got it. What about the Federal Pacific — is the homeowner aware there may be asbestos in the panel backing? Your Verde Valley job had that issue and added $800 for abatement.

**Jake**: Good point. I'll check. For now, note it as a potential extra and I'll look when I open it up.

**Kerf**: Flagged as exclusion with note. Keep going — what's happening in the kitchen?

**Jake**: OK so she's doing a full kitchen remodel. I need: 2 dedicated 20-amp circuits for countertop receptacles — GFCI. 1 dedicated circuit for the dishwasher. 1 dedicated circuit for the disposal. She's adding a gas range so I just need the igniter outlet behind it. Microwave circuit above. 6 receptacles along the countertop, plus 2 on the island — those'll need a floor box. And she wants under-cabinet LED lighting on a dimmer.

**Kerf**: That's 6 new dedicated circuits plus the general receptacle and lighting work. A couple of things based on your past jobs:

1. The island floor box — your last two floor box installs in slab-on-grade averaged 1.8 hours, not the 1 hour you usually estimate. This house is slab-on-grade from the listing data. Want to use 1.8?
2. Under-cabinet LEDs — are you supplying the fixtures, or is the homeowner buying them and you're just doing the wiring?
3. 2021 NEC requires AFCI protection on all kitchen circuits in Arizona. That adds ~$45 per breaker over standard. Are you pricing AFCI breakers?

**Jake**: Good catches. Yeah use the 1.8 for the floor box. She's buying the LED fixtures, I'm just running the low-voltage wire and the transformer. And yes on the AFCI breakers.

**Kerf**: Got it. Anything else in the kitchen or other rooms?

**Jake**: That's it. Just the panel and the kitchen.

**Kerf**: OK, pulling this together. One more thing — your last 4 residential jobs, you didn't include the permit fee in your price and then ate it. Phoenix residential electrical permit for this scope is $134. Want to include it as a line item or exclude it in the terms?

**Jake**: Include it. You're right, I keep eating that.

**Kerf**: Here's your estimate. I've used your actual labour rates from your last 15 jobs, current City Electric Supply pricing from your March PO, and the AFCI requirement. Take a look.

---

### The Output: Proposal to Homeowner

*(What Kerf generates as a PDF for Jake to send to Maria Gonzalez)*

---

**JAKE TORRES ELECTRICAL LLC**
ROC #298451 | Licensed, Bonded, Insured
Phoenix, AZ | (602) 555-0147 | jake@jtelectrical.com

---

**PROPOSAL**

**Prepared for:** Maria Gonzalez
**Property:** 1847 East Meadow Drive, Phoenix, AZ 85016
**Date:** April 14, 2026
**Valid for:** 30 days

---

**PROJECT DESCRIPTION**

Electrical panel upgrade and kitchen remodel circuit installation at the above property.

---

**PRICING**

| # | Description | Qty | Unit | Amount |
|---|---|---|---|---|
| | **Panel Upgrade** | | | |
| 1 | Remove existing 150A Federal Pacific panel and all breakers | 1 | EA | — |
| 2 | Supply and install 200A 40-space main breaker panel (Square D Homeline) | 1 | EA | — |
| 3 | Replace service entrance cable, meter to panel (~15 LF) | 15 | LF | — |
| 4 | Transfer all existing circuits to new panel, label, and test | 1 | LS | — |
| 5 | Coordinate utility disconnect/reconnect with APS (includes wait time) | 1 | LS | — |
| 6 | Ground rod and bonding to current code | 1 | LS | — |
| | **Panel Upgrade Subtotal** | | | **$3,280** |
| | | | | |
| | **Kitchen Circuits** | | | |
| 7 | Dedicated 20A GFCI circuit — countertop receptacles (×2 circuits) | 2 | EA | — |
| 8 | Dedicated 20A circuit — dishwasher | 1 | EA | — |
| 9 | Dedicated 20A circuit — garbage disposal | 1 | EA | — |
| 10 | Dedicated 120V outlet — gas range igniter | 1 | EA | — |
| 11 | Dedicated 20A circuit — microwave (above range) | 1 | EA | — |
| 12 | Countertop GFCI receptacles (installed in new backsplash location) | 6 | EA | — |
| 13 | Island floor box with duplex receptacle (slab-on-grade core drill) | 2 | EA | — |
| 14 | Under-cabinet LED lighting circuit with dimmer switch — wiring and transformer only | 1 | LS | — |
| 15 | AFCI breakers for all new kitchen circuits (required per 2021 NEC) | 6 | EA | — |
| | **Kitchen Subtotal** | | | **$4,840** |
| | | | | |
| | **Other** | | | |
| 16 | City of Phoenix electrical permit | 1 | EA | $134 |
| 17 | Final inspection coordination | 1 | LS | — |
| | | | | |
| | **PROJECT TOTAL** | | | **$8,254** |

---

**WHAT'S INCLUDED**

- All labour and materials to complete the scope described above
- All wire, conduit, boxes, connectors, breakers, receptacles, cover plates, and hardware
- AFCI-rated breakers on all new kitchen circuits per current Arizona electrical code (2021 NEC)
- GFCI protection on all countertop and island receptacles
- APS utility disconnect/reconnect coordination
- Permit and final inspection
- Cleanup and removal of old panel and debris
- 1-year workmanship warranty on all labour

**WHAT'S NOT INCLUDED**

- Under-cabinet LED fixtures (owner-supplied; contractor installs wiring and transformer only)
- Drywall patching, painting, or finish work at any penetration or chase location
- Any work behind the meter or on the utility side of the service
- Asbestos abatement — if asbestos-containing materials are found in the existing panel backing or surrounding area, abatement by a licensed contractor will be required before electrical work can proceed. This will be priced as additional work if encountered.
- Structural modifications — if the existing panel location cannot accommodate the new 200A panel without framing modifications, this will be priced as additional work
- Any circuits, outlets, or fixtures not listed above
- Work in attic spaces, crawl spaces, or areas requiring special access beyond the garage and kitchen

**ASSUMPTIONS**

- Existing service entrance conduit and meter base are in serviceable condition and do not require replacement
- The existing wiring from the panel to all current circuits is in acceptable condition (no aluminium branch wiring requiring remediation)
- The homeowner's kitchen contractor will have backsplash and cabinet locations marked before receptacle rough-in
- Access to all work areas will be clear and available during normal working hours (7:00 AM – 4:00 PM, Monday – Friday)
- Work will be completed in approximately 2–3 working days, subject to APS scheduling for the disconnect

**ADDITIONAL WORK**

Any work requested beyond the scope described above will be performed on a time-and-materials basis at $95/hour plus materials at cost + 15%, with your approval before work begins. Additional work will be documented and invoiced separately.

**PAYMENT TERMS**

- 50% deposit upon acceptance of this proposal
- 50% balance due upon completion and final inspection approval
- Accepted payment methods: check, Zelle, or credit card (3% processing fee applies to credit card)

---

**ACCEPTANCE**

To accept this proposal, sign below and return with the deposit. This proposal is valid for 30 days from the date above. Pricing is subject to change after the expiration date due to material cost fluctuations.

Homeowner Signature: _________________________ Date: ___________

Contractor Signature: _________________________ Date: ___________

---

### What the Agent Did That Jake Wouldn't Have Done Alone

1. **Included APS wait time** — 2 hours of dead time Jake always eats
2. **Flagged asbestos risk** — excluded it properly instead of discovering it mid-job
3. **Corrected floor box labour** — used Jake's actual 1.8 hours, not his habitual underestimate
4. **Added AFCI breakers** — code requirement Jake sometimes forgets to price
5. **Included the permit fee** — $134 Jake has eaten on 4 consecutive jobs
6. **Structured the "additional work" clause** — so when Maria asks for "just one more outlet" during the job, Jake has a documented mechanism to charge for it. This is the clause that would have saved him $1,400 on the Greenfield job.
7. **Separated owner-supplied fixtures** — clear responsibility boundary for the LEDs
8. **Documented assumptions about existing conditions** — if the service entrance conduit is rotted, or there's aluminium wiring, Jake has a basis to price additional work

**Time to produce:** ~8 minutes of conversation while walking the property, versus 0 minutes (Jake's previous method was a verbal quote from memory, no documentation, no terms).

---

---

## SCENARIO 2: Sarah Chen — 45-Person Electrical Contractor

**Profile:** Chen Electrical Services, Atlanta, GA. 45 employees, 3 crews. Commercial and light industrial. Revenue ~$8M/year. Sarah is owner, lead estimator, and PM on major jobs. Subs to GCs on most work. Has a part-time office admin.

**Job:** Electrical fit-out of a 2-storey medical office building, 8,400 SF. General contractor is Peterson GC. Competitive bid — Peterson is getting 3-4 electrical quotes.

**What Kerf knows about Sarah (after 38 completed jobs):**
- Her crew's actual productivity on commercial receptacle install is 0.35 man-hours/device (industry book rate is 0.25, but her crews work in renovation conditions 60% of the time)
- Her loaded labour rate (journeyman) is $68.40/hour including burden (base $44, 36% on-cost, 15% non-productive time)
- Her apprentice loaded rate is $38.20/hour
- She typically runs a 2-person crew (1 journeyman + 1 apprentice) on medical office work
- Her actual conduit productivity is 32 LF/hour for EMT in commercial drop ceilings (book rate is 40)
- She targets 18-22% margin on GC work, higher on direct-to-owner
- Peterson GC has delayed site access on 3 of the last 5 jobs, averaging 11 days late
- Peterson's standard subcontract has a 10% retention clause and 45-day payment terms
- Her material markup is 10% on GC jobs
- She has current pricing from City Electric Supply (her primary distributor) and Graybar (secondary)
- She lost $12K on the Buckhead Dental job because she priced prelims as a lump sum and Peterson delayed her 6 weeks — she couldn't substantiate a delay claim because her overhead wasn't broken out by duration
- Medical office work requires dedicated circuits for every exam room (imaging, sterilisation equipment) — she's done 4 medical offices and knows the typical scope

---

### The Conversation

**Sarah** *(at her desk after the site walk, reviewing the plans Peterson sent)*: Starting an estimate. Peterson GC, 4th Street medical office. They sent the bid package yesterday. I walked it this morning and took photos. Let me upload the plans and specs.

**Kerf**: Project created — Peterson GC, 4th Street Medical Office. I see you've uploaded 14 files. Let me process those. While I'm reading, what are the key bid conditions?

**Sarah**: Lump sum subcontract. They want our price by Friday the 18th. Their schedule shows electrical rough-in starting June 2nd, substantial completion October 15th — about 19 weeks. They're getting three other electrical quotes.

**Kerf**: Got it. A few things before we start on the scope:

1. **Peterson GC access history.** On your last 5 Peterson jobs, they've been late on site access 3 times, averaging 11 days. Your Buckhead Dental loss was partly because your prelims weren't duration-based and you couldn't claim the delay. Do you want to structure your prelims by duration this time so we have a variation basis if they're late again?

2. **Peterson's subcontract terms.** Their standard form has 10% retention and net-45 payment. On your last job, they held retention for 97 days past substantial completion. Do you want to flag retention release timing in your offer?

3. **Medical office scope.** Based on your last 4 medical offices, there are typically dedicated circuit requirements for each exam room that aren't always shown on the electrical drawings — imaging equipment, autoclaves, suction units. The mechanical drawings usually show the equipment but the electrical drawings sometimes miss the dedicated circuits. Want me to cross-reference when I finish reading the plans?

**Sarah**: Yes to all three. Good catch on the cross-reference — that's exactly what happened on Peachtree Medical.

**Kerf**: I've finished reading the plans and specifications. Here's my initial scope summary:

**Building:** 2-storey medical office, 8,400 SF (4,200 per floor). Steel frame, drop ceiling, concrete slab on grade.

**Electrical scope from drawings:**
- 200A 3-phase service, 2 distribution panels (one per floor)
- 84 standard receptacles
- 22 dedicated receptacles (exam rooms, lab, imaging, break room appliances)
- 16 data/low-voltage locations (cabling by others, we provide conduit and boxes)
- 143 light fixtures (mix of 2×4 troffers, exam lights, can lights in corridors)
- 12 switches and 6 dimmers
- 8 emergency/exit lights with battery backup
- Fire alarm conduit and boxes (FA system by fire alarm contractor, we provide raceways)
- Mechanical equipment connections: 2 RTUs, 1 split system, 1 exhaust fan

**Spec requirements noted:**
- All wiring in EMT conduit (no MC cable)
- Arc-fault protection on all 15A and 20A circuits per 2020 NEC
- Generator transfer switch and connection (generator by owner, we install ATS and connection)
- Metering for each tenant space (3 meters)

**Cross-reference flag:** The mechanical drawings show an autoclave in the sterilisation room and a panoramic X-ray unit in imaging. Neither has a corresponding dedicated circuit on the electrical drawings. Based on your Peachtree Medical job, the autoclave needed a 30A 208V circuit and the X-ray unit needed a 20A dedicated with isolated ground. Want me to include these and note them as plan discrepancies in your offer?

**Sarah**: Yes. Include them in our price but call them out as items we added based on the mechanical drawings. If they're in, we've covered them. If they strip them, we can reduce. Either way, we look thorough and it protects us from a variation dispute later.

**Kerf**: Smart. I also notice the spec calls for EMT throughout — no MC cable. Your MC cable productivity is about 20% faster than EMT in drop ceilings. Going to EMT adds roughly 180 labour hours to this job compared to MC. Do you want to note in your offer that a value engineering option exists to switch to MC cable for corridors and non-patient areas, with a potential saving? It might differentiate your bid.

**Sarah**: Yes. Show the base price with EMT as specified, and a VE option for MC in non-clinical areas. What's the saving look like?

**Kerf**: Based on your crew rates and the conduit quantities, switching corridors and admin areas to MC cable would save approximately $8,200 in labour and add approximately $2,100 in material cost (MC cable costs more per foot than EMT). Net saving to Peterson: roughly $6,100. I'll include it as an alternate.

**Sarah**: Perfect. Let's build this out. Give me the full estimate.

---

*(The agent now builds the complete estimate from the plan takeoff, Sarah's historical productivity rates, current supplier pricing, and the scope decisions made in conversation. Sarah reviews the detailed worksheets, adjusts a few items based on site conditions she noted during the walk, and approves the final numbers. That review process takes about 20 minutes.)*

---

### The Output: Letter of Offer to Peterson GC

*(What Kerf generates as the formal bid submission)*

---

**CHEN ELECTRICAL SERVICES, INC.**
Georgia Contractor License #EN-214538
1240 Chattahoochee Avenue NW, Suite 200, Atlanta, GA 30318
(404) 555-0283 | estimating@chenelectrical.com

---

**LETTER OF OFFER — ELECTRICAL SUBCONTRACT**

**Date:** April 14, 2026
**Reference:** Peterson GC Tender — 4th Street Medical Office Building
**Attention:** Mark Peterson, Peterson General Contractors

Dear Mr. Peterson,

Chen Electrical Services is pleased to submit the following lump sum offer for the electrical installation at the above-referenced project. This offer is based on the documents listed in Section 7 and the terms set out below.

---

**1. CONTRACT PRICE**

| Division | Description | Amount |
|---|---|---|
| **1.0** | **Electrical Distribution** | |
| 1.1 | 200A 3-phase main switchboard and service entrance | $18,400 |
| 1.2 | Distribution panels — Level 1 (42-circuit) | $4,200 |
| 1.3 | Distribution panels — Level 2 (42-circuit) | $4,200 |
| 1.4 | Automatic transfer switch — 200A (generator connection; generator by owner) | $6,800 |
| 1.5 | Tenant metering — 3 CT meter sockets | $3,600 |
| | *Distribution subtotal* | *$37,200* |
| | | |
| **2.0** | **Branch Circuit Wiring** | |
| 2.1 | EMT conduit, wire, and fittings — lighting circuits (est. 2,800 LF conduit) | $28,700 |
| 2.2 | EMT conduit, wire, and fittings — receptacle circuits (est. 3,400 LF conduit) | $33,200 |
| 2.3 | EMT conduit, wire, and fittings — dedicated equipment circuits (est. 1,100 LF conduit) | $14,800 |
| 2.4 | EMT conduit, wire, and fittings — mechanical equipment connections (est. 600 LF conduit) | $7,400 |
| 2.5 | AFCI breakers — all 15A and 20A branch circuits (per NEC 210.12) | $4,500 |
| | *Branch circuit subtotal* | *$88,600* |
| | | |
| **3.0** | **Devices and Terminations** | |
| 3.1 | Standard duplex receptacles — supply and install (84 locations) | $6,400 |
| 3.2 | Dedicated receptacles — supply and install (22 locations, various configurations) | $3,800 |
| 3.3 | Data/low-voltage conduit and boxes — pathway only, cabling by others (16 locations) | $2,900 |
| 3.4 | Switches (12) and dimmers (6) — supply and install | $1,600 |
| | *Devices subtotal* | *$14,700* |
| | | |
| **4.0** | **Lighting** | |
| 4.1 | 2×4 LED troffer — supply and install (86 fixtures) | $18,200 |
| 4.2 | Exam room light fixtures — supply and install (24 fixtures) | $7,800 |
| 4.3 | Recessed can lights, corridors — supply and install (21 fixtures) | $3,400 |
| 4.4 | Decorative fixtures, reception and waiting — supply and install (12 fixtures) | $4,200 |
| 4.5 | Emergency/exit lights with battery backup — supply and install (8 fixtures) | $2,400 |
| 4.6 | Lighting controls — switches, dimmers, and occupancy sensors per specification | $3,200 |
| | *Lighting subtotal* | *$39,200* |
| | | |
| **5.0** | **Mechanical Equipment Connections** | |
| 5.1 | RTU #1 — disconnect, whip, and final connection | $1,800 |
| 5.2 | RTU #2 — disconnect, whip, and final connection | $1,800 |
| 5.3 | Split system — disconnect, whip, and final connection | $1,200 |
| 5.4 | Exhaust fan — disconnect, whip, and final connection | $800 |
| | *Mechanical connections subtotal* | *$5,600* |
| | | |
| **6.0** | **Fire Alarm Raceways** | |
| 6.1 | Fire alarm conduit, boxes, and device rings — raceways only, FA system by others | $4,800 |
| | | |
| **7.0** | **Items Added from Mechanical Drawing Review** | |
| 7.1 | Autoclave — 30A/208V dedicated circuit with disconnect (Sterilisation Rm 204) — not shown on electrical drawings, identified from mechanical dwg M-3 | $1,400 |
| 7.2 | Panoramic X-ray unit — 20A dedicated circuit with isolated ground (Imaging Rm 108) — not shown on electrical drawings, identified from mechanical dwg M-2 | $1,100 |
| | *Added items subtotal* | *$2,500* |
| | | |
| **8.0** | **Project Management and Supervision** | |
| 8.1 | Foreman — 19 weeks × 40 hours (on-site supervision, full duration) | $12,800 |
| 8.2 | Project management — 19 weeks × 8 hours/week (coordination, submittals, scheduling) | $10,400 |
| 8.3 | Submittals, shop drawings, and O&M manuals | $2,200 |
| 8.4 | As-built drawings | $1,800 |
| | *PM and supervision subtotal* | *$27,200* |
| | | |
| **9.0** | **Mobilisation and General Requirements** | |
| 9.1 | Mobilisation and site setup (1 occurrence) | $2,400 |
| 9.2 | Demobilisation and final cleanup | $1,600 |
| 9.3 | Temporary power and lighting during construction (if not provided by GC) | $3,200 |
| 9.4 | Testing, energisation, and commissioning | $4,800 |
| 9.5 | Permit fees — City of Atlanta electrical permit | $1,460 |
| | *Mobilisation subtotal* | *$13,460* |
| | | |
| | | |
| | **TOTAL LUMP SUM PRICE** | **$233,260** |

---

**VALUE ENGINEERING OPTION**

| Option | Description | Adjustment |
|---|---|---|
| VE-1 | Substitute MC cable for EMT conduit in non-clinical areas (corridors, admin offices, break room, storage) — approximately 1,800 LF. Clinical/exam areas remain EMT per specification. | **Deduct $6,100** |
| | **Revised total with VE-1** | **$227,160** |

*Note: MC cable is permitted under NEC and Georgia amendments for the areas identified. Clinical areas remain in EMT per specification. This substitution reduces installation time by approximately 180 labour hours with no change to system performance.*

---

**2. SCOPE OF WORK — INCLUSIONS**

The following is included in our lump sum price:

- All electrical labour, materials, equipment, and supervision to complete the scope described in Section 1
- All wire, conduit (EMT), fittings, boxes, connectors, breakers, devices, and cover plates
- All light fixtures as scheduled on drawings E-4 through E-7
- AFCI breakers on all 15A and 20A branch circuits per NEC 210.12
- Fire alarm raceways, boxes, and device rings (fire alarm system and devices by FA contractor)
- Data/low-voltage conduit and boxes as pathway (structured cabling by data contractor)
- Mechanical equipment final connections per specifications and mechanical drawings
- Automatic transfer switch supply and installation (generator and fuel system by owner)
- All required permits and inspections
- Submittal packages, shop drawings, as-built drawings, and O&M documentation
- Testing, energisation, and commissioning of all electrical systems
- Project management and coordination for 19 weeks per your issued schedule
- One (1) mobilisation and one (1) demobilisation
- Cleanup of our work areas throughout and at project completion

---

**3. SCOPE OF WORK — EXCLUSIONS**

The following is expressly excluded from our price:

- **Fire alarm system** — devices, panels, programming, monitoring, and commissioning (raceways and boxes only by us)
- **Structured data cabling** — all cabling, patch panels, racks, and terminations (conduit and boxes only by us)
- **Security and access control systems** — all devices, wiring, and programming
- **Audio/visual systems** — speakers, displays, wiring, and programming
- **Generator and fuel system** — supply, installation, fuel piping, pad, and enclosure (ATS and connection only by us)
- **Telephone/nurse call system** — devices and cabling (we provide conduit if shown on drawings)
- **Medical gas alarm panels** — wiring by medical gas contractor
- **Furniture connections** — any modular furniture whips or connections not shown on electrical drawings
- **Excavation, trenching, or underground work** — if required for site electrical beyond the building service entrance
- **Temporary power and lighting** if provided by GC under a separate arrangement
- **Drywall, ceiling, or finish repair** at our penetration locations — GC/drywall contractor to patch
- **Painting or touch-up** at any electrical device or equipment location
- **Asbestos, lead, or hazardous material abatement**
- **Premium time, overtime, shift work, or acceleration** unless separately agreed and priced
- **Material price escalation beyond 90 days** from this offer date (see Section 6)

---

**4. QUALIFICATIONS AND ASSUMPTIONS**

Our price is based on the following assumptions. If any prove incorrect, we reserve the right to adjust our price accordingly.

**4.1 Documents Relied Upon**

Our price is based exclusively on the following documents provided by Peterson GC on April 10, 2026:

| Document | Revision | Date |
|---|---|---|
| Architectural drawings A-1 through A-12 | Rev B | 2026-03-28 |
| Electrical drawings E-1 through E-8 | Rev A | 2026-03-15 |
| Mechanical drawings M-1 through M-6 | Rev A | 2026-03-15 |
| Plumbing drawings P-1 through P-4 | Rev A | 2026-03-15 |
| Specification Division 26 — Electrical | Rev A | 2026-03-15 |
| Peterson GC Project Schedule (preliminary) | Rev 0 | 2026-04-08 |

Any subsequent revisions, addenda, or RFI responses issued after our submission may result in a price adjustment.

**4.2 Schedule**

- Our price is based on the project schedule issued April 8, 2026, showing electrical rough-in commencing June 2, 2026 and substantial completion October 15, 2026 — a duration of 19 weeks.
- **Our project management and supervision costs (Section 1, Item 8.0) are calculated on a 19-week duration.** If the project duration extends beyond 19 weeks for reasons not caused by Chen Electrical, we will submit a variation for the additional overhead at the weekly rates set out below:
  - Foreman: $672/week
  - Project management: $547/week
- We have allowed for **one (1) mobilisation and one (1) demobilisation.** If site access is interrupted and remobilisation is required, each additional mobilisation will be charged at $2,400.
- We require continuous and unimpeded access to our work areas in the sequence shown on the construction schedule. If access is delayed or work areas are not available as scheduled, resulting in crew standby or return visits, this will be priced as additional work.

**4.3 Quantities**

- All quantities in this offer have been measured by Chen Electrical from the documents listed in Section 4.1.
- Conduit quantities are estimated from drawing review and include an allowance for routing, drops, and fittings. Actual installed quantities may vary. Our price is a lump sum based on the scope shown on the drawings — not a measurement of conduit footage.

**4.4 Coordination**

- We have assumed reasonable trade coordination and stacking will be managed by Peterson GC per normal commercial construction practice.
- If excessive trade stacking, out-of-sequence work, or work area congestion results in productivity loss to our crews, we reserve the right to submit a claim for the impact.

**4.5 Design Completeness**

- Items 7.1 and 7.2 (autoclave circuit and X-ray circuit) are not shown on the electrical drawings but are identified on the mechanical drawings. We have included them in our price. If these items are confirmed as not required by the design team, we will issue a credit of $2,500.
- If additional dedicated circuits are identified during construction for medical equipment not shown on either the electrical or mechanical drawings, these will be priced as variations.

**4.6 Site Conditions**

- We have assumed normal commercial construction site conditions.
- We have assumed the building structure, ceilings, and walls will be installed by others in advance of our work, providing clear access for conduit and device installation.
- We have assumed adequate power, water, toilet facilities, and secure storage will be provided by Peterson GC at no cost to our trade.

---

**5. VARIATIONS AND ADDITIONAL WORK**

Any work requested beyond the scope described in this offer will be priced as a variation. Variations will be calculated using the following rates unless otherwise agreed:

| Resource | Rate |
|---|---|
| Journeyman Electrician | $95.00/hour |
| Apprentice Electrician | $58.00/hour |
| Project Manager | $115.00/hour |
| Materials | Cost + 15% |
| Subcontracted work | Cost + 10% |

These rates include all labour burden, insurance, overheads, and profit. Variation pricing will be submitted for approval before work commences unless directed otherwise by Peterson GC in writing.

---

**6. COMMERCIAL TERMS**

**Offer validity:** This offer is valid for 60 days from April 14, 2026. Material pricing is firm for 90 days. If the subcontract is not executed within 90 days of this offer, we reserve the right to adjust material pricing to reflect current supplier costs.

**Payment terms:** We request progress payment monthly based on percentage of work completed, net-30 days from invoice. Retention, if applicable, should not exceed 5% and should be released within 30 days of substantial completion of our scope — not the overall project.

**Insurance:** Chen Electrical maintains the following coverage and can provide certificates upon request:
- General liability: $2,000,000 per occurrence / $4,000,000 aggregate
- Workers' compensation: Statutory limits, Georgia
- Automobile liability: $1,000,000 combined single limit
- Umbrella/excess: $5,000,000

**Warranty:** 1-year warranty on workmanship from the date of substantial completion. Manufacturer warranties on all fixtures and equipment are passed through to the owner.

---

**7. CONTACT**

For questions regarding this offer, please contact:

**Sarah Chen** — President / Lead Estimator
(404) 555-0283 | sarah@chenelectrical.com

We appreciate the opportunity to quote this project and look forward to working with Peterson GC again.

Respectfully submitted,

**CHEN ELECTRICAL SERVICES, INC.**

Sarah Chen
President

---

### What the Agent Did That Protects Sarah's Margin

**1. Duration-based prelims (the Buckhead Dental fix).** Section 8.0 breaks supervision and PM into weekly rates × 19 weeks. Section 4.2 explicitly states that if the project extends beyond 19 weeks for reasons not caused by Chen Electrical, the weekly overhead rates apply. This is the exact structure Tim recommends — and the exact structure Sarah was missing when she lost $12K on the Buckhead Dental job. If Peterson delays site access by 3 weeks (which they've done on 3 of the last 5 jobs), Sarah's variation claim is arithmetic: 3 weeks × ($672 + $547) = $3,657. No argument, no negotiation about what's reasonable. The rates are in the offer.

**2. Mobilisation count qualification.** Section 4.2 explicitly states one mob/demob is included, with additional mobs at $2,400 each. If Peterson's schedule changes force Sarah to demobilise and return, she has a contractual basis to charge.

**3. The autoclave/X-ray cross-reference.** Items 7.1 and 7.2 demonstrate that Sarah read the full drawing set, not just the electrical pages. This does two things: it protects her from missing scope (if those circuits are needed, she's already priced them), and it makes her bid look more thorough than competitors who only read the E-sheets. If Peterson strips them, she offers a credit — she looks collaborative. If they keep them and another bidder missed them, she avoids eating a mid-project variation.

**4. The VE option.** The MC cable alternate saves Peterson $6,100 and differentiates Sarah's bid. If Peterson is comparing 4 bids and Sarah's is $3K higher than the lowest, but she's offering a $6,100 VE option, she may win on net price while having a more comprehensive base scope.

**5. Variation rates in the offer.** Section 5 establishes the rates for additional work *before* the contract is signed. This prevents the mid-project negotiation where the GC says "just do it and we'll sort out the price later" — Sarah can point to agreed rates. Note the rates include margin (journeyman at $95/hr vs. loaded cost of $68.40/hr = 39% markup covering overhead and profit on variations).

**6. Material escalation protection.** Section 6 locks material pricing for 90 days, not indefinitely. If Peterson takes 4 months to execute the subcontract, Sarah isn't locked into pricing from April on copper she buys in August.

**7. Retention and payment terms.** Section 6 requests 5% retention (not Peterson's standard 10%) and release at completion of *her scope*, not the overall project. Peterson held retention for 97 days past substantial completion on the last job. This language gives Sarah a negotiation basis.

**8. Access and stacking clauses.** Section 4.4 qualifies that productivity loss from excessive trade stacking or out-of-sequence work is claimable. This is Tim's point about understanding what drives your costs and qualifying the things outside your control.

---

## HOW THE AGENT ADAPTS BETWEEN SCALES

| Dimension | Jake (Solo Residential) | Sarah (45-Person Commercial) |
|---|---|---|
| **Estimate structure** | Flat list, ~15 line items, single page | Hierarchical WBS, 9 divisions, multi-page |
| **Pricing method** | Bottom-up from labour hours + material cost | Bottom-up from productivity rates × quantities + sub quotes + overhead |
| **Terms complexity** | Simple exclusions, change order clause, payment terms | Full letter of offer with qualifications, schedule reliance, variation rates, insurance, VE options |
| **What the agent checks** | Did Jake forget the permit? Is he underestimating attic work again? | Cross-reference between drawing sets. Peterson's access history. Duration-based overhead structure. Material escalation. |
| **Historical data used** | Jake's actual hours per task type | Crew productivity by work type, loaded labour rates, supplier pricing, GC payment behaviour |
| **Proactive guidance** | 5-6 simple reminders based on past mistakes | Strategic advice: VE options, cross-referencing, prelim structure for variation protection |
| **Output format** | Residential proposal (2 pages) | Formal letter of offer (6+ pages) suitable for commercial subcontract negotiation |
| **Time to produce** | ~8 minutes (during site walk) | ~45 minutes (plan review + conversation + review of detailed worksheets) |

---

## THE LEARNING LOOP

Both proposals get better with every job. The graph captures:

**From Jake's jobs:**
- Actual hours vs. estimated hours per task type (panel swap, receptacle install, floor box, etc.)
- Which exclusions he ended up needing (the asbestos on the Verde Valley job becomes a permanent checklist item)
- Change orders captured vs. missed (after Greenfield, the agent always includes an additional work clause)
- Material cost trends from his POs

**From Sarah's jobs:**
- Crew productivity by work type, building type, and GC (Peterson jobs run 8% slower due to coordination issues)
- Variation success rate by qualification type (duration-based prelim claims have 90% approval; productivity impact claims have 40%)
- Which GCs pay on time and which don't (affects cash flow assumptions and the retention negotiation)
- Which scope items are consistently missed on medical office drawings
- VE option acceptance rate (Peterson has accepted 3 of 5 VE proposals)

After 50 jobs, the agent doesn't just calculate faster — it knows Sarah's business better than she does. It knows which qualifications actually protect her, which GCs are worth the risk, and where her crews consistently over- or under-perform against her estimates. That institutional knowledge currently lives in Sarah's head and disappears if she gets sick, retires, or loses the spreadsheet.

---

## WHAT THIS MEANS FOR KERF'S DATA MODEL

The estimating experience requires these entities and relationships that flow through the lifecycle:

```
Conversation (voice/chat)
  → extracts WorkItems with labour, material, equipment quantities
  → grouped into WorkPackages (divisions)
  → with Assumptions (structured, referenceable)
  → with Exclusions (structured, referenceable)
  → with AlternateOptions (VE proposals, linked to affected WorkItems)
  → snapshot as Estimate (versioned, dated)
  → generates Proposal document (PDF)
  → on award: WorkItems become ScheduleTasks
  → on execution: TimeEntries charged to WorkItems
  → on completion: Actual vs. Estimated comparison feeds back to productivity rates

The terms and conditions are not free text bolted onto a spreadsheet.
They are structured data in the graph — queryable, learnable, referenceable
in future estimates and in variation claims during construction.
```
