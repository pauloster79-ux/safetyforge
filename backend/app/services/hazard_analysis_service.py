"""AI-powered photo hazard analysis service using Claude Vision."""

import json
import logging

import anthropic

from app.config import Settings
from app.exceptions import GenerationError

logger = logging.getLogger(__name__)

_PHOTO_ANALYSIS_SYSTEM_PROMPT = """You are an expert OSHA Compliance Safety and Health Officer examining a construction site photograph. Analyze this image for safety hazards, violations, and areas of concern.

For each hazard identified, provide:
1. "description": Clear description of the hazard
2. "severity": "imminent_danger", "high", "medium", or "low"
3. "osha_standard": The specific OSHA standard being violated (e.g., "29 CFR 1926.451(g)(1)")
4. "category": Category (Fall Protection, Housekeeping, PPE, Electrical, Struck-By, Excavation, Scaffolding, Fire Safety, Respiratory, Noise, Other)
5. "recommended_action": Specific corrective action
6. "location_in_image": Where in the image the hazard is visible

Also provide:
- "summary": A 2-3 sentence overall assessment
- "positive_observations": Any good safety practices visible (PPE worn correctly, barricades in place, etc.)

Return ONLY valid JSON with the following structure:
{
  "identified_hazards": [...],
  "summary": "...",
  "positive_observations": ["..."]
}

Be thorough but avoid false positives — only flag genuine hazards visible in the image."""


class HazardAnalysisService:
    """Analyzes construction site photos for safety hazards using Claude Vision.

    Args:
        settings: Application settings containing the Anthropic API key.
    """

    def __init__(self, settings: Settings) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def analyze_photo(
        self,
        image_base64: str,
        image_media_type: str,
        context: dict,
    ) -> dict:
        """Analyze a construction site photo for safety hazards.

        Args:
            image_base64: Base64-encoded image data (without data URI prefix).
            image_media_type: MIME type (image/jpeg, image/png, image/gif, image/webp).
            context: Dict with optional keys: description, location, project_name.

        Returns:
            Dict with identified_hazards list, summary, and positive_observations.

        Raises:
            GenerationError: If the API call fails or returns invalid JSON.
        """
        context_parts = []
        if context.get("project_name"):
            context_parts.append(f"Project: {context['project_name']}")
        if context.get("description"):
            context_parts.append(f"Description: {context['description']}")
        if context.get("location"):
            context_parts.append(f"Location: {context['location']}")

        context_text = (
            "\n".join(context_parts) if context_parts else "No additional context provided."
        )

        user_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type,
                    "data": image_base64,
                },
            },
            {
                "type": "text",
                "text": (
                    f"Analyze this construction site photo for safety hazards.\n\n"
                    f"Context about this site:\n{context_text}\n\n"
                    f"Return ONLY valid JSON."
                ),
            },
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=_PHOTO_ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic API authentication failed: %s", exc)
            raise GenerationError(
                "AI analysis service authentication failed",
                detail="Invalid API key configuration",
            )
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic API rate limit hit: %s", exc)
            raise GenerationError(
                "AI analysis service is temporarily busy. Please try again in a moment.",
                detail="Rate limit exceeded",
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during photo analysis: %s", exc)
            raise GenerationError(
                "AI analysis service encountered an error",
                detail=str(exc),
            )

        raw_text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            first_newline = raw_text.index("\n")
            raw_text = raw_text[first_newline + 1 :]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].rstrip()

        try:
            content = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI photo analysis as JSON: %s", exc)
            logger.debug("Raw response: %s", raw_text[:500])
            raise GenerationError(
                "AI analysis could not be parsed. Please try again.",
                detail=f"JSON parse error: {exc}",
            )

        if not isinstance(content, dict):
            raise GenerationError(
                "AI analysis was not in the expected format. Please try again.",
                detail=f"Expected dict, got {type(content).__name__}",
            )

        return content
