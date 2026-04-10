"""FastAPI dependency injection providers."""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from neo4j import Driver

from app.config import Settings, get_settings
from app.services.auth_service import (
    ClerkAuthError,
    ClerkTokenExpiredError,
    verify_clerk_token,
)
from app.services.neo4j_client import get_sync_driver
from app.services.agent_identity_service import AgentIdentityService
from app.services.analytics_service import AnalyticsService
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.context_assembler import ContextAssemblerService
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
from app.services.project_assignment_service import ProjectAssignmentService
from app.services.project_service import ProjectService
from app.services.state_compliance_service import StateComplianceService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.voice_service import VoiceService
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)


def get_neo4j_driver() -> Driver:
    """Return the Neo4j driver singleton.

    Returns:
        A Neo4j Driver with connection pooling.
    """
    return get_sync_driver()


async def get_current_user(
    authorization: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Clerk JWT and return user information.

    Extracts the Bearer token from the Authorization header, verifies it
    against Clerk's JWKS endpoint, and returns the decoded user claims.

    Args:
        authorization: The Authorization header value (Bearer <token>).
        settings: Application settings for Clerk configuration.

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

    try:
        return verify_clerk_token(token, settings)
    except ClerkTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except ClerkAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def verify_company_access(
    company_id: str, user_uid: str, driver: Driver
) -> None:
    """Verify that a user or agent has access to a company.

    Checks both human membership (created_by match) and agent identity
    (BELONGS_TO relationship). Permission = traversability.

    Args:
        company_id: The company ID to check.
        user_uid: The Clerk user ID or agent_id of the caller.
        driver: Neo4j driver.

    Raises:
        HTTPException: 404 if the company doesn't exist, 403 if caller lacks access.
    """
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Company {id: $company_id})
            OPTIONAL MATCH (a:AgentIdentity {agent_id: $uid})-[:BELONGS_TO]->(c)
            RETURN c.id AS id,
                   c.created_by AS owner_uid,
                   a.agent_id AS agent_id,
                   a.status AS agent_status
            """,
            company_id=company_id,
            uid=user_uid,
        )
        record = result.single()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )

    # Agent access: BELONGS_TO relationship exists and agent is active
    if record["agent_id"] is not None:
        if record["agent_status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent is suspended or revoked",
            )
        return

    # Human access: must be company owner
    if record["owner_uid"] != user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )


# -- Agent services ---------------------------------------------------------------


def get_agent_identity_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> AgentIdentityService:
    """Provide an AgentIdentityService instance."""
    return AgentIdentityService(driver)


# -- Tier 1: Simple services (Neo4j driver only) ----------------------------------


def get_company_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> CompanyService:
    """Provide a CompanyService instance."""
    return CompanyService(driver)


def get_context_assembler(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ContextAssemblerService:
    """Provide a ContextAssemblerService instance."""
    return ContextAssemblerService(driver)


def get_document_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> DocumentService:
    """Provide a DocumentService instance."""
    return DocumentService(driver)


def get_project_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ProjectService:
    """Provide a ProjectService instance."""
    return ProjectService(driver)


def get_worker_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> WorkerService:
    """Provide a WorkerService instance."""
    return WorkerService(driver)


def get_inspection_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> InspectionService:
    """Provide an InspectionService instance."""
    return InspectionService(driver)


def get_toolbox_talk_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ToolboxTalkService:
    """Provide a ToolboxTalkService instance."""
    return ToolboxTalkService(driver)


def get_osha_log_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> OshaLogService:
    """Provide an OshaLogService instance."""
    return OshaLogService(driver)


def get_environmental_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> EnvironmentalService:
    """Provide an EnvironmentalService instance."""
    return EnvironmentalService(driver)


def get_equipment_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> EquipmentService:
    """Provide an EquipmentService instance."""
    return EquipmentService(driver)


def get_project_assignment_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ProjectAssignmentService:
    """Provide a ProjectAssignmentService instance."""
    return ProjectAssignmentService(driver)


def get_member_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> MemberService:
    """Provide a MemberService instance."""
    return MemberService(driver)


def get_invitation_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> InvitationService:
    """Provide an InvitationService instance."""
    return InvitationService(driver)


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


def get_voice_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VoiceService:
    """Provide a VoiceService instance."""
    return VoiceService(settings)


# -- Tier 3: driver + settings services ------------------------------------------


def get_billing_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BillingService:
    """Provide a BillingService instance."""
    return BillingService(driver, settings)


def get_incident_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IncidentService:
    """Provide an IncidentService instance."""
    return IncidentService(driver, settings)


# -- Tier 4: Stateless services --------------------------------------------------


def get_inspection_template_service() -> InspectionTemplateService:
    """Provide an InspectionTemplateService instance."""
    return InspectionTemplateService()


# -- Tier 5: Complex services (depend on other services) -------------------------


def get_hazard_report_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    analysis_service: Annotated[HazardAnalysisService, Depends(get_hazard_analysis_service)],
) -> HazardReportService:
    """Provide a HazardReportService instance."""
    return HazardReportService(driver, analysis_service)


def get_morning_brief_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> MorningBriefService:
    """Provide a MorningBriefService instance."""
    return MorningBriefService(driver, worker_service, inspection_service, toolbox_talk_service)


def get_analytics_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> AnalyticsService:
    """Provide an AnalyticsService instance."""
    return AnalyticsService(
        driver, project_service, inspection_service, toolbox_talk_service,
        worker_service, osha_log_service,
    )


def get_mock_inspection_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
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
        driver, settings, document_service, worker_service, project_service,
        inspection_service, toolbox_talk_service, osha_log_service,
    )


def get_prequalification_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    mock_inspection_service: Annotated[MockInspectionService, Depends(get_mock_inspection_service)],
) -> PrequalificationService:
    """Provide a PrequalificationService instance."""
    return PrequalificationService(
        driver, company_service, document_service, osha_log_service,
        worker_service, mock_inspection_service,
    )


def get_gc_portal_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> GcPortalService:
    """Provide a GcPortalService instance."""
    return GcPortalService(
        driver, company_service, document_service, osha_log_service, worker_service,
    )


def get_state_compliance_service(
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> StateComplianceService:
    """Provide a StateComplianceService instance."""
    return StateComplianceService(company_service, document_service, worker_service)
