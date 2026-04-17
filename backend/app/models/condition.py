"""Pydantic models for Condition — contract conditions and prerequisites."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ConditionCategory(str, Enum):
    """Type of contract condition."""

    SITE_ACCESS = "site_access"
    WORKING_HOURS = "working_hours"
    PERMITS = "permits"
    MATERIALS = "materials"
    CLIENT_OBLIGATIONS = "client_obligations"
    INSURANCE = "insurance"
    OTHER = "other"


class ConditionCreate(BaseModel):
    """Input model for creating a condition."""

    category: ConditionCategory = Field(..., description="Category of this condition")
    description: str = Field(
        ..., min_length=2, max_length=2000, description="Description of the condition"
    )
    responsible_party: str | None = Field(
        None, max_length=256, description="Who is responsible for fulfilling this condition"
    )


class ConditionUpdate(BaseModel):
    """Input model for updating a condition. All fields optional."""

    category: ConditionCategory | None = None
    description: str | None = Field(None, min_length=2, max_length=2000)
    responsible_party: str | None = Field(None, max_length=256)


class Condition(BaseModel):
    """Full condition model with ID and audit fields."""

    id: str
    contract_id: str
    category: ConditionCategory
    description: str
    responsible_party: str | None = None
    created_at: datetime
    created_by: str
    actor_type: str = "human"
    updated_at: datetime
    updated_by: str
    updated_actor_type: str = "human"


class ConditionListResponse(BaseModel):
    """Response model for listing conditions."""

    conditions: list[Condition]
    total: int
