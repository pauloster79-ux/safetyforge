"""Pydantic models for AgentIdentity — AI agents registered to companies."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentType(str, Enum):
    """Agent category types."""

    COMPLIANCE = "compliance"
    BRIEFING = "briefing"
    INTAKE = "intake"
    FORECAST = "forecast"
    EXTERNAL = "external"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class ModelTier(str, Enum):
    """LLM model tier for cost control."""

    FAST = "fast"
    STANDARD = "standard"
    ADVANCED = "advanced"


class AgentIdentityCreate(BaseModel):
    """Input model for registering a new agent."""

    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(
        ..., min_length=2, max_length=128, description="Human-readable agent name"
    )
    agent_type: AgentType = Field(..., description="Agent category")
    scopes: list[str] = Field(
        ..., min_length=1, description="Permitted operation scopes"
    )
    model_tier: ModelTier = Field(
        default=ModelTier.STANDARD, description="Default model tier"
    )
    daily_budget_cents: int = Field(
        default=1000, ge=1, le=100000, description="Max daily LLM spend in cents"
    )

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: list[str]) -> list[str]:
        """Validate that all scopes follow the 'action:domain' format.

        Args:
            v: List of scope strings.

        Returns:
            The validated scope list.

        Raises:
            ValueError: If any scope is malformed.
        """
        valid_actions = {"read", "write"}
        valid_domains = {
            "safety", "workers", "inspections", "incidents",
            "hazards", "equipment", "documents", "projects",
            "compliance", "briefings", "environmental", "all",
        }
        for scope in v:
            parts = scope.split(":")
            if len(parts) != 2:
                raise ValueError(f"Scope must be 'action:domain', got: {scope}")
            if parts[0] not in valid_actions:
                raise ValueError(f"Invalid scope action '{parts[0]}', must be one of: {valid_actions}")
            if parts[1] not in valid_domains:
                raise ValueError(f"Invalid scope domain '{parts[1]}', must be one of: {valid_domains}")
        return v


class AgentIdentityUpdate(BaseModel):
    """Input model for updating an agent."""

    model_config = ConfigDict(protected_namespaces=())

    name: str | None = Field(None, min_length=2, max_length=128)
    scopes: list[str] | None = None
    model_tier: ModelTier | None = None
    daily_budget_cents: int | None = Field(None, ge=1, le=100000)
    status: AgentStatus | None = None


class AgentIdentity(BaseModel):
    """Full agent identity model with all fields.

    Primary ID is now 'id' (new ontology). The 'agent_id' field is kept
    as an alias for backward compatibility.
    """

    model_config = ConfigDict(protected_namespaces=())

    id: str = Field(..., description="Primary identifier (new ontology)")
    agent_id: str = Field(
        default="",
        description="Deprecated alias for id — use id instead",
    )
    name: str
    agent_type: AgentType
    status: AgentStatus
    scopes: list[str]
    model_tier: ModelTier
    daily_budget_cents: int
    daily_spend_cents: int = 0
    company_id: str
    created_at: str
    created_by: str

    def model_post_init(self, __context: object) -> None:
        """Sync agent_id with id for backward compatibility."""
        if not self.agent_id:
            object.__setattr__(self, "agent_id", self.id)
        elif not self.id:
            object.__setattr__(self, "id", self.agent_id)


class AgentSpendReport(BaseModel):
    """Agent spend report for cost monitoring."""

    id: str = Field(..., description="Primary identifier")
    agent_id: str = Field(default="", description="Deprecated alias for id")
    name: str
    agent_type: str
    daily_budget_cents: int
    daily_spend_cents: int
    budget_remaining_cents: int
    budget_utilisation_pct: float
