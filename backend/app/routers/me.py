"""Convenience /me router that resolves the current user's company automatically."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.middleware.feature_gate import require_feature
from app.middleware.rate_limit import limiter
from app.utils.async_helpers import run_sync

from app.dependencies import (
    get_analytics_service,
    get_billing_service,
    get_company_service,
    get_current_user,
    get_document_service,
    get_environmental_service,
    get_equipment_service,
    get_generation_service,
    get_hazard_analysis_service,
    get_hazard_report_service,
    get_incident_service,
    get_inspection_service,
    get_inspection_template_service,
    get_mock_inspection_service,
    get_morning_brief_service,
    get_osha_log_service,
    get_prequalification_service,
    get_project_assignment_service,
    get_project_service,
    get_state_compliance_service,
    get_toolbox_talk_service,
    get_worker_service,
)
from app.exceptions import (
    AssignmentNotFoundError,
    CompanyNotFoundError,
    DocumentLimitExceededError,
    DocumentNotFoundError,
    EnvironmentalProgramNotFoundError,
    EquipmentNotFoundError,
    GenerationError,
    HazardReportNotFoundError,
    IncidentNotFoundError,
    InspectionNotFoundError,
    MockInspectionNotFoundError,
    MorningBriefNotFoundError,
    OshaLogEntryNotFoundError,
    PrequalPackageNotFoundError,
    ProjectNotFoundError,
    ToolboxTalkNotFoundError,
    WorkerNotFoundError,
)
from app.models.billing import SubscriptionInfo
from app.models.company import Company, CompanyUpdate
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentGenerateRequest,
    DocumentListResponse,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
)
from app.models.inspection import (
    Inspection,
    InspectionCreate,
    InspectionItem,
    InspectionListResponse,
    InspectionType,
    InspectionUpdate,
)
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectListResponse,
    ProjectStatus,
    ProjectUpdate,
)
from app.models.worker import (
    CertificationCreate,
    CertificationMatrixResponse,
    CertificationUpdate,
    ExpiringCertificationsResponse,
    Worker,
    WorkerCreate,
    WorkerListResponse,
    WorkerStatus,
    WorkerUpdate,
)
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.generation_service import GenerationService
from app.services.inspection_service import InspectionService
from app.services.inspection_template_service import InspectionTemplateService
from app.services.pdf_service import PdfService
from app.models.toolbox_talk import (
    AttendeeCreate,
    CompleteTalkRequest,
    GenerateContentRequest,
    ToolboxTalk,
    ToolboxTalkCreate,
    ToolboxTalkListResponse,
    ToolboxTalkStatus,
    ToolboxTalkUpdate,
)
from app.models.osha_log import (
    CertifySummaryRequest,
    Osha300Summary,
    OshaLogEntry,
    OshaLogEntryCreate,
    OshaLogEntryListResponse,
    OshaLogEntryUpdate,
    OshaLogYearsResponse,
)
from app.services.mock_inspection_service import MockInspectionService
from app.services.osha_log_service import OshaLogService
from app.services.project_service import ProjectService
from app.services.toolbox_talk_service import ToolboxTalkService
from app.services.worker_service import WorkerService
from app.models.mock_inspection import (
    MockInspectionListResponse,
    MockInspectionResult,
    RunInspectionRequest,
)
from app.services.hazard_analysis_service import HazardAnalysisService
from app.services.hazard_report_service import HazardReportService
from app.services.morning_brief_service import MorningBriefService
from app.services.incident_service import IncidentService
from app.services.analytics_service import AnalyticsService
from app.models.morning_brief import (
    MorningBrief,
    MorningBriefListResponse,
)
from app.models.incident import (
    Incident,
    IncidentCreate,
    IncidentListResponse,
    IncidentUpdate,
)
from app.models.analytics import (
    EmrEstimate,
    EmrEstimateRequest,
    SafetyDashboardMetrics,
)
from app.models.hazard_report import (
    HazardReport,
    HazardReportCreate,
    HazardReportListResponse,
    HazardReportStatusUpdate,
    HazardSeverity,
    HazardStatus,
    QuickAnalysisRequest,
)
from app.models.environmental import (
    ComplianceStatusResponse,
    EnvironmentalProgram,
    EnvironmentalProgramCreate,
    EnvironmentalProgramListResponse,
    EnvironmentalProgramType,
    EnvironmentalProgramUpdate,
    ExposureMonitoringRecord,
    ExposureMonitoringRecordCreate,
    ExposureMonitoringRecordListResponse,
    ExposureSummaryResponse,
    SwpppInspection,
    SwpppInspectionCreate,
    SwpppInspectionListResponse,
)
from app.models.equipment import (
    DotComplianceResponse,
    Equipment,
    EquipmentCreate,
    EquipmentInspectionLog,
    EquipmentInspectionLogCreate,
    EquipmentInspectionLogListResponse,
    EquipmentListResponse,
    EquipmentStatus,
    EquipmentSummaryResponse,
    EquipmentType,
    EquipmentUpdate,
    OverdueEquipmentResponse,
)
from app.services.environmental_service import EnvironmentalService
from app.services.equipment_service import EquipmentService
from app.models.project_assignment import (
    ProjectAssignment,
    ProjectAssignmentCreate,
    ProjectAssignmentListResponse,
    ProjectAssignmentUpdate,
    AssignmentStatus,
    ResourceType,
)
from app.services.project_assignment_service import ProjectAssignmentService

router = APIRouter(prefix="/me", tags=["me"])


async def _resolve_company(
    user: dict, company_service: CompanyService
) -> Company:
    """Resolve the current user's company or raise 404.

    Args:
        user: The current user claims dict.
        company_service: CompanyService instance.

    Returns:
        The user's Company.

    Raises:
        HTTPException: 404 if no company found.
    """
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


# -- Company endpoints ---------------------------------------------------------------


@router.get("/company", response_model=Company)
async def get_my_company(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
) -> Company:
    """Get the current user's company profile.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.

    Returns:
        The user's Company.
    """
    return await _resolve_company(current_user, company_service)


@router.patch("/company", response_model=Company)
async def update_my_company(
    data: CompanyUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
) -> Company:
    """Update the current user's company profile.

    Args:
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.

    Returns:
        The updated Company.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return await run_sync(company_service.update, company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


# -- Document endpoints --------------------------------------------------------------


@router.get("/documents", response_model=DocumentListResponse)
async def list_my_documents(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
    limit: int = Query(20, ge=1, le=100, description="Max documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    document_type: DocumentType | None = Query(None, alias="type", description="Filter by type"),
    document_status: DocumentStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    sort: str = Query("created_at:desc", description="Sort field:direction"),
) -> DocumentListResponse:
    """List documents for the current user's company with pagination.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
        limit: Page size.
        offset: Skip count.
        document_type: Optional type filter.
        document_status: Optional status filter.
        sort: Sort specification as field:direction.

    Returns:
        A DocumentListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)

    sort_parts = sort.split(":")
    sort_field = sort_parts[0] if sort_parts else "created_at"
    sort_direction = sort_parts[1] if len(sort_parts) > 1 else "desc"

    result = await run_sync(
        doc_service.list_documents,
        company_id=company.id,
        document_type=document_type,
        status=document_status,
        limit=limit,
        offset=offset,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )

    return DocumentListResponse(documents=result["documents"], total=result["total"])


@router.post("/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_my_document(
    data: DocumentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> Document:
    """Create a new document for the current user's company.

    Args:
        data: Document creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
        billing_service: BillingService dependency.

    Returns:
        The created Document.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        await run_sync(billing_service.check_document_limit, company.id)
    except DocumentLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly document limit reached. Upgrade your plan for more documents.",
        )

    try:
        return await run_sync(doc_service.create, company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/documents/stats")
async def get_my_document_stats(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> dict:
    """Get document statistics for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
        billing_service: BillingService dependency.

    Returns:
        A dict with total, this_month, monthly_limit, by_type, by_status.
    """
    company = await _resolve_company(current_user, company_service)
    stats = await run_sync(doc_service.get_stats, company.id)
    sub_info = await run_sync(billing_service.get_subscription_status, company.id)

    return {
        "total": stats["total"],
        "this_month": stats["this_month"],
        "monthly_limit": sub_info.documents_limit,
        "by_type": stats["by_type"],
        "by_status": stats["by_status"],
    }


@router.get("/documents/{document_id}", response_model=Document)
async def get_my_document(
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
) -> Document:
    """Get a specific document by ID.

    Args:
        document_id: The document ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.

    Returns:
        The Document.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return await run_sync(doc_service.get, company.id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.patch("/documents/{document_id}", response_model=Document)
async def update_my_document(
    document_id: str,
    data: DocumentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
) -> Document:
    """Update a document.

    Args:
        document_id: The document ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.

    Returns:
        The updated Document.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return await run_sync(doc_service.update, company.id, document_id, data, current_user["uid"])
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_document(
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
) -> None:
    """Soft-delete a document.

    Args:
        document_id: The document ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        await run_sync(doc_service.delete, company.id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.post("/documents/{document_id}/generate", response_model=Document)
@limiter.limit("5/minute")
async def generate_my_document_content(
    request: Request,
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
    gen_service: Annotated[GenerationService, Depends(get_generation_service)],
) -> Document:
    """Generate AI content for an existing document.

    Args:
        document_id: The document to generate content for.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
        gen_service: GenerationService dependency.

    Returns:
        The Document with generated content populated.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        document = await run_sync(doc_service.get, company.id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    company_info = {
        "company_name": company.name,
        "company_address": company.address,
        "license_number": company.license_number,
        "trade_type": company.trade_type.value,
        "owner_name": company.owner_name,
        "phone": company.phone,
        "email": company.email,
    }

    try:
        content = await run_sync(
            gen_service.generate_document,
            template_type=document.document_type.value,
            company_info=company_info,
            project_info=document.project_info,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return await run_sync(
        doc_service.set_generated_content,
        company.id, document_id, content, current_user["uid"],
    )


@router.post("/documents/generate", response_model=Document, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_and_generate_my_document(
    request: Request,
    data: DocumentGenerateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
    gen_service: Annotated[GenerationService, Depends(get_generation_service)],
) -> Document:
    """Create a new document and immediately generate its content.

    Args:
        data: Generation request with document type, project info, and title.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.
        billing_service: BillingService dependency.
        gen_service: GenerationService dependency.

    Returns:
        The created Document with generated content.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        await run_sync(billing_service.check_document_limit, company.id)
    except DocumentLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly document limit reached. Upgrade your plan for more documents.",
        )

    create_data = DocumentCreate(
        title=data.title,
        document_type=data.document_type,
        project_info=data.project_info,
    )

    try:
        document = await run_sync(doc_service.create, company.id, create_data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    company_info = {
        "company_name": company.name,
        "company_address": company.address,
        "license_number": company.license_number,
        "trade_type": company.trade_type.value,
        "owner_name": company.owner_name,
        "phone": company.phone,
        "email": company.email,
    }

    try:
        content = await run_sync(
            gen_service.generate_document,
            template_type=data.document_type.value,
            company_info=company_info,
            project_info=data.project_info,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return await run_sync(
        doc_service.set_generated_content,
        company.id, document.id, content, current_user["uid"],
    )


# -- PDF export ----------------------------------------------------------------------


@router.get("/documents/{document_id}/pdf")
async def export_my_document_pdf(
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    doc_service: Annotated[DocumentService, Depends(get_document_service)],
) -> StreamingResponse:
    """Generate and return a PDF for a safety document.

    Args:
        document_id: The document ID to export.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        doc_service: DocumentService dependency.

    Returns:
        StreamingResponse with PDF bytes.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        document = doc_service.get(company.id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    pdf_service = PdfService()
    pdf_bytes = pdf_service.generate(document, company)

    safe_title = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_"
        for c in document.title
    ).strip()
    filename = f"{safe_title}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


# -- Subscription --------------------------------------------------------------------


@router.get("/subscription", response_model=SubscriptionInfo)
async def get_my_subscription(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> SubscriptionInfo:
    """Get subscription status for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        billing_service: BillingService dependency.

    Returns:
        A SubscriptionInfo model.
    """
    company = await _resolve_company(current_user, company_service)
    return billing_service.get_subscription_status(company.id)


class CreateCheckoutRequest(BaseModel):
    """Request body for creating a subscription checkout session."""

    tier: str = Field(
        ...,
        description="Target subscription tier: starter, professional, or business",
    )


class CreateCheckoutResponse(BaseModel):
    """Response containing a checkout URL."""

    checkout_url: str = Field(..., description="Paddle checkout URL")


@router.post("/subscription/create-checkout", response_model=CreateCheckoutResponse)
async def create_checkout(
    body: CreateCheckoutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> CreateCheckoutResponse:
    """Create a Paddle checkout session for upgrading the subscription.

    Args:
        body: Request body containing the target tier.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        billing_service: BillingService dependency.

    Returns:
        A CreateCheckoutResponse with the checkout URL.
    """
    valid_tiers = {"starter", "professional", "business"}
    if body.tier.lower() not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{body.tier}'. Must be one of: {', '.join(sorted(valid_tiers))}",
        )

    company = await _resolve_company(current_user, company_service)
    checkout_url = billing_service.create_checkout(company.id, body.tier)
    return CreateCheckoutResponse(checkout_url=checkout_url)


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: Annotated[dict, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
) -> dict:
    """Cancel the current subscription via Paddle API.

    Args:
        current_user: Authenticated user claims.
        billing_service: BillingService dependency.
        company_service: CompanyService dependency.

    Returns:
        A dict with cancellation status and effective date.
    """
    company = company_service.get_by_user(current_user["uid"])
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    if not company.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel",
        )

    result = billing_service.cancel_subscription(company.subscription_id)
    return {"status": "cancellation_requested", "effective_date": result.get("ends_at")}


# -- Project endpoints ---------------------------------------------------------------


@router.get("/projects", response_model=ProjectListResponse)
async def list_my_projects(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    limit: int = Query(20, ge=1, le=100, description="Max projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    project_status: ProjectStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
) -> ProjectListResponse:
    """List projects for the current user's company with pagination.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        project_service: ProjectService dependency.
        limit: Page size.
        offset: Skip count.
        project_status: Optional status filter.

    Returns:
        A ProjectListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = project_service.list_projects(
        company_id=company.id,
        status=project_status,
        limit=limit,
        offset=offset,
    )
    return ProjectListResponse(projects=result["projects"], total=result["total"])


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_my_project(
    data: ProjectCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
) -> Project:
    """Create a new project for the current user's company.

    Enforces the subscription tier's active project limit before creation.

    Args:
        data: Project creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        project_service: ProjectService dependency.
        billing_service: BillingService dependency.

    Returns:
        The created Project.
    """
    company = await _resolve_company(current_user, company_service)
    billing_service.check_project_limit(company.id)
    try:
        return project_service.create(company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/projects/{project_id}", response_model=Project)
async def get_my_project(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    """Get a specific project by ID, including compliance score.

    Args:
        project_id: The project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        project_service: ProjectService dependency.

    Returns:
        The Project with updated compliance_score.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        project = project_service.get(company.id, project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    # Calculate and include live compliance score
    score = project_service.get_compliance_score(company.id, project_id)
    project.compliance_score = score
    return project


@router.patch("/projects/{project_id}", response_model=Project)
async def update_my_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    """Update a project.

    Args:
        project_id: The project ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        project_service: ProjectService dependency.

    Returns:
        The updated Project.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return project_service.update(company.id, project_id, data, current_user["uid"])
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_project(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Soft-delete a project.

    Args:
        project_id: The project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        project_service: ProjectService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        project_service.delete(company.id, project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


# -- Cross-project aggregate endpoints -----------------------------------------------


@router.get("/inspections", response_model=InspectionListResponse)
async def list_all_inspections(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    limit: int = Query(50, ge=1, le=200, description="Max inspections to return"),
    inspection_type: InspectionType | None = Query(
        None, alias="type", description="Filter by inspection type"
    ),
) -> InspectionListResponse:
    """List inspections across all projects for the current company."""
    company = await _resolve_company(current_user, company_service)
    projects_result = project_service.list_projects(company.id, limit=100)
    all_inspections = []
    for project in projects_result["projects"]:
        result = inspection_service.list_inspections(
            company_id=company.id,
            project_id=project.id,
            inspection_type=inspection_type,
            limit=limit,
        )
        all_inspections.extend(result["inspections"])
    all_inspections.sort(key=lambda i: i.inspection_date, reverse=True)
    return InspectionListResponse(
        inspections=all_inspections[:limit], total=len(all_inspections)
    )


@router.get("/incidents", response_model=IncidentListResponse)
async def list_all_incidents(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    limit: int = Query(50, ge=1, le=200, description="Max incidents to return"),
) -> IncidentListResponse:
    """List incidents across all projects for the current company."""
    company = await _resolve_company(current_user, company_service)
    projects_result = project_service.list_projects(company.id, limit=100)
    all_incidents = []
    for project in projects_result["projects"]:
        result = incident_service.list_incidents(
            company_id=company.id,
            project_id=project.id,
            limit=limit,
        )
        all_incidents.extend(result["incidents"])
    all_incidents.sort(key=lambda i: i.incident_date, reverse=True)
    return IncidentListResponse(
        incidents=all_incidents[:limit], total=len(all_incidents)
    )


@router.get("/toolbox-talks", response_model=ToolboxTalkListResponse)
async def list_all_toolbox_talks(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    toolbox_talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    limit: int = Query(50, ge=1, le=200, description="Max talks to return"),
    talk_status: ToolboxTalkStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
) -> ToolboxTalkListResponse:
    """List toolbox talks across all projects for the current company."""
    company = await _resolve_company(current_user, company_service)
    projects_result = project_service.list_projects(company.id, limit=100)
    all_talks = []
    for project in projects_result["projects"]:
        result = toolbox_talk_service.list_talks(
            company_id=company.id,
            project_id=project.id,
            status=talk_status,
            limit=limit,
        )
        all_talks.extend(result["toolbox_talks"])
    all_talks.sort(key=lambda t: t.created_at, reverse=True)
    return ToolboxTalkListResponse(
        toolbox_talks=all_talks[:limit], total=len(all_talks)
    )


# -- Inspection endpoints ------------------------------------------------------------


@router.get(
    "/projects/{project_id}/inspections",
    response_model=InspectionListResponse,
)
async def list_my_inspections(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
    limit: int = Query(20, ge=1, le=100, description="Max inspections to return"),
    offset: int = Query(0, ge=0, description="Number of inspections to skip"),
    inspection_type: InspectionType | None = Query(
        None, alias="type", description="Filter by inspection type"
    ),
    date_from: date | None = Query(None, description="Filter from date (inclusive)"),
    date_to: date | None = Query(None, description="Filter to date (inclusive)"),
) -> InspectionListResponse:
    """List inspections for a project with optional filters.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        inspection_service: InspectionService dependency.
        limit: Page size.
        offset: Skip count.
        inspection_type: Optional type filter.
        date_from: Optional start date filter.
        date_to: Optional end date filter.

    Returns:
        An InspectionListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = inspection_service.list_inspections(
        company_id=company.id,
        project_id=project_id,
        inspection_type=inspection_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return InspectionListResponse(
        inspections=result["inspections"], total=result["total"]
    )


@router.post(
    "/projects/{project_id}/inspections",
    response_model=Inspection,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_inspection(
    project_id: str,
    data: InspectionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
) -> Inspection:
    """Create a new inspection for a project.

    Args:
        project_id: The parent project ID.
        data: Inspection creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        inspection_service: InspectionService dependency.

    Returns:
        The created Inspection.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return inspection_service.create(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/inspections/{inspection_id}",
    response_model=Inspection,
)
async def get_my_inspection(
    project_id: str,
    inspection_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
) -> Inspection:
    """Get a specific inspection by ID.

    Args:
        project_id: The parent project ID.
        inspection_id: The inspection ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        inspection_service: InspectionService dependency.

    Returns:
        The Inspection.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return inspection_service.get(company.id, project_id, inspection_id)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection not found: {inspection_id}",
        )


@router.patch(
    "/projects/{project_id}/inspections/{inspection_id}",
    response_model=Inspection,
)
async def update_my_inspection(
    project_id: str,
    inspection_id: str,
    data: InspectionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
) -> Inspection:
    """Update an inspection.

    Args:
        project_id: The parent project ID.
        inspection_id: The inspection ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        inspection_service: InspectionService dependency.

    Returns:
        The updated Inspection.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return inspection_service.update(
            company.id, project_id, inspection_id, data, current_user["uid"]
        )
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection not found: {inspection_id}",
        )


@router.delete(
    "/projects/{project_id}/inspections/{inspection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_inspection(
    project_id: str,
    inspection_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    inspection_service: Annotated[InspectionService, Depends(get_inspection_service)],
) -> None:
    """Soft-delete an inspection.

    Args:
        project_id: The parent project ID.
        inspection_id: The inspection ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        inspection_service: InspectionService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        inspection_service.delete(company.id, project_id, inspection_id)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection not found: {inspection_id}",
        )


# -- Inspection template endpoint ----------------------------------------------------


@router.get("/inspection-templates/{inspection_type}")
async def get_inspection_template(
    inspection_type: InspectionType,
    current_user: Annotated[dict, Depends(get_current_user)],
    template_service: Annotated[
        InspectionTemplateService, Depends(get_inspection_template_service)
    ],
) -> list[dict]:
    """Return the checklist template for a given inspection type.

    Args:
        inspection_type: The inspection type to get the template for.
        current_user: Authenticated user claims.
        template_service: InspectionTemplateService dependency.

    Returns:
        A list of checklist item dicts with default values.
    """
    return template_service.get_template_dicts(inspection_type)


# -- Toolbox Talk endpoints ----------------------------------------------------------


@router.get(
    "/projects/{project_id}/toolbox-talks",
    response_model=ToolboxTalkListResponse,
)
async def list_my_toolbox_talks(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    limit: int = Query(20, ge=1, le=100, description="Max talks to return"),
    offset: int = Query(0, ge=0, description="Number of talks to skip"),
    talk_status: ToolboxTalkStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
) -> ToolboxTalkListResponse:
    """List toolbox talks for a project with optional filters.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.
        limit: Page size.
        offset: Skip count.
        talk_status: Optional status filter.

    Returns:
        A ToolboxTalkListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = talk_service.list_talks(
        company_id=company.id,
        project_id=project_id,
        status=talk_status,
        limit=limit,
        offset=offset,
    )
    return ToolboxTalkListResponse(
        toolbox_talks=result["toolbox_talks"], total=result["total"]
    )


@router.post(
    "/projects/{project_id}/toolbox-talks",
    response_model=ToolboxTalk,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_toolbox_talk(
    project_id: str,
    data: ToolboxTalkCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    gen_service: Annotated[GenerationService, Depends(get_generation_service)],
) -> ToolboxTalk:
    """Create a new toolbox talk, optionally generating AI content.

    Args:
        project_id: The parent project ID.
        data: Toolbox talk creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.
        gen_service: GenerationService dependency.

    Returns:
        The created ToolboxTalk.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        talk = await run_sync(
            talk_service.create,
            company.id, project_id, data, current_user["uid"],
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    if data.generate_content:
        company_info = {
            "company_name": company.name,
            "company_address": company.address,
            "license_number": company.license_number,
            "trade_type": company.trade_type.value,
        }
        project_info = {
            "project_id": project_id,
            "target_audience": data.target_audience,
            "target_trade": data.target_trade or "",
            "duration_minutes": str(data.duration_minutes),
        }

        try:
            content = await run_sync(
                gen_service.generate_toolbox_talk,
                topic=data.topic,
                company_info=company_info,
                project_info=project_info,
                language=data.language,
                custom_points=data.custom_points,
            )
        except GenerationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            )

        content_en = content.get("en")
        content_es = content.get("es")
        talk = await run_sync(
            talk_service.set_generated_content,
            company.id, project_id, talk.id,
            content_en=content_en,
            content_es=content_es,
            user_id=current_user["uid"],
        )

    return talk


@router.get(
    "/projects/{project_id}/toolbox-talks/{talk_id}",
    response_model=ToolboxTalk,
)
async def get_my_toolbox_talk(
    project_id: str,
    talk_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> ToolboxTalk:
    """Get a specific toolbox talk by ID.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.

    Returns:
        The ToolboxTalk.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return talk_service.get(company.id, project_id, talk_id)
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )


@router.patch(
    "/projects/{project_id}/toolbox-talks/{talk_id}",
    response_model=ToolboxTalk,
)
async def update_my_toolbox_talk(
    project_id: str,
    talk_id: str,
    data: ToolboxTalkUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> ToolboxTalk:
    """Update a toolbox talk.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.

    Returns:
        The updated ToolboxTalk.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return talk_service.update(
            company.id, project_id, talk_id, data, current_user["uid"]
        )
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )


@router.delete(
    "/projects/{project_id}/toolbox-talks/{talk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_toolbox_talk(
    project_id: str,
    talk_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> None:
    """Soft-delete a toolbox talk.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        talk_service.delete(company.id, project_id, talk_id)
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )


@router.post(
    "/projects/{project_id}/toolbox-talks/{talk_id}/attend",
    response_model=ToolboxTalk,
)
async def attend_my_toolbox_talk(
    project_id: str,
    talk_id: str,
    data: AttendeeCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> ToolboxTalk:
    """Add an attendee signature to a toolbox talk.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        data: Attendee information.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.

    Returns:
        The updated ToolboxTalk with the new attendee.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return talk_service.add_attendee(company.id, project_id, talk_id, data)
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )


@router.post(
    "/projects/{project_id}/toolbox-talks/{talk_id}/complete",
    response_model=ToolboxTalk,
)
async def complete_my_toolbox_talk(
    project_id: str,
    talk_id: str,
    data: CompleteTalkRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
) -> ToolboxTalk:
    """Mark a toolbox talk as completed with presenter info.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        data: Completion details.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.

    Returns:
        The completed ToolboxTalk.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return talk_service.complete_talk(
            company.id, project_id, talk_id,
            presented_by=data.presented_by,
            notes=data.notes,
        )
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )


@router.post(
    "/projects/{project_id}/toolbox-talks/{talk_id}/generate",
    response_model=ToolboxTalk,
)
async def generate_my_toolbox_talk_content(
    project_id: str,
    talk_id: str,
    data: GenerateContentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    talk_service: Annotated[ToolboxTalkService, Depends(get_toolbox_talk_service)],
    gen_service: Annotated[GenerationService, Depends(get_generation_service)],
) -> ToolboxTalk:
    """Generate or regenerate AI content for a toolbox talk.

    Args:
        project_id: The parent project ID.
        talk_id: The toolbox talk ID.
        data: Language preferences for generation.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        talk_service: ToolboxTalkService dependency.
        gen_service: GenerationService dependency.

    Returns:
        The ToolboxTalk with updated generated content.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        talk = talk_service.get(company.id, project_id, talk_id)
    except ToolboxTalkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Toolbox talk not found: {talk_id}",
        )

    company_info = {
        "company_name": company.name,
        "company_address": company.address,
        "license_number": company.license_number,
        "trade_type": company.trade_type.value,
    }
    project_info = {
        "project_id": project_id,
        "target_audience": talk.target_audience,
        "target_trade": talk.target_trade or "",
        "duration_minutes": str(talk.duration_minutes),
    }

    try:
        content = gen_service.generate_toolbox_talk(
            topic=talk.topic,
            company_info=company_info,
            project_info=project_info,
            language=data.language,
            custom_points=talk.custom_points,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    content_en = content.get("en")
    content_es = content.get("es")
    return talk_service.set_generated_content(
        company.id, project_id, talk.id,
        content_en=content_en,
        content_es=content_es,
        user_id=current_user["uid"],
    )


# -- Worker endpoints ----------------------------------------------------------------


@router.get("/workers/expiring-certifications", response_model=ExpiringCertificationsResponse)
async def get_expiring_certifications(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    days: int = Query(30, ge=1, le=365, description="Days ahead to check"),
) -> ExpiringCertificationsResponse:
    """Get all certifications expiring within N days across all workers.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.
        days: Number of days ahead to check.

    Returns:
        An ExpiringCertificationsResponse with expiring certs.
    """
    company = await _resolve_company(current_user, company_service)
    result = worker_service.get_expiring_certifications(company.id, days_ahead=days)
    return ExpiringCertificationsResponse(
        certifications=result["certifications"], total=result["total"]
    )


@router.get("/workers/certification-matrix", response_model=CertificationMatrixResponse)
async def get_certification_matrix(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> CertificationMatrixResponse:
    """Get the certification matrix: workers x cert types with status.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        A CertificationMatrixResponse with the full matrix.
    """
    company = await _resolve_company(current_user, company_service)
    result = worker_service.get_certification_matrix(company.id)
    return CertificationMatrixResponse(
        matrix=result["matrix"],
        workers=result["workers"],
        certification_types=result["certification_types"],
    )


@router.get("/workers", response_model=WorkerListResponse)
async def list_my_workers(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
    limit: int = Query(20, ge=1, le=100, description="Max workers to return"),
    offset: int = Query(0, ge=0, description="Number of workers to skip"),
    worker_status: WorkerStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    role: str | None = Query(None, description="Filter by role"),
    trade: str | None = Query(None, description="Filter by trade"),
    search: str | None = Query(None, description="Search by name"),
) -> WorkerListResponse:
    """List workers for the current user's company with pagination.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.
        limit: Page size.
        offset: Skip count.
        worker_status: Optional status filter.
        role: Optional role filter.
        trade: Optional trade filter.
        search: Optional name search.

    Returns:
        A WorkerListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = worker_service.list_workers(
        company_id=company.id,
        status=worker_status,
        role=role,
        trade=trade,
        search=search,
        limit=limit,
        offset=offset,
    )
    return WorkerListResponse(workers=result["workers"], total=result["total"])


@router.post("/workers", response_model=Worker, status_code=status.HTTP_201_CREATED)
async def create_my_worker(
    data: WorkerCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Create a new worker for the current user's company.

    Args:
        data: Worker creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The created Worker.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.create(company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/workers/{worker_id}", response_model=Worker)
async def get_my_worker(
    worker_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Get a specific worker by ID with certifications.

    Args:
        worker_id: The worker ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The Worker with computed certification statuses.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.get(company.id, worker_id)
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )


@router.patch("/workers/{worker_id}", response_model=Worker)
async def update_my_worker(
    worker_id: str,
    data: WorkerUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Update a worker.

    Args:
        worker_id: The worker ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The updated Worker.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.update(company.id, worker_id, data, current_user["uid"])
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )


@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_worker(
    worker_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> None:
    """Soft-delete a worker (set status to terminated).

    Args:
        worker_id: The worker ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        worker_service.delete(company.id, worker_id)
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )


# -- Worker certification endpoints --------------------------------------------------


@router.post(
    "/workers/{worker_id}/certifications",
    response_model=Worker,
    status_code=status.HTTP_201_CREATED,
)
async def add_worker_certification(
    worker_id: str,
    data: CertificationCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Add a certification to a worker.

    Args:
        worker_id: The worker ID.
        data: Certification creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The updated Worker with the new certification.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.add_certification(company.id, worker_id, data)
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )


@router.patch(
    "/workers/{worker_id}/certifications/{cert_id}",
    response_model=Worker,
)
async def update_worker_certification(
    worker_id: str,
    cert_id: str,
    data: CertificationUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Update a certification on a worker.

    Args:
        worker_id: The worker ID.
        cert_id: The certification ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The updated Worker.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.update_certification(
            company.id, worker_id, cert_id, data
        )
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/workers/{worker_id}/certifications/{cert_id}",
    response_model=Worker,
)
async def remove_worker_certification(
    worker_id: str,
    cert_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    worker_service: Annotated[WorkerService, Depends(get_worker_service)],
) -> Worker:
    """Remove a certification from a worker.

    Args:
        worker_id: The worker ID.
        cert_id: The certification ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        worker_service: WorkerService dependency.

    Returns:
        The updated Worker without the removed certification.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return worker_service.remove_certification(company.id, worker_id, cert_id)
    except WorkerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker not found: {worker_id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# -- OSHA 300 Log endpoints ----------------------------------------------------------


@router.get("/osha-log/entries", response_model=OshaLogEntryListResponse)
async def list_osha_log_entries(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    year: int | None = Query(None, description="Filter by calendar year"),
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
) -> OshaLogEntryListResponse:
    """List OSHA 300 Log entries for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.
        year: Optional year filter.
        limit: Page size.
        offset: Skip count.

    Returns:
        An OshaLogEntryListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = osha_log_service.list_entries(
        company_id=company.id,
        year=year,
        limit=limit,
        offset=offset,
    )
    return OshaLogEntryListResponse(entries=result["entries"], total=result["total"])


@router.post(
    "/osha-log/entries",
    response_model=OshaLogEntry,
    status_code=status.HTTP_201_CREATED,
)
async def create_osha_log_entry(
    data: OshaLogEntryCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> OshaLogEntry:
    """Create a new OSHA 300 Log entry.

    Args:
        data: Entry creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.

    Returns:
        The created OshaLogEntry.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return osha_log_service.create_entry(company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/osha-log/entries/{entry_id}", response_model=OshaLogEntry)
async def get_osha_log_entry(
    entry_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> OshaLogEntry:
    """Get a specific OSHA 300 Log entry by ID.

    Args:
        entry_id: The entry ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.

    Returns:
        The OshaLogEntry.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return osha_log_service.get_entry(company.id, entry_id)
    except OshaLogEntryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OSHA log entry not found: {entry_id}",
        )


@router.patch("/osha-log/entries/{entry_id}", response_model=OshaLogEntry)
async def update_osha_log_entry(
    entry_id: str,
    data: OshaLogEntryUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> OshaLogEntry:
    """Update an OSHA 300 Log entry.

    Args:
        entry_id: The entry ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.

    Returns:
        The updated OshaLogEntry.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return osha_log_service.update_entry(
            company.id, entry_id, data, current_user["uid"]
        )
    except OshaLogEntryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OSHA log entry not found: {entry_id}",
        )


@router.delete(
    "/osha-log/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_osha_log_entry(
    entry_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> None:
    """Delete an OSHA 300 Log entry.

    Args:
        entry_id: The entry ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        osha_log_service.delete_entry(company.id, entry_id)
    except OshaLogEntryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OSHA log entry not found: {entry_id}",
        )


@router.get("/osha-log/summary", response_model=Osha300Summary)
async def get_osha_300a_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    year: int = Query(..., description="Calendar year for the summary"),
) -> Osha300Summary:
    """Get the OSHA 300A Annual Summary for a given year.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.
        year: The calendar year.

    Returns:
        The computed Osha300Summary.
    """
    company = await _resolve_company(current_user, company_service)
    return osha_log_service.get_300a_summary(company.id, year)


@router.post("/osha-log/summary/certify", response_model=Osha300Summary)
async def certify_osha_300a_summary(
    data: CertifySummaryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
    year: int = Query(..., description="Calendar year to certify"),
) -> Osha300Summary:
    """Certify the OSHA 300A summary for a given year.

    Args:
        data: Certification request data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.
        year: The calendar year.

    Returns:
        The certified Osha300Summary.
    """
    company = await _resolve_company(current_user, company_service)
    return osha_log_service.certify_summary(
        company_id=company.id,
        year=year,
        certified_by=data.certified_by,
        annual_average_employees=data.annual_average_employees,
        total_hours_worked=data.total_hours_worked,
    )


@router.get("/osha-log/years", response_model=OshaLogYearsResponse)
async def list_osha_log_years(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    osha_log_service: Annotated[OshaLogService, Depends(get_osha_log_service)],
) -> OshaLogYearsResponse:
    """List years that have OSHA 300 Log entries.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        osha_log_service: OshaLogService dependency.

    Returns:
        An OshaLogYearsResponse with sorted year list.
    """
    company = await _resolve_company(current_user, company_service)
    years = osha_log_service.get_years_with_entries(company.id)
    return OshaLogYearsResponse(years=years)


# -- Mock OSHA Inspection endpoints ------------------------------------------


@router.post(
    "/mock-inspection/run",
    response_model=MockInspectionResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_feature("mock_inspection"))],
)
@limiter.limit("3/minute")
async def run_mock_inspection(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    mock_inspection_service: Annotated[
        MockInspectionService, Depends(get_mock_inspection_service)
    ],
    data: RunInspectionRequest | None = None,
) -> MockInspectionResult:
    """Run a mock OSHA inspection on the current user's company.

    Optionally scope to a specific project and/or enable deep AI audit.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        mock_inspection_service: MockInspectionService dependency.
        data: Optional request body with project_id and deep_audit flag.

    Returns:
        The complete MockInspectionResult with all findings.
    """
    company = await _resolve_company(current_user, company_service)

    project_id = data.project_id if data else None
    deep_audit = data.deep_audit if data else False

    result = await run_sync(
        mock_inspection_service.run_inspection,
        company_id=company.id,
        project_id=project_id,
        deep_audit=deep_audit,
        user_id=current_user["uid"],
    )
    return result


@router.get(
    "/mock-inspection/results",
    response_model=MockInspectionListResponse,
)
async def list_mock_inspection_results(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    mock_inspection_service: Annotated[
        MockInspectionService, Depends(get_mock_inspection_service)
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MockInspectionListResponse:
    """List past mock inspection results with pagination.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        mock_inspection_service: MockInspectionService dependency.
        limit: Maximum results per page.
        offset: Number of results to skip.

    Returns:
        Paginated list of mock inspection result summaries.
    """
    company = await _resolve_company(current_user, company_service)
    data = mock_inspection_service.list_results(
        company.id, limit=limit, offset=offset
    )
    return MockInspectionListResponse(**data)


@router.get(
    "/mock-inspection/results/{result_id}",
    response_model=MockInspectionResult,
)
async def get_mock_inspection_result(
    result_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    mock_inspection_service: Annotated[
        MockInspectionService, Depends(get_mock_inspection_service)
    ],
) -> MockInspectionResult:
    """Get a specific mock inspection result by ID.

    Args:
        result_id: The mock inspection result ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        mock_inspection_service: MockInspectionService dependency.

    Returns:
        The full MockInspectionResult with all findings.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return mock_inspection_service.get_result(company.id, result_id)
    except MockInspectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mock inspection result not found: {result_id}",
        )


# -- Hazard Report endpoints ---------------------------------------------------------


@router.post(
    "/projects/{project_id}/hazard-reports",
    response_model=HazardReport,
    status_code=status.HTTP_201_CREATED,
)
async def create_hazard_report(
    project_id: str,
    data: HazardReportCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    hazard_report_service: Annotated[
        HazardReportService, Depends(get_hazard_report_service)
    ],
) -> HazardReport:
    """Create a hazard report by analyzing a photo with AI.

    Accepts a base64-encoded photo, runs AI hazard analysis, and saves
    the report with identified hazards.

    Args:
        project_id: The project to create the report for.
        data: Hazard report creation data including photo.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        hazard_report_service: HazardReportService dependency.

    Returns:
        The created HazardReport with AI analysis results.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return hazard_report_service.create_from_photo(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


@router.get(
    "/projects/{project_id}/hazard-reports",
    response_model=HazardReportListResponse,
)
async def list_hazard_reports(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    hazard_report_service: Annotated[
        HazardReportService, Depends(get_hazard_report_service)
    ],
    limit: int = Query(20, ge=1, le=100, description="Max reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    report_status: HazardStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    severity: HazardSeverity | None = Query(
        None, description="Filter by highest severity"
    ),
) -> HazardReportListResponse:
    """List hazard reports for a project with optional filters.

    Args:
        project_id: The project to list reports for.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        hazard_report_service: HazardReportService dependency.
        limit: Maximum number of reports to return.
        offset: Number of reports to skip.
        report_status: Optional status filter.
        severity: Optional severity filter.

    Returns:
        A HazardReportListResponse with reports and total count.
    """
    company = await _resolve_company(current_user, company_service)
    data = hazard_report_service.list_reports(
        company.id,
        project_id,
        report_status=report_status,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return HazardReportListResponse(**data)


@router.get(
    "/projects/{project_id}/hazard-reports/{report_id}",
    response_model=HazardReport,
)
async def get_hazard_report(
    project_id: str,
    report_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    hazard_report_service: Annotated[
        HazardReportService, Depends(get_hazard_report_service)
    ],
) -> HazardReport:
    """Get a specific hazard report by ID.

    Args:
        project_id: The parent project ID.
        report_id: The hazard report ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        hazard_report_service: HazardReportService dependency.

    Returns:
        The HazardReport.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return hazard_report_service.get(company.id, project_id, report_id)
    except HazardReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hazard report not found: {report_id}",
        )


@router.patch(
    "/projects/{project_id}/hazard-reports/{report_id}",
    response_model=HazardReport,
)
async def update_hazard_report_status(
    project_id: str,
    report_id: str,
    data: HazardReportStatusUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    hazard_report_service: Annotated[
        HazardReportService, Depends(get_hazard_report_service)
    ],
) -> HazardReport:
    """Update the status and corrective action of a hazard report.

    Args:
        project_id: The parent project ID.
        report_id: The hazard report ID.
        data: Status update data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        hazard_report_service: HazardReportService dependency.

    Returns:
        The updated HazardReport.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return hazard_report_service.update_status(
            company.id, project_id, report_id, data, current_user["uid"]
        )
    except HazardReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hazard report not found: {report_id}",
        )


@router.delete(
    "/projects/{project_id}/hazard-reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hazard_report(
    project_id: str,
    report_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    hazard_report_service: Annotated[
        HazardReportService, Depends(get_hazard_report_service)
    ],
) -> None:
    """Delete a hazard report.

    Args:
        project_id: The parent project ID.
        report_id: The hazard report ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        hazard_report_service: HazardReportService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        hazard_report_service.delete(company.id, project_id, report_id)
    except HazardReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hazard report not found: {report_id}",
        )


@router.post("/analyze-photo", dependencies=[Depends(require_feature("photo_hazard"))])
@limiter.limit("10/minute")
async def quick_analyze_photo(
    request: Request,
    data: QuickAnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    analysis_service: Annotated[
        HazardAnalysisService, Depends(get_hazard_analysis_service)
    ],
) -> dict:
    """Perform a quick photo hazard analysis without saving a report.

    Returns the AI analysis result directly for preview purposes.

    Args:
        data: Photo and context data.
        current_user: Authenticated user claims.
        analysis_service: HazardAnalysisService dependency.

    Returns:
        Dict with identified_hazards, summary, and positive_observations.
    """
    # Strip data URI prefix if present
    photo_base64 = data.photo_base64
    if photo_base64.startswith("data:"):
        comma_idx = photo_base64.index(",")
        photo_base64 = photo_base64[comma_idx + 1 :]

    context = {
        "description": data.description,
        "location": data.location,
    }

    try:
        return await run_sync(
            analysis_service.analyze_photo,
            image_base64=photo_base64,
            image_media_type=data.media_type,
            context=context,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


# -- Morning Brief endpoints --------------------------------------------------------


@router.get(
    "/projects/{project_id}/morning-brief",
    response_model=MorningBrief,
    dependencies=[Depends(require_feature("morning_brief"))],
)
async def get_today_morning_brief(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    morning_brief_service: Annotated[
        MorningBriefService, Depends(get_morning_brief_service)
    ],
) -> MorningBrief:
    """Get today's morning brief for a project, generating if not exists.

    Args:
        project_id: The project to get the brief for.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        morning_brief_service: MorningBriefService dependency.

    Returns:
        Today's MorningBrief.
    """
    company = await _resolve_company(current_user, company_service)

    try:
        # Check if today's brief already exists
        existing = await run_sync(morning_brief_service.get_today_brief, company.id, project_id)
        if existing is not None:
            return existing

        # Generate a new brief for today
        return await run_sync(morning_brief_service.generate_brief, company.id, project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/morning-briefs",
    response_model=MorningBriefListResponse,
    dependencies=[Depends(require_feature("morning_brief"))],
)
async def list_morning_briefs(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    morning_brief_service: Annotated[
        MorningBriefService, Depends(get_morning_brief_service)
    ],
    limit: int = Query(20, ge=1, le=100, description="Max briefs to return"),
) -> MorningBriefListResponse:
    """List past morning briefs for a project.

    Args:
        project_id: The project to list briefs for.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        morning_brief_service: MorningBriefService dependency.
        limit: Maximum number of briefs to return.

    Returns:
        A MorningBriefListResponse with briefs and total count.
    """
    company = await _resolve_company(current_user, company_service)
    result = morning_brief_service.list_briefs(
        company.id, project_id, limit=limit
    )
    return MorningBriefListResponse(
        briefs=result["briefs"], total=result["total"]
    )


# -- Incident endpoints --------------------------------------------------------------


@router.get(
    "/projects/{project_id}/incidents",
    response_model=IncidentListResponse,
)
async def list_my_incidents(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
    limit: int = Query(20, ge=1, le=100, description="Max incidents to return"),
    offset: int = Query(0, ge=0, description="Number of incidents to skip"),
) -> IncidentListResponse:
    """List incidents for a project with pagination.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.
        limit: Page size.
        offset: Skip count.

    Returns:
        An IncidentListResponse with paginated results.
    """
    company = await _resolve_company(current_user, company_service)
    result = incident_service.list_incidents(
        company_id=company.id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return IncidentListResponse(
        incidents=result["incidents"], total=result["total"]
    )


@router.post(
    "/projects/{project_id}/incidents",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_incident(
    project_id: str,
    data: IncidentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
) -> Incident:
    """Create a new incident report.

    Args:
        project_id: The parent project ID.
        data: Incident creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.

    Returns:
        The created Incident.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return incident_service.create(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/incidents/{incident_id}",
    response_model=Incident,
)
async def get_my_incident(
    project_id: str,
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
) -> Incident:
    """Get a specific incident by ID.

    Args:
        project_id: The parent project ID.
        incident_id: The incident ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.

    Returns:
        The Incident.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return incident_service.get(company.id, project_id, incident_id)
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident not found: {incident_id}",
        )


@router.patch(
    "/projects/{project_id}/incidents/{incident_id}",
    response_model=Incident,
)
async def update_my_incident(
    project_id: str,
    incident_id: str,
    data: IncidentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
) -> Incident:
    """Update an existing incident.

    Args:
        project_id: The parent project ID.
        incident_id: The incident ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.

    Returns:
        The updated Incident.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return incident_service.update(
            company.id, project_id, incident_id, data, current_user["uid"]
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident not found: {incident_id}",
        )


@router.delete(
    "/projects/{project_id}/incidents/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_incident(
    project_id: str,
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
) -> None:
    """Delete an incident report.

    Args:
        project_id: The parent project ID.
        incident_id: The incident ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        incident_service.delete(company.id, project_id, incident_id)
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident not found: {incident_id}",
        )


@router.post(
    "/projects/{project_id}/incidents/{incident_id}/investigate",
    response_model=Incident,
)
async def investigate_incident(
    project_id: str,
    incident_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    incident_service: Annotated[IncidentService, Depends(get_incident_service)],
) -> Incident:
    """Trigger AI-assisted root cause analysis for an incident.

    Args:
        project_id: The parent project ID.
        incident_id: The incident ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        incident_service: IncidentService dependency.

    Returns:
        The Incident with ai_analysis populated.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return incident_service.generate_investigation(
            company.id, project_id, incident_id, current_user["uid"]
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident not found: {incident_id}",
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


# -- Analytics endpoints --------------------------------------------------------------


@router.get("/analytics/dashboard", response_model=SafetyDashboardMetrics)
async def get_dashboard_metrics(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> SafetyDashboardMetrics:
    """Get full safety dashboard metrics for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        analytics_service: AnalyticsService dependency.

    Returns:
        A SafetyDashboardMetrics with all aggregated data.
    """
    company = await _resolve_company(current_user, company_service)
    return analytics_service.get_dashboard_metrics(company.id)


@router.post("/analytics/emr-estimate", response_model=EmrEstimate)
async def estimate_emr(
    data: EmrEstimateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> EmrEstimate:
    """Calculate EMR projection and financial impact.

    Args:
        data: EMR estimation input with current_emr, payroll, and rate.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        analytics_service: AnalyticsService dependency.

    Returns:
        An EmrEstimate with projections and recommendations.
    """
    company = await _resolve_company(current_user, company_service)

    # Get current year TRIR for projection
    current_year = date.today().year
    try:
        summary = analytics_service.osha_log_service.get_300a_summary(
            company.id, current_year
        )
        trir = summary.trir
    except Exception:
        trir = 0.0

    return AnalyticsService.get_emr_estimate(
        current_emr=data.current_emr,
        annual_payroll=data.annual_payroll,
        workers_comp_rate=data.workers_comp_rate,
        trir=trir,
    )


# -- Prequalification endpoints --------------------------------------------------------

from app.models.prequalification import (  # noqa: E402
    PrequalPackage,
    PrequalPackageListResponse,
    PrequalPlatform,
    PrequalRequirementsResponse,
)
from app.services.prequalification_service import PrequalificationService  # noqa: E402


@router.post(
    "/prequalification/generate",
    response_model=PrequalPackage,
    dependencies=[Depends(require_feature("prequalification_auto"))],
)
@limiter.limit("5/minute")
async def generate_prequal_package(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    prequal_service: Annotated[
        PrequalificationService, Depends(get_prequalification_service)
    ],
    platform: PrequalPlatform = Query(
        default=PrequalPlatform.GENERIC,
        description="Target prequalification platform",
    ),
    client_name: str = Query(
        default="",
        description="Name of the GC or owner requesting prequalification",
    ),
) -> PrequalPackage:
    """Generate a prequalification package from existing company data.

    Assembles documents, OSHA records, training data, and pre-fills
    questionnaire answers for the target platform.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        prequal_service: PrequalificationService dependency.
        platform: Target prequalification platform.
        client_name: Name of the requesting GC/owner.

    Returns:
        A PrequalPackage with readiness scores and pre-filled data.
    """
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        prequal_service.generate_package,
        company_id=company.id,
        platform=platform,
        client_name=client_name,
        user_id=current_user["uid"],
    )


@router.get(
    "/prequalification/packages",
    response_model=PrequalPackageListResponse,
    dependencies=[Depends(require_feature("prequalification_auto"))],
)
async def list_prequal_packages(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    prequal_service: Annotated[
        PrequalificationService, Depends(get_prequalification_service)
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PrequalPackageListResponse:
    """List prequalification packages for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        prequal_service: PrequalificationService dependency.
        limit: Maximum number of packages to return.
        offset: Number of packages to skip.

    Returns:
        A PrequalPackageListResponse with packages and total count.
    """
    company = await _resolve_company(current_user, company_service)
    result = prequal_service.list_packages(company.id, limit=limit, offset=offset)
    return PrequalPackageListResponse(**result)


@router.get("/prequalification/packages/{package_id}", response_model=PrequalPackage)
async def get_prequal_package(
    package_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    prequal_service: Annotated[
        PrequalificationService, Depends(get_prequalification_service)
    ],
) -> PrequalPackage:
    """Get a specific prequalification package.

    Args:
        package_id: The package ID to retrieve.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        prequal_service: PrequalificationService dependency.

    Returns:
        The PrequalPackage.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return prequal_service.get_package(company.id, package_id)
    except PrequalPackageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prequalification package not found: {package_id}",
        )


@router.get(
    "/prequalification/requirements/{platform}",
    response_model=PrequalRequirementsResponse,
)
async def get_prequal_requirements(
    platform: PrequalPlatform,
    current_user: Annotated[dict, Depends(get_current_user)],
    prequal_service: Annotated[
        PrequalificationService, Depends(get_prequalification_service)
    ],
) -> PrequalRequirementsResponse:
    """Get the document requirements for a prequalification platform.

    Args:
        platform: The target prequalification platform.
        current_user: Authenticated user claims.
        prequal_service: PrequalificationService dependency.

    Returns:
        A PrequalRequirementsResponse with platform requirements.
    """
    if platform == PrequalPlatform.ISNETWORLD:
        reqs = prequal_service.get_isnetworld_requirements()
    elif platform == PrequalPlatform.AVETTA:
        reqs = prequal_service.get_avetta_requirements()
    elif platform == PrequalPlatform.BROWZ:
        reqs = prequal_service.get_avetta_requirements()
    else:
        reqs = prequal_service.get_generic_gc_requirements()

    return PrequalRequirementsResponse(
        platform=platform,
        requirements=reqs,
        total=len(reqs),
    )


# -- State Compliance endpoints --------------------------------------------------------

from app.models.state_compliance import (  # noqa: E402
    StateComplianceCheck,
    StateListResponse,
    StateRequirementsResponse,
)
from app.services.state_compliance_service import StateComplianceService  # noqa: E402


@router.get("/state-compliance/states", response_model=StateListResponse)
async def list_available_states(
    current_user: Annotated[dict, Depends(get_current_user)],
    state_service: Annotated[
        StateComplianceService, Depends(get_state_compliance_service)
    ],
) -> StateListResponse:
    """List states with supported compliance checks.

    Args:
        current_user: Authenticated user claims.
        state_service: StateComplianceService dependency.

    Returns:
        A StateListResponse with available states.
    """
    states = state_service.get_available_states()
    return StateListResponse(states=states, total=len(states))


@router.get(
    "/state-compliance/requirements/{state}",
    response_model=StateRequirementsResponse,
)
async def get_state_requirements(
    state: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    state_service: Annotated[
        StateComplianceService, Depends(get_state_compliance_service)
    ],
) -> StateRequirementsResponse:
    """Get state-specific safety requirements.

    Args:
        state: Two-letter state code (e.g., 'CA', 'NY').
        current_user: Authenticated user claims.
        state_service: StateComplianceService dependency.

    Returns:
        A StateRequirementsResponse with state requirements.
    """
    requirements = state_service.get_state_requirements(state)
    return StateRequirementsResponse(
        state=state.upper(),
        requirements=requirements,
        total=len(requirements),
    )


@router.get("/state-compliance/check/{state}", response_model=StateComplianceCheck)
async def check_state_compliance(
    state: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    state_service: Annotated[
        StateComplianceService, Depends(get_state_compliance_service)
    ],
) -> StateComplianceCheck:
    """Check company compliance against state-specific requirements.

    Args:
        state: Two-letter state code (e.g., 'CA', 'NY').
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        state_service: StateComplianceService dependency.

    Returns:
        A StateComplianceCheck with gaps and compliance percentage.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return state_service.check_compliance(company.id, state)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


# -- Environmental Compliance endpoints -----------------------------------------------


@router.post(
    "/environmental/programs",
    response_model=EnvironmentalProgram,
    status_code=status.HTTP_201_CREATED,
)
async def create_environmental_program(
    data: EnvironmentalProgramCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> EnvironmentalProgram:
    """Create a new environmental compliance program.

    Args:
        data: Program creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        The created EnvironmentalProgram.
    """
    company = await _resolve_company(current_user, company_service)
    return env_service.create_program(company.id, data, current_user["uid"])


@router.get(
    "/environmental/programs",
    response_model=EnvironmentalProgramListResponse,
)
async def list_environmental_programs(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    program_type: EnvironmentalProgramType | None = Query(None, alias="type"),
) -> EnvironmentalProgramListResponse:
    """List environmental programs for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.
        limit: Page size.
        offset: Skip count.
        program_type: Optional type filter.

    Returns:
        An EnvironmentalProgramListResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = env_service.list_programs(
        company_id=company.id,
        program_type=program_type,
        limit=limit,
        offset=offset,
    )
    return EnvironmentalProgramListResponse(
        programs=result["programs"], total=result["total"]
    )


@router.get(
    "/environmental/programs/{program_id}",
    response_model=EnvironmentalProgram,
)
async def get_environmental_program(
    program_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> EnvironmentalProgram:
    """Get a specific environmental program by ID.

    Args:
        program_id: The program ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        The EnvironmentalProgram.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return env_service.get_program(company.id, program_id)
    except EnvironmentalProgramNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental program not found: {program_id}",
        )


@router.patch(
    "/environmental/programs/{program_id}",
    response_model=EnvironmentalProgram,
)
async def update_environmental_program(
    program_id: str,
    data: EnvironmentalProgramUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> EnvironmentalProgram:
    """Update an existing environmental program.

    Args:
        program_id: The program ID to update.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        The updated EnvironmentalProgram.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return env_service.update_program(
            company.id, program_id, data, current_user["uid"]
        )
    except EnvironmentalProgramNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental program not found: {program_id}",
        )


@router.delete(
    "/environmental/programs/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_environmental_program(
    program_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> None:
    """Delete an environmental program (soft-delete).

    Args:
        program_id: The program ID to delete.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        env_service.delete_program(company.id, program_id)
    except EnvironmentalProgramNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environmental program not found: {program_id}",
        )


@router.post(
    "/projects/{project_id}/exposure-records",
    response_model=ExposureMonitoringRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_exposure_record(
    project_id: str,
    data: ExposureMonitoringRecordCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> ExposureMonitoringRecord:
    """Create an exposure monitoring record for a project.

    Args:
        project_id: The parent project ID.
        data: Exposure record data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        The created ExposureMonitoringRecord.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return env_service.create_exposure_record(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/exposure-records",
    response_model=ExposureMonitoringRecordListResponse,
)
async def list_exposure_records(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    monitoring_type: str | None = Query(None, alias="type"),
    worker_id: str | None = Query(None),
) -> ExposureMonitoringRecordListResponse:
    """List exposure monitoring records for a project.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.
        limit: Page size.
        offset: Skip count.
        monitoring_type: Optional type filter.
        worker_id: Optional worker ID filter.

    Returns:
        An ExposureMonitoringRecordListResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = env_service.list_exposure_records(
        company_id=company.id,
        project_id=project_id,
        monitoring_type=monitoring_type,
        worker_id=worker_id,
        limit=limit,
        offset=offset,
    )
    return ExposureMonitoringRecordListResponse(
        records=result["records"], total=result["total"]
    )


@router.get(
    "/projects/{project_id}/exposure-records/summary",
    response_model=ExposureSummaryResponse,
)
async def get_exposure_summary(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> ExposureSummaryResponse:
    """Get a summary of exposure monitoring results by type.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        An ExposureSummaryResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = env_service.get_exposure_summary(company.id, project_id)
    return ExposureSummaryResponse(
        summaries=result["summaries"], total_samples=result["total_samples"]
    )


@router.post(
    "/projects/{project_id}/swppp-inspections",
    response_model=SwpppInspection,
    status_code=status.HTTP_201_CREATED,
)
async def create_swppp_inspection(
    project_id: str,
    data: SwpppInspectionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> SwpppInspection:
    """Create a SWPPP inspection record for a project.

    Args:
        project_id: The parent project ID.
        data: SWPPP inspection data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        The created SwpppInspection.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return env_service.create_swppp_inspection(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/swppp-inspections",
    response_model=SwpppInspectionListResponse,
)
async def list_swppp_inspections(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SwpppInspectionListResponse:
    """List SWPPP inspections for a project.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.
        limit: Page size.
        offset: Skip count.

    Returns:
        A SwpppInspectionListResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = env_service.list_swppp_inspections(
        company_id=company.id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return SwpppInspectionListResponse(
        inspections=result["inspections"], total=result["total"]
    )


@router.get(
    "/environmental/compliance-status",
    response_model=ComplianceStatusResponse,
)
async def get_compliance_status(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    env_service: Annotated[EnvironmentalService, Depends(get_environmental_service)],
) -> ComplianceStatusResponse:
    """Get overall environmental compliance status.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        env_service: EnvironmentalService dependency.

    Returns:
        A ComplianceStatusResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = env_service.get_compliance_status(company.id)
    return ComplianceStatusResponse(**result)


# -- Equipment & Fleet Management endpoints -------------------------------------------


@router.get(
    "/equipment",
    response_model=EquipmentListResponse,
)
async def list_my_equipment(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    equipment_type: EquipmentType | None = Query(None, alias="type"),
    equipment_status: EquipmentStatus | None = Query(None, alias="status"),
    project_id: str | None = Query(None),
) -> EquipmentListResponse:
    """List equipment for the current user's company.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.
        limit: Page size.
        offset: Skip count.
        equipment_type: Optional type filter.
        equipment_status: Optional status filter.
        project_id: Optional project filter.

    Returns:
        An EquipmentListResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = equip_service.list_equipment(
        company_id=company.id,
        equipment_type=equipment_type,
        equipment_status=equipment_status,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return EquipmentListResponse(
        equipment=result["equipment"], total=result["total"]
    )


@router.post(
    "/equipment",
    response_model=Equipment,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_equipment(
    data: EquipmentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> Equipment:
    """Create a new equipment record.

    Args:
        data: Equipment creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        The created Equipment.
    """
    company = await _resolve_company(current_user, company_service)
    return equip_service.create(company.id, data, current_user["uid"])


@router.get(
    "/equipment/overdue-inspections",
    response_model=OverdueEquipmentResponse,
)
async def get_overdue_equipment_inspections(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> OverdueEquipmentResponse:
    """List equipment with overdue inspections.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        An OverdueEquipmentResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = equip_service.get_overdue_inspections(company.id)
    return OverdueEquipmentResponse(
        equipment=result["equipment"], total=result["total"]
    )


@router.get(
    "/equipment/summary",
    response_model=EquipmentSummaryResponse,
)
async def get_equipment_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> EquipmentSummaryResponse:
    """Get equipment fleet summary.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        An EquipmentSummaryResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = equip_service.get_equipment_summary(company.id)
    return EquipmentSummaryResponse(**result)


@router.get(
    "/equipment/dot-compliance",
    response_model=DotComplianceResponse,
)
async def get_dot_compliance(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> DotComplianceResponse:
    """Get DOT vehicle compliance status.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        A DotComplianceResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = equip_service.get_dot_compliance_status(company.id)
    return DotComplianceResponse(**result)


@router.get(
    "/equipment/{equipment_id}",
    response_model=Equipment,
)
async def get_my_equipment(
    equipment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> Equipment:
    """Get a specific equipment record by ID.

    Args:
        equipment_id: The equipment ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        The Equipment.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return equip_service.get(company.id, equipment_id)
    except EquipmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {equipment_id}",
        )


@router.patch(
    "/equipment/{equipment_id}",
    response_model=Equipment,
)
async def update_my_equipment(
    equipment_id: str,
    data: EquipmentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> Equipment:
    """Update an existing equipment record.

    Args:
        equipment_id: The equipment ID to update.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        The updated Equipment.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return equip_service.update(
            company.id, equipment_id, data, current_user["uid"]
        )
    except EquipmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {equipment_id}",
        )


@router.delete(
    "/equipment/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_equipment(
    equipment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> None:
    """Delete an equipment record (soft-delete).

    Args:
        equipment_id: The equipment ID to delete.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        equip_service.delete(company.id, equipment_id)
    except EquipmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {equipment_id}",
        )


@router.post(
    "/equipment/{equipment_id}/inspections",
    response_model=EquipmentInspectionLog,
    status_code=status.HTTP_201_CREATED,
)
async def create_equipment_inspection(
    equipment_id: str,
    data: EquipmentInspectionLogCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> EquipmentInspectionLog:
    """Create an inspection log for an equipment item.

    Args:
        equipment_id: The equipment ID.
        data: Inspection log data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        The created EquipmentInspectionLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return equip_service.create_inspection_log(
            company.id, equipment_id, data, current_user["uid"]
        )
    except EquipmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {equipment_id}",
        )


@router.get(
    "/equipment/{equipment_id}/inspections",
    response_model=EquipmentInspectionLogListResponse,
)
async def list_equipment_inspections(
    equipment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> EquipmentInspectionLogListResponse:
    """List inspection logs for an equipment item.

    Args:
        equipment_id: The equipment ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.
        limit: Page size.
        offset: Skip count.

    Returns:
        An EquipmentInspectionLogListResponse.
    """
    company = await _resolve_company(current_user, company_service)
    result = equip_service.list_inspection_logs(
        company_id=company.id,
        equipment_id=equipment_id,
        limit=limit,
        offset=offset,
    )
    return EquipmentInspectionLogListResponse(
        logs=result["logs"], total=result["total"]
    )


@router.get(
    "/equipment/{equipment_id}/inspection-template",
)
async def get_equipment_inspection_template(
    equipment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    equip_service: Annotated[EquipmentService, Depends(get_equipment_service)],
) -> dict:
    """Get the pre-built inspection checklist for an equipment item's type.

    Args:
        equipment_id: The equipment ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        equip_service: EquipmentService dependency.

    Returns:
        A dict with 'template' list of checklist items.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        equipment = equip_service.get(company.id, equipment_id)
    except EquipmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment not found: {equipment_id}",
        )
    template = EquipmentService.get_inspection_template(equipment.equipment_type.value)
    return {"template": template, "equipment_type": equipment.equipment_type.value}


# ---------------------------------------------------------------------------
# Project Assignments
# ---------------------------------------------------------------------------


@router.get("/assignments", response_model=ProjectAssignmentListResponse)
async def list_my_assignments(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
    project_id: str | None = Query(None, description="Filter by project"),
    resource_type: ResourceType | None = Query(None, description="Filter: worker or equipment"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    assignment_status: AssignmentStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ProjectAssignmentListResponse:
    """List project assignments with optional filters.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.
        project_id: Optional project filter.
        resource_type: Optional worker/equipment filter.
        resource_id: Optional specific resource filter.
        assignment_status: Optional status filter.
        limit: Max results.
        offset: Pagination offset.

    Returns:
        ProjectAssignmentListResponse with assignments and total count.
    """
    company = await _resolve_company(current_user, company_service)
    result = assignment_service.list_assignments(
        company_id=company.id,
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        status=assignment_status,
        limit=limit,
        offset=offset,
    )
    return ProjectAssignmentListResponse(
        assignments=result["assignments"], total=result["total"]
    )


@router.post(
    "/assignments",
    response_model=ProjectAssignment,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_assignment(
    data: ProjectAssignmentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
) -> ProjectAssignment:
    """Create a project assignment (assign worker or equipment to a project).

    Args:
        data: Assignment creation payload.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.

    Returns:
        The created ProjectAssignment.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return assignment_service.create(company.id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/assignments/{assignment_id}", response_model=ProjectAssignment)
async def get_my_assignment(
    assignment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
) -> ProjectAssignment:
    """Fetch a single project assignment.

    Args:
        assignment_id: The assignment ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.

    Returns:
        The ProjectAssignment.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return assignment_service.get(company.id, assignment_id)
    except AssignmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found: {assignment_id}",
        )


@router.patch("/assignments/{assignment_id}", response_model=ProjectAssignment)
async def update_my_assignment(
    assignment_id: str,
    data: ProjectAssignmentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
) -> ProjectAssignment:
    """Update a project assignment.

    Args:
        assignment_id: The assignment ID.
        data: Update payload (only non-None fields applied).
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.

    Returns:
        The updated ProjectAssignment.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return assignment_service.update(
            company.id, assignment_id, data, current_user["uid"]
        )
    except AssignmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found: {assignment_id}",
        )


@router.delete(
    "/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_assignment(
    assignment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
) -> None:
    """Soft-delete a project assignment.

    Args:
        assignment_id: The assignment ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        assignment_service.delete(company.id, assignment_id)
    except AssignmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment not found: {assignment_id}",
        )


@router.get(
    "/projects/{project_id}/assignments",
    response_model=ProjectAssignmentListResponse,
)
async def list_project_assignments(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assignment_service: Annotated[
        ProjectAssignmentService, Depends(get_project_assignment_service)
    ],
    resource_type: ResourceType | None = Query(None),
    assignment_status: AssignmentStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ProjectAssignmentListResponse:
    """List assignments for a specific project.

    Args:
        project_id: The project to list assignments for.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        assignment_service: ProjectAssignmentService dependency.
        resource_type: Optional worker/equipment filter.
        assignment_status: Optional status filter.
        limit: Max results.
        offset: Pagination offset.

    Returns:
        ProjectAssignmentListResponse with assignments and total count.
    """
    company = await _resolve_company(current_user, company_service)
    result = assignment_service.list_assignments(
        company_id=company.id,
        project_id=project_id,
        resource_type=resource_type,
        status=assignment_status,
        limit=limit,
        offset=offset,
    )
    return ProjectAssignmentListResponse(
        assignments=result["assignments"], total=result["total"]
    )
