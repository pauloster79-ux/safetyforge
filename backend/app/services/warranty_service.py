"""Warranty CRUD service (Neo4j-backed).

One warranty per contract. set_warranty does an upsert (deletes existing, creates new).
Graph model: (Contract)-[:HAS_WARRANTY]->(Warranty)
Auto-creates a Contract node if the project doesn't have one yet.
"""

from typing import Any

from app.exceptions import ProjectNotFoundError, WarrantyNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class WarrantyService(BaseService):
    """Manages the single Warranty node on a project's Contract."""

    def _ensure_contract(
        self, company_id: str, project_id: str, actor: Actor
    ) -> str:
        """Ensure a Contract node exists for the project, creating one if needed.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            actor: The actor performing the operation.

        Returns:
            The contract ID.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            WITH p
            OPTIONAL MATCH (p)-[:HAS_CONTRACT]->(existing:Contract)
            WITH p, existing
            WHERE existing IS NULL
            CREATE (ctr:Contract {
                id: $contract_id,
                status: 'draft',
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_CONTRACT]->(ctr)
            RETURN ctr.id AS contract_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": self._generate_id("ctr"),
                **self._provenance_create(actor),
            },
        )
        if result is not None:
            return result["contract_id"]

        existing = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
            RETURN ctr.id AS contract_id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if existing is None:
            raise ProjectNotFoundError(project_id)
        return existing["contract_id"]

    def set_warranty(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Upsert a warranty on a project's contract (one warranty per contract).

        Deletes any existing warranty and creates a new one.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Warranty fields.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created warranty dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        actor = Actor.human(user_id)
        contract_id = self._ensure_contract(company_id, project_id, actor)
        wrty_id = self._generate_id("wrty")

        props: dict[str, Any] = {
            "id": wrty_id,
            "period_months": data["period_months"],
            "scope": data["scope"],
            "start_trigger": data.get("start_trigger", "practical_completion"),
            "terms": data.get("terms"),
            "start_date": None,
            "end_date": None,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            OPTIONAL MATCH (ctr)-[:HAS_WARRANTY]->(old:Warranty)
            WITH ctr, old
            FOREACH (_ IN CASE WHEN old IS NOT NULL THEN [1] ELSE [] END |
                DETACH DELETE old
            )
            WITH ctr
            CREATE (w:Warranty $props)
            CREATE (ctr)-[:HAS_WARRANTY]->(w)
            RETURN w {.*, contract_id: ctr.id} AS warranty
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "props": props,
            },
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=wrty_id,
            entity_type="Warranty",
            company_id=company_id,
            actor=actor,
            summary=f"Set warranty: {data['period_months']} months, trigger={data.get('start_trigger', 'practical_completion')}",
            related_entity_ids=[project_id, contract_id],
        )
        return result["warranty"]

    def get_by_contract(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Fetch the warranty for a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            The warranty dict.

        Raises:
            WarrantyNotFoundError: If no warranty exists.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_WARRANTY]->(w:Warranty)
            RETURN w {.*, contract_id: ctr.id} AS warranty
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise WarrantyNotFoundError(project_id)
        return result["warranty"]

    def delete(
        self, company_id: str, project_id: str
    ) -> None:
        """Delete the warranty on a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Raises:
            WarrantyNotFoundError: If no warranty exists.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_WARRANTY]->(w:Warranty)
            DETACH DELETE w
            RETURN ctr.id AS contract_id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise WarrantyNotFoundError(project_id)
