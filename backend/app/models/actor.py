"""Actor identity model for provenance tracking.

Every mutation in the system records who performed it — human or agent.
This model represents the actor making the request.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class Actor:
    """Identity of the entity performing an operation.

    Attributes:
        id: Unique identifier — Clerk user ID for humans, agent_id for agents.
        type: Whether this is a human user or an AI agent.
        agent_id: Agent identifier (only set when type is 'agent').
        company_id: The company context for this operation.
        scopes: Permission scopes granted to this actor.
        agent_version: Semantic version of the agent, e.g. '1.2.0'. Agents only.
        model_id: Model that produced the output, e.g. 'claude-sonnet-4-6'. Agents only.
        confidence: Agent's self-reported confidence 0.0-1.0. Agents only.
        cost_cents: Token cost of the invocation in cents. Agents only.
    """

    id: str
    type: Literal["human", "agent"] = "human"
    agent_id: str | None = None
    company_id: str | None = None
    scopes: tuple[str, ...] = field(default_factory=tuple)
    agent_version: str | None = None
    model_id: str | None = None
    confidence: float | None = None
    cost_cents: int | None = None

    @classmethod
    def human(cls, uid: str, company_id: str | None = None) -> "Actor":
        """Create an Actor representing a human user.

        Args:
            uid: The Clerk user ID.
            company_id: Optional company context.

        Returns:
            An Actor with type 'human'.
        """
        return cls(id=uid, type="human", company_id=company_id)

    @classmethod
    def agent(
        cls,
        agent_id: str,
        company_id: str | None = None,
        scopes: tuple[str, ...] = (),
        agent_version: str | None = None,
        model_id: str | None = None,
        confidence: float | None = None,
        cost_cents: int | None = None,
    ) -> "Actor":
        """Create an Actor representing an AI agent.

        Args:
            agent_id: The agent's unique identifier.
            company_id: Optional company context.
            scopes: Permission scopes granted to this agent.
            agent_version: Semantic version of the agent ('1.2.0').
            model_id: Model used for the invocation ('claude-sonnet-4-6').
            confidence: Self-reported confidence 0.0-1.0.
            cost_cents: Token cost in cents.

        Returns:
            An Actor with type 'agent'.
        """
        return cls(
            id=agent_id,
            type="agent",
            agent_id=agent_id,
            company_id=company_id,
            scopes=scopes,
            agent_version=agent_version,
            model_id=model_id,
            confidence=confidence,
            cost_cents=cost_cents,
        )
