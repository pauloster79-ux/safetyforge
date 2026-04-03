"""Pydantic models for equipment and fleet management."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class EquipmentType(str, Enum):
    """Available equipment types."""

    CRANE = "crane"
    FORKLIFT = "forklift"
    AERIAL_LIFT = "aerial_lift"
    SCISSOR_LIFT = "scissor_lift"
    EXCAVATOR = "excavator"
    LOADER = "loader"
    SKID_STEER = "skid_steer"
    CONCRETE_PUMP = "concrete_pump"
    GENERATOR = "generator"
    COMPRESSOR = "compressor"
    SCAFFOLD_SYSTEM = "scaffold_system"
    FALL_PROTECTION_EQUIPMENT = "fall_protection_equipment"
    VEHICLE = "vehicle"
    TRAILER = "trailer"
    OTHER = "other"


class EquipmentStatus(str, Enum):
    """Equipment operational status."""

    ACTIVE = "active"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class InspectionFrequency(str, Enum):
    """Equipment inspection frequency."""

    PRE_SHIFT = "pre_shift"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class EquipmentCreate(BaseModel):
    """Input model for creating equipment."""

    name: str = Field(
        ..., min_length=1, max_length=256,
        description="Equipment name, e.g. CAT 320 Excavator",
    )
    equipment_type: EquipmentType = Field(..., description="Type of equipment")
    make: str = Field(default="", max_length=128, description="Manufacturer")
    model: str = Field(default="", max_length=128, description="Model name/number")
    year: int | None = Field(None, description="Year of manufacture")
    serial_number: str = Field(default="", max_length=128, description="Serial number")
    vin: str = Field(default="", max_length=17, description="VIN for vehicles")
    license_plate: str = Field(default="", max_length=20, description="License plate for vehicles")
    current_project_id: str | None = Field(None, description="Assigned project ID")
    status: EquipmentStatus = Field(
        default=EquipmentStatus.ACTIVE, description="Operational status"
    )
    inspection_frequency: InspectionFrequency = Field(
        default=InspectionFrequency.DAILY, description="How often to inspect"
    )
    annual_inspection_date: date | None = Field(
        None, description="Last annual inspection date"
    )
    annual_inspection_due: date | None = Field(
        None, description="Next annual inspection due date"
    )
    annual_inspection_vendor: str = Field(
        default="", max_length=256, description="Annual inspection vendor"
    )
    annual_inspection_cert_url: str | None = Field(
        None, description="Annual inspection certificate URL"
    )
    dot_inspection_date: date | None = Field(None, description="Last DOT inspection date")
    dot_inspection_due: date | None = Field(None, description="Next DOT inspection due date")
    dot_number: str = Field(default="", max_length=20, description="DOT number")
    last_maintenance_date: date | None = Field(None, description="Last maintenance date")
    next_maintenance_due: date | None = Field(None, description="Next maintenance due date")
    maintenance_notes: str = Field(default="", max_length=2000, description="Maintenance notes")
    required_certifications: list[str] = Field(
        default_factory=list, description="Cert types needed to operate"
    )
    notes: str = Field(default="", max_length=2000, description="Additional notes")


class EquipmentUpdate(BaseModel):
    """Input model for updating equipment. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=256)
    equipment_type: EquipmentType | None = None
    make: str | None = Field(None, max_length=128)
    model: str | None = Field(None, max_length=128)
    year: int | None = None
    serial_number: str | None = Field(None, max_length=128)
    vin: str | None = Field(None, max_length=17)
    license_plate: str | None = Field(None, max_length=20)
    current_project_id: str | None = None
    status: EquipmentStatus | None = None
    inspection_frequency: InspectionFrequency | None = None
    annual_inspection_date: date | None = None
    annual_inspection_due: date | None = None
    annual_inspection_vendor: str | None = Field(None, max_length=256)
    annual_inspection_cert_url: str | None = None
    dot_inspection_date: date | None = None
    dot_inspection_due: date | None = None
    dot_number: str | None = Field(None, max_length=20)
    last_maintenance_date: date | None = None
    next_maintenance_due: date | None = None
    maintenance_notes: str | None = Field(None, max_length=2000)
    required_certifications: list[str] | None = None
    notes: str | None = Field(None, max_length=2000)


class Equipment(BaseModel):
    """Full equipment model with ID and audit fields."""

    id: str
    company_id: str
    name: str
    equipment_type: EquipmentType
    make: str = ""
    model: str = ""
    year: int | None = None
    serial_number: str = ""
    vin: str = ""
    license_plate: str = ""
    current_project_id: str | None = None
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    last_inspection_date: date | None = None
    next_inspection_due: date | None = None
    inspection_frequency: InspectionFrequency = InspectionFrequency.DAILY
    annual_inspection_date: date | None = None
    annual_inspection_due: date | None = None
    annual_inspection_vendor: str = ""
    annual_inspection_cert_url: str | None = None
    dot_inspection_date: date | None = None
    dot_inspection_due: date | None = None
    dot_number: str = ""
    last_maintenance_date: date | None = None
    next_maintenance_due: date | None = None
    maintenance_notes: str = ""
    required_certifications: list[str] = Field(default_factory=list)
    notes: str = ""
    created_at: datetime
    updated_at: datetime
    deleted: bool = False


class EquipmentListResponse(BaseModel):
    """Response model for listing equipment."""

    equipment: list[Equipment]
    total: int


class EquipmentInspectionLogCreate(BaseModel):
    """Input model for creating an equipment inspection log."""

    project_id: str | None = Field(None, description="Project where inspection was done")
    inspection_date: date = Field(..., description="Date of inspection")
    inspector_name: str = Field(
        ..., min_length=2, max_length=128, description="Inspector name"
    )
    inspection_type: str = Field(
        ..., description="Type: pre_shift, daily, monthly, annual"
    )
    items: list[dict] = Field(
        default_factory=list, description="Checklist items [{item, status, notes}]"
    )
    overall_status: str = Field(..., description="Overall result: pass or fail")
    deficiencies_found: str = Field(
        default="", max_length=5000, description="Deficiencies found"
    )
    corrective_action: str = Field(
        default="", max_length=5000, description="Corrective action taken"
    )
    out_of_service: bool = Field(
        default=False, description="Equipment tagged out of service?"
    )


class EquipmentInspectionLog(EquipmentInspectionLogCreate):
    """Full equipment inspection log with ID and audit fields."""

    id: str
    company_id: str
    equipment_id: str
    created_at: datetime
    created_by: str


class EquipmentInspectionLogListResponse(BaseModel):
    """Response model for listing equipment inspection logs."""

    logs: list[EquipmentInspectionLog]
    total: int


class EquipmentSummaryResponse(BaseModel):
    """Response model for equipment fleet summary."""

    total_equipment: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    overdue_inspections: int = 0
    overdue_maintenance: int = 0


class OverdueEquipment(BaseModel):
    """Equipment with an overdue inspection."""

    equipment_id: str
    equipment_name: str
    equipment_type: EquipmentType
    next_inspection_due: date | None = None
    days_overdue: int = 0


class OverdueEquipmentResponse(BaseModel):
    """Response model for overdue inspections endpoint."""

    equipment: list[OverdueEquipment]
    total: int


class DotComplianceEntry(BaseModel):
    """DOT compliance status for a single vehicle."""

    equipment_id: str
    equipment_name: str
    dot_number: str = ""
    dot_inspection_date: date | None = None
    dot_inspection_due: date | None = None
    status: str = Field(description="compliant, overdue, missing")


class DotComplianceResponse(BaseModel):
    """Response model for DOT compliance status."""

    vehicles: list[DotComplianceEntry]
    total: int
    compliant: int = 0
    overdue: int = 0
    missing: int = 0
