"""Company profile management service."""

import secrets
from datetime import datetime, timezone

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError
from app.models.company import Company, CompanyCreate, CompanyUpdate, SubscriptionStatus


class CompanyService:
    """Manages company profiles in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _collection(self) -> firestore.CollectionReference:
        """Return the companies collection reference."""
        return self.db.collection("companies")

    def _generate_id(self) -> str:
        """Generate a unique company ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"comp_{secrets.token_hex(8)}"

    def create(self, data: CompanyCreate, user_id: str) -> Company:
        """Create a new company profile.

        Args:
            data: Validated company creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Company with all fields populated.
        """
        now = datetime.now(timezone.utc)
        company_id = self._generate_id()

        company_dict = {
            "id": company_id,
            "name": data.name,
            "address": data.address,
            "license_number": data.license_number,
            "trade_type": data.trade_type.value,
            "owner_name": data.owner_name,
            "phone": data.phone,
            "email": data.email,
            "ein": data.ein,
            "safety_officer": data.safety_officer,
            "safety_officer_phone": data.safety_officer_phone,
            "logo_url": data.logo_url,
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "subscription_status": SubscriptionStatus.FREE.value,
            "subscription_id": None,
        }

        self._collection().document(company_id).set(company_dict)
        return Company(**company_dict)

    def get(self, company_id: str) -> Company:
        """Fetch a company by ID.

        Args:
            company_id: The company document ID.

        Returns:
            The Company model.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        doc = self._collection().document(company_id).get()
        if not doc.exists:
            raise CompanyNotFoundError(company_id)
        return Company(**doc.to_dict())

    def get_by_user(self, user_id: str) -> Company | None:
        """Find a company associated with a user.

        Args:
            user_id: Firebase UID to look up.

        Returns:
            The Company if found, None otherwise.
        """
        query = self._collection().where("created_by", "==", user_id).limit(1)
        docs = list(query.stream())
        if not docs:
            return None
        return Company(**docs[0].to_dict())

    def update(self, company_id: str, data: CompanyUpdate, user_id: str) -> Company:
        """Update an existing company profile.

        Args:
            company_id: The company document ID.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Company model.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        doc_ref = self._collection().document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise CompanyNotFoundError(company_id)

        update_data: dict = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "trade_type" and value is not None:
                update_data[field_name] = value.value if hasattr(value, "value") else value
            else:
                update_data[field_name] = value

        if not update_data:
            return Company(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Company(**updated_doc.to_dict())

    def update_subscription(
        self,
        company_id: str,
        status: SubscriptionStatus,
        subscription_id: str | None = None,
    ) -> None:
        """Update a company's subscription status.

        Args:
            company_id: The company document ID.
            status: New subscription status.
            subscription_id: Paddle subscription ID.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        doc_ref = self._collection().document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise CompanyNotFoundError(company_id)

        update_data: dict = {
            "subscription_status": status.value,
            "updated_at": datetime.now(timezone.utc),
        }
        if subscription_id is not None:
            update_data["subscription_id"] = subscription_id

        doc_ref.update(update_data)

    def delete(self, company_id: str) -> None:
        """Delete a company profile.

        Args:
            company_id: The company document ID.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        doc_ref = self._collection().document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise CompanyNotFoundError(company_id)
        doc_ref.delete()
