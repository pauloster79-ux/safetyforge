"""Equipment and fleet management service against Firestore."""

import secrets
from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, EquipmentNotFoundError
from app.models.equipment import (
    Equipment,
    EquipmentCreate,
    EquipmentInspectionLog,
    EquipmentInspectionLogCreate,
    EquipmentStatus,
    EquipmentType,
    EquipmentUpdate,
)

# Pre-built inspection checklists per equipment type
EQUIPMENT_INSPECTION_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "crane": [
        {"item": "Boom condition", "category": "Structure"},
        {"item": "Wire rope condition and reeving", "category": "Rigging"},
        {"item": "Outriggers and pads", "category": "Stability"},
        {"item": "Load chart available and legible", "category": "Documentation"},
        {"item": "Anti-two-block device functional", "category": "Safety Systems"},
        {"item": "Load moment indicator functional", "category": "Safety Systems"},
        {"item": "Hydraulic system — no leaks", "category": "Hydraulics"},
        {"item": "Swing brake operational", "category": "Controls"},
        {"item": "Horn and warning devices", "category": "Safety"},
        {"item": "Fire extinguisher present and charged", "category": "Safety"},
        {"item": "Operator certification verified", "category": "Documentation"},
        {"item": "Ground conditions adequate", "category": "Site"},
    ],
    "forklift": [
        {"item": "Tire condition and pressure", "category": "Tires"},
        {"item": "Fork condition — no cracks or bends", "category": "Forks"},
        {"item": "Hydraulic system — no leaks", "category": "Hydraulics"},
        {"item": "Horn operational", "category": "Safety"},
        {"item": "Lights operational (head, tail, warning)", "category": "Safety"},
        {"item": "Seat belt functional", "category": "Safety"},
        {"item": "Overhead guard intact", "category": "Structure"},
        {"item": "Brakes — service and parking", "category": "Brakes"},
        {"item": "Steering operation smooth", "category": "Controls"},
        {"item": "Fluid levels (engine oil, coolant, hydraulic)", "category": "Fluids"},
    ],
    "aerial_lift": [
        {"item": "Upper and lower controls functional", "category": "Controls"},
        {"item": "Guardrails and mid-rails intact", "category": "Fall Protection"},
        {"item": "Outriggers operational and pads present", "category": "Stability"},
        {"item": "Emergency lowering system functional", "category": "Safety Systems"},
        {"item": "Warning labels legible", "category": "Documentation"},
        {"item": "Hydraulic system — no leaks", "category": "Hydraulics"},
        {"item": "Tire condition (if applicable)", "category": "Tires"},
        {"item": "Platform floor — no damage or debris", "category": "Platform"},
        {"item": "Boom condition — no cracks", "category": "Structure"},
        {"item": "Horn and alarm operational", "category": "Safety"},
    ],
    "vehicle": [
        {"item": "Tire condition and pressure", "category": "Tires"},
        {"item": "Brakes — service and parking", "category": "Brakes"},
        {"item": "Lights — head, tail, brake, turn signals", "category": "Lights"},
        {"item": "Mirrors — side and rear view", "category": "Visibility"},
        {"item": "Horn operational", "category": "Safety"},
        {"item": "Seat belts functional", "category": "Safety"},
        {"item": "Fire extinguisher present and charged", "category": "Safety"},
        {"item": "First aid kit present", "category": "Safety"},
        {"item": "Fluid levels (oil, coolant, washer)", "category": "Fluids"},
        {"item": "Windshield and wipers condition", "category": "Visibility"},
    ],
}


class EquipmentService:
    """Manages equipment and fleet records in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore document reference.
        """
        return self.db.collection("companies").document(company_id)

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the equipment subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("equipment")

    def _inspection_logs_collection(
        self, company_id: str, equipment_id: str
    ) -> firestore.CollectionReference:
        """Return the inspection_logs subcollection for an equipment item.

        Args:
            company_id: The parent company ID.
            equipment_id: The equipment ID.

        Returns:
            Firestore collection reference.
        """
        return (
            self._collection(company_id)
            .document(equipment_id)
            .collection("inspection_logs")
        )

    def _generate_id(self) -> str:
        """Generate a unique equipment ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"eqp_{secrets.token_hex(8)}"

    def _generate_log_id(self) -> str:
        """Generate a unique inspection log ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"eqlog_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    @staticmethod
    def _serialize_dates(data: dict[str, Any]) -> dict[str, Any]:
        """Serialize date fields to ISO format strings for Firestore.

        Args:
            data: Dict with potential date fields.

        Returns:
            Dict with date fields as ISO strings.
        """
        date_fields = [
            "last_inspection_date",
            "next_inspection_due",
            "annual_inspection_date",
            "annual_inspection_due",
            "dot_inspection_date",
            "dot_inspection_due",
            "last_maintenance_date",
            "next_maintenance_due",
            "inspection_date",
        ]
        result = dict(data)
        for field in date_fields:
            value = result.get(field)
            if value is not None and hasattr(value, "isoformat"):
                result[field] = value.isoformat()
        return result

    # -- Equipment CRUD ----------------------------------------------------------------

    def create(
        self, company_id: str, data: EquipmentCreate, user_id: str
    ) -> Equipment:
        """Create a new equipment record.

        Args:
            company_id: The owning company ID.
            data: Validated equipment creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Equipment with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        equip_id = self._generate_id()

        equip_dict: dict[str, Any] = {
            "id": equip_id,
            "company_id": company_id,
            "name": data.name,
            "equipment_type": data.equipment_type.value,
            "make": data.make,
            "model": data.model,
            "year": data.year,
            "serial_number": data.serial_number,
            "vin": data.vin,
            "license_plate": data.license_plate,
            "current_project_id": data.current_project_id,
            "status": data.status.value,
            "last_inspection_date": None,
            "next_inspection_due": None,
            "inspection_frequency": data.inspection_frequency.value,
            "annual_inspection_date": (
                data.annual_inspection_date.isoformat()
                if data.annual_inspection_date
                else None
            ),
            "annual_inspection_due": (
                data.annual_inspection_due.isoformat()
                if data.annual_inspection_due
                else None
            ),
            "annual_inspection_vendor": data.annual_inspection_vendor,
            "annual_inspection_cert_url": data.annual_inspection_cert_url,
            "dot_inspection_date": (
                data.dot_inspection_date.isoformat()
                if data.dot_inspection_date
                else None
            ),
            "dot_inspection_due": (
                data.dot_inspection_due.isoformat()
                if data.dot_inspection_due
                else None
            ),
            "dot_number": data.dot_number,
            "last_maintenance_date": (
                data.last_maintenance_date.isoformat()
                if data.last_maintenance_date
                else None
            ),
            "next_maintenance_due": (
                data.next_maintenance_due.isoformat()
                if data.next_maintenance_due
                else None
            ),
            "maintenance_notes": data.maintenance_notes,
            "required_certifications": data.required_certifications,
            "notes": data.notes,
            "created_at": now,
            "updated_at": now,
            "deleted": False,
        }

        self._collection(company_id).document(equip_id).set(equip_dict)
        return Equipment(**equip_dict)

    def get(self, company_id: str, equipment_id: str) -> Equipment:
        """Fetch a single equipment record.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID to fetch.

        Returns:
            The Equipment model.

        Raises:
            EquipmentNotFoundError: If not found or soft-deleted.
        """
        doc = self._collection(company_id).document(equipment_id).get()
        if not doc.exists:
            raise EquipmentNotFoundError(equipment_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise EquipmentNotFoundError(equipment_id)

        return Equipment(**data)

    def list_equipment(
        self,
        company_id: str,
        equipment_type: EquipmentType | None = None,
        equipment_status: EquipmentStatus | None = None,
        project_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List equipment for a company with optional filters.

        Args:
            company_id: The owning company ID.
            equipment_type: Optional filter by equipment type.
            equipment_status: Optional filter by status.
            project_id: Optional filter by assigned project.
            limit: Maximum records to return.
            offset: Number of records to skip.

        Returns:
            A dict with 'equipment' list and 'total' count.
        """
        base_query: firestore.Query = self._collection(company_id).where(
            "deleted", "==", False
        )

        if equipment_type is not None:
            base_query = base_query.where(
                "equipment_type", "==", equipment_type.value
            )

        if equipment_status is not None:
            base_query = base_query.where("status", "==", equipment_status.value)

        if project_id is not None:
            base_query = base_query.where("current_project_id", "==", project_id)

        all_docs = [Equipment(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        all_docs.sort(key=lambda e: e.created_at, reverse=True)
        paginated = all_docs[offset : offset + limit]

        return {"equipment": paginated, "total": total}

    def update(
        self, company_id: str, equipment_id: str, data: EquipmentUpdate, user_id: str
    ) -> Equipment:
        """Update an existing equipment record.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Equipment model.

        Raises:
            EquipmentNotFoundError: If not found or soft-deleted.
        """
        doc_ref = self._collection(company_id).document(equipment_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise EquipmentNotFoundError(equipment_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name in ("equipment_type", "status", "inspection_frequency"):
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name in (
                "annual_inspection_date",
                "annual_inspection_due",
                "dot_inspection_date",
                "dot_inspection_due",
                "last_maintenance_date",
                "next_maintenance_due",
            ):
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            else:
                update_data[field_name] = value

        if not update_data:
            return Equipment(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)

        doc_ref.update(update_data)
        updated_doc = doc_ref.get()
        return Equipment(**updated_doc.to_dict())

    def delete(self, company_id: str, equipment_id: str) -> None:
        """Soft-delete an equipment record.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID to delete.

        Raises:
            EquipmentNotFoundError: If not found or already deleted.
        """
        doc_ref = self._collection(company_id).document(equipment_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise EquipmentNotFoundError(equipment_id)

        doc_ref.update(
            {
                "deleted": True,
                "status": EquipmentStatus.RETIRED.value,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    # -- Inspection Logs ---------------------------------------------------------------

    def create_inspection_log(
        self,
        company_id: str,
        equipment_id: str,
        data: EquipmentInspectionLogCreate,
        user_id: str,
    ) -> EquipmentInspectionLog:
        """Create an inspection log for an equipment item.

        Also updates the equipment's last_inspection_date. If the inspection
        fails and out_of_service is True, sets equipment status to OUT_OF_SERVICE.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID.
            data: Validated inspection log data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created EquipmentInspectionLog.

        Raises:
            EquipmentNotFoundError: If equipment not found or soft-deleted.
        """
        # Verify equipment exists
        equip_doc_ref = self._collection(company_id).document(equipment_id)
        equip_doc = equip_doc_ref.get()

        if not equip_doc.exists or equip_doc.to_dict().get("deleted", False):
            raise EquipmentNotFoundError(equipment_id)

        now = datetime.now(timezone.utc)
        log_id = self._generate_log_id()

        log_dict: dict[str, Any] = {
            "id": log_id,
            "company_id": company_id,
            "equipment_id": equipment_id,
            "project_id": data.project_id,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "inspection_type": data.inspection_type,
            "items": data.items,
            "overall_status": data.overall_status,
            "deficiencies_found": data.deficiencies_found,
            "corrective_action": data.corrective_action,
            "out_of_service": data.out_of_service,
            "created_at": now,
            "created_by": user_id,
        }

        self._inspection_logs_collection(company_id, equipment_id).document(
            log_id
        ).set(log_dict)

        # Update equipment's last inspection date
        equip_update: dict[str, Any] = {
            "last_inspection_date": data.inspection_date.isoformat(),
            "updated_at": now,
        }

        if data.out_of_service:
            equip_update["status"] = EquipmentStatus.OUT_OF_SERVICE.value

        equip_doc_ref.update(equip_update)

        return EquipmentInspectionLog(**log_dict)

    def list_inspection_logs(
        self,
        company_id: str,
        equipment_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List inspection logs for an equipment item.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID.
            limit: Maximum logs to return.
            offset: Number of logs to skip.

        Returns:
            A dict with 'logs' list and 'total' count.
        """
        all_docs = [
            EquipmentInspectionLog(**doc.to_dict())
            for doc in self._inspection_logs_collection(
                company_id, equipment_id
            ).stream()
        ]
        total = len(all_docs)

        all_docs.sort(key=lambda l: l.created_at, reverse=True)
        paginated = all_docs[offset : offset + limit]

        return {"logs": paginated, "total": total}

    # -- Fleet Queries -----------------------------------------------------------------

    def get_overdue_inspections(self, company_id: str) -> dict:
        """Get equipment with overdue inspections.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with 'equipment' list and 'total' count.
        """
        today = date.today()
        base_query = self._collection(company_id).where("deleted", "==", False)

        overdue = []
        for doc in base_query.stream():
            data = doc.to_dict()
            next_due = data.get("next_inspection_due")
            if next_due is None:
                continue
            if isinstance(next_due, str):
                next_due = date.fromisoformat(next_due)

            if next_due < today:
                days_overdue = (today - next_due).days
                overdue.append(
                    {
                        "equipment_id": data.get("id", ""),
                        "equipment_name": data.get("name", ""),
                        "equipment_type": data.get("equipment_type", "other"),
                        "next_inspection_due": next_due.isoformat()
                        if hasattr(next_due, "isoformat")
                        else next_due,
                        "days_overdue": days_overdue,
                    }
                )

        overdue.sort(key=lambda e: e.get("days_overdue", 0), reverse=True)
        return {"equipment": overdue, "total": len(overdue)}

    def get_equipment_by_project(self, company_id: str, project_id: str) -> dict:
        """Get all equipment assigned to a specific project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to filter by.

        Returns:
            A dict with 'equipment' list and 'total' count.
        """
        return self.list_equipment(company_id, project_id=project_id)

    def get_equipment_summary(self, company_id: str) -> dict:
        """Get a summary of the equipment fleet.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with total, by_type, by_status, overdue counts.
        """
        today = date.today()
        base_query = self._collection(company_id).where("deleted", "==", False)

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        overdue_inspections = 0
        overdue_maintenance = 0
        total = 0

        for doc in base_query.stream():
            data = doc.to_dict()
            total += 1

            etype = data.get("equipment_type", "other")
            by_type[etype] = by_type.get(etype, 0) + 1

            estatus = data.get("status", "active")
            by_status[estatus] = by_status.get(estatus, 0) + 1

            next_insp = data.get("next_inspection_due")
            if next_insp:
                if isinstance(next_insp, str):
                    next_insp = date.fromisoformat(next_insp)
                if next_insp < today:
                    overdue_inspections += 1

            next_maint = data.get("next_maintenance_due")
            if next_maint:
                if isinstance(next_maint, str):
                    next_maint = date.fromisoformat(next_maint)
                if next_maint < today:
                    overdue_maintenance += 1

        return {
            "total_equipment": total,
            "by_type": by_type,
            "by_status": by_status,
            "overdue_inspections": overdue_inspections,
            "overdue_maintenance": overdue_maintenance,
        }

    def get_dot_compliance_status(self, company_id: str) -> dict:
        """Get DOT compliance status for all vehicles.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with vehicles list and compliance counts.
        """
        today = date.today()
        base_query = self._collection(company_id).where("deleted", "==", False).where(
            "equipment_type", "==", EquipmentType.VEHICLE.value
        )

        vehicles = []
        compliant_count = 0
        overdue_count = 0
        missing_count = 0

        for doc in base_query.stream():
            data = doc.to_dict()

            dot_due = data.get("dot_inspection_due")
            dot_date = data.get("dot_inspection_date")

            if dot_due is None and dot_date is None:
                entry_status = "missing"
                missing_count += 1
            else:
                if dot_due and isinstance(dot_due, str):
                    dot_due = date.fromisoformat(dot_due)
                if dot_due and dot_due < today:
                    entry_status = "overdue"
                    overdue_count += 1
                else:
                    entry_status = "compliant"
                    compliant_count += 1

            vehicles.append(
                {
                    "equipment_id": data.get("id", ""),
                    "equipment_name": data.get("name", ""),
                    "dot_number": data.get("dot_number", ""),
                    "dot_inspection_date": data.get("dot_inspection_date"),
                    "dot_inspection_due": data.get("dot_inspection_due"),
                    "status": entry_status,
                }
            )

        return {
            "vehicles": vehicles,
            "total": len(vehicles),
            "compliant": compliant_count,
            "overdue": overdue_count,
            "missing": missing_count,
        }

    @staticmethod
    def get_inspection_template(equipment_type: str) -> list[dict[str, str]]:
        """Get the pre-built inspection checklist for an equipment type.

        Args:
            equipment_type: The equipment type string.

        Returns:
            A list of checklist item dicts with 'item' and 'category' keys.
        """
        return EQUIPMENT_INSPECTION_TEMPLATES.get(equipment_type, [])
