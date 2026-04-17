"""Pydantic models for Exclusion — structured scope boundaries on quotes."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExclusionCategory(str, Enum):
    """Type of exclusion."""

    SCOPE = "scope"
    TRADE_BOUNDARY = "trade_boundary"
    CONDITIONS = "conditions"
    RISK = "risk"
    REGULATORY = "regulatory"


class ExclusionCreate(BaseModel):
    """Input model for creating an exclusion."""

    category: ExclusionCategory = Field(..., description="Type of exclusion")
    statement: str = Field(
        ..., min_length=5, max_length=2000, description="Human-readable exclusion text"
    )
    partial_inclusion: str = Field(
        default="", max_length=1000, description="What IS included despite the exclusion"
    )
    trade_type: str = Field(
        default="", max_length=64, description="Which trade this applies to"
    )
    source: str = Field(
        default="", max_length=512, description="Why this exclusion exists"
    )
    sort_order: int = Field(default=0, ge=0, description="Display ordering")


class ExclusionUpdate(BaseModel):
    """Input model for updating an exclusion. All fields optional."""

    category: ExclusionCategory | None = None
    statement: str | None = Field(None, min_length=5, max_length=2000)
    partial_inclusion: str | None = Field(None, max_length=1000)
    trade_type: str | None = Field(None, max_length=64)
    source: str | None = Field(None, max_length=512)
    sort_order: int | None = Field(None, ge=0)


class Exclusion(BaseModel):
    """Full exclusion model with ID and audit fields."""

    id: str
    project_id: str
    category: ExclusionCategory
    statement: str
    partial_inclusion: str = ""
    is_template: bool = False
    trade_type: str = ""
    source: str = ""
    sort_order: int = 0
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class ExclusionTemplate(BaseModel):
    """Company-level exclusion template."""

    id: str
    company_id: str
    category: ExclusionCategory
    statement: str
    partial_inclusion: str = ""
    trade_type: str = ""
    source: str = ""
    sort_order: int = 0
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class ExclusionListResponse(BaseModel):
    """Response model for listing exclusions."""

    exclusions: list[Exclusion]
    total: int


class ExclusionTemplateListResponse(BaseModel):
    """Response model for listing exclusion templates."""

    templates: list[ExclusionTemplate]
    total: int
