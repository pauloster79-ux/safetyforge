"""Chat router — SSE streaming endpoint for conversational AI."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.models.chat import ChatEvent, ChatRequest
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.services.embedding_service import EmbeddingService
from app.services.event_bus import EventBus
from app.services.inspection_service import InspectionService
from app.services.inspection_template_service import InspectionTemplateService
from app.services.mcp_tools import MCPToolService
from app.services.memory_extraction_service import MemoryExtractionService
from app.services.message_service import MessageService
from app.services.neo4j_client import get_sync_driver

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def get_chat_service(request: Request) -> ChatService:
    """Assemble ChatService from app state and fresh service instances."""
    settings = get_settings()
    driver = get_sync_driver()

    mcp_tools: MCPToolService = request.app.state.mcp_tools
    event_bus: EventBus = request.app.state.event_bus

    # Conversation persistence services
    conversation_service = ConversationService(driver)
    message_service = MessageService(driver)
    embedding_service = EmbeddingService(driver, settings)

    # Memory extraction (requires LLM service from app state)
    memory_extraction_service = None
    if hasattr(request.app.state, "llm_service"):
        memory_extraction_service = MemoryExtractionService(
            driver, request.app.state.llm_service,
        )

    return ChatService(
        settings=settings,
        mcp_tools=mcp_tools,
        template_service=InspectionTemplateService(),
        inspection_service=InspectionService(driver),
        event_bus=event_bus,
        conversation_service=conversation_service,
        message_service=message_service,
        embedding_service=embedding_service,
        memory_extraction_service=memory_extraction_service,
    )


async def _sse_generator(
    chat_service: ChatService,
    data: ChatRequest,
    user_id: str,
) -> AsyncGenerator[str, None]:
    """Wrap ChatService stream as SSE-formatted text lines."""
    async for event in chat_service.stream_response(
        session_id=data.session_id,
        message=data.message,
        company_id=data.company_id,
        project_id=data.project_id,
        mode=data.mode,
        inspection_type=data.inspection_type,
        user_id=user_id,
    ):
        payload = json.dumps(event.model_dump(), default=str)
        yield f"data: {payload}\n\n"


@router.post("/me/chat")
async def chat_stream(
    data: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> StreamingResponse:
    """Stream a chat response as Server-Sent Events.

    Accepts a user message and returns a stream of ChatEvent objects.
    Supports two modes: 'general' for open-ended queries, 'inspection'
    for guided checklist flows.
    """
    user_id = current_user["uid"]

    return StreamingResponse(
        _sse_generator(chat_service, data, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
