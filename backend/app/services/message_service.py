"""Message service (Neo4j-backed).

Messages are the individual turns within a Conversation. They are immutable —
once created they are not edited. Authorship is captured via the SENT_BY
relationship; per-call provenance (model, tokens, cost, latency, actor type,
agent id/version, confidence) is captured as properties on the Message node
so the Knowledge view can surface cost/latency/model per turn and the
AGENTIC_INFRASTRUCTURE provenance requirement is met from day one.
"""

from datetime import datetime, timezone
from typing import Any

from app.services.base_service import BaseService


# Properties accepted as per-message provenance. Whitelisted to avoid
# accidental property pollution from callers.
_PROVENANCE_FIELDS: tuple[str, ...] = (
    "actor_type",       # "human" | "agent"
    "agent_id",         # logical agent id (e.g. "agent_chat")
    "agent_version",    # agent version string for rollback traceability
    "model_id",         # Anthropic model id used for this turn
    "input_tokens",     # prompt tokens
    "output_tokens",    # completion tokens
    "cost_cents",       # cost attributed to this turn (float)
    "latency_ms",       # wall-clock time for the LLM call
    "confidence",       # agent-declared confidence [0..1] (nullable)
)


class MessageNotFoundError(Exception):
    """Raised when a message cannot be found."""

    def __init__(self, message_id: str) -> None:
        self.message_id = message_id
        super().__init__(f"Message not found: {message_id}")


class ConversationNotFoundError(Exception):
    """Raised when the parent conversation cannot be found during message creation."""

    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        super().__init__(f"Conversation not found: {conversation_id}")


class MessageService(BaseService):
    """Manages Message nodes in the Neo4j graph.

    Messages connect to conversations via (Message)-[:PART_OF]->(Conversation).
    Sequential ordering is captured via (Message)-[:FOLLOWS]->(Message).
    Authorship uses (Message)-[:SENT_BY]->(Member|AgentIdentity).
    Messages are immutable — no update or delete methods are provided.
    """

    def create(
        self,
        conversation_id: str,
        data: dict[str, Any],
        sender_id: str,
        sender_type: str = "member",
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new message in a conversation.

        Creates the PART_OF relationship and optionally a FOLLOWS relationship
        to the previous message. Authorship is recorded via SENT_BY.

        Args:
            conversation_id: The parent conversation ID.
            data: Message fields — role ('user'|'assistant'|'system'), content,
                embedding (optional list of floats), scope_project_id (optional).
            sender_id: ID of the sending entity (Member or AgentIdentity).
            sender_type: Label of the sender node — 'member' or 'agent'.
                Defaults to 'member'.
            provenance: Optional per-turn provenance dict. Recognised keys:
                ``actor_type``, ``agent_id``, ``agent_version``, ``model_id``,
                ``input_tokens``, ``output_tokens``, ``cost_cents``,
                ``latency_ms``, ``confidence``. Unknown keys are ignored.
                All keys are stored as properties on the Message node for
                use in the Knowledge trace view and structural validation.

        Returns:
            The created message dict.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        msg_id = self._generate_id("msg")
        now = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": msg_id,
            "role": data.get("role", "user"),
            "content": data.get("content", ""),
            "content_blocks": data.get("content_blocks"),
            "timestamp": now,
            "embedding": data.get("embedding"),
            # Scope tag — populated by Phase 3; nullable until then so older
            # messages simply carry null.
            "scope_project_id": data.get("scope_project_id"),
        }

        # Merge whitelisted provenance fields. Missing keys remain absent
        # from props so Neo4j stores null for them.
        if provenance:
            for key in _PROVENANCE_FIELDS:
                if key in provenance:
                    props[key] = provenance[key]

        sender_label = "AgentIdentity" if sender_type == "agent" else "Member"

        result = self._write_tx_single(
            f"""
            MATCH (conv:Conversation {{id: $conversation_id}})
            WHERE conv.deleted = false
            OPTIONAL MATCH (prev:Message)-[:PART_OF]->(conv)
            WITH conv, prev
            ORDER BY prev.timestamp DESC
            LIMIT 1
            CREATE (msg:Message $props)
            CREATE (msg)-[:PART_OF]->(conv)
            FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
                CREATE (msg)-[:FOLLOWS]->(prev)
            )
            WITH msg, conv
            OPTIONAL MATCH (sender:{sender_label} {{id: $sender_id}})
            FOREACH (_ IN CASE WHEN sender IS NOT NULL THEN [1] ELSE [] END |
                CREATE (msg)-[:SENT_BY]->(sender)
            )
            RETURN msg {{.*, conversation_id: conv.id, sender_id: $sender_id}} AS message
            """,
            {
                "conversation_id": conversation_id,
                "props": props,
                "sender_id": sender_id,
            },
        )
        if result is None:
            raise ConversationNotFoundError(conversation_id)
        return result["message"]

    def get(self, conversation_id: str, message_id: str) -> dict[str, Any]:
        """Fetch a single message.

        Args:
            conversation_id: The parent conversation ID.
            message_id: The message ID to fetch.

        Returns:
            The message dict.

        Raises:
            MessageNotFoundError: If the message does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (msg:Message {id: $message_id})-[:PART_OF]->(conv:Conversation {id: $conversation_id})
            OPTIONAL MATCH (msg)-[:SENT_BY]->(sender)
            RETURN msg {.*, conversation_id: conv.id, sender_id: sender.id} AS message
            """,
            {"conversation_id": conversation_id, "message_id": message_id},
        )
        if result is None:
            raise MessageNotFoundError(message_id)
        return result["message"]

    def list_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List messages in a conversation, ordered chronologically.

        Args:
            conversation_id: The parent conversation ID.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip.

        Returns:
            A dict with 'messages' list and 'total' count.
        """
        params: dict[str, Any] = {
            "conversation_id": conversation_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (msg:Message)-[:PART_OF]->(conv:Conversation {id: $conversation_id})
            RETURN count(msg) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (msg:Message)-[:PART_OF]->(conv:Conversation {id: $conversation_id})
            OPTIONAL MATCH (msg)-[:SENT_BY]->(sender)
            RETURN msg {.*, conversation_id: conv.id, sender_id: sender.id} AS message
            ORDER BY msg.timestamp ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"messages": [r["message"] for r in results], "total": total}

    def search_by_embedding(
        self,
        conversation_id: str,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve messages semantically similar to a query embedding.

        Uses Neo4j vector index for approximate nearest-neighbour search.
        The index must exist as: CALL db.index.vector.createNodeIndex(
            'message-embeddings', 'Message', 'embedding', <dim>, 'cosine')

        Args:
            conversation_id: Scope search to this conversation only.
            query_embedding: Float vector representing the search query.
            top_k: Number of nearest messages to return.

        Returns:
            List of message dicts ordered by similarity (most similar first).
        """
        results = self._read_tx(
            """
            CALL db.index.vector.queryNodes('message-embeddings', $top_k, $embedding)
            YIELD node AS msg, score
            MATCH (msg)-[:PART_OF]->(conv:Conversation {id: $conversation_id})
            OPTIONAL MATCH (msg)-[:SENT_BY]->(sender)
            RETURN msg {.*, conversation_id: conv.id, sender_id: sender.id, similarity: score}
                   AS message
            ORDER BY score DESC
            """,
            {
                "conversation_id": conversation_id,
                "embedding": query_embedding,
                "top_k": top_k,
            },
        )
        return [r["message"] for r in results]
