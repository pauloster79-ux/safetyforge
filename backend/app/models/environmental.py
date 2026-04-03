"""Pydantic models for environmental compliance management."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class EnvironmentalProgramType(str, Enum):
    """Available environmental program types."""

    SILICA_EXPOSURE_CONTROL = "silica_exposure_control"
    LEAD_COMPLIANCE = "lead_compliance"
    ASBESTOS_MANAGEMENT = "asbestos_management"
    STORMWATER_SWPPP = "stormwater_swppp"
    DUST_CONTROL = "dust_control"
    NOISE_MONITORING = "noise_monitoring"
    HAZARDOUS_WASTE = "hazardous_waste"


class ExposureMonitoringRecordCreate(BaseModel):
    """Input model for creating an exposure monitoring record."""

    monitoring_type: str = Field(
        ..., description="Type: silica, lead, noise, asbestos"
    )
    monitoring_date: date = Field(..., description="Date of monitoring")
    location: str = Field(..., min_length=1, max_length=256, description="Monitoring location")
    worker_name: str = Field(
        ..., min_length=1, max_length=128, description="Worker being monitored"
    )
    worker_id: str | None = Field(None, description="Optional linked worker ID")
    sample_type: str = Field(
        ..., description="Sample type: personal or area"
    )
    duration_hours: float = Field(..., gt=0, description="Monitoring duration in hours")
    result_value: float = Field(..., ge=0, description="Concentration result")
    result_unit: str = Field(
        ..., description="Unit: ug/m3, dBA, f/cc"
    )
    action_level: float = Field(..., ge=0, description="OSHA action level for this substance")
    pel: float = Field(..., ge=0, description="Permissible Exposure Limit")
    controls_in_place: str = Field(default="", max_length=2000, description="Controls used")
    notes: str = Field(default="", max_length=2000, description="Additional notes")


class ExposureMonitoringRecord(ExposureMonitoringRecordCreate):
    """Full exposure monitoring record with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    exceeds_action_level: bool = False
    exceeds_pel: bool = False
    created_at: datetime
    created_by: str


class ExposureMonitoringRecordListResponse(BaseModel):
    """Response model for listing exposure monitoring records."""

    records: list[ExposureMonitoringRecord]
    total: int


class ExposureSummaryEntry(BaseModel):
    """Summary of exposure monitoring for a single type."""

    monitoring_type: str
    total_samples: int = 0
    samples_above_action_level: int = 0
    samples_above_pel: int = 0
    average_result: float = 0.0
    max_result: float = 0.0
    result_unit: str = ""
    action_level: float = 0.0
    pel: float = 0.0


class ExposureSummaryResponse(BaseModel):
    """Response model for exposure summary endpoint."""

    summaries: list[ExposureSummaryEntry]
    total_samples: int = 0


class SwpppInspectionCreate(BaseModel):
    """Input model for creating a SWPPP inspection."""

    inspection_date: date = Field(..., description="Date of SWPPP inspection")
    inspector_name: str = Field(
        ..., min_length=2, max_length=128, description="Inspector name"
    )
    inspection_type: str = Field(
        ..., description="Type: routine_weekly, post_storm, pre_storm"
    )
    precipitation_last_24h: float = Field(
        default=0, ge=0, description="Precipitation in last 24h (inches)"
    )
    bmp_items: list[dict] = Field(
        default_factory=list,
        description="BMP checklist items [{name, status, notes}]",
    )
    corrective_actions: str = Field(
        default="", max_length=5000, description="Corrective actions needed"
    )
    overall_status: str = Field(..., description="Overall status: pass, fail, partial")
    photo_urls: list[str] = Field(default_factory=list, description="Photo evidence URLs")


class SwpppInspection(SwpppInspectionCreate):
    """Full SWPPP inspection record with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    created_at: datetime
    created_by: str


class SwpppInspectionListResponse(BaseModel):
    """Response model for listing SWPPP inspections."""

    inspections: list[SwpppInspection]
    total: int


class EnvironmentalProgramCreate(BaseModel):
    """Input model for creating an environmental program."""

    program_type: EnvironmentalProgramType = Field(
        ..., description="Type of environmental program"
    )
    title: str = Field(
        ..., min_length=2, max_length=256, description="Program title"
    )
    content: dict = Field(default_factory=dict, description="Program content")
    applicable_projects: list[str] = Field(
        default_factory=list, description="Project IDs this program applies to"
    )
    next_review_due: date | None = Field(None, description="Next review date")


class EnvironmentalProgramUpdate(BaseModel):
    """Input model for updating an environmental program. All fields optional."""

    title: str | None = Field(None, min_length=2, max_length=256)
    content: dict | None = None
    applicable_projects: list[str] | None = None
    next_review_due: date | None = None
    status: str | None = Field(None, description="active, needs_review, expired")


class EnvironmentalProgram(BaseModel):
    """Full environmental program model with ID and audit fields."""

    id: str
    company_id: str
    program_type: EnvironmentalProgramType
    title: str
    content: dict = Field(default_factory=dict)
    applicable_projects: list[str] = Field(default_factory=list)
    last_reviewed: date | None = None
    next_review_due: date | None = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    deleted: bool = False


class EnvironmentalProgramListResponse(BaseModel):
    """Response model for listing environmental programs."""

    programs: list[EnvironmentalProgram]
    total: int


class ComplianceStatusEntry(BaseModel):
    """Compliance status for a single area."""

    area: str
    status: str = Field(description="compliant, non_compliant, needs_attention")
    details: str = ""
    programs_count: int = 0
    overdue_reviews: int = 0
    exposure_exceedances: int = 0


class ComplianceStatusResponse(BaseModel):
    """Response model for overall environmental compliance status."""

    overall_status: str = Field(description="compliant, non_compliant, needs_attention")
    areas: list[ComplianceStatusEntry]
    total_programs: int = 0
    active_programs: int = 0
    overdue_reviews: int = 0
    total_exposure_exceedances: int = 0
