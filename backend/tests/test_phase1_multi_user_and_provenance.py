"""Phase 1 regression tests — multi-user demo tokens + per-message provenance.

Covers:
  * ``_resolve_demo_token`` maps ``demo-token`` and ``demo-token-<alias>`` to
    the correct seeded golden user, and rejects unknown aliases.
  * ``MessageService.create`` persists whitelisted provenance fields onto
    the Message node and ignores unknown keys.
  * Structural validation: assistant messages without model_id are detected
    by the V-MSG-02 validation query.

These are the invariants Phase 1 establishes. Later phases must not regress
them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from neo4j import Driver

from app.dependencies import DEMO_USERS, _resolve_demo_token
from app.services.message_service import MessageService


# -----------------------------------------------------------------------------
# Pure-function tests — no Neo4j required
# -----------------------------------------------------------------------------


class TestResolveDemoToken:
    """@CAT:HAPPY @CAT:VALIDATION @CAT:EDGE — demo-token multi-user resolution."""

    def test_bare_demo_token_resolves_to_gp04(self) -> None:
        """[HAPPY] Back-compat: plain ``demo-token`` still resolves to GP04."""
        result = _resolve_demo_token("demo-token")
        assert result is not None
        assert result["uid"] == "demo_user_001"
        assert result["email"] == "demo@kerf.build"
        assert result["email_verified"] is True

    def test_suffixed_demo_token_resolves_to_seeded_user(self) -> None:
        """[HAPPY] Each golden alias resolves to the matching seeded user."""
        for alias, expected in DEMO_USERS.items():
            result = _resolve_demo_token(f"demo-token-{alias}")
            assert result is not None, f"alias {alias} failed to resolve"
            assert result["uid"] == expected["uid"]
            assert result["email"] == expected["email"]
            assert result["email_verified"] is True

    def test_unknown_alias_returns_none(self) -> None:
        """[VALIDATION] Unknown demo-token suffixes are rejected."""
        assert _resolve_demo_token("demo-token-nonexistent") is None
        assert _resolve_demo_token("demo-token-") is None

    def test_non_demo_tokens_return_none(self) -> None:
        """[EDGE] Anything that doesn't look like a demo token returns None.

        Ensures real JWTs fall through to the Clerk verification branch
        rather than being spuriously accepted.
        """
        assert _resolve_demo_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.abc.def") is None
        assert _resolve_demo_token("") is None
        assert _resolve_demo_token("demo_token") is None  # underscore, not dash

    def test_all_demo_users_have_consistent_fields(self) -> None:
        """[VALIDATION] Every entry in DEMO_USERS has required fields."""
        for alias, user in DEMO_USERS.items():
            assert "uid" in user
            assert "email" in user
            assert "name" in user
            assert user["uid"].strip(), f"{alias} has blank uid"
            assert "@" in user["email"], f"{alias} has invalid email"


# -----------------------------------------------------------------------------
# MessageService provenance integration tests — real Neo4j
# -----------------------------------------------------------------------------


@pytest.fixture()
def message_service(neo4j_driver: Driver) -> MessageService:
    """Provide a MessageService instance for direct test usage."""
    return MessageService(neo4j_driver)


@pytest.fixture()
def conversation_id(neo4j_driver: Driver) -> str:
    """Create a Conversation node and return its id for message tests."""
    cid = "conv_test_phase1"
    now = datetime.now(timezone.utc).isoformat()
    with neo4j_driver.session() as session:
        session.run(
            """
            CREATE (c:Conversation {
              id: $id,
              session_id: $id,
              mode: 'general',
              title: 'Phase 1 test',
              deleted: false,
              started_at: $now,
              created_at: $now,
              created_by: 'test_user_001'
            })
            """,
            id=cid,
            now=now,
        )
    return cid


def _fetch_message_props(driver: Driver, msg_id: str) -> dict[str, Any]:
    """Return all properties on a Message node."""
    with driver.session() as session:
        record = session.run(
            "MATCH (m:Message {id: $id}) RETURN properties(m) AS props",
            id=msg_id,
        ).single()
    assert record is not None, f"Message {msg_id} not found"
    return record["props"]


class TestMessageProvenance:
    """@CAT:HAPPY @CAT:EDGE @CAT:VALIDATION — provenance persistence."""

    def test_assistant_message_persists_all_provenance_fields(
        self,
        message_service: MessageService,
        neo4j_driver: Driver,
        conversation_id: str,
    ) -> None:
        """[HAPPY] All whitelisted provenance keys are stored on the node."""
        provenance = {
            "actor_type": "agent",
            "agent_id": "agent_chat",
            "agent_version": "1.0.0",
            "model_id": "claude-sonnet-4-20250514",
            "input_tokens": 1234,
            "output_tokens": 567,
            "cost_cents": 1.22,
            "latency_ms": 2100,
            "confidence": None,
        }
        msg = message_service.create(
            conversation_id=conversation_id,
            data={"role": "assistant", "content": "hi"},
            sender_id="agent_chat",
            sender_type="agent",
            provenance=provenance,
        )
        props = _fetch_message_props(neo4j_driver, msg["id"])

        assert props["actor_type"] == "agent"
        assert props["agent_id"] == "agent_chat"
        assert props["agent_version"] == "1.0.0"
        assert props["model_id"] == "claude-sonnet-4-20250514"
        assert props["input_tokens"] == 1234
        assert props["output_tokens"] == 567
        assert props["cost_cents"] == pytest.approx(1.22)
        assert props["latency_ms"] == 2100

    def test_user_message_carries_human_actor_type(
        self,
        message_service: MessageService,
        neo4j_driver: Driver,
        conversation_id: str,
    ) -> None:
        """[HAPPY] User-authored messages have actor_type='human' and no model/tokens."""
        provenance = {
            "actor_type": "human",
            "agent_id": None,
            "agent_version": None,
            "model_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cost_cents": None,
            "latency_ms": None,
            "confidence": None,
        }
        msg = message_service.create(
            conversation_id=conversation_id,
            data={"role": "user", "content": "hello"},
            sender_id="test_user_001",
            sender_type="member",
            provenance=provenance,
        )
        props = _fetch_message_props(neo4j_driver, msg["id"])
        assert props["actor_type"] == "human"
        # Absent fields should be stored as null / missing — either is fine
        # as long as the Knowledge view sees "no model" for user turns.
        assert props.get("model_id") in (None,)
        assert props.get("input_tokens") in (None,)

    def test_unknown_provenance_keys_are_ignored(
        self,
        message_service: MessageService,
        neo4j_driver: Driver,
        conversation_id: str,
    ) -> None:
        """[VALIDATION] Non-whitelisted provenance keys do not leak onto the node."""
        msg = message_service.create(
            conversation_id=conversation_id,
            data={"role": "assistant", "content": "hi"},
            sender_id="agent_chat",
            sender_type="agent",
            provenance={
                "actor_type": "agent",
                "model_id": "claude-sonnet-4-20250514",
                # These should be silently dropped:
                "malicious_key": "evil",
                "internal_secret": "leaked",
            },
        )
        props = _fetch_message_props(neo4j_driver, msg["id"])
        assert "malicious_key" not in props
        assert "internal_secret" not in props
        assert props["model_id"] == "claude-sonnet-4-20250514"

    def test_missing_provenance_does_not_break_create(
        self,
        message_service: MessageService,
        neo4j_driver: Driver,
        conversation_id: str,
    ) -> None:
        """[EDGE] Existing callers that don't pass provenance still succeed."""
        msg = message_service.create(
            conversation_id=conversation_id,
            data={"role": "user", "content": "legacy path"},
            sender_id="test_user_001",
            sender_type="member",
        )
        props = _fetch_message_props(neo4j_driver, msg["id"])
        # No provenance stored; read path must still work.
        assert props["content"] == "legacy path"
        assert props.get("actor_type") is None


# -----------------------------------------------------------------------------
# Structural validation — V-MSG-02 catches missing model_id
# -----------------------------------------------------------------------------


class TestProvenanceValidation:
    """@CAT:VALIDATION — CI-enforceable structural invariants."""

    def test_v_msg_02_detects_agent_message_without_model_id(
        self,
        message_service: MessageService,
        neo4j_driver: Driver,
        conversation_id: str,
    ) -> None:
        """V-MSG-02: an assistant Message without model_id is flagged."""
        # Seed a non-compliant agent message (omitting model_id).
        message_service.create(
            conversation_id=conversation_id,
            data={"role": "assistant", "content": "no model"},
            sender_id="agent_chat",
            sender_type="agent",
            provenance={"actor_type": "agent", "agent_id": "agent_chat"},
        )

        with neo4j_driver.session() as session:
            violations = list(session.run(
                """
                MATCH (m:Message)
                WHERE m.actor_type = "agent" AND m.model_id IS NULL
                  AND NOT coalesce(m.content, "") STARTS WITH '[{"tool_use_id"'
                RETURN m.id AS id
                """
            ))
        assert len(violations) == 1, "V-MSG-02 should detect the seeded violation"
