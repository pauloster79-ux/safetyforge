"""Contract tests for /api/v1/me/documents/* endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.company import Company
from app.services.document_service import DocumentService


class TestCreateDocument:
    """Tests for POST /api/v1/me/documents."""

    def test_create_document(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Creating a document returns 201 with the document data."""
        response = client.post(
            "/api/v1/me/documents",
            json={
                "title": "Test SSSP Document",
                "document_type": "sssp",
                "project_info": {
                    "project_name": "Test Project",
                    "site_address": "456 Job Site Rd",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test SSSP Document"
        assert data["document_type"] == "sssp"
        assert data["status"] == "draft"
        assert data["company_id"] == test_company["id"]
        assert data["id"].startswith("doc_")
        assert data["created_by"] == "test_user_001"


class TestListDocuments:
    """Tests for GET /api/v1/me/documents."""

    def test_list_documents_empty(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Listing documents when none exist returns an empty list."""
        response = client.get("/api/v1/me/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_list_documents_with_data(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Listing documents returns all matching documents."""
        # Create two documents
        for i in range(2):
            client.post(
                "/api/v1/me/documents",
                json={
                    "title": f"Doc {i}",
                    "document_type": "jha",
                    "project_info": {"task": f"Task {i}"},
                },
            )

        response = client.get("/api/v1/me/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["documents"]) == 2

    def test_pagination(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Pagination parameters limit and offset work correctly."""
        # Create 5 documents
        for i in range(5):
            client.post(
                "/api/v1/me/documents",
                json={
                    "title": f"Doc {i}",
                    "document_type": "sssp",
                    "project_info": {"name": f"Project {i}"},
                },
            )

        # Get first page of 2
        response = client.get("/api/v1/me/documents?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5

        # Get second page of 2
        response = client.get("/api/v1/me/documents?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5

        # Get last page
        response = client.get("/api/v1/me/documents?limit=2&offset=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["total"] == 5


class TestGetDocument:
    """Tests for GET /api/v1/me/documents/{id}."""

    def test_get_document(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Getting an existing document returns 200 with full data."""
        create_resp = client.post(
            "/api/v1/me/documents",
            json={
                "title": "Get Test Doc",
                "document_type": "sssp",
                "project_info": {"name": "Project"},
            },
        )
        doc_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/me/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["title"] == "Get Test Doc"

    def test_get_document_not_found(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Getting a non-existent document returns 404."""
        response = client.get("/api/v1/me/documents/doc_nonexistent")

        assert response.status_code == 404


class TestUpdateDocument:
    """Tests for PATCH /api/v1/me/documents/{id}."""

    def test_update_document(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Updating a document changes the specified fields."""
        create_resp = client.post(
            "/api/v1/me/documents",
            json={
                "title": "Original Title",
                "document_type": "jha",
                "project_info": {"task": "Original"},
            },
        )
        doc_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/v1/me/documents/{doc_id}",
            json={"title": "Updated Title", "status": "final"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "final"


class TestDeleteDocument:
    """Tests for DELETE /api/v1/me/documents/{id}."""

    def test_delete_document(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Deleting a document returns 204 and hides it from listing."""
        create_resp = client.post(
            "/api/v1/me/documents",
            json={
                "title": "To Delete",
                "document_type": "sssp",
                "project_info": {"name": "Delete Me"},
            },
        )
        doc_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/v1/me/documents/{doc_id}")
        assert delete_resp.status_code == 204

        # Document should now be not found
        get_resp = client.get(f"/api/v1/me/documents/{doc_id}")
        assert get_resp.status_code == 404


class TestDocumentStats:
    """Tests for GET /api/v1/me/documents/stats."""

    def test_document_stats(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Stats endpoint returns correct counts."""
        # Create documents of different types
        for doc_type in ["sssp", "jha", "toolbox_talk"]:
            client.post(
                "/api/v1/me/documents",
                json={
                    "title": f"Test {doc_type}",
                    "document_type": doc_type,
                    "project_info": {"name": "Project"},
                },
            )

        response = client.get("/api/v1/me/documents/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["this_month"] == 3
        assert data["monthly_limit"] is None  # Professional tier (unlimited)
        assert data["by_type"]["sssp"] == 1
        assert data["by_type"]["jha"] == 1
        assert data["by_type"]["toolbox_talk"] == 1
        assert data["by_status"]["draft"] == 3
