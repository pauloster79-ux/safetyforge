"""Pydantic models for toolbox talk delivery and attendance."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ToolboxTalkStatus(str, Enum):
    """Toolbox talk lifecycle status."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Attendee(BaseModel):
    """A worker who attended the toolbox talk."""

    worker_name: str = Field(..., min_length=1, max_length=128, description="Name of the attendee")
    worker_id: str | None = Field(None, description="Worker ID if linked to a worker record")
    signature_data: str = Field(default="", description="Base64 encoded signature or empty")
    signed_at: datetime | None = Field(None, description="Timestamp when the attendee signed")
    language_preference: str = Field(default="en", description="Language preference: en or es")


class ToolboxTalkCreate(BaseModel):
    """Input model for creating a new toolbox talk."""

    topic: str = Field(..., min_length=2, max_length=256, description="Talk topic")
    scheduled_date: date = Field(..., description="Scheduled date for the talk")
    target_audience: str = Field(
        default="all_workers",
        description="Target audience: all_workers, new_hires, supervisors, specific_trade",
    )
    target_trade: str | None = Field(
        None, description="Target trade if target_audience is specific_trade"
    )
    duration_minutes: int = Field(
        default=15, ge=5, le=60, description="Duration in minutes"
    )
    custom_points: str = Field(
        default="", max_length=5000, description="Optional custom talking points"
    )
    generate_content: bool = Field(
        default=True, description="Whether to AI-generate the talk content"
    )
    language: str = Field(
        default="en", description="Primary language: en, es, or both"
    )


class ToolboxTalkUpdate(BaseModel):
    """Input model for updating a toolbox talk. All fields optional."""

    topic: str | None = Field(None, min_length=2, max_length=256)
    content_en: dict | None = None
    content_es: dict | None = None
    status: ToolboxTalkStatus | None = None
    overall_notes: str | None = Field(None, max_length=5000)


class ToolboxTalk(BaseModel):
    """Full toolbox talk model with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    topic: str
    scheduled_date: date
    target_audience: str
    target_trade: str | None = None
    duration_minutes: int
    custom_points: str = ""
    content_en: dict = Field(default_factory=dict)
    content_es: dict = Field(default_factory=dict)
    status: ToolboxTalkStatus = ToolboxTalkStatus.SCHEDULED
    attendees: list[Attendee] = Field(default_factory=list)
    overall_notes: str = ""
    presented_at: datetime | None = None
    presented_by: str = ""
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class ToolboxTalkListResponse(BaseModel):
    """Response model for listing toolbox talks."""

    toolbox_talks: list[ToolboxTalk]
    total: int


class AttendeeCreate(BaseModel):
    """Input model for adding an attendee to a toolbox talk."""

    worker_name: str = Field(..., min_length=1, max_length=128, description="Name of the attendee")
    worker_id: str | None = Field(None, description="Worker ID if linked to a worker record")
    signature_data: str = Field(default="", description="Base64 encoded signature or empty")
    language_preference: str = Field(default="en", description="Language preference: en or es")


class CompleteTalkRequest(BaseModel):
    """Input model for completing a toolbox talk."""

    presented_by: str = Field(..., min_length=1, max_length=128, description="Name of the presenter")
    notes: str = Field(default="", max_length=5000, description="Overall notes from the talk")


class GenerateContentRequest(BaseModel):
    """Input model for generating/regenerating talk content."""

    language: str = Field(default="both", description="Language to generate: en, es, or both")
