"""FastAPI dependency injection providers."""

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
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
from app.services.audit_service import AuditService
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.context_assembler import ContextAssemblerService
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.document_service import DocumentService
from app.services.environmental_service import EnvironmentalService
from app.services.equipment_service import EquipmentService
from app.services.gc_portal_service import GcPortalService
from app.services.generation_service import GenerationService
from app.services.hazard_analysis_service import HazardAnalysisService
from app.services.hazard_report_service import HazardReportService
from app.services.incident_service import IncidentService
from app.services.daily_log_service import DailyLogService
from app.services.inspection_service import InspectionService
from app.services.inspection_template_service import InspectionTemplateService
from app.services.invitation_service import InvitationService
from app.services.member_service import MemberService
from app.services.mock_inspection_service import MockInspectionService
from app.services.morning_brief_service import MorningBriefService
from app.services.osha_log_service import OshaLogService
from app.services.prequalification_service import PrequalificationService
from app.services.assumption_service import AssumptionService
from app.services.condition_service import ConditionService
from app.services.exclusion_service import ExclusionService
from app.services.industry_baseline_service import IndustryBaselineService
from app.services.insight_service import InsightService
from app.services.material_catalog_service import MaterialCatalogService
from app.services.payment_milestone_service import PaymentMilestoneService
from app.services.warranty_service import WarrantyService
from app.services.item_service import ItemService
from app.services.labour_service import LabourService
from app.services.productivity_rate_service import ProductivityRateService
from app.services.project_assignment_service import ProjectAssignmentService
from app.services.estimating_service import EstimatingService
from app.services.resource_rate_service import ResourceRateService
from app.services.project_service import ProjectService
from app.services.state_compliance_service import StateComplianceService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.voice_service import VoiceService
from app.services.query_canvas_service import QueryCanvasService
from app.services.worker_service import WorkerService
from app.services.work_category_service import WorkCategoryService

logger = logging.getLogger(__name__)


def get_neo4j_driver() -> Driver:
    """Return the Neo4j driver singleton.

    Returns:
        A Neo4j Driver with connection pooling.
    """
    return get_sync_driver()


# ----------------------------------------------------------------------------
# Demo user registry (dev/test only)
#
# Unlocks the 10 golden companies for multi-tenant testing. Each entry maps
# a demo-token suffix to the uid of the company owner seeded by the golden
# fixtures. The uids here MUST match fixtures/golden/companies.py.
#
# Usage from frontend: Authorization: Bearer demo-token-gp03
# Backward-compatible: plain "demo-token" continues to resolve to GP04.
# ----------------------------------------------------------------------------
DEMO_USERS: dict[str, dict[str, str]] = {
    # alias         uid                      email                                      label
    "gp01":       {"uid": "user_gp01_mike",    "email": "mike@mikeshandyman.com",          "name": "Mike Torres (Handyman, FL)"},
    "gp02":       {"uid": "user_gp02_sarah",   "email": "sarah@lakeshorebuilders.ca",      "name": "Sarah Chen (Deck, ON)"},
    "gp03":       {"uid": "user_gp03_james",   "email": "james@brightstone.co.uk",         "name": "James Okafor (Shop fitout, UK)"},
    "gp04":       {"uid": "demo_user_001",     "email": "demo@kerf.build",                 "name": "David Nguyen (Custom home, CA)"},
    "gp05":       {"uid": "user_gp05_emma",    "email": "emma@southerncrossindustrial.com.au", "name": "Emma Walsh (Warehouse, AU)"},
    "gp06":       {"uid": "user_gp06_ryan",    "email": "ryan@fraservalleycontracting.ca", "name": "Ryan Patel (School reno, BC)"},
    "gp07":       {"uid": "user_gp07_anthony", "email": "arusso@manhattanskyline.com",     "name": "Anthony Russo (High-rise, NY)"},
    "gp08":       {"uid": "user_gp08_maria",   "email": "mgonzalez@lonestarinfra.com",     "name": "Maria Gonzalez (Bridge, TX)"},
    "gp09":       {"uid": "user_gp09_fiona",   "email": "fiona@highlanddevelopments.co.uk","name": "Fiona MacLeod (Incident, UK)"},
    "gp10":       {"uid": "user_gp10_ben",     "email": "ben@yarrafitout.com.au",          "name": "Ben Kowalski (Closeout, AU)"},
}


def _resolve_demo_token(token: str) -> dict | None:
    """Map a demo token to a seeded user, or None if not a demo token.

    Accepts:
        demo-token            -> GP04 (David Nguyen) — back-compat default
        demo-token-<suffix>   -> looks up DEMO_USERS[<suffix>]

    Returns:
        User dict with uid/email/email_verified, or None if unrecognised.
    """
    if token == "demo-token":
        u = DEMO_USERS["gp04"]
        return {"uid": u["uid"], "email": u["email"], "email_verified": True}

    if token.startswith("demo-token-"):
        suffix = token[len("demo-token-"):]
        u = DEMO_USERS.get(suffix)
        if u is not None:
            return {"uid": u["uid"], "email": u["email"], "email_verified": True}

    return None


async def get_current_user(
    authorization: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Clerk JWT and return user information.

    Extracts the Bearer token from the Authorization header, verifies it
    against Clerk's JWKS endpoint, and returns the decoded user claims.

    In development/test environments, demo tokens (``demo-token`` and
    ``demo-token-<suffix>``) bypass Clerk and resolve to a seeded golden
    user — see ``DEMO_USERS``.

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

    # Demo mode bypass — maps demo tokens to any of the 10 seeded golden users
    if settings.environment in ("development", "test"):
        demo = _resolve_demo_token(token)
        if demo is not None:
            return demo

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
            OPTIONAL MATCH (a:AgentIdentity {id: $uid})-[:BELONGS_TO]->(c)
            RETURN c.id AS id,
                   c.created_by AS owner_uid,
                   a.id AS agent_id,
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


def get_document_ingestion_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentIngestionService:
    """Provide a DocumentIngestionService instance."""
    return DocumentIngestionService(driver, settings)


def get_project_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    request: Request,
) -> ProjectService:
    """Provide a ProjectService instance.

    Pulls the EventBus off ``app.state`` when available so the service can
    emit ``project.actuals_ready`` on state transitions. Falls back to None
    when agentic infrastructure failed to initialise — the service remains
    fully functional, events are just skipped.
    """
    event_bus = getattr(request.app.state, "event_bus", None)
    return ProjectService(driver, event_bus=event_bus)


def get_audit_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> AuditService:
    """Provide an AuditService instance for activity-stream queries."""
    return AuditService(driver)


def get_worker_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> WorkerService:
    """Provide a WorkerService instance."""
    return WorkerService(driver)


def get_daily_log_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> DailyLogService:
    """Provide a DailyLogService instance."""
    return DailyLogService(driver)


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


def get_labour_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> LabourService:
    """Provide a LabourService instance."""
    return LabourService(driver)


def get_item_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ItemService:
    """Provide an ItemService instance."""
    return ItemService(driver)


def get_work_item_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
):
    """Provide a WorkItemService instance."""
    from app.services.work_item_service import WorkItemService
    return WorkItemService(driver)


def get_assumption_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> AssumptionService:
    """Provide an AssumptionService instance."""
    return AssumptionService(driver)


def get_exclusion_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ExclusionService:
    """Provide an ExclusionService instance."""
    return ExclusionService(driver)


def get_payment_milestone_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> PaymentMilestoneService:
    """Provide a PaymentMilestoneService instance."""
    return PaymentMilestoneService(driver)


def get_condition_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ConditionService:
    """Provide a ConditionService instance."""
    return ConditionService(driver)


def get_warranty_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> WarrantyService:
    """Provide a WarrantyService instance."""
    return WarrantyService(driver)


def get_estimating_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> EstimatingService:
    """Provide an EstimatingService instance."""
    return EstimatingService(driver)


def get_resource_rate_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ResourceRateService:
    """Provide a ResourceRateService instance."""
    return ResourceRateService(driver)


def get_work_category_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> WorkCategoryService:
    """Provide a WorkCategoryService instance."""
    return WorkCategoryService(driver)


def get_productivity_rate_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> ProductivityRateService:
    """Provide a ProductivityRateService instance."""
    return ProductivityRateService(driver)


def get_insight_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> InsightService:
    """Provide an InsightService instance."""
    return InsightService(driver)


def get_material_catalog_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> MaterialCatalogService:
    """Provide a MaterialCatalogService instance."""
    return MaterialCatalogService(driver)


def get_industry_baseline_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> IndustryBaselineService:
    """Provide an IndustryBaselineService instance (read-only lookup)."""
    return IndustryBaselineService(driver)


def get_query_canvas_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> QueryCanvasService:
    """Provide a QueryCanvasService instance."""
    return QueryCanvasService(driver)


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
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> StateComplianceService:
    """Provide a StateComplianceService instance."""
    return StateComplianceService(driver, company_service, document_service, worker_service)


# -- Agentic infrastructure providers ------------------------------------------

from app.services.event_bus import EventBus
from app.services.agent_orchestrator import AgentOrchestrator


def get_event_bus(request: Request) -> EventBus:
    """Provide the EventBus singleton from app state.

    Args:
        request: The FastAPI request (for app.state access).

    Returns:
        The EventBus instance.
    """
    return request.app.state.event_bus


def get_agent_orchestrator(request: Request) -> AgentOrchestrator:
    """Provide the AgentOrchestrator singleton from app state.

    Args:
        request: The FastAPI request (for app.state access).

    Returns:
        The AgentOrchestrator instance.
    """
    return request.app.state.agent_orchestrator
