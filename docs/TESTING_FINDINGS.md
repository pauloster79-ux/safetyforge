# Kerf Testing Findings & Vision Gap Analysis

## Testing Date: 2026-04-03
## Method: Manual browser testing via preview tool (all pages tested)

---

## 1. FUNCTIONALITY STATUS BY SECTION

### Section 1-2: Landing Page + Getting Started
| Feature | Status | Notes |
|---------|--------|-------|
| Landing page | WORKING | Strong messaging aligned with vision |
| Login (email/password) | WORKING | Requires Firebase config for real auth |
| Login (Google OAuth) | WORKING | Requires Firebase config |
| Demo mode | WORKING | Quick entry, good sample data |
| Sign up page | WORKING | Google or email/password |
| Company onboarding | WORKING | Multi-jurisdiction: US, UK, AU, CA |
| 14-day free trial | PARTIAL | Billing page shows "Free" plan, trial logic not visible |

### Section 3: Dashboard
| Feature | Status | Notes |
|---------|--------|-------|
| Status strip metrics | WORKING | Shows Active Projects, Inspections, Workers, Cert Alerts, TRIR |
| Recent documents | WORKING | Shows 3 docs with DRAFT/FINAL badges |
| Certification alerts table | WORKING | Expiring/expired certs with worker names |
| Active projects list | WORKING | With compliance percentages |
| Quick actions | WORKING | New Inspection, New Document, New Project |
| EN/ES language toggle | WORKING | In header bar |
| Compliance Score metric | DIFFERENT | Manual says "Compliance Score" but app shows TRIR |
| Open Actions metric | MISSING | Manual describes this but not in current dashboard |
| Inspections Due metric | MISSING | Manual describes this but shows Cert Alerts instead |

### Section 4: Projects
| Feature | Status | Notes |
|---------|--------|-------|
| Project list | WORKING | 3 demo projects with status badges |
| Status filter | WORKING | Dropdown filter |
| New Project form | WORKING | Comprehensive with 14 trade types, safety/emergency fields |
| Project detail page | WORKING | Rich with 7 tabs, action buttons, compliance ring |
| Morning Safety Brief | WORKING | Accessible from project detail, excellent content |
| Project overview | WORKING | Details, safety info, emergency contacts |

### Section 5: Inspections
| Feature | Status | Notes |
|---------|--------|-------|
| Checklist inspection | WORKING | 8 inspection types, form with weather/conditions |
| Voice inspection | NOT VISIBLE | Manual describes voice mode but not in UI |
| Photo inspection | NOT VISIBLE | Manual describes photo mode but not in UI |
| Past inspections list | WORKING | Accessible via project detail Inspections tab |
| Standalone inspections page | MISSING | Sidebar "Inspections" links to /projects, not its own page |

### Section 6: Documents
| Feature | Status | Notes |
|---------|--------|-------|
| Document list | WORKING | Search, 3 filter dropdowns, status badges |
| New Document wizard | WORKING | 4-step: Select Type, Fill Details, Generate, Review |
| Document types | PARTIAL | Has SSSP, JHA, Toolbox Talk, Incident Report, Fall Protection Plan. Manual also lists "Hazard Communication" which is not present |
| Export as PDF | PRESENT | Available on document detail page |
| Templates page | NOT VISIBLE | Manual mentions Templates but not accessible from Documents page |
| Document editing | WORKING | Edit page exists at /documents/:id |

### Section 7: Workers & Certifications
| Feature | Status | Notes |
|---------|--------|-------|
| Worker list | WORKING | 6 demo workers, search/filter, language indicators |
| Add worker form | WORKING | Name, role, trade, language, emergency contact |
| Worker detail page | WORKING | Route exists at /workers/:workerId |
| Certification tracking | WORKING | Cert counts visible on worker cards |
| Certification Matrix | WORKING | 14 cert types x all workers, color-coded, Print/Export |
| Certification alerts | WORKING | Banner showing expired/expiring counts |
| 30/14/7/1 day alerts | NOT VISIBLE | Dashboard shows alerts but granular timing not confirmed |

### Section 8: Toolbox Talks
| Feature | Status | Notes |
|---------|--------|-------|
| Create toolbox talk | WORKING | Topic, audience, duration, custom points, "Generate Talk" |
| Toolbox talk list | WORKING | Via project detail Toolbox Talks tab |
| Deliver mode | PRESENT | Route exists at /projects/:id/toolbox-talks/:id/deliver |
| Digital signatures | NOT TESTED | Delivery mode exists but not tested interactively |
| Bilingual content | WORKING | EN/ES toggle in header, generation supports both |
| Standalone talks page | MISSING | Sidebar "Toolbox Talks" links to /projects |

### Section 9: Incidents
| Feature | Status | Notes |
|---------|--------|-------|
| Incident report form | WORKING | Date, time, location, severity, description, persons, witnesses |
| Voice reporting | NOT VISIBLE | Manual describes voice mode but not in UI |
| OSHA classification | NOT TESTED | Form exists but auto-classification not visible in creation flow |
| Incident tracking workflow | PARTIAL | Incident list visible via project tab |
| Standalone incidents page | MISSING | Sidebar "Incidents" links to /projects |

### Section 10: Mock OSHA Inspection
| Feature | Status | Notes |
|---------|--------|-------|
| Run inspection | WORKING | Company-wide scope selector, Run button |
| Past results | WORKING | Score 62, Grade C, 9 findings, 2 critical |
| Finding details | PRESENT | Results page route exists |
| Export as PDF | NOT TESTED | Button may exist on results page |
| Auto-fix suggestions | NOT TESTED | Listed in manual but not confirmed |

### Section 11: Equipment
| Feature | Status | Notes |
|---------|--------|-------|
| Equipment list | WORKING | 4 demo items with status/serial/certs |
| Add equipment | WORKING | Form exists at /equipment/new |
| Equipment detail | WORKING | Route at /equipment/:id |
| Inspection tracking | WORKING | Due dates, overdue alerts visible |
| DOT compliance | PARTIAL | Vehicle shows DOT info |

### Section 12: OSHA Log
| Feature | Status | Notes |
|---------|--------|-------|
| 300 Log | WORKING | 3 entries with full details |
| 300A Summary | WORKING | Tab present |
| Incidence Rates | WORKING | Tab present |
| Year selector | WORKING | 2026 shown |
| Add/Delete entries | WORKING | Buttons visible |
| 300A posting warning | WORKING | Banner shown |

### Section 13: State/Regional Compliance
| Feature | Status | Notes |
|---------|--------|-------|
| State selector | WORKING | Dropdown present |
| Compliance requirements | NOT TESTED | Requires selecting a state |
| Label discrepancy | NOTED | Sidebar says "Regional Compliance", manual says "State Compliance" |

### Section 14: Prequalification
| Feature | Status | Notes |
|---------|--------|-------|
| Platform selector | WORKING | ISNetworld shown |
| Readiness score | WORKING | 72% with breakdown |
| Document checklist | WORKING | 18 items across 5 categories |
| Ready/Outdated/Missing status | WORKING | Color-coded with actions |
| Pre-filled questionnaire | WORKING | 40 auto-filled fields |
| Generate missing docs | WORKING | Generate buttons on missing items |

### Section 15: GC Portal
| Feature | Status | Notes |
|---------|--------|-------|
| GC view | WORKING | 2 connected subs with compliance data |
| Sub view | WORKING | Tab toggle present |
| Invite subcontractor | WORKING | Button present |
| Real-time compliance | WORKING | Scores and activity indicators |

### Section 16: Environmental
| Feature | Status | Notes |
|---------|--------|-------|
| Programs tab | WORKING | Active and available programs listed |
| Exposure Monitoring | PRESENT | Tab exists |
| SWPPP | PRESENT | Tab exists |
| Program generation | WORKING | Generate buttons for inactive programs |

### Section 17: Analytics
| Feature | Status | Notes |
|---------|--------|-------|
| Key metrics | WORKING | 8 metrics shown |
| Industry comparison | WORKING | TRIR and DART vs averages |
| EMR Impact Calculator | WORKING | Input fields for EMR, payroll, rate |
| Compliance overview | WORKING | Cert summary, mock score, avg compliance |

### Section 18: Settings
| Feature | Status | Notes |
|---------|--------|-------|
| Company profile | WORKING | Name, license, address, phone, email, EIN |
| Safety officer | WORKING | Name and phone |
| Account info | WORKING | Name, email |
| Team member management | NOT VISIBLE | Manual describes invite/remove/role change but no team section in Settings |

### Section 19: Billing
| Feature | Status | Notes |
|---------|--------|-------|
| Current plan display | WORKING | Shows Free plan |
| Plan comparison | WORKING | All 4 tiers with features |
| Upgrade buttons | WORKING | Present on each plan |
| Payment method | WORKING | "Add Card" section |
| Usage tracking | NOT VISIBLE | Manual describes usage stats but not shown |
| Billing history | NOT VISIBLE | Manual describes invoice history but not shown |

---

## 2. MISSING FUNCTIONALITY (Not Present in Current Build)

### Critical (core user flows affected)
1. **Voice input for inspections and incidents** - The product vision's #1 differentiator ("the foreman talks and the AI writes") is not visible in the UI. No microphone/record buttons on inspection or incident forms.
2. **Team member management** - No way to invite team members, assign roles, or manage a team from Settings. This blocks multi-user adoption.
3. **Standalone Inspections/Incidents/Toolbox Talks list pages** - Sidebar links route to /projects. Users cannot see all inspections across all projects in one place.

### Important (mentioned in manual, not yet built)
4. **Templates page** - Manual references Templates accessible from Documents page but not found
5. **Photo hazard assessment** - Button exists on project detail but flow not tested/confirmed
6. **Billing history / invoice viewing** - Not present on billing page
7. **Usage tracking** - Not shown on billing page
8. **14-day trial logic** - No trial countdown or status visible

### Nice-to-have (vision features not yet in manual scope)
9. **Video walkthrough inspection** - Vision describes this as Horizon 2 feature
10. **Conversational voice agent for incidents** - Vision describes this for high-value reports
11. **Predictive risk scoring** - Listed in Phase 3
12. **EMR Impact Modeling** (beyond calculator) - Vision describes projections
13. **Insurance carrier integration** - Phase 3+
14. **Offline capability** - Manual mentions it but not testable in browser
15. **Spanish UI translation** - EN/ES toggle exists but may only affect generated content, not full UI

---

## 3. DISCREPANCIES BETWEEN MANUAL AND APP

| # | Manual Says | App Shows | Recommended Fix |
|---|-------------|-----------|-----------------|
| 1 | Dashboard: "Compliance Score" | TRIR | Update manual to match app |
| 2 | Dashboard: "Open Actions" | Workers count | Update manual |
| 3 | Dashboard: "Inspections Due" | Cert Alerts | Update manual |
| 4 | "State Compliance" | "Regional Compliance" | Update manual - reflects multi-jurisdiction |
| 5 | Document type: "Hazard Communication" | "Fall Protection Plan" | Update manual |
| 6 | No mention of multi-jurisdiction | Supports US, UK, AU, CA | Add to manual |
| 7 | Inspections via sidebar | Routes to /projects | Clarify in manual that inspections are project-scoped |
| 8 | Team management in Settings | Not visible | Mark as "Coming Soon" |
| 9 | No mention of Morning Brief | Full feature in project detail | Add section to manual |
| 10 | No mention of EMR Calculator | Present in Analytics | Add to manual |
| 11 | No mention of EN/ES header toggle | Present on every page | Add to manual |
| 12 | Templates accessible from Documents | Not visible | Mark as "Coming Soon" |

---

## 4. VISION IMPROVEMENT SUGGESTIONS

### High Priority (directly from product vision gaps)

1. **Add voice input to inspections and incident reports**
   - Vision principle: "We never require typing when voice or photo will do"
   - This is the core differentiator. A push-to-talk button on inspection and incident forms would transform the field experience.
   - Consider: large, always-visible microphone button, EN/ES auto-detection

2. **Build cross-project views for Inspections, Incidents, Toolbox Talks**
   - Sarah (the owner persona) needs to see all inspections across all projects in one dashboard
   - Current implementation requires clicking into each project individually
   - Add dedicated list pages at /inspections, /incidents, /toolbox-talks

3. **Add team member invitation and role management**
   - The product is "unlimited users per tier" but there's no way to invite users
   - This is critical for the "field adoption" metric - foremen need their own accounts
   - Add to Settings page: invite by email, assign role, manage team

4. **Show compliance score on dashboard (not just TRIR)**
   - The mock OSHA score (62, Grade C) is the most actionable metric
   - Vision says "compliance score" should be front and center
   - Consider adding the mock inspection score to the dashboard status strip

5. **Implement the "3 taps or less" principle**
   - Currently creating an inspection is: Sidebar > Projects > Select Project > New Inspection > Select Type > Fill Form (6+ steps)
   - Consider: dashboard quick action "New Inspection" should let you pick project + type in 2-3 taps

### Medium Priority

6. **Add hazard reporting from project detail**
   - Project detail has "Hazards (2)" tab but no standalone "Report Hazard" with photo+voice
   - This is Carlos's (laborer persona) key interaction - photo + voice note = hazard report
   - Should be the simplest possible flow: big red button > take photo > speak > submit

7. **Enhance Morning Brief with actionable buttons**
   - Current brief is excellent content but could be more actionable
   - Vision: "Marco taps 'Start Toolbox Talk'" - the brief should be the launchpad for the day
   - Already partially done with View Worker, Start Inspection, Generate Talk buttons

8. **Add document gap analysis to dashboard**
   - Vision describes the "Document Gap Auditor"
   - Dashboard could show a simple "X of Y required documents present" per project
   - Already partially done with the document usage counter

9. **Implement corrective action tracking**
   - Manual mentions corrective actions from inspections but no standalone corrective action tracker
   - Vision's "Open Actions" dashboard metric implies a corrective action workflow
   - Add: action items from inspections/incidents with assignee, deadline, status

10. **Certification upload capability**
    - Manual mentions uploading photos/scans of certificates
    - Not visible in the current worker/cert management flow
    - Important for prequalification packages and GC portal verification

### Lower Priority (vision Horizon 2-3 features)

11. **Anonymized safety network / benchmarks**
    - Show industry comparison data beyond the static analytics page
    - "Roofing contractors in Texas have 3x fall incidents in July"

12. **Push notifications for cert expiry and inspection reminders**
    - Vision mentions 30/14/7/1 day alerts
    - Currently shown as dashboard badges but not as active notifications

13. **PDF export across all document types**
    - Confirm PDF generation works for all document types
    - Add bulk export for prequalification packages

14. **Offline mode indication**
    - If offline support exists, show sync status clearly
    - Currently shows "Last sync: 2 min ago" in footer - good foundation

---

## 5. CONSOLE ERRORS NOTED

1. **Base UI nativeButton warning** - ~48 instances on landing page
   - All buttons using `<a>` tags wrapped in `<Button>` component trigger this warning
   - Fix: Use native `<button>` elements or set `nativeButton={false}` on link-buttons
   - Non-blocking but creates console noise

---

## 6. OVERALL ASSESSMENT

Kerf has a comprehensive and well-implemented frontend that covers the majority of features described in the user manual. The demo mode provides rich, realistic sample data that effectively showcases the platform's capabilities.

**Strongest areas (well-aligned with vision):**
- Mock OSHA Inspection (killer feature per strategy doc)
- Prequalification automation (72% readiness score UX is compelling)
- Morning Safety Brief (directly implements the "Marco scenario")
- Certification Matrix (clear, actionable compliance view)
- Multi-jurisdiction support (US, UK, AU, CA - exceeds manual scope)
- EN/ES language toggle (core vision requirement)
- EMR Impact Calculator (connects safety to dollars)
- GC Portal with dual-perspective (GC and Sub views)

**Areas needing most attention:**
- Voice input (vision's #1 differentiator, not yet in UI)
- Cross-project aggregate views (Inspections, Incidents, Talks)
- Team member management (blocks multi-user adoption)
- Corrective action tracking (implied by vision, not built)

The application is at a strong MVP stage with excellent design and data architecture. The primary gaps are in the field-first interaction patterns (voice, photo-to-hazard, video walkthrough) that the vision positions as the key differentiators from template-based competitors.
