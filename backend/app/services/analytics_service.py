"""Safety analytics and EMR estimation service."""

from datetime import datetime, timezone
from typing import Any

from app.models.analytics import EmrEstimate, SafetyDashboardMetrics
from app.services.base_service import BaseService
from app.services.inspection_service import InspectionService
from app.services.osha_log_service import OshaLogService
from app.services.project_service import ProjectService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService


class AnalyticsService(BaseService):
    """Aggregates safety data across services for dashboard analytics.

    Args:
        driver: Neo4j driver instance.
        project_service: ProjectService for project queries.
        inspection_service: InspectionService for inspection queries.
        toolbox_talk_service: ToolboxTalkService for talk queries.
        worker_service: WorkerService for worker/cert queries.
        osha_log_service: OshaLogService for OSHA metrics.
    """

    def __init__(
        self,
        driver: Any,
        project_service: ProjectService,
        inspection_service: InspectionService,
        toolbox_talk_service: ToolboxTalkService,
        worker_service: WorkerService,
        osha_log_service: OshaLogService,
    ) -> None:
        super().__init__(driver)
        self.project_service = project_service
        self.inspection_service = inspection_service
        self.toolbox_talk_service = toolbox_talk_service
        self.worker_service = worker_service
        self.osha_log_service = osha_log_service

    def get_dashboard_metrics(self, company_id: str) -> SafetyDashboardMetrics:
        """Aggregate safety metrics across all company data.

        Args:
            company_id: The company ID to aggregate metrics for.

        Returns:
            A SafetyDashboardMetrics with all fields populated.
        """
        now = datetime.now(timezone.utc)
        current_year = now.year
        current_month = now.month

        # -- Project metrics --
        project_data = self.project_service.list_projects(
            company_id=company_id, limit=500
        )
        all_projects = project_data.get("projects", [])
        total_projects = project_data.get("total", 0)
        active_projects = sum(
            1 for p in all_projects if p.status.value == "active"
        )

        # -- Inspection metrics --
        total_inspections = 0
        inspections_this_month = 0
        compliance_scores: list[int] = []

        for project in all_projects:
            insp_data = self.inspection_service.list_inspections(
                company_id=company_id,
                project_id=project.id,
                limit=500,
            )
            inspections = insp_data.get("inspections", [])
            total_inspections += len(inspections)

            for insp in inspections:
                created = insp.created_at
                if isinstance(created, datetime):
                    if created.year == current_year and created.month == current_month:
                        inspections_this_month += 1

            if project.status.value == "active":
                score = self.project_service.get_compliance_score(
                    company_id, project.id
                )
                compliance_scores.append(score)

        avg_compliance = (
            sum(compliance_scores) / len(compliance_scores)
            if compliance_scores
            else 0.0
        )

        # -- Toolbox talk metrics --
        total_talks = 0
        talks_this_month = 0

        for project in all_projects:
            talk_data = self.toolbox_talk_service.list_talks(
                company_id=company_id,
                project_id=project.id,
                limit=500,
            )
            talks = talk_data.get("toolbox_talks", [])
            total_talks += len(talks)

            for talk in talks:
                created = talk.created_at
                if isinstance(created, datetime):
                    if created.year == current_year and created.month == current_month:
                        talks_this_month += 1

        # -- Worker and certification metrics --
        worker_data = self.worker_service.list_workers(
            company_id=company_id, limit=500
        )
        total_workers = worker_data.get("total", 0)

        workers_with_expired = 0
        workers_with_expiring = 0
        for worker in worker_data.get("workers", []):
            if worker.expired > 0:
                workers_with_expired += 1
            if worker.expiring_soon > 0:
                workers_with_expiring += 1

        # -- Hazard report metrics (Neo4j) --
        hazard_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_HAZARD_REPORT]->(h:HazardReport)
            WHERE h.deleted = false
            RETURN count(h) AS total,
                   sum(CASE WHEN h.status IN ['open', 'in_progress'] THEN 1 ELSE 0 END) AS open_count
            """,
            {"company_id": company_id},
        )
        total_hazard_reports = hazard_result["total"] if hazard_result else 0
        open_hazard_reports = hazard_result["open_count"] if hazard_result else 0

        # -- Incident metrics (Neo4j) --
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        incident_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_INCIDENT]->(i:Incident)
            RETURN count(i) AS total,
                   sum(CASE WHEN i.created_at >= $month_start THEN 1 ELSE 0 END) AS this_month
            """,
            {"company_id": company_id, "month_start": month_start},
        )
        total_incidents = incident_result["total"] if incident_result else 0
        incidents_this_month = incident_result["this_month"] if incident_result else 0

        # -- OSHA metrics --
        try:
            osha_summary = self.osha_log_service.get_300a_summary(
                company_id, current_year
            )
            trir = osha_summary.trir
            dart = osha_summary.dart
        except Exception:
            trir = 0.0
            dart = 0.0

        # -- Mock inspection metrics (Neo4j) --
        last_mock_score = None
        last_mock_grade = None
        last_mock_date = None

        mock_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_MOCK_INSPECTION]->(r:Inspection)
            WHERE r.category = 'simulated'
            RETURN r.overall_score AS score, r.grade AS grade, r.created_at AS created_at
            ORDER BY r.created_at DESC
            LIMIT 1
            """,
            {"company_id": company_id},
        )
        if mock_result:
            last_mock_score = mock_result.get("score")
            last_mock_grade = mock_result.get("grade")
            created = mock_result.get("created_at")
            if isinstance(created, datetime):
                last_mock_date = created.isoformat()
            elif isinstance(created, str):
                last_mock_date = created

        return SafetyDashboardMetrics(
            total_projects=total_projects,
            active_projects=active_projects,
            total_inspections=total_inspections,
            inspections_this_month=inspections_this_month,
            total_toolbox_talks=total_talks,
            talks_this_month=talks_this_month,
            total_hazard_reports=total_hazard_reports,
            open_hazard_reports=open_hazard_reports,
            total_incidents=total_incidents,
            incidents_this_month=incidents_this_month,
            avg_compliance_score=round(avg_compliance, 1),
            total_workers=total_workers,
            workers_with_expired_certs=workers_with_expired,
            workers_with_expiring_certs=workers_with_expiring,
            trir=trir,
            dart=dart,
            last_mock_score=last_mock_score,
            last_mock_grade=last_mock_grade,
            last_mock_date=last_mock_date,
            current_emr=1.0,
            projected_emr=1.0,
            emr_premium_impact=0.0,
        )

    @staticmethod
    def get_emr_estimate(
        current_emr: float,
        annual_payroll: float,
        workers_comp_rate: float,
        trir: float = 0.0,
    ) -> EmrEstimate:
        """Calculate EMR impact and projected savings.

        Args:
            current_emr: The company's current EMR value.
            annual_payroll: Annual payroll in dollars.
            workers_comp_rate: Workers comp rate per $100 of payroll.
            trir: Current year TRIR for projection.

        Returns:
            An EmrEstimate with financial projections.
        """
        premium_base = annual_payroll * (workers_comp_rate / 100)
        current_premium = premium_base * current_emr

        industry_avg_trir = 3.0
        if trir <= 0:
            projected_emr = max(current_emr * 0.90, 0.60)
        elif trir < industry_avg_trir:
            ratio = trir / industry_avg_trir
            projected_emr = max(current_emr * (0.90 + 0.10 * ratio), 0.60)
        else:
            ratio = min(trir / industry_avg_trir, 2.0)
            projected_emr = min(current_emr * (0.90 + 0.10 * ratio), 2.0)

        projected_emr = round(projected_emr, 3)
        projected_premium = premium_base * projected_emr
        potential_savings = current_premium - projected_premium

        recommendations: list[str] = []

        if trir > industry_avg_trir:
            recommendations.append(
                "Your TRIR is above industry average. Focus on hazard identification "
                "and elimination to reduce recordable incidents."
            )
        if trir > 0:
            recommendations.append(
                "Implement a near-miss reporting program to identify hazards before "
                "they cause recordable incidents."
            )
        if current_emr > 1.0:
            recommendations.append(
                "Your EMR is above 1.0, indicating higher-than-average losses. "
                "Invest in safety training and return-to-work programs."
            )
        recommendations.append(
            "Maintain consistent daily inspections and weekly toolbox talks "
            "to demonstrate a proactive safety culture."
        )
        recommendations.append(
            "Ensure all workers have current certifications. Expired certifications "
            "increase liability and potential OSHA citations."
        )

        return EmrEstimate(
            current_emr=current_emr,
            projected_emr=projected_emr,
            premium_base=round(premium_base, 2),
            current_premium=round(current_premium, 2),
            projected_premium=round(projected_premium, 2),
            potential_savings=round(potential_savings, 2),
            recommendations=recommendations,
        )
