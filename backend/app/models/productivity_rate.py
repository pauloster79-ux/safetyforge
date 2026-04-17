"""Pydantic models for ProductivityRate — company productivity knowledge."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProductivityTimeUnit(str, Enum):
    """Time period for productivity rates."""

    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_WEEK = "per_week"


class ProductivitySource(str, Enum):
    """How the productivity rate was established."""

    MANUAL_ENTRY = "manual_entry"
    DERIVED_FROM_ACTUALS = "derived_from_actuals"


class ProductivityRateCreate(BaseModel):
    """Input model for creating a productivity rate."""

    description: str = Field(
        ..., min_length=2, max_length=512,
        description="Human-readable description (e.g. 'EMT conduit in commercial drop ceiling')",
    )
    rate: float = Field(..., gt=0, description="Output per unit of time")
    rate_unit: str = Field(
        ..., max_length=20, description="Unit of output (LF, SF, CY, EA, etc.)"
    )
    time_unit: ProductivityTimeUnit = Field(
        ..., description="Time period for the rate"
    )
    crew_composition: str = Field(
        default="", max_length=256, description="Typical crew makeup"
    )
    conditions: str = Field(
        default="", max_length=512, description="When this rate applies"
    )
    source: ProductivitySource = Field(
        default=ProductivitySource.MANUAL_ENTRY, description="How rate was established"
    )
    includes_non_productive: bool = Field(
        default=False, description="Whether non-productive time is baked in"
    )


class ProductivityRateUpdate(BaseModel):
    """Input model for updating a productivity rate. All fields optional."""

    description: str | None = Field(None, min_length=2, max_length=512)
    rate: float | None = Field(None, gt=0)
    rate_unit: str | None = Field(None, max_length=20)
    time_unit: ProductivityTimeUnit | None = None
    crew_composition: str | None = Field(None, max_length=256)
    conditions: str | None = Field(None, max_length=512)
    source: ProductivitySource | None = None
    includes_non_productive: bool | None = None
    active: bool | None = None


class ProductivityRate(BaseModel):
    """Full productivity rate model with ID and audit fields."""

    id: str
    company_id: str
    description: str
    rate: float
    rate_unit: str
    time_unit: ProductivityTimeUnit
    crew_composition: str = ""
    conditions: str = ""
    source: ProductivitySource
    sample_size: int | None = None
    std_deviation: float | None = None
    includes_non_productive: bool = False
    last_derived_at: datetime | None = None
    active: bool = True
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class ProductivityRateListResponse(BaseModel):
    """Response model for listing productivity rates."""

    rates: list[ProductivityRate]
    total: int
