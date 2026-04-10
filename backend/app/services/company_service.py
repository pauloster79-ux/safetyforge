"""Company profile management service (Neo4j-backed)."""

from typing import Any

from app.exceptions import CompanyNotFoundError
from app.models.actor import Actor
from app.models.company import Company, CompanyCreate, CompanyUpdate, SubscriptionStatus
from app.services.base_service import BaseService


class CompanyService(BaseService):
    """Manages company profiles as Neo4j nodes.

    Company is the root organisational node. All other entities connect
    to the graph through relationship edges originating from Company.
    """

    def create(self, data: CompanyCreate, user_id: str) -> Company:
        """Create a new company node.

        Args:
            data: Validated company creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created Company with all fields populated.
        """
        actor = Actor.human(user_id)
        company_id = self._generate_id("comp")

        props: dict[str, Any] = {
            "id": company_id,
            "name": data.name,
            "address": data.address,
            "license_number": data.license_number,
            "trade_type": data.trade_type.value,
            "owner_name": data.owner_name,
            "phone": data.phone,
            "email": data.email,
            "ein": data.ein,
            "tax_id": data.tax_id,
            "tax_id_type": data.tax_id_type,
            "jurisdiction_code": data.jurisdiction_code,
            "jurisdiction_region": data.jurisdiction_region,
            "safety_officer": data.safety_officer,
            "safety_officer_phone": data.safety_officer_phone,
            "logo_url": data.logo_url,
            "subscription_status": SubscriptionStatus.FREE.value,
            "subscription_id": None,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            "CREATE (c:Company $props) RETURN c {.*} AS company",
            {"props": props},
        )
        return Company(**result["company"])

    def get(self, company_id: str) -> Company:
        """Fetch a company by ID.

        Args:
            company_id: The company node ID.

        Returns:
            The Company model.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c {.*} AS company",
            {"id": company_id},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        return Company(**result["company"])

    def get_by_user(self, user_id: str) -> Company | None:
        """Find a company owned by a user.

        Args:
            user_id: Clerk user ID to look up.

        Returns:
            The Company if found, None otherwise.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {created_by: $uid})
            RETURN c {.*} AS company
            LIMIT 1
            """,
            {"uid": user_id},
        )
        if result is None:
            return None
        return Company(**result["company"])

    def update(self, company_id: str, data: CompanyUpdate, user_id: str) -> Company:
        """Update an existing company profile.

        Args:
            company_id: The company node ID.
            data: Fields to update (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated Company model.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "trade_type" and value is not None:
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(user_id)
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $id})
            SET c += $props
            RETURN c {.*} AS company
            """,
            {"id": company_id, "props": update_fields},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        return Company(**result["company"])

    def update_subscription(
        self,
        company_id: str,
        status: SubscriptionStatus,
        subscription_id: str | None = None,
    ) -> None:
        """Update a company's subscription status.

        Args:
            company_id: The company node ID.
            status: New subscription status.
            subscription_id: Paddle subscription ID.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        props: dict[str, Any] = {
            "subscription_status": status.value,
        }
        if subscription_id is not None:
            props["subscription_id"] = subscription_id

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $id})
            SET c += $props
            RETURN c.id AS id
            """,
            {"id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

    def delete(self, company_id: str) -> None:
        """Delete a company and all its relationships.

        Args:
            company_id: The company node ID.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $id})
            RETURN c.id AS id
            """,
            {"id": company_id},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

        self._write_tx(
            "MATCH (c:Company {id: $id}) DETACH DELETE c",
            {"id": company_id},
        )
