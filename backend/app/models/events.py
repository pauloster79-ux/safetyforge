"""Event envelope models for the in-process event backbone.

Matches the event envelope spec in AGENTIC_ARCHITECTURE.md §4.
Coarse event types with rich summary payloads.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.actor import Actor


class EventType(str, Enum):
    """Coarse event types — entity.verb format."""

    INSPECTION_COMPLETED = "inspection.completed"
    INSPECTION_ITEM_FAILED = "inspection.item_failed"
    INCIDENT_REPORTED = "incident.reported"
    HAZARD_REPORTED = "hazard.reported"
    CERTIFICATION_EXPIRING = "certification.expiring"
    EQUIPMENT_INSPECTION_DUE = "equipment.inspection_due"
    WORKER_ASSIGNED = "worker.assigned_to_project"
    WORKER_REMOVED = "worker.removed_from_project"
    CORRECTIVE_ACTION_OVERDUE = "corrective_action.overdue"
    DOCUMENT_GENERATED = "document.generated"
    DAILY_LOG_SUBMITTED = "daily_log.submitted"
    DAILY_LOG_CREATED = "daily_log.created"
    TIME_ENTRY_RECORDED = "time_entry.recorded"
    QUALITY_OBSERVATION_REPORTED = "quality_observation.reported"
    VARIATION_CREATED = "variation.created"
    VARIATION_DETECTED = "variation.detected"
    WORK_ITEM_CREATED = "work_item.created"
    WORK_ITEM_UPDATED = "work_item.updated"
    INVOICE_CREATED = "invoice.created"
    PAYMENT_RECORDED = "payment.recorded"
    PROPOSAL_GENERATED = "proposal.generated"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    PROJECT_ACTUALS_READY = "project.actuals_ready"


class EventActor(BaseModel):
    """Actor who caused the event."""

    type: str = Field(..., description="'human' or 'agent'")
    id: str = Field(..., description="User UID or agent_id")
    agent_id: str | None = Field(None, description="Agent ID if actor is agent")

    @classmethod
    def from_actor(cls, actor: Actor) -> "EventActor":
        """Create from an Actor dataclass.

        Args:
            actor: The Actor who triggered the event.

        Returns:
            An EventActor instance.
        """
        return cls(type=actor.type, id=actor.id, agent_id=actor.agent_id)


class Event(BaseModel):
    """Event envelope matching AGENTIC_ARCHITECTURE.md §4.

    Attributes:
        event_id: Unique event identifier.
        event_type: Coarse event type (entity.verb).
        version: Schema version for this event type.
        entity_id: ID of the entity that changed.
        entity_type: Type label of the entity.
        project_id: Project context (if applicable).
        company_id: Tenant scope.
        actor: Who caused this event.
        timestamp: When the event occurred.
        summary: Rich summary payload — enough for consumers to decide relevance.
        graph_context: Pre-computed graph neighbourhood context.
    """

    event_id: str
    event_type: EventType
    version: str = "1.0"
    entity_id: str
    entity_type: str
    project_id: str | None = None
    company_id: str
    actor: EventActor
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    summary: dict[str, Any] = Field(default_factory=dict)
    graph_context: dict[str, Any] = Field(default_factory=dict)

    @property
    def idempotency_key(self) -> str:
        """Generate an idempotency key for this event.

        Returns:
            A string key combining event_id, entity_id, and event_type.
        """
        return f"{self.event_id}:{self.entity_id}:{self.event_type.value}"
