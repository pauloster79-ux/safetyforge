"""AI document generation service using the Claude API.

Generates jurisdiction-aware safety documents by loading system prompts
from the appropriate jurisdiction pack.
"""

import json
import logging
from typing import Any

import anthropic

from app.config import Settings
from app.exceptions import GenerationError
from app.jurisdiction.context import JurisdictionContext
from app.jurisdiction.loader import JurisdictionLoader

logger = logging.getLogger(__name__)


class GenerationService:
    """Generates safety document content using the Claude API.

    Prompts are loaded from jurisdiction packs rather than being hardcoded,
    allowing the same service to generate documents compliant with any
    supported jurisdiction's regulations.

    Args:
        settings: Application settings containing the Anthropic API key.
    """

    def __init__(self, settings: Settings) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def _build_user_prompt(
        self,
        template_type: str,
        company_info: dict[str, Any],
        project_info: dict[str, Any],
        ctx: JurisdictionContext,
    ) -> str:
        """Build the user message with company, project, and jurisdiction details.

        Args:
            template_type: The document type being generated.
            company_info: Company profile data.
            project_info: Project-specific input data.
            ctx: Jurisdiction context for regulatory awareness.

        Returns:
            A formatted user prompt string.
        """
        company_section = "\n".join(
            f"  - {key}: {value}" for key, value in company_info.items() if value
        )
        project_section = "\n".join(
            f"  - {key}: {value}" for key, value in project_info.items() if value
        )

        # Add jurisdiction context to help the AI
        jurisdiction_section = (
            f"  - Country: {ctx.manifest.get('name', ctx.code)}\n"
            f"  - Regulatory Body: {ctx.regulatory_body}\n"
            f"  - Primary Legislation: {ctx.primary_legislation}\n"
            f"  - Construction Legislation: {ctx.construction_legislation}\n"
            f"  - Measurement System: {ctx.measurement_system}\n"
            f"  - Temperature Unit: {ctx.temperature_unit}"
        )

        doc_type = ctx.get_document_type_by_id(template_type)
        doc_name = doc_type["name"] if doc_type else template_type.replace("_", " ").title()

        return f"""Generate a {doc_name} document for the following project.

COMPANY INFORMATION:
{company_section}

PROJECT INFORMATION:
{project_section}

JURISDICTION CONTEXT:
{jurisdiction_section}

Generate comprehensive, site-specific content for all required sections. Return ONLY valid JSON."""

    def _parse_ai_response(self, raw_text: str) -> dict[str, Any]:
        """Parse and validate AI response JSON.

        Args:
            raw_text: Raw text from the Claude API response.

        Returns:
            Parsed dict content.

        Raises:
            GenerationError: If the response is not valid JSON or not a dict.
        """
        text = raw_text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()

        try:
            content = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI response as JSON: %s", exc)
            logger.debug("Raw response: %s", text[:500])
            raise GenerationError(
                "AI generated content could not be parsed. Please try again.",
                detail=f"JSON parse error: {exc}",
            )

        if not isinstance(content, dict):
            raise GenerationError(
                "AI generated content was not in the expected format. Please try again.",
                detail=f"Expected dict, got {type(content).__name__}",
            )

        return content

    def _call_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Call the Claude API and return the raw response text.

        Args:
            system_prompt: The system prompt.
            user_prompt: The user message.

        Returns:
            Raw text from the API response.

        Raises:
            GenerationError: If the API call fails.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.AuthenticationError as exc:
            logger.error("Anthropic API authentication failed: %s", exc)
            raise GenerationError(
                "AI generation service authentication failed",
                detail="Invalid API key configuration",
            )
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic API rate limit hit: %s", exc)
            raise GenerationError(
                "AI generation service is temporarily busy. Please try again in a moment.",
                detail="Rate limit exceeded",
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s", exc)
            raise GenerationError(
                "AI generation service encountered an error",
                detail=str(exc),
            )

        return response.content[0].text

    def generate_document(
        self,
        template_type: str,
        company_info: dict[str, Any],
        project_info: dict[str, Any],
        jurisdiction_code: str = "US",
        jurisdiction_region: str | None = None,
    ) -> dict[str, Any]:
        """Generate document content using the Claude API.

        Loads the system prompt from the appropriate jurisdiction pack,
        allowing the same method to generate OSHA-compliant SSSPs for
        US companies and CDM-compliant CPPs for UK companies.

        Args:
            template_type: Document type key (e.g. 'sssp', 'construction_phase_plan').
            company_info: Company profile data.
            project_info: Project-specific input fields.
            jurisdiction_code: Country code for prompt selection.
            jurisdiction_region: Optional sub-national region.

        Returns:
            A dict of generated content sections keyed by section ID.

        Raises:
            GenerationError: If the API call fails or returns invalid JSON.
        """
        ctx = JurisdictionLoader.load(jurisdiction_code, jurisdiction_region)

        # Try loading the prompt for this specific document type
        try:
            system_prompt = ctx.get_prompt(template_type)
        except (ValueError, FileNotFoundError) as exc:
            # Try mapping via universal key if the direct type isn't found
            logger.info(
                "No direct prompt for '%s' in %s, trying universal mapping",
                template_type,
                jurisdiction_code,
            )
            # Check if this is a universal key that maps to a local doc type
            dt = ctx.get_document_type_by_universal(template_type)
            if dt:
                try:
                    system_prompt = ctx.get_prompt(dt["id"])
                except (ValueError, FileNotFoundError):
                    raise GenerationError(
                        f"No generation prompt configured for document type "
                        f"'{template_type}' in jurisdiction '{jurisdiction_code}'",
                        detail=str(exc),
                    )
            else:
                raise GenerationError(
                    f"No generation prompt configured for document type "
                    f"'{template_type}' in jurisdiction '{jurisdiction_code}'",
                    detail=str(exc),
                )

        user_prompt = self._build_user_prompt(template_type, company_info, project_info, ctx)
        raw_text = self._call_claude(system_prompt, user_prompt)
        return self._parse_ai_response(raw_text)

    def generate_toolbox_talk(
        self,
        topic: str,
        company_info: dict[str, Any],
        project_info: dict[str, Any],
        language: str = "both",
        custom_points: str = "",
        jurisdiction_code: str = "US",
        jurisdiction_region: str | None = None,
    ) -> dict[str, Any]:
        """Generate toolbox talk content, optionally bilingual.

        Args:
            topic: The safety topic for the toolbox talk.
            company_info: Company profile data.
            project_info: Project-specific data.
            language: Target language — "en", "es", or "both".
            custom_points: Optional custom talking points to incorporate.
            jurisdiction_code: Country code for prompt selection.
            jurisdiction_region: Optional sub-national region.

        Returns:
            A dict with language keys mapping to content sections.

        Raises:
            GenerationError: If the API call fails or returns invalid JSON.
        """
        ctx = JurisdictionLoader.load(jurisdiction_code, jurisdiction_region)

        # Load toolbox talk prompt from jurisdiction pack
        try:
            system_prompt = ctx.get_prompt("toolbox_talk")
        except (ValueError, FileNotFoundError):
            raise GenerationError(
                f"No toolbox talk prompt configured for jurisdiction '{jurisdiction_code}'"
            )

        # Determine languages from jurisdiction
        supported_languages = ctx.languages
        primary_lang = supported_languages[0].split("-")[0] if supported_languages else "en"

        # Build language instruction
        if language == "both":
            language_instruction = (
                f"Generate the content in BOTH {primary_lang.upper()} and the "
                f"secondary workforce language. Return a JSON object with language "
                f"code keys (e.g. \"en\", \"es\"). Each key maps to an object with "
                f"the sections described above. Write each language independently "
                f"with culturally appropriate phrasing and terminology."
            )
        elif language != primary_lang:
            language_instruction = (
                f"Generate the content ONLY in {language}. "
                f"Return a JSON object with one top-level key: \"{language}\"."
            )
        else:
            language_instruction = (
                f"Generate the content ONLY in {primary_lang}. "
                f"Return a JSON object with one top-level key: \"{primary_lang}\"."
            )

        company_section = "\n".join(
            f"  - {key}: {value}" for key, value in company_info.items() if value
        )
        project_section = "\n".join(
            f"  - {key}: {value}" for key, value in project_info.items() if value
        )

        jurisdiction_section = (
            f"  - Country: {ctx.manifest.get('name', ctx.code)}\n"
            f"  - Regulatory Body: {ctx.regulatory_body}\n"
            f"  - Primary Legislation: {ctx.primary_legislation}"
        )

        custom_section = ""
        if custom_points:
            custom_section = f"\nCUSTOM TALKING POINTS TO INCORPORATE:\n{custom_points}\n"

        user_prompt = f"""Generate a Toolbox Talk on the following topic: {topic}

COMPANY INFORMATION:
{company_section}

PROJECT INFORMATION:
{project_section}

JURISDICTION CONTEXT:
{jurisdiction_section}
{custom_section}
LANGUAGE INSTRUCTIONS:
{language_instruction}

Generate comprehensive, site-specific content for all required sections. Return ONLY valid JSON."""

        raw_text = self._call_claude(system_prompt, user_prompt)
        return self._parse_ai_response(raw_text)

    def translate_content(
        self,
        content_dict: dict[str, Any],
        target_language: str = "es",
        jurisdiction_code: str = "US",
    ) -> dict[str, Any]:
        """Translate existing document content to another language.

        Args:
            content_dict: The source content sections to translate.
            target_language: Target language code.
            jurisdiction_code: Country code for terminology context.

        Returns:
            A dict with translated content sections.

        Raises:
            GenerationError: If the API call fails or returns invalid JSON.
        """
        ctx = JurisdictionLoader.load(jurisdiction_code)
        country_name = ctx.manifest.get("name", jurisdiction_code)

        language_names = {"es": "Spanish", "en": "English", "fr": "French", "de": "German", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "zh": "Chinese"}
        language_name = language_names.get(target_language, target_language)

        system_prompt = (
            f"You are a professional {language_name} translator specializing in "
            f"construction safety documentation for {country_name}."
        )

        user_prompt = f"""Translate the following construction safety document content to {language_name}.
Use professional construction safety terminology appropriate for {country_name}.
Write naturally with culturally appropriate phrasing — do not produce a literal machine translation.

SOURCE CONTENT (JSON):
{json.dumps(content_dict, indent=2, ensure_ascii=False)}

Return the translated content as a valid JSON object with the same structure and keys as the source. Return ONLY valid JSON."""

        raw_text = self._call_claude(system_prompt, user_prompt)
        return self._parse_ai_response(raw_text)
