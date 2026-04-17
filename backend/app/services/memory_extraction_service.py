"""Memory extraction service — extracts Decisions and Insights from conversations.

After a conversation turn completes, this service runs a lightweight LLM pass
(FAST tier) to check if any decisions or institutional knowledge were expressed.
Results are persisted as Decision and Insight nodes linked to the Conversation.

Runs in the background — must never block chat streaming.
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from neo4j import Driver

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """\
You are an analyst extracting structured memory from a construction safety \
conversation. Identify any decisions made and institutional knowledge expressed.

A DECISION is something the user decided or committed to:
- "let's price it at $2400"
- "use OSHA 30 for this project"
- "assign Mike to the roofing team"

An INSIGHT is institutional knowledge or a learned heuristic:
- "kitchen rewires average 16 hours"
- "I use 0.38 hours per receptacle in renovations"
- "OSHA inspectors always check fall protection first"

Return JSON only. If nothing qualifies, return empty arrays.

{
  "decisions": [
    {
      "description": "Brief description of the decision",
      "reasoning": "Why it was decided (if stated)",
      "affects_entity_type": "Project|Worker|Equipment|null",
      "affects_entity_id": "entity ID if mentioned, null otherwise"
    }
  ],
  "insights": [
    {
      "content": "The institutional knowledge statement",
      "applicability_tags": ["tag1", "tag2"]
    }
  ]
}"""

EXTRACTION_USER_TEMPLATE = """\
Extract decisions and insights from this conversation turn:

USER: {user_message}

ASSISTANT: {assistant_message}"""


class MemoryExtractionService:
    """Extracts Decisions and Insights from conversation turns.

    Uses a FAST-tier LLM call to identify structured memory from
    natural language conversation. Results are stored as graph nodes
    linked to the originating Conversation.

    Attributes:
        driver: Neo4j driver for persisting extracted nodes.
        llm_service: LLM service for the extraction call.
    """

    def __init__(self, driver: Driver, llm_service: LLMService) -> None:
        """Initialise the memory extraction service.

        Args:
            driver: Neo4j driver for writing extraction results.
            llm_service: LLM service with cost tracking.
        """
        self.driver = driver
        self.llm_service = llm_service

    def extract_and_persist(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        agent_id: str = "agent_memory_extractor",
    ) -> dict[str, Any]:
        """Extract decisions and insights from a conversation turn.

        Runs a FAST-tier LLM call, parses the structured response, and
        persists any Decision or Insight nodes linked to the Conversation.

        This is a fire-and-forget operation — failures are logged, not raised.

        Args:
            conversation_id: The Conversation node ID.
            user_message: The user's message text.
            assistant_message: The assistant's response text.
            agent_id: Agent ID for cost attribution.

        Returns:
            A dict with counts: {"decisions": N, "insights": N}.
        """
        try:
            return self._do_extract(
                conversation_id, user_message, assistant_message, agent_id,
            )
        except Exception:
            logger.warning(
                "Memory extraction failed for conversation %s",
                conversation_id,
                exc_info=True,
            )
            return {"decisions": 0, "insights": 0}

    def _do_extract(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        agent_id: str,
    ) -> dict[str, Any]:
        """Internal extraction logic.

        Args:
            conversation_id: The Conversation node ID.
            user_message: The user's message text.
            assistant_message: The assistant's response text.
            agent_id: Agent ID for cost attribution.

        Returns:
            A dict with counts of extracted items.
        """
        # Skip trivial messages
        if len(user_message) < 20 and len(assistant_message) < 50:
            return {"decisions": 0, "insights": 0}

        prompt = EXTRACTION_USER_TEMPLATE.format(
            user_message=user_message[:2000],
            assistant_message=assistant_message[:2000],
        )

        result = self.llm_service.complete(
            agent_id=agent_id,
            messages=[{"role": "user", "content": prompt}],
            system=EXTRACTION_SYSTEM_PROMPT,
            model_tier="fast",
            max_tokens=1024,
        )

        # Parse JSON from LLM response
        parsed = self._parse_response(result.content)
        if parsed is None:
            return {"decisions": 0, "insights": 0}

        decisions = parsed.get("decisions", [])
        insights = parsed.get("insights", [])

        # Persist decisions
        for decision in decisions:
            self._persist_decision(conversation_id, decision)

        # Persist insights
        for insight in insights:
            self._persist_insight(conversation_id, insight)

        count = {"decisions": len(decisions), "insights": len(insights)}
        if count["decisions"] or count["insights"]:
            logger.info(
                "Extracted %d decisions, %d insights from conversation %s",
                count["decisions"],
                count["insights"],
                conversation_id,
            )
        return count

    def _parse_response(self, content: str) -> dict[str, Any] | None:
        """Parse the LLM's JSON response.

        Args:
            content: Raw LLM output text.

        Returns:
            Parsed dict, or None if parsing fails.
        """
        # Strip markdown code fences if present
        text = content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Failed to parse extraction response: %s", content[:200])
            return None

    def _persist_decision(
        self, conversation_id: str, decision: dict[str, Any]
    ) -> None:
        """Create a Decision node linked to the Conversation.

        Args:
            conversation_id: The parent Conversation ID.
            decision: Extracted decision dict with description, reasoning, etc.
        """
        dec_id = f"dec_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": dec_id,
            "description": decision.get("description", ""),
            "reasoning": decision.get("reasoning"),
            "confidence": 0.8,
            "created_at": now,
        }

        affects_type = decision.get("affects_entity_type")
        affects_id = decision.get("affects_entity_id")

        try:
            with self.driver.session() as session:
                if affects_type and affects_id:
                    session.run(
                        f"""
                        MATCH (conv:Conversation {{id: $conversation_id}})
                        CREATE (d:Decision $props)
                        CREATE (conv)-[:PRODUCED_DECISION]->(d)
                        WITH d
                        OPTIONAL MATCH (target:{affects_type} {{id: $affects_id}})
                        FOREACH (_ IN CASE WHEN target IS NOT NULL THEN [1] ELSE [] END |
                            CREATE (d)-[:AFFECTS]->(target)
                        )
                        """,
                        {
                            "conversation_id": conversation_id,
                            "props": props,
                            "affects_id": affects_id,
                        },
                    )
                else:
                    session.run(
                        """
                        MATCH (conv:Conversation {id: $conversation_id})
                        CREATE (d:Decision $props)
                        CREATE (conv)-[:PRODUCED_DECISION]->(d)
                        """,
                        {"conversation_id": conversation_id, "props": props},
                    )
        except Exception:
            logger.warning(
                "Failed to persist decision %s for conversation %s",
                dec_id,
                conversation_id,
                exc_info=True,
            )

    def _persist_insight(
        self, conversation_id: str, insight: dict[str, Any]
    ) -> None:
        """Create an Insight node linked to the Conversation.

        Args:
            conversation_id: The parent Conversation ID.
            insight: Extracted insight dict with content and tags.
        """
        ins_id = f"ins_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": ins_id,
            "content": insight.get("content", ""),
            "confidence": 0.7,
            "applicability_tags": insight.get("applicability_tags", []),
            "created_at": now,
        }

        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (conv:Conversation {id: $conversation_id})
                    CREATE (i:Insight $props)
                    CREATE (conv)-[:EXPRESSED_KNOWLEDGE]->(i)
                    """,
                    {"conversation_id": conversation_id, "props": props},
                )
        except Exception:
            logger.warning(
                "Failed to persist insight %s for conversation %s",
                ins_id,
                conversation_id,
                exc_info=True,
            )
