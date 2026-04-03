"""Pydantic models for construction projects."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class ProjectCreate(BaseModel):
    """Input model for creating a new project."""

    name: str = Field(..., min_length=2, max_length=256, description="Project name")
    address: str = Field(..., min_length=5, max_length=512, description="Site address")
    client_name: str = Field(default="", max_length=256, description="Client/owner name")
    project_type: str = Field(
        default="commercial",
        description="Project type: commercial, residential, industrial, infrastructure, renovation",
    )
    trade_types: list[str] = Field(
        default_factory=list, description="Trades active on this project"
    )
    start_date: date | None = Field(None, description="Project start date")
    end_date: date | None = Field(None, description="Project end date")
    estimated_workers: int = Field(
        default=0, ge=0, description="Estimated number of workers on site"
    )
    description: str = Field(default="", max_length=2000, description="Project description")
    special_hazards: str = Field(
        default="", max_length=2000, description="Special hazards on site"
    )
    nearest_hospital: str = Field(
        default="", max_length=256, description="Nearest hospital name and address"
    )
    emergency_contact_name: str = Field(
        default="", max_length=128, description="Emergency contact name"
    )
    emergency_contact_phone: str = Field(
        default="", max_length=20, description="Emergency contact phone"
    )


class ProjectUpdate(BaseModel):
    """Input model for updating a project. All fields optional."""

    name: str | None = Field(None, min_length=2, max_length=256)
    address: str | None = Field(None, min_length=5, max_length=512)
    client_name: str | None = Field(None, max_length=256)
    project_type: str | None = Field(None)
    trade_types: list[str] | None = Field(None)
    start_date: date | None = Field(None)
    end_date: date | None = Field(None)
    estimated_workers: int | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=2000)
    special_hazards: str | None = Field(None, max_length=2000)
    nearest_hospital: str | None = Field(None, max_length=256)
    emergency_contact_name: str | None = Field(None, max_length=128)
    emergency_contact_phone: str | None = Field(None, max_length=20)
    status: ProjectStatus | None = Field(None)


class Project(ProjectCreate):
    """Full project model with ID and audit fields."""

    id: str
    company_id: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    compliance_score: int = Field(default=0, ge=0, le=100, description="Calculated compliance score")
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""

    projects: list[Project]
    total: int
