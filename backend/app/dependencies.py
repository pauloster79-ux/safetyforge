"""FastAPI dependency injection providers."""

import logging
from typing import Annotated

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth, credentials
from google.cloud import firestore

from app.config import Settings, get_settings
from app.services.analytics_service import AnalyticsService
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.environmental_service import EnvironmentalService
from app.services.equipment_service import EquipmentService
from app.services.gc_portal_service import GcPortalService
from app.services.generation_service import GenerationService
from app.services.hazard_analysis_service import HazardAnalysisService
from app.services.hazard_report_service import HazardReportService
from app.services.incident_service import IncidentService
from app.services.inspection_service import InspectionService
from app.services.inspection_template_service import InspectionTemplateService
from app.services.invitation_service import InvitationService
from app.services.member_service import MemberService
from app.services.mock_inspection_service import MockInspectionService
from app.services.morning_brief_service import MorningBriefService
from app.services.osha_log_service import OshaLogService
from app.services.prequalification_service import PrequalificationService
from app.services.project_service import ProjectService
from app.services.state_compliance_service import StateComplianceService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)

_firestore_client: firestore.Client | None = None
_firebase_initialized: bool = False


def _init_firebase(settings: Settings) -> None:
    """Initialize Firebase Admin SDK if not already initialized."""
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(
            credentials.ApplicationDefault(),
            {"projectId": settings.google_cloud_project},
        )
    _firebase_initialized = True


def get_firestore_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> firestore.Client:
    """Return a singleton Firestore client instance.

    Args:
        settings: Application settings with project configuration.

    Returns:
        A Firestore client connected to the configured project.
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=settings.google_cloud_project)
    return _firestore_client


async def get_current_user(
    authorization: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Firebase ID token and return user information.

    Extracts the Bearer token from the Authorization header, verifies it
    against Firebase Auth, and returns the decoded user claims.

    Args:
        authorization: The Authorization header value (Bearer <token>).
        settings: Application settings for Firebase initialization.

    Returns:
        A dict containing uid, email, and email_verified from the token.

    Raises:
        HTTPException: 401 if the token is missing, malformed, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[7:]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing from Authorization header",
        )

    _init_firebase(settings)

    try:
        decoded_token = auth.verify_id_token(token)
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
        )
    except Exception as exc:
        logger.error("Unexpected error verifying Firebase token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify authentication token",
        )

    return {
        "uid": decoded_token["uid"],
        "email": decoded_token.get("email", ""),
        "email_verified": decoded_token.get("email_verified", False),
    }


def verify_company_access(
    company_id: str, user_uid: str, db: firestore.Client
) -> None:
    """Verify that a user has access to a company.

    Args:
        company_id: The company ID to check.
        user_uid: The Firebase UID of the current user.
        db: Firestore client.

    Raises:
        HTTPException: 404 if the company doesn't exist, 403 if user lacks access.
    """
    company_ref = db.collection("companies").document(company_id)
    company_doc = company_ref.get()
    if not company_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )
    company_data = company_doc.to_dict()
    if company_data.get("owner_uid") != user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )


# -- Tier 1: Simple services (db only) ------------------------------------------


def get_company_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> CompanyService:
    """Provide a CompanyService instance."""
    return CompanyService(db)


def get_document_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> DocumentService:
    """Provide a DocumentService instance."""
    return DocumentService(db)


def get_project_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> ProjectService:
    """Provide a ProjectService instance."""
    return ProjectService(db)


def get_worker_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> WorkerService:
    """Provide a WorkerService instance."""
    return WorkerService(db)


def get_inspection_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> InspectionService:
    """Provide an InspectionService instance."""
    return InspectionService(db)


def get_toolbox_talk_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> ToolboxTalkService:
    """Provide a ToolboxTalkService instance."""
    return ToolboxTalkService(db)


def get_osha_log_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> OshaLogService:
    """Provide an OshaLogService instance."""
    return OshaLogService(db)


def get_environmental_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> EnvironmentalService:
    """Provide an EnvironmentalService instance."""
    return EnvironmentalService(db)


def get_equipment_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> EquipmentService:
    """Provide an EquipmentService instance."""
    return EquipmentService(db)


def get_member_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> MemberService:
    """Provide a MemberService instance."""
    return MemberService(db)


def get_invitation_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> InvitationService:
    """Provide an InvitationService instance."""
    return InvitationService(db)


# -- Tier 2: Settings-only services ---------------------------------------------


def get_generation_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenerationService:
    """Provide a GenerationService instance."""
    return GenerationService(settings)


def get_hazard_analysis_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HazardAnalysisService:
    """Provide a HazardAnalysisService instance."""
    return HazardAnalysisService(settings)


# -- Tier 3: db + settings services ----------------------------------------------


def get_billing_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BillingService:
    """Provide a BillingService instance."""
    return BillingService(db, settings)


def get_incident_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IncidentService:
    """Provide an IncidentService instance."""
    return IncidentService(db, settings)


# -- Tier 4: Stateless services --------------------------------------------------


def get_inspection_template_service() -> InspectionTemplateService:
    """Provide an InspectionTemplateService instance."""
    return InspectionTemplateService()


# -- Tier 5: Complex services (depend on other services) -------------------------


def get_hazard_report_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    analysis_service: Annotated[HazardAnalysisService, Depends(get_hazard_analysis_service)],
) -> HazardReportService:
    """Provide a HazardReportService instance."""
    return HazardReportService(db, analysis_service)


def get_morning_brief_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> MorningBriefService:
    """Provide a MorningBriefService instance."""
    return MorningBriefService(db, worker_service, inspection_service, toolbox_talk_service)


def get_analytics_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> AnalyticsService:
    """Provide an AnalyticsService instance."""
    return AnalyticsService(
        db, project_service, inspection_service, toolbox_talk_service,
        worker_service, osha_log_service,
    )


def get_mock_inspection_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> MockInspectionService:
    """Provide a MockInspectionService instance."""
    return MockInspectionService(
        db, settings, document_service, worker_service, project_service,
        inspection_service, toolbox_talk_service, osha_log_service,
    )


def get_prequalification_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    mock_inspection_service: Annotated[MockInspectionService, Depends(get_mock_inspection_service)],
) -> PrequalificationService:
    """Provide a PrequalificationService instance."""
    return PrequalificationService(
        db, company_service, document_service, osha_log_service,
        worker_service, mock_inspection_service,
    )


def get_gc_portal_service(
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> GcPortalService:
    """Provide a GcPortalService instance."""
    return GcPortalService(
        db, company_service, document_service, osha_log_service, worker_service,
    )


def get_state_compliance_service(
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> StateComplianceService:
    """Provide a StateComplianceService instance."""
    return StateComplianceService(company_service, document_service, worker_service)
