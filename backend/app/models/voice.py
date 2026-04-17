"""Voice input models for speech-to-structured-data processing."""

from datetime import datetime

from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    """Request to transcribe audio to text."""

    audio_base64: str = Field(..., description="Base64-encoded audio data")
    media_type: str = Field(
        default="audio/webm", description="Audio MIME type (audio/webm, audio/wav, audio/mp4)"
    )


class TranscribeResponse(BaseModel):
    """Response from audio transcription."""

    transcript: str = Field(..., description="Transcribed text from audio")


class ParseInspectionRequest(BaseModel):
    """Request to parse a voice transcript into structured inspection data."""

    transcript: str = Field(..., description="Voice transcript to parse")
    inspection_type: str = Field(
        default="daily_site", description="Inspection type for context"
    )
    checklist_template: list[dict] = Field(
        default_factory=list,
        description="Checklist template items for matching (each has item_id, category, description)",
    )


class ParseInspectionResponse(BaseModel):
    """Structured inspection data extracted from voice."""

    items: list[dict] = Field(
        default_factory=list,
        description="Checklist items with status (pass/fail/na), notes, matched item_id",
    )
    notes: str = Field(default="", description="Overall inspection notes")
    corrective_actions: str = Field(default="", description="Corrective actions identified")


class ParseIncidentRequest(BaseModel):
    """Request to parse a voice transcript into structured incident data."""

    transcript: str = Field(..., description="Voice transcript describing an incident")


class ParseIncidentResponse(BaseModel):
    """Structured incident data extracted from voice."""

    location: str = Field(default="", description="Incident location")
    severity: str = Field(default="near_miss", description="Incident severity")
    description: str = Field(default="", description="Incident description")
    persons_involved: str = Field(default="", description="Persons involved")
    witnesses: str = Field(default="", description="Witnesses")
    immediate_actions_taken: str = Field(default="", description="Actions taken")


class Conversation(BaseModel):
    """A conversation session in the new ontology.

    Replaces VoiceSession — absorbed into Conversation with a 'mode' field.
    Use mode='voice' for voice sessions.
    """

    id: str
    company_id: str
    mode: str = Field(
        default="voice",
        description="Conversation mode: 'voice', 'text', or 'agent'",
    )
    transcript: str = Field(default="", description="Full conversation transcript")
    structured_data: dict = Field(
        default_factory=dict,
        description="Structured data extracted from the conversation",
    )
    created_at: datetime
    created_by: str
    created_by_type: str = Field(default="human", description="Actor type: 'human' or 'agent'")


# Backward-compat alias
VoiceSession = Conversation
