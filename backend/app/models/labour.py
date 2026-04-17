"""Pydantic models for Labour — discrete labour tasks within WorkItems."""

from datetime import datetime

from pydantic import BaseModel, Field


class LabourCreate(BaseModel):
    """Input model for creating a labour task."""

    task: str = Field(..., min_length=2, max_length=512, description="What the labour task is")
    rate_cents: int = Field(..., ge=0, description="Hourly rate in cents")
    hours: float = Field(..., gt=0, description="Estimated hours")
    notes: str = Field(default="", max_length=2000, description="Additional notes")


class LabourUpdate(BaseModel):
    """Input model for updating a labour task. All fields optional.

    Source-cascade provenance fields (rate_source_*, productivity_source_*,
    source_reasoning) can be updated to reflect where the rate/productivity
    estimate came from.
    """

    task: str | None = Field(None, min_length=2, max_length=512)
    rate_cents: int | None = Field(None, ge=0)
    hours: float | None = Field(None, gt=0)
    notes: str | None = Field(None, max_length=2000)
    # -- Source cascade provenance --
    rate_source_id: str | None = Field(
        None, max_length=64, description="Points to a ResourceRate ID"
    )
    rate_source_type: str | None = Field(
        None,
        max_length=64,
        description=(
            "One of 'resource_rate', 'contractor_stated', "
            "'inherited_from_similar_project'"
        ),
    )
    productivity_source_id: str | None = Field(
        None,
        max_length=64,
        description=(
            "Points to ProductivityRate, Insight, or IndustryProductivityBaseline"
        ),
    )
    productivity_source_type: str | None = Field(
        None,
        max_length=64,
        description=(
            "One of 'productivity_rate', 'insight', 'industry_baseline', "
            "'contractor_estimate'"
        ),
    )
    source_reasoning: str | None = Field(
        None,
        max_length=2000,
        description="Human-readable explanation (e.g. 'From your Peachtree job, Mar 2026')",
    )


class Labour(LabourCreate):
    """Full labour model with ID, computed cost, and audit fields."""

    id: str
    work_item_id: str
    cost_cents: int = Field(description="rate_cents * hours, in cents")
    # -- Source cascade provenance (set via MCP tools / estimating agents) --
    rate_source_id: str | None = None
    rate_source_type: str | None = None
    productivity_source_id: str | None = None
    productivity_source_type: str | None = None
    source_reasoning: str | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class LabourListResponse(BaseModel):
    """Response model for listing labour tasks."""

    labour: list[Labour]
    total: int
