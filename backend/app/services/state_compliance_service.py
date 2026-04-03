"""State compliance engine service.

Provides state-specific safety requirements beyond federal OSHA
and checks company compliance against those requirements.
"""

from app.models.state_compliance import (
    StateComplianceCheck,
    StateComplianceGap,
    StateRequirement,
)
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.worker_service import WorkerService


# -- State requirements knowledge base ------------------------------------------------

_STATE_REQUIREMENTS: dict[str, list[dict]] = {
    "CA": [
        {
            "id": "CA-001",
            "state": "CA",
            "requirement_name": "Written Injury & Illness Prevention Program (IIPP)",
            "description": "Every California employer must establish, implement, and maintain a written IIPP. More detailed than federal requirements.",
            "federal_equivalent": "29 CFR 1904 (General Recording)",
            "state_standard": "Cal/OSHA T8 CCR 3203",
            "additional_details": "Must include system for identifying/evaluating hazards, methods for correcting hazards, training, communication, and recordkeeping.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "CA-002",
            "state": "CA",
            "requirement_name": "Heat Illness Prevention Plan",
            "description": "Mandatory outdoor heat illness prevention plan when temperatures exceed 80 degrees F.",
            "federal_equivalent": None,
            "state_standard": "Cal/OSHA T8 CCR 3395",
            "additional_details": "Must provide water, shade, rest breaks, acclimatization procedures, and emergency response procedures.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "CA-003",
            "state": "CA",
            "requirement_name": "Wildfire Smoke Protection Plan",
            "description": "Employers must protect workers from wildfire smoke exposure when AQI for PM2.5 exceeds 151.",
            "federal_equivalent": None,
            "state_standard": "Cal/OSHA T8 CCR 5141.1",
            "additional_details": "Must include monitoring air quality, providing N95 respirators, and communication procedures.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "CA-004",
            "state": "CA",
            "requirement_name": "Higher Penalty Structure",
            "description": "Cal/OSHA penalties are significantly higher than federal OSHA. Serious violations up to $25,000.",
            "federal_equivalent": "29 CFR 1903.15",
            "state_standard": "Cal/OSHA Labor Code 6427-6430",
            "additional_details": "Willful violations up to $156,259. Repeat violations up to $156,259.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "CA-005",
            "state": "CA",
            "requirement_name": "Permit-Required Confined Space (Construction)",
            "description": "Cal/OSHA has specific construction-focused confined space requirements beyond federal.",
            "federal_equivalent": "29 CFR 1926.1200",
            "state_standard": "Cal/OSHA T8 CCR 5157",
            "additional_details": "Requires written program, entry permits, and attendant training specific to construction environments.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
    ],
    "NY": [
        {
            "id": "NY-001",
            "state": "NY",
            "requirement_name": "OSHA 10-Hour Training (All Workers)",
            "description": "All construction workers on NYC public and private sites must have OSHA 10-hour training.",
            "federal_equivalent": None,
            "state_standard": "NYC Local Law 196 of 2017",
            "additional_details": "Workers must carry SST cards. Employers face fines for non-compliant workers on site.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "NY-002",
            "state": "NY",
            "requirement_name": "OSHA 30-Hour Training (Supervisors)",
            "description": "All construction supervisors and foremen on NYC sites must have OSHA 30-hour training.",
            "federal_equivalent": None,
            "state_standard": "NYC Local Law 196 of 2017",
            "additional_details": "Site Safety Managers must also hold 30-hour cards plus additional FDNY certificates.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "NY-003",
            "state": "NY",
            "requirement_name": "Site Safety Manager Requirement",
            "description": "Certain NYC construction projects require a designated Site Safety Manager or Coordinator.",
            "federal_equivalent": None,
            "state_standard": "NYC Building Code 3310.5",
            "additional_details": "Required on major buildings (10+ stories, full demolition, certain excavations). Must hold NYC DOB license.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "NY-004",
            "state": "NY",
            "requirement_name": "Scaffold Safety Training",
            "description": "All workers erecting, dismantling, or using scaffolds must complete scaffold safety training.",
            "federal_equivalent": "29 CFR 1926.454",
            "state_standard": "NY Industrial Code Rule 23",
            "additional_details": "4-hour scaffold training course approved by NYC DOB. Must be renewed every 4 years.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
    ],
    "WA": [
        {
            "id": "WA-001",
            "state": "WA",
            "requirement_name": "Accident Prevention Program (APP)",
            "description": "Every Washington employer must have a written Accident Prevention Program tailored to their workplace.",
            "federal_equivalent": None,
            "state_standard": "WAC 296-800-140",
            "additional_details": "Must include safety orientation, hazard reporting, regular safety meetings, and first-aid procedures.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "WA-002",
            "state": "WA",
            "requirement_name": "Outdoor Heat Exposure Rule",
            "description": "Employers must take precautions when temperatures reach 80 degrees F or above.",
            "federal_equivalent": None,
            "state_standard": "WAC 296-62-095",
            "additional_details": "Water, shade, rest breaks required. High heat procedures at 90 degrees F. Emergency response plan mandatory.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "WA-003",
            "state": "WA",
            "requirement_name": "Fall Protection at 4 Feet",
            "description": "Washington requires fall protection at 4 feet in construction, stricter than federal 6-foot trigger.",
            "federal_equivalent": "29 CFR 1926.501 (6 feet)",
            "state_standard": "WAC 296-880-20005",
            "additional_details": "All unprotected sides and edges at 4 feet or more require guardrails, safety nets, or personal fall arrest.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "WA-004",
            "state": "WA",
            "requirement_name": "Safety Committee or Safety Meetings",
            "description": "Employers with 11+ employees must have a safety committee. Smaller employers must hold regular safety meetings.",
            "federal_equivalent": None,
            "state_standard": "WAC 296-800-130",
            "additional_details": "Committee must meet monthly, include employer and employee representatives, and maintain written records.",
            "applies_to": "all",
            "severity": "mandatory",
        },
    ],
    "OR": [
        {
            "id": "OR-001",
            "state": "OR",
            "requirement_name": "Safety Committee or Safety Meetings",
            "description": "Employers with 11 or more employees must establish a safety committee. Smaller employers must hold regular safety meetings.",
            "federal_equivalent": None,
            "state_standard": "OAR 437-001-0765",
            "additional_details": "Committee must meet monthly. Must include employee-elected representatives. Written minutes required.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "OR-002",
            "state": "OR",
            "requirement_name": "Fall Protection at 10 Feet",
            "description": "Oregon requires fall protection in construction at 10 feet, different from federal 6-foot standard.",
            "federal_equivalent": "29 CFR 1926.501 (6 feet)",
            "state_standard": "OAR 437-003-0001(5)",
            "additional_details": "Applies to construction activities. Some exceptions for specific trades with alternative protection measures.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
        {
            "id": "OR-003",
            "state": "OR",
            "requirement_name": "Heat Illness Prevention",
            "description": "Oregon requires employers to protect workers from heat-related illness at 80 degrees F.",
            "federal_equivalent": None,
            "state_standard": "OAR 437-002-0156",
            "additional_details": "Access to shade, cool water, acclimatization for new workers, and high heat protocols at 90 degrees F.",
            "applies_to": "all",
            "severity": "mandatory",
        },
    ],
    "MI": [
        {
            "id": "MI-001",
            "state": "MI",
            "requirement_name": "Written Safety & Health Program",
            "description": "Michigan OSHA (MIOSHA) requires employers to develop and maintain a comprehensive written safety and health program.",
            "federal_equivalent": None,
            "state_standard": "MIOSHA Part 1, Rule 114",
            "additional_details": "Must include management commitment, employee involvement, worksite analysis, hazard prevention, and training.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "MI-002",
            "state": "MI",
            "requirement_name": "Right to Know Act",
            "description": "Michigan's Right to Know law has additional requirements beyond federal HazCom standard.",
            "federal_equivalent": "29 CFR 1910.1200",
            "state_standard": "PA 154 of 1986",
            "additional_details": "Employers must provide annual training, maintain chemical lists, and post workplace notices.",
            "applies_to": "all",
            "severity": "mandatory",
        },
        {
            "id": "MI-003",
            "state": "MI",
            "requirement_name": "Construction Safety Standards",
            "description": "MIOSHA has state-specific construction safety standards that may differ from federal OSHA.",
            "federal_equivalent": "29 CFR 1926",
            "state_standard": "MIOSHA Construction Safety Standards Part 1-45",
            "additional_details": "Includes state-specific requirements for scaffolding, demolition, and steel erection.",
            "applies_to": "construction",
            "severity": "mandatory",
        },
    ],
}

_SUPPORTED_STATES: list[dict[str, str]] = [
    {"code": "CA", "name": "California"},
    {"code": "NY", "name": "New York"},
    {"code": "WA", "name": "Washington"},
    {"code": "OR", "name": "Oregon"},
    {"code": "MI", "name": "Michigan"},
]


class StateComplianceService:
    """Checks company compliance against state-specific safety requirements.

    Args:
        company_service: CompanyService for company profile lookups.
        document_service: DocumentService for document checks.
        worker_service: WorkerService for training/cert checks.
    """

    def __init__(
        self,
        company_service: CompanyService,
        document_service: DocumentService,
        worker_service: WorkerService,
    ) -> None:
        self.company_service = company_service
        self.document_service = document_service
        self.worker_service = worker_service

    def get_available_states(self) -> list[dict[str, str]]:
        """Return the list of states with supported compliance checks.

        Returns:
            A list of dicts with 'code' and 'name' keys.
        """
        return list(_SUPPORTED_STATES)

    def get_state_requirements(self, state: str) -> list[StateRequirement]:
        """Return all requirements for a given state.

        Args:
            state: Two-letter state code (e.g., 'CA', 'NY').

        Returns:
            A list of StateRequirement models for the state.
        """
        state_upper = state.upper()
        raw_requirements = _STATE_REQUIREMENTS.get(state_upper, [])
        return [StateRequirement(**req) for req in raw_requirements]

    def check_compliance(
        self, company_id: str, state: str
    ) -> StateComplianceCheck:
        """Check a company's compliance against state-specific requirements.

        Examines the company's documents, training records, and safety
        programs to determine which state requirements are met.

        Args:
            company_id: The company ID to check.
            state: Two-letter state code.

        Returns:
            A StateComplianceCheck with gaps and compliance percentage.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        state_upper = state.upper()
        requirements = self.get_state_requirements(state_upper)

        if not requirements:
            return StateComplianceCheck(
                state=state_upper,
                total_requirements=0,
                met_requirements=0,
                gaps=[],
                compliance_percentage=100,
            )

        # Gather company data for checking
        self.company_service.get(company_id)

        # Get documents
        doc_result = self.document_service.list_documents(
            company_id=company_id, limit=500
        )
        existing_docs = doc_result.get("documents", [])
        doc_titles_lower = [d.title.lower() for d in existing_docs]
        doc_types = {d.document_type.value for d in existing_docs}

        # Get worker data
        worker_result = self.worker_service.list_workers(
            company_id=company_id, limit=500
        )
        workers = worker_result.get("workers", [])

        # Check for specific certifications
        has_osha_10 = False
        has_osha_30 = False
        has_fall_protection_training = False

        for worker in workers:
            for cert in worker.certifications:
                cert_type = cert.certification_type.value
                if cert_type == "osha_10":
                    has_osha_10 = True
                elif cert_type == "osha_30":
                    has_osha_30 = True
                elif cert_type == "fall_protection":
                    has_fall_protection_training = True

        has_written_safety = "sssp" in doc_types
        has_fall_protection_doc = "fall_protection" in doc_types

        # Check each requirement
        gaps: list[StateComplianceGap] = []
        met_count = 0

        for req in requirements:
            is_met = False

            # Check by requirement keywords against documents and capabilities
            req_name_lower = req.requirement_name.lower()

            if "iipp" in req_name_lower or "injury" in req_name_lower and "illness" in req_name_lower:
                is_met = has_written_safety or any(
                    "iipp" in t or "injury" in t for t in doc_titles_lower
                )

            elif "heat illness" in req_name_lower or "heat exposure" in req_name_lower:
                is_met = any(
                    "heat" in t for t in doc_titles_lower
                )

            elif "wildfire" in req_name_lower or "smoke" in req_name_lower:
                is_met = any(
                    "wildfire" in t or "smoke" in t for t in doc_titles_lower
                )

            elif "penalty" in req_name_lower:
                # Awareness item - always considered met if they have a safety program
                is_met = has_written_safety

            elif "confined space" in req_name_lower:
                is_met = any(
                    "confined" in t for t in doc_titles_lower
                )

            elif "osha 10" in req_name_lower and "all worker" in req_name_lower.lower():
                is_met = has_osha_10

            elif "osha 30" in req_name_lower and "supervisor" in req_name_lower.lower():
                is_met = has_osha_30

            elif "site safety manager" in req_name_lower:
                # Check if company has a safety officer designated
                try:
                    company = self.company_service.get(company_id)
                    is_met = bool(company.safety_officer)
                except Exception:
                    is_met = False

            elif "scaffold" in req_name_lower:
                is_met = any(
                    cert.certification_type.value == "scaffold_competent"
                    for w in workers
                    for cert in w.certifications
                )

            elif "accident prevention" in req_name_lower:
                is_met = has_written_safety or any(
                    "accident prevention" in t or "app" in t
                    for t in doc_titles_lower
                )

            elif "fall protection" in req_name_lower:
                is_met = has_fall_protection_doc or has_fall_protection_training

            elif "safety committee" in req_name_lower or "safety meeting" in req_name_lower:
                # Check if they conduct toolbox talks (proxy for safety meetings)
                is_met = any(
                    "toolbox" in t or "safety meeting" in t
                    for t in doc_titles_lower
                )

            elif "written safety" in req_name_lower or "safety & health program" in req_name_lower:
                is_met = has_written_safety

            elif "right to know" in req_name_lower or "hazcom" in req_name_lower:
                is_met = any(
                    "hazcom" in t or "right to know" in t or "ghs" in t
                    for t in doc_titles_lower
                )

            elif "construction safety" in req_name_lower:
                is_met = has_written_safety

            else:
                # Default: check if any document title contains keywords
                keywords = [
                    w for w in req_name_lower.split() if len(w) > 3
                ]
                is_met = any(
                    any(kw in t for kw in keywords) for t in doc_titles_lower
                )

            if is_met:
                met_count += 1
            else:
                gaps.append(
                    StateComplianceGap(
                        requirement_id=req.id,
                        requirement_name=req.requirement_name,
                        status="not_met",
                        action_needed=f"Create or upload documentation for: {req.requirement_name}. "
                        f"Reference: {req.state_standard}",
                    )
                )

        total = len(requirements)
        compliance_pct = int((met_count / total) * 100) if total > 0 else 100

        return StateComplianceCheck(
            state=state_upper,
            total_requirements=total,
            met_requirements=met_count,
            gaps=gaps,
            compliance_percentage=compliance_pct,
        )
