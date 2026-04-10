"""Guardrails models — action classification and approval queue.

Implements the action taxonomy from AGENTIC_ARCHITECTURE.md §5:
- read-only: always allow
- low-risk write: allow with audit trail, rate-limited
- high-risk write: require human approval
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionClass(str, Enum):
    """Risk classification for agent operations."""

    READ_ONLY = "read_only"
    LOW_RISK_WRITE = "low_risk_write"
    HIGH_RISK_WRITE = "high_risk_write"


class ApprovalStatus(str, Enum):
    """Status of a high-risk write approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """A queued request for human approval of a high-risk agent action.

    Attributes:
        request_id: Unique request identifier.
        agent_id: The agent requesting the action.
        agent_name: Human-readable agent name.
        company_id: Tenant scope.
        tool_name: The MCP tool being invoked.
        action_class: Always HIGH_RISK_WRITE.
        parameters: Tool invocation parameters.
        reasoning: Agent's explanation of why this action is needed.
        confidence: Agent's declared confidence (0.0-1.0).
        evidence: Supporting evidence from graph traversals.
        status: Current approval status.
        created_at: When the request was created.
        reviewed_by: User ID of the reviewer (once reviewed).
        reviewed_at: When the review happened.
        review_comment: Reviewer's comment.
        timeout_hours: Hours before the request auto-expires.
    """

    request_id: str
    agent_id: str
    agent_name: str = ""
    company_id: str
    tool_name: str
    action_class: ActionClass = ActionClass.HIGH_RISK_WRITE
    parameters: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    confidence: float | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_comment: str | None = None
    timeout_hours: int = 24


class GuardrailCheckResult(BaseModel):
    """Result of a pre-execution guardrail check.

    Attributes:
        allowed: Whether the action is allowed to proceed.
        action_class: The determined action classification.
        reason: Human-readable reason if denied.
        approval_request_id: If queued for approval, the request ID.
        rate_limit_remaining: Remaining calls in the current window.
    """

    allowed: bool
    action_class: ActionClass
    reason: str = ""
    approval_request_id: str | None = None
    rate_limit_remaining: int | None = None
