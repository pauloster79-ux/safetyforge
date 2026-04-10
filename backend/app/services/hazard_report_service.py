"""Hazard report CRUD service against Neo4j."""

import json
from datetime import datetime, timezone
from typing import Any

from app.exceptions import HazardReportNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.hazard_report import (
    HazardReport,
    HazardReportCreate,
    HazardReportStatusUpdate,
    HazardSeverity,
    HazardStatus,
    IdentifiedHazard,
    SEVERITY_RANK,
)
from app.services.base_service import BaseService
from app.services.hazard_analysis_service import HazardAnalysisService


class HazardReportService(BaseService):
    """Manages photo-based hazard reports in Neo4j.

    Graph model:
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_HAZARD_REPORT]->(HazardReport)
        AI analysis and identified hazards stored as JSON strings.

    Args:
        driver: Neo4j driver instance.
        analysis_service: HazardAnalysisService for AI photo analysis.
    """

    def __init__(self, driver: Any, analysis_service: HazardAnalysisService) -> None:
        super().__init__(driver)
        self.analysis_service = analysis_service

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

    @staticmethod
    def _strip_data_uri_prefix(photo_base64: str) -> str:
        """Strip data URI prefix if present (e.g. 'data:image/jpeg;base64,').

        Args:
            photo_base64: Raw base64 string, possibly with data URI prefix.

        Returns:
            Clean base64 string without prefix.
        """
        if photo_base64.startswith("data:"):
            comma_idx = photo_base64.index(",")
            return photo_base64[comma_idx + 1:]
        return photo_base64

    @staticmethod
    def _parse_hazards(ai_analysis: dict) -> list[IdentifiedHazard]:
        """Parse identified hazards from AI analysis result.

        Args:
            ai_analysis: The raw AI analysis dict.

        Returns:
            List of validated IdentifiedHazard models.
        """
        raw_hazards = ai_analysis.get("identified_hazards", [])
        hazards: list[IdentifiedHazard] = []

        for i, raw in enumerate(raw_hazards):
            severity_str = raw.get("severity", "low").lower().replace(" ", "_")
            try:
                severity = HazardSeverity(severity_str)
            except ValueError:
                severity = HazardSeverity.LOW

            hazards.append(
                IdentifiedHazard(
                    hazard_id=raw.get("hazard_id", f"h_{i + 1}"),
                    description=raw.get("description", ""),
                    severity=severity,
                    osha_standard=raw.get("osha_standard", ""),
                    category=raw.get("category", "Other"),
                    recommended_action=raw.get("recommended_action", ""),
                    location_in_image=raw.get("location_in_image", ""),
                )
            )

        return hazards

    @staticmethod
    def _highest_severity(
        hazards: list[IdentifiedHazard],
    ) -> HazardSeverity | None:
        """Determine the highest severity among identified hazards.

        Args:
            hazards: List of identified hazards.

        Returns:
            The highest severity value, or None if no hazards.
        """
        if not hazards:
            return None
        return max(hazards, key=lambda h: SEVERITY_RANK.get(h.severity, 0)).severity

    @staticmethod
    def _to_model(record: dict[str, Any]) -> HazardReport:
        """Convert a Neo4j record dict to a HazardReport model.

        Args:
            record: Dict with 'report', 'company_id', 'project_id' keys.

        Returns:
            A HazardReport model instance.
        """
        data = record["report"]
        ai_json = data.pop("_ai_analysis_json", "{}")
        data["ai_analysis"] = json.loads(ai_json) if ai_json else {}
        hazards_json = data.pop("_identified_hazards_json", "[]")
        data["identified_hazards"] = json.loads(hazards_json) if hazards_json else []
        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return HazardReport(**data)

    def create_from_photo(
        self,
        company_id: str,
        project_id: str,
        data: HazardReportCreate,
        user_id: str,
    ) -> HazardReport:
        """Create a hazard report by analyzing a photo with AI.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated creation data including photo.
            user_id: UID of the creating user.

        Returns:
            The created HazardReport with AI analysis results.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            GenerationError: If AI analysis fails.
        """
        self._verify_project_exists(company_id, project_id)

        clean_base64 = self._strip_data_uri_prefix(data.photo_base64)

        context = {
            "description": data.description,
            "location": data.location,
        }
        ai_analysis = self.analysis_service.analyze_photo(
            image_base64=clean_base64,
            image_media_type=data.media_type,
            context=context,
        )

        hazards = self._parse_hazards(ai_analysis)
        highest = self._highest_severity(hazards)

        actor = Actor.human(user_id)
        report_id = self._generate_id("hzrd")
        photo_url = f"data:{data.media_type};base64,{clean_base64[:50]}..."

        props: dict[str, Any] = {
            "id": report_id,
            "photo_url": photo_url,
            "description": data.description,
            "location": data.location,
            "gps_latitude": data.gps_latitude,
            "gps_longitude": data.gps_longitude,
            "_ai_analysis_json": json.dumps(ai_analysis),
            "_identified_hazards_json": json.dumps([h.model_dump() for h in hazards]),
            "hazard_count": len(hazards),
            "highest_severity": highest.value if highest else None,
            "status": HazardStatus.OPEN.value,
            "corrective_action_taken": "",
            "corrected_at": None,
            "corrected_by": "",
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (r:HazardReport $props)
            CREATE (p)-[:HAS_HAZARD_REPORT]->(r)
            RETURN r {.*} AS report, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        return self._to_model(result)

    def get(
        self, company_id: str, project_id: str, report_id: str
    ) -> HazardReport:
        """Fetch a single hazard report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID to fetch.

        Returns:
            The HazardReport model.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_HAZARD_REPORT]->(r:HazardReport {id: $report_id})
            RETURN r {.*} AS report, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "report_id": report_id,
            },
        )
        if result is None:
            raise HazardReportNotFoundError(report_id)
        return self._to_model(result)

    def list_reports(
        self,
        company_id: str,
        project_id: str,
        report_status: HazardStatus | None = None,
        severity: HazardSeverity | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List hazard reports for a project with optional filters.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_status: Optional status filter.
            severity: Optional highest_severity filter.
            limit: Maximum number of reports to return.
            offset: Number of reports to skip.

        Returns:
            Dict with 'reports' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if report_status is not None:
            where_clauses.append("r.status = $report_status")
            params["report_status"] = report_status.value

        if severity is not None:
            where_clauses.append("r.highest_severity = $severity")
            params["severity"] = severity.value

        where_str = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_HAZARD_REPORT]->(r:HazardReport)
            {("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""}
            RETURN count(r) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_HAZARD_REPORT]->(r:HazardReport)
            {("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""}
            RETURN r {{.*}} AS report, c.id AS company_id, p.id AS project_id
            ORDER BY r.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        reports = [self._to_model(r) for r in results]
        return {"reports": reports, "total": total}

    def update_status(
        self,
        company_id: str,
        project_id: str,
        report_id: str,
        data: HazardReportStatusUpdate,
        user_id: str,
    ) -> HazardReport:
        """Update the status and corrective action of a hazard report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID.
            data: Status update data.
            user_id: UID of the updating user.

        Returns:
            The updated HazardReport.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        actor = Actor.human(user_id)
        now = datetime.now(timezone.utc).isoformat()

        update_props: dict[str, Any] = {
            "status": data.status.value,
            "corrective_action_taken": data.corrective_action_taken,
            **self._provenance_update(actor),
        }

        if data.status in (HazardStatus.CORRECTED, HazardStatus.CLOSED):
            update_props["corrected_at"] = now
            update_props["corrected_by"] = user_id

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_HAZARD_REPORT]->(r:HazardReport {id: $report_id})
            SET r += $props
            RETURN r {.*} AS report, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "report_id": report_id,
                "props": update_props,
            },
        )
        if result is None:
            raise HazardReportNotFoundError(report_id)
        return self._to_model(result)

    def delete(
        self, company_id: str, project_id: str, report_id: str
    ) -> None:
        """Delete a hazard report (DETACH DELETE).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID to delete.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_HAZARD_REPORT]->(r:HazardReport {id: $report_id})
            WITH r, r.id AS deleted_id
            DETACH DELETE r
            RETURN deleted_id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "report_id": report_id,
            },
        )
        if result is None:
            raise HazardReportNotFoundError(report_id)
