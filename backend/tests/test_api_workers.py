"""API contract tests for worker and certification endpoints."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


class TestCreateWorker:
    """Tests for POST /me/workers."""

    def test_create_worker(self, client: TestClient, test_company):
        """Create a worker with valid data returns 201."""
        response = client.post(
            "/me/workers",
            json={
                "first_name": "Carlos",
                "last_name": "Martinez",
                "email": "carlos@example.com",
                "phone": "555-111-2222",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "es",
                "emergency_contact_name": "Maria Martinez",
                "emergency_contact_phone": "555-333-4444",
                "notes": "Bilingual worker, 10 years experience",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Carlos"
        assert data["last_name"] == "Martinez"
        assert data["email"] == "carlos@example.com"
        assert data["phone"] == "555-111-2222"
        assert data["role"] == "foreman"
        assert data["trade"] == "electrical"
        assert data["language_preference"] == "es"
        assert data["emergency_contact_name"] == "Maria Martinez"
        assert data["status"] == "active"
        assert data["id"].startswith("wkr_")
        assert data["company_id"] == test_company.id
        assert data["certifications"] == []
        assert data["total_certifications"] == 0
        assert data["expiring_soon"] == 0
        assert data["expired"] == 0
        assert data["deleted"] is False


class TestListWorkers:
    """Tests for GET /me/workers."""

    def test_list_workers(self, client: TestClient, test_company):
        """List workers returns created workers."""
        # Create two workers
        client.post(
            "/me/workers",
            json={"first_name": "John", "last_name": "Doe"},
        )
        client.post(
            "/me/workers",
            json={"first_name": "Jane", "last_name": "Smith"},
        )

        response = client.get("/me/workers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["workers"]) == 2

    def test_list_workers_search_by_name(self, client: TestClient, test_company):
        """Search workers by name filters results correctly."""
        client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        client.post(
            "/me/workers",
            json={"first_name": "John", "last_name": "Doe"},
        )
        client.post(
            "/me/workers",
            json={"first_name": "Maria", "last_name": "Garcia"},
        )

        # Search by first name
        response = client.get("/me/workers?search=Carlos")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["workers"][0]["first_name"] == "Carlos"

        # Search by last name (case insensitive)
        response = client.get("/me/workers?search=garcia")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["workers"][0]["last_name"] == "Garcia"


class TestGetWorker:
    """Tests for GET /me/workers/{worker_id}."""

    def test_get_worker(self, client: TestClient, test_company):
        """Get a worker by ID returns the worker."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        response = client.get(f"/me/workers/{worker_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == worker_id
        assert data["first_name"] == "Carlos"
        assert data["last_name"] == "Martinez"


class TestUpdateWorker:
    """Tests for PATCH /me/workers/{worker_id}."""

    def test_update_worker(self, client: TestClient, test_company):
        """Update a worker's fields returns the updated worker."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez", "role": "laborer"},
        )
        worker_id = create_resp.json()["id"]

        response = client.patch(
            f"/me/workers/{worker_id}",
            json={"role": "foreman", "trade": "electrical"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "foreman"
        assert data["trade"] == "electrical"
        assert data["first_name"] == "Carlos"  # unchanged


class TestDeleteWorker:
    """Tests for DELETE /me/workers/{worker_id}."""

    def test_delete_worker(self, client: TestClient, test_company):
        """Soft-delete a worker sets status to terminated."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        response = client.delete(f"/me/workers/{worker_id}")
        assert response.status_code == 204

        # Worker should no longer be accessible
        get_resp = client.get(f"/me/workers/{worker_id}")
        assert get_resp.status_code == 404


class TestAddCertification:
    """Tests for POST /me/workers/{worker_id}/certifications."""

    def test_add_certification(self, client: TestClient, test_company):
        """Add a certification without expiry returns worker with cert."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        response = client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "osha_10",
                "issued_date": "2024-01-15",
                "issuing_body": "OSHA Training Institute",
                "certificate_number": "OSH-2024-12345",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_certifications"] == 1
        cert = data["certifications"][0]
        assert cert["certification_type"] == "osha_10"
        assert cert["issued_date"] == "2024-01-15"
        assert cert["expiry_date"] is None
        assert cert["status"] == "valid"
        assert cert["id"].startswith("cert_")

    def test_add_certification_with_expiry(self, client: TestClient, test_company):
        """Add a certification with a future expiry date."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "John", "last_name": "Doe"},
        )
        worker_id = create_resp.json()["id"]

        future_date = (date.today() + timedelta(days=365)).isoformat()
        response = client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "fall_protection",
                "issued_date": "2024-06-01",
                "expiry_date": future_date,
                "issuing_body": "Safety Training Corp",
            },
        )
        assert response.status_code == 201
        data = response.json()
        cert = data["certifications"][0]
        assert cert["certification_type"] == "fall_protection"
        assert cert["expiry_date"] == future_date
        assert cert["status"] == "valid"


class TestCertificationStatus:
    """Tests for certification status computation."""

    def test_certification_status_valid(self, client: TestClient, test_company):
        """Certification with no expiry or far future expiry is valid."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        # No expiry = valid forever
        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "osha_10",
                "issued_date": "2024-01-15",
            },
        )

        response = client.get(f"/me/workers/{worker_id}")
        data = response.json()
        assert data["certifications"][0]["status"] == "valid"
        assert data["expired"] == 0
        assert data["expiring_soon"] == 0

    def test_certification_status_expired(self, client: TestClient, test_company):
        """Certification with past expiry date is expired."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        past_date = (date.today() - timedelta(days=10)).isoformat()
        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "first_aid_cpr",
                "issued_date": "2022-01-01",
                "expiry_date": past_date,
            },
        )

        response = client.get(f"/me/workers/{worker_id}")
        data = response.json()
        assert data["certifications"][0]["status"] == "expired"
        assert data["expired"] == 1
        assert data["expiring_soon"] == 0

    def test_certification_status_expiring_soon(self, client: TestClient, test_company):
        """Certification expiring within 30 days is expiring_soon."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        soon_date = (date.today() + timedelta(days=15)).isoformat()
        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "forklift_operator",
                "issued_date": "2023-06-01",
                "expiry_date": soon_date,
            },
        )

        response = client.get(f"/me/workers/{worker_id}")
        data = response.json()
        assert data["certifications"][0]["status"] == "expiring_soon"
        assert data["expiring_soon"] == 1
        assert data["expired"] == 0


class TestRemoveCertification:
    """Tests for DELETE /me/workers/{worker_id}/certifications/{cert_id}."""

    def test_remove_certification(self, client: TestClient, test_company):
        """Remove a certification from a worker."""
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        # Add two certifications
        add_resp1 = client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "osha_10",
                "issued_date": "2024-01-15",
            },
        )
        cert_id = add_resp1.json()["certifications"][0]["id"]

        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "fall_protection",
                "issued_date": "2024-03-01",
            },
        )

        # Remove the first certification
        response = client.delete(
            f"/me/workers/{worker_id}/certifications/{cert_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_certifications"] == 1
        assert data["certifications"][0]["certification_type"] == "fall_protection"


class TestExpiringCertifications:
    """Tests for GET /me/workers/expiring-certifications."""

    def test_expiring_certifications_endpoint(self, client: TestClient, test_company):
        """Get expiring certifications returns certs expiring within N days."""
        # Create worker with an expiring cert
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        soon_date = (date.today() + timedelta(days=10)).isoformat()
        far_date = (date.today() + timedelta(days=365)).isoformat()

        # Add one expiring soon cert
        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "first_aid_cpr",
                "issued_date": "2023-01-01",
                "expiry_date": soon_date,
            },
        )
        # Add one valid cert (far future)
        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "osha_30",
                "issued_date": "2024-01-01",
                "expiry_date": far_date,
            },
        )

        response = client.get("/me/workers/expiring-certifications?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["certifications"][0]["worker_id"] == worker_id
        assert data["certifications"][0]["certification"]["certification_type"] == "first_aid_cpr"


class TestCertificationMatrix:
    """Tests for GET /me/workers/certification-matrix."""

    def test_certification_matrix(self, client: TestClient, test_company):
        """Get certification matrix returns workers x cert types grid."""
        # Create a worker with one cert
        create_resp = client.post(
            "/me/workers",
            json={"first_name": "Carlos", "last_name": "Martinez"},
        )
        worker_id = create_resp.json()["id"]

        client.post(
            f"/me/workers/{worker_id}/certifications",
            json={
                "certification_type": "osha_10",
                "issued_date": "2024-01-15",
            },
        )

        response = client.get("/me/workers/certification-matrix")
        assert response.status_code == 200
        data = response.json()

        assert len(data["workers"]) == 1
        assert data["workers"][0]["id"] == worker_id
        assert len(data["certification_types"]) > 0
        assert "osha_10" in data["certification_types"]

        # Find the osha_10 entry for this worker
        osha_entry = [
            e for e in data["matrix"]
            if e["worker_id"] == worker_id and e["certification_type"] == "osha_10"
        ]
        assert len(osha_entry) == 1
        assert osha_entry[0]["status"] == "valid"

        # Find a missing cert entry
        fall_entry = [
            e for e in data["matrix"]
            if e["worker_id"] == worker_id and e["certification_type"] == "fall_protection"
        ]
        assert len(fall_entry) == 1
        assert fall_entry[0]["status"] == "missing"
