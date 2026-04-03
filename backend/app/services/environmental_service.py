"""Environmental compliance service against Firestore."""

import secrets
from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import (
    CompanyNotFoundError,
    EnvironmentalProgramNotFoundError,
    ProjectNotFoundError,
)
from app.models.environmental import (
    EnvironmentalProgram,
    EnvironmentalProgramCreate,
    EnvironmentalProgramType,
    EnvironmentalProgramUpdate,
    ExposureMonitoringRecord,
    ExposureMonitoringRecordCreate,
    SwpppInspection,
    SwpppInspectionCreate,
)

# OSHA exposure limits by substance type
OSHA_EXPOSURE_LIMITS: dict[str, dict[str, Any]] = {
    "silica": {
        "pel": 50.0,  # ug/m3 — 29 CFR 1926.1153
        "action_level": 25.0,
        "unit": "ug/m3",
    },
    "lead": {
        "pel": 50.0,  # ug/m3 — 29 CFR 1926.62
        "action_level": 30.0,
        "unit": "ug/m3",
    },
    "asbestos": {
        "pel": 0.1,  # f/cc — 29 CFR 1926.1101
        "action_level": 0.1,  # excursion limit is 1.0 f/cc
        "unit": "f/cc",
    },
    "noise": {
        "pel": 90.0,  # dBA TWA — 29 CFR 1926.52
        "action_level": 85.0,
        "unit": "dBA",
    },
}


class EnvironmentalService:
    """Manages environmental compliance programs, exposure records, and SWPPP inspections.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore document reference.
        """
        return self.db.collection("companies").document(company_id)

    def _programs_collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the environmental_programs subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("environmental_programs")

    def _project_ref(
        self, company_id: str, project_id: str
    ) -> firestore.DocumentReference:
        """Return a reference to the project document.

        Args:
            company_id: The parent company ID.
            project_id: The project ID.

        Returns:
            Firestore document reference.
        """
        return (
            self.db.collection("companies")
            .document(company_id)
            .collection("projects")
            .document(project_id)
        )

    def _exposure_collection(
        self, company_id: str, project_id: str
    ) -> firestore.CollectionReference:
        """Return the exposure_records subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("exposure_records")

    def _swppp_collection(
        self, company_id: str, project_id: str
    ) -> firestore.CollectionReference:
        """Return the swppp_inspections subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection(
            "swppp_inspections"
        )

    def _generate_program_id(self) -> str:
        """Generate a unique environmental program ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"envp_{secrets.token_hex(8)}"

    def _generate_exposure_id(self) -> str:
        """Generate a unique exposure record ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"expr_{secrets.token_hex(8)}"

    def _generate_swppp_id(self) -> str:
        """Generate a unique SWPPP inspection ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"swpp_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        doc = self._project_ref(company_id, project_id).get()
        if not doc.exists:
            raise ProjectNotFoundError(project_id)
        if doc.to_dict().get("deleted", False):
            raise ProjectNotFoundError(project_id)

    # -- Environmental Programs --------------------------------------------------------

    def create_program(
        self,
        company_id: str,
        data: EnvironmentalProgramCreate,
        user_id: str,
    ) -> EnvironmentalProgram:
        """Create a new environmental compliance program.

        Args:
            company_id: The owning company ID.
            data: Validated program creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created EnvironmentalProgram.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        program_id = self._generate_program_id()

        program_dict: dict[str, Any] = {
            "id": program_id,
            "company_id": company_id,
            "program_type": data.program_type.value,
            "title": data.title,
            "content": data.content,
            "applicable_projects": data.applicable_projects,
            "last_reviewed": None,
            "next_review_due": (
                data.next_review_due.isoformat() if data.next_review_due else None
            ),
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "deleted": False,
        }

        self._programs_collection(company_id).document(program_id).set(program_dict)
        return EnvironmentalProgram(**program_dict)

    def get_program(self, company_id: str, program_id: str) -> EnvironmentalProgram:
        """Fetch a single environmental program.

        Args:
            company_id: The owning company ID.
            program_id: The program ID to fetch.

        Returns:
            The EnvironmentalProgram.

        Raises:
            EnvironmentalProgramNotFoundError: If not found or soft-deleted.
        """
        doc = self._programs_collection(company_id).document(program_id).get()
        if not doc.exists:
            raise EnvironmentalProgramNotFoundError(program_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise EnvironmentalProgramNotFoundError(program_id)

        return EnvironmentalProgram(**data)

    def list_programs(
        self,
        company_id: str,
        program_type: EnvironmentalProgramType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List environmental programs for a company with optional filters.

        Args:
            company_id: The owning company ID.
            program_type: Optional filter by program type.
            limit: Maximum number of programs to return.
            offset: Number of programs to skip.

        Returns:
            A dict with 'programs' list and 'total' count.
        """
        base_query: firestore.Query = self._programs_collection(company_id).where(
            "deleted", "==", False
        )

        if program_type is not None:
            base_query = base_query.where("program_type", "==", program_type.value)

        all_docs = [EnvironmentalProgram(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        all_docs.sort(key=lambda p: p.created_at, reverse=True)
        paginated = all_docs[offset : offset + limit]

        return {"programs": paginated, "total": total}

    def update_program(
        self,
        company_id: str,
        program_id: str,
        data: EnvironmentalProgramUpdate,
        user_id: str,
    ) -> EnvironmentalProgram:
        """Update an existing environmental program.

        Args:
            company_id: The owning company ID.
            program_id: The program ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated EnvironmentalProgram.

        Raises:
            EnvironmentalProgramNotFoundError: If not found or soft-deleted.
        """
        doc_ref = self._programs_collection(company_id).document(program_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise EnvironmentalProgramNotFoundError(program_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "next_review_due" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            else:
                update_data[field_name] = value

        if not update_data:
            return EnvironmentalProgram(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)

        doc_ref.update(update_data)
        updated_doc = doc_ref.get()
        return EnvironmentalProgram(**updated_doc.to_dict())

    def delete_program(self, company_id: str, program_id: str) -> None:
        """Soft-delete an environmental program.

        Args:
            company_id: The owning company ID.
            program_id: The program ID to delete.

        Raises:
            EnvironmentalProgramNotFoundError: If not found or already deleted.
        """
        doc_ref = self._programs_collection(company_id).document(program_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise EnvironmentalProgramNotFoundError(program_id)

        doc_ref.update(
            {
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    # -- Exposure Monitoring Records ---------------------------------------------------

    def create_exposure_record(
        self,
        company_id: str,
        project_id: str,
        data: ExposureMonitoringRecordCreate,
        user_id: str,
    ) -> ExposureMonitoringRecord:
        """Create an exposure monitoring record, auto-flagging exceedances.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated exposure record data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created ExposureMonitoringRecord.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        now = datetime.now(timezone.utc)
        record_id = self._generate_exposure_id()

        exceeds_action = data.result_value >= data.action_level
        exceeds_pel = data.result_value >= data.pel

        record_dict: dict[str, Any] = {
            "id": record_id,
            "company_id": company_id,
            "project_id": project_id,
            "monitoring_type": data.monitoring_type,
            "monitoring_date": data.monitoring_date.isoformat(),
            "location": data.location,
            "worker_name": data.worker_name,
            "worker_id": data.worker_id,
            "sample_type": data.sample_type,
            "duration_hours": data.duration_hours,
            "result_value": data.result_value,
            "result_unit": data.result_unit,
            "action_level": data.action_level,
            "pel": data.pel,
            "exceeds_action_level": exceeds_action,
            "exceeds_pel": exceeds_pel,
            "controls_in_place": data.controls_in_place,
            "notes": data.notes,
            "created_at": now,
            "created_by": user_id,
        }

        self._exposure_collection(company_id, project_id).document(record_id).set(
            record_dict
        )
        return ExposureMonitoringRecord(**record_dict)

    def list_exposure_records(
        self,
        company_id: str,
        project_id: str,
        monitoring_type: str | None = None,
        worker_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List exposure monitoring records for a project with optional filters.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            monitoring_type: Optional filter by monitoring type.
            worker_id: Optional filter by worker ID.
            limit: Maximum records to return.
            offset: Number of records to skip.

        Returns:
            A dict with 'records' list and 'total' count.
        """
        base_query: firestore.Query = self._exposure_collection(
            company_id, project_id
        )

        if monitoring_type is not None:
            base_query = base_query.where("monitoring_type", "==", monitoring_type)

        if worker_id is not None:
            base_query = base_query.where("worker_id", "==", worker_id)

        all_docs = [
            ExposureMonitoringRecord(**doc.to_dict()) for doc in base_query.stream()
        ]
        total = len(all_docs)

        all_docs.sort(key=lambda r: r.created_at, reverse=True)
        paginated = all_docs[offset : offset + limit]

        return {"records": paginated, "total": total}

    def get_exposure_summary(self, company_id: str, project_id: str) -> dict:
        """Get a summary of exposure monitoring results by type for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            A dict with 'summaries' list and 'total_samples' count.
        """
        all_records = list(
            self._exposure_collection(company_id, project_id).stream()
        )

        type_data: dict[str, list[dict]] = {}
        for doc in all_records:
            record = doc.to_dict()
            mtype = record.get("monitoring_type", "unknown")
            if mtype not in type_data:
                type_data[mtype] = []
            type_data[mtype].append(record)

        summaries = []
        total_samples = 0

        for mtype, records in type_data.items():
            values = [r.get("result_value", 0) for r in records]
            above_action = sum(
                1 for r in records if r.get("exceeds_action_level", False)
            )
            above_pel = sum(1 for r in records if r.get("exceeds_pel", False))
            avg_val = sum(values) / len(values) if values else 0.0
            max_val = max(values) if values else 0.0
            total_samples += len(records)

            # Use first record for unit/limits reference
            first = records[0]

            summaries.append(
                {
                    "monitoring_type": mtype,
                    "total_samples": len(records),
                    "samples_above_action_level": above_action,
                    "samples_above_pel": above_pel,
                    "average_result": round(avg_val, 2),
                    "max_result": round(max_val, 2),
                    "result_unit": first.get("result_unit", ""),
                    "action_level": first.get("action_level", 0),
                    "pel": first.get("pel", 0),
                }
            )

        return {"summaries": summaries, "total_samples": total_samples}

    # -- SWPPP Inspections -------------------------------------------------------------

    def create_swppp_inspection(
        self,
        company_id: str,
        project_id: str,
        data: SwpppInspectionCreate,
        user_id: str,
    ) -> SwpppInspection:
        """Create a SWPPP inspection record.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated SWPPP inspection data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created SwpppInspection.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        now = datetime.now(timezone.utc)
        insp_id = self._generate_swppp_id()

        insp_dict: dict[str, Any] = {
            "id": insp_id,
            "company_id": company_id,
            "project_id": project_id,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "inspection_type": data.inspection_type,
            "precipitation_last_24h": data.precipitation_last_24h,
            "bmp_items": data.bmp_items,
            "corrective_actions": data.corrective_actions,
            "overall_status": data.overall_status,
            "photo_urls": data.photo_urls,
            "created_at": now,
            "created_by": user_id,
        }

        self._swppp_collection(company_id, project_id).document(insp_id).set(insp_dict)
        return SwpppInspection(**insp_dict)

    def list_swppp_inspections(
        self,
        company_id: str,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List SWPPP inspections for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum inspections to return.
            offset: Number of inspections to skip.

        Returns:
            A dict with 'inspections' list and 'total' count.
        """
        all_docs = [
            SwpppInspection(**doc.to_dict())
            for doc in self._swppp_collection(company_id, project_id).stream()
        ]
        total = len(all_docs)

        all_docs.sort(key=lambda i: i.created_at, reverse=True)
        paginated = all_docs[offset : offset + limit]

        return {"inspections": paginated, "total": total}

    # -- Compliance Status -------------------------------------------------------------

    def get_compliance_status(self, company_id: str) -> dict:
        """Get overall environmental compliance status for a company.

        Checks program statuses, overdue reviews, and exposure exceedances
        across all projects.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with overall_status, areas, and summary counts.
        """
        # Get all programs
        programs_query = self._programs_collection(company_id).where(
            "deleted", "==", False
        )
        all_programs = [doc.to_dict() for doc in programs_query.stream()]

        total_programs = len(all_programs)
        active_programs = sum(1 for p in all_programs if p.get("status") == "active")
        today = date.today()

        overdue_reviews = 0
        for p in all_programs:
            review_due = p.get("next_review_due")
            if review_due:
                if isinstance(review_due, str):
                    review_due = date.fromisoformat(review_due)
                if review_due < today:
                    overdue_reviews += 1

        # Scan projects for exposure exceedances
        total_exceedances = 0
        projects_ref = self._company_ref(company_id).collection("projects")
        for proj_doc in projects_ref.stream():
            proj_id = proj_doc.id
            exposure_ref = self._exposure_collection(company_id, proj_id)
            for exp_doc in exposure_ref.stream():
                record = exp_doc.to_dict()
                if record.get("exceeds_pel", False):
                    total_exceedances += 1

        # Build area-level status
        areas = []
        program_types_found = set()
        for p in all_programs:
            ptype = p.get("program_type", "")
            program_types_found.add(ptype)

        for ptype_enum in EnvironmentalProgramType:
            ptype_programs = [
                p for p in all_programs if p.get("program_type") == ptype_enum.value
            ]
            ptype_overdue = 0
            for p in ptype_programs:
                review_due = p.get("next_review_due")
                if review_due:
                    if isinstance(review_due, str):
                        review_due = date.fromisoformat(review_due)
                    if review_due < today:
                        ptype_overdue += 1

            if ptype_programs:
                area_status = "compliant"
                if ptype_overdue > 0:
                    area_status = "needs_attention"

                areas.append(
                    {
                        "area": ptype_enum.value,
                        "status": area_status,
                        "details": f"{len(ptype_programs)} program(s), {ptype_overdue} overdue review(s)",
                        "programs_count": len(ptype_programs),
                        "overdue_reviews": ptype_overdue,
                        "exposure_exceedances": 0,
                    }
                )

        # Determine overall status
        overall = "compliant"
        if total_exceedances > 0:
            overall = "non_compliant"
        elif overdue_reviews > 0:
            overall = "needs_attention"

        return {
            "overall_status": overall,
            "areas": areas,
            "total_programs": total_programs,
            "active_programs": active_programs,
            "overdue_reviews": overdue_reviews,
            "total_exposure_exceedances": total_exceedances,
        }
