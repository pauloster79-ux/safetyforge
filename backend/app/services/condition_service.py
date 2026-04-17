"""Condition CRUD service (Neo4j-backed).

Conditions are contract prerequisites attached to a project's Contract.
Graph model: (Contract)-[:HAS_CONDITION]->(Condition)
Auto-creates a Contract node if the project doesn't have one yet.
"""

from typing import Any

from app.exceptions import ConditionNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ConditionService(BaseService):
    """Manages Condition nodes on project Contracts."""

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

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a condition on a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Condition fields.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created condition dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        actor = Actor.human(user_id)
        contract_id = self._ensure_contract(company_id, project_id, actor)
        cond_id = self._generate_id("cond")

        props: dict[str, Any] = {
            "id": cond_id,
            "category": data["category"],
            "description": data["description"],
            "responsible_party": data.get("responsible_party"),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            CREATE (cond:Condition $props)
            CREATE (ctr)-[:HAS_CONDITION]->(cond)
            RETURN cond {.*, contract_id: ctr.id} AS condition
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
            entity_id=cond_id,
            entity_type="Condition",
            company_id=company_id,
            actor=actor,
            summary=f"Created condition in category '{data['category']}'",
            related_entity_ids=[project_id, contract_id],
        )
        return result["condition"]

    def get(
        self, company_id: str, project_id: str, condition_id: str
    ) -> dict[str, Any]:
        """Fetch a single condition.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            condition_id: The condition ID.

        Returns:
            The condition dict.

        Raises:
            ConditionNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_CONDITION]->(cond:Condition {id: $condition_id})
            RETURN cond {.*, contract_id: ctr.id} AS condition
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "condition_id": condition_id,
            },
        )
        if result is None:
            raise ConditionNotFoundError(condition_id)
        return result["condition"]

    def list_by_contract(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """List conditions for a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            A dict with 'conditions' list and 'total' count.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_CONDITION]->(cond:Condition)
            RETURN cond {.*, contract_id: ctr.id} AS condition
            ORDER BY cond.category ASC, cond.created_at ASC
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        conditions = [r["condition"] for r in results]
        return {"conditions": conditions, "total": len(conditions)}

    def update(
        self,
        company_id: str,
        project_id: str,
        condition_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update a condition.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            condition_id: The condition ID.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID.

        Returns:
            The updated condition dict.

        Raises:
            ConditionNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_CONDITION]->(cond:Condition {id: $condition_id})
            SET cond += $props
            RETURN cond {.*, contract_id: ctr.id} AS condition
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "condition_id": condition_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ConditionNotFoundError(condition_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=condition_id,
            entity_type="Condition",
            company_id=company_id,
            actor=actor,
            summary=f"Updated condition {condition_id}",
        )
        return result["condition"]

    def delete(
        self, company_id: str, project_id: str, condition_id: str
    ) -> None:
        """Delete a condition (hard delete).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            condition_id: The condition ID.

        Raises:
            ConditionNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_CONDITION]->(cond:Condition {id: $condition_id})
            DETACH DELETE cond
            RETURN ctr.id AS contract_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "condition_id": condition_id,
            },
        )
        if result is None:
            raise ConditionNotFoundError(condition_id)
