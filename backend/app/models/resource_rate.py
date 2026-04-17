"""Pydantic models for ResourceRate — company rate knowledge."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Type of resource being rated."""

    LABOUR = "labour"
    MATERIAL = "material"
    EQUIPMENT = "equipment"


class RateUnit(str, Enum):
    """Unit the rate is expressed in."""

    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_UNIT = "per_unit"
    PER_LF = "per_lf"
    PER_SF = "per_sf"
    PER_CY = "per_cy"
    PER_EA = "per_ea"
    PER_TON = "per_ton"
    LUMP_SUM = "lump_sum"


class RateSource(str, Enum):
    """How the rate was established."""

    MANUAL_ENTRY = "manual_entry"
    DERIVED_FROM_ACTUALS = "derived_from_actuals"
    SUPPLIER_QUOTE = "supplier_quote"


class ResourceRateCreate(BaseModel):
    """Input model for creating a resource rate."""

    resource_type: ResourceType = Field(..., description="Type of resource")
    description: str = Field(
        ..., min_length=2, max_length=512, description="Human-readable description"
    )
    rate_cents: int = Field(..., ge=0, description="Rate in cents per unit")
    unit: RateUnit = Field(..., description="What the rate is per")
    source: RateSource = Field(
        default=RateSource.MANUAL_ENTRY, description="How rate was established"
    )
    base_rate_cents: int | None = Field(
        None, ge=0, description="Pre-burden rate in cents (labour)"
    )
    burden_percent: float | None = Field(
        None, ge=0, le=100, description="On-cost percentage (labour)"
    )
    non_productive_percent: float | None = Field(
        None, ge=0, le=100, description="Non-productive time adjustment (labour)"
    )
    supplier_name: str = Field(
        default="", max_length=256, description="Supplier providing this rate"
    )
    quote_valid_until: date | None = Field(
        None, description="Supplier quote expiry date"
    )


class ResourceRateUpdate(BaseModel):
    """Input model for updating a resource rate. All fields optional."""

    resource_type: ResourceType | None = None
    description: str | None = Field(None, min_length=2, max_length=512)
    rate_cents: int | None = Field(None, ge=0)
    unit: RateUnit | None = None
    source: RateSource | None = None
    base_rate_cents: int | None = Field(None, ge=0)
    burden_percent: float | None = Field(None, ge=0, le=100)
    non_productive_percent: float | None = Field(None, ge=0, le=100)
    supplier_name: str | None = Field(None, max_length=256)
    quote_valid_until: date | None = None
    active: bool | None = None


class ResourceRate(BaseModel):
    """Full resource rate model with ID and audit fields."""

    id: str
    company_id: str
    resource_type: ResourceType
    description: str
    rate_cents: int
    unit: RateUnit
    source: RateSource
    base_rate_cents: int | None = None
    burden_percent: float | None = None
    non_productive_percent: float | None = None
    supplier_name: str = ""
    quote_valid_until: date | None = None
    sample_size: int | None = None
    std_deviation_cents: int | None = None
    last_derived_at: datetime | None = None
    active: bool = True
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class ResourceRateListResponse(BaseModel):
    """Response model for listing resource rates."""

    rates: list[ResourceRate]
    total: int
