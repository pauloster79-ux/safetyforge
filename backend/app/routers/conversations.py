"""Conversations router — list, get, and search conversation history."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_neo4j_driver
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)
from app.services.embedding_service import EmbeddingService
from app.services.message_service import MessageService
from neo4j import Driver

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


# -- Dependency providers -------------------------------------------------------


def get_conversation_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ConversationService:
    """Provide a ConversationService instance."""
    return ConversationService(driver)


def get_message_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> MessageService:
    """Provide a MessageService instance."""
    return MessageService(driver)


def get_embedding_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingService:
    """Provide an EmbeddingService instance."""
    return EmbeddingService(driver, settings)


# -- Request/response models ---------------------------------------------------


class ConversationSearchRequest(BaseModel):
    """Request body for conversation search."""

    query: str = Field(..., min_length=1, description="Search query text")
    project_id: str | None = Field(None, description="Optional project filter")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")


class ConversationSearchResult(BaseModel):
    """A single search result."""

    conversation_id: str
    message_id: str
    content: str
    role: str
    timestamp: str
    similarity: float | None = None


# -- Helper to resolve company ---------------------------------------------------


def _resolve_company_id(driver: Driver, user_uid: str) -> str:
    """Resolve the user's company ID from the graph.

    Args:
        driver: Neo4j driver.
        user_uid: Clerk user ID.

    Returns:
        The company_id string.

    Raises:
        HTTPException: If no company found for user.
    """
    with driver.session() as session:
        result = session.run(
            "MATCH (c:Company {created_by: $uid}) RETURN c.id AS id LIMIT 1",
            uid=user_uid,
        )
        record = result.single()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company found for current user",
        )
    return record["id"]


# -- Endpoints -------------------------------------------------------------------


@router.get("/me/conversations")
def list_conversations(
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
    project_id: str | None = Query(None, description="Filter by project"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List conversations for the current user's company.

    Returns paginated conversation list with total count.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    if project_id:
        return conv_service.list_by_project(company_id, project_id, limit, offset)
    return conv_service.list_by_company(company_id, limit, offset)


@router.get("/me/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
    msg_service: Annotated[MessageService, Depends(get_message_service)],
    include_messages: bool = Query(True, description="Include messages in response"),
    message_limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """Get a conversation with its messages.

    Returns the conversation details and optionally its message history.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    try:
        conversation = conv_service.get(company_id, conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {conversation_id}",
        )

    result: dict[str, Any] = {"conversation": conversation}

    if include_messages:
        messages = msg_service.list_by_conversation(
            conversation_id, limit=message_limit,
        )
        result["messages"] = messages["messages"]
        result["message_count"] = messages["total"]

    return result


@router.post("/me/conversations/search")
def search_conversations(
    body: ConversationSearchRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
) -> dict[str, Any]:
    """Search conversations using hybrid vector + graph search.

    Combines vector similarity search on Message.embedding with graph
    traversal for company/project filtering. Falls back to text search
    if embeddings are unavailable.
    """
    user_uid = current_user["uid"]
    company_id = _resolve_company_id(driver, user_uid)

    # Try vector search first
    query_embedding = embedding_service.generate_query_embedding(body.query)

    if query_embedding:
        results = _vector_search(
            driver, company_id, query_embedding,
            project_id=body.project_id,
            limit=body.limit,
        )
    else:
        results = _text_search(
            driver, company_id, body.query,
            project_id=body.project_id,
            limit=body.limit,
        )

    return {"results": results, "total": len(results), "query": body.query}


def _vector_search(
    driver: Driver,
    company_id: str,
    embedding: list[float],
    project_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Search messages by vector similarity scoped to a company.

    Args:
        driver: Neo4j driver.
        company_id: Company scope.
        embedding: Query embedding vector.
        project_id: Optional project filter.
        limit: Max results.

    Returns:
        List of search result dicts.
    """
    try:
        with driver.session() as session:
            if project_id:
                result = session.run(
                    """
                    CALL db.index.vector.queryNodes('message-embeddings', $top_k, $embedding)
                    YIELD node AS msg, score
                    MATCH (msg)-[:PART_OF]->(conv:Conversation)<-[:HAS_CONVERSATION]-(c:Company {id: $company_id})
                    MATCH (conv)-[:ABOUT_PROJECT]->(p:Project {id: $project_id})
                    RETURN msg.id AS message_id, conv.id AS conversation_id,
                           msg.content AS content, msg.role AS role,
                           msg.timestamp AS timestamp, score AS similarity
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    {
                        "embedding": embedding,
                        "top_k": limit * 3,
                        "company_id": company_id,
                        "project_id": project_id,
                        "limit": limit,
                    },
                )
            else:
                result = session.run(
                    """
                    CALL db.index.vector.queryNodes('message-embeddings', $top_k, $embedding)
                    YIELD node AS msg, score
                    MATCH (msg)-[:PART_OF]->(conv:Conversation)<-[:HAS_CONVERSATION]-(c:Company {id: $company_id})
                    RETURN msg.id AS message_id, conv.id AS conversation_id,
                           msg.content AS content, msg.role AS role,
                           msg.timestamp AS timestamp, score AS similarity
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    {
                        "embedding": embedding,
                        "top_k": limit * 3,
                        "company_id": company_id,
                        "limit": limit,
                    },
                )
            return [dict(record) for record in result]
    except Exception:
        logger.warning("Vector search failed, falling back to text", exc_info=True)
        return _text_search(driver, company_id, "", project_id=project_id, limit=limit)


def _text_search(
    driver: Driver,
    company_id: str,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Fallback text search using CONTAINS on message content.

    Args:
        driver: Neo4j driver.
        company_id: Company scope.
        query: Text to search for.
        project_id: Optional project filter.
        limit: Max results.

    Returns:
        List of search result dicts.
    """
    try:
        with driver.session() as session:
            if project_id:
                result = session.run(
                    """
                    MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
                          -[:ABOUT_PROJECT]->(p:Project {id: $project_id})
                    MATCH (msg:Message)-[:PART_OF]->(conv)
                    WHERE toLower(msg.content) CONTAINS toLower($query)
                    RETURN msg.id AS message_id, conv.id AS conversation_id,
                           msg.content AS content, msg.role AS role,
                           msg.timestamp AS timestamp, null AS similarity
                    ORDER BY msg.timestamp DESC
                    LIMIT $limit
                    """,
                    {
                        "company_id": company_id,
                        "project_id": project_id,
                        "query": query,
                        "limit": limit,
                    },
                )
            else:
                result = session.run(
                    """
                    MATCH (c:Company {id: $company_id})-[:HAS_CONVERSATION]->(conv:Conversation)
                    MATCH (msg:Message)-[:PART_OF]->(conv)
                    WHERE toLower(msg.content) CONTAINS toLower($query)
                    RETURN msg.id AS message_id, conv.id AS conversation_id,
                           msg.content AS content, msg.role AS role,
                           msg.timestamp AS timestamp, null AS similarity
                    ORDER BY msg.timestamp DESC
                    LIMIT $limit
                    """,
                    {
                        "company_id": company_id,
                        "query": query,
                        "limit": limit,
                    },
                )
            return [dict(record) for record in result]
    except Exception:
        logger.warning("Text search failed", exc_info=True)
        return []
