"""Shared test fixtures for SafetyForge backend tests."""

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore

# Point at the Firestore emulator
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_firestore_client
from app.main import app
from app.models.company import Company
from app.models.project import Project
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService
from app.services.inspection_service import InspectionService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.osha_log_service import OshaLogService
from app.services.worker_service import WorkerService
from app.services.mock_inspection_service import MockInspectionService
from app.services.morning_brief_service import MorningBriefService
from app.services.incident_service import IncidentService
from app.services.analytics_service import AnalyticsService
from app.services.prequalification_service import PrequalificationService
from app.services.gc_portal_service import GcPortalService
from app.services.state_compliance_service import StateComplianceService
from app.services.environmental_service import EnvironmentalService
from app.services.equipment_service import EquipmentService


TEST_USER = {
    "uid": "test_user_001",
    "email": "test@example.com",
    "email_verified": True,
}

TEST_SETTINGS = Settings(
    google_cloud_project="test-project",
    anthropic_api_key="test-key",
    paddle_webhook_secret="test-webhook-secret",
    paddle_api_key="test-paddle-key",
    paddle_environment="sandbox",
    cors_origins="http://localhost:5173",
    environment="test",
)


@pytest.fixture()
def firestore_client() -> firestore.Client:
    """Return a Firestore client connected to the emulator.

    Returns:
        A Firestore client for the test project.
    """
    return firestore.Client(project="test-project")


@pytest.fixture()
def document_service(firestore_client: firestore.Client) -> DocumentService:
    """Return a DocumentService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A DocumentService instance.
    """
    return DocumentService(firestore_client)


@pytest.fixture()
def company_service(firestore_client: firestore.Client) -> CompanyService:
    """Return a CompanyService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A CompanyService instance.
    """
    return CompanyService(firestore_client)


@pytest.fixture()
def billing_service(firestore_client: firestore.Client) -> BillingService:
    """Return a BillingService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A BillingService instance.
    """
    return BillingService(firestore_client, TEST_SETTINGS)


@pytest.fixture()
def test_company(
    firestore_client: firestore.Client,
    company_service: CompanyService,
) -> Company:
    """Create a test company before each test and return it.

    Args:
        firestore_client: Firestore emulator client.
        company_service: CompanyService instance.

    Returns:
        The created Company.
    """
    from app.models.company import CompanyCreate, TradeType

    data = CompanyCreate(
        name="Test Construction Co",
        address="123 Test Street, Testville, TX 75001",
        license_number="TX-12345",
        trade_type=TradeType.GENERAL,
        owner_name="Test Owner",
        phone="555-123-4567",
        email="owner@testconstruction.com",
    )
    return company_service.create(data, TEST_USER["uid"])


@pytest.fixture()
def project_service(firestore_client: firestore.Client) -> ProjectService:
    """Return a ProjectService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A ProjectService instance.
    """
    return ProjectService(firestore_client)


@pytest.fixture()
def inspection_service(firestore_client: firestore.Client) -> InspectionService:
    """Return an InspectionService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        An InspectionService instance.
    """
    return InspectionService(firestore_client)


@pytest.fixture()
def worker_service(firestore_client: firestore.Client) -> WorkerService:
    """Return a WorkerService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A WorkerService instance.
    """
    return WorkerService(firestore_client)


@pytest.fixture()
def osha_log_service(firestore_client: firestore.Client) -> OshaLogService:
    """Return an OshaLogService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        An OshaLogService instance.
    """
    return OshaLogService(firestore_client)


@pytest.fixture()
def toolbox_talk_service(firestore_client: firestore.Client) -> ToolboxTalkService:
    """Return a ToolboxTalkService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A ToolboxTalkService instance.
    """
    return ToolboxTalkService(firestore_client)


@pytest.fixture()
def mock_inspection_service(
    firestore_client: firestore.Client,
    document_service: DocumentService,
    worker_service: WorkerService,
    project_service: ProjectService,
    inspection_service: InspectionService,
    toolbox_talk_service: ToolboxTalkService,
    osha_log_service: OshaLogService,
) -> MockInspectionService:
    """Return a MockInspectionService using the emulator.

    Args:
        firestore_client: Firestore emulator client.
        document_service: DocumentService instance.
        worker_service: WorkerService instance.
        project_service: ProjectService instance.
        inspection_service: InspectionService instance.
        toolbox_talk_service: ToolboxTalkService instance.
        osha_log_service: OshaLogService instance.

    Returns:
        A MockInspectionService instance.
    """
    return MockInspectionService(
        db=firestore_client,
        settings=TEST_SETTINGS,
        document_service=document_service,
        worker_service=worker_service,
        project_service=project_service,
        inspection_service=inspection_service,
        toolbox_talk_service=toolbox_talk_service,
        osha_log_service=osha_log_service,
    )


@pytest.fixture()
def morning_brief_service(
    firestore_client: firestore.Client,
    worker_service: WorkerService,
    inspection_service: InspectionService,
    toolbox_talk_service: ToolboxTalkService,
) -> MorningBriefService:
    """Return a MorningBriefService using the emulator.

    Args:
        firestore_client: Firestore emulator client.
        worker_service: WorkerService instance.
        inspection_service: InspectionService instance.
        toolbox_talk_service: ToolboxTalkService instance.

    Returns:
        A MorningBriefService instance.
    """
    return MorningBriefService(
        db=firestore_client,
        worker_service=worker_service,
        inspection_service=inspection_service,
        toolbox_talk_service=toolbox_talk_service,
    )


@pytest.fixture()
def incident_service(firestore_client: firestore.Client) -> IncidentService:
    """Return an IncidentService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        An IncidentService instance.
    """
    return IncidentService(firestore_client, TEST_SETTINGS)


@pytest.fixture()
def analytics_service(
    firestore_client: firestore.Client,
    project_service: ProjectService,
    inspection_service: InspectionService,
    toolbox_talk_service: ToolboxTalkService,
    worker_service: WorkerService,
    osha_log_service: OshaLogService,
) -> AnalyticsService:
    """Return an AnalyticsService using the emulator.

    Args:
        firestore_client: Firestore emulator client.
        project_service: ProjectService instance.
        inspection_service: InspectionService instance.
        toolbox_talk_service: ToolboxTalkService instance.
        worker_service: WorkerService instance.
        osha_log_service: OshaLogService instance.

    Returns:
        An AnalyticsService instance.
    """
    return AnalyticsService(
        db=firestore_client,
        project_service=project_service,
        inspection_service=inspection_service,
        toolbox_talk_service=toolbox_talk_service,
        worker_service=worker_service,
        osha_log_service=osha_log_service,
    )


@pytest.fixture()
def test_project(
    test_company: Company,
    project_service: ProjectService,
) -> Project:
    """Create a test project before each test and return it.

    Args:
        test_company: The test company fixture.
        project_service: ProjectService instance.

    Returns:
        The created Project.
    """
    from app.models.project import ProjectCreate

    data = ProjectCreate(
        name="Test Construction Site",
        address="456 Build Avenue, Construction City, TX 75002",
    )
    return project_service.create(test_company.id, data, TEST_USER["uid"])


@pytest.fixture(autouse=True)
def cleanup_firestore(firestore_client: firestore.Client):
    """Delete all documents from Firestore after each test.

    Args:
        firestore_client: Firestore emulator client.
    """
    yield

    # Clean up all top-level collections
    for collection_ref in firestore_client.collections():
        _delete_collection(collection_ref)


def _delete_collection(collection_ref: firestore.CollectionReference) -> None:
    """Recursively delete all documents in a collection.

    Args:
        collection_ref: The Firestore collection to delete.
    """
    docs = list(collection_ref.stream())
    for doc in docs:
        # Delete subcollections first
        for subcol in doc.reference.collections():
            _delete_collection(subcol)
        doc.reference.delete()


@pytest.fixture()
def client(firestore_client: firestore.Client) -> TestClient:
    """Return a FastAPI TestClient with auth and Firestore overrides.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        A TestClient configured for testing.
    """

    async def override_get_current_user() -> dict:
        return TEST_USER

    def override_get_firestore_client() -> firestore.Client:
        return firestore_client

    def override_get_settings() -> Settings:
        return TEST_SETTINGS

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_firestore_client] = override_get_firestore_client
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def prequalification_service(
    firestore_client: firestore.Client,
    company_service: CompanyService,
    document_service: DocumentService,
    osha_log_service: OshaLogService,
    worker_service: WorkerService,
    mock_inspection_service: MockInspectionService,
) -> PrequalificationService:
    """Return a PrequalificationService using the emulator.

    Args:
        firestore_client: Firestore emulator client.
        company_service: CompanyService instance.
        document_service: DocumentService instance.
        osha_log_service: OshaLogService instance.
        worker_service: WorkerService instance.
        mock_inspection_service: MockInspectionService instance.

    Returns:
        A PrequalificationService instance.
    """
    return PrequalificationService(
        db=firestore_client,
        company_service=company_service,
        document_service=document_service,
        osha_log_service=osha_log_service,
        worker_service=worker_service,
        mock_inspection_service=mock_inspection_service,
    )


@pytest.fixture()
def gc_portal_service(
    firestore_client: firestore.Client,
    company_service: CompanyService,
    document_service: DocumentService,
    osha_log_service: OshaLogService,
    worker_service: WorkerService,
) -> GcPortalService:
    """Return a GcPortalService using the emulator.

    Args:
        firestore_client: Firestore emulator client.
        company_service: CompanyService instance.
        document_service: DocumentService instance.
        osha_log_service: OshaLogService instance.
        worker_service: WorkerService instance.

    Returns:
        A GcPortalService instance.
    """
    return GcPortalService(
        db=firestore_client,
        company_service=company_service,
        document_service=document_service,
        osha_log_service=osha_log_service,
        worker_service=worker_service,
    )


@pytest.fixture()
def state_compliance_service(
    company_service: CompanyService,
    document_service: DocumentService,
    worker_service: WorkerService,
) -> StateComplianceService:
    """Return a StateComplianceService using the emulator.

    Args:
        company_service: CompanyService instance.
        document_service: DocumentService instance.
        worker_service: WorkerService instance.

    Returns:
        A StateComplianceService instance.
    """
    return StateComplianceService(
        company_service=company_service,
        document_service=document_service,
        worker_service=worker_service,
    )


@pytest.fixture()
def environmental_service(firestore_client: firestore.Client) -> EnvironmentalService:
    """Return an EnvironmentalService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        An EnvironmentalService instance.
    """
    return EnvironmentalService(firestore_client)


@pytest.fixture()
def equipment_service(firestore_client: firestore.Client) -> EquipmentService:
    """Return an EquipmentService using the emulator.

    Args:
        firestore_client: Firestore emulator client.

    Returns:
        An EquipmentService instance.
    """
    return EquipmentService(firestore_client)
