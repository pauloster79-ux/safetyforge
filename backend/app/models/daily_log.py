"""Pydantic models for construction daily logs."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DailyLogStatus(str, Enum):
    """Daily log workflow status."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"


class WeatherData(BaseModel):
    """Weather conditions for a daily log."""

    conditions: str = Field(
        default="", max_length=256, description="General conditions (sunny, cloudy, rain)"
    )
    temperature_high: str = Field(default="", max_length=50)
    temperature_low: str = Field(default="", max_length=50)
    wind: str = Field(default="", max_length=256)
    precipitation: str = Field(default="", max_length=256)


class MaterialDelivery(BaseModel):
    """Material delivery record."""

    material: str = Field(..., min_length=1, max_length=256)
    quantity: str = Field(default="", max_length=128)
    supplier: str = Field(default="", max_length=256)
    received_by: str = Field(default="", max_length=128)
    notes: str = Field(default="", max_length=1000)


class DelayRecord(BaseModel):
    """Delay/disruption record."""

    delay_type: str = Field(..., description="weather, material, labor, equipment, other")
    duration_hours: float = Field(default=0, ge=0)
    description: str = Field(default="", max_length=2000)
    impact: str = Field(default="", max_length=1000)


class VisitorRecord(BaseModel):
    """Site visitor record."""

    name: str = Field(..., min_length=1, max_length=128)
    company: str = Field(default="", max_length=256)
    purpose: str = Field(default="", max_length=512)
    time_in: str = Field(default="", max_length=50)
    time_out: str = Field(default="", max_length=50)


class DailyLogCreate(BaseModel):
    """Input model for creating a daily log."""

    log_date: date = Field(..., description="Date this log covers")
    superintendent_name: str = Field(..., min_length=2, max_length=128)
    weather: WeatherData = Field(default_factory=WeatherData)
    workers_on_site: int = Field(default=0, ge=0)
    work_performed: str = Field(
        default="", max_length=10000, description="Description of work performed today"
    )
    materials_delivered: list[MaterialDelivery] = Field(default_factory=list)
    delays: list[DelayRecord] = Field(default_factory=list)
    visitors: list[VisitorRecord] = Field(default_factory=list)
    safety_incidents: str = Field(
        default="", max_length=5000, description="Safety incidents or near-misses"
    )
    equipment_used: str = Field(default="", max_length=5000)
    notes: str = Field(default="", max_length=10000)


class DailyLogUpdate(BaseModel):
    """Input model for updating a daily log. All fields optional."""

    superintendent_name: str | None = Field(None, min_length=2, max_length=128)
    weather: WeatherData | None = None
    workers_on_site: int | None = Field(None, ge=0)
    work_performed: str | None = Field(None, max_length=10000)
    materials_delivered: list[MaterialDelivery] | None = None
    delays: list[DelayRecord] | None = None
    visitors: list[VisitorRecord] | None = None
    safety_incidents: str | None = Field(None, max_length=5000)
    equipment_used: str | None = Field(None, max_length=5000)
    notes: str | None = Field(None, max_length=10000)


class DailyLog(DailyLogCreate):
    """Full daily log model with ID and audit fields."""

    id: str
    company_id: str
    project_id: str
    status: DailyLogStatus = DailyLogStatus.DRAFT
    # Auto-populated summaries from graph data
    inspections_summary: list[dict[str, Any]] = Field(default_factory=list)
    toolbox_talks_summary: list[dict[str, Any]] = Field(default_factory=list)
    incidents_summary: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    submitted_at: str | None = None
    submitted_by: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    deleted: bool = False


class DailyLogListResponse(BaseModel):
    """Response model for listing daily logs."""

    daily_logs: list[DailyLog]
    total: int
