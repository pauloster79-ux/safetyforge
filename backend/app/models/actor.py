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
    """

    id: str
    type: Literal["human", "agent"] = "human"
    agent_id: str | None = None
    company_id: str | None = None
    scopes: tuple[str, ...] = field(default_factory=tuple)

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
    ) -> "Actor":
        """Create an Actor representing an AI agent.

        Args:
            agent_id: The agent's unique identifier.
            company_id: Optional company context.
            scopes: Permission scopes granted to this agent.

        Returns:
            An Actor with type 'agent'.
        """
        return cls(
            id=agent_id,
            type="agent",
            agent_id=agent_id,
            company_id=company_id,
            scopes=scopes,
        )
