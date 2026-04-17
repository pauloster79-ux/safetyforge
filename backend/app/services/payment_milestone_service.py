"""PaymentMilestone CRUD service (Neo4j-backed).

PaymentMilestones define the payment schedule on a project's Contract.
Graph model: (Contract)-[:HAS_PAYMENT_MILESTONE]->(PaymentMilestone)
Auto-creates a Contract node if the project doesn't have one yet.
"""

from typing import Any

from app.exceptions import PaymentMilestoneNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class PaymentMilestoneService(BaseService):
    """Manages PaymentMilestone nodes on project Contracts."""

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
        # If the above returned None, either the project doesn't exist
        # or the contract already existed. Check which case.
        if result is not None:
            return result["contract_id"]

        # Contract already existed — fetch its ID
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
        """Create a payment milestone on a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: PaymentMilestone fields.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created payment milestone dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        actor = Actor.human(user_id)
        contract_id = self._ensure_contract(company_id, project_id, actor)
        pms_id = self._generate_id("pms")

        props: dict[str, Any] = {
            "id": pms_id,
            "description": data["description"],
            "percentage": data.get("percentage"),
            "fixed_amount_cents": data.get("fixed_amount_cents"),
            "trigger_condition": data["trigger_condition"],
            "sort_order": data.get("sort_order", 0),
            "status": "pending",
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            CREATE (pm:PaymentMilestone $props)
            CREATE (ctr)-[:HAS_PAYMENT_MILESTONE]->(pm)
            RETURN pm {.*, contract_id: ctr.id} AS milestone
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
            entity_id=pms_id,
            entity_type="PaymentMilestone",
            company_id=company_id,
            actor=actor,
            summary=f"Created payment milestone '{data['description']}'",
            related_entity_ids=[project_id, contract_id],
        )
        return result["milestone"]

    def get(
        self, company_id: str, project_id: str, milestone_id: str
    ) -> dict[str, Any]:
        """Fetch a single payment milestone.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The payment milestone ID.

        Returns:
            The payment milestone dict.

        Raises:
            PaymentMilestoneNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone {id: $milestone_id})
            RETURN pm {.*, contract_id: ctr.id} AS milestone
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
            },
        )
        if result is None:
            raise PaymentMilestoneNotFoundError(milestone_id)
        return result["milestone"]

    def list_by_contract(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """List payment milestones for a project's contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.

        Returns:
            A dict with 'milestones' list and 'total' count.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone)
            RETURN pm {.*, contract_id: ctr.id} AS milestone
            ORDER BY pm.sort_order ASC, pm.created_at ASC
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        milestones = [r["milestone"] for r in results]
        return {"milestones": milestones, "total": len(milestones)}

    def update(
        self,
        company_id: str,
        project_id: str,
        milestone_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update a payment milestone.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The payment milestone ID.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID.

        Returns:
            The updated payment milestone dict.

        Raises:
            PaymentMilestoneNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone {id: $milestone_id})
            SET pm += $props
            RETURN pm {.*, contract_id: ctr.id} AS milestone
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise PaymentMilestoneNotFoundError(milestone_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=milestone_id,
            entity_type="PaymentMilestone",
            company_id=company_id,
            actor=actor,
            summary=f"Updated payment milestone {milestone_id}",
        )
        return result["milestone"]

    def delete(
        self, company_id: str, project_id: str, milestone_id: str
    ) -> None:
        """Delete a payment milestone (hard delete).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The payment milestone ID.

        Raises:
            PaymentMilestoneNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)-[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone {id: $milestone_id})
            DETACH DELETE pm
            RETURN ctr.id AS contract_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
            },
        )
        if result is None:
            raise PaymentMilestoneNotFoundError(milestone_id)
