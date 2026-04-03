"""Document CRUD service against Firestore."""

import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, DocumentNotFoundError
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
)


class DocumentService:
    """Manages safety documents in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document."""
        return self.db.collection("companies").document(company_id)

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the documents subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("documents")

    def _generate_id(self) -> str:
        """Generate a unique document ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"doc_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    def create(self, company_id: str, data: DocumentCreate, user_id: str) -> Document:
        """Create a new draft document.

        Args:
            company_id: The owning company ID.
            data: Validated document creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Document with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        doc_id = self._generate_id()

        doc_dict = {
            "id": doc_id,
            "company_id": company_id,
            "title": data.title,
            "document_type": data.document_type.value,
            "status": DocumentStatus.DRAFT.value,
            "content": {},
            "project_info": data.project_info,
            "generated_at": None,
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "pdf_url": None,
            "deleted": False,
        }

        self._collection(company_id).document(doc_id).set(doc_dict)
        return Document(**doc_dict)

    def get(self, company_id: str, document_id: str) -> Document:
        """Fetch a single document.

        Args:
            company_id: The owning company ID.
            document_id: The document ID to fetch.

        Returns:
            The Document model.

        Raises:
            DocumentNotFoundError: If the document does not exist or is soft-deleted.
        """
        doc = self._collection(company_id).document(document_id).get()
        if not doc.exists:
            raise DocumentNotFoundError(document_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise DocumentNotFoundError(document_id)

        return Document(**data)

    def list_documents(
        self,
        company_id: str,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        limit: int = 20,
        offset: int = 0,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
    ) -> dict:
        """List documents for a company with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            document_type: Filter by document type.
            status: Filter by document status.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.
            sort_field: Field to sort by (default: created_at).
            sort_direction: Sort direction, 'asc' or 'desc' (default: desc).

        Returns:
            A dict with 'documents' list and 'total' count.
        """
        direction = (
            firestore.Query.DESCENDING
            if sort_direction == "desc"
            else firestore.Query.ASCENDING
        )

        base_query: firestore.Query = self._collection(company_id).where(
            "deleted", "==", False
        )

        if document_type is not None:
            base_query = base_query.where("document_type", "==", document_type.value)

        if status is not None:
            base_query = base_query.where("status", "==", status.value)

        # Count total matching documents
        all_docs = [Document(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        # Apply sorting, offset, and limit
        paginated_query = base_query.order_by(sort_field, direction=direction)
        paginated_query = paginated_query.offset(offset).limit(limit)

        documents = [Document(**doc.to_dict()) for doc in paginated_query.stream()]

        return {"documents": documents, "total": total}

    def update(
        self, company_id: str, document_id: str, data: DocumentUpdate, user_id: str
    ) -> Document:
        """Update an existing document.

        Args:
            company_id: The owning company ID.
            document_id: The document ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Document model.

        Raises:
            DocumentNotFoundError: If the document does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id).document(document_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise DocumentNotFoundError(document_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_data[field_name] = value.value if hasattr(value, "value") else value
            else:
                update_data[field_name] = value

        if not update_data:
            return Document(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Document(**updated_doc.to_dict())

    def set_generated_content(
        self,
        company_id: str,
        document_id: str,
        content: dict[str, Any],
        user_id: str,
    ) -> Document:
        """Set AI-generated content on a document.

        Args:
            company_id: The owning company ID.
            document_id: The document ID.
            content: Generated content sections as a dict.
            user_id: Firebase UID of the user who triggered generation.

        Returns:
            The updated Document model.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        doc_ref = self._collection(company_id).document(document_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise DocumentNotFoundError(document_id)

        now = datetime.now(timezone.utc)
        doc_ref.update(
            {
                "content": content,
                "generated_at": now,
                "updated_at": now,
                "updated_by": user_id,
            }
        )

        updated_doc = doc_ref.get()
        return Document(**updated_doc.to_dict())

    def delete(self, company_id: str, document_id: str) -> None:
        """Soft-delete a document by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            document_id: The document ID to delete.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        doc_ref = self._collection(company_id).document(document_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise DocumentNotFoundError(document_id)

        doc_ref.update(
            {
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def get_stats(self, company_id: str) -> dict:
        """Get document statistics for a company.

        Args:
            company_id: The company ID to get stats for.

        Returns:
            A dict with total, this_month, by_type, and by_status counts.
        """
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        all_docs = list(
            self._collection(company_id).where("deleted", "==", False).stream()
        )

        total = len(all_docs)
        this_month = 0
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for doc_snapshot in all_docs:
            data = doc_snapshot.to_dict()
            doc_type = data.get("document_type", "unknown")
            doc_status = data.get("status", "unknown")
            created_at = data.get("created_at")

            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            by_status[doc_status] = by_status.get(doc_status, 0) + 1

            if created_at is not None and created_at >= month_start:
                this_month += 1

        return {
            "total": total,
            "this_month": this_month,
            "by_type": by_type,
            "by_status": by_status,
        }

    def count_documents_this_month(self, company_id: str) -> int:
        """Count documents created by a company in the current calendar month.

        Args:
            company_id: The company ID to count for.

        Returns:
            The number of documents created this month.
        """
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = (
            self._collection(company_id)
            .where("created_at", ">=", month_start)
            .where("deleted", "==", False)
        )

        return sum(1 for _ in query.stream())
