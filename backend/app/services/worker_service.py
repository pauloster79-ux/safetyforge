"""Worker CRUD service with certification management (Neo4j-backed)."""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, WorkerNotFoundError
from app.models.actor import Actor
from app.models.worker import (
    Certification,
    CertificationCreate,
    CertificationType,
    CertificationUpdate,
    Worker,
    WorkerCreate,
    WorkerStatus,
    WorkerUpdate,
)
from app.services.base_service import BaseService


class WorkerService(BaseService):
    """Manages worker profiles and certifications as Neo4j nodes.

    Workers connect to companies via (Company)-[:EMPLOYS]->(Worker).
    Certifications are stored as a JSON string on the Worker node
    (Neo4j does not support lists of maps as properties).
    """

    @staticmethod
    def _compute_cert_status(expiry_date: date | None) -> str:
        """Compute the status of a certification based on its expiry date.

        Args:
            expiry_date: The certification expiry date, or None if it never expires.

        Returns:
            One of 'valid', 'expired', or 'expiring_soon'.
        """
        if expiry_date is None:
            return "valid"
        today = date.today()
        if expiry_date < today:
            return "expired"
        if expiry_date < today + timedelta(days=30):
            return "expiring_soon"
        return "valid"

    @staticmethod
    def _serialize_certs(certs: list[dict[str, Any]]) -> str:
        """Serialize certifications list to JSON for Neo4j storage.

        Args:
            certs: List of certification dicts.

        Returns:
            JSON string.
        """
        return json.dumps(certs)

    @staticmethod
    def _deserialize_certs(raw: str | None) -> list[dict[str, Any]]:
        """Deserialize certifications JSON from Neo4j.

        Args:
            raw: JSON string from the node, or None.

        Returns:
            List of certification dicts.
        """
        if not raw:
            return []
        return json.loads(raw)

    def _compute_worker_fields(self, worker_dict: dict[str, Any]) -> dict[str, Any]:
        """Compute certification statuses and summary fields on a worker dict.

        Args:
            worker_dict: The raw worker dict from Neo4j.

        Returns:
            The worker dict with computed fields populated.
        """
        raw_certs = worker_dict.pop("_certifications_json", None)
        certs = self._deserialize_certs(raw_certs)

        expired_count = 0
        expiring_soon_count = 0

        for cert in certs:
            expiry = cert.get("expiry_date")
            if isinstance(expiry, str):
                expiry = date.fromisoformat(expiry)
            cert_status = self._compute_cert_status(expiry)
            cert["status"] = cert_status
            if cert_status == "expired":
                expired_count += 1
            elif cert_status == "expiring_soon":
                expiring_soon_count += 1

        worker_dict["certifications"] = certs
        worker_dict["total_certifications"] = len(certs)
        worker_dict["expiring_soon"] = expiring_soon_count
        worker_dict["expired"] = expired_count
        return worker_dict

    def _serialize_cert_dates(self, cert: dict[str, Any]) -> dict[str, Any]:
        """Serialize certification date fields to ISO strings.

        Args:
            cert: Certification dict.

        Returns:
            Certification dict with date fields as ISO strings.
        """
        result = dict(cert)
        for field in ("issued_date", "expiry_date"):
            if result.get(field) and hasattr(result[field], "isoformat"):
                result[field] = result[field].isoformat()
        return result

    def create(self, company_id: str, data: WorkerCreate, user_id: str) -> Worker:
        """Create a new worker.

        Args:
            company_id: The owning company ID.
            data: Validated worker creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created Worker with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        worker_id = self._generate_id("wkr")

        props: dict[str, Any] = {
            "id": worker_id,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email": data.email,
            "phone": data.phone,
            "role": data.role,
            "trade": data.trade,
            "language_preference": data.language_preference,
            "emergency_contact_name": data.emergency_contact_name,
            "emergency_contact_phone": data.emergency_contact_phone,
            "hire_date": data.hire_date.isoformat() if data.hire_date else None,
            "notes": data.notes,
            "status": WorkerStatus.ACTIVE.value,
            "_certifications_json": "[]",
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (w:Worker $props)
            CREATE (c)-[:EMPLOYS]->(w)
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

        worker_data = self._compute_worker_fields(result["worker"])
        return Worker(**worker_data)

    def get(self, company_id: str, worker_id: str) -> Worker:
        """Fetch a single worker with computed certification statuses.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID to fetch.

        Returns:
            The Worker model with computed fields.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {"company_id": company_id, "worker_id": worker_id},
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

        worker_data = self._compute_worker_fields(result["worker"])
        return Worker(**worker_data)

    def list_workers(
        self,
        company_id: str,
        status: WorkerStatus | None = None,
        role: str | None = None,
        trade: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List workers for a company with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            status: Filter by worker status.
            role: Filter by role.
            trade: Filter by trade.
            search: Search by first or last name (case-insensitive contains).
            limit: Maximum number of workers to return.
            offset: Number of workers to skip.

        Returns:
            A dict with 'workers' list and 'total' count.
        """
        where_clauses = ["w.deleted = false"]
        params: dict[str, Any] = {"company_id": company_id, "limit": limit, "offset": offset}

        if status is not None:
            where_clauses.append("w.status = $status")
            params["status"] = status.value
        if role is not None:
            where_clauses.append("w.role = $role")
            params["role"] = role
        if trade is not None:
            where_clauses.append("w.trade = $trade")
            params["trade"] = trade
        if search:
            where_clauses.append(
                "(toLower(w.first_name) CONTAINS $search OR toLower(w.last_name) CONTAINS $search)"
            )
            params["search"] = search.lower()

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:EMPLOYS]->(w:Worker)
            WHERE {where_str}
            RETURN count(w) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:EMPLOYS]->(w:Worker)
            WHERE {where_str}
            RETURN w {{.*, company_id: c.id}} AS worker
            ORDER BY w.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        workers = [Worker(**self._compute_worker_fields(r["worker"])) for r in results]
        return {"workers": workers, "total": total}

    def update(
        self, company_id: str, worker_id: str, data: WorkerUpdate, user_id: str
    ) -> Worker:
        """Update an existing worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated Worker model.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
        """
        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            elif field_name == "hire_date" and value is not None:
                update_fields[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(user_id)
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            SET w += $props
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {"company_id": company_id, "worker_id": worker_id, "props": update_fields},
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

        worker_data = self._compute_worker_fields(result["worker"])
        return Worker(**worker_data)

    def delete(self, company_id: str, worker_id: str) -> None:
        """Soft-delete a worker by setting status to terminated and deleted flag.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID to delete.

        Raises:
            WorkerNotFoundError: If the worker does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            SET w.status = $terminated, w.deleted = true, w.updated_at = $now
            RETURN w.id AS id
            """,
            {
                "company_id": company_id,
                "worker_id": worker_id,
                "terminated": WorkerStatus.TERMINATED.value,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

    def add_certification(
        self, company_id: str, worker_id: str, cert_data: CertificationCreate
    ) -> Worker:
        """Add a certification to a worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID.
            cert_data: Validated certification creation data.

        Returns:
            The updated Worker with the new certification.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            RETURN w._certifications_json AS certs_json
            """,
            {"company_id": company_id, "worker_id": worker_id},
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

        certs = self._deserialize_certs(result["certs_json"])

        cert_id = self._generate_id("cert")
        cert_dict: dict[str, Any] = {
            "id": cert_id,
            "certification_type": cert_data.certification_type.value,
            "custom_name": cert_data.custom_name,
            "issued_date": cert_data.issued_date.isoformat(),
            "expiry_date": cert_data.expiry_date.isoformat() if cert_data.expiry_date else None,
            "issuing_body": cert_data.issuing_body,
            "certificate_number": cert_data.certificate_number,
            "proof_document_url": None,
            "status": self._compute_cert_status(cert_data.expiry_date),
            "notes": cert_data.notes,
        }
        certs.append(cert_dict)

        updated = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            SET w._certifications_json = $certs_json, w.updated_at = $now
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {
                "company_id": company_id,
                "worker_id": worker_id,
                "certs_json": self._serialize_certs(certs),
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        worker_data = self._compute_worker_fields(updated["worker"])
        return Worker(**worker_data)

    def update_certification(
        self,
        company_id: str,
        worker_id: str,
        cert_id: str,
        cert_data: CertificationUpdate,
    ) -> Worker:
        """Update a certification on a worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID.
            cert_id: The certification ID to update.
            cert_data: Fields to update.

        Returns:
            The updated Worker.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
            ValueError: If the certification ID is not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            RETURN w._certifications_json AS certs_json
            """,
            {"company_id": company_id, "worker_id": worker_id},
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

        certs = self._deserialize_certs(result["certs_json"])

        cert_found = False
        for cert in certs:
            if cert["id"] == cert_id:
                cert_found = True
                for field_name, value in cert_data.model_dump(exclude_none=True).items():
                    if field_name == "certification_type" and value is not None:
                        cert[field_name] = value.value if hasattr(value, "value") else value
                    elif field_name in ("issued_date", "expiry_date") and value is not None:
                        cert[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
                    else:
                        cert[field_name] = value
                break

        if not cert_found:
            raise ValueError(f"Certification not found: {cert_id}")

        updated = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            SET w._certifications_json = $certs_json, w.updated_at = $now
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {
                "company_id": company_id,
                "worker_id": worker_id,
                "certs_json": self._serialize_certs(certs),
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        worker_data = self._compute_worker_fields(updated["worker"])
        return Worker(**worker_data)

    def remove_certification(
        self, company_id: str, worker_id: str, cert_id: str
    ) -> Worker:
        """Remove a certification from a worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID.
            cert_id: The certification ID to remove.

        Returns:
            The updated Worker.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
            ValueError: If the certification ID is not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            RETURN w._certifications_json AS certs_json
            """,
            {"company_id": company_id, "worker_id": worker_id},
        )
        if result is None:
            raise WorkerNotFoundError(worker_id)

        certs = self._deserialize_certs(result["certs_json"])
        new_certs = [c for c in certs if c["id"] != cert_id]

        if len(new_certs) == len(certs):
            raise ValueError(f"Certification not found: {cert_id}")

        updated = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            SET w._certifications_json = $certs_json, w.updated_at = $now
            RETURN w {.*, company_id: c.id} AS worker
            """,
            {
                "company_id": company_id,
                "worker_id": worker_id,
                "certs_json": self._serialize_certs(new_certs),
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        worker_data = self._compute_worker_fields(updated["worker"])
        return Worker(**worker_data)

    def get_expiring_certifications(
        self, company_id: str, days_ahead: int = 30
    ) -> dict:
        """Get all certifications expiring within N days across all workers.

        Args:
            company_id: The owning company ID.
            days_ahead: Number of days to look ahead for expiring certs.

        Returns:
            A dict with 'certifications' list and 'total' count.
        """
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        results_raw = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker)
            WHERE w.deleted = false
            RETURN w.id AS worker_id,
                   w.first_name AS first_name,
                   w.last_name AS last_name,
                   w._certifications_json AS certs_json
            """,
            {"company_id": company_id},
        )

        cert_results = []
        for row in results_raw:
            worker_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            worker_id = row["worker_id"]
            certs = self._deserialize_certs(row["certs_json"])

            for cert in certs:
                expiry = cert.get("expiry_date")
                if expiry is None:
                    continue
                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)

                cert_status = self._compute_cert_status(expiry)
                if cert_status in ("expiring_soon", "expired") or expiry <= cutoff:
                    cert_copy = dict(cert)
                    cert_copy["status"] = cert_status
                    cert_results.append(
                        {
                            "worker_id": worker_id,
                            "worker_name": worker_name,
                            "certification": cert_copy,
                        }
                    )

        cert_results.sort(
            key=lambda r: r["certification"].get("expiry_date", "9999-12-31")
        )
        return {"certifications": cert_results, "total": len(cert_results)}

    def get_certification_matrix(self, company_id: str) -> dict:
        """Get a certification matrix: workers x cert types with status.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with 'matrix' entries, 'workers' list, and 'certification_types'.
        """
        results_raw = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker)
            WHERE w.deleted = false
            RETURN w.id AS worker_id,
                   w.first_name AS first_name,
                   w.last_name AS last_name,
                   w._certifications_json AS certs_json
            """,
            {"company_id": company_id},
        )

        all_cert_types = [ct.value for ct in CertificationType]
        workers_list = []
        matrix = []

        for row in results_raw:
            worker_id = row["worker_id"]
            worker_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            workers_list.append({"id": worker_id, "name": worker_name})

            certs = self._deserialize_certs(row["certs_json"])
            cert_map: dict[str, dict] = {}
            for cert in certs:
                cert_type = cert.get("certification_type", "")
                expiry = cert.get("expiry_date")
                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)
                cert_status = self._compute_cert_status(expiry)
                cert["status"] = cert_status

                if cert_type not in cert_map or _status_priority(cert_status) > _status_priority(
                    cert_map[cert_type].get("status", "missing")
                ):
                    cert_map[cert_type] = cert

            for cert_type in all_cert_types:
                if cert_type in cert_map:
                    cert = cert_map[cert_type]
                    expiry = cert.get("expiry_date")
                    if isinstance(expiry, str):
                        expiry = date.fromisoformat(expiry)
                    matrix.append(
                        {
                            "worker_id": worker_id,
                            "worker_name": worker_name,
                            "certification_type": cert_type,
                            "status": cert.get("status", "valid"),
                            "expiry_date": (
                                expiry.isoformat()
                                if expiry and hasattr(expiry, "isoformat")
                                else expiry
                            ),
                        }
                    )
                else:
                    matrix.append(
                        {
                            "worker_id": worker_id,
                            "worker_name": worker_name,
                            "certification_type": cert_type,
                            "status": "missing",
                            "expiry_date": None,
                        }
                    )

        return {
            "matrix": matrix,
            "workers": workers_list,
            "certification_types": all_cert_types,
        }


def _status_priority(status: str) -> int:
    """Return a priority ranking for certification statuses.

    Args:
        status: The certification status string.

    Returns:
        An integer priority (higher is better).
    """
    priorities = {"valid": 3, "expiring_soon": 2, "expired": 1, "missing": 0}
    return priorities.get(status, 0)
