"""Conversation service (Neo4j-backed).

Conversations represent a chat or voice session between a user (or agent)
and the Kerf AI assistant. They are the container for Message nodes.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ConversationNotFoundError(Exception):
    """Raised when a conversation cannot be found."""

    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        super().__init__(f"Conversation not found: {conversation_id}")


class ConversationService(BaseService):
    """Manages Conversation nodes in the Neo4j graph.

    Conversations connect to companies via (Company)-[:HAS_CONVERSATION]->(Conversation)
    and optionally to projects via (Conversation)-[:ABOUT_PROJECT]->(Project).
    """

    def create(
        self,
        company_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new conversation for a company.

        Args:
            company_id: The owning company ID.
            data: Conversation fields — mode ('chat'|'voice'), title, project_id.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created conversation dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        conv_id = self._generate_id("conv")
        project_id = data.get("project_id")

        props: dict[str, Any] = {
            "id": conv_id,
            "session_id": data.get("session_id"),
            "mode": data.get("mode", "chat"),
            "title": data.get("title"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None,
            "transcript_url": None,
            "deleted": False,
            **self._provenance_create(actor),
        }

        if project_id:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                MATCH (p:Project {id: $project_id})
                CREATE (conv:Conversation $props)
                CREATE (c)-[:HAS_CONVERSATION]->(conv)
                CREATE (conv)-[:ABOUT_PROJECT]->(p)
                RETURN conv {.*, company_id: c.id, project_id: p.id} AS conversation
                """,
                {"company_id": company_id, "props": props, "project_id": project_id},
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                CREATE (conv:Conversation $props)
                CREATE (c)-[:HAS_CONVERSATION]->(conv)
                RETURN conv {.*, company_id: c.id} AS conversation
                """,
                {"company_id": company_id, "props": props},
            )

        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=conv_id,
            entity_type="Conversation",
            company_id=company_id,
            actor=actor,
            summary=f"Started {data.get('mode', 'chat')} conversation",
        )
        return result["conversation"]

    def get(self, company_id: str, conversation_id: str) -> dict[str, Any]:
        """Fetch a single conversation.

        Args:
            company_id: The owning company ID.
            conversation_id: The conversation ID to fetch.

        Returns:
            The conversation dict.

        Raises:
            ConversationNotFoundError: If the conversation does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]
                  ->(conv:Conversation {id: $conversation_id})
            WHERE conv.deleted = false
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN conv {.*, company_id: c.id, project_id: p.id} AS conversation
            """,
            {"company_id": company_id, "conversation_id": conversation_id},
        )
        if result is None:
            raise ConversationNotFoundError(conversation_id)
        return result["conversation"]

    def list_by_company(
        self,
        company_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all conversations for a company.

        Args:
            company_id: The owning company ID.
            limit: Maximum number of conversations to return.
            offset: Number of conversations to skip.

        Returns:
            A dict with 'conversations' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
            WHERE conv.deleted = false
            RETURN count(conv) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
            WHERE conv.deleted = false
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN conv {.*, company_id: c.id, project_id: p.id} AS conversation
            ORDER BY conv.started_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"conversations": [r["conversation"] for r in results], "total": total}

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List conversations about a specific project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to filter by.
            limit: Maximum number of conversations to return.
            offset: Number of conversations to skip.

        Returns:
            A dict with 'conversations' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
                  -[:ABOUT_PROJECT]->(p:Project {id: $project_id})
            WHERE conv.deleted = false
            RETURN count(conv) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
                  -[:ABOUT_PROJECT]->(p:Project {id: $project_id})
            WHERE conv.deleted = false
            RETURN conv {.*, company_id: c.id, project_id: p.id} AS conversation
            ORDER BY conv.started_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"conversations": [r["conversation"] for r in results], "total": total}

    def end_conversation(
        self,
        company_id: str,
        conversation_id: str,
        transcript_url: str | None,
        user_id: str,
    ) -> dict[str, Any]:
        """Mark a conversation as ended.

        Sets ended_at to now and optionally records a transcript URL.

        Args:
            company_id: The owning company ID.
            conversation_id: The conversation ID.
            transcript_url: Optional URL to a stored transcript/recording.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated conversation dict.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        actor = Actor.human(user_id)
        update_fields: dict[str, Any] = {
            "ended_at": datetime.now(timezone.utc).isoformat(),
            **self._provenance_update(actor),
        }
        if transcript_url is not None:
            update_fields["transcript_url"] = transcript_url

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]
                  ->(conv:Conversation {id: $conversation_id})
            WHERE conv.deleted = false
            SET conv += $props
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN conv {.*, company_id: c.id, project_id: p.id} AS conversation
            """,
            {
                "company_id": company_id,
                "conversation_id": conversation_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ConversationNotFoundError(conversation_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=conversation_id,
            entity_type="Conversation",
            company_id=company_id,
            actor=actor,
            summary=f"Ended conversation {conversation_id}",
        )
        return result["conversation"]
