"""Voice input endpoints for speech-to-structured-data processing."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_voice_service
from app.exceptions import GenerationError
from app.middleware.feature_gate import require_feature
from app.models.voice import (
    ParseIncidentRequest,
    ParseIncidentResponse,
    ParseInspectionRequest,
    ParseInspectionResponse,
    TranscribeRequest,
    TranscribeResponse,
)
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/me/voice", tags=["voice"])


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    dependencies=[Depends(require_feature("voice_input"))],
)
async def transcribe_audio(
    data: TranscribeRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
) -> TranscribeResponse:
    """Transcribe audio recording to text.

    Accepts base64-encoded audio and returns a text transcript.
    Supports webm, wav, and mp4 audio formats.

    Args:
        data: Audio data and media type.
        current_user: Authenticated user claims.
        voice_service: VoiceService dependency.

    Returns:
        TranscribeResponse with the transcript text.
    """
    try:
        transcript = voice_service.transcribe(data.audio_base64, data.media_type)
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return TranscribeResponse(transcript=transcript)


@router.post(
    "/parse-inspection",
    response_model=ParseInspectionResponse,
    dependencies=[Depends(require_feature("voice_input"))],
)
async def parse_inspection_transcript(
    data: ParseInspectionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
) -> ParseInspectionResponse:
    """Parse a voice transcript into structured inspection checklist data.

    Takes a transcript of a foreman's verbal site walkthrough and extracts
    structured checklist items with pass/fail/na status, notes, and
    corrective actions.

    Args:
        data: Transcript text, inspection type, and optional checklist template.
        current_user: Authenticated user claims.
        voice_service: VoiceService dependency.

    Returns:
        ParseInspectionResponse with structured checklist items.
    """
    try:
        result = voice_service.parse_inspection(
            transcript=data.transcript,
            inspection_type=data.inspection_type,
            checklist_template=data.checklist_template,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return ParseInspectionResponse(
        items=result.get("items", []),
        notes=result.get("notes", ""),
        corrective_actions=result.get("corrective_actions", ""),
    )


@router.post(
    "/parse-incident",
    response_model=ParseIncidentResponse,
    dependencies=[Depends(require_feature("voice_input"))],
)
async def parse_incident_transcript(
    data: ParseIncidentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
) -> ParseIncidentResponse:
    """Parse a voice transcript into structured incident report data.

    Takes a natural-language description of a safety incident and extracts
    OSHA-format fields: location, severity, description, persons involved,
    witnesses, and immediate actions taken.

    Args:
        data: Transcript text describing the incident.
        current_user: Authenticated user claims.
        voice_service: VoiceService dependency.

    Returns:
        ParseIncidentResponse with structured incident fields.
    """
    try:
        result = voice_service.parse_incident(data.transcript)
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return ParseIncidentResponse(
        location=result.get("location", ""),
        severity=result.get("severity", "near_miss"),
        description=result.get("description", ""),
        persons_involved=result.get("persons_involved", ""),
        witnesses=result.get("witnesses", ""),
        immediate_actions_taken=result.get("immediate_actions_taken", ""),
    )
