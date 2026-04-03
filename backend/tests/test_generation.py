"""Tests for the AI document generation service."""

from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import GenerationError
from app.services.generation_service import GenerationService, _SYSTEM_PROMPTS
from tests.conftest import TEST_SETTINGS


class TestGenerationReturnsValidJson:
    """Tests for generate_document output structure."""

    def test_generation_returns_valid_json(self) -> None:
        """Generation service returns a dict when the API returns valid JSON.

        Mocks the external Anthropic client (external dependency -- allowed).
        """
        service = GenerationService(TEST_SETTINGS)

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"project_overview": "Test overview", "hazard_assessment": []}'
            )
        ]

        with patch.object(service.client.messages, "create", return_value=mock_response):
            result = service.generate_document(
                template_type="sssp",
                company_info={"company_name": "Test Co", "address": "123 Test St"},
                project_info={"project_name": "Test", "site_address": "456 Site Rd"},
            )

        assert isinstance(result, dict)
        assert "project_overview" in result

    def test_generation_handles_markdown_fenced_json(self) -> None:
        """Generation service strips markdown code fences from API responses."""
        service = GenerationService(TEST_SETTINGS)

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='```json\n{"topic_overview": "Safety first"}\n```'
            )
        ]

        with patch.object(service.client.messages, "create", return_value=mock_response):
            result = service.generate_document(
                template_type="toolbox_talk",
                company_info={"company_name": "Test Co"},
                project_info={"topic": "Fall protection"},
            )

        assert isinstance(result, dict)
        assert result["topic_overview"] == "Safety first"

    def test_generation_invalid_json_raises(self) -> None:
        """Generation service raises GenerationError for non-JSON responses."""
        service = GenerationService(TEST_SETTINGS)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON at all")]

        with patch.object(service.client.messages, "create", return_value=mock_response):
            with pytest.raises(GenerationError, match="could not be parsed"):
                service.generate_document(
                    template_type="sssp",
                    company_info={"company_name": "Test Co"},
                    project_info={"project_name": "Test"},
                )

    def test_generation_non_dict_raises(self) -> None:
        """Generation service raises GenerationError for non-dict JSON."""
        service = GenerationService(TEST_SETTINGS)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='["not", "a", "dict"]')]

        with patch.object(service.client.messages, "create", return_value=mock_response):
            with pytest.raises(GenerationError, match="not in the expected format"):
                service.generate_document(
                    template_type="sssp",
                    company_info={"company_name": "Test Co"},
                    project_info={"project_name": "Test"},
                )


class TestDocumentTypePrompts:
    """Tests for system prompt coverage."""

    def test_all_document_types_have_prompts(self) -> None:
        """Every DocumentType enum value has a corresponding system prompt."""
        from app.models.document import DocumentType

        for doc_type in DocumentType:
            assert doc_type.value in _SYSTEM_PROMPTS, (
                f"Missing system prompt for document type: {doc_type.value}"
            )

    def test_unknown_document_type_raises_error(self) -> None:
        """Requesting generation for an unknown type raises GenerationError."""
        service = GenerationService(TEST_SETTINGS)

        with pytest.raises(GenerationError, match="No generation prompt configured"):
            service.generate_document(
                template_type="totally_fake_type",
                company_info={"company_name": "Test"},
                project_info={"name": "Test"},
            )

    def test_prompts_are_non_empty(self) -> None:
        """All system prompts are non-empty strings."""
        for doc_type, prompt in _SYSTEM_PROMPTS.items():
            assert isinstance(prompt, str), f"Prompt for {doc_type} is not a string"
            assert len(prompt) > 100, f"Prompt for {doc_type} seems too short"
