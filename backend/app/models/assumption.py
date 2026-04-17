"""Pydantic models for Assumption — structured qualifications on quotes."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AssumptionCategory(str, Enum):
    """Type of assumption."""

    SCHEDULE = "schedule"
    QUANTITIES = "quantities"
    ACCESS = "access"
    COORDINATION = "coordination"
    SITE_CONDITIONS = "site_conditions"
    DESIGN_COMPLETENESS = "design_completeness"
    PRICING = "pricing"
    REGULATORY = "regulatory"


class AssumptionStatus(str, Enum):
    """Assumption lifecycle status."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    VOID = "void"


class AssumptionCreate(BaseModel):
    """Input model for creating an assumption."""

    category: AssumptionCategory = Field(..., description="Type of assumption")
    statement: str = Field(
        ..., min_length=5, max_length=2000, description="Human-readable assumption text"
    )
    relied_on_value: str = Field(
        default="", max_length=256, description="The specific value relied upon"
    )
    relied_on_unit: str = Field(
        default="", max_length=64, description="Unit for the value"
    )
    source_document: str = Field(
        default="", max_length=512, description="Document the assumption references"
    )
    variation_trigger: bool = Field(
        default=False, description="Whether violation triggers a potential variation"
    )
    trigger_description: str = Field(
        default="", max_length=1000, description="What condition would violate this assumption"
    )
    trade_type: str = Field(
        default="", max_length=64, description="Which trade this applies to"
    )
    sort_order: int = Field(default=0, ge=0, description="Display ordering")


class AssumptionUpdate(BaseModel):
    """Input model for updating an assumption. All fields optional."""

    category: AssumptionCategory | None = None
    statement: str | None = Field(None, min_length=5, max_length=2000)
    relied_on_value: str | None = Field(None, max_length=256)
    relied_on_unit: str | None = Field(None, max_length=64)
    source_document: str | None = Field(None, max_length=512)
    variation_trigger: bool | None = None
    trigger_description: str | None = Field(None, max_length=1000)
    trade_type: str | None = Field(None, max_length=64)
    sort_order: int | None = Field(None, ge=0)
    status: AssumptionStatus | None = None


class Assumption(BaseModel):
    """Full assumption model with ID and audit fields."""

    id: str
    project_id: str
    category: AssumptionCategory
    statement: str
    relied_on_value: str = ""
    relied_on_unit: str = ""
    source_document: str = ""
    variation_trigger: bool = False
    trigger_description: str = ""
    is_template: bool = False
    trade_type: str = ""
    status: AssumptionStatus = AssumptionStatus.ACTIVE
    triggered_at: datetime | None = None
    triggered_by_event: str | None = None
    sort_order: int = 0
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class AssumptionTemplate(BaseModel):
    """Company-level assumption template."""

    id: str
    company_id: str
    category: AssumptionCategory
    statement: str
    relied_on_value: str = ""
    relied_on_unit: str = ""
    source_document: str = ""
    variation_trigger: bool = False
    trigger_description: str = ""
    trade_type: str = ""
    sort_order: int = 0
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class AssumptionListResponse(BaseModel):
    """Response model for listing assumptions."""

    assumptions: list[Assumption]
    total: int


class AssumptionTemplateListResponse(BaseModel):
    """Response model for listing assumption templates."""

    templates: list[AssumptionTemplate]
    total: int
