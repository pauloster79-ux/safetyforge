"""API contract tests for project endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestCreateProject:
    """Tests for POST /me/projects."""

    def test_create_project(self, client: TestClient, test_company):
        """Create a project with valid data returns 201."""
        response = client.post(
            "/api/v1/me/projects",
            json={
                "name": "Downtown Office Tower",
                "address": "100 Main Street, Dallas, TX 75201",
                "client_name": "Acme Corp",
                "project_type": "commercial",
                "trade_types": ["general", "electrical"],
                "estimated_workers": 50,
                "description": "20-story office building",
                "special_hazards": "Confined spaces in basement",
                "nearest_hospital": "Dallas General Hospital",
                "emergency_contact_name": "John Safety",
                "emergency_contact_phone": "555-999-0000",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Downtown Office Tower"
        assert data["address"] == "100 Main Street, Dallas, TX 75201"
        assert data["client_name"] == "Acme Corp"
        assert data["project_type"] == "commercial"
        assert data["trade_types"] == ["general", "electrical"]
        assert data["estimated_workers"] == 50
        assert data["status"] == "active"
        assert data["id"].startswith("proj_")
        assert data["company_id"] == test_company["id"]
        assert data["deleted"] is False

    def test_create_project_minimal(self, client: TestClient, test_company):
        """Create a project with only required fields returns 201."""
        response = client.post(
            "/api/v1/me/projects",
            json={
                "name": "Small Reno Job",
                "address": "200 Oak Lane, Austin, TX 78701",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Small Reno Job"
        assert data["client_name"] == ""
        assert data["project_type"] == "commercial"
        assert data["trade_types"] == []
        assert data["estimated_workers"] == 0


class TestListProjects:
    """Tests for GET /me/projects."""

    def test_list_projects_empty(self, client: TestClient, test_company):
        """List projects when none exist returns empty list."""
        response = client.get("/api/v1/me/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["projects"] == []
        assert data["total"] == 0

    def test_list_projects_with_data(self, client: TestClient, test_company):
        """List projects returns created projects."""
        # Create two projects
        client.post(
            "/api/v1/me/projects",
            json={"name": "Project Alpha", "address": "100 Alpha St, TX 75001"},
        )
        client.post(
            "/api/v1/me/projects",
            json={"name": "Project Beta", "address": "200 Beta Ave, TX 75002"},
        )

        response = client.get("/api/v1/me/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["projects"]) == 2

    def test_list_projects_filter_by_status(self, client: TestClient, test_company):
        """List projects with status filter returns only matching projects."""
        # Create a project
        create_resp = client.post(
            "/api/v1/me/projects",
            json={"name": "Active Project", "address": "100 Active St, TX 75001"},
        )
        project_id = create_resp.json()["id"]

        # Create another and set to completed
        create_resp2 = client.post(
            "/api/v1/me/projects",
            json={"name": "Done Project", "address": "200 Done Ave, TX 75002"},
        )
        project_id2 = create_resp2.json()["id"]
        client.patch(
            f"/api/v1/me/projects/{project_id2}",
            json={"status": "completed"},
        )

        # Filter active only
        response = client.get("/api/v1/me/projects?status=active")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["projects"][0]["name"] == "Active Project"

        # Filter completed only
        response = client.get("/api/v1/me/projects?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["projects"][0]["name"] == "Done Project"


class TestGetProject:
    """Tests for GET /me/projects/{project_id}."""

    def test_get_project(self, client: TestClient, test_company):
        """Get an existing project returns 200 with data."""
        create_resp = client.post(
            "/api/v1/me/projects",
            json={
                "name": "My Project",
                "address": "123 Test Rd, TX 75001",
                "client_name": "Test Client",
            },
        )
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/me/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "My Project"
        assert data["client_name"] == "Test Client"
        assert "compliance_score" in data

    def test_get_project_not_found(self, client: TestClient, test_company):
        """Get a non-existent project returns 404."""
        response = client.get("/api/v1/me/projects/proj_nonexistent1234")
        assert response.status_code == 404


class TestUpdateProject:
    """Tests for PATCH /me/projects/{project_id}."""

    def test_update_project(self, client: TestClient, test_company):
        """Update project fields returns updated data."""
        create_resp = client.post(
            "/api/v1/me/projects",
            json={"name": "Original Name", "address": "100 Old St, TX 75001"},
        )
        project_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/v1/me/projects/{project_id}",
            json={
                "name": "Updated Name",
                "client_name": "New Client",
                "status": "on_hold",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["client_name"] == "New Client"
        assert data["status"] == "on_hold"


class TestDeleteProject:
    """Tests for DELETE /me/projects/{project_id}."""

    def test_delete_project(self, client: TestClient, test_company):
        """Soft-delete a project returns 204 and hides it from list."""
        create_resp = client.post(
            "/api/v1/me/projects",
            json={"name": "To Delete", "address": "100 Delete St, TX 75001"},
        )
        project_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/me/projects/{project_id}")
        assert response.status_code == 204

        # Verify it's gone from list
        list_resp = client.get("/api/v1/me/projects")
        assert list_resp.json()["total"] == 0

        # Verify direct get also 404s
        get_resp = client.get(f"/api/v1/me/projects/{project_id}")
        assert get_resp.status_code == 404
