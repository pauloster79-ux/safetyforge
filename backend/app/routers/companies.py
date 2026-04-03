"""Company profile CRUD router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore

from app.dependencies import get_current_user, get_firestore_client
from app.exceptions import CompanyNotFoundError
from app.models.company import Company, CompanyCreate, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Company:
    """Create a new company profile.

    A user can only have one company. Returns 409 if the user already has one.

    Args:
        data: Validated company creation data.
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The created Company.
    """
    service = CompanyService(db)

    existing = service.get_by_user(current_user["uid"])
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a company profile",
        )

    return service.create(data, current_user["uid"])


@router.get("/me", response_model=Company)
async def get_my_company(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Company:
    """Get the current user's company profile.

    Args:
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The user's Company.
    """
    service = CompanyService(db)
    company = service.get_by_user(current_user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


@router.get("/{company_id}", response_model=Company)
async def get_company(
    company_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Company:
    """Get a company by ID.

    Args:
        company_id: The company document ID.
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The Company.
    """
    service = CompanyService(db)
    try:
        return service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )


@router.patch("/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
) -> Company:
    """Update a company profile.

    Only the company owner can update the profile.

    Args:
        company_id: The company document ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        db: Firestore client.

    Returns:
        The updated Company.
    """
    service = CompanyService(db)

    try:
        existing = service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )

    if existing.created_by != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this company",
        )

    try:
        return service.update(company_id, data, current_user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )
