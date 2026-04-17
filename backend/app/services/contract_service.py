"""Contract CRUD service (Neo4j-backed).

Contracts represent formal agreements on a project, capturing value,
payment terms, and status lifecycle.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ContractNotFoundError(Exception):
    """Raised when a contract cannot be found."""

    def __init__(self, contract_id: str) -> None:
        self.contract_id = contract_id
        super().__init__(f"Contract not found: {contract_id}")


class ContractService(BaseService):
    """Manages Contract nodes in the Neo4j graph.

    Contracts connect to projects via (Project)-[:HAS_CONTRACT]->(Contract).
    """

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new contract on a project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Contract fields — status, value, currency, retention_pct,
                payment_terms, payment_schedule, scope_description,
                start_date, end_date.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created contract dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
        """
        actor = Actor.human(user_id)
        ctr_id = self._generate_id("ctr")

        props: dict[str, Any] = {
            "id": ctr_id,
            "status": data.get("status", "draft"),
            "value": data.get("value"),
            "currency": data.get("currency", "USD"),
            "retention_pct": data.get("retention_pct", 0),
            "payment_terms": data.get("payment_terms"),
            "payment_schedule": data.get("payment_schedule"),
            "scope_description": data.get("scope_description"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (ctr:Contract $props)
            CREATE (p)-[:HAS_CONTRACT]->(ctr)
            RETURN ctr {.*, project_id: p.id, company_id: c.id} AS contract
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=ctr_id,
            entity_type="Contract",
            company_id=company_id,
            actor=actor,
            summary=f"Created contract on project {project_id}",
            related_entity_ids=[project_id],
        )
        return result["contract"]

    def get(
        self, company_id: str, project_id: str, contract_id: str
    ) -> dict[str, Any]:
        """Fetch a single contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            contract_id: The contract ID to fetch.

        Returns:
            The contract dict.

        Raises:
            ContractNotFoundError: If the contract does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            WHERE ctr.deleted = false
            RETURN ctr {.*, project_id: p.id, company_id: c.id} AS contract
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
            },
        )
        if result is None:
            raise ContractNotFoundError(contract_id)
        return result["contract"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List contracts for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of contracts to return.
            offset: Number of contracts to skip.

        Returns:
            A dict with 'contracts' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
            WHERE ctr.deleted = false
            RETURN count(ctr) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
            WHERE ctr.deleted = false
            RETURN ctr {.*, project_id: p.id, company_id: c.id} AS contract
            ORDER BY ctr.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"contracts": [r["contract"] for r in results], "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        contract_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            contract_id: The contract ID to update.
            data: Fields to update (only non-None values are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated contract dict.

        Raises:
            ContractNotFoundError: If the contract does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            WHERE ctr.deleted = false
            SET ctr += $props
            RETURN ctr {.*, project_id: p.id, company_id: c.id} AS contract
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ContractNotFoundError(contract_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=contract_id,
            entity_type="Contract",
            company_id=company_id,
            actor=actor,
            summary=f"Updated contract {contract_id}",
        )
        return result["contract"]

    def archive(
        self,
        company_id: str,
        project_id: str,
        contract_id: str,
        user_id: str,
    ) -> None:
        """Soft-delete a contract.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            contract_id: The contract ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            ContractNotFoundError: If the contract does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            WHERE ctr.deleted = false
            SET ctr.deleted = true, ctr.updated_at = $now
            RETURN ctr.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise ContractNotFoundError(contract_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=contract_id,
            entity_type="Contract",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived contract {contract_id}",
        )
