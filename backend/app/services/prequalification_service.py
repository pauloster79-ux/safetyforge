"""Prequalification automation service.

Assembles prequalification packages from existing SafetyForge data
for ISNetworld, Avetta, BROWZ, and generic GC submissions.
"""

import secrets
from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, PrequalPackageNotFoundError
from app.models.prequalification import (
    PrequalDocument,
    PrequalDocumentStatus,
    PrequalPackage,
    PrequalPlatform,
)
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.mock_inspection_service import MockInspectionService
from app.services.osha_log_service import OshaLogService
from app.services.worker_service import WorkerService


class PrequalificationService:
    """Assembles prequalification packages from existing company data.

    Args:
        db: Firestore client instance.
        company_service: CompanyService for company profile data.
        document_service: DocumentService for safety documents.
        osha_log_service: OshaLogService for OSHA 300 data.
        worker_service: WorkerService for training/cert data.
        mock_inspection_service: MockInspectionService for inspection scores.
    """

    def __init__(
        self,
        db: firestore.Client,
        company_service: CompanyService,
        document_service: DocumentService,
        osha_log_service: OshaLogService,
        worker_service: WorkerService,
        mock_inspection_service: MockInspectionService,
    ) -> None:
        self.db = db
        self.company_service = company_service
        self.document_service = document_service
        self.osha_log_service = osha_log_service
        self.worker_service = worker_service
        self.mock_inspection_service = mock_inspection_service

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the prequalification_packages subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return (
            self.db.collection("companies")
            .document(company_id)
            .collection("prequalification_packages")
        )

    def _generate_id(self) -> str:
        """Generate a unique prequalification package ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"prequal_{secrets.token_hex(8)}"

    def get_isnetworld_requirements(self) -> list[PrequalDocument]:
        """Return the list of ISNetworld-specific document requirements.

        Returns:
            A list of PrequalDocument objects with ISNetworld requirements.
        """
        return [
            PrequalDocument(
                document_name="Written Safety & Health Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Must include company safety policy, responsibilities, and procedures",
            ),
            PrequalDocument(
                document_name="Hazard Communication (HazCom/GHS) Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Written HazCom program with SDS management procedures",
            ),
            PrequalDocument(
                document_name="Fall Protection Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Written fall protection plan per 29 CFR 1926.502",
            ),
            PrequalDocument(
                document_name="Excavation/Trenching Safety Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Competent person designation and soil classification procedures",
            ),
            PrequalDocument(
                document_name="Confined Space Entry Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Permit-required confined space entry procedures",
            ),
            PrequalDocument(
                document_name="Lockout/Tagout (LOTO) Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Energy control procedures per 29 CFR 1910.147",
            ),
            PrequalDocument(
                document_name="OSHA 300 Log - Current Year",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Current calendar year OSHA 300 log",
            ),
            PrequalDocument(
                document_name="OSHA 300 Log - Previous Year",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Previous calendar year OSHA 300 log",
            ),
            PrequalDocument(
                document_name="OSHA 300 Log - Two Years Prior",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Two years prior OSHA 300 log",
            ),
            PrequalDocument(
                document_name="OSHA 300A Annual Summary (3 years)",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Certified 300A summaries for the past 3 years",
            ),
            PrequalDocument(
                document_name="EMR Letter - Current Year",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Experience Modification Rate letter from insurance carrier",
            ),
            PrequalDocument(
                document_name="EMR Letter - Previous Year",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Previous year EMR letter",
            ),
            PrequalDocument(
                document_name="EMR Letter - Two Years Prior",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Two years prior EMR letter",
            ),
            PrequalDocument(
                document_name="Certificate of Insurance (COI)",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Current certificate of liability insurance",
            ),
            PrequalDocument(
                document_name="Drug & Alcohol Testing Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Written drug and alcohol policy with testing procedures",
            ),
            PrequalDocument(
                document_name="Training Records Matrix",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="workers",
                notes="Complete training matrix showing all worker certifications",
            ),
            PrequalDocument(
                document_name="Safety Meeting/Toolbox Talk Records",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Weekly safety meeting and toolbox talk documentation",
            ),
            PrequalDocument(
                document_name="Incident Investigation Procedures",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Written incident investigation and root cause analysis procedures",
            ),
        ]

    def get_avetta_requirements(self) -> list[PrequalDocument]:
        """Return the list of Avetta-specific document requirements.

        Returns:
            A list of PrequalDocument objects with Avetta requirements.
        """
        return [
            PrequalDocument(
                document_name="Health & Safety Management System",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Comprehensive H&S management system documentation",
            ),
            PrequalDocument(
                document_name="Environmental Management Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Environmental compliance and waste management procedures",
            ),
            PrequalDocument(
                document_name="OSHA 300 Log (3 years)",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="OSHA 300 logs for the past 3 calendar years",
            ),
            PrequalDocument(
                document_name="OSHA 300A Summary (3 years)",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Certified 300A summaries for the past 3 years",
            ),
            PrequalDocument(
                document_name="EMR Documentation (3 years)",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="EMR letters or NCCI worksheets for 3 years",
            ),
            PrequalDocument(
                document_name="Certificate of Insurance (COI)",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Current comprehensive liability insurance certificate",
            ),
            PrequalDocument(
                document_name="Workers Compensation Certificate",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Current workers compensation insurance certificate",
            ),
            PrequalDocument(
                document_name="Drug & Alcohol Policy",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Written drug and alcohol testing policy",
            ),
            PrequalDocument(
                document_name="Training Records",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="workers",
                notes="Certification and training records for all workers",
            ),
            PrequalDocument(
                document_name="Incident/Accident Reports",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Incident investigation reports for the past 3 years",
            ),
            PrequalDocument(
                document_name="Safety Orientation Program",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="New hire safety orientation program documentation",
            ),
            PrequalDocument(
                document_name="Company Profile & Contact Information",
                category="Company Info",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Company overview, contact details, years in business",
            ),
        ]

    def get_generic_gc_requirements(self) -> list[PrequalDocument]:
        """Return common GC prequalification document requirements.

        Returns:
            A list of PrequalDocument objects with generic GC requirements.
        """
        return [
            PrequalDocument(
                document_name="Written Safety Program",
                category="Safety Programs",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Company safety and health program",
            ),
            PrequalDocument(
                document_name="OSHA 300 Log (Current Year)",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Current year OSHA 300 log",
            ),
            PrequalDocument(
                document_name="OSHA 300A Summary",
                category="OSHA Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="osha_log",
                notes="Most recent certified 300A annual summary",
            ),
            PrequalDocument(
                document_name="EMR Letter",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Current year Experience Modification Rate letter",
            ),
            PrequalDocument(
                document_name="Certificate of Insurance",
                category="Insurance",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Current certificate of liability insurance",
            ),
            PrequalDocument(
                document_name="Training Records",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="workers",
                notes="Worker training and certification records",
            ),
            PrequalDocument(
                document_name="Safety Meeting Records",
                category="Training Records",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="documents",
                notes="Toolbox talk and safety meeting documentation",
            ),
            PrequalDocument(
                document_name="Company Information",
                category="Company Info",
                required=True,
                status=PrequalDocumentStatus.MISSING,
                source="company",
                notes="Company profile, trade info, and contact details",
            ),
        ]

    def _get_platform_requirements(
        self, platform: PrequalPlatform
    ) -> list[PrequalDocument]:
        """Return requirements for the specified platform.

        Args:
            platform: The target prequalification platform.

        Returns:
            A list of PrequalDocument objects for the platform.
        """
        if platform == PrequalPlatform.ISNETWORLD:
            return self.get_isnetworld_requirements()
        elif platform == PrequalPlatform.AVETTA:
            return self.get_avetta_requirements()
        elif platform == PrequalPlatform.BROWZ:
            # BROWZ requirements are similar to Avetta
            return self.get_avetta_requirements()
        else:
            return self.get_generic_gc_requirements()

    def _check_document_availability(
        self, company_id: str, requirements: list[PrequalDocument]
    ) -> list[PrequalDocument]:
        """Check which required documents exist in SafetyForge and update statuses.

        Args:
            company_id: The company ID to check documents for.
            requirements: List of platform requirements to check against.

        Returns:
            Updated list of PrequalDocuments with accurate statuses.
        """
        # Get all company documents
        doc_result = self.document_service.list_documents(
            company_id=company_id, limit=500
        )
        existing_docs = doc_result.get("documents", [])
        doc_titles_lower = {d.title.lower(): d for d in existing_docs}
        doc_types = {d.document_type.value for d in existing_docs}

        # Get OSHA log years
        osha_years = self.osha_log_service.get_years_with_entries(company_id)
        current_year = date.today().year

        # Get worker training data
        worker_result = self.worker_service.list_workers(
            company_id=company_id, limit=500
        )
        workers = worker_result.get("workers", [])
        has_training_records = len(workers) > 0 and any(
            w.total_certifications > 0 for w in workers
        )

        # Get company profile
        try:
            company = self.company_service.get(company_id)
            has_company_info = True
        except CompanyNotFoundError:
            has_company_info = False

        updated = []
        for req in requirements:
            req_copy = req.model_copy()

            if req_copy.source == "documents":
                # Check if a matching document exists by type or title keyword
                matched = False
                for doc in existing_docs:
                    title_lower = doc.title.lower()
                    req_name_lower = req_copy.document_name.lower()
                    # Match by keywords in the document name
                    keywords = req_name_lower.split()
                    if any(kw in title_lower for kw in keywords if len(kw) > 3):
                        req_copy.status = PrequalDocumentStatus.READY
                        req_copy.source_id = doc.id
                        matched = True
                        break

                if not matched:
                    # Check by document type mapping
                    type_map = {
                        "sssp": ["safety", "health", "management"],
                        "jha": ["hazard", "analysis"],
                        "fall_protection": ["fall protection"],
                    }
                    for doc_type, keywords in type_map.items():
                        if doc_type in doc_types:
                            if any(
                                kw in req_copy.document_name.lower()
                                for kw in keywords
                            ):
                                req_copy.status = PrequalDocumentStatus.READY
                                matched = True
                                break

                if not matched:
                    req_copy.status = PrequalDocumentStatus.MISSING

            elif req_copy.source == "osha_log":
                # Check OSHA log availability
                if "current" in req_copy.document_name.lower():
                    if current_year in osha_years:
                        req_copy.status = PrequalDocumentStatus.READY
                    else:
                        req_copy.status = PrequalDocumentStatus.MISSING
                elif "previous" in req_copy.document_name.lower():
                    if (current_year - 1) in osha_years:
                        req_copy.status = PrequalDocumentStatus.READY
                    else:
                        req_copy.status = PrequalDocumentStatus.MISSING
                elif "two years" in req_copy.document_name.lower():
                    if (current_year - 2) in osha_years:
                        req_copy.status = PrequalDocumentStatus.READY
                    else:
                        req_copy.status = PrequalDocumentStatus.MISSING
                elif "3 year" in req_copy.notes.lower() or "3 year" in req_copy.document_name.lower():
                    years_available = sum(
                        1
                        for y in [current_year, current_year - 1, current_year - 2]
                        if y in osha_years
                    )
                    if years_available >= 3:
                        req_copy.status = PrequalDocumentStatus.READY
                    elif years_available > 0:
                        req_copy.status = PrequalDocumentStatus.OUTDATED
                        req_copy.notes += f" ({years_available}/3 years available)"
                    else:
                        req_copy.status = PrequalDocumentStatus.MISSING
                else:
                    # Generic OSHA check
                    if len(osha_years) > 0:
                        req_copy.status = PrequalDocumentStatus.READY
                    else:
                        req_copy.status = PrequalDocumentStatus.MISSING

            elif req_copy.source == "workers":
                if has_training_records:
                    req_copy.status = PrequalDocumentStatus.READY
                else:
                    req_copy.status = PrequalDocumentStatus.MISSING

            elif req_copy.source == "company":
                if has_company_info:
                    req_copy.status = PrequalDocumentStatus.READY
                else:
                    req_copy.status = PrequalDocumentStatus.MISSING

            updated.append(req_copy)

        return updated

    def prefill_questionnaire(
        self, company_id: str, platform: PrequalPlatform
    ) -> dict[str, Any]:
        """Auto-fill common prequalification questionnaire answers.

        Args:
            company_id: The company ID to pull data from.
            platform: The target prequalification platform.

        Returns:
            A dict of pre-filled questionnaire answers.
        """
        try:
            company = self.company_service.get(company_id)
        except CompanyNotFoundError:
            return {}

        current_year = date.today().year

        # Get OSHA metrics for current and prior years
        trir_current = 0.0
        dart_current = 0.0
        trir_prev_1 = 0.0
        trir_prev_2 = 0.0
        for year_offset, label in [(0, "current"), (1, "prev_1"), (2, "prev_2")]:
            try:
                summary = self.osha_log_service.get_300a_summary(
                    company_id, current_year - year_offset
                )
                if year_offset == 0:
                    trir_current = summary.trir
                    dart_current = summary.dart
                elif year_offset == 1:
                    trir_prev_1 = summary.trir
                elif year_offset == 2:
                    trir_prev_2 = summary.trir
            except Exception:
                pass

        # Get worker count
        worker_result = self.worker_service.list_workers(
            company_id=company_id, limit=1
        )
        num_employees = worker_result.get("total", 0)

        # Get document stats
        doc_stats = self.document_service.get_stats(company_id)
        has_written_safety = doc_stats.get("by_type", {}).get("sssp", 0) > 0

        # Get mock inspection data
        mock_ref = (
            self.db.collection("companies")
            .document(company_id)
            .collection("mock_inspection_results")
        )
        mock_docs = list(
            mock_ref.order_by(
                "created_at", direction=firestore.Query.DESCENDING
            )
            .limit(1)
            .stream()
        )
        mock_score = None
        if mock_docs:
            mock_data = mock_docs[0].to_dict()
            mock_score = mock_data.get("overall_score")

        # Calculate years in business from company creation
        years_in_business = 0
        if company.created_at:
            delta = datetime.now(timezone.utc) - company.created_at
            years_in_business = max(1, delta.days // 365)

        questionnaire: dict[str, Any] = {
            "company_name": company.name,
            "company_address": company.address,
            "ein": company.ein or "",
            "license_number": company.license_number,
            "trade_type": company.trade_type.value,
            "owner_name": company.owner_name,
            "phone": company.phone,
            "email": company.email,
            "years_in_business": years_in_business,
            "number_of_employees": num_employees,
            "emr_current": 1.0,
            "emr_previous_1": 1.0,
            "emr_previous_2": 1.0,
            "trir_current": trir_current,
            "trir_previous_1": trir_prev_1,
            "trir_previous_2": trir_prev_2,
            "dart_current": dart_current,
            "has_written_safety_program": has_written_safety,
            "has_drug_testing_program": False,
            "safety_director_name": company.safety_officer or "",
            "safety_director_phone": company.safety_officer_phone or "",
            "osha_citations_past_5_years": 0,
            "fatalities_past_5_years": 0,
            "has_fall_protection_program": doc_stats.get("by_type", {}).get("fall_protection", 0) > 0,
            "has_hazcom_program": False,
            "has_confined_space_program": False,
            "has_lockout_tagout_program": False,
            "has_excavation_program": False,
            "conducts_regular_inspections": True,
            "conducts_toolbox_talks": True,
            "has_incident_investigation_procedure": False,
            "has_return_to_work_program": False,
            "has_safety_orientation": False,
            "mock_inspection_score": mock_score,
            "total_documents_on_file": doc_stats.get("total", 0),
        }

        return questionnaire

    def generate_package(
        self,
        company_id: str,
        platform: PrequalPlatform,
        client_name: str,
        user_id: str,
    ) -> PrequalPackage:
        """Assemble a complete prequalification package from existing data.

        Pulls from all SafetyForge modules to check document availability,
        compute OSHA metrics, assess training records, and pre-fill
        questionnaire answers.

        Args:
            company_id: The company ID to generate the package for.
            platform: The target prequalification platform.
            client_name: Name of the GC or owner requesting prequal.
            user_id: Firebase UID of the user generating the package.

        Returns:
            The assembled PrequalPackage with readiness scores.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        # Verify company exists
        self.company_service.get(company_id)

        # Get platform requirements and check availability
        requirements = self._get_platform_requirements(platform)
        documents = self._check_document_availability(company_id, requirements)

        # Calculate readiness
        required_docs = [d for d in documents if d.required]
        total = len(required_docs)
        ready = sum(1 for d in required_docs if d.status == PrequalDocumentStatus.READY)
        outdated = sum(
            1 for d in required_docs if d.status == PrequalDocumentStatus.OUTDATED
        )
        missing = sum(
            1 for d in required_docs if d.status == PrequalDocumentStatus.MISSING
        )
        overall_readiness = int((ready / total) * 100) if total > 0 else 0

        # Pre-fill questionnaire
        questionnaire = self.prefill_questionnaire(company_id, platform)

        now = datetime.now(timezone.utc)
        package_id = self._generate_id()

        package = PrequalPackage(
            id=package_id,
            company_id=company_id,
            platform=platform,
            client_name=client_name,
            submission_deadline=None,
            overall_readiness=overall_readiness,
            total_documents=len(documents),
            ready_documents=ready,
            outdated_documents=outdated,
            missing_documents=missing,
            documents=documents,
            questionnaire=questionnaire,
            created_at=now,
            updated_at=now,
            created_by=user_id,
        )

        # Store the package
        package_dict = package.model_dump()
        # Serialize datetime and date fields for Firestore
        package_dict["created_at"] = now
        package_dict["updated_at"] = now
        package_dict["platform"] = platform.value
        for doc in package_dict["documents"]:
            doc["status"] = doc["status"]

        self._collection(company_id).document(package_id).set(package_dict)

        return package

    def get_package(self, company_id: str, package_id: str) -> PrequalPackage:
        """Fetch a single prequalification package.

        Args:
            company_id: The owning company ID.
            package_id: The package ID to fetch.

        Returns:
            The PrequalPackage model.

        Raises:
            PrequalPackageNotFoundError: If the package does not exist.
        """
        doc = self._collection(company_id).document(package_id).get()
        if not doc.exists:
            raise PrequalPackageNotFoundError(package_id)
        return PrequalPackage(**doc.to_dict())

    def list_packages(
        self, company_id: str, limit: int = 20, offset: int = 0
    ) -> dict:
        """List prequalification packages for a company.

        Args:
            company_id: The owning company ID.
            limit: Maximum number of packages to return.
            offset: Number of packages to skip.

        Returns:
            A dict with 'packages' list and 'total' count.
        """
        all_docs = []
        for doc in self._collection(company_id).stream():
            all_docs.append(doc.to_dict())

        total = len(all_docs)
        all_docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        paginated = all_docs[offset : offset + limit]

        packages = [PrequalPackage(**d) for d in paginated]
        return {"packages": packages, "total": total}
