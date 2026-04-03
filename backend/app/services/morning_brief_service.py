"""Morning safety brief service that aggregates data from multiple sources."""

import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import MorningBriefNotFoundError, ProjectNotFoundError
from app.models.morning_brief import BriefAlert, MorningBrief, RiskLevel
from app.services.inspection_service import InspectionService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService


# Default mock weather for MVP
_DEFAULT_WEATHER: dict[str, Any] = {
    "temperature": 78,
    "condition": "Partly Cloudy",
    "wind_speed": 8,
    "humidity": 55,
    "precipitation_chance": 10,
    "alerts": [],
}

# Topic recommendations keyed by alert type
_TOPIC_RECOMMENDATIONS: dict[str, str] = {
    "weather_heat": "Heat Illness Prevention",
    "weather_wind": "Wind Safety and Secure Materials",
    "certification_expired": "Fall Protection Refresher",
    "certification_expiring": "Training and Certification Awareness",
    "inspection_overdue": "Daily Inspection Best Practices",
    "toolbox_talk_overdue": "Safety Communication and Toolbox Talks",
}


class MorningBriefService:
    """Assembles morning safety briefs from multiple data sources.

    Args:
        db: Firestore client instance.
        worker_service: WorkerService for certification queries.
        inspection_service: InspectionService for recent inspection queries.
        toolbox_talk_service: ToolboxTalkService for recent talk queries.
    """

    def __init__(
        self,
        db: firestore.Client,
        worker_service: WorkerService,
        inspection_service: InspectionService,
        toolbox_talk_service: ToolboxTalkService,
    ) -> None:
        self.db = db
        self.worker_service = worker_service
        self.inspection_service = inspection_service
        self.toolbox_talk_service = toolbox_talk_service

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

    def _collection(
        self, company_id: str, project_id: str
    ) -> firestore.CollectionReference:
        """Return the morning_briefs subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("morning_briefs")

    def _generate_id(self) -> str:
        """Generate a unique morning brief ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"brief_{secrets.token_hex(8)}"

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

    def _get_certification_alerts(self, company_id: str) -> list[BriefAlert]:
        """Build alerts for expiring and expired certifications.

        Args:
            company_id: The company ID.

        Returns:
            List of BriefAlert objects for certification issues.
        """
        alerts: list[BriefAlert] = []
        cert_data = self.worker_service.get_expiring_certifications(
            company_id, days_ahead=14
        )
        expired_count = 0
        expiring_count = 0

        for item in cert_data.get("certifications", []):
            cert = item.get("certification", {})
            cert_status = cert.get("status", "")
            if cert_status == "expired":
                expired_count += 1
            elif cert_status == "expiring_soon":
                expiring_count += 1

        if expired_count > 0:
            alerts.append(
                BriefAlert(
                    alert_type="certification",
                    severity="critical",
                    title=f"{expired_count} Expired Certification(s)",
                    description=(
                        f"{expired_count} worker certification(s) have expired. "
                        "Workers may not perform tasks requiring these certifications."
                    ),
                    action_url="/workers?filter=expired",
                    action_label="View Expired Certs",
                )
            )

        if expiring_count > 0:
            alerts.append(
                BriefAlert(
                    alert_type="certification",
                    severity="warning",
                    title=f"{expiring_count} Certification(s) Expiring Soon",
                    description=(
                        f"{expiring_count} worker certification(s) expire within 14 days. "
                        "Schedule renewals to maintain compliance."
                    ),
                    action_url="/workers?filter=expiring",
                    action_label="View Expiring Certs",
                )
            )

        return alerts

    def _get_inspection_alerts(
        self, company_id: str, project_id: str
    ) -> list[BriefAlert]:
        """Check if a recent inspection exists for the project.

        Args:
            company_id: The company ID.
            project_id: The project ID.

        Returns:
            List of BriefAlert objects for missing inspections.
        """
        alerts: list[BriefAlert] = []
        today = date.today()
        two_days_ago = today - timedelta(days=2)

        result = self.inspection_service.list_inspections(
            company_id=company_id,
            project_id=project_id,
            date_from=two_days_ago,
            limit=1,
        )

        if result.get("total", 0) == 0:
            alerts.append(
                BriefAlert(
                    alert_type="inspection",
                    severity="warning",
                    title="No Recent Inspection",
                    description=(
                        "No daily inspection has been completed in the last 2 days. "
                        "OSHA requires regular site inspections."
                    ),
                    action_url=f"/projects/{project_id}/inspections/new",
                    action_label="Start Inspection",
                )
            )

        return alerts

    def _get_toolbox_talk_alerts(
        self, company_id: str, project_id: str
    ) -> list[BriefAlert]:
        """Check if a recent toolbox talk exists for the project.

        Args:
            company_id: The company ID.
            project_id: The project ID.

        Returns:
            List of BriefAlert objects for missing toolbox talks.
        """
        alerts: list[BriefAlert] = []

        # Check for talks in the last 7 days
        result = self.toolbox_talk_service.list_talks(
            company_id=company_id,
            project_id=project_id,
            limit=50,
        )

        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        has_recent_talk = False

        for talk in result.get("toolbox_talks", []):
            scheduled = talk.scheduled_date
            if isinstance(scheduled, str):
                scheduled = date.fromisoformat(scheduled)
            if scheduled >= seven_days_ago:
                has_recent_talk = True
                break

        if not has_recent_talk:
            alerts.append(
                BriefAlert(
                    alert_type="toolbox_talk",
                    severity="info",
                    title="Toolbox Talk Overdue",
                    description=(
                        "No toolbox talk has been conducted in the last 7 days. "
                        "Weekly safety talks are recommended for compliance."
                    ),
                    action_url=f"/projects/{project_id}/toolbox-talks/new",
                    action_label="Schedule Talk",
                )
            )

        return alerts

    def _get_weather_alerts(self, weather: dict[str, Any]) -> list[BriefAlert]:
        """Build alerts based on weather conditions.

        Args:
            weather: Weather data dict.

        Returns:
            List of BriefAlert objects for weather hazards.
        """
        alerts: list[BriefAlert] = []
        temp = weather.get("temperature", 0)
        wind = weather.get("wind_speed", 0)

        if temp > 95:
            alerts.append(
                BriefAlert(
                    alert_type="weather",
                    severity="critical",
                    title="Extreme Heat Warning",
                    description=(
                        f"Temperature is {temp}°F. Implement heat illness prevention: "
                        "mandatory water breaks every 20 minutes, shade access, "
                        "and buddy system per OSHA heat standards."
                    ),
                )
            )

        if wind > 20:
            alerts.append(
                BriefAlert(
                    alert_type="weather",
                    severity="warning",
                    title="High Wind Advisory",
                    description=(
                        f"Wind speed is {wind} mph. Secure loose materials, "
                        "suspend crane operations if gusts exceed 25 mph, "
                        "and monitor conditions for escalation."
                    ),
                )
            )

        return alerts

    @staticmethod
    def _calculate_risk_score(
        weather: dict[str, Any],
        cert_alerts: list[BriefAlert],
        inspection_alerts: list[BriefAlert],
        toolbox_alerts: list[BriefAlert],
    ) -> float:
        """Calculate a risk score (0-10) based on aggregated data.

        Args:
            weather: Weather data dict.
            cert_alerts: Certification-related alerts.
            inspection_alerts: Inspection-related alerts.
            toolbox_alerts: Toolbox talk-related alerts.

        Returns:
            A float risk score capped at 10.
        """
        score = 3.0  # Base score

        # Weather factors
        temp = weather.get("temperature", 0)
        wind = weather.get("wind_speed", 0)
        if temp > 95:
            score += 2.0
        if wind > 20:
            score += 1.0

        # Certification factors
        has_expired = any(
            a.severity == "critical" and a.alert_type == "certification"
            for a in cert_alerts
        )
        has_expiring = any(
            a.severity == "warning" and a.alert_type == "certification"
            for a in cert_alerts
        )
        if has_expired:
            score += 2.0
        if has_expiring:
            score += 1.0

        # Inspection factor
        if inspection_alerts:
            score += 1.5

        # Toolbox talk factor
        if toolbox_alerts:
            score += 0.5

        return min(score, 10.0)

    @staticmethod
    def _determine_risk_level(score: float) -> RiskLevel:
        """Determine risk level from numeric score.

        Args:
            score: Risk score from 0 to 10.

        Returns:
            The corresponding RiskLevel enum value.
        """
        if score <= 2:
            return RiskLevel.LOW
        if score <= 4:
            return RiskLevel.MODERATE
        if score <= 6:
            return RiskLevel.ELEVATED
        if score <= 8:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @staticmethod
    def _recommend_topic(
        weather_alerts: list[BriefAlert],
        cert_alerts: list[BriefAlert],
        inspection_alerts: list[BriefAlert],
        toolbox_alerts: list[BriefAlert],
    ) -> str:
        """Recommend a toolbox talk topic based on highest-priority alert.

        Args:
            weather_alerts: Weather-related alerts.
            cert_alerts: Certification-related alerts.
            inspection_alerts: Inspection-related alerts.
            toolbox_alerts: Toolbox talk-related alerts.

        Returns:
            A recommended topic string.
        """
        # Priority order: weather heat > expired certs > inspection > wind > expiring > toolbox
        for alert in weather_alerts:
            if "Heat" in alert.title:
                return _TOPIC_RECOMMENDATIONS["weather_heat"]

        for alert in cert_alerts:
            if alert.severity == "critical":
                return _TOPIC_RECOMMENDATIONS["certification_expired"]

        if inspection_alerts:
            return _TOPIC_RECOMMENDATIONS["inspection_overdue"]

        for alert in weather_alerts:
            if "Wind" in alert.title:
                return _TOPIC_RECOMMENDATIONS["weather_wind"]

        for alert in cert_alerts:
            if alert.severity == "warning":
                return _TOPIC_RECOMMENDATIONS["certification_expiring"]

        if toolbox_alerts:
            return _TOPIC_RECOMMENDATIONS["toolbox_talk_overdue"]

        return "General Site Safety Awareness"

    @staticmethod
    def _generate_summary(
        risk_level: RiskLevel,
        risk_score: float,
        alerts: list[BriefAlert],
        weather: dict[str, Any],
    ) -> str:
        """Generate a brief narrative summary for the morning brief.

        Args:
            risk_level: The calculated risk level.
            risk_score: The numeric risk score.
            alerts: All collected alerts.
            weather: Weather data.

        Returns:
            A summary string.
        """
        temp = weather.get("temperature", 0)
        condition = weather.get("condition", "Unknown")
        alert_count = len(alerts)
        critical_count = sum(1 for a in alerts if a.severity == "critical")

        parts = [
            f"Today's site risk level is {risk_level.value.upper()} "
            f"(score: {risk_score:.1f}/10).",
            f"Weather: {condition}, {temp}°F.",
        ]

        if alert_count == 0:
            parts.append("No active safety alerts. Maintain standard protocols.")
        elif critical_count > 0:
            parts.append(
                f"{alert_count} alert(s) identified, including "
                f"{critical_count} critical item(s) requiring immediate attention."
            )
        else:
            parts.append(
                f"{alert_count} advisory alert(s) identified. "
                "Review and address during morning briefing."
            )

        return " ".join(parts)

    def generate_brief(
        self,
        company_id: str,
        project_id: str,
        weather_override: dict[str, Any] | None = None,
    ) -> MorningBrief:
        """Assemble and persist a morning safety brief.

        Aggregates weather, certification, inspection, and toolbox talk data
        to produce a risk-scored brief with actionable alerts.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            weather_override: Optional weather data to override defaults.

        Returns:
            The generated MorningBrief.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        weather = weather_override if weather_override is not None else dict(_DEFAULT_WEATHER)

        # Collect alerts from all sources
        weather_alerts = self._get_weather_alerts(weather)
        cert_alerts = self._get_certification_alerts(company_id)
        inspection_alerts = self._get_inspection_alerts(company_id, project_id)
        toolbox_alerts = self._get_toolbox_talk_alerts(company_id, project_id)

        all_alerts = weather_alerts + cert_alerts + inspection_alerts + toolbox_alerts

        # Calculate risk
        risk_score = self._calculate_risk_score(
            weather, cert_alerts, inspection_alerts, toolbox_alerts
        )
        risk_level = self._determine_risk_level(risk_score)

        # Recommend topic
        topic = self._recommend_topic(
            weather_alerts, cert_alerts, inspection_alerts, toolbox_alerts
        )

        # Generate summary
        summary = self._generate_summary(risk_level, risk_score, all_alerts, weather)

        now = datetime.now(timezone.utc)
        brief_id = self._generate_id()
        today = date.today()

        brief_dict: dict[str, Any] = {
            "id": brief_id,
            "company_id": company_id,
            "project_id": project_id,
            "date": today.isoformat(),
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level.value,
            "weather": weather,
            "alerts": [a.model_dump() for a in all_alerts],
            "recommended_toolbox_talk_topic": topic,
            "summary": summary,
            "created_at": now,
        }

        self._collection(company_id, project_id).document(brief_id).set(brief_dict)
        return MorningBrief(**brief_dict)

    def get_brief(self, company_id: str, project_id: str, brief_id: str) -> MorningBrief:
        """Fetch a single morning brief.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            brief_id: The brief ID to fetch.

        Returns:
            The MorningBrief model.

        Raises:
            MorningBriefNotFoundError: If the brief does not exist.
        """
        doc = self._collection(company_id, project_id).document(brief_id).get()
        if not doc.exists:
            raise MorningBriefNotFoundError(brief_id)
        return MorningBrief(**doc.to_dict())

    def list_briefs(
        self,
        company_id: str,
        project_id: str,
        limit: int = 20,
    ) -> dict:
        """List morning briefs for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of briefs to return.

        Returns:
            A dict with 'briefs' list and 'total' count.
        """
        query: firestore.Query = self._collection(company_id, project_id).order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )

        all_docs = list(query.stream())
        total = len(all_docs)

        briefs = [MorningBrief(**doc.to_dict()) for doc in all_docs[:limit]]
        return {"briefs": briefs, "total": total}

    def get_today_brief(
        self,
        company_id: str,
        project_id: str,
    ) -> MorningBrief | None:
        """Check if a brief already exists for today.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            The existing MorningBrief for today, or None.
        """
        today = date.today()
        query = self._collection(company_id, project_id).where(
            "date", "==", today.isoformat()
        )
        docs = list(query.stream())
        if docs:
            return MorningBrief(**docs[0].to_dict())
        return None
