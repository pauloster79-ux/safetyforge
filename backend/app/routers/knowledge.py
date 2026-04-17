"""Knowledge router — surfaces what Kerf has recorded about a tenant.

Powers the frontend "Knowledge" canvas:
  * Conversation list (paginated) with provenance summary
  * Conversation trace (per-turn, with tool calls + provenance + linked decisions/insights)
  * Decision list (extracted from past chats)
  * Insight list (extracted from past chats)
  * Entity mentions (every message that REFERENCES a Project/Worker/Inspection/...)

All endpoints are scoped to the caller's company via the existing
``Company.created_by = user_uid`` traversal pattern. No new ACL layer.
The router is mounted under ``/api/v1`` and uses the ``/me/knowledge``
prefix.

Why a separate router instead of extending /me/conversations?
  - /me/conversations is consumed by code that doesn't need provenance
  - /me/knowledge/* returns a richer, denormalised payload for one UI
  - Keeps existing endpoints small and stable
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from neo4j import Driver

from app.dependencies import get_current_user, get_neo4j_driver

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge"])


# -----------------------------------------------------------------------------
# Tenant resolution helper
# -----------------------------------------------------------------------------


def _resolve_company_id(driver: Driver, user_uid: str) -> str:
    """Resolve the user's company ID by graph traversal.

    Mirrors ``conversations.py::_resolve_company_id``. Single source of truth
    for "what company does this caller belong to" — change here when member
    access lands in Phase 5.
    """
    with driver.session() as session:
        record = session.run(
            "MATCH (c:Company {created_by: $uid}) RETURN c.id AS id LIMIT 1",
            uid=user_uid,
        ).single()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company found for current user",
        )
    return record["id"]


def _safe_load_blocks(raw: Any) -> list[dict[str, Any]] | None:
    """Decode the JSON-stringified ``Message.content_blocks`` property.

    Returns ``None`` if the value is missing or unparseable. Non-fatal —
    the trace still renders without structured blocks.
    """
    if not raw:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return None
    return None


def _extract_tool_calls(blocks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Pull tool_use blocks out of the structured content for trace display."""
    if not blocks:
        return []
    return [
        {
            "id": b.get("id"),
            "name": b.get("name"),
            "input": b.get("input"),
        }
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "tool_use"
    ]


def _extract_tool_results(
    blocks: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Pull tool_result blocks out of the structured content for trace display."""
    if not blocks:
        return []
    out: list[dict[str, Any]] = []
    for b in blocks:
        if not isinstance(b, dict) or b.get("type") != "tool_result":
            continue
        content = b.get("content")
        # Tool result content is often pre-stringified JSON; truncate for the
        # list view, full payload available via /trace.
        if isinstance(content, str) and len(content) > 500:
            content = content[:500] + "…"
        out.append({"tool_use_id": b.get("tool_use_id"), "content": content})
    return out


# -----------------------------------------------------------------------------
# Conversations
# -----------------------------------------------------------------------------


@router.get("/me/knowledge/conversations")
def list_conversations(
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    project_id: str | None = Query(None, description="Filter by project scope"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List conversations with provenance summary for the current company.

    Each row includes turn count, total cost, last activity, and the linked
    project (if any). Designed for the Knowledge canvas conversation list.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    where_project = "AND (conv)-[:ABOUT_PROJECT]->(:Project {id: $project_id})" if project_id else ""

    with driver.session() as session:
        total = session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)
            WHERE conv.deleted = false
            {where_project}
            RETURN count(conv) AS n
            """,
            company_id=company_id,
            project_id=project_id,
        ).single()["n"]

        rows = list(session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)
            WHERE conv.deleted = false
            {where_project}
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            OPTIONAL MATCH (m:Message)-[:PART_OF]->(conv)
            WITH conv, p,
                 count(m) AS turn_count,
                 sum(coalesce(m.cost_cents, 0)) AS total_cost_cents,
                 max(m.timestamp) AS last_message_at
            RETURN conv.id AS id,
                   conv.title AS title,
                   conv.mode AS mode,
                   conv.started_at AS started_at,
                   conv.created_by AS created_by,
                   coalesce(last_message_at, conv.started_at) AS last_activity,
                   turn_count,
                   total_cost_cents,
                   p.id AS project_id,
                   p.name AS project_name
            ORDER BY last_activity DESC
            SKIP $offset LIMIT $limit
            """,
            company_id=company_id,
            project_id=project_id,
            offset=offset,
            limit=limit,
        ))

    return {
        "conversations": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/me/knowledge/conversations/{conversation_id}/trace")
def get_conversation_trace(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> dict[str, Any]:
    """Return a fully denormalised trace of a conversation.

    Includes:
      * The conversation node + its project link
      * Every message with full provenance + parsed tool calls / results
      * Every entity REFERENCED by each message
      * Every Decision / Insight extracted from the conversation

    The Knowledge canvas renders this directly — one round trip per
    conversation view. Tenant-scoped: 404 if the caller's company doesn't
    own the conversation.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    with driver.session() as session:
        # Conversation header — also acts as the tenant gate
        conv = session.run(
            """
            MATCH (co:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation {id: $cid})
            WHERE conv.deleted = false
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN conv {.*, company_id: co.id, project_id: p.id, project_name: p.name} AS conv
            """,
            company_id=company_id,
            cid=conversation_id,
        ).single()
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation not found: {conversation_id}",
            )

        # Messages with provenance, ordered chronologically
        msg_rows = list(session.run(
            """
            MATCH (m:Message)-[:PART_OF]->(conv:Conversation {id: $cid})
            OPTIONAL MATCH (m)-[:SENT_BY]->(sender)
            OPTIONAL MATCH (m)-[ref:REFERENCES]->(entity)
            WITH m, sender,
                 collect(DISTINCT CASE WHEN entity IS NOT NULL
                   THEN { entity_id: entity.id, entity_type: ref.entity_type,
                          entity_name: coalesce(entity.name, entity.title, entity.id) }
                   ELSE NULL END) AS refs
            RETURN m.id            AS id,
                   m.role          AS role,
                   m.actor_type    AS actor_type,
                   m.agent_id      AS agent_id,
                   m.agent_version AS agent_version,
                   m.model_id      AS model_id,
                   m.input_tokens  AS input_tokens,
                   m.output_tokens AS output_tokens,
                   m.cost_cents    AS cost_cents,
                   m.latency_ms    AS latency_ms,
                   m.confidence    AS confidence,
                   m.scope_project_id AS scope_project_id,
                   m.timestamp     AS timestamp,
                   m.content       AS content,
                   m.content_blocks AS content_blocks,
                   coalesce(sender.id, null) AS sender_id,
                   labels(sender)            AS sender_labels,
                   [r IN refs WHERE r IS NOT NULL] AS references
            ORDER BY m.timestamp ASC
            """,
            cid=conversation_id,
        ))

        messages: list[dict[str, Any]] = []
        for r in msg_rows:
            row = dict(r)
            blocks = _safe_load_blocks(row.pop("content_blocks", None))
            row["tool_calls"] = _extract_tool_calls(blocks)
            row["tool_results"] = _extract_tool_results(blocks)
            messages.append(row)

        # Decisions + insights extracted from this conversation
        decisions = [dict(r) for r in session.run(
            """
            MATCH (conv:Conversation {id: $cid})-[:HAS_DECISION]->(d:Decision)
            RETURN d.id AS id, d.description AS description, d.reasoning AS reasoning,
                   d.affected_entity_type AS affected_entity_type,
                   d.affected_entity_id   AS affected_entity_id,
                   d.created_at           AS created_at
            ORDER BY d.created_at DESC
            """,
            cid=conversation_id,
        )]

        insights = [dict(r) for r in session.run(
            """
            MATCH (conv:Conversation {id: $cid})-[:HAS_INSIGHT]->(i:Insight)
            RETURN i.id AS id, i.content AS content, i.tags AS tags,
                   i.created_at AS created_at
            ORDER BY i.created_at DESC
            """,
            cid=conversation_id,
        )]

    # Roll-up totals so the UI can show the conversation cost without summing client-side
    total_cost = sum(
        (m["cost_cents"] or 0) for m in messages if m.get("cost_cents") is not None
    )
    total_tokens_in = sum(
        (m["input_tokens"] or 0) for m in messages if m.get("input_tokens") is not None
    )
    total_tokens_out = sum(
        (m["output_tokens"] or 0) for m in messages if m.get("output_tokens") is not None
    )

    return {
        "conversation": dict(conv["conv"]),
        "messages": messages,
        "decisions": decisions,
        "insights": insights,
        "totals": {
            "turn_count": len(messages),
            "cost_cents": round(total_cost, 4),
            "input_tokens": total_tokens_in,
            "output_tokens": total_tokens_out,
        },
    }


# -----------------------------------------------------------------------------
# Decisions / Insights (cross-conversation, scoped to the company)
# -----------------------------------------------------------------------------


@router.get("/me/knowledge/decisions")
def list_decisions(
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    project_id: str | None = Query(None, description="Filter by source-conversation project"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List Decision nodes extracted from the company's conversations.

    Each row links back to the source conversation so the UI can jump
    into the relevant trace.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    where_project = "AND (conv)-[:ABOUT_PROJECT]->(:Project {id: $project_id})" if project_id else ""

    with driver.session() as session:
        total = session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)-[:HAS_DECISION]->(d:Decision)
            WHERE conv.deleted = false
            {where_project}
            RETURN count(d) AS n
            """,
            company_id=company_id, project_id=project_id,
        ).single()["n"]

        rows = list(session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)-[:HAS_DECISION]->(d:Decision)
            WHERE conv.deleted = false
            {where_project}
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN d.id AS id,
                   d.description AS description,
                   d.reasoning   AS reasoning,
                   d.affected_entity_type AS affected_entity_type,
                   d.affected_entity_id   AS affected_entity_id,
                   d.created_at  AS created_at,
                   conv.id       AS conversation_id,
                   conv.title    AS conversation_title,
                   p.id          AS project_id,
                   p.name        AS project_name
            ORDER BY d.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            company_id=company_id, project_id=project_id,
            offset=offset, limit=limit,
        ))

    return {
        "decisions": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/me/knowledge/insights")
def list_insights(
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    project_id: str | None = Query(None, description="Filter by source-conversation project"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List Insight nodes extracted from the company's conversations."""
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    where_project = "AND (conv)-[:ABOUT_PROJECT]->(:Project {id: $project_id})" if project_id else ""

    with driver.session() as session:
        total = session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)-[:HAS_INSIGHT]->(i:Insight)
            WHERE conv.deleted = false
            {where_project}
            RETURN count(i) AS n
            """,
            company_id=company_id, project_id=project_id,
        ).single()["n"]

        rows = list(session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)-[:HAS_INSIGHT]->(i:Insight)
            WHERE conv.deleted = false
            {where_project}
            OPTIONAL MATCH (conv)-[:ABOUT_PROJECT]->(p:Project)
            RETURN i.id AS id,
                   i.content AS content,
                   i.tags    AS tags,
                   i.created_at AS created_at,
                   conv.id   AS conversation_id,
                   conv.title AS conversation_title,
                   p.id      AS project_id,
                   p.name    AS project_name
            ORDER BY i.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            company_id=company_id, project_id=project_id,
            offset=offset, limit=limit,
        ))

    return {
        "insights": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# -----------------------------------------------------------------------------
# Entity mentions
# -----------------------------------------------------------------------------


_VALID_ENTITY_LABELS: set[str] = {
    "Project", "Worker", "Inspection", "Equipment",
    "Incident", "HazardReport", "DailyLog",
}


@router.get("/me/knowledge/entities/{entity_type}/{entity_id}/mentions")
def list_entity_mentions(
    entity_type: str,
    entity_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Every Message that REFERENCES the given entity, scoped to the company.

    Powers entity-page "Mentions" tabs (e.g. ProjectDetailPage).
    """
    if entity_type not in _VALID_ENTITY_LABELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported entity_type: {entity_type}. "
                   f"Allowed: {sorted(_VALID_ENTITY_LABELS)}",
        )

    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    # The :{entity_type} interpolation is safe because we whitelisted above.
    with driver.session() as session:
        total = session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)
                  <-[:PART_OF]-(m:Message)-[:REFERENCES]->(e:{entity_type} {{id: $entity_id}})
            RETURN count(DISTINCT m) AS n
            """,
            company_id=company_id, entity_id=entity_id,
        ).single()["n"]

        rows = list(session.run(
            f"""
            MATCH (co:Company {{id: $company_id}})-[:HAS_CONVERSATION]->(conv:Conversation)
                  <-[:PART_OF]-(m:Message)-[:REFERENCES]->(e:{entity_type} {{id: $entity_id}})
            RETURN m.id AS message_id,
                   m.role AS role,
                   m.actor_type AS actor_type,
                   m.timestamp AS timestamp,
                   substring(coalesce(m.content, ""), 0, 240) AS preview,
                   conv.id AS conversation_id,
                   conv.title AS conversation_title
            ORDER BY m.timestamp DESC
            SKIP $offset LIMIT $limit
            """,
            company_id=company_id, entity_id=entity_id,
            offset=offset, limit=limit,
        ))

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "mentions": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
