"""Equipment and fleet management service (Neo4j-backed)."""

import json
from datetime import date, datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, EquipmentNotFoundError
from app.models.actor import Actor
from app.models.equipment import (
    Equipment,
    EquipmentCreate,
    EquipmentInspectionLog,
    EquipmentInspectionLogCreate,
    EquipmentStatus,
    EquipmentType,
    EquipmentUpdate,
)
from app.services.base_service import BaseService

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


class EquipmentService(BaseService):
    """Manages equipment and fleet records as Neo4j nodes.

    Equipment connects to companies via (Company)-[:OWNS_EQUIPMENT]->(Equipment).
    Inspection logs connect via (Equipment)-[:HAS_INSPECTION_LOG]->(EquipmentInspectionLog).
    """

    def _date_fields(self) -> list[str]:
        """Return list of date field names that need serialization."""
        return [
            "last_inspection_date", "next_inspection_due",
            "annual_inspection_date", "annual_inspection_due",
            "dot_inspection_date", "dot_inspection_due",
            "last_maintenance_date", "next_maintenance_due",
        ]

    def create(
        self, company_id: str, data: EquipmentCreate, user_id: str
    ) -> Equipment:
        """Create a new equipment record.

        Args:
            company_id: The owning company ID.
            data: Validated equipment creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created Equipment with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        equip_id = self._generate_id("eqp")

        props: dict[str, Any] = {
            "id": equip_id,
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
            "annual_inspection_date": data.annual_inspection_date.isoformat() if data.annual_inspection_date else None,
            "annual_inspection_due": data.annual_inspection_due.isoformat() if data.annual_inspection_due else None,
            "annual_inspection_vendor": data.annual_inspection_vendor,
            "annual_inspection_cert_url": data.annual_inspection_cert_url,
            "dot_inspection_date": data.dot_inspection_date.isoformat() if data.dot_inspection_date else None,
            "dot_inspection_due": data.dot_inspection_due.isoformat() if data.dot_inspection_due else None,
            "dot_number": data.dot_number,
            "last_maintenance_date": data.last_maintenance_date.isoformat() if data.last_maintenance_date else None,
            "next_maintenance_due": data.next_maintenance_due.isoformat() if data.next_maintenance_due else None,
            "maintenance_notes": data.maintenance_notes,
            "required_certifications": data.required_certifications,
            "notes": data.notes,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (e:Equipment $props)
            CREATE (c)-[:OWNS_EQUIPMENT]->(e)
            RETURN e {.*, company_id: c.id} AS equipment
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=equip_id,
            entity_type="Equipment",
            company_id=company_id,
            actor=actor,
            summary=f"Created equipment: {data.name}",
        )
        return Equipment(**result["equipment"])

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
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment {id: $id})
            WHERE e.deleted = false
            RETURN e {.*, company_id: c.id} AS equipment
            """,
            {"company_id": company_id, "id": equipment_id},
        )
        if result is None:
            raise EquipmentNotFoundError(equipment_id)
        return Equipment(**result["equipment"])

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
        where_clauses = ["e.deleted = false"]
        params: dict[str, Any] = {"company_id": company_id, "limit": limit, "offset": offset}

        if equipment_type is not None:
            where_clauses.append("e.equipment_type = $etype")
            params["etype"] = equipment_type.value
        if equipment_status is not None:
            where_clauses.append("e.status = $estatus")
            params["estatus"] = equipment_status.value
        if project_id is not None:
            where_clauses.append("e.current_project_id = $project_id")
            params["project_id"] = project_id

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_EQUIPMENT]->(e:Equipment)
            WHERE {where_str}
            RETURN count(e) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_EQUIPMENT]->(e:Equipment)
            WHERE {where_str}
            RETURN e {{.*, company_id: c.id}} AS equipment
            ORDER BY e.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        equipment = [Equipment(**r["equipment"]) for r in results]
        return {"equipment": equipment, "total": total}

    def update(
        self, company_id: str, equipment_id: str, data: EquipmentUpdate, user_id: str
    ) -> Equipment:
        """Update an existing equipment record.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated Equipment model.

        Raises:
            EquipmentNotFoundError: If not found or soft-deleted.
        """
        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name in ("equipment_type", "status", "inspection_frequency"):
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            elif field_name in self._date_fields():
                update_fields[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(user_id)
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment {id: $id})
            WHERE e.deleted = false
            SET e += $props
            RETURN e {.*, company_id: c.id} AS equipment
            """,
            {"company_id": company_id, "id": equipment_id, "props": update_fields},
        )
        if result is None:
            raise EquipmentNotFoundError(equipment_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=equipment_id,
            entity_type="Equipment",
            company_id=company_id,
            actor=actor,
            summary=f"Updated equipment {equipment_id}",
        )
        return Equipment(**result["equipment"])

    def delete(self, company_id: str, equipment_id: str) -> None:
        """Soft-delete an equipment record.

        Args:
            company_id: The owning company ID.
            equipment_id: The equipment ID to delete.

        Raises:
            EquipmentNotFoundError: If not found or already deleted.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment {id: $id})
            WHERE e.deleted = false
            SET e.deleted = true, e.status = $retired, e.updated_at = $now
            RETURN e.id AS id
            """,
            {
                "company_id": company_id,
                "id": equipment_id,
                "retired": EquipmentStatus.RETIRED.value,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise EquipmentNotFoundError(equipment_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=equipment_id,
            entity_type="Equipment",
            company_id=company_id,
            actor=Actor.human("system"),
            summary=f"Archived equipment {equipment_id}",
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
            user_id: Clerk user ID of the creating user.

        Returns:
            The created EquipmentInspectionLog.

        Raises:
            EquipmentNotFoundError: If equipment not found or soft-deleted.
        """
        actor = Actor.human(user_id)
        log_id = self._generate_id("eqlog")
        now = datetime.now(timezone.utc).isoformat()

        log_props: dict[str, Any] = {
            "id": log_id,
            "project_id": data.project_id,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "inspection_type": data.inspection_type,
            "_items_json": json.dumps(data.items),
            "overall_status": data.overall_status,
            "deficiencies_found": data.deficiencies_found,
            "corrective_action": data.corrective_action,
            "out_of_service": data.out_of_service,
            **self._provenance_create(actor),
        }

        equip_update = f", e.last_inspection_date = '{data.inspection_date.isoformat()}', e.updated_at = '{now}'"
        if data.out_of_service:
            equip_update += f", e.status = '{EquipmentStatus.OUT_OF_SERVICE.value}'"

        result = self._write_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_EQUIPMENT]->(e:Equipment {{id: $equipment_id}})
            WHERE e.deleted = false
            CREATE (log:EquipmentInspectionLog $log_props)
            CREATE (e)-[:HAS_INSPECTION_LOG]->(log)
            SET e.updated_at = $now{', e.status = $oos_status' if data.out_of_service else ''}
            , e.last_inspection_date = $insp_date
            RETURN log {{.*, company_id: c.id, equipment_id: e.id}} AS log_result
            """,
            {
                "company_id": company_id,
                "equipment_id": equipment_id,
                "log_props": log_props,
                "now": now,
                "insp_date": data.inspection_date.isoformat(),
                **({"oos_status": EquipmentStatus.OUT_OF_SERVICE.value} if data.out_of_service else {}),
            },
        )
        if result is None:
            raise EquipmentNotFoundError(equipment_id)

        log_data = result["log_result"]
        log_data["items"] = json.loads(log_data.pop("_items_json", "[]"))
        self._emit_audit(
            event_type="entity.created",
            entity_id=log_id,
            entity_type="EquipmentInspectionLog",
            company_id=company_id,
            actor=actor,
            summary=f"Created inspection log for equipment {equipment_id}",
            related_entity_ids=[equipment_id],
        )
        return EquipmentInspectionLog(**log_data)

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
        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment {id: $eid})
                  -[:HAS_INSPECTION_LOG]->(log:EquipmentInspectionLog)
            RETURN count(log) AS total
            """,
            {"company_id": company_id, "eid": equipment_id},
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment {id: $eid})
                  -[:HAS_INSPECTION_LOG]->(log:EquipmentInspectionLog)
            RETURN log {.*, company_id: c.id, equipment_id: e.id} AS log_result
            ORDER BY log.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            {"company_id": company_id, "eid": equipment_id, "offset": offset, "limit": limit},
        )

        logs = []
        for r in results:
            log_data = r["log_result"]
            log_data["items"] = json.loads(log_data.pop("_items_json", "[]"))
            logs.append(EquipmentInspectionLog(**log_data))

        return {"logs": logs, "total": total}

    # -- Fleet Queries -----------------------------------------------------------------

    def get_overdue_inspections(self, company_id: str) -> dict:
        """Get equipment with overdue inspections.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with 'equipment' list and 'total' count.
        """
        today_str = date.today().isoformat()

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment)
            WHERE e.deleted = false AND e.next_inspection_due IS NOT NULL
                  AND e.next_inspection_due < $today
            RETURN e.id AS equipment_id, e.name AS equipment_name,
                   e.equipment_type AS equipment_type,
                   e.next_inspection_due AS next_inspection_due
            ORDER BY e.next_inspection_due ASC
            """,
            {"company_id": company_id, "today": today_str},
        )

        today = date.today()
        overdue = []
        for r in results:
            next_due = r["next_inspection_due"]
            if isinstance(next_due, str):
                next_due = date.fromisoformat(next_due)
            days_overdue = (today - next_due).days
            overdue.append({
                "equipment_id": r["equipment_id"],
                "equipment_name": r["equipment_name"],
                "equipment_type": r["equipment_type"],
                "next_inspection_due": next_due.isoformat() if hasattr(next_due, "isoformat") else next_due,
                "days_overdue": days_overdue,
            })

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
        today_str = date.today().isoformat()

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment)
            WHERE e.deleted = false
            RETURN e.equipment_type AS etype, e.status AS estatus,
                   e.next_inspection_due AS next_insp,
                   e.next_maintenance_due AS next_maint
            """,
            {"company_id": company_id},
        )

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        overdue_inspections = 0
        overdue_maintenance = 0
        total = 0

        for r in results:
            total += 1
            etype = r.get("etype", "other")
            by_type[etype] = by_type.get(etype, 0) + 1

            estatus = r.get("estatus", "active")
            by_status[estatus] = by_status.get(estatus, 0) + 1

            next_insp = r.get("next_insp")
            if next_insp and str(next_insp) < today_str:
                overdue_inspections += 1

            next_maint = r.get("next_maint")
            if next_maint and str(next_maint) < today_str:
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

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_EQUIPMENT]->(e:Equipment)
            WHERE e.deleted = false AND e.equipment_type = $vehicle_type
            RETURN e.id AS id, e.name AS name, e.dot_number AS dot_number,
                   e.dot_inspection_date AS dot_date, e.dot_inspection_due AS dot_due
            """,
            {"company_id": company_id, "vehicle_type": EquipmentType.VEHICLE.value},
        )

        vehicles = []
        compliant_count = 0
        overdue_count = 0
        missing_count = 0

        for r in results:
            dot_due = r.get("dot_due")
            dot_date = r.get("dot_date")

            if dot_due is None and dot_date is None:
                entry_status = "missing"
                missing_count += 1
            else:
                if dot_due and isinstance(dot_due, str):
                    dot_due_parsed = date.fromisoformat(dot_due)
                else:
                    dot_due_parsed = dot_due
                if dot_due_parsed and dot_due_parsed < today:
                    entry_status = "overdue"
                    overdue_count += 1
                else:
                    entry_status = "compliant"
                    compliant_count += 1

            vehicles.append({
                "equipment_id": r["id"],
                "equipment_name": r["name"],
                "dot_number": r.get("dot_number", ""),
                "dot_inspection_date": r.get("dot_date"),
                "dot_inspection_due": r.get("dot_due"),
                "status": entry_status,
            })

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
