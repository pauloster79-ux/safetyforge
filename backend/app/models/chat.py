"""Chat models for the conversational AI interface.

Supports two modes:
- 'general': Open-ended queries against the knowledge graph
- 'inspection': Guided inspection flow with checklist state
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message author role"
    )
    content: str = Field(default="", description="Text content of the message")
    tool_calls: list[dict[str, Any]] | None = Field(
        None, description="Tool use blocks from assistant"
    )
    tool_results: list[dict[str, Any]] | None = Field(
        None, description="Tool result blocks"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    session_id: str | None = Field(
        None, description="Session ID for conversation continuity. Auto-generated if missing."
    )
    message: str = Field(..., min_length=1, description="User message text")
    company_id: str = Field(..., description="Tenant scope")
    project_id: str | None = Field(
        None, description="Project context (required for inspection mode)"
    )
    mode: Literal["general", "inspection"] = Field(
        default="general", description="Chat mode"
    )
    inspection_type: str | None = Field(
        None, description="Inspection type for inspection mode (e.g. 'daily_site')"
    )


class ChatEvent(BaseModel):
    """Server-Sent Event payload for streaming chat responses."""

    type: Literal[
        "text_delta",
        "tool_call",
        "tool_result",
        "inspection_progress",
        "done",
        "error",
    ] = Field(..., description="Event type for frontend routing")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")


class InspectionChatState(BaseModel):
    """In-memory state for an active inspection conversation."""

    template_items: list[dict[str, Any]] = Field(
        default_factory=list, description="Full checklist template"
    )
    responses: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="item_id -> {status, notes}"
    )
    current_index: int = Field(default=0, description="Index of current checklist item")
    inspection_type: str = Field(..., description="e.g. 'daily_site'")
    project_id: str = Field(..., description="Project being inspected")
    inspector_name: str = Field(default="", description="Name of the inspector")
    completed: bool = Field(default=False, description="Whether the inspection is done")


class ChatSession(BaseModel):
    """In-memory conversation session."""

    session_id: str
    messages: list[dict[str, Any]] = Field(
        default_factory=list, description="Anthropic messages array"
    )
    mode: Literal["general", "inspection"] = "general"
    inspection_state: InspectionChatState | None = None
    company_id: str = ""
    project_id: str | None = None
    user_id: str = ""
    conversation_id: str | None = Field(
        None, description="Neo4j Conversation node ID for persistence"
    )
    last_message_id: str | None = Field(
        None, description="ID of the last persisted Message node (for FOLLOWS chain)"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_active: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
