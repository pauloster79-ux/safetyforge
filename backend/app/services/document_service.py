"""Document CRUD service against Neo4j."""

import json
from datetime import datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, DocumentNotFoundError
from app.models.actor import Actor
from app.models.document import (
    Document,
    DocumentCreate,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
)
from app.services.base_service import BaseService


class DocumentService(BaseService):
    """Manages safety documents in Neo4j.

    Graph model:
        (Company)-[:HAS_DOCUMENT]->(Document)
        content and project_info stored as _content_json and _project_info_json.
    """

    @staticmethod
    def _to_model(record: dict[str, Any]) -> Document:
        """Convert a Neo4j record dict to a Document model.

        Args:
            record: Dict with 'doc' and 'company_id' keys from Cypher.

        Returns:
            A Document model instance.
        """
        data = dict(record["doc"])
        content_json = data.pop("_content_json", "{}")
        data["content"] = json.loads(content_json) if content_json else {}
        project_info_json = data.pop("_project_info_json", "{}")
        data["project_info"] = json.loads(project_info_json) if project_info_json else {}
        data["company_id"] = record["company_id"]
        return Document(**data)

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.id AS id",
            {"id": company_id},
        )
        if result is None:
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

        actor = Actor.human(user_id)
        doc_id = self._generate_id("doc")

        props: dict[str, Any] = {
            "id": doc_id,
            "title": data.title,
            "document_type": data.document_type.value,
            "status": DocumentStatus.DRAFT.value,
            "_content_json": json.dumps({}),
            "_project_info_json": json.dumps(data.project_info),
            "generated_at": None,
            "pdf_url": None,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (d:Document $props)
            CREATE (c)-[:HAS_DOCUMENT]->(d)
            RETURN d {.*} AS doc, c.id AS company_id
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=doc_id,
            entity_type="Document",
            company_id=company_id,
            actor=actor,
            summary=f"Created document '{data.title}'",
        )
        return self._to_model(result)

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
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id})
            WHERE d.deleted = false
            RETURN d {.*} AS doc, c.id AS company_id
            """,
            {"company_id": company_id, "document_id": document_id},
        )
        if result is None:
            raise DocumentNotFoundError(document_id)
        return self._to_model(result)

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
        where_clauses = ["d.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if document_type is not None:
            where_clauses.append("d.document_type = $document_type")
            params["document_type"] = document_type.value

        if status is not None:
            where_clauses.append("d.status = $status")
            params["status"] = status.value

        where_str = " AND ".join(where_clauses)
        order_dir = "DESC" if sort_direction == "desc" else "ASC"
        allowed_sort_fields = {"created_at", "updated_at", "title", "document_type", "status"}
        if sort_field not in allowed_sort_fields:
            sort_field = "created_at"

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_DOCUMENT]->(d:Document)
            WHERE {where_str}
            RETURN count(d) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_DOCUMENT]->(d:Document)
            WHERE {where_str}
            RETURN d {{.*}} AS doc, c.id AS company_id
            ORDER BY d.{sort_field} {order_dir}
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        documents = [self._to_model(r) for r in results]
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
        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_data[field_name] = value.value if hasattr(value, "value") else value
            elif field_name == "content" and value is not None:
                update_data["_content_json"] = json.dumps(value)
            else:
                update_data[field_name] = value

        if not update_data:
            return self.get(company_id, document_id)

        actor = Actor.human(user_id)
        update_data.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id})
            WHERE d.deleted = false
            SET d += $props
            RETURN d {.*} AS doc, c.id AS company_id
            """,
            {"company_id": company_id, "document_id": document_id, "props": update_data},
        )
        if result is None:
            raise DocumentNotFoundError(document_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=document_id,
            entity_type="Document",
            company_id=company_id,
            actor=actor,
            summary=f"Updated document {document_id}",
        )
        return self._to_model(result)

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
        actor = Actor.human(user_id)
        now = datetime.now(timezone.utc).isoformat()

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id})
            WHERE d.deleted = false
            SET d._content_json = $content_json,
                d.generated_at = $now,
                d.updated_at = $now,
                d.updated_by = $user_id,
                d.updated_actor_type = $actor_type
            RETURN d {.*} AS doc, c.id AS company_id
            """,
            {
                "company_id": company_id,
                "document_id": document_id,
                "content_json": json.dumps(content),
                "now": now,
                "user_id": actor.id,
                "actor_type": actor.type,
            },
        )
        if result is None:
            raise DocumentNotFoundError(document_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=document_id,
            entity_type="Document",
            company_id=company_id,
            actor=actor,
            summary=f"Generated content for document {document_id}",
        )
        return self._to_model(result)

    def delete(self, company_id: str, document_id: str) -> None:
        """Soft-delete a document by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            document_id: The document ID to delete.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id})
            WHERE d.deleted = false
            SET d.deleted = true, d.updated_at = $now
            RETURN d.id AS id
            """,
            {
                "company_id": company_id,
                "document_id": document_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise DocumentNotFoundError(document_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=document_id,
            entity_type="Document",
            company_id=company_id,
            actor=Actor.human("system"),
            summary=f"Archived document {document_id}",
        )

    def get_stats(self, company_id: str) -> dict:
        """Get document statistics for a company.

        Args:
            company_id: The company ID to get stats for.

        Returns:
            A dict with total, this_month, by_type, and by_status counts.
        """
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        # Get all non-deleted docs with type and status
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false
            RETURN d.document_type AS doc_type, d.status AS doc_status,
                   d.created_at AS created_at
            """,
            {"company_id": company_id},
        )

        total = len(results)
        this_month = 0
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for r in results:
            doc_type = r.get("doc_type", "unknown")
            doc_status = r.get("doc_status", "unknown")
            created_at = r.get("created_at", "")

            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            by_status[doc_status] = by_status.get(doc_status, 0) + 1

            if created_at and created_at >= month_start:
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
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false AND d.created_at >= $month_start
            RETURN count(d) AS cnt
            """,
            {"company_id": company_id, "month_start": month_start},
        )
        return result["cnt"] if result else 0
