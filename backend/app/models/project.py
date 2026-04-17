"""Pydantic models for construction projects."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectState(str, Enum):
    """Project lifecycle stage."""

    LEAD = "lead"
    QUOTED = "quoted"
    ACTIVE = "active"
    COMPLETED = "completed"
    CLOSED = "closed"
    LOST = "lost"


class ProjectStatus(str, Enum):
    """Project operating condition within the current state."""

    NORMAL = "normal"
    ON_HOLD = "on_hold"
    DELAYED = "delayed"
    SUSPENDED = "suspended"


class EstimateConfidence(str, Enum):
    """Class of estimate accuracy."""

    CONCEPT = "concept"
    BUDGET = "budget"
    DEFINITIVE = "definitive"


class ContractType(str, Enum):
    """Type of contract governing the project."""

    LUMP_SUM = "lump_sum"
    SCHEDULE_OF_RATES = "schedule_of_rates"
    COST_PLUS = "cost_plus"
    TIME_AND_MATERIALS = "time_and_materials"


class ProjectCreate(BaseModel):
    """Input model for creating a new project."""

    name: str = Field(..., min_length=2, max_length=256, description="Project name")
    address: str = Field(..., min_length=5, max_length=512, description="Site address")
    city: str | None = Field(None, max_length=128, description="City")
    us_state: str | None = Field(
        None,
        max_length=64,
        description=(
            "US state or equivalent jurisdiction subdivision. Named ``us_state`` to "
            "avoid colliding with the existing ``state`` (ProjectState lifecycle) field."
        ),
    )
    region: str | None = Field(
        None, max_length=128, description="Metro area or region (e.g. 'Atlanta, GA', 'Bay Area')"
    )
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
    estimate_confidence: EstimateConfidence | None = Field(
        None, description="Class of estimate accuracy"
    )
    target_margin_percent: float | None = Field(
        None, ge=0, le=100, description="Target margin percentage"
    )
    contract_type: ContractType | None = Field(
        None, description="Type of contract"
    )


class ProjectUpdate(BaseModel):
    """Input model for updating a project. All fields optional."""

    name: str | None = Field(None, min_length=2, max_length=256)
    address: str | None = Field(None, min_length=5, max_length=512)
    city: str | None = Field(None, max_length=128)
    # NB: `state` below is the project lifecycle state (ProjectState).
    # The US-state-or-equivalent jurisdiction field uses `us_state` on this
    # update model to avoid colliding with the existing lifecycle field.
    us_state: str | None = Field(
        None, max_length=64, description="US state or jurisdiction subdivision"
    )
    region: str | None = Field(None, max_length=128)
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
    state: ProjectState | None = Field(None)
    status: ProjectStatus | None = Field(None)
    estimate_confidence: EstimateConfidence | None = None
    target_margin_percent: float | None = Field(None, ge=0, le=100)
    contract_type: ContractType | None = None
    quote_valid_until: date | None = None
    quote_submitted_at: datetime | None = None


class Project(ProjectCreate):
    """Full project model with ID and audit fields."""

    id: str
    company_id: str
    state: ProjectState = ProjectState.LEAD
    status: ProjectStatus = ProjectStatus.NORMAL
    compliance_score: int = Field(default=0, ge=0, le=100, description="Calculated compliance score")
    quote_valid_until: date | None = None
    quote_submitted_at: datetime | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""

    projects: list[Project]
    total: int
