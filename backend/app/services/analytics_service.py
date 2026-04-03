"""Safety analytics and EMR estimation service."""

from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.models.analytics import EmrEstimate, SafetyDashboardMetrics
from app.services.inspection_service import InspectionService
from app.services.osha_log_service import OshaLogService
from app.services.project_service import ProjectService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService


class AnalyticsService:
    """Aggregates safety data across services for dashboard analytics.

    Args:
        db: Firestore client instance.
        project_service: ProjectService for project queries.
        inspection_service: InspectionService for inspection queries.
        toolbox_talk_service: ToolboxTalkService for talk queries.
        worker_service: WorkerService for worker/cert queries.
        osha_log_service: OshaLogService for OSHA metrics.
    """

    def __init__(
        self,
        db: firestore.Client,
        project_service: ProjectService,
        inspection_service: InspectionService,
        toolbox_talk_service: ToolboxTalkService,
        worker_service: WorkerService,
        osha_log_service: OshaLogService,
    ) -> None:
        self.db = db
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

            # Compliance score per active project
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

        # -- Hazard report metrics --
        total_hazard_reports = 0
        open_hazard_reports = 0

        for project in all_projects:
            hazard_ref = (
                self.db.collection("companies")
                .document(company_id)
                .collection("projects")
                .document(project.id)
                .collection("hazard_reports")
            )
            for doc in hazard_ref.stream():
                data = doc.to_dict()
                if data.get("deleted", False):
                    continue
                total_hazard_reports += 1
                if data.get("status") in ("open", "in_progress"):
                    open_hazard_reports += 1

        # -- Incident metrics --
        total_incidents = 0
        incidents_this_month = 0

        for project in all_projects:
            inc_ref = (
                self.db.collection("companies")
                .document(company_id)
                .collection("projects")
                .document(project.id)
                .collection("incidents")
            )
            for doc in inc_ref.stream():
                data = doc.to_dict()
                total_incidents += 1
                created = data.get("created_at")
                if isinstance(created, datetime):
                    if created.year == current_year and created.month == current_month:
                        incidents_this_month += 1

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

        # -- Mock inspection metrics --
        last_mock_score = None
        last_mock_grade = None
        last_mock_date = None

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
        if mock_docs:
            mock_data = mock_docs[0].to_dict()
            last_mock_score = mock_data.get("overall_score")
            last_mock_grade = mock_data.get("overall_grade")
            created = mock_data.get("created_at")
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

        The EMR projection is simplified for MVP: if current TRIR is below
        industry average (~3.0), the projected EMR decreases; if above, it
        increases.

        Args:
            current_emr: The company's current EMR value.
            annual_payroll: Annual payroll in dollars.
            workers_comp_rate: Workers comp rate per $100 of payroll.
            trir: Current year TRIR for projection.

        Returns:
            An EmrEstimate with financial projections.
        """
        # Calculate base premium
        premium_base = annual_payroll * (workers_comp_rate / 100)
        current_premium = premium_base * current_emr

        # Project EMR based on TRIR trend
        # Industry average TRIR is approximately 3.0
        industry_avg_trir = 3.0
        if trir <= 0:
            # No incidents — trending toward lower EMR
            projected_emr = max(current_emr * 0.90, 0.60)
        elif trir < industry_avg_trir:
            # Below average — EMR should decrease
            ratio = trir / industry_avg_trir
            projected_emr = max(current_emr * (0.90 + 0.10 * ratio), 0.60)
        else:
            # Above average — EMR may increase
            ratio = min(trir / industry_avg_trir, 2.0)
            projected_emr = min(current_emr * (0.90 + 0.10 * ratio), 2.0)

        projected_emr = round(projected_emr, 3)
        projected_premium = premium_base * projected_emr
        potential_savings = current_premium - projected_premium

        # Generate recommendations
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
