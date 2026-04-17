"""State compliance engine service.

Provides state-specific safety requirements beyond federal OSHA
and checks company compliance against those requirements.

Requirements are stored in the Neo4j graph as Regulation nodes
linked to Region nodes via HAS_REQUIREMENT relationships.
"""

from neo4j import Driver

from app.models.state_compliance import (
    StateComplianceCheck,
    StateComplianceGap,
    StateRequirement,
)
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.worker_service import WorkerService


class StateComplianceService:
    """Checks company compliance against state-specific safety requirements.

    Reads requirements from the Neo4j knowledge graph instead of
    hardcoded Python dicts, enabling dynamic expansion of state
    coverage via YAML jurisdiction packs and the seed script.

    Args:
        driver: Neo4j driver for graph queries.
        company_service: CompanyService for company profile lookups.
        document_service: DocumentService for document checks.
        worker_service: WorkerService for training/cert checks.
    """

    def __init__(
        self,
        driver: Driver,
        company_service: CompanyService,
        document_service: DocumentService,
        worker_service: WorkerService,
    ) -> None:
        self.driver = driver
        self.company_service = company_service
        self.document_service = document_service
        self.worker_service = worker_service

    def get_available_states(self) -> list[dict[str, str]]:
        """Return all US states that have requirements in the graph.

        Returns:
            A list of dicts with 'code' and 'name' keys, sorted by name.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (j:Jurisdiction {code: 'US'})-[:HAS_REGION]->(r:Region)
                WHERE EXISTS { (r)-[:HAS_REQUIREMENT]->(:Regulation) }
                RETURN r.code AS code, r.name AS name
                ORDER BY r.name
                """
            )
            return [{"code": record["code"], "name": record["name"]} for record in result]

    def get_state_requirements(self, state: str) -> list[StateRequirement]:
        """Return all requirements for a given state from the graph.

        Args:
            state: Two-letter state code (e.g., 'CA', 'NY').

        Returns:
            A list of StateRequirement models for the state.
        """
        state_upper = state.upper()
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (r:Region {code: $state})-[:HAS_REQUIREMENT]->(reg:Regulation)
                RETURN reg.id AS id,
                       reg.region_code AS state,
                       reg.requirement_name AS requirement_name,
                       reg.description AS description,
                       reg.federal_equivalent AS federal_equivalent,
                       reg.state_standard AS state_standard,
                       reg.additional_details AS additional_details,
                       reg.applies_to AS applies_to,
                       reg.severity AS severity
                ORDER BY reg.id
                """,
                state=state_upper,
            )
            return [
                StateRequirement(
                    id=record["id"],
                    state=record["state"] or state_upper,
                    requirement_name=record["requirement_name"],
                    description=record["description"] or "",
                    federal_equivalent=record["federal_equivalent"],
                    state_standard=record["state_standard"] or "",
                    additional_details=record["additional_details"] or "",
                    applies_to=record["applies_to"] or "all",
                    severity=record["severity"] or "mandatory",
                )
                for record in result
            ]

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
            is_met = self._check_requirement(
                req,
                doc_titles_lower,
                has_written_safety,
                has_osha_10,
                has_osha_30,
                has_fall_protection_training,
                has_fall_protection_doc,
                workers,
                company_id,
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

    def _check_requirement(
        self,
        req: StateRequirement,
        doc_titles_lower: list[str],
        has_written_safety: bool,
        has_osha_10: bool,
        has_osha_30: bool,
        has_fall_protection_training: bool,
        has_fall_protection_doc: bool,
        workers: list,
        company_id: str,
    ) -> bool:
        """Check whether a single requirement is met by company data.

        Uses keyword-matching heuristics against document titles,
        certifications, and company fields.

        Args:
            req: The requirement to check.
            doc_titles_lower: Lowercased document titles.
            has_written_safety: Whether an SSSP document exists.
            has_osha_10: Whether any worker has OSHA 10 cert.
            has_osha_30: Whether any worker has OSHA 30 cert.
            has_fall_protection_training: Whether fall protection cert exists.
            has_fall_protection_doc: Whether fall protection doc exists.
            workers: List of worker objects.
            company_id: Company ID for additional lookups.

        Returns:
            True if the requirement appears to be met.
        """
        req_name_lower = req.requirement_name.lower()

        if "iipp" in req_name_lower or ("injury" in req_name_lower and "illness" in req_name_lower):
            return has_written_safety or any(
                "iipp" in t or "injury" in t for t in doc_titles_lower
            )

        if "heat illness" in req_name_lower or "heat exposure" in req_name_lower:
            return any("heat" in t for t in doc_titles_lower)

        if "wildfire" in req_name_lower or "smoke" in req_name_lower:
            return any("wildfire" in t or "smoke" in t for t in doc_titles_lower)

        if "penalty" in req_name_lower:
            return has_written_safety

        if "confined space" in req_name_lower:
            return any("confined" in t for t in doc_titles_lower)

        if "osha 10" in req_name_lower and "all worker" in req_name_lower:
            return has_osha_10

        if "osha 30" in req_name_lower and "supervisor" in req_name_lower:
            return has_osha_30

        if "site safety manager" in req_name_lower:
            try:
                company = self.company_service.get(company_id)
                return bool(company.safety_officer)
            except Exception:
                return False

        if "scaffold" in req_name_lower:
            return any(
                cert.certification_type.value == "scaffold_competent"
                for w in workers
                for cert in w.certifications
            )

        if "accident prevention" in req_name_lower:
            return has_written_safety or any(
                "accident prevention" in t or "app" in t
                for t in doc_titles_lower
            )

        if "fall protection" in req_name_lower:
            return has_fall_protection_doc or has_fall_protection_training

        if "safety committee" in req_name_lower or "safety meeting" in req_name_lower:
            return any(
                "toolbox" in t or "safety meeting" in t
                for t in doc_titles_lower
            )

        if "written safety" in req_name_lower or "safety & health program" in req_name_lower:
            return has_written_safety

        if "right to know" in req_name_lower or "hazcom" in req_name_lower:
            return any(
                "hazcom" in t or "right to know" in t or "ghs" in t
                for t in doc_titles_lower
            )

        if "construction safety" in req_name_lower:
            return has_written_safety

        if "workers' compensation" in req_name_lower or "workers compensation" in req_name_lower:
            return any("workers" in t and "comp" in t for t in doc_titles_lower)

        # Default: check if any document title contains keywords
        keywords = [w for w in req_name_lower.split() if len(w) > 3]
        return any(any(kw in t for kw in keywords) for t in doc_titles_lower)
