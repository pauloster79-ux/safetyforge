"""Pydantic models for project resource assignments (workers and equipment)."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Type of resource being assigned to a project."""

    WORKER = "worker"
    EQUIPMENT = "equipment"


class AssignmentStatus(str, Enum):
    """Status of a project assignment."""

    ACTIVE = "active"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"


class ProjectAssignmentCreate(BaseModel):
    """Input model for creating a project assignment."""

    resource_type: ResourceType = Field(..., description="Type of resource: worker or equipment")
    resource_id: str = Field(
        ..., min_length=1, max_length=128, description="ID of the worker or equipment"
    )
    project_id: str = Field(
        ..., min_length=1, max_length=128, description="ID of the project"
    )
    role: str | None = Field(
        None, max_length=128,
        description="Role on project, e.g. foreman, crane_operator, scaffold_system",
    )
    start_date: date = Field(..., description="Assignment start date")
    end_date: date | None = Field(None, description="Assignment end date (None = still assigned)")
    status: AssignmentStatus = Field(
        default=AssignmentStatus.ACTIVE, description="Assignment status"
    )
    notes: str | None = Field(None, max_length=2000, description="Additional notes")


class ProjectAssignmentUpdate(BaseModel):
    """Input model for updating an assignment. All fields optional."""

    role: str | None = Field(None, max_length=128)
    start_date: date | None = None
    end_date: date | None = None
    status: AssignmentStatus | None = None
    notes: str | None = Field(None, max_length=2000)


class ProjectAssignment(BaseModel):
    """Full project assignment model with ID and audit fields."""

    id: str
    company_id: str
    resource_type: ResourceType
    resource_id: str
    project_id: str
    role: str | None = None
    start_date: date
    end_date: date | None = None
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    notes: str | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class ProjectAssignmentListResponse(BaseModel):
    """Response model for listing project assignments."""

    assignments: list[ProjectAssignment]
    total: int
