"""Document CRUD and generation router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from google.cloud import firestore

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_firestore_client, verify_company_access
from app.exceptions import (
    CompanyNotFoundError,
    DocumentLimitExceededError,
    DocumentNotFoundError,
    GenerationError,
)
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentGenerateRequest,
    DocumentListResponse,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
)
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/companies/{company_id}/documents", tags=["documents"])


# Use shared verify_company_access from dependencies
_verify_company_access = verify_company_access


@router.post("", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    company_id: str,
    data: DocumentCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Document:
    """Create a new draft document for a company.

    Checks the document limit for free tier users before creation.

    Args:
        company_id: The owning company ID.
        data: Document creation data.
        current_user: Authenticated user claims.
        db: Firestore client.
        settings: Application settings.

    Returns:
        The created Document.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    billing_service = BillingService(db, settings)
    try:
        billing_service.check_document_limit(company_id)
    except DocumentLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly document limit reached. Upgrade to Pro for unlimited documents.",
        )

    doc_service = DocumentService(db)
    try:
        return doc_service.create(company_id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    company_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    document_type: DocumentType | None = Query(None, description="Filter by document type"),
    document_status: DocumentStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
) -> DocumentListResponse:
    """List documents for a company with optional filters.

    Args:
        company_id: The owning company ID.
        current_user: Authenticated user claims.
        db: Firestore client.
        document_type: Optional document type filter.
        document_status: Optional status filter.

    Returns:
        A DocumentListResponse with matching documents.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    doc_service = DocumentService(db)
    result = doc_service.list_documents(company_id, document_type, document_status)
    return DocumentListResponse(documents=result["documents"], total=result["total"])


@router.get("/{document_id}", response_model=Document)
async def get_document(
    company_id: str,
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Document:
    """Get a single document by ID.

    Args:
        company_id: The owning company ID.
        document_id: The document ID.
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The Document.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    doc_service = DocumentService(db)
    try:
        return doc_service.get(company_id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.patch("/{document_id}", response_model=Document)
async def update_document(
    company_id: str,
    document_id: str,
    data: DocumentUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Document:
    """Update a document's content, title, or status.

    Args:
        company_id: The owning company ID.
        document_id: The document ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The updated Document.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    doc_service = DocumentService(db)
    try:
        return doc_service.update(company_id, document_id, data, current_user["uid"])
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    company_id: str,
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> None:
    """Soft-delete a document.

    Args:
        company_id: The owning company ID.
        document_id: The document ID.
        current_user: Authenticated user claims.
        db: Firestore client.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    doc_service = DocumentService(db)
    try:
        doc_service.delete(company_id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )


@router.post("/{document_id}/generate", response_model=Document)
async def generate_document_content(
    company_id: str,
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Document:
    """Generate AI content for an existing document.

    Uses the document's type and project_info to generate content via Claude.

    Args:
        company_id: The owning company ID.
        document_id: The document to generate content for.
        current_user: Authenticated user claims.
        db: Firestore client.
        settings: Application settings.

    Returns:
        The Document with generated content populated.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    doc_service = DocumentService(db)
    company_service = CompanyService(db)

    try:
        document = doc_service.get(company_id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    try:
        company = company_service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
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

    gen_service = GenerationService(settings)
    try:
        content = gen_service.generate_document(
            template_type=document.document_type.value,
            company_info=company_info,
            project_info=document.project_info,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return doc_service.set_generated_content(
        company_id, document_id, content, current_user["uid"]
    )


@router.post("/generate", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_and_generate_document(
    company_id: str,
    data: DocumentGenerateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Document:
    """Create a new document and immediately generate its content.

    Convenience endpoint that combines document creation and AI generation
    into a single request.

    Args:
        company_id: The owning company ID.
        data: Generation request with document type, project info, and title.
        current_user: Authenticated user claims.
        db: Firestore client.
        settings: Application settings.

    Returns:
        The created Document with generated content.
    """
    _verify_company_access(company_id, current_user["uid"], db)

    billing_service = BillingService(db, settings)
    try:
        billing_service.check_document_limit(company_id)
    except DocumentLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly document limit reached. Upgrade to Pro for unlimited documents.",
        )

    doc_service = DocumentService(db)
    company_service = CompanyService(db)

    create_data = DocumentCreate(
        title=data.title,
        document_type=data.document_type,
        project_info=data.project_info,
    )

    try:
        document = doc_service.create(company_id, create_data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )

    try:
        company = company_service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
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

    gen_service = GenerationService(settings)
    try:
        content = gen_service.generate_document(
            template_type=data.document_type.value,
            company_info=company_info,
            project_info=data.project_info,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    return doc_service.set_generated_content(
        company_id, document.id, content, current_user["uid"]
    )
