"""Environmental compliance service against Neo4j."""

import json
from datetime import date, datetime, timezone
from typing import Any

from app.exceptions import (
    CompanyNotFoundError,
    EnvironmentalProgramNotFoundError,
    ProjectNotFoundError,
)
from app.models.actor import Actor
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
from app.services.base_service import BaseService

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


class EnvironmentalService(BaseService):
    """Manages environmental compliance programs, exposure records, and SWPPP inspections.

    Graph model:
        (Company)-[:HAS_ENV_PROGRAM]->(EnvironmentalProgram)
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_EXPOSURE_RECORD]->(ExposureRecord)
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_SWPPP_INSPECTION]->(SwpppInspection)
    """

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.id AS id",
            {"id": company_id},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.id AS id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

    # -- Environmental Programs --------------------------------------------------------

    @staticmethod
    def _program_to_model(record: dict[str, Any]) -> EnvironmentalProgram:
        """Convert a Neo4j record to an EnvironmentalProgram model.

        Args:
            record: Dict with 'prog' and 'company_id' keys.

        Returns:
            An EnvironmentalProgram model instance.
        """
        data = dict(record["prog"])
        content_json = data.pop("_content_json", "{}")
        data["content"] = json.loads(content_json) if content_json else {}
        applicable_json = data.pop("_applicable_projects_json", "[]")
        data["applicable_projects"] = json.loads(applicable_json) if applicable_json else []
        data["company_id"] = record["company_id"]
        return EnvironmentalProgram(**data)

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

        actor = Actor.human(user_id)
        program_id = self._generate_id("envp")

        props: dict[str, Any] = {
            "id": program_id,
            "program_type": data.program_type.value,
            "title": data.title,
            "_content_json": json.dumps(data.content),
            "_applicable_projects_json": json.dumps(data.applicable_projects),
            "last_reviewed": None,
            "next_review_due": (
                data.next_review_due.isoformat() if data.next_review_due else None
            ),
            "status": "active",
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (p:EnvironmentalProgram $props)
            CREATE (c)-[:HAS_ENV_PROGRAM]->(p)
            RETURN p {.*} AS prog, c.id AS company_id
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        return self._program_to_model(result)

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
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram {id: $program_id})
            WHERE p.deleted = false
            RETURN p {.*} AS prog, c.id AS company_id
            """,
            {"company_id": company_id, "program_id": program_id},
        )
        if result is None:
            raise EnvironmentalProgramNotFoundError(program_id)
        return self._program_to_model(result)

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
        where_clauses = ["p.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if program_type is not None:
            where_clauses.append("p.program_type = $program_type")
            params["program_type"] = program_type.value

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram)
            WHERE {where_str}
            RETURN count(p) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram)
            WHERE {where_str}
            RETURN p {{.*}} AS prog, c.id AS company_id
            ORDER BY p.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        programs = [self._program_to_model(r) for r in results]
        return {"programs": programs, "total": total}

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
        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "next_review_due" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            elif field_name == "content" and value is not None:
                update_data["_content_json"] = json.dumps(value)
            elif field_name == "applicable_projects" and value is not None:
                update_data["_applicable_projects_json"] = json.dumps(value)
            else:
                update_data[field_name] = value

        if not update_data:
            return self.get_program(company_id, program_id)

        actor = Actor.human(user_id)
        update_data.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram {id: $program_id})
            WHERE p.deleted = false
            SET p += $props
            RETURN p {.*} AS prog, c.id AS company_id
            """,
            {"company_id": company_id, "program_id": program_id, "props": update_data},
        )
        if result is None:
            raise EnvironmentalProgramNotFoundError(program_id)
        return self._program_to_model(result)

    def delete_program(self, company_id: str, program_id: str) -> None:
        """Soft-delete an environmental program.

        Args:
            company_id: The owning company ID.
            program_id: The program ID to delete.

        Raises:
            EnvironmentalProgramNotFoundError: If not found or already deleted.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram {id: $program_id})
            WHERE p.deleted = false
            SET p.deleted = true, p.updated_at = $now
            RETURN p.id AS id
            """,
            {
                "company_id": company_id,
                "program_id": program_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise EnvironmentalProgramNotFoundError(program_id)

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

        actor = Actor.human(user_id)
        record_id = self._generate_id("expr")

        exceeds_action = data.result_value >= data.action_level
        exceeds_pel = data.result_value >= data.pel

        props: dict[str, Any] = {
            "id": record_id,
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
            "created_by": actor.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (r:ExposureRecord $props)
            CREATE (p)-[:HAS_EXPOSURE_RECORD]->(r)
            RETURN r {.*} AS rec, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        data_dict = dict(result["rec"])
        data_dict["company_id"] = result["company_id"]
        data_dict["project_id"] = result["project_id"]
        return ExposureMonitoringRecord(**data_dict)

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
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if monitoring_type is not None:
            where_clauses.append("r.monitoring_type = $monitoring_type")
            params["monitoring_type"] = monitoring_type

        if worker_id is not None:
            where_clauses.append("r.worker_id = $worker_id")
            params["worker_id"] = worker_id

        where_str = " AND ".join(where_clauses)
        where_clause = f"WHERE {where_str}" if where_str else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_EXPOSURE_RECORD]->(r:ExposureRecord)
            {where_clause}
            RETURN count(r) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_EXPOSURE_RECORD]->(r:ExposureRecord)
            {where_clause}
            RETURN r {{.*}} AS rec, c.id AS company_id, p.id AS project_id
            ORDER BY r.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        records = []
        for r in results:
            data_dict = dict(r["rec"])
            data_dict["company_id"] = r["company_id"]
            data_dict["project_id"] = r["project_id"]
            records.append(ExposureMonitoringRecord(**data_dict))

        return {"records": records, "total": total}

    def get_exposure_summary(self, company_id: str, project_id: str) -> dict:
        """Get a summary of exposure monitoring results by type for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            A dict with 'summaries' list and 'total_samples' count.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_EXPOSURE_RECORD]->(r:ExposureRecord)
            RETURN r.monitoring_type AS mtype,
                   r.result_value AS result_value,
                   r.exceeds_action_level AS exceeds_action,
                   r.exceeds_pel AS exceeds_pel,
                   r.result_unit AS result_unit,
                   r.action_level AS action_level,
                   r.pel AS pel
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        type_data: dict[str, list[dict]] = {}
        for r in results:
            mtype = r.get("mtype", "unknown")
            if mtype not in type_data:
                type_data[mtype] = []
            type_data[mtype].append(r)

        summaries = []
        total_samples = 0

        for mtype, records in type_data.items():
            values = [r.get("result_value", 0) for r in records]
            above_action = sum(1 for r in records if r.get("exceeds_action", False))
            above_pel = sum(1 for r in records if r.get("exceeds_pel", False))
            avg_val = sum(values) / len(values) if values else 0.0
            max_val = max(values) if values else 0.0
            total_samples += len(records)

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

        actor = Actor.human(user_id)
        insp_id = self._generate_id("swpp")

        props: dict[str, Any] = {
            "id": insp_id,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "inspection_type": data.inspection_type,
            "precipitation_last_24h": data.precipitation_last_24h,
            "_bmp_items_json": json.dumps(data.bmp_items),
            "corrective_actions": data.corrective_actions,
            "overall_status": data.overall_status,
            "_photo_urls_json": json.dumps(data.photo_urls),
            "created_by": actor.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (s:SwpppInspection $props)
            CREATE (p)-[:HAS_SWPPP_INSPECTION]->(s)
            RETURN s {.*} AS insp, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        return self._swppp_to_model(result)

    @staticmethod
    def _swppp_to_model(record: dict[str, Any]) -> SwpppInspection:
        """Convert a Neo4j record to a SwpppInspection model.

        Args:
            record: Dict with 'insp', 'company_id', and 'project_id' keys.

        Returns:
            A SwpppInspection model instance.
        """
        data = dict(record["insp"])
        bmp_json = data.pop("_bmp_items_json", "[]")
        data["bmp_items"] = json.loads(bmp_json) if bmp_json else []
        photo_json = data.pop("_photo_urls_json", "[]")
        data["photo_urls"] = json.loads(photo_json) if photo_json else []
        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return SwpppInspection(**data)

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
        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_SWPPP_INSPECTION]->(s:SwpppInspection)
            RETURN count(s) AS total
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_SWPPP_INSPECTION]->(s:SwpppInspection)
            RETURN s {.*} AS insp, c.id AS company_id, p.id AS project_id
            ORDER BY s.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            {"company_id": company_id, "project_id": project_id, "limit": limit, "offset": offset},
        )

        inspections = [self._swppp_to_model(r) for r in results]
        return {"inspections": inspections, "total": total}

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
        prog_results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ENV_PROGRAM]->(p:EnvironmentalProgram)
            WHERE p.deleted = false
            RETURN p.program_type AS program_type, p.status AS status,
                   p.next_review_due AS next_review_due
            """,
            {"company_id": company_id},
        )

        total_programs = len(prog_results)
        active_programs = sum(1 for p in prog_results if p.get("status") == "active")
        today = date.today()

        overdue_reviews = 0
        for p in prog_results:
            review_due = p.get("next_review_due")
            if review_due:
                if isinstance(review_due, str):
                    review_due = date.fromisoformat(review_due)
                if review_due < today:
                    overdue_reviews += 1

        # Count exposure exceedances across all projects
        exc_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(proj:Project)
                  -[:HAS_EXPOSURE_RECORD]->(r:ExposureRecord)
            WHERE r.exceeds_pel = true
            RETURN count(r) AS total_exceedances
            """,
            {"company_id": company_id},
        )
        total_exceedances = exc_result["total_exceedances"] if exc_result else 0

        # Build area-level status
        areas = []
        for ptype_enum in EnvironmentalProgramType:
            ptype_programs = [
                p for p in prog_results if p.get("program_type") == ptype_enum.value
            ]
            if not ptype_programs:
                continue

            ptype_overdue = 0
            for p in ptype_programs:
                review_due = p.get("next_review_due")
                if review_due:
                    if isinstance(review_due, str):
                        review_due = date.fromisoformat(review_due)
                    if review_due < today:
                        ptype_overdue += 1

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
