"""Pydantic models for company members and invitations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class MemberRole(str, Enum):
    """Role hierarchy for company members."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MemberCreate(BaseModel):
    """Input model for inviting a new member."""

    email: EmailStr = Field(..., description="Email address of the member to invite")
    display_name: str = Field(..., min_length=2, max_length=128, description="Display name")
    role: MemberRole = Field(..., description="Role to assign to the member")


class MemberUpdate(BaseModel):
    """Input model for updating a member. All fields optional."""

    role: MemberRole | None = None
    display_name: str | None = Field(None, min_length=2, max_length=128)


class Member(BaseModel):
    """Full member model with ID and audit fields."""

    id: str
    company_id: str
    uid: str
    email: str
    display_name: str
    role: MemberRole
    invited_by: str | None = None
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class InvitationStatus(str, Enum):
    """Status values for member invitations."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class InvitationCreate(BaseModel):
    """Input model for creating an invitation."""

    email: EmailStr = Field(..., description="Email address to invite")
    role: MemberRole = Field(..., description="Role to assign when accepted")


class Invitation(BaseModel):
    """Full invitation model with all fields."""

    id: str
    company_id: str
    company_name: str
    email: str
    role: MemberRole
    status: InvitationStatus
    invited_by: str
    invited_by_email: str
    token: str
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None = None
