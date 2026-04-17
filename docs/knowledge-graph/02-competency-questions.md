# Competency Questions (Revised)

## Lifecycle Stage 1: Find & Qualify

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-001 | Who is this client, and what's our history with them (past projects, outcomes, payment behaviour)? | TRAVERSE | P1 |
| CQ-002 | Have we done similar work before, and how did it go financially? | TRAVERSE | P1 |
| CQ-003 | Do we have the certifications and workforce capacity to take this on? | RULE | P1 |
| CQ-004 | How quickly does this client typically pay? | AGGREGATE | P1 |

## Lifecycle Stage 2: Estimate & Price

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-005 | What did similar work actually cost us on past jobs (labour, materials, by work category)? | AGGREGATE | P1 |
| CQ-006 | What are our real labour rates for this type of work, based on actual time data? | AGGREGATE | P1 |
| CQ-007 | What regulatory requirements apply to this work in this jurisdiction? | RULE | P1 |
| CQ-008 | What does the uploaded plan or specification say about what's needed? | TRAVERSE | P2 |
| CQ-009 | Based on our history, what's a reasonable cost for this work item? | AGGREGATE | P2 |
| CQ-010 | What materials does this work require and what do they typically cost us? | AGGREGATE | P1 |

## Lifecycle Stage 3: Propose & Win

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-011 | What's our win rate with this client? | AGGREGATE | P1 |
| CQ-012 | What's our effective margin at this price, based on how our crews actually perform? | AGGREGATE | P1 |
| CQ-013 | What are the key terms in this contract (retention, payment schedule, scope, penalties)? | TRAVERSE | P2 |
| CQ-014 | What's the status of all our outstanding proposals? | AGGREGATE | P1 |

## Lifecycle Stage 4: Plan & Mobilise

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-015 | Which workers are available and qualified for this work next week? | TRAVERSE | P1 |
| CQ-016 | Do assigned workers have all required certifications valid through the work dates? | RULE | P1 |
| CQ-017 | Is the assigned equipment available and inspection-current for the planned period? | TRAVERSE | P1 |
| CQ-018 | What materials need to be ordered and when, based on the work schedule? | TRAVERSE | P1 |
| CQ-019 | Are there scheduling conflicts — workers or equipment double-booked across projects? | TRAVERSE | P1 |
| CQ-020 | What's scheduled for this week across all my projects? | TRAVERSE | P1 |
| CQ-021 | What's the critical path — which work items must finish before others can start? | TRAVERSE | P2 |

## Lifecycle Stage 5: Execute & Document

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-022 | What happened on this project today (work done, people, deliveries, weather, issues)? | TRAVERSE | P1 |
| CQ-023 | What work remains on this job? | AGGREGATE | P1 |
| CQ-024 | How much of a specific piece of work have we completed vs what was agreed? | TRAVERSE | P1 |
| CQ-025 | Is this worker / project / site compliant right now? | RULE | P1 |
| CQ-026 | What safety hazards have been identified and are they resolved? | TRAVERSE | P1 |
| CQ-027 | Which corrective actions are overdue? | AGGREGATE | P1 |
| CQ-028 | Who was on site today and how long did they work? | TRAVERSE | P1 |
| CQ-029 | Is any worker at fatigue risk (excessive consecutive hours)? | RULE + APP | P1 | Note: requires TimeEntry data + jurisdiction-specific fatigue thresholds. Thresholds configurable per jurisdiction via Regulation nodes where available (EU Working Time Directive) or application-level defaults where no regulatory threshold exists |
| CQ-030 | What quality deficiencies are open and who is responsible for each? | TRAVERSE | P1 |
| CQ-031 | Which work items are blocked and why? | TRAVERSE | P1 |
| CQ-032 | What did we discuss about this project or issue previously? | TRAVERSE | P1 |
| CQ-033 | What decisions have been made about this project and what was the reasoning? | TRAVERSE | P1 |
| CQ-034 | When were we supposed to finish this work / this project? | LOOKUP | P1 |
| CQ-035 | Is a specific worker available to do specific work next week? | TRAVERSE | P1 |

## Lifecycle Stage 6: Manage Money

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-036 | Is this job on budget right now? | AGGREGATE | P1 |
| CQ-037 | Where exactly are we over or under budget on this job (by work item / work category)? | AGGREGATE | P1 |
| CQ-038 | Is this work within the original agreed scope, or is it additional? | RULE | P1 |
| CQ-039 | What evidence supports this variation / change order? | TRAVERSE | P1 |
| CQ-040 | What completed work has not yet been invoiced? | AGGREGATE | P1 |
| CQ-041 | What has been invoiced but not yet paid? | AGGREGATE | P1 |
| CQ-042 | What's my total outstanding receivables and how old are they? | AGGREGATE | P1 |

## Lifecycle Stage 7: Close Out

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-043 | What deficiency / snag list items are still open? | AGGREGATE | P1 |
| CQ-044 | Are all required closeout documents complete for this project? | TRAVERSE | P1 |
| CQ-045 | Is all subcontractor compliance documentation current? | TRAVERSE | P1 |
| CQ-046 | What warranty obligations exist and when do they expire? | TRAVERSE | P2 |

## Lifecycle Stage 8: Get Paid

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-047 | What retention is being held and when can we claim it? | AGGREGATE | P1 |
| CQ-048 | Have all required lien waivers / payment release documents been collected? | TRAVERSE | P1 |
| CQ-049 | What's the total across all projects that we're owed? | AGGREGATE | P1 |

## Lifecycle Stage 9: Learn

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-050 | Did we make money on this job, and why or why not? | AGGREGATE | P1 |
| CQ-051 | How does this job's financial performance compare to similar past jobs? | AGGREGATE | P1 |
| CQ-052 | Which crews or workers are most productive for this type of work? | AGGREGATE | P2 |
| CQ-053 | What's my incident rate trend and projected next insurance rating? | AGGREGATE | P1 |
| CQ-054 | Which subcontractors perform best / worst (safety, quality, reliability, payment)? | AGGREGATE | P1 |

## Cross-Cutting: Safety & Compliance

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-055 | What regulatory standards apply to this activity in this jurisdiction? | RULE | P1 |
| CQ-056 | What certifications does a worker need to do this work in this jurisdiction? | RULE | P1 |
| CQ-057 | What's my compliance score across all projects? | AGGREGATE | P1 |
| CQ-058 | What should today's safety briefing cover, given the project risks and schedule? | TRAVERSE | P1 |
| CQ-059 | What hazardous substances are present on this project and what are the exposure limits? | TRAVERSE | P1 |
| CQ-060 | What regulatory forms / records are required in this jurisdiction and are they current? | TRAVERSE | P1 |

## Cross-Cutting: Communication & Memory

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-061 | What has the contractor told the system about their preferences, rates, and working patterns? | TRAVERSE | P1 |
| CQ-062 | Find past conversations relevant to the current question (semantic search) | TRAVERSE | P1 |
| CQ-063 | What formal queries (RFIs / technical queries) are overdue? | AGGREGATE | P1 |
| CQ-064 | Who is currently responsible for responding to this open query? | LOOKUP | P1 |
| CQ-065 | What submissions are awaiting review or approval? | AGGREGATE | P1 |

## Cross-Cutting: Documents

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-066 | What does the specification or plan document say about a specific topic? (semantic search) | TRAVERSE | P1 |
| CQ-067 | Does the estimate match the quantities shown in the plans? | TRAVERSE | P2 |
| CQ-068 | When does this insurance certificate expire? | LOOKUP | P1 |
| CQ-069 | What documents are required for this project and which are missing? | TRAVERSE | P1 |

## Cross-Cutting: Globalisation

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-070 | What jurisdiction is this company operating in? | LOOKUP | P1 |
| CQ-071 | What languages are used in this jurisdiction / by this company's workforce? | TRAVERSE | P1 |
| CQ-072 | What currency does this company operate in? | LOOKUP | P1 |
| CQ-073 | What measurement system (metric / imperial) applies in this jurisdiction? | LOOKUP | P1 |

## Cross-Cutting: Access & Permissions

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-074 | What can this user see and do, given their role and what they're connected to? | TRAVERSE | P1 |
| CQ-075 | Can this foreman see the commercial data (margins, total contract value) for their project? | RULE | P1 |
| CQ-076 | Can this worker only see their own time entries, assignments, and safety data? | RULE | P1 |
| CQ-077 | Can this GC see their sub's compliance and safety data for shared projects only? | TRAVERSE | P1 |
| CQ-078 | Can this client see progress and invoices for their project but not the contractor's costs? | TRAVERSE | P1 |
| CQ-079 | Can this external party (architect, inspector) only see what they're explicitly given access to? | TRAVERSE | P1 |
| CQ-080 | What has this user been granted access to that is outside their default role-based visibility? | TRAVERSE | P1 |
| CQ-081 | Who has access to this sensitive data (estimates, margins, payroll)? | TRAVERSE | P1 |

## Agentic Overlay

| # | Question | Type | Priority |
|---|----------|------|----------|
| CQ-A01 | Which agent or human performed this action, and when? | TRAVERSE | P1 |
| CQ-A02 | Can this agent access data belonging to this company? | TRAVERSE | P1 |
| CQ-A03 | What regulations applied on a specific historical date? | TRAVERSE | P1 |
| CQ-A04 | What's the total cost attributed to this agent this month? | AGGREGATE | P1 |
| CQ-A05 | Has this agent exceeded its daily budget? | LOOKUP | P1 |

---

## Summary

| Category | Count | P1 | P2 |
|----------|-------|----|----|
| Stage 1: Find & Qualify | 4 | 4 | 0 |
| Stage 2: Estimate & Price | 6 | 4 | 2 |
| Stage 3: Propose & Win | 4 | 3 | 1 |
| Stage 4: Plan & Mobilise | 7 | 6 | 1 |
| Stage 5: Execute & Document | 14 | 14 | 0 |
| Stage 6: Manage Money | 7 | 7 | 0 |
| Stage 7: Close Out | 4 | 3 | 1 |
| Stage 8: Get Paid | 3 | 3 | 0 |
| Stage 9: Learn | 5 | 4 | 1 |
| Safety & Compliance | 6 | 6 | 0 |
| Communication & Memory | 5 | 5 | 0 |
| Documents | 4 | 2 | 2 |
| Globalisation | 4 | 4 | 0 |
| Access & Permissions | 8 | 8 | 0 |
| Agentic Overlay | 5 | 5 | 0 |
| **Total** | **86** | **78** | **8** |

### Type Distribution

| Type | Count |
|------|-------|
| TRAVERSE | 36 |
| AGGREGATE | 25 |
| RULE | 9 |
| LOOKUP | 8 |
