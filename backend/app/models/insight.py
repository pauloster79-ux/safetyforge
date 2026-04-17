"""Pydantic models for Insight — contractor-specific learned adjustments.

Insights capture knowledge a contractor has developed across projects: "add
15% to rough-in hours for low-ceiling renovations", "use crew-of-2 for
sub-500sf jobs", and similar qualitative or quantitative adjustments.
They feed the Layer 3 source cascade for estimating.

Graph model: (Company)-[:HAS_INSIGHT]->(Insight)
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InsightScope(str, Enum):
    """What dimension of context this insight applies to."""

    WORK_TYPE = "work_type"
    TRADE = "trade"
    JURISDICTION = "jurisdiction"
    CLIENT_TYPE = "client_type"
    PROJECT_SIZE = "project_size"
    OTHER = "other"


class InsightCreate(BaseModel):
    """Input model for creating an insight."""

    scope: InsightScope = Field(..., description="Dimension this insight scopes to")
    scope_value: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Concrete value for the scope (e.g. 'low_ceiling_renovation')",
    )
    statement: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Human-readable insight (e.g. 'Add 15% to rough-in hours')",
    )
    adjustment_type: str = Field(
        ...,
        max_length=64,
        description=(
            "Kind of adjustment: 'productivity_multiplier', 'rate_adjustment', "
            "or 'qualitative'"
        ),
    )
    adjustment_value: float | None = Field(
        None, description="Numeric adjustment value where applicable (e.g. 1.15)"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence the insight holds (0-1)"
    )
    source_context: str | None = Field(
        None,
        max_length=512,
        description="Where the insight came from (e.g. a conversation_id)",
    )


class InsightUpdate(BaseModel):
    """Input model for updating an insight. All fields optional."""

    scope: InsightScope | None = None
    scope_value: str | None = Field(None, min_length=1, max_length=256)
    statement: str | None = Field(None, min_length=3, max_length=2000)
    adjustment_type: str | None = Field(None, max_length=64)
    adjustment_value: float | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    source_context: str | None = Field(None, max_length=512)
    validation_count: int | None = Field(None, ge=0)
    last_applied_at: datetime | None = None


class Insight(BaseModel):
    """Full insight model with ID and audit fields."""

    id: str
    company_id: str
    scope: InsightScope
    scope_value: str
    statement: str
    adjustment_type: str
    adjustment_value: float | None = None
    confidence: float = 0.5
    source_context: str | None = None
    validation_count: int = 0
    last_applied_at: datetime | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class InsightListResponse(BaseModel):
    """Response model for listing insights."""

    insights: list[Insight]
    total: int
