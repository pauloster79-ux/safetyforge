"""Pydantic models for audit events.

Every mutation and state transition on a tenant-scoped entity emits an
AuditEvent node. Events are append-only, linked to the affected entity
via (Entity)-[:EMITTED]->(AuditEvent). See docs/design/phase-0-foundations.md §3.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Kind of event recorded on a tenant-scoped entity."""

    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    STATE_TRANSITIONED = "state.transitioned"
    ENTITY_ARCHIVED = "entity.archived"
    FIELD_CHANGED = "field.changed"
    RELATIONSHIP_ADDED = "relationship.added"
    RELATIONSHIP_REMOVED = "relationship.removed"


class AuditEvent(BaseModel):
    """An immutable record of a mutation on a tenant-scoped entity."""

    id: str = Field(..., description="Unique event ID with prefix 'evt_'")
    event_type: EventType = Field(..., description="Kind of event")
    entity_id: str = Field(..., description="ID of the affected entity")
    entity_type: str = Field(..., description="Neo4j node label of the affected entity")
    company_id: str = Field(..., description="Tenant scope")
    occurred_at: datetime = Field(..., description="When the event occurred, UTC")

    # Actor provenance
    actor_type: Literal["human", "agent"] = Field(..., description="Human user or AI agent")
    actor_id: str = Field(..., description="User ID for humans, agent ID for agents")
    agent_id: str | None = Field(None, description="Agent ID (same as actor_id for agents)")
    agent_version: str | None = Field(None, description="Agent version, e.g. '1.2.0'")
    model_id: str | None = Field(None, description="Model used, e.g. 'claude-sonnet-4-6'")
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Agent self-reported confidence"
    )
    cost_cents: int | None = Field(None, ge=0, description="Token cost in cents, agents only")

    # Payload
    summary: str = Field(..., description="Human-readable one-line description")
    changes: dict[str, Any] | None = Field(
        None, description='Shape: { "field": { "from": X, "to": Y } }'
    )
    prev_state: str | None = Field(None, description="Previous state for state.transitioned")
    new_state: str | None = Field(None, description="New state for state.transitioned")

    # Causal chain
    caused_by_event_id: str | None = Field(None, description="Parent event in a causal chain")
    related_entity_ids: list[str] | None = Field(
        None, description="Additional entities referenced by this event"
    )


class ActivityStreamResponse(BaseModel):
    """Response model for an entity's activity stream."""

    events: list[AuditEvent]
    total: int
    has_more: bool
