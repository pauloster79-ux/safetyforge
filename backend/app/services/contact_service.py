"""Contact CRUD service (Neo4j-backed).

Contacts represent external individuals or organisations — clients, consultants,
subcontractors — associated with a company or project.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ContactNotFoundError(Exception):
    """Raised when a contact cannot be found."""

    def __init__(self, contact_id: str) -> None:
        self.contact_id = contact_id
        super().__init__(f"Contact not found: {contact_id}")


class ContactService(BaseService):
    """Manages Contact nodes in the Neo4j graph.

    Contacts connect to companies via (Company)-[:HAS_CONTACT]->(Contact).
    They may also be linked to projects as the client
    via (Project)-[:CLIENT_IS]->(Contact).
    """

    def create(
        self,
        company_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new contact for a company.

        Args:
            company_id: The owning company ID.
            data: Contact fields — name, email, phone, company_name, role_description.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created contact dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        cont_id = self._generate_id("cont")

        props: dict[str, Any] = {
            "id": cont_id,
            "name": data.get("name", ""),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "company_name": data.get("company_name"),
            "role_description": data.get("role_description"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (cont:Contact $props)
            CREATE (c)-[:HAS_CONTACT]->(cont)
            RETURN cont {.*, company_id: c.id} AS contact
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=cont_id,
            entity_type="Contact",
            company_id=company_id,
            actor=actor,
            summary=f"Created contact '{data.get('name', '')}'",
        )
        return result["contact"]

    def get(self, company_id: str, contact_id: str) -> dict[str, Any]:
        """Fetch a single contact.

        Args:
            company_id: The owning company ID.
            contact_id: The contact ID to fetch.

        Returns:
            The contact dict.

        Raises:
            ContactNotFoundError: If the contact does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONTACT]->(cont:Contact {id: $contact_id})
            WHERE cont.deleted = false
            RETURN cont {.*, company_id: c.id} AS contact
            """,
            {"company_id": company_id, "contact_id": contact_id},
        )
        if result is None:
            raise ContactNotFoundError(contact_id)
        return result["contact"]

    def list_by_company(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all contacts for a company.

        Args:
            company_id: The owning company ID.
            limit: Maximum number of contacts to return.
            offset: Number of contacts to skip.

        Returns:
            A dict with 'contacts' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONTACT]->(cont:Contact)
            WHERE cont.deleted = false
            RETURN count(cont) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONTACT]->(cont:Contact)
            WHERE cont.deleted = false
            RETURN cont {.*, company_id: c.id} AS contact
            ORDER BY cont.name ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"contacts": [r["contact"] for r in results], "total": total}

    def update(
        self,
        company_id: str,
        contact_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing contact.

        Args:
            company_id: The owning company ID.
            contact_id: The contact ID to update.
            data: Fields to update (only non-None values are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated contact dict.

        Raises:
            ContactNotFoundError: If the contact does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONTACT]->(cont:Contact {id: $contact_id})
            WHERE cont.deleted = false
            SET cont += $props
            RETURN cont {.*, company_id: c.id} AS contact
            """,
            {"company_id": company_id, "contact_id": contact_id, "props": update_fields},
        )
        if result is None:
            raise ContactNotFoundError(contact_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=contact_id,
            entity_type="Contact",
            company_id=company_id,
            actor=actor,
            summary=f"Updated contact {contact_id}",
        )
        return result["contact"]

    def archive(self, company_id: str, contact_id: str, user_id: str) -> None:
        """Soft-delete a contact.

        Args:
            company_id: The owning company ID.
            contact_id: The contact ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            ContactNotFoundError: If the contact does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CONTACT]->(cont:Contact {id: $contact_id})
            WHERE cont.deleted = false
            SET cont.deleted = true, cont.updated_at = $now
            RETURN cont.id AS id
            """,
            {
                "company_id": company_id,
                "contact_id": contact_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise ContactNotFoundError(contact_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=contact_id,
            entity_type="Contact",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived contact {contact_id}",
        )
