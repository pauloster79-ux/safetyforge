"""Pydantic models for Warranty — warranty terms on Contracts."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class WarrantyStartTrigger(str, Enum):
    """What event triggers the warranty period start."""

    PRACTICAL_COMPLETION = "practical_completion"
    HANDOVER = "handover"
    OTHER = "other"


class WarrantyCreate(BaseModel):
    """Input model for creating or upserting a warranty."""

    period_months: int = Field(
        ..., ge=1, le=120, description="Warranty duration in months"
    )
    scope: str = Field(
        ..., min_length=2, max_length=2000, description="What the warranty covers"
    )
    start_trigger: WarrantyStartTrigger = Field(
        default=WarrantyStartTrigger.PRACTICAL_COMPLETION,
        description="Event that starts the warranty period",
    )
    terms: str | None = Field(
        None, max_length=5000, description="Additional warranty terms and conditions"
    )


class WarrantyUpdate(BaseModel):
    """Input model for updating a warranty. All fields optional."""

    period_months: int | None = Field(None, ge=1, le=120)
    scope: str | None = Field(None, min_length=2, max_length=2000)
    start_trigger: WarrantyStartTrigger | None = None
    terms: str | None = Field(None, max_length=5000)


class Warranty(BaseModel):
    """Full warranty model with ID and audit fields."""

    id: str
    contract_id: str
    period_months: int
    scope: str
    start_trigger: WarrantyStartTrigger = WarrantyStartTrigger.PRACTICAL_COMPLETION
    terms: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime
    created_by: str
    actor_type: str = "human"
    updated_at: datetime
    updated_by: str
    updated_actor_type: str = "human"
