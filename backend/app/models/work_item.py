"""Pydantic models for WorkItem — discrete scope items within a Project."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkItemState(str, Enum):
    """Lifecycle state of a work item."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    INVOICED = "invoiced"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class WorkItemUpdate(BaseModel):
    """Input model for updating a work item. All fields optional."""

    description: str | None = Field(None, min_length=2, max_length=2000)
    quantity: float | None = Field(None, gt=0)
    unit: str | None = Field(None, min_length=1, max_length=32)
    margin_pct: float | None = Field(None, ge=0, le=500)
    notes: str | None = Field(None, max_length=4000)
    planned_start: date | None = None
    planned_end: date | None = None


class WorkItem(BaseModel):
    """Full work item model with computed totals and audit fields."""

    id: str
    project_id: str
    company_id: str
    description: str
    state: str
    quantity: float
    unit: str
    margin_pct: float
    labour_total_cents: int = 0
    items_total_cents: int = 0
    sell_price_cents: float = 0
    is_alternate: bool = False
    alternate_label: str | None = None
    alternate_description: str | None = None
    alternate_price_adjustment_cents: int | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    actual_start: date | None = None
    actual_end: date | None = None
    notes: str | None = None
    deleted: bool = False
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
