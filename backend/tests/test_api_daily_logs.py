"""API contract tests for daily log endpoints."""

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/api/v1/me/projects",
        json={
            "name": "Daily Log Test Project",
            "address": "789 Safety Blvd, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_daily_log(client: TestClient, project_id: str, **overrides) -> dict:
    """Helper to create a daily log and return the response JSON."""
    payload = {
        "log_date": "2026-04-10",
        "superintendent_name": "John Super",
        "workers_on_site": 15,
        "work_performed": "Poured concrete for foundation",
        "notes": "Good progress today",
    }
    payload.update(overrides)
    resp = client.post(
        f"/api/v1/me/projects/{project_id}/daily-logs",
        json=payload,
    )
    assert resp.status_code == 201
    return resp.json()


class TestCreateDailyLog:
    """Tests for POST /me/projects/{project_id}/daily-logs."""

    def test_create_daily_log_draft(self, client: TestClient, test_company):
        """Create a daily log draft with valid data returns 201."""
        project_id = _create_project(client)

        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs",
            json={
                "log_date": "2026-04-10",
                "superintendent_name": "John Super",
                "weather": {
                    "conditions": "Sunny",
                    "temperature_high": "85F",
                    "temperature_low": "65F",
                    "wind": "5 mph SW",
                    "precipitation": "None",
                },
                "workers_on_site": 25,
                "work_performed": "Foundation pouring, east wing",
                "materials_delivered": [
                    {
                        "material": "Ready-mix concrete",
                        "quantity": "40 yards",
                        "supplier": "Texas Concrete Co",
                        "received_by": "Mike R",
                        "notes": "Delivered on time",
                    }
                ],
                "delays": [
                    {
                        "delay_type": "weather",
                        "duration_hours": 1.5,
                        "description": "Morning rain delay",
                        "impact": "Delayed concrete pour start by 1.5 hours",
                    }
                ],
                "visitors": [
                    {
                        "name": "OSHA Inspector",
                        "company": "OSHA",
                        "purpose": "Routine inspection",
                        "time_in": "10:00 AM",
                        "time_out": "11:30 AM",
                    }
                ],
                "safety_incidents": "Near-miss: unsecured tool fell from scaffold",
                "equipment_used": "Crane, concrete pump, vibrators",
                "notes": "Good progress overall.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("dlog_")
        assert data["status"] == "draft"
        assert data["superintendent_name"] == "John Super"
        assert data["workers_on_site"] == 25
        assert data["project_id"] == project_id
        assert data["deleted"] is False
        assert data["weather"]["conditions"] == "Sunny"
        assert len(data["materials_delivered"]) == 1
        assert len(data["delays"]) == 1
        assert len(data["visitors"]) == 1
        assert data["submitted_at"] is None
        assert data["approved_at"] is None

    def test_create_daily_log_minimal(self, client: TestClient, test_company):
        """Create a daily log with only required fields."""
        project_id = _create_project(client)

        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs",
            json={
                "log_date": "2026-04-10",
                "superintendent_name": "Jane S",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["workers_on_site"] == 0
        assert data["materials_delivered"] == []
        assert data["delays"] == []
        assert data["visitors"] == []

    def test_create_daily_log_nonexistent_project(self, client: TestClient, test_company):
        """Create daily log for non-existent project returns 404."""
        response = client.post(
            "/api/v1/me/projects/proj_nonexistent/daily-logs",
            json={
                "log_date": "2026-04-10",
                "superintendent_name": "John S",
            },
        )
        assert response.status_code == 404


class TestListDailyLogs:
    """Tests for GET /me/projects/{project_id}/daily-logs."""

    def test_list_daily_logs(self, client: TestClient, test_company):
        """List daily logs returns created logs."""
        project_id = _create_project(client)

        _create_daily_log(client, project_id, log_date="2026-04-09")
        _create_daily_log(client, project_id, log_date="2026-04-10")

        response = client.get(f"/api/v1/me/projects/{project_id}/daily-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["daily_logs"]) == 2

    def test_list_daily_logs_empty(self, client: TestClient, test_company):
        """List daily logs for project with no logs returns empty."""
        project_id = _create_project(client)
        response = client.get(f"/api/v1/me/projects/{project_id}/daily-logs")
        assert response.status_code == 200
        data = response.json()
        assert data["daily_logs"] == []
        assert data["total"] == 0

    def test_list_daily_logs_filter_by_status(self, client: TestClient, test_company):
        """List daily logs filtered by status returns only matching logs."""
        project_id = _create_project(client)

        log1 = _create_daily_log(client, project_id, log_date="2026-04-09")
        _create_daily_log(client, project_id, log_date="2026-04-10")

        # Submit the first log
        client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log1['id']}/submit"
        )

        # Filter by submitted status
        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs",
            params={"status": "submitted"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["daily_logs"][0]["status"] == "submitted"

    def test_list_daily_logs_filter_by_date_range(self, client: TestClient, test_company):
        """List daily logs filtered by date range."""
        project_id = _create_project(client)

        _create_daily_log(client, project_id, log_date="2026-04-08")
        _create_daily_log(client, project_id, log_date="2026-04-09")
        _create_daily_log(client, project_id, log_date="2026-04-10")

        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs",
            params={"date_from": "2026-04-09", "date_to": "2026-04-09"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestGetDailyLog:
    """Tests for GET /me/projects/{project_id}/daily-logs/{daily_log_id}."""

    def test_get_daily_log(self, client: TestClient, test_company):
        """Get an existing daily log returns 200."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == log["id"]
        assert data["superintendent_name"] == "John Super"

    def test_get_daily_log_not_found(self, client: TestClient, test_company):
        """Get a non-existent daily log returns 404."""
        project_id = _create_project(client)
        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs/dlog_nonexistent123"
        )
        assert response.status_code == 404


class TestUpdateDailyLog:
    """Tests for PATCH /me/projects/{project_id}/daily-logs/{daily_log_id}."""

    def test_update_daily_log(self, client: TestClient, test_company):
        """Update daily log fields returns updated data."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        response = client.patch(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}",
            json={
                "superintendent_name": "Updated Super",
                "workers_on_site": 30,
                "work_performed": "Updated work description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["superintendent_name"] == "Updated Super"
        assert data["workers_on_site"] == 30
        assert data["work_performed"] == "Updated work description"

    def test_update_daily_log_not_found(self, client: TestClient, test_company):
        """Update a non-existent daily log returns 404."""
        project_id = _create_project(client)
        response = client.patch(
            f"/api/v1/me/projects/{project_id}/daily-logs/dlog_nonexistent123",
            json={"workers_on_site": 10},
        )
        assert response.status_code == 404


class TestSubmitDailyLog:
    """Tests for POST /me/projects/{project_id}/daily-logs/{daily_log_id}/submit."""

    def test_submit_daily_log(self, client: TestClient, test_company):
        """Submit a draft daily log transitions to submitted status."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/submit"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None
        assert data["submitted_by"] is not None

    def test_submit_already_submitted_log_returns_404(self, client: TestClient, test_company):
        """Submitting an already submitted log returns 404 (not in draft status)."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        # Submit once
        client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/submit"
        )

        # Try to submit again
        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/submit"
        )
        assert response.status_code == 404

    def test_submit_nonexistent_log(self, client: TestClient, test_company):
        """Submit a non-existent daily log returns 404."""
        project_id = _create_project(client)
        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/dlog_nonexistent/submit"
        )
        assert response.status_code == 404


class TestApproveDailyLog:
    """Tests for POST /me/projects/{project_id}/daily-logs/{daily_log_id}/approve."""

    def test_approve_daily_log(self, client: TestClient, test_company):
        """Approve a submitted daily log transitions to approved status."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        # First submit
        client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/submit"
        )

        # Then approve
        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/approve"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["approved_at"] is not None
        assert data["approved_by"] is not None

    def test_approve_draft_log_returns_404(self, client: TestClient, test_company):
        """Approving a draft log (not submitted) returns 404."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/approve"
        )
        assert response.status_code == 404

    def test_approve_nonexistent_log(self, client: TestClient, test_company):
        """Approve a non-existent daily log returns 404."""
        project_id = _create_project(client)
        response = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/dlog_nonexistent/approve"
        )
        assert response.status_code == 404


class TestDeleteDailyLog:
    """Tests for DELETE /me/projects/{project_id}/daily-logs/{daily_log_id}."""

    def test_delete_daily_log(self, client: TestClient, test_company):
        """Soft-delete a daily log returns 204 and hides it."""
        project_id = _create_project(client)
        log = _create_daily_log(client, project_id)

        # Delete
        response = client.delete(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}"
        )
        assert response.status_code == 204

        # Verify gone from list
        list_resp = client.get(f"/api/v1/me/projects/{project_id}/daily-logs")
        assert list_resp.json()["total"] == 0

        # Verify direct get 404s
        get_resp = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}"
        )
        assert get_resp.status_code == 404

    def test_delete_nonexistent_log(self, client: TestClient, test_company):
        """Delete a non-existent daily log returns 404."""
        project_id = _create_project(client)
        response = client.delete(
            f"/api/v1/me/projects/{project_id}/daily-logs/dlog_nonexistent"
        )
        assert response.status_code == 404


class TestMissingDailyLogs:
    """Tests for GET /me/projects/{project_id}/daily-logs/missing."""

    def test_get_missing_logs(self, client: TestClient, test_company):
        """Get missing logs returns dates without daily logs."""
        project_id = _create_project(client)

        # Create logs for April 9 and 11, skip April 10
        _create_daily_log(client, project_id, log_date="2026-04-09")
        _create_daily_log(client, project_id, log_date="2026-04-11")

        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs/missing",
            params={"date_from": "2026-04-09", "date_to": "2026-04-11"},
        )
        assert response.status_code == 200
        missing = response.json()
        assert "2026-04-10" in missing
        assert "2026-04-09" not in missing
        assert "2026-04-11" not in missing

    def test_get_missing_logs_all_present(self, client: TestClient, test_company):
        """Get missing logs when all dates are covered returns empty list."""
        project_id = _create_project(client)

        _create_daily_log(client, project_id, log_date="2026-04-09")
        _create_daily_log(client, project_id, log_date="2026-04-10")

        response = client.get(
            f"/api/v1/me/projects/{project_id}/daily-logs/missing",
            params={"date_from": "2026-04-09", "date_to": "2026-04-10"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_missing_logs_nonexistent_project(self, client: TestClient, test_company):
        """Get missing logs for non-existent project returns 404."""
        response = client.get(
            "/api/v1/me/projects/proj_nonexistent/daily-logs/missing",
            params={"date_from": "2026-04-09", "date_to": "2026-04-10"},
        )
        assert response.status_code == 404


class TestDailyLogWorkflow:
    """Tests for the full draft -> submitted -> approved workflow."""

    def test_full_workflow(self, client: TestClient, test_company):
        """Test the complete daily log lifecycle."""
        project_id = _create_project(client)

        # Create draft
        log = _create_daily_log(client, project_id)
        assert log["status"] == "draft"

        # Update while in draft
        update_resp = client.patch(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}",
            json={"workers_on_site": 50},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["workers_on_site"] == 50

        # Submit
        submit_resp = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/submit"
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "submitted"

        # Approve
        approve_resp = client.post(
            f"/api/v1/me/projects/{project_id}/daily-logs/{log['id']}/approve"
        )
        assert approve_resp.status_code == 200
        data = approve_resp.json()
        assert data["status"] == "approved"
        assert data["approved_at"] is not None
        assert data["submitted_at"] is not None
