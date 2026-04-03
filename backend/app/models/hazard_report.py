"""Pydantic models for photo-based hazard assessment reports."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class HazardSeverity(str, Enum):
    """Severity levels for identified hazards."""

    IMMINENT_DANGER = "imminent_danger"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HazardStatus(str, Enum):
    """Lifecycle status of a hazard report."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CORRECTED = "corrected"
    CLOSED = "closed"


# Ordered from most severe to least severe for ranking.
SEVERITY_RANK: dict[HazardSeverity, int] = {
    HazardSeverity.IMMINENT_DANGER: 4,
    HazardSeverity.HIGH: 3,
    HazardSeverity.MEDIUM: 2,
    HazardSeverity.LOW: 1,
}


class IdentifiedHazard(BaseModel):
    """A single hazard identified in a photo analysis."""

    hazard_id: str = Field(..., description="Unique hazard identifier within the report")
    description: str = Field(..., description="Clear description of the hazard")
    severity: HazardSeverity = Field(..., description="Hazard severity level")
    osha_standard: str = Field(
        ..., description="Specific OSHA standard violated, e.g. 29 CFR 1926.451(g)(1)"
    )
    category: str = Field(
        ...,
        description=(
            "Hazard category: Fall Protection, Housekeeping, PPE, Electrical, "
            "Struck-By, Excavation, Scaffolding, Fire Safety, Respiratory, Noise, Other"
        ),
    )
    recommended_action: str = Field(..., description="Specific corrective action")
    location_in_image: str = Field(
        ..., description="Where in the image the hazard is visible"
    )


class HazardReportCreate(BaseModel):
    """Input model for creating a hazard report from a photo."""

    project_id: str = Field(..., description="The project this report belongs to")
    photo_base64: str = Field(..., description="Base64-encoded image data")
    media_type: str = Field(
        ..., description="Image MIME type: image/jpeg or image/png"
    )
    description: str = Field(
        default="", max_length=2000, description="Optional text description of the area"
    )
    location: str = Field(
        default="", max_length=256, description="Location description"
    )
    gps_latitude: float | None = Field(None, description="GPS latitude")
    gps_longitude: float | None = Field(None, description="GPS longitude")


class QuickAnalysisRequest(BaseModel):
    """Input model for a quick photo analysis without saving a report."""

    photo_base64: str = Field(..., description="Base64-encoded image data")
    media_type: str = Field(
        ..., description="Image MIME type: image/jpeg or image/png"
    )
    description: str = Field(
        default="", max_length=2000, description="Optional context about the area"
    )
    location: str = Field(
        default="", max_length=256, description="Location description"
    )


class HazardReportStatusUpdate(BaseModel):
    """Input model for updating hazard report status."""

    status: HazardStatus = Field(..., description="New status")
    corrective_action_taken: str = Field(
        default="", max_length=5000, description="Description of corrective action taken"
    )


class HazardReport(BaseModel):
    """Full hazard report model with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    photo_url: str = Field(
        default="", description="URL to uploaded photo (or base64 data URI for MVP)"
    )
    description: str = ""
    location: str = ""
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    ai_analysis: dict = Field(default_factory=dict, description="Full AI analysis result")
    identified_hazards: list[IdentifiedHazard] = Field(default_factory=list)
    hazard_count: int = 0
    highest_severity: HazardSeverity | None = None
    status: HazardStatus = HazardStatus.OPEN
    corrective_action_taken: str = ""
    corrected_at: datetime | None = None
    corrected_by: str = ""
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class HazardReportListResponse(BaseModel):
    """Response model for listing hazard reports."""

    reports: list[HazardReport]
    total: int
