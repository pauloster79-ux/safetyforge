# Jurisdiction Abstraction Architecture

## Design Principle

**Every piece of jurisdiction-specific knowledge becomes data, not code.**

The platform code handles universal operations (inspections, documents, workers, incidents). Jurisdiction packs provide the regulatory context. Adding a new country = adding a new data pack — zero code changes.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLATFORM LAYER                           │
│  (jurisdiction-agnostic services, models, UI components)        │
│                                                                 │
│  CompanyService   ProjectService   InspectionService   ...      │
│       │                │                  │                     │
│       └────────────────┼──────────────────┘                     │
│                        │                                        │
│              ┌─────────▼──────────┐                             │
│              │ JurisdictionContext │ ← injected into every       │
│              │                    │   service call via DI        │
│              └─────────┬──────────┘                             │
│                        │                                        │
├────────────────────────┼────────────────────────────────────────┤
│                        │       JURISDICTION LAYER               │
│              ┌─────────▼──────────┐                             │
│              │ JurisdictionLoader │                              │
│              └─────────┬──────────┘                             │
│                        │                                        │
│         ┌──────────────┼──────────────┐                        │
│         ▼              ▼              ▼                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│  │ US Pack  │   │ UK Pack  │   │ AU Pack  │   ...              │
│  │ (YAML)   │   │ (YAML)   │   │ (YAML)   │                   │
│  └──────────┘   └──────────┘   └──────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Jurisdiction Pack Structure

Each jurisdiction is a directory under `jurisdictions/`:

```
backend/
  jurisdictions/
    _schema.yaml              # JSON Schema for pack validation
    us/
      manifest.yaml           # Country metadata, locale, units, currency
      regulations.yaml        # Regulatory framework (acts, sections, penalties)
      certifications.yaml     # Valid certification types for this jurisdiction
      document_types.yaml     # Available document types + generation prompt refs
      compliance_rules.yaml   # Regional compliance engine rules
      regions/
        federal.yaml          # Federal requirements
        ca.yaml               # California-specific additions
        ny.yaml               # New York-specific additions
        wa.yaml               # Washington-specific additions
        ...
      prompts/
        sssp.md               # System prompt for SSSP generation
        jha.md                # System prompt for JHA generation
        fall_protection.md    # System prompt for fall protection plan
        toolbox_talk.md       # System prompt for toolbox talk
        incident_analysis.md  # System prompt for incident root cause
        hazard_analysis.md    # System prompt for photo hazard analysis
        mock_inspection.md    # System prompt for mock inspection findings
    uk/
      manifest.yaml
      regulations.yaml
      certifications.yaml
      document_types.yaml
      compliance_rules.yaml
      regions/
        england_wales.yaml
        scotland.yaml
        northern_ireland.yaml
      prompts/
        construction_phase_plan.md    # UK equivalent of SSSP
        method_statement.md           # UK equivalent of JHA
        rams.md                       # Risk Assessment & Method Statement
        toolbox_talk.md
        ...
    au/
      manifest.yaml
      regulations.yaml
      certifications.yaml
      document_types.yaml
      compliance_rules.yaml
      regions/
        nsw.yaml
        vic.yaml
        qld.yaml
        ...
      prompts/
        swms.md                       # Safe Work Method Statement
        ...
```

### 1.1 manifest.yaml (Country Metadata)

```yaml
# jurisdictions/uk/manifest.yaml
code: UK
name: United Kingdom
regulatory_body: Health and Safety Executive (HSE)
primary_legislation: Health and Safety at Work etc Act 1974
construction_legislation: Construction (Design and Management) Regulations 2015

locale:
  languages: [en-GB]
  date_format: DD/MM/YYYY
  temperature_unit: celsius
  measurement_system: metric
  currency: GBP
  currency_symbol: "£"
  phone_format: "+44 XXXX XXXXXX"
  address_format: "{line1}, {line2}, {city}, {county}, {postcode}"
  tax_type: VAT
  tax_rate: 0.20

safety_metrics:
  incident_rate_name: "Accident Frequency Rate (AFR)"
  incident_rate_formula: "(reportable injuries × 100,000) / total hours worked"
  incident_rate_multiplier: 100000    # UK uses 100K, not US 200K
  reporting_period: "calendar_year"
  reporting_body: "HSE via RIDDOR"

record_keeping:
  name: "RIDDOR"
  full_name: "Reporting of Injuries, Diseases and Dangerous Occurrences Regulations 2013"
  replaces: "osha_log"     # Maps to which US feature this replaces
  classifications:
    - id: fatal
      name: "Fatal injury"
      reportable: true
      report_deadline_hours: 0   # Immediate
    - id: specified
      name: "Specified injury"
      reportable: true
      report_deadline_days: 10
    - id: over_7_day
      name: "Over 7-day incapacitation"
      reportable: true
      report_deadline_days: 15
    - id: dangerous_occurrence
      name: "Dangerous occurrence"
      reportable: true
      report_deadline_days: 10
    - id: occupational_disease
      name: "Occupational disease"
      reportable: true
      report_deadline_days: 10
    - id: minor
      name: "Minor injury"
      reportable: false

enforcement:
  conviction_rate: 0.96
  max_fine_unlimited: true
  typical_serious_fine_range: [10000, 6000000]
  currency: GBP
  criminal_liability: true
  who_enforces: "HSE Inspectors"

prequalification_platforms:
  - id: chas
    name: "CHAS (Contractors Health and Safety Assessment Scheme)"
  - id: safe_contractor
    name: "SafeContractor"
  - id: constructionline
    name: "Constructionline"
  - id: ssip
    name: "SSIP (Safety Schemes in Procurement)"

data_residency:
  gdpr_applicable: true
  uk_dpa_2018: true
  data_region: "europe-west2"   # London GCP region
```

### 1.2 regulations.yaml

```yaml
# jurisdictions/uk/regulations.yaml
primary:
  - id: hswa_1974
    short: "HSWA 1974"
    full: "Health and Safety at Work etc Act 1974"
    sections:
      - id: s2
        title: "General duties of employers to their employees"
        summary: "Ensure so far as is reasonably practicable the health, safety and welfare at work of all employees"
      - id: s3
        title: "General duties to persons other than employees"
      - id: s4
        title: "General duties to persons in control of premises"

construction:
  - id: cdm_2015
    short: "CDM 2015"
    full: "Construction (Design and Management) Regulations 2015"
    roles:
      - client
      - principal_designer
      - principal_contractor
      - designer
      - contractor
    required_documents:
      - pre_construction_information
      - construction_phase_plan
      - health_and_safety_file
    sections:
      - id: reg4
        title: "Client duties"
        summary: "Make suitable arrangements for managing a project"
      - id: reg12
        title: "Construction phase plan"
        summary: "Principal contractor must draw up a construction phase plan"
      - id: reg13
        title: "Duties of contractors"

  - id: wahr_2005
    short: "WAHR 2005"
    full: "Work at Height Regulations 2005"
    trigger_height_metres: 0    # No minimum height — all work at height covered
    key_requirements:
      - "Avoid work at height where possible"
      - "Use work equipment to prevent falls where WAH cannot be avoided"
      - "Minimise distance and consequences of fall"

  - id: loler_1998
    short: "LOLER 1998"
    full: "Lifting Operations and Lifting Equipment Regulations 1998"
    inspection_frequency: "6 months for lifting persons, 12 months otherwise"

  - id: puwer_1998
    short: "PUWER 1998"
    full: "Provision and Use of Work Equipment Regulations 1998"

environmental:
  - id: caw_2012
    short: "CAW 2012"
    full: "Control of Asbestos Regulations 2012"
    exposure_limit: { value: 0.1, unit: "fibres/ml", period: "4-hour TWA" }

  - id: coshh_2002
    short: "COSHH 2002"
    full: "Control of Substances Hazardous to Health Regulations 2002"
    silica_wel: { value: 0.1, unit: "mg/m3", period: "8-hour TWA" }
    # Note: UK silica WEL is 0.1 mg/m³ vs US OSHA PEL of 0.05 mg/m³

  - id: noise_2005
    short: "Noise Regs 2005"
    full: "Control of Noise at Work Regulations 2005"
    lower_action: { value: 80, unit: "dB(A)", period: "daily" }
    upper_action: { value: 85, unit: "dB(A)", period: "daily" }
    exposure_limit: { value: 87, unit: "dB(A)", period: "daily" }
```

### 1.3 certifications.yaml

```yaml
# jurisdictions/uk/certifications.yaml
certifications:
  - id: cscs_card
    name: "CSCS Card"
    full_name: "Construction Skills Certification Scheme"
    expires: true
    validity_years: 5
    required_for: "all_site_workers"
    levels:
      - green: "Labourer"
      - blue: "Skilled Worker"
      - gold: "Supervisory"
      - black: "Manager"
    issuing_body: "CSCS"

  - id: smsts
    name: "SMSTS"
    full_name: "Site Management Safety Training Scheme"
    expires: true
    validity_years: 5
    required_for: "site_managers"
    issuing_body: "CITB"

  - id: sssts
    name: "SSSTS"
    full_name: "Site Supervisors' Safety Training Scheme"
    expires: true
    validity_years: 5
    required_for: "supervisors"
    issuing_body: "CITB"

  - id: nvq_health_safety
    name: "NVQ Level 6 Health & Safety"
    expires: false
    required_for: "health_safety_professionals"

  - id: nebosh_construction
    name: "NEBOSH Construction Certificate"
    full_name: "National Examination Board in Occupational Safety and Health"
    expires: false
    required_for: "safety_officers"

  - id: first_aid_at_work
    name: "First Aid at Work (FAW)"
    expires: true
    validity_years: 3
    issuing_body: "HSE Approved Provider"

  - id: ipaf
    name: "IPAF Operator Licence"
    full_name: "International Powered Access Federation"
    expires: true
    validity_years: 5
    required_for: "mewp_operators"

  - id: cpcs
    name: "CPCS Card"
    full_name: "Construction Plant Competence Scheme"
    expires: true
    validity_years: 5
    required_for: "plant_operators"
    categories: [A01, A02, A04, A09, A17, A31, A36, A40, A58, A59, A60, A61, A62]

  - id: pasma
    name: "PASMA"
    full_name: "Prefabricated Access Suppliers' and Manufacturers' Association"
    expires: true
    validity_years: 5
    required_for: "tower_scaffold_users"

  - id: asbestos_awareness
    name: "Asbestos Awareness (Category A)"
    expires: true
    validity_years: 1
    required_for: "all_site_workers"
    regulation: "CAW 2012"
```

### 1.4 document_types.yaml

```yaml
# jurisdictions/uk/document_types.yaml
document_types:
  - id: construction_phase_plan
    name: "Construction Phase Plan"
    abbreviation: "CPP"
    maps_to_universal: "site_safety_plan"    # Cross-jurisdiction mapping
    us_equivalent: "sssp"
    regulation: "CDM 2015 Reg 12"
    required: true
    prompt_file: "prompts/construction_phase_plan.md"
    sections:
      - project_description
      - management_structure
      - arrangements_for_health_and_safety
      - site_rules
      - specific_measures_for_high_risk_work
      - welfare_arrangements
      - emergency_procedures
      - monitoring_arrangements

  - id: rams
    name: "Risk Assessment & Method Statement"
    abbreviation: "RAMS"
    maps_to_universal: "job_hazard_analysis"
    us_equivalent: "jha"
    regulation: "Management of H&S at Work Regs 1999, Reg 3"
    required: true
    prompt_file: "prompts/rams.md"

  - id: method_statement
    name: "Method Statement"
    abbreviation: "MS"
    maps_to_universal: "job_hazard_analysis"
    us_equivalent: "jha"
    required: true
    prompt_file: "prompts/method_statement.md"

  - id: toolbox_talk
    name: "Toolbox Talk"
    abbreviation: "TBT"
    maps_to_universal: "toolbox_talk"       # Same concept worldwide
    us_equivalent: "toolbox_talk"
    required: false
    prompt_file: "prompts/toolbox_talk.md"

  - id: coshh_assessment
    name: "COSHH Assessment"
    abbreviation: "COSHH"
    maps_to_universal: "hazardous_substance_assessment"
    us_equivalent: null                      # No direct US equivalent
    regulation: "COSHH 2002"
    required: true
    prompt_file: "prompts/coshh_assessment.md"

  - id: rescue_plan
    name: "Work at Height Rescue Plan"
    maps_to_universal: "fall_protection_plan"
    us_equivalent: "fall_protection"
    regulation: "WAHR 2005"
    required: true
    prompt_file: "prompts/rescue_plan.md"

  - id: permit_to_work
    name: "Permit to Work"
    abbreviation: "PTW"
    maps_to_universal: "high_risk_work_permit"
    us_equivalent: null
    required_for: ["hot_work", "confined_space", "live_electrical", "excavation"]
    prompt_file: "prompts/permit_to_work.md"
```

### 1.5 compliance_rules.yaml

```yaml
# jurisdictions/uk/compliance_rules.yaml
# Rules engine: each rule evaluates against company/project data

required_programs:
  - id: construction_phase_plan
    name: "Construction Phase Plan"
    regulation: "CDM 2015 Reg 12"
    check: "document_exists"
    document_type: "construction_phase_plan"
    applies_when: "always"
    severity: "critical"

  - id: health_safety_policy
    name: "Health & Safety Policy"
    regulation: "HSWA 1974 s2(3)"
    check: "document_exists"
    document_type: "health_safety_policy"
    applies_when: "company.employee_count >= 5"
    severity: "critical"

  - id: risk_assessments
    name: "Suitable and Sufficient Risk Assessments"
    regulation: "MHSW 1999 Reg 3"
    check: "risk_assessments_current"
    applies_when: "always"
    severity: "critical"

  - id: fire_risk_assessment
    name: "Fire Risk Assessment"
    regulation: "Regulatory Reform (Fire Safety) Order 2005"
    check: "document_exists"
    document_type: "fire_risk_assessment"
    applies_when: "always"
    severity: "high"

  - id: asbestos_survey
    name: "Asbestos Refurbishment/Demolition Survey"
    regulation: "CAW 2012 Reg 5"
    check: "document_exists"
    document_type: "asbestos_survey"
    applies_when: "project.involves_refurbishment_or_demolition"
    severity: "critical"

required_certifications:
  - id: cscs_all_workers
    name: "CSCS Cards for All Workers"
    check: "all_workers_have_cert"
    certification_type: "cscs_card"
    applies_when: "always"
    severity: "high"

  - id: smsts_site_manager
    name: "SMSTS for Site Managers"
    check: "role_has_cert"
    role: "superintendent"
    certification_type: "smsts"
    applies_when: "always"
    severity: "critical"

  - id: first_aid_coverage
    name: "Adequate First Aid Cover"
    regulation: "H&S (First-Aid) Regs 1981"
    check: "min_cert_count"
    certification_type: "first_aid_at_work"
    min_ratio: 0.05    # 1 per 20 workers minimum
    applies_when: "always"
    severity: "high"

inspection_requirements:
  - id: weekly_site_inspection
    name: "Weekly Site Inspection"
    regulation: "CDM 2015"
    check: "inspection_frequency"
    max_days_between: 7
    applies_when: "always"
    severity: "high"

  - id: scaffold_inspection
    name: "Scaffold Inspection Before Use & Every 7 Days"
    regulation: "WAHR 2005 Schedule 7"
    check: "inspection_frequency"
    inspection_type: "scaffold"
    max_days_between: 7
    applies_when: "project.has_scaffolding"
    severity: "critical"

  - id: excavation_inspection
    name: "Excavation Inspection at Start of Each Shift"
    regulation: "CDM 2015 Schedule 4"
    check: "inspection_frequency"
    inspection_type: "excavation"
    max_days_between: 1
    applies_when: "project.has_excavation"
    severity: "critical"

training_requirements:
  - id: site_induction
    name: "Site-Specific Induction for All Workers"
    regulation: "CDM 2015 Reg 13(4)"
    check: "induction_completed"
    applies_when: "always"
    severity: "critical"

  - id: asbestos_awareness
    name: "Asbestos Awareness Training (Annual)"
    regulation: "CAW 2012 Reg 10"
    check: "all_workers_have_cert"
    certification_type: "asbestos_awareness"
    applies_when: "always"
    severity: "high"
```

---

## 2. Backend Architecture Changes

### 2.1 New: JurisdictionContext

The core abstraction. Loaded once per request based on the company's jurisdiction, then injected into every service.

```python
# backend/app/jurisdiction/context.py

@dataclass(frozen=True)
class JurisdictionContext:
    """Immutable jurisdiction context injected into services."""

    code: str                          # "US", "UK", "AU"
    region: str | None                 # "CA", "england_wales", "nsw"
    manifest: dict                     # Parsed manifest.yaml
    regulations: dict                  # Parsed regulations.yaml
    certifications: list[dict]         # Parsed certifications.yaml
    document_types: list[dict]         # Parsed document_types.yaml
    compliance_rules: dict             # Parsed compliance_rules.yaml
    region_rules: dict | None          # Parsed regions/{region}.yaml

    # Convenience accessors
    @property
    def currency(self) -> str: ...
    @property
    def date_format(self) -> str: ...
    @property
    def measurement_system(self) -> str: ...   # "metric" | "imperial"
    @property
    def temperature_unit(self) -> str: ...     # "celsius" | "fahrenheit"
    @property
    def incident_rate_multiplier(self) -> int: ...  # 200000 (US) | 100000 (UK)
    @property
    def incident_rate_name(self) -> str: ...   # "TRIR" | "AFR" | "LTIFR"

    def get_prompt(self, document_type: str) -> str:
        """Load the generation prompt for a document type."""
        ...

    def get_certification_types(self) -> list[dict]:
        """Return valid certification types for this jurisdiction."""
        ...

    def get_document_types(self) -> list[dict]:
        """Return available document types for this jurisdiction."""
        ...

    def format_regulation_ref(self, reg_id: str, section_id: str) -> str:
        """Format a regulation reference (e.g., '29 CFR 1926.501' or 'CDM 2015 Reg 12')."""
        ...
```

### 2.2 New: JurisdictionLoader

Loads and caches jurisdiction packs from the filesystem.

```python
# backend/app/jurisdiction/loader.py

class JurisdictionLoader:
    """Loads jurisdiction packs from YAML files with LRU caching."""

    _cache: dict[str, JurisdictionContext] = {}

    @classmethod
    def load(cls, code: str, region: str | None = None) -> JurisdictionContext:
        """Load a jurisdiction context by country code and optional region."""
        ...

    @classmethod
    def available_jurisdictions(cls) -> list[dict]:
        """Return list of available jurisdiction codes and names."""
        ...

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the jurisdiction cache (for testing/hot-reload)."""
        ...
```

### 2.3 Modified: Company Model

```python
# Add to existing Company model
class Company(CompanyCreate):
    # ... existing fields ...
    jurisdiction_code: str = "US"              # NEW — country code
    jurisdiction_region: str | None = None     # NEW — state/province/region
    tax_id: str | None = None                  # REPLACES ein
    tax_id_type: str | None = None             # NEW — "EIN", "UTR", "ABN", "VAT"
```

### 2.4 Modified: Dependency Injection

The key integration point. `JurisdictionContext` gets resolved from the company's `jurisdiction_code` and injected into services.

```python
# backend/app/dependencies.py — additions

from app.jurisdiction.loader import JurisdictionLoader
from app.jurisdiction.context import JurisdictionContext

async def get_jurisdiction_context(
    company_id: str,
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> JurisdictionContext:
    """Resolve jurisdiction context from the company's settings."""
    company_service = CompanyService(db)
    company = company_service.get(company_id)
    return JurisdictionLoader.load(
        code=company.jurisdiction_code,
        region=company.jurisdiction_region,
    )
```

### 2.5 Service Changes Pattern

Every service that currently has hardcoded US logic accepts `JurisdictionContext` as a parameter. The pattern is the same everywhere:

**Before (hardcoded):**
```python
class OshaLogService:
    def calculate_trir(self, cases, hours):
        return (cases * 200_000) / hours  # US-only formula
```

**After (jurisdiction-aware):**
```python
class IncidentRecordService:     # Renamed from OshaLogService
    def calculate_incident_rate(self, cases, hours, ctx: JurisdictionContext):
        return (cases * ctx.incident_rate_multiplier) / hours
        # US: 200,000 → TRIR
        # UK: 100,000 → AFR
        # AU: 1,000,000 → LTIFR
```

### 2.6 Renamed/Generalized Services

| Current Name | New Name | Why |
|---|---|---|
| `OshaLogService` | `IncidentRecordService` | OSHA is US-only; UK uses RIDDOR, AU uses notifiable incidents |
| `StateComplianceService` | `RegionalComplianceService` | States → provinces, regions, devolved nations |
| `MockInspectionService` | `ComplianceAuditService` | "Mock OSHA Inspection" is US concept; generic compliance audit is universal |

All other services keep their names (inspections, workers, documents, equipment are universal concepts).

### 2.7 Generation Service Changes

**Before:** System prompts hardcoded in Python strings referencing OSHA.

**After:** Prompts loaded from jurisdiction pack files.

```python
class GenerationService:
    async def generate_document(
        self,
        document_type: str,
        project_info: dict,
        ctx: JurisdictionContext,    # NEW parameter
    ) -> dict:
        # Load prompt from jurisdiction pack
        system_prompt = ctx.get_prompt(document_type)

        # Inject jurisdiction context into prompt
        prompt_context = {
            "regulatory_body": ctx.manifest["regulatory_body"],
            "primary_legislation": ctx.manifest["primary_legislation"],
            "construction_legislation": ctx.manifest["construction_legislation"],
            "regulations": ctx.regulations,
            "measurement_system": ctx.measurement_system,
            "temperature_unit": ctx.temperature_unit,
        }

        # Call Claude with jurisdiction-aware prompt
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            system=system_prompt.format(**prompt_context),
            messages=[{"role": "user", "content": user_prompt}],
        )
        return self._parse_response(response)
```

### 2.8 Generation Prompt Example (UK)

```markdown
# jurisdictions/uk/prompts/construction_phase_plan.md

You are a UK construction health and safety professional generating a
Construction Phase Plan in accordance with the Construction (Design and
Management) Regulations 2015 (CDM 2015), specifically Regulation 12.

## Regulatory Context
- Primary legislation: Health and Safety at Work etc Act 1974
- Construction regulations: CDM 2015
- Work at height: Work at Height Regulations 2005
- Manual handling: Manual Handling Operations Regulations 1992
- All references must cite UK legislation, never OSHA or US standards

## Required Sections (CDM 2015 Reg 12 & Schedule 2)
1. Description of the project
2. Management of the work (including timeline)
3. Arrangements for controlling significant site risks including:
   - Delivery and removal of materials
   - Work at height (WAHR 2005 — no minimum trigger height)
   - Excavations (CDM Schedule 4)
   - Temporary works
   - Services (underground and overhead)
4. Health hazards (noise, dust, substances, vibration)
5. Welfare facilities (CDM Schedule 2)
6. Site rules and fire/emergency procedures
7. Monitoring arrangements for H&S standards

## Measurement Units
- Heights in metres (not feet)
- Temperatures in Celsius
- Weights in kilograms
- Distances in metres

## Key Differences from US SSSP
- UK has no minimum height for fall protection (WAHR 2005 applies to ALL work at height)
- CDM 2015 requires Principal Contractor and Principal Designer roles
- Health and Safety File must be prepared for handover to client
- Specific welfare requirements (heated rest areas, drying rooms, etc.)

Generate a comprehensive, site-specific CPP for the following project:
```

---

## 3. Frontend Architecture Changes

### 3.1 Jurisdiction Provider (React Context)

```typescript
// src/contexts/JurisdictionContext.tsx

interface JurisdictionConfig {
  code: string;                    // "US", "UK", "AU"
  region: string | null;           // "CA", "england_wales"
  name: string;                    // "United Kingdom"
  regulatoryBody: string;          // "Health and Safety Executive"
  locale: {
    languages: string[];           // ["en-GB"]
    dateFormat: string;            // "DD/MM/YYYY"
    temperatureUnit: string;       // "celsius"
    measurementSystem: string;     // "metric"
    currency: string;              // "GBP"
    currencySymbol: string;        // "£"
    phoneFormat: string;           // "+44 XXXX XXXXXX"
    addressFormat: string;
  };
  certificationTypes: CertificationType[];
  documentTypes: DocumentType[];
  incidentRateName: string;        // "AFR" instead of "TRIR"
  recordKeepingName: string;       // "RIDDOR" instead of "OSHA Log"
  complianceAuditName: string;     // "Compliance Audit" instead of "Mock OSHA Inspection"
}

const JurisdictionContext = createContext<JurisdictionConfig>(US_DEFAULT);

export function JurisdictionProvider({ children }: Props) {
  const { company } = useCompany();
  const { data: config } = useQuery({
    queryKey: ['jurisdiction', company?.jurisdiction_code],
    queryFn: () => api.getJurisdictionConfig(company.jurisdiction_code),
    enabled: !!company,
  });

  return (
    <JurisdictionContext.Provider value={config ?? US_DEFAULT}>
      {children}
    </JurisdictionContext.Provider>
  );
}

export const useJurisdiction = () => useContext(JurisdictionContext);
```

### 3.2 Dynamic UI Labels

```typescript
// Components use jurisdiction context for labels

function Sidebar() {
  const j = useJurisdiction();

  return (
    <nav>
      {/* "OSHA Log" in US, "RIDDOR Log" in UK, "Notifiable Incidents" in AU */}
      <NavItem icon={FileText} label={j.recordKeepingName} href="/incident-records" />

      {/* "State Compliance" in US, "Regional Compliance" in UK */}
      <NavItem icon={Shield} label={t('compliance.regional')} href="/compliance" />

      {/* "Mock OSHA Inspection" in US, "Compliance Audit" in UK */}
      <NavItem icon={ClipboardCheck} label={j.complianceAuditName} href="/audit" />
    </nav>
  );
}
```

### 3.3 Dynamic Form Fields

```typescript
function CompanyOnboarding() {
  const j = useJurisdiction();

  return (
    <form>
      {/* Country selector drives everything else */}
      <CountrySelect onChange={handleJurisdictionChange} />

      {/* Dynamic based on jurisdiction */}
      <Input
        label={j.code === 'US' ? 'EIN' : j.code === 'UK' ? 'UTR' : 'Tax ID'}
        placeholder={j.code === 'US' ? '12-3456789' : j.code === 'UK' ? '1234567890' : ''}
      />
      <Input
        label="Phone"
        placeholder={j.locale.phoneFormat}
      />
      {/* Address fields adapt to jurisdiction */}
      <AddressInput format={j.locale.addressFormat} />
    </form>
  );
}
```

### 3.4 Formatting Utilities

```typescript
// src/lib/formatters.ts

export function formatDate(date: string | Date, jurisdiction: JurisdictionConfig): string {
  const d = new Date(date);
  switch (jurisdiction.locale.dateFormat) {
    case 'DD/MM/YYYY': return d.toLocaleDateString('en-GB');
    case 'MM/DD/YYYY': return d.toLocaleDateString('en-US');
    case 'YYYY-MM-DD': return d.toISOString().split('T')[0];
    default: return d.toLocaleDateString();
  }
}

export function formatCurrency(amount: number, jurisdiction: JurisdictionConfig): string {
  return new Intl.NumberFormat(jurisdiction.locale.languages[0], {
    style: 'currency',
    currency: jurisdiction.locale.currency,
  }).format(amount);
}

export function formatTemperature(celsius: number, jurisdiction: JurisdictionConfig): string {
  if (jurisdiction.locale.temperatureUnit === 'fahrenheit') {
    return `${Math.round(celsius * 9/5 + 32)}°F`;
  }
  return `${Math.round(celsius)}°C`;
}

export function formatHeight(metres: number, jurisdiction: JurisdictionConfig): string {
  if (jurisdiction.locale.measurementSystem === 'imperial') {
    return `${Math.round(metres * 3.281)} ft`;
  }
  return `${metres} m`;
}
```

---

## 4. API Changes

### 4.1 New Endpoint: Jurisdiction Config

```
GET /api/v1/jurisdictions
  → Returns list of available jurisdictions [{code, name, regulatory_body}]

GET /api/v1/jurisdictions/{code}
  → Returns full jurisdiction config for frontend (manifest + document types + cert types)

GET /api/v1/jurisdictions/{code}/regions
  → Returns available regions for a jurisdiction
```

### 4.2 Modified Endpoints

All existing endpoints remain the same. The jurisdiction is resolved server-side from the company's `jurisdiction_code` — no client changes needed for data endpoints.

The only client change: onboarding flow sends `jurisdiction_code` when creating a company.

---

## 5. Firestore Changes

### 5.1 Company Document

Add two fields:
```
companies/{companyId}:
  jurisdiction_code: "UK"         # NEW
  jurisdiction_region: "england"  # NEW
  tax_id: "1234567890"           # REPLACES ein
  tax_id_type: "UTR"             # NEW
```

### 5.2 New Collection: regulatory_standards

Already defined in firestore.rules but unpopulated. Seed from jurisdiction packs:

```
regulatory_standards/{jurisdictionCode}:
  code: "UK"
  name: "United Kingdom"
  regulatory_body: "HSE"
  last_updated: timestamp
  # Denormalized summary for fast reads
```

---

## 6. Migration Strategy

### Phase 1: Abstract (Week 1-2)
1. Create `jurisdictions/` directory structure
2. Extract current US hardcoded values into `jurisdictions/us/` YAML files
3. Build `JurisdictionLoader` and `JurisdictionContext`
4. Add `jurisdiction_code` to Company model (default: "US")
5. Modify dependency injection to resolve jurisdiction context
6. All existing tests continue to pass (US is default)

### Phase 2: Refactor Services (Week 3-4)
1. Rename `OshaLogService` → `IncidentRecordService`
2. Rename `StateComplianceService` → `RegionalComplianceService`
3. Rename `MockInspectionService` → `ComplianceAuditService`
4. Modify each service to accept `JurisdictionContext`
5. Move hardcoded prompts from `generation_service.py` to `jurisdictions/us/prompts/`
6. Move hardcoded state requirements to `jurisdictions/us/regions/`
7. Move hardcoded certification types to `jurisdictions/us/certifications.yaml`

### Phase 3: Frontend (Week 5-6)
1. Add `JurisdictionProvider` React context
2. Add country selector to onboarding
3. Replace hardcoded labels with jurisdiction-aware labels
4. Add formatting utilities (date, currency, units)
5. Update sidebar, forms, and display components

### Phase 4: First International Pack (Week 7-8)
1. Create `jurisdictions/uk/` pack (all YAML files + prompts)
2. Create `jurisdictions/ca/` pack
3. Create `jurisdictions/au/` pack
4. End-to-end testing with UK company
5. Validate AI-generated documents against UK regulations

### Phase 5: Scale (Week 9+)
1. Each additional jurisdiction: 3-5 days
2. Community/partner contributions for local expertise
3. Regulatory monitoring for pack updates

---

## 7. What Stays Universal (No Jurisdiction Changes Needed)

These features work identically worldwide — the jurisdiction layer doesn't touch them:

- **Authentication** (Firebase Auth)
- **Team management** (members, roles, invitations)
- **Project management** (create, status, timeline)
- **Inspection execution** (checklist items, pass/fail, photos, GPS)
- **Worker management** (profiles, assignments)
- **Equipment tracking** (maintenance schedules, inspection logs)
- **Hazard reporting** (photo upload, description, status tracking)
- **Incident recording** (who, what, when, where — classification is jurisdiction-specific)
- **Morning brief** (weather, alerts, risk score)
- **Toolbox talks** (scheduling, attendance, signatures)
- **PDF generation** (WeasyPrint — content is jurisdiction-specific, rendering is universal)
- **GC portal** (relationship management, document sharing)
- **Analytics** (aggregation logic is universal; metric names/formulas are jurisdiction-specific)
- **Billing** (Paddle handles multi-currency natively)

The jurisdiction layer only affects:
1. **What standards are referenced** in generated documents
2. **What certifications are valid** for workers
3. **What compliance rules are checked** in audits
4. **What metric formulas** are used for incident rates
5. **How data is formatted** (dates, units, currency)
6. **What UI labels say** (OSHA Log vs RIDDOR vs Notifiable Incidents)

---

## 8. Validation: How to Verify a Jurisdiction Pack

Each pack goes through this checklist before release:

1. **Schema validation**: All YAML files pass `_schema.yaml` validation
2. **Prompt test**: Generate one of each document type, review for correct regulation references
3. **Compliance test**: Run compliance audit against a test company, verify rules fire correctly
4. **Certification test**: Create workers with local cert types, verify status tracking works
5. **Formatting test**: Verify dates, currency, units display correctly in UI
6. **Expert review**: Local safety professional reviews generated documents (1-2 days)
7. **Regression**: All US tests still pass (jurisdiction default unchanged)
