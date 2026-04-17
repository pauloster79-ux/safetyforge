"""Pydantic models for PaymentMilestone — payment schedule items on Contracts."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PaymentMilestoneStatus(str, Enum):
    """Payment milestone lifecycle status."""

    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"


class PaymentMilestoneCreate(BaseModel):
    """Input model for creating a payment milestone."""

    description: str = Field(
        ..., min_length=2, max_length=1000, description="Description of this milestone"
    )
    percentage: float | None = Field(
        None, ge=0, le=100, description="Percentage of contract value"
    )
    fixed_amount_cents: int | None = Field(
        None, ge=0, description="Fixed amount in cents"
    )
    trigger_condition: str = Field(
        ..., min_length=2, max_length=1000,
        description="Condition that triggers this milestone payment",
    )
    sort_order: int = Field(default=0, ge=0, description="Display ordering")

    @model_validator(mode="after")
    def exactly_one_amount(self) -> "PaymentMilestoneCreate":
        """Ensure exactly one of percentage or fixed_amount_cents is provided."""
        has_pct = self.percentage is not None
        has_fixed = self.fixed_amount_cents is not None
        if has_pct == has_fixed:
            raise ValueError(
                "Exactly one of 'percentage' or 'fixed_amount_cents' must be provided"
            )
        return self


class PaymentMilestoneUpdate(BaseModel):
    """Input model for updating a payment milestone. All fields optional."""

    description: str | None = Field(None, min_length=2, max_length=1000)
    percentage: float | None = Field(None, ge=0, le=100)
    fixed_amount_cents: int | None = Field(None, ge=0)
    trigger_condition: str | None = Field(None, min_length=2, max_length=1000)
    sort_order: int | None = Field(None, ge=0)
    status: PaymentMilestoneStatus | None = None


class PaymentMilestone(BaseModel):
    """Full payment milestone model with ID and audit fields."""

    id: str
    contract_id: str
    description: str
    percentage: float | None = None
    fixed_amount_cents: int | None = None
    trigger_condition: str
    sort_order: int = 0
    status: PaymentMilestoneStatus = PaymentMilestoneStatus.PENDING
    created_at: datetime
    created_by: str
    actor_type: str = "human"
    updated_at: datetime
    updated_by: str
    updated_actor_type: str = "human"


class PaymentMilestoneListResponse(BaseModel):
    """Response model for listing payment milestones."""

    milestones: list[PaymentMilestone]
    total: int
