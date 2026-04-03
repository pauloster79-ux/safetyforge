"""Template listing router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.template import Template, TemplateListResponse
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TemplateListResponse:
    """List all available document templates.

    Args:
        current_user: Authenticated user claims (auth required).

    Returns:
        A TemplateListResponse with all templates and a count.
    """
    service = TemplateService()
    templates = service.list_templates()
    return TemplateListResponse(templates=templates, total=len(templates))


@router.get("/{document_type}", response_model=Template)
async def get_template(
    document_type: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Template:
    """Get a specific template by document type.

    Args:
        document_type: The document type key (sssp, jha, etc.).
        current_user: Authenticated user claims (auth required).

    Returns:
        The Template definition.
    """
    service = TemplateService()
    template = service.get_template(document_type)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found for document type: {document_type}",
        )
    return template
