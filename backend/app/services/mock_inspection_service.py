"""Mock OSHA Inspection engine — the killer feature.

Orchestrates a multi-step compliance audit that simulates what happens
when an OSHA Compliance Safety and Health Officer (CSHO) shows up at a
contractor's job site.  Returns findings in the exact format OSHA uses.
"""

import json
import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any

import anthropic

from app.config import Settings
from app.exceptions import (
    GenerationError,
    MockInspectionNotFoundError,
    ProjectNotFoundError,
)
from app.models.mock_inspection import (
    FindingCategory,
    FindingSeverity,
    MockInspectionFinding,
    MockInspectionResult,
    MockInspectionResultSummary,
)
from app.services.base_service import BaseService
from app.services.document_service import DocumentService
from app.services.inspection_service import InspectionService
from app.services.osha_log_service import OshaLogService
from app.services.project_service import ProjectService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Required programs knowledge base
# ---------------------------------------------------------------------------

REQUIRED_PROGRAMS: list[dict[str, Any]] = [
    {
        "program": "Hazard Communication Program",
        "standard": "29 CFR 1926.59",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["hazard communication", "hazcom", "ghs", "sds"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Fall Protection Plan",
        "standard": "29 CFR 1926.502(k)",
        "required_for": "all",
        "severity": "critical",
        "document_type": "fall_protection",
        "search_terms": ["fall protection", "fall prevention"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Emergency Action Plan",
        "standard": "29 CFR 1926.35",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["emergency action", "emergency plan", "eap"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Fire Prevention Plan",
        "standard": "29 CFR 1926.24",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["fire prevention", "fire safety"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Scaffold Safety Program",
        "standard": "29 CFR 1926.451",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["scaffold", "scaffolding"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Excavation & Trenching Program",
        "standard": "29 CFR 1926.651",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["excavation", "trenching", "trench"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Lockout/Tagout (LOTO) Program",
        "standard": "29 CFR 1926.417",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["lockout", "tagout", "loto"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Respiratory Protection Program",
        "standard": "29 CFR 1926.103",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["respiratory", "respirator"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Hearing Conservation Program",
        "standard": "29 CFR 1926.52",
        "required_for": "all",
        "severity": "medium",
        "document_type": "sssp",
        "search_terms": ["hearing conservation", "noise"],
        "penalty_range": "$1,000 - $16,131",
    },
    {
        "program": "Electrical Safety Program",
        "standard": "29 CFR 1926.405",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["electrical safety", "gfci", "electrical"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Confined Space Entry Program",
        "standard": "29 CFR 1926.1203",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["confined space"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Personal Protective Equipment Program",
        "standard": "29 CFR 1926.95",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["ppe", "personal protective equipment"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Silica Exposure Control Plan",
        "standard": "29 CFR 1926.1153",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["silica", "crystalline silica"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Lead Exposure Control Plan",
        "standard": "29 CFR 1926.62",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["lead", "lead exposure"],
        "penalty_range": "$4,000 - $16,131",
    },
    {
        "program": "Crane & Rigging Safety Program",
        "standard": "29 CFR 1926.1400",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["crane", "rigging", "hoisting"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Steel Erection Safety Program",
        "standard": "29 CFR 1926.750",
        "required_for": "all",
        "severity": "critical",
        "document_type": "sssp",
        "search_terms": ["steel erection", "structural steel"],
        "penalty_range": "$16,131 - $161,323",
    },
    {
        "program": "Stairways and Ladders Program",
        "standard": "29 CFR 1926.1050",
        "required_for": "all",
        "severity": "high",
        "document_type": "sssp",
        "search_terms": ["stairway", "ladder"],
        "penalty_range": "$4,000 - $16,131",
    },
]

ROLE_CERT_REQUIREMENTS: dict[str, list[str]] = {
    "foreman": ["osha_30", "fall_protection", "first_aid_cpr"],
    "superintendent": ["osha_30", "fall_protection", "first_aid_cpr"],
    "project_manager": ["osha_30"],
    "safety_manager": ["osha_30", "fall_protection", "first_aid_cpr", "confined_space"],
    "laborer": ["osha_10"],
    "carpenter": ["osha_10", "fall_protection"],
    "electrician": ["osha_10", "electrical_safety"],
    "ironworker": ["osha_10", "fall_protection"],
    "plumber": ["osha_10", "confined_space"],
    "operator": ["osha_10", "forklift_operator"],
    "crane_operator": ["osha_10", "crane_operator_nccco", "rigging_signal"],
    "welder": ["osha_10", "first_aid_cpr"],
    "painter": ["osha_10", "respiratory_fit_test", "lead_awareness"],
    "roofer": ["osha_10", "fall_protection"],
    "mason": ["osha_10", "scaffold_competent"],
}

# Severity to point deductions for score calculation
_SEVERITY_DEDUCTIONS: dict[str, int] = {
    FindingSeverity.CRITICAL: 15,
    FindingSeverity.HIGH: 10,
    FindingSeverity.MEDIUM: 5,
    FindingSeverity.LOW: 2,
    FindingSeverity.INFO: 0,
}

# AI prompts
_DOCUMENT_AUDIT_SYSTEM_PROMPT = """You are an OSHA Compliance Safety and Health Officer (CSHO) conducting an inspection of a construction contractor's written safety programs.

You will receive a safety document and its type. Evaluate whether it meets the requirements of the applicable OSHA standards. Identify any deficiencies, missing required elements, outdated references, or non-compliant sections.

For each finding, return a JSON object with these exact keys:
- "title": Short description of the deficiency
- "osha_standard": The specific CFR reference being violated
- "description": What you observed
- "citation_language": How OSHA would write this citation
- "corrective_action": Recommended fix
- "severity": One of "critical", "high", "medium", "low", "info"
- "category": One of "incomplete_document", "outdated_document", "program_deficiency"

Return ONLY a JSON array of finding objects. If the document is fully compliant, return an empty array [].
Do not include any text outside the JSON."""

_EXECUTIVE_SUMMARY_SYSTEM_PROMPT = """You are a senior safety consultant writing an executive summary of a mock OSHA inspection for a construction company.

Write a professional 2-3 paragraph summary that:
1. States the overall compliance posture (score and grade)
2. Highlights the most critical findings that would result in citations
3. Provides actionable next steps prioritized by severity

Use professional, direct language. Reference specific OSHA standards where applicable.
Return ONLY the narrative text, no JSON or formatting."""


class MockInspectionService(BaseService):
    """Orchestrates mock OSHA inspections across all company data.

    Graph model:
        (Company)-[:HAS_MOCK_INSPECTION]->(MockInspectionResult)
        findings stored as _findings_json, areas_checked as _areas_checked_json.

    Args:
        driver: Neo4j driver instance.
        settings: Application settings containing the Anthropic API key.
        document_service: Service for fetching company documents.
        worker_service: Service for fetching worker/certification data.
        project_service: Service for fetching projects.
        inspection_service: Service for fetching daily inspections.
        toolbox_talk_service: Service for fetching toolbox talks.
        osha_log_service: Service for fetching OSHA 300 log data.
    """

    def __init__(
        self,
        driver: Any,
        settings: Settings,
        document_service: DocumentService,
        worker_service: WorkerService,
        project_service: ProjectService,
        inspection_service: InspectionService,
        toolbox_talk_service: ToolboxTalkService,
        osha_log_service: OshaLogService,
    ) -> None:
        super().__init__(driver)
        self.settings = settings
        self.document_service = document_service
        self.worker_service = worker_service
        self.project_service = project_service
        self.inspection_service = inspection_service
        self.toolbox_talk_service = toolbox_talk_service
        self.osha_log_service = osha_log_service

        if settings.anthropic_api_key:
            self.ai_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            self.ai_client = None
        self.model = "claude-sonnet-4-20250514"

    def _generate_finding_id(self) -> str:
        """Generate a unique finding ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"find_{secrets.token_hex(8)}"

    @staticmethod
    def _to_model(record: dict[str, Any]) -> MockInspectionResult:
        """Convert a Neo4j record to a MockInspectionResult model.

        Args:
            record: Dict with 'result' key from Cypher.

        Returns:
            A MockInspectionResult model instance.
        """
        data = dict(record["result"])
        findings_json = data.pop("_findings_json", "[]")
        data["findings"] = json.loads(findings_json) if findings_json else []
        areas_json = data.pop("_areas_checked_json", "[]")
        data["areas_checked"] = json.loads(areas_json) if areas_json else []
        data["company_id"] = record["company_id"]
        return MockInspectionResult(**data)

    # -----------------------------------------------------------------------
    # Step 2: Rule-based checks
    # -----------------------------------------------------------------------

    def _check_written_programs(
        self, company_id: str, documents: list[dict[str, Any]]
    ) -> list[MockInspectionFinding]:
        """Check for missing or outdated required written programs.

        Args:
            company_id: The company ID.
            documents: List of document dicts.

        Returns:
            List of findings for missing programs.
        """
        findings: list[MockInspectionFinding] = []
        doc_titles_lower = [d.get("title", "").lower() for d in documents]
        doc_types = [d.get("document_type", "") for d in documents]

        for program in REQUIRED_PROGRAMS:
            found = False
            for title in doc_titles_lower:
                for term in program["search_terms"]:
                    if term in title:
                        found = True
                        break
                if found:
                    break

            if not found and program["document_type"] in doc_types:
                if program["document_type"] == "sssp" and "sssp" in doc_types:
                    continue

            if not found:
                severity_map = {
                    "critical": FindingSeverity.CRITICAL,
                    "high": FindingSeverity.HIGH,
                    "medium": FindingSeverity.MEDIUM,
                    "low": FindingSeverity.LOW,
                }
                severity = severity_map.get(
                    program.get("severity", "high"), FindingSeverity.HIGH
                )

                findings.append(
                    MockInspectionFinding(
                        finding_id=self._generate_finding_id(),
                        severity=severity,
                        category=FindingCategory.MISSING_DOCUMENT,
                        title=f"Missing {program['program']}",
                        osha_standard=program["standard"],
                        description=(
                            f"The employer does not have a written "
                            f"{program['program']} as required by "
                            f"{program['standard']}. No document was found "
                            f"in the company's safety program library that "
                            f"addresses this requirement."
                        ),
                        citation_language=(
                            f"Section {program['standard']}: The employer "
                            f"did not develop and implement a written "
                            f"{program['program']}."
                        ),
                        corrective_action=(
                            f"Develop and implement a written "
                            f"{program['program']} that meets the "
                            f"requirements of {program['standard']}."
                        ),
                        estimated_penalty=program.get("penalty_range", "N/A"),
                        can_auto_fix=True,
                        auto_fix_action=(
                            f"Generate a {program['program']} document "
                            f"using Kerf's AI document generator."
                        ),
                    )
                )

        return findings

    def _check_certifications(
        self, company_id: str, workers: list[dict[str, Any]]
    ) -> list[MockInspectionFinding]:
        """Check for expired or expiring-soon certifications.

        Args:
            company_id: The company ID.
            workers: List of worker dicts with certifications.

        Returns:
            List of findings for certification issues.
        """
        findings: list[MockInspectionFinding] = []
        today = date.today()
        warning_cutoff = today + timedelta(days=30)

        for worker in workers:
            worker_name = (
                f"{worker.get('first_name', '')} {worker.get('last_name', '')}"
            ).strip()

            for cert in worker.get("certifications", []):
                expiry = cert.get("expiry_date")
                if expiry is None:
                    continue

                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)

                cert_type = cert.get("certification_type", "unknown")
                cert_display = cert_type.replace("_", " ").title()

                if expiry < today:
                    findings.append(
                        MockInspectionFinding(
                            finding_id=self._generate_finding_id(),
                            severity=FindingSeverity.HIGH,
                            category=FindingCategory.EXPIRED_CERTIFICATION,
                            title=f"Expired {cert_display} — {worker_name}",
                            osha_standard="29 CFR 1926.21(b)(2)",
                            description=(
                                f"Worker {worker_name}'s {cert_display} "
                                f"certification expired on {expiry.isoformat()}. "
                                f"The worker may be performing tasks without "
                                f"current, valid training documentation."
                            ),
                            citation_language=(
                                f"Section 29 CFR 1926.21(b)(2): The employer "
                                f"did not ensure that employee {worker_name} "
                                f"had current training certification for "
                                f"{cert_display}. Certification expired "
                                f"{expiry.isoformat()}."
                            ),
                            corrective_action=(
                                f"Schedule {worker_name} for {cert_display} "
                                f"recertification training immediately. Remove "
                                f"from tasks requiring this certification "
                                f"until recertified."
                            ),
                            estimated_penalty="$4,000 - $16,131",
                            can_auto_fix=False,
                        )
                    )
                elif expiry <= warning_cutoff:
                    findings.append(
                        MockInspectionFinding(
                            finding_id=self._generate_finding_id(),
                            severity=FindingSeverity.LOW,
                            category=FindingCategory.EXPIRED_CERTIFICATION,
                            title=f"Expiring Soon: {cert_display} — {worker_name}",
                            osha_standard="29 CFR 1926.21(b)(2)",
                            description=(
                                f"Worker {worker_name}'s {cert_display} "
                                f"certification expires on {expiry.isoformat()}, "
                                f"within the next 30 days."
                            ),
                            citation_language="N/A — not yet expired",
                            corrective_action=(
                                f"Schedule {worker_name} for {cert_display} "
                                f"renewal training before {expiry.isoformat()}."
                            ),
                            estimated_penalty="N/A",
                            can_auto_fix=False,
                        )
                    )

        return findings

    def _check_osha_log(self, company_id: str) -> list[MockInspectionFinding]:
        """Check OSHA 300 log for recordkeeping gaps.

        Args:
            company_id: The company ID.

        Returns:
            List of findings for recordkeeping issues.
        """
        findings: list[MockInspectionFinding] = []
        current_year = date.today().year

        result = self.osha_log_service.list_entries(company_id, year=current_year, limit=1)
        # has_entries = result["total"] > 0  # noqa: ERA001

        prev_year = current_year - 1
        try:
            summary = self.osha_log_service.get_300a_summary(company_id, prev_year)
            if not summary.posted:
                findings.append(
                    MockInspectionFinding(
                        finding_id=self._generate_finding_id(),
                        severity=FindingSeverity.MEDIUM,
                        category=FindingCategory.RECORDKEEPING_GAP,
                        title=f"OSHA 300A Summary Not Certified/Posted ({prev_year})",
                        osha_standard="29 CFR 1904.32",
                        description=(
                            f"The employer has not certified and posted the "
                            f"OSHA 300A Annual Summary for calendar year {prev_year}. "
                            f"The summary must be posted from February 1 to April 30."
                        ),
                        citation_language=(
                            f"Section 29 CFR 1904.32: The employer did not "
                            f"certify and post the OSHA 300A Annual Summary "
                            f"for the year {prev_year}."
                        ),
                        corrective_action=(
                            f"Complete and certify the OSHA 300A Annual Summary "
                            f"for {prev_year}. Post it in a conspicuous location "
                            f"where employee notices are customarily posted."
                        ),
                        estimated_penalty="$1,000 - $16,131",
                        can_auto_fix=False,
                    )
                )
        except Exception:
            findings.append(
                MockInspectionFinding(
                    finding_id=self._generate_finding_id(),
                    severity=FindingSeverity.MEDIUM,
                    category=FindingCategory.RECORDKEEPING_GAP,
                    title=f"No OSHA 300A Summary for {prev_year}",
                    osha_standard="29 CFR 1904.32",
                    description=(
                        f"No OSHA 300A Annual Summary was found for "
                        f"calendar year {prev_year}."
                    ),
                    citation_language=(
                        f"Section 29 CFR 1904.32: The employer did not "
                        f"prepare the annual summary of the OSHA 300 Log "
                        f"for year {prev_year}."
                    ),
                    corrective_action=(
                        f"Prepare, certify, and post the OSHA 300A Annual "
                        f"Summary for {prev_year}."
                    ),
                    estimated_penalty="$1,000 - $16,131",
                    can_auto_fix=False,
                )
            )

        return findings

    def _check_inspections(
        self,
        company_id: str,
        project_id: str | None,
        projects: list[dict[str, Any]],
    ) -> list[MockInspectionFinding]:
        """Check for stale or missing inspections on projects.

        Args:
            company_id: The company ID.
            project_id: Specific project to check, or None for all.
            projects: List of project dicts.

        Returns:
            List of findings for inspection gaps.
        """
        findings: list[MockInspectionFinding] = []
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        for project in projects:
            pid = project.get("id", "")
            proj_name = project.get("name", "Unknown Project")
            proj_status = project.get("status", "")

            if proj_status != "active":
                continue
            if project_id and pid != project_id:
                continue

            try:
                insp_result = self.inspection_service.list_inspections(
                    company_id, pid, limit=50
                )
                inspections = insp_result.get("inspections", [])
            except (ProjectNotFoundError, Exception):
                inspections = []

            has_recent = False
            for insp in inspections:
                created_at = getattr(insp, "created_at", None)
                if created_at and created_at >= seven_days_ago:
                    has_recent = True
                    break

            if not has_recent:
                findings.append(
                    MockInspectionFinding(
                        finding_id=self._generate_finding_id(),
                        severity=FindingSeverity.MEDIUM,
                        category=FindingCategory.MISSING_INSPECTION,
                        title=f"No Recent Safety Inspection — {proj_name}",
                        osha_standard="29 CFR 1926.20(b)(2)",
                        description=(
                            f"Active project '{proj_name}' has no daily safety "
                            f"inspection recorded within the last 7 days. "
                            f"OSHA requires frequent and regular inspections "
                            f"of job sites by competent persons."
                        ),
                        citation_language=(
                            f"Section 29 CFR 1926.20(b)(2): The employer did "
                            f"not provide for frequent and regular inspections "
                            f"of the job site at '{proj_name}'."
                        ),
                        corrective_action=(
                            f"Conduct a daily safety inspection of '{proj_name}' "
                            f"by a competent person and document the findings."
                        ),
                        estimated_penalty="$4,000 - $16,131",
                        can_auto_fix=False,
                    )
                )

        return findings

    def _check_toolbox_talks(
        self,
        company_id: str,
        project_id: str | None,
        projects: list[dict[str, Any]],
    ) -> list[MockInspectionFinding]:
        """Check for missing toolbox talks on active projects.

        Args:
            company_id: The company ID.
            project_id: Specific project to check, or None for all.
            projects: List of project dicts.

        Returns:
            List of findings for missing toolbox talks.
        """
        findings: list[MockInspectionFinding] = []
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        for project in projects:
            pid = project.get("id", "")
            proj_name = project.get("name", "Unknown Project")
            proj_status = project.get("status", "")

            if proj_status != "active":
                continue
            if project_id and pid != project_id:
                continue

            try:
                talk_result = self.toolbox_talk_service.list_talks(
                    company_id, pid, limit=50
                )
                talks = talk_result.get("toolbox_talks", [])
            except Exception:
                talks = []

            has_recent = False
            for talk in talks:
                created_at = getattr(talk, "created_at", None)
                if created_at and created_at >= seven_days_ago:
                    has_recent = True
                    break

            if not has_recent:
                findings.append(
                    MockInspectionFinding(
                        finding_id=self._generate_finding_id(),
                        severity=FindingSeverity.MEDIUM,
                        category=FindingCategory.MISSING_TRAINING,
                        title=f"No Recent Toolbox Talk — {proj_name}",
                        osha_standard="29 CFR 1926.21(b)(2)",
                        description=(
                            f"Active project '{proj_name}' has no toolbox "
                            f"talk or safety meeting recorded in the last "
                            f"7 days. Regular safety instruction is required."
                        ),
                        citation_language=(
                            f"Section 29 CFR 1926.21(b)(2): The employer did "
                            f"not instruct employees in the recognition and "
                            f"avoidance of unsafe conditions at '{proj_name}'."
                        ),
                        corrective_action=(
                            f"Conduct weekly toolbox talks at '{proj_name}' "
                            f"covering site-specific hazards. Document "
                            f"attendance with sign-in sheets."
                        ),
                        estimated_penalty="$4,000 - $16,131",
                        can_auto_fix=True,
                        auto_fix_action=(
                            f"Generate a toolbox talk for '{proj_name}' "
                            f"using Kerf's AI toolbox talk generator."
                        ),
                    )
                )

        return findings

    def _check_training_matrix(
        self, company_id: str, workers: list[dict[str, Any]]
    ) -> list[MockInspectionFinding]:
        """Check for gaps between worker roles and required certifications.

        Args:
            company_id: The company ID.
            workers: List of worker dicts.

        Returns:
            List of findings for training gaps.
        """
        findings: list[MockInspectionFinding] = []

        for worker in workers:
            if worker.get("status") != "active":
                continue

            role = (worker.get("role") or "").lower().strip()
            worker_name = (
                f"{worker.get('first_name', '')} {worker.get('last_name', '')}"
            ).strip()

            required_certs = ROLE_CERT_REQUIREMENTS.get(role, [])
            if not required_certs:
                continue

            worker_cert_types = set()
            for cert in worker.get("certifications", []):
                worker_cert_types.add(cert.get("certification_type", ""))

            for required_cert in required_certs:
                if required_cert not in worker_cert_types:
                    cert_display = required_cert.replace("_", " ").title()
                    role_display = role.replace("_", " ").title()

                    findings.append(
                        MockInspectionFinding(
                            finding_id=self._generate_finding_id(),
                            severity=FindingSeverity.HIGH,
                            category=FindingCategory.MISSING_TRAINING,
                            title=(
                                f"Missing {cert_display} for "
                                f"{role_display} — {worker_name}"
                            ),
                            osha_standard="29 CFR 1926.21(b)(2)",
                            description=(
                                f"Worker {worker_name} (role: {role_display}) "
                                f"does not have the required {cert_display} "
                                f"certification on file. This training is "
                                f"required for workers in the {role_display} role."
                            ),
                            citation_language=(
                                f"Section 29 CFR 1926.21(b)(2): The employer "
                                f"did not ensure that {worker_name}, employed "
                                f"as {role_display}, received required "
                                f"{cert_display} training."
                            ),
                            corrective_action=(
                                f"Enroll {worker_name} in {cert_display} "
                                f"training. Do not assign {role_display} "
                                f"duties until training is completed and "
                                f"documented."
                            ),
                            estimated_penalty="$4,000 - $16,131",
                            can_auto_fix=False,
                        )
                    )

        return findings

    # -----------------------------------------------------------------------
    # Step 3: AI-powered document audit (optional, for deep_audit)
    # -----------------------------------------------------------------------

    def _ai_audit_document(
        self, document: dict[str, Any]
    ) -> list[MockInspectionFinding]:
        """Run AI-powered audit on a single document.

        Args:
            document: Document dict with content and metadata.

        Returns:
            List of findings from AI analysis.
        """
        if not self.ai_client:
            return []

        doc_type = document.get("document_type", "safety document")
        doc_title = document.get("title", "Untitled")
        content = document.get("content", {})

        if not content:
            return []

        user_prompt = (
            f"Document Title: {doc_title}\n"
            f"Document Type: {doc_type}\n\n"
            f"Document Content:\n{json.dumps(content, indent=2, default=str)}"
        )

        try:
            response = self.ai_client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=_DOCUMENT_AUDIT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except (anthropic.APIError, Exception) as exc:
            logger.warning("AI document audit failed for %s: %s", doc_title, exc)
            return []

        raw_text = response.content[0].text.strip()

        if raw_text.startswith("```"):
            first_newline = raw_text.index("\n")
            raw_text = raw_text[first_newline + 1:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].rstrip()

        try:
            ai_findings = json.loads(raw_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI audit response for %s", doc_title)
            return []

        if not isinstance(ai_findings, list):
            return []

        findings: list[MockInspectionFinding] = []
        severity_map = {
            "critical": FindingSeverity.CRITICAL,
            "high": FindingSeverity.HIGH,
            "medium": FindingSeverity.MEDIUM,
            "low": FindingSeverity.LOW,
            "info": FindingSeverity.INFO,
        }
        category_map = {
            "incomplete_document": FindingCategory.INCOMPLETE_DOCUMENT,
            "outdated_document": FindingCategory.OUTDATED_DOCUMENT,
            "program_deficiency": FindingCategory.PROGRAM_DEFICIENCY,
        }

        for af in ai_findings:
            if not isinstance(af, dict):
                continue
            findings.append(
                MockInspectionFinding(
                    finding_id=self._generate_finding_id(),
                    severity=severity_map.get(
                        af.get("severity", "medium"), FindingSeverity.MEDIUM
                    ),
                    category=category_map.get(
                        af.get("category", "program_deficiency"),
                        FindingCategory.PROGRAM_DEFICIENCY,
                    ),
                    title=af.get("title", "AI-identified deficiency"),
                    osha_standard=af.get("osha_standard", ""),
                    description=af.get("description", ""),
                    citation_language=af.get("citation_language", ""),
                    corrective_action=af.get("corrective_action", ""),
                    estimated_penalty="Varies",
                    can_auto_fix=False,
                )
            )

        return findings

    # -----------------------------------------------------------------------
    # Step 4: Score calculation
    # -----------------------------------------------------------------------

    def _calculate_score(
        self, findings: list[MockInspectionFinding]
    ) -> tuple[int, str]:
        """Calculate overall compliance score and letter grade.

        Args:
            findings: All findings from the inspection.

        Returns:
            Tuple of (score, grade).
        """
        score = 100
        for finding in findings:
            deduction = _SEVERITY_DEDUCTIONS.get(finding.severity, 0)
            score -= deduction

        score = max(score, 0)

        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 40:
            grade = "D"
        else:
            grade = "F"

        return score, grade

    # -----------------------------------------------------------------------
    # Step 5: Executive summary generation
    # -----------------------------------------------------------------------

    def _generate_executive_summary(
        self,
        findings: list[MockInspectionFinding],
        score: int,
        grade: str,
        company_name: str,
    ) -> str:
        """Generate an AI-powered executive summary of findings.

        Args:
            findings: All findings from the inspection.
            score: Overall compliance score.
            grade: Letter grade.
            company_name: The company name for the report.

        Returns:
            Executive summary narrative text.
        """
        critical_count = sum(
            1 for f in findings if f.severity == FindingSeverity.CRITICAL
        )
        high_count = sum(
            1 for f in findings if f.severity == FindingSeverity.HIGH
        )
        medium_count = sum(
            1 for f in findings if f.severity == FindingSeverity.MEDIUM
        )

        if self.ai_client and findings:
            findings_summary = "\n".join(
                f"- [{f.severity.value.upper()}] {f.title} ({f.osha_standard})"
                for f in findings
            )
            user_prompt = (
                f"Company: {company_name}\n"
                f"Score: {score}/100 (Grade: {grade})\n"
                f"Total Findings: {len(findings)}\n"
                f"Critical: {critical_count}, High: {high_count}, "
                f"Medium: {medium_count}\n\n"
                f"Findings:\n{findings_summary}"
            )

            try:
                response = self.ai_client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=_EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text.strip()
            except Exception as exc:
                logger.warning("AI executive summary generation failed: %s", exc)

        if not findings:
            return (
                f"Mock OSHA inspection of {company_name} resulted in a "
                f"score of {score}/100 (Grade: {grade}). No significant "
                f"compliance gaps were identified. The company appears to "
                f"maintain adequate safety documentation, training records, "
                f"and inspection logs. Continue current safety management "
                f"practices and conduct regular self-audits."
            )

        top_findings = [
            f for f in findings
            if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
        ][:5]
        top_list = "; ".join(f.title for f in top_findings) if top_findings else "N/A"

        return (
            f"Mock OSHA inspection of {company_name} resulted in a "
            f"score of {score}/100 (Grade: {grade}) with {len(findings)} "
            f"total findings. Of these, {critical_count} are critical and "
            f"{high_count} are high severity — these would likely result "
            f"in OSHA citations if found during an actual inspection.\n\n"
            f"The most significant issues identified: {top_list}.\n\n"
            f"Immediate action is recommended on all critical and high "
            f"severity findings. Address medium severity items within "
            f"30 days. Review low severity recommendations for continuous "
            f"improvement opportunities."
        )

    # -----------------------------------------------------------------------
    # Main orchestration
    # -----------------------------------------------------------------------

    def run_inspection(
        self,
        company_id: str,
        project_id: str | None = None,
        deep_audit: bool = False,
        user_id: str = "",
    ) -> MockInspectionResult:
        """Run a full mock OSHA inspection.

        Args:
            company_id: The company to inspect.
            project_id: Scope to a specific project, or None for company-wide.
            deep_audit: Whether to run AI-powered document review.
            user_id: Firebase UID of the requesting user.

        Returns:
            The complete MockInspectionResult.
        """
        now = datetime.now(timezone.utc)

        # -- Step 1: Gather all company data via Neo4j -------------------------

        company_result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.name AS name",
            {"id": company_id},
        )
        company_name = company_result["name"] if company_result else "Unknown Company"

        doc_result = self.document_service.list_documents(company_id, limit=200)
        documents = [
            d.model_dump() if hasattr(d, "model_dump") else d
            for d in doc_result.get("documents", [])
        ]

        worker_result = self.worker_service.list_workers(company_id, limit=500)
        workers = [
            w.model_dump() if hasattr(w, "model_dump") else w
            for w in worker_result.get("workers", [])
        ]

        proj_result = self.project_service.list_projects(company_id, limit=100)
        projects = [
            p.model_dump() if hasattr(p, "model_dump") else p
            for p in proj_result.get("projects", [])
        ]

        # -- Step 2: Rule-based checks ----------------------------------------

        all_findings: list[MockInspectionFinding] = []

        all_findings.extend(self._check_written_programs(company_id, documents))
        all_findings.extend(self._check_certifications(company_id, workers))
        all_findings.extend(self._check_osha_log(company_id))
        all_findings.extend(
            self._check_inspections(company_id, project_id, projects)
        )
        all_findings.extend(
            self._check_toolbox_talks(company_id, project_id, projects)
        )
        all_findings.extend(self._check_training_matrix(company_id, workers))

        # -- Step 3: AI-powered document audit (optional) ----------------------

        documents_ai_audited = 0
        if deep_audit:
            for doc in documents:
                content = doc.get("content")
                if content:
                    ai_findings = self._ai_audit_document(doc)
                    all_findings.extend(ai_findings)
                    documents_ai_audited += 1

        # -- Step 4: Calculate score -------------------------------------------

        score, grade = self._calculate_score(all_findings)

        # -- Step 5: Executive summary -----------------------------------------

        executive_summary = self._generate_executive_summary(
            all_findings, score, grade, company_name
        )

        # -- Count findings by severity ----------------------------------------

        critical_count = sum(
            1 for f in all_findings if f.severity == FindingSeverity.CRITICAL
        )
        high_count = sum(
            1 for f in all_findings if f.severity == FindingSeverity.HIGH
        )
        medium_count = sum(
            1 for f in all_findings if f.severity == FindingSeverity.MEDIUM
        )
        low_count = sum(
            1 for f in all_findings if f.severity == FindingSeverity.LOW
        )
        info_count = sum(
            1 for f in all_findings if f.severity == FindingSeverity.INFO
        )

        areas_checked = list(
            {p["program"].split(" ")[0] for p in REQUIRED_PROGRAMS}
        )
        areas_checked.sort()

        inspections_reviewed = 0
        for project in projects:
            pid = project.get("id", "")
            if project_id and pid != project_id:
                continue
            try:
                insp_result = self.inspection_service.list_inspections(
                    company_id, pid, limit=1
                )
                inspections_reviewed += insp_result.get("total", 0)
            except Exception:
                pass

        # -- Build and store result --------------------------------------------

        result_id = self._generate_id("minsp")
        result = MockInspectionResult(
            id=result_id,
            company_id=company_id,
            project_id=project_id,
            inspection_date=now,
            overall_score=score,
            grade=grade,
            total_findings=len(all_findings),
            critical_findings=critical_count,
            high_findings=high_count,
            medium_findings=medium_count,
            low_findings=low_count,
            info_findings=info_count,
            findings=all_findings,
            documents_reviewed=len(documents),
            training_records_reviewed=len(workers),
            inspections_reviewed=inspections_reviewed,
            areas_checked=areas_checked,
            executive_summary=executive_summary,
            deep_audit=deep_audit,
            created_at=now,
            created_by=user_id,
        )

        # Serialize findings and areas for Neo4j storage
        findings_data = []
        for f in all_findings:
            fd = f.model_dump()
            if hasattr(fd.get("severity"), "value"):
                fd["severity"] = fd["severity"].value
            if hasattr(fd.get("category"), "value"):
                fd["category"] = fd["category"].value
            findings_data.append(fd)

        props: dict[str, Any] = {
            "id": result_id,
            "project_id": project_id,
            "inspection_date": now.isoformat(),
            "overall_score": score,
            "grade": grade,
            "total_findings": len(all_findings),
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
            "low_findings": low_count,
            "info_findings": info_count,
            "_findings_json": json.dumps(findings_data, default=str),
            "documents_reviewed": len(documents),
            "training_records_reviewed": len(workers),
            "inspections_reviewed": inspections_reviewed,
            "_areas_checked_json": json.dumps(areas_checked),
            "executive_summary": executive_summary,
            "deep_audit": deep_audit,
            "created_at": now.isoformat(),
            "created_by": user_id,
        }

        self._write_tx(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (r:MockInspectionResult $props)
            CREATE (c)-[:HAS_MOCK_INSPECTION]->(r)
            """,
            {"company_id": company_id, "props": props},
        )

        return result

    # -----------------------------------------------------------------------
    # Read operations
    # -----------------------------------------------------------------------

    def get_result(
        self, company_id: str, result_id: str
    ) -> MockInspectionResult:
        """Fetch a stored mock inspection result.

        Args:
            company_id: The company ID.
            result_id: The inspection result ID.

        Returns:
            The MockInspectionResult.

        Raises:
            MockInspectionNotFoundError: If the result does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_MOCK_INSPECTION]->(r:MockInspectionResult {id: $result_id})
            RETURN r {.*} AS result, c.id AS company_id
            """,
            {"company_id": company_id, "result_id": result_id},
        )
        if result is None:
            raise MockInspectionNotFoundError(result_id)
        return self._to_model(result)

    def list_results(
        self,
        company_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List past mock inspection results with pagination.

        Args:
            company_id: The company ID.
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            A dict with 'results' list and 'total' count.
        """
        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_MOCK_INSPECTION]->(r:MockInspectionResult)
            RETURN count(r) AS total
            """,
            {"company_id": company_id},
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_MOCK_INSPECTION]->(r:MockInspectionResult)
            RETURN r.id AS id, r.inspection_date AS inspection_date,
                   r.overall_score AS overall_score, r.grade AS grade,
                   r.total_findings AS total_findings,
                   r.critical_findings AS critical_findings,
                   r.deep_audit AS deep_audit, r.created_at AS created_at,
                   r.project_id AS project_id,
                   $company_id AS company_id
            ORDER BY r.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            {"company_id": company_id, "limit": limit, "offset": offset},
        )

        summaries = []
        for r in results:
            summaries.append(
                MockInspectionResultSummary(
                    id=r["id"],
                    company_id=r["company_id"],
                    project_id=r.get("project_id"),
                    inspection_date=r["inspection_date"],
                    overall_score=r["overall_score"],
                    grade=r["grade"],
                    total_findings=r["total_findings"],
                    critical_findings=r["critical_findings"],
                    deep_audit=r.get("deep_audit", False),
                    created_at=r["created_at"],
                )
            )

        return {"results": summaries, "total": total}
