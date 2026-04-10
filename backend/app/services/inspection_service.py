"""Inspection CRUD service against Neo4j."""

import json
from datetime import date, datetime, timezone
from typing import Any

from app.exceptions import InspectionNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.inspection import (
    Inspection,
    InspectionCreate,
    InspectionItem,
    InspectionStatus,
    InspectionType,
    InspectionUpdate,
)
from app.services.base_service import BaseService


class InspectionService(BaseService):
    """Manages daily inspection logs in Neo4j.

    Graph model:
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_INSPECTION]->(Inspection)
        Items stored as _items_json (JSON string) on the Inspection node.
    """

    @staticmethod
    def calculate_overall_status(items: list[InspectionItem]) -> InspectionStatus:
        """Calculate the overall inspection status from checklist items.

        Rules:
        - If any item has status 'fail', overall is FAIL.
        - If all items are 'pass' or 'na', overall is PASS.
        - Otherwise, overall is PARTIAL.
        - If no items, default to PASS.

        Args:
            items: List of inspection checklist items.

        Returns:
            The calculated InspectionStatus.
        """
        if not items:
            return InspectionStatus.PASS

        statuses = [item.status for item in items]

        if any(s == "fail" for s in statuses):
            return InspectionStatus.FAIL

        if all(s in ("pass", "na") for s in statuses):
            return InspectionStatus.PASS

        return InspectionStatus.PARTIAL

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.id AS id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

    @staticmethod
    def _to_model(record: dict[str, Any]) -> Inspection:
        """Convert a Neo4j record dict to an Inspection model.

        Args:
            record: Dict with 'inspection' and 'company_id' keys from Cypher.

        Returns:
            An Inspection model instance.
        """
        data = record["inspection"]
        items_json = data.pop("_items_json", "[]")
        items = json.loads(items_json) if items_json else []
        data["items"] = items
        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return Inspection(**data)

    def create(
        self,
        company_id: str,
        project_id: str,
        data: InspectionCreate,
        user_id: str,
    ) -> Inspection:
        """Create a new inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated inspection creation data.
            user_id: UID of the creating user.

        Returns:
            The created Inspection with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        actor = Actor.human(user_id)
        insp_id = self._generate_id("insp")
        overall_status = self.calculate_overall_status(data.items)
        items_json = json.dumps([item.model_dump() for item in data.items])

        props: dict[str, Any] = {
            "id": insp_id,
            "inspection_type": data.inspection_type.value,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "inspector_id": data.inspector_id,
            "weather_conditions": data.weather_conditions,
            "temperature": data.temperature,
            "wind_conditions": data.wind_conditions,
            "workers_on_site": data.workers_on_site,
            "_items_json": items_json,
            "overall_notes": data.overall_notes,
            "corrective_actions_needed": data.corrective_actions_needed,
            "gps_latitude": data.gps_latitude,
            "gps_longitude": data.gps_longitude,
            "overall_status": overall_status.value,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (i:Inspection $props)
            CREATE (p)-[:HAS_INSPECTION]->(i)
            RETURN i {.*} AS inspection, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        return self._to_model(result)

    def get(
        self, company_id: str, project_id: str, inspection_id: str
    ) -> Inspection:
        """Fetch a single inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to fetch.

        Returns:
            The Inspection model.

        Raises:
            InspectionNotFoundError: If the inspection does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INSPECTION]->(i:Inspection {id: $inspection_id})
            WHERE i.deleted = false
            RETURN i {.*} AS inspection, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "inspection_id": inspection_id,
            },
        )
        if result is None:
            raise InspectionNotFoundError(inspection_id)
        return self._to_model(result)

    def list_inspections(
        self,
        company_id: str,
        project_id: str,
        inspection_type: InspectionType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List inspections for a project with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_type: Filter by inspection type.
            date_from: Filter inspections on or after this date.
            date_to: Filter inspections on or before this date.
            limit: Maximum number of inspections to return.
            offset: Number of inspections to skip.

        Returns:
            A dict with 'inspections' list and 'total' count.
        """
        where_clauses = ["i.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if inspection_type is not None:
            where_clauses.append("i.inspection_type = $inspection_type")
            params["inspection_type"] = inspection_type.value

        if date_from is not None:
            where_clauses.append("i.inspection_date >= $date_from")
            params["date_from"] = date_from.isoformat()

        if date_to is not None:
            where_clauses.append("i.inspection_date <= $date_to")
            params["date_to"] = date_to.isoformat()

        where_str = " AND ".join(where_clauses)

        # Count query
        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_INSPECTION]->(i:Inspection)
            WHERE {where_str}
            RETURN count(i) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        # Data query
        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_INSPECTION]->(i:Inspection)
            WHERE {where_str}
            RETURN i {{.*}} AS inspection, c.id AS company_id, p.id AS project_id
            ORDER BY i.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        inspections = [self._to_model(r) for r in results]
        return {"inspections": inspections, "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        inspection_id: str,
        data: InspectionUpdate,
        user_id: str,
    ) -> Inspection:
        """Update an existing inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: UID of the updating user.

        Returns:
            The updated Inspection model.

        Raises:
            InspectionNotFoundError: If the inspection does not exist or is soft-deleted.
        """
        # Build update props from non-None fields
        update_props: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "inspection_type" and value is not None:
                update_props[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name == "inspection_date" and value is not None:
                update_props[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            elif field_name == "items" and value is not None:
                items = [
                    InspectionItem(**item) if isinstance(item, dict) else item
                    for item in value
                ]
                update_props["_items_json"] = json.dumps(
                    [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
                )
                update_props["overall_status"] = self.calculate_overall_status(items).value
            else:
                update_props[field_name] = value

        if not update_props:
            return self.get(company_id, project_id, inspection_id)

        actor = Actor.human(user_id)
        update_props.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INSPECTION]->(i:Inspection {id: $inspection_id})
            WHERE i.deleted = false
            SET i += $props
            RETURN i {.*} AS inspection, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "inspection_id": inspection_id,
                "props": update_props,
            },
        )
        if result is None:
            raise InspectionNotFoundError(inspection_id)
        return self._to_model(result)

    def delete(
        self, company_id: str, project_id: str, inspection_id: str
    ) -> None:
        """Soft-delete an inspection by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to delete.

        Raises:
            InspectionNotFoundError: If the inspection does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INSPECTION]->(i:Inspection {id: $inspection_id})
            WHERE i.deleted = false
            SET i.deleted = true, i.updated_at = $now
            RETURN i.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "inspection_id": inspection_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise InspectionNotFoundError(inspection_id)
