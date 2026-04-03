"""Pydantic models for billing and subscriptions."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Paddle webhook event types we handle."""

    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELED = "subscription.canceled"
    SUBSCRIPTION_PAUSED = "subscription.paused"
    SUBSCRIPTION_RESUMED = "subscription.resumed"
    TRANSACTION_COMPLETED = "transaction.completed"
    TRANSACTION_PAYMENT_FAILED = "transaction.payment_failed"


class SubscriptionInfo(BaseModel):
    """Subscription status information returned to the frontend."""

    company_id: str
    status: str = Field(..., description="Current subscription status")
    plan_name: str = Field(default="Free", description="Current plan name")
    documents_used_this_month: int = Field(
        default=0, description="Documents generated in the current billing period"
    )
    documents_limit: int | None = Field(
        default=3,
        description="Monthly document limit. None means unlimited.",
    )
    current_period_end: datetime | None = Field(
        default=None, description="End of the current billing period"
    )
    cancel_at_period_end: bool = Field(
        default=False, description="Whether the subscription cancels at period end"
    )


class PaddleWebhookPayload(BaseModel):
    """Paddle webhook notification payload."""

    event_type: str = Field(..., description="Paddle event type (dot notation)")
    notification_id: str = Field(..., description="Unique notification ID for idempotency")
    data: dict = Field(..., description="Webhook event data")
    occurred_at: str = Field(..., description="ISO 8601 timestamp of when the event occurred")
