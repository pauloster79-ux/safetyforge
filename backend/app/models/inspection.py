"""Pydantic models for daily inspection logs."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class InspectionType(str, Enum):
    """Available inspection types."""

    DAILY_SITE = "daily_site"
    SCAFFOLD = "scaffold"
    EXCAVATION = "excavation"
    ELECTRICAL = "electrical"
    FALL_PROTECTION = "fall_protection"
    HOUSEKEEPING = "housekeeping"
    EQUIPMENT = "equipment"
    FIRE_SAFETY = "fire_safety"


class InspectionStatus(str, Enum):
    """Overall inspection result status."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class InspectionItem(BaseModel):
    """Single checklist item within an inspection."""

    item_id: str = Field(..., description="Unique item identifier within the checklist")
    category: str = Field(..., description="Category, e.g. PPE, Fall Protection, Housekeeping")
    description: str = Field(..., description="What to inspect")
    status: str = Field(..., description="Item result: pass, fail, or na")
    notes: str = Field(default="", description="Inspector notes for this item")
    photo_url: str | None = Field(None, description="URL to attached photo evidence")


class InspectionCreate(BaseModel):
    """Input model for creating a new inspection."""

    inspection_type: InspectionType = Field(..., description="Type of inspection")
    inspection_date: date = Field(..., description="Date of inspection")
    inspector_name: str = Field(
        ..., min_length=2, max_length=128, description="Name of the inspector"
    )
    weather_conditions: str = Field(
        default="", max_length=256, description="Weather conditions at time of inspection"
    )
    temperature: str = Field(default="", max_length=50, description="Temperature reading")
    wind_conditions: str = Field(
        default="", max_length=256, description="Wind conditions"
    )
    workers_on_site: int = Field(
        default=0, ge=0, description="Number of workers on site during inspection"
    )
    items: list[InspectionItem] = Field(
        default_factory=list, description="Checklist items"
    )
    overall_notes: str = Field(
        default="", max_length=5000, description="General inspection notes"
    )
    corrective_actions_needed: str = Field(
        default="", max_length=5000, description="Corrective actions required"
    )
    gps_latitude: float | None = Field(None, description="GPS latitude of inspection")
    gps_longitude: float | None = Field(None, description="GPS longitude of inspection")


class InspectionUpdate(BaseModel):
    """Input model for updating an inspection. All fields optional."""

    inspection_type: InspectionType | None = None
    inspection_date: date | None = None
    inspector_name: str | None = Field(None, min_length=2, max_length=128)
    weather_conditions: str | None = Field(None, max_length=256)
    temperature: str | None = Field(None, max_length=50)
    wind_conditions: str | None = Field(None, max_length=256)
    workers_on_site: int | None = Field(None, ge=0)
    items: list[InspectionItem] | None = None
    overall_notes: str | None = Field(None, max_length=5000)
    corrective_actions_needed: str | None = Field(None, max_length=5000)
    gps_latitude: float | None = None
    gps_longitude: float | None = None


class Inspection(InspectionCreate):
    """Full inspection model with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    overall_status: InspectionStatus = Field(
        ..., description="Calculated from items: pass, fail, or partial"
    )
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class InspectionListResponse(BaseModel):
    """Response model for listing inspections."""

    inspections: list[Inspection]
    total: int
