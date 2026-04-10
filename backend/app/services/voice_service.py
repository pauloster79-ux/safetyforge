"""Voice-to-structured-data service using Claude for transcription and parsing."""

import json
import logging

import anthropic

from app.config import Settings
from app.exceptions import GenerationError

logger = logging.getLogger(__name__)

_TRANSCRIBE_SYSTEM = """You are transcribing audio from a construction site worker.
The speaker may be in a noisy environment with machinery, wind, or other workers talking.
Transcribe exactly what was said, preserving construction terminology and safety-specific language.
Return ONLY the transcript text, nothing else."""

_PARSE_INSPECTION_SYSTEM = """You are an expert safety inspector parsing a foreman's verbal walkthrough into structured inspection data.

The foreman walks a construction site and narrates what they see. Your job is to extract:
1. Which checklist items they referenced (match to the template if provided)
2. Whether each item passed, failed, or was not applicable
3. Any notes or observations for each item
4. Overall notes and corrective actions needed

Rules:
- "looks good", "in place", "secure", "solid", "fine" → status: "pass"
- "fail", "failed", "issue", "problem", "violation", "exposed", "missing", "broken" → status: "fail"
- "not applicable", "N/A", "doesn't apply", "skip" → status: "na"
- If the foreman mentions taking a photo, note it but don't create a photo_url
- Extract any corrective actions mentioned (e.g., "need to fix", "have to replace", "talked to him about it")

Return ONLY valid JSON with this structure:
{
  "items": [
    {
      "item_id": "matched_template_id or auto_generated",
      "category": "category name",
      "description": "what was inspected",
      "status": "pass|fail|na",
      "notes": "any observations"
    }
  ],
  "notes": "overall inspection notes",
  "corrective_actions": "actions needed"
}"""

_PARSE_INCIDENT_SYSTEM = """You are a safety officer parsing a verbal incident report into structured OSHA-format data.

A worker or foreman is describing a safety incident that occurred on a construction site. Extract all relevant fields for an incident report.

Severity classification:
- "fatality" — someone died
- "hospitalization" — required hospitalization
- "medical_treatment" — required professional medical treatment beyond first aid
- "first_aid" — minor injury treated on site
- "near_miss" — no injury but could have been serious
- "property_damage" — damage to equipment or property only

Return ONLY valid JSON:
{
  "location": "where on site the incident occurred",
  "severity": "fatality|hospitalization|medical_treatment|first_aid|near_miss|property_damage",
  "description": "detailed description of what happened",
  "persons_involved": "names/roles of people involved",
  "witnesses": "names/roles of witnesses",
  "immediate_actions_taken": "what was done immediately after"
}"""


class VoiceService:
    """Processes voice recordings into structured safety data using Claude.

    Uses Claude's audio understanding to transcribe and parse construction
    site voice recordings into structured inspection, incident, and hazard
    report data.

    Args:
        settings: Application settings containing the Anthropic API key.
    """

    def __init__(self, settings: Settings) -> None:
        if settings.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            self.client = None
        self.model = "claude-sonnet-4-20250514"

    def transcribe(self, audio_base64: str, media_type: str = "audio/webm") -> str:
        """Transcribe audio to text using Claude.

        Args:
            audio_base64: Base64-encoded audio data.
            media_type: Audio MIME type.

        Returns:
            Transcribed text.

        Raises:
            GenerationError: If transcription fails.
        """
        if not self.client:
            raise GenerationError(
                "Voice service unavailable",
                detail="Anthropic API key not configured",
            )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=_TRANSCRIBE_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": audio_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Transcribe this audio recording from a construction site.",
                            },
                        ],
                    }
                ],
            )
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic API authentication failed: %s", exc)
            raise GenerationError(
                "Voice service authentication failed",
                detail="Invalid API key configuration",
            )
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic API rate limit hit: %s", exc)
            raise GenerationError(
                "Voice service is temporarily busy. Please try again in a moment.",
                detail="Rate limit exceeded",
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during transcription: %s", exc)
            raise GenerationError(
                "Voice transcription failed",
                detail=str(exc),
            )

        return response.content[0].text.strip()

    def parse_inspection(
        self,
        transcript: str,
        inspection_type: str = "daily_site",
        checklist_template: list[dict] | None = None,
    ) -> dict:
        """Parse a voice transcript into structured inspection data.

        Args:
            transcript: Transcribed voice recording.
            inspection_type: Type of inspection for context.
            checklist_template: Optional checklist template to match items against.

        Returns:
            Dict with items, notes, and corrective_actions.

        Raises:
            GenerationError: If parsing fails.
        """
        template_text = ""
        if checklist_template:
            items_desc = "\n".join(
                f"- [{item.get('item_id', 'unknown')}] {item.get('category', '')}: {item.get('description', '')}"
                for item in checklist_template
            )
            template_text = f"\n\nCHECKLIST TEMPLATE (match items to these when possible):\n{items_desc}"

        user_text = (
            f"Parse this inspection walkthrough transcript into structured checklist data.\n\n"
            f"Inspection type: {inspection_type}{template_text}\n\n"
            f"TRANSCRIPT:\n{transcript}\n\n"
            f"Return ONLY valid JSON."
        )

        return self._call_claude_json(_PARSE_INSPECTION_SYSTEM, user_text)

    def parse_incident(self, transcript: str) -> dict:
        """Parse a voice transcript into structured incident report data.

        Args:
            transcript: Transcribed voice recording describing an incident.

        Returns:
            Dict with location, severity, description, persons_involved,
            witnesses, and immediate_actions_taken.

        Raises:
            GenerationError: If parsing fails.
        """
        user_text = (
            f"Parse this incident report into structured data.\n\n"
            f"TRANSCRIPT:\n{transcript}\n\n"
            f"Return ONLY valid JSON."
        )

        return self._call_claude_json(_PARSE_INCIDENT_SYSTEM, user_text)

    def _call_claude_json(self, system_prompt: str, user_text: str) -> dict:
        """Call Claude and parse the JSON response.

        Args:
            system_prompt: System prompt for the call.
            user_text: User message text.

        Returns:
            Parsed JSON dict.

        Raises:
            GenerationError: If the call fails or returns invalid JSON.
        """
        if not self.client:
            raise GenerationError(
                "Voice service unavailable",
                detail="Anthropic API key not configured",
            )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_text}],
            )
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic API auth failed: %s", exc)
            raise GenerationError("Voice service authentication failed")
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic API rate limit: %s", exc)
            raise GenerationError("Voice service is temporarily busy.")
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise GenerationError("Voice processing failed", detail=str(exc))

        raw_text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw_text = "\n".join(lines)

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Claude response as JSON: %s", raw_text[:200])
            raise GenerationError(
                "Voice processing returned invalid data",
                detail=f"JSON parse error: {exc}",
            )

        if not isinstance(result, dict):
            raise GenerationError("Voice processing returned unexpected format")

        return result
