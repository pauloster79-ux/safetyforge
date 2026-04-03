"""Pydantic models for company profiles."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator


class TradeType(str, Enum):
    """Construction trade types."""

    GENERAL = "general"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    ROOFING = "roofing"
    CONCRETE = "concrete"
    STEEL = "steel"
    DEMOLITION = "demolition"
    EXCAVATION = "excavation"
    PAINTING = "painting"
    CARPENTRY = "carpentry"
    MASONRY = "masonry"
    LANDSCAPING = "landscaping"
    FIRE_PROTECTION = "fire_protection"
    OTHER = "other"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    FREE = "free"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    PAUSED = "paused"


class CompanyCreate(BaseModel):
    """Input model for creating a company profile."""

    name: str = Field(..., min_length=2, max_length=128, description="Company legal name")
    address: str = Field(..., min_length=5, max_length=256, description="Business address")
    license_number: str = Field(
        ..., min_length=1, max_length=64, description="Contractor license number"
    )
    trade_type: TradeType = Field(..., description="Primary trade classification")
    owner_name: str = Field(..., min_length=2, max_length=128, description="Owner/principal name")
    phone: str = Field(..., min_length=7, max_length=20, description="Business phone number")
    email: EmailStr = Field(..., description="Business email address")
    ein: str | None = Field(None, max_length=20, description="Employer Identification Number")
    tax_id: str | None = Field(None, max_length=64, description="Tax identifier (EIN, UTR, ABN, etc.)")
    tax_id_type: str | None = Field(None, max_length=20, description="Tax ID type: EIN, UTR, ABN, VAT, GST")
    jurisdiction_code: str = Field(default="US", max_length=5, description="Country jurisdiction code (US, UK, AU, CA)")
    jurisdiction_region: str | None = Field(None, max_length=64, description="Sub-national region (state, province, etc.)")
    safety_officer: str | None = Field(None, max_length=128, description="Safety officer name")
    safety_officer_phone: str | None = Field(
        None, max_length=20, description="Safety officer phone number"
    )
    logo_url: str | None = Field(None, max_length=512, description="Company logo URL")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Strip whitespace and validate phone has only allowed characters."""
        cleaned = v.strip()
        allowed = set("0123456789+-() .")
        if not all(c in allowed for c in cleaned):
            raise ValueError("Phone number contains invalid characters")
        return cleaned


class CompanyUpdate(BaseModel):
    """Input model for updating a company profile. All fields optional."""

    name: str | None = Field(None, min_length=2, max_length=128)
    address: str | None = Field(None, min_length=5, max_length=256)
    license_number: str | None = Field(None, min_length=1, max_length=64)
    trade_type: TradeType | None = None
    owner_name: str | None = Field(None, min_length=2, max_length=128)
    phone: str | None = Field(None, min_length=7, max_length=20)
    email: EmailStr | None = None
    ein: str | None = Field(None, max_length=20)
    tax_id: str | None = Field(None, max_length=64)
    tax_id_type: str | None = Field(None, max_length=20)
    jurisdiction_code: str | None = Field(None, max_length=5)
    jurisdiction_region: str | None = Field(None, max_length=64)
    safety_officer: str | None = Field(None, max_length=128)
    safety_officer_phone: str | None = Field(None, max_length=20)
    logo_url: str | None = Field(None, max_length=512)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Strip whitespace and validate phone has only allowed characters."""
        if v is None:
            return v
        cleaned = v.strip()
        allowed = set("0123456789+-() .")
        if not all(c in allowed for c in cleaned):
            raise ValueError("Phone number contains invalid characters")
        return cleaned


class Company(BaseModel):
    """Full company model with ID and audit fields."""

    id: str
    name: str
    address: str
    license_number: str
    trade_type: TradeType
    owner_name: str
    phone: str
    email: str
    ein: str | None = None
    tax_id: str | None = None
    tax_id_type: str | None = None
    jurisdiction_code: str = "US"
    jurisdiction_region: str | None = None
    safety_officer: str | None = None
    safety_officer_phone: str | None = None
    logo_url: str | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    subscription_status: SubscriptionStatus = SubscriptionStatus.FREE
    subscription_id: str | None = None
