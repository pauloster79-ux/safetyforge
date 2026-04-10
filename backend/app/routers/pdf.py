"""PDF export router for safety documents."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from neo4j import Driver

from app.dependencies import get_current_user, get_neo4j_driver, verify_company_access
from app.exceptions import CompanyNotFoundError, DocumentNotFoundError
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.pdf_service import PdfService

router = APIRouter(
    prefix="/companies/{company_id}/documents",
    tags=["pdf"],
)


_verify_company_access = verify_company_access


@router.get("/{document_id}/pdf")
async def export_document_pdf(
    company_id: str,
    document_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> StreamingResponse:
    """Generate and return a PDF for a safety document.

    Fetches the document from Neo4j, generates a branded PDF
    using WeasyPrint, and returns it as a downloadable file.

    Args:
        company_id: The owning company ID.
        document_id: The document ID to export.
        current_user: Authenticated user claims.
        driver: Neo4j driver.

    Returns:
        StreamingResponse with PDF bytes and content-disposition header.

    Raises:
        HTTPException: 404 if company or document not found, 403 if access denied.
    """
    _verify_company_access(company_id, current_user["uid"], driver)

    doc_service = DocumentService(driver)
    try:
        document = doc_service.get(company_id, document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    company_service = CompanyService(driver)
    try:
        company = company_service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
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
