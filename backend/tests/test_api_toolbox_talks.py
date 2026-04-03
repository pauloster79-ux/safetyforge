"""API contract tests for toolbox talk endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/me/projects",
        json={
            "name": "Toolbox Talk Test Project",
            "address": "789 Safety Blvd, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestCreateToolboxTalk:
    """Tests for POST /me/projects/{project_id}/toolbox-talks."""

    def test_create_toolbox_talk(self, client: TestClient, test_company):
        """Create a toolbox talk without generation returns 201."""
        project_id = _create_project(client)

        response = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Fall Protection Awareness",
                "scheduled_date": "2026-04-15",
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "generate_content": False,
                "language": "en",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Fall Protection Awareness"
        assert data["scheduled_date"] == "2026-04-15"
        assert data["target_audience"] == "all_workers"
        assert data["duration_minutes"] == 15
        assert data["status"] == "scheduled"
        assert data["id"].startswith("talk_")
        assert data["project_id"] == project_id
        assert data["attendees"] == []
        assert data["content_en"] == {}
        assert data["content_es"] == {}
        assert data["deleted"] is False

    def test_create_with_generation(self, client: TestClient, test_company):
        """Create a toolbox talk with AI generation mocks the Anthropic client."""
        project_id = _create_project(client)

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"en": {"topic_overview": "Test overview", "key_points": [], "discussion_questions": [], "safety_reminders": [], "osha_references": []}}'
            )
        ]

        with patch(
            "app.services.generation_service.anthropic.Anthropic"
        ) as mock_anthropic:
            mock_client_instance = MagicMock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client_instance

            response = client.post(
                f"/me/projects/{project_id}/toolbox-talks",
                json={
                    "topic": "Scaffolding Safety",
                    "scheduled_date": "2026-04-20",
                    "target_audience": "specific_trade",
                    "target_trade": "scaffolding",
                    "duration_minutes": 20,
                    "generate_content": True,
                    "language": "en",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Scaffolding Safety"
        assert data["content_en"]["topic_overview"] == "Test overview"


class TestListToolboxTalks:
    """Tests for GET /me/projects/{project_id}/toolbox-talks."""

    def test_list_toolbox_talks(self, client: TestClient, test_company):
        """List toolbox talks returns created talks."""
        project_id = _create_project(client)

        # Create two talks
        client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "PPE Requirements",
                "scheduled_date": "2026-04-10",
                "generate_content": False,
            },
        )
        client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Heat Illness Prevention",
                "scheduled_date": "2026-04-11",
                "generate_content": False,
            },
        )

        response = client.get(f"/me/projects/{project_id}/toolbox-talks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["toolbox_talks"]) == 2

    def test_list_toolbox_talks_empty(self, client: TestClient, test_company):
        """List talks for project with no talks returns empty."""
        project_id = _create_project(client)
        response = client.get(f"/me/projects/{project_id}/toolbox-talks")
        assert response.status_code == 200
        data = response.json()
        assert data["toolbox_talks"] == []
        assert data["total"] == 0


class TestGetToolboxTalk:
    """Tests for GET /me/projects/{project_id}/toolbox-talks/{talk_id}."""

    def test_get_toolbox_talk(self, client: TestClient, test_company):
        """Get an existing toolbox talk returns 200."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Electrical Safety",
                "scheduled_date": "2026-04-15",
                "generate_content": False,
            },
        )
        talk_id = create_resp.json()["id"]

        response = client.get(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == talk_id
        assert data["topic"] == "Electrical Safety"

    def test_get_toolbox_talk_not_found(self, client: TestClient, test_company):
        """Get a non-existent toolbox talk returns 404."""
        project_id = _create_project(client)
        response = client.get(
            f"/me/projects/{project_id}/toolbox-talks/talk_nonexistent123"
        )
        assert response.status_code == 404


class TestAddAttendee:
    """Tests for POST /me/projects/{project_id}/toolbox-talks/{talk_id}/attend."""

    def test_add_attendee(self, client: TestClient, test_company):
        """Add an attendee to a toolbox talk returns updated talk."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Ladder Safety",
                "scheduled_date": "2026-04-15",
                "generate_content": False,
            },
        )
        talk_id = create_resp.json()["id"]

        response = client.post(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}/attend",
            json={
                "worker_name": "Juan Garcia",
                "signature_data": "base64sigdata==",
                "language_preference": "es",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["attendees"]) == 1
        assert data["attendees"][0]["worker_name"] == "Juan Garcia"
        assert data["attendees"][0]["signature_data"] == "base64sigdata=="
        assert data["attendees"][0]["language_preference"] == "es"
        assert data["attendees"][0]["signed_at"] is not None

    def test_add_multiple_attendees(self, client: TestClient, test_company):
        """Add multiple attendees accumulates in the list."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Trench Safety",
                "scheduled_date": "2026-04-15",
                "generate_content": False,
            },
        )
        talk_id = create_resp.json()["id"]

        client.post(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}/attend",
            json={"worker_name": "Worker A"},
        )
        response = client.post(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}/attend",
            json={"worker_name": "Worker B"},
        )
        assert response.status_code == 200
        assert len(response.json()["attendees"]) == 2


class TestCompleteTalk:
    """Tests for POST /me/projects/{project_id}/toolbox-talks/{talk_id}/complete."""

    def test_complete_talk(self, client: TestClient, test_company):
        """Complete a toolbox talk sets status and timestamp."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Fire Extinguisher Use",
                "scheduled_date": "2026-04-15",
                "generate_content": False,
            },
        )
        talk_id = create_resp.json()["id"]

        response = client.post(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}/complete",
            json={
                "presented_by": "Mike Foreman",
                "notes": "Good engagement from crew. Hands-on demo was effective.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["presented_by"] == "Mike Foreman"
        assert data["overall_notes"] == "Good engagement from crew. Hands-on demo was effective."
        assert data["presented_at"] is not None


class TestBilingualGeneration:
    """Tests for bilingual generation prompt structure."""

    def test_bilingual_generation_prompt_structure(self, client: TestClient, test_company):
        """Verify the prompt requests both languages when language is 'both'."""
        project_id = _create_project(client)

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='{"en": {"topic_overview": "English overview", "key_points": [], "discussion_questions": [], "safety_reminders": [], "osha_references": []}, "es": {"topic_overview": "Resumen en espanol", "key_points": [], "discussion_questions": [], "safety_reminders": [], "osha_references": []}}'
            )
        ]

        with patch(
            "app.services.generation_service.anthropic.Anthropic"
        ) as mock_anthropic:
            mock_client_instance = MagicMock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client_instance

            response = client.post(
                f"/me/projects/{project_id}/toolbox-talks",
                json={
                    "topic": "Confined Space Entry",
                    "scheduled_date": "2026-04-20",
                    "generate_content": True,
                    "language": "both",
                },
            )

            # Verify the API was called
            assert mock_client_instance.messages.create.called
            call_args = mock_client_instance.messages.create.call_args
            user_message = call_args.kwargs["messages"][0]["content"]

            # Verify bilingual instructions are in the prompt
            assert "BOTH English and Spanish" in user_message
            assert "native Spanish-speaking safety" in user_message

        assert response.status_code == 201
        data = response.json()
        assert data["content_en"]["topic_overview"] == "English overview"
        assert data["content_es"]["topic_overview"] == "Resumen en espanol"


class TestDeleteToolboxTalk:
    """Tests for DELETE /me/projects/{project_id}/toolbox-talks/{talk_id}."""

    def test_delete_toolbox_talk(self, client: TestClient, test_company):
        """Soft-delete a toolbox talk returns 204 and hides it."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/toolbox-talks",
            json={
                "topic": "Hazcom GHS Labels",
                "scheduled_date": "2026-04-15",
                "generate_content": False,
            },
        )
        talk_id = create_resp.json()["id"]

        # Delete
        response = client.delete(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}"
        )
        assert response.status_code == 204

        # Verify gone from list
        list_resp = client.get(f"/me/projects/{project_id}/toolbox-talks")
        assert list_resp.json()["total"] == 0

        # Verify direct get 404s
        get_resp = client.get(
            f"/me/projects/{project_id}/toolbox-talks/{talk_id}"
        )
        assert get_resp.status_code == 404

    def test_delete_toolbox_talk_not_found(self, client: TestClient, test_company):
        """Delete a non-existent toolbox talk returns 404."""
        project_id = _create_project(client)
        response = client.delete(
            f"/me/projects/{project_id}/toolbox-talks/talk_nonexistent123"
        )
        assert response.status_code == 404
