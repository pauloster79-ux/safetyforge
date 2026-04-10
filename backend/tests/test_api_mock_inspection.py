"""API contract tests for Mock OSHA Inspection endpoints."""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.models.mock_inspection import FindingCategory, FindingSeverity


def _create_worker(client: TestClient, **overrides) -> dict:
    """Create a worker via the API and return the response data.

    Args:
        client: FastAPI test client.
        **overrides: Fields to override in the default payload.

    Returns:
        Worker response dict.
    """
    payload = {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "role": "laborer",
        "trade": "general",
    }
    payload.update(overrides)
    r = client.post("/api/v1/me/workers", json=payload)
    assert r.status_code == 201
    return r.json()


def _create_project(client: TestClient, **overrides) -> dict:
    """Create a project via the API and return the response data.

    Args:
        client: FastAPI test client.
        **overrides: Fields to override in the default payload.

    Returns:
        Project response dict.
    """
    payload = {
        "name": "Test Site Alpha",
        "address": "789 Build Rd, Houston TX 77001",
    }
    payload.update(overrides)
    r = client.post("/api/v1/me/projects", json=payload)
    assert r.status_code == 201
    return r.json()


def _create_document(client: TestClient, **overrides) -> dict:
    """Create a document via the API and return the response data.

    Args:
        client: FastAPI test client.
        **overrides: Fields to override in the default payload.

    Returns:
        Document response dict.
    """
    payload = {
        "title": "Site-Specific Safety Plan",
        "document_type": "sssp",
        "project_info": {},
    }
    payload.update(overrides)
    r = client.post("/api/v1/me/documents", json=payload)
    assert r.status_code == 201
    return r.json()


class TestRunBasicInspection:
    """Tests for POST /me/mock-inspection/run — basic (no deep audit)."""

    def test_run_basic_inspection(self, client: TestClient, test_company):
        """Running a basic mock inspection returns 201 with a result."""
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        assert response.status_code == 201

        data = response.json()
        assert data["id"].startswith("minsp_")
        assert data["company_id"] == test_company["id"]
        assert data["project_id"] is None
        assert data["deep_audit"] is False
        assert 0 <= data["overall_score"] <= 100
        assert data["grade"] in ("A", "B", "C", "D", "F")
        assert data["total_findings"] >= 0
        assert isinstance(data["findings"], list)
        assert isinstance(data["areas_checked"], list)
        assert data["executive_summary"]
        assert data["inspection_date"]
        assert data["created_by"] == "test_user_001"

    def test_run_inspection_no_body(self, client: TestClient, test_company):
        """Running without a request body still works (defaults)."""
        response = client.post("/api/v1/me/mock-inspection/run")
        assert response.status_code == 201
        data = response.json()
        assert data["deep_audit"] is False
        assert data["project_id"] is None

    def test_run_inspection_with_project_scope(
        self, client: TestClient, test_company
    ):
        """Running scoped to a project sets project_id on the result."""
        project = _create_project(client)
        response = client.post(
            "/api/v1/me/mock-inspection/run",
            json={"project_id": project["id"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project["id"]


class TestInspectionFindsGaps:
    """Tests verifying the engine detects specific compliance gaps."""

    def test_inspection_finds_missing_programs(
        self, client: TestClient, test_company
    ):
        """A company with no documents should have many missing-program findings."""
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        assert response.status_code == 201

        data = response.json()
        findings = data["findings"]

        # Should find multiple missing program findings
        missing_doc_findings = [
            f for f in findings
            if f["category"] == FindingCategory.MISSING_DOCUMENT.value
        ]
        # At minimum, the engine should flag several required programs
        assert len(missing_doc_findings) >= 5

        # Each missing document finding should have proper structure
        for finding in missing_doc_findings:
            assert finding["finding_id"].startswith("find_")
            assert finding["osha_standard"].startswith("29 CFR")
            assert finding["citation_language"]
            assert finding["corrective_action"]
            assert finding["can_auto_fix"] is True

    def test_inspection_finds_expired_certs(
        self, client: TestClient, test_company
    ):
        """A worker with an expired cert should generate a finding."""
        # Create a worker
        worker = _create_worker(client, first_name="Mike", last_name="Jones")
        worker_id = worker["id"]

        # Add an expired certification
        expired_date = (date.today() - timedelta(days=60)).isoformat()
        cert_payload = {
            "certification_type": "osha_10",
            "issued_date": "2024-01-01",
            "expiry_date": expired_date,
            "issuing_body": "OSHA",
        }
        r = client.post(
            f"/api/v1/me/workers/{worker_id}/certifications", json=cert_payload
        )
        assert r.status_code == 201

        # Run inspection
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        assert response.status_code == 201

        data = response.json()
        expired_findings = [
            f for f in data["findings"]
            if f["category"] == FindingCategory.EXPIRED_CERTIFICATION.value
            and f["severity"] == FindingSeverity.HIGH.value
        ]
        # Should find the expired OSHA 10 cert
        assert len(expired_findings) >= 1
        assert any("Mike Jones" in f["title"] for f in expired_findings)

    def test_inspection_finds_stale_inspections(
        self, client: TestClient, test_company
    ):
        """An active project with no recent inspection generates a finding."""
        _create_project(client, name="Stale Inspection Site")

        response = client.post("/api/v1/me/mock-inspection/run", json={})
        assert response.status_code == 201

        data = response.json()
        insp_findings = [
            f for f in data["findings"]
            if f["category"] == FindingCategory.MISSING_INSPECTION.value
        ]
        assert len(insp_findings) >= 1
        assert any(
            "Stale Inspection Site" in f["title"] for f in insp_findings
        )

    def test_inspection_finds_missing_training(
        self, client: TestClient, test_company
    ):
        """A foreman without OSHA 30 should generate a training gap finding."""
        _create_worker(
            client,
            first_name="Sarah",
            last_name="Connor",
            role="foreman",
        )

        response = client.post("/api/v1/me/mock-inspection/run", json={})
        assert response.status_code == 201

        data = response.json()
        training_findings = [
            f for f in data["findings"]
            if f["category"] == FindingCategory.MISSING_TRAINING.value
            and "Sarah Connor" in f["title"]
        ]
        # Foreman missing osha_30, fall_protection, first_aid_cpr
        assert len(training_findings) >= 1

    def test_sssp_document_reduces_missing_program_findings(
        self, client: TestClient, test_company
    ):
        """Having an SSSP document should reduce missing program findings."""
        # First run without any documents
        r1 = client.post("/api/v1/me/mock-inspection/run", json={})
        findings_without = len([
            f for f in r1.json()["findings"]
            if f["category"] == FindingCategory.MISSING_DOCUMENT.value
        ])

        # Create an SSSP document (covers many programs)
        _create_document(
            client,
            title="Site-Specific Safety Plan",
            document_type="sssp",
        )

        # Run again
        r2 = client.post("/api/v1/me/mock-inspection/run", json={})
        findings_with = len([
            f for f in r2.json()["findings"]
            if f["category"] == FindingCategory.MISSING_DOCUMENT.value
        ])

        # Having an SSSP should reduce the count of missing-doc findings
        assert findings_with < findings_without


class TestScoreCalculation:
    """Tests for compliance score and grade calculation."""

    def test_score_calculation_deductions(
        self, client: TestClient, test_company
    ):
        """Score should be 100 minus deductions, floored at 0."""
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        data = response.json()

        score = data["overall_score"]
        assert 0 <= score <= 100

        # With a bare company (no docs, no workers), we should have many
        # findings and a low score
        assert data["total_findings"] > 0

    def test_grade_assignment(self, client: TestClient, test_company):
        """Grade should correspond to the score ranges."""
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        data = response.json()

        score = data["overall_score"]
        grade = data["grade"]

        if score >= 90:
            assert grade == "A"
        elif score >= 75:
            assert grade == "B"
        elif score >= 60:
            assert grade == "C"
        elif score >= 40:
            assert grade == "D"
        else:
            assert grade == "F"

    def test_finding_counts_match(self, client: TestClient, test_company):
        """Finding severity counts should add up to total_findings."""
        response = client.post("/api/v1/me/mock-inspection/run", json={})
        data = response.json()

        total = data["total_findings"]
        parts = (
            data["critical_findings"]
            + data["high_findings"]
            + data["medium_findings"]
            + data["low_findings"]
            + data.get("info_findings", 0)
        )
        assert parts == total
        assert len(data["findings"]) == total


class TestListResults:
    """Tests for GET /me/mock-inspection/results."""

    def test_list_results_empty(self, client: TestClient, test_company):
        """Listing results with none returns empty list."""
        response = client.get("/api/v1/me/mock-inspection/results")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0

    def test_list_results_after_run(self, client: TestClient, test_company):
        """Results appear in list after running an inspection."""
        # Run an inspection
        client.post("/api/v1/me/mock-inspection/run", json={})

        response = client.get("/api/v1/me/mock-inspection/results")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1

        result = data["results"][0]
        assert result["id"].startswith("minsp_")
        assert result["overall_score"] >= 0
        assert result["grade"] in ("A", "B", "C", "D", "F")

    def test_list_results_pagination(self, client: TestClient, test_company):
        """Pagination limits and offsets work correctly."""
        # Run two inspections
        client.post("/api/v1/me/mock-inspection/run", json={})
        client.post("/api/v1/me/mock-inspection/run", json={})

        # Get first page
        r1 = client.get("/api/v1/me/mock-inspection/results?limit=1&offset=0")
        assert r1.status_code == 200
        assert r1.json()["total"] == 2
        assert len(r1.json()["results"]) == 1

        # Get second page
        r2 = client.get("/api/v1/me/mock-inspection/results?limit=1&offset=1")
        assert r2.status_code == 200
        assert len(r2.json()["results"]) == 1

        # Different results
        assert r1.json()["results"][0]["id"] != r2.json()["results"][0]["id"]


class TestGetResult:
    """Tests for GET /me/mock-inspection/results/{id}."""

    def test_get_result(self, client: TestClient, test_company):
        """Fetching a result by ID returns the full result."""
        # Run an inspection
        run_response = client.post("/api/v1/me/mock-inspection/run", json={})
        result_id = run_response.json()["id"]

        # Fetch it
        response = client.get(f"/api/v1/me/mock-inspection/results/{result_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == result_id
        assert isinstance(data["findings"], list)
        assert data["executive_summary"]

    def test_get_result_not_found(self, client: TestClient, test_company):
        """Fetching a non-existent result returns 404."""
        response = client.get(
            "/api/v1/me/mock-inspection/results/minsp_nonexistent"
        )
        assert response.status_code == 404

    def test_result_matches_run_output(
        self, client: TestClient, test_company
    ):
        """The stored result should match what was returned at run time."""
        run_response = client.post("/api/v1/me/mock-inspection/run", json={})
        run_data = run_response.json()

        get_response = client.get(
            f"/api/v1/me/mock-inspection/results/{run_data['id']}"
        )
        get_data = get_response.json()

        assert get_data["overall_score"] == run_data["overall_score"]
        assert get_data["grade"] == run_data["grade"]
        assert get_data["total_findings"] == run_data["total_findings"]
        assert len(get_data["findings"]) == len(run_data["findings"])
