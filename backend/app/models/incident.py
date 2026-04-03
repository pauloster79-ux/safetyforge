"""Pydantic models for incident reports."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Incident severity classification."""

    FATALITY = "fatality"
    HOSPITALIZATION = "hospitalization"
    MEDICAL_TREATMENT = "medical_treatment"
    FIRST_AID = "first_aid"
    NEAR_MISS = "near_miss"
    PROPERTY_DAMAGE = "property_damage"


class IncidentStatus(str, Enum):
    """Incident investigation lifecycle status."""

    REPORTED = "reported"
    INVESTIGATING = "investigating"
    CORRECTIVE_ACTIONS = "corrective_actions"
    CLOSED = "closed"


class IncidentCreate(BaseModel):
    """Input model for creating an incident report."""

    project_id: str = Field(..., description="Parent project ID")
    incident_date: date = Field(..., description="Date the incident occurred")
    incident_time: str = Field(default="", description="Time the incident occurred")
    location: str = Field(..., min_length=2, max_length=512, description="Incident location on site")
    severity: IncidentSeverity = Field(..., description="Incident severity classification")
    description: str = Field(
        ..., min_length=10, max_length=5000, description="Detailed incident description"
    )
    persons_involved: str = Field(default="", max_length=2000, description="Persons involved")
    witnesses: str = Field(default="", max_length=2000, description="Witnesses present")
    immediate_actions_taken: str = Field(
        default="", max_length=2000, description="Immediate response actions taken"
    )
    root_cause: str = Field(default="", max_length=2000, description="Identified root cause")
    corrective_actions: str = Field(
        default="", max_length=2000, description="Corrective actions planned or taken"
    )
    voice_transcript: str = Field(
        default="", max_length=5000, description="Voice-dictated report transcript"
    )
    photo_urls: list[str] = Field(default_factory=list, description="Incident photo URLs")


class IncidentUpdate(BaseModel):
    """Input model for updating an incident. All fields optional."""

    incident_date: date | None = Field(None)
    incident_time: str | None = Field(None)
    location: str | None = Field(None, min_length=2, max_length=512)
    severity: IncidentSeverity | None = Field(None)
    description: str | None = Field(None, min_length=10, max_length=5000)
    status: IncidentStatus | None = Field(None)
    persons_involved: str | None = Field(None, max_length=2000)
    witnesses: str | None = Field(None, max_length=2000)
    immediate_actions_taken: str | None = Field(None, max_length=2000)
    root_cause: str | None = Field(None, max_length=2000)
    corrective_actions: str | None = Field(None, max_length=2000)
    voice_transcript: str | None = Field(None, max_length=5000)
    photo_urls: list[str] | None = Field(None)
    osha_recordable: bool | None = Field(None)
    osha_reportable: bool | None = Field(None)


class Incident(IncidentCreate):
    """Full incident model with ID and audit fields."""

    id: str
    company_id: str
    status: IncidentStatus = IncidentStatus.REPORTED
    osha_recordable: bool = False
    osha_reportable: bool = False
    ai_analysis: dict = Field(default_factory=dict, description="AI root cause analysis")
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class IncidentListResponse(BaseModel):
    """Response model for listing incidents."""

    incidents: list[Incident]
    total: int
