"""Pydantic models for Mock OSHA Inspection engine."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    """OSHA violation severity classification.

    Maps to real OSHA citation categories:
    - CRITICAL: Willful or Serious with high gravity
    - HIGH: Serious citation
    - MEDIUM: Other-Than-Serious
    - LOW: Recommendation, not likely cited
    - INFO: Best practice suggestion
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Category of compliance gap identified during mock inspection."""

    MISSING_DOCUMENT = "missing_document"
    OUTDATED_DOCUMENT = "outdated_document"
    INCOMPLETE_DOCUMENT = "incomplete_document"
    MISSING_TRAINING = "missing_training"
    EXPIRED_CERTIFICATION = "expired_certification"
    MISSING_INSPECTION = "missing_inspection"
    RECORDKEEPING_GAP = "recordkeeping_gap"
    PROGRAM_DEFICIENCY = "program_deficiency"


class MockInspectionFinding(BaseModel):
    """A single finding from a mock OSHA inspection.

    Mirrors the format a real OSHA CSHO would use when writing
    a citation, including the applicable standard, observed condition,
    and proposed penalty range.
    """

    finding_id: str
    severity: FindingSeverity
    category: FindingCategory
    title: str = Field(..., description="Short title, e.g. 'Missing Fall Protection Written Program'")
    osha_standard: str = Field(..., description="OSHA standard reference, e.g. '29 CFR 1926.502(k)'")
    description: str = Field(..., description="What the CSHO would observe or note")
    citation_language: str = Field(..., description="Written as OSHA would write the citation")
    corrective_action: str = Field(..., description="Recommended fix")
    estimated_penalty: str = Field(..., description="Penalty range, e.g. '$4,000 - $16,131' or 'N/A'")
    can_auto_fix: bool = Field(
        default=False,
        description="Whether SafetyForge can fix this automatically",
    )
    auto_fix_action: str = Field(
        default="",
        description="What the auto-fix would do, if applicable",
    )


class MockInspectionResult(BaseModel):
    """Complete result of a mock OSHA inspection.

    Contains the overall score, grade, all findings, and metadata
    about what was reviewed during the inspection.
    """

    id: str
    company_id: str
    project_id: str | None = None
    inspection_date: datetime
    overall_score: int = Field(..., ge=0, le=100)
    grade: str = Field(..., pattern=r"^[ABCDF]$")
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int = 0
    findings: list[MockInspectionFinding]
    documents_reviewed: int
    training_records_reviewed: int
    inspections_reviewed: int
    areas_checked: list[str]
    executive_summary: str
    deep_audit: bool = False
    created_at: datetime
    created_by: str


class MockInspectionResultSummary(BaseModel):
    """Lightweight summary for listing past inspection results."""

    id: str
    company_id: str
    project_id: str | None = None
    inspection_date: datetime
    overall_score: int
    grade: str
    total_findings: int
    critical_findings: int
    deep_audit: bool = False
    created_at: datetime


class MockInspectionListResponse(BaseModel):
    """Paginated response for listing mock inspection results."""

    results: list[MockInspectionResultSummary]
    total: int


class RunInspectionRequest(BaseModel):
    """Request body for running a mock OSHA inspection."""

    project_id: str | None = Field(
        default=None,
        description="Scope to a specific project. None = company-wide.",
    )
    deep_audit: bool = Field(
        default=False,
        description="Run AI-powered document audit (slower, uses Claude API).",
    )
