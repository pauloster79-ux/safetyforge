"""Worker CRUD service with certification management against Firestore."""

import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, WorkerNotFoundError
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


class WorkerService:
    """Manages worker profiles and certifications in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore document reference.
        """
        return self.db.collection("companies").document(company_id)

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the workers subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("workers")

    def _generate_id(self) -> str:
        """Generate a unique worker ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"wkr_{secrets.token_hex(8)}"

    def _generate_cert_id(self) -> str:
        """Generate a unique certification ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"cert_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    def _compute_cert_status(self, expiry_date: date | None) -> str:
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

    def _compute_worker_fields(self, worker_dict: dict[str, Any]) -> dict[str, Any]:
        """Compute certification statuses and summary fields on a worker dict.

        Updates each certification's status and computes total_certifications,
        expiring_soon, and expired counts.

        Args:
            worker_dict: The raw worker dict from Firestore.

        Returns:
            The worker dict with computed fields populated.
        """
        certs = worker_dict.get("certifications", [])
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

    def _serialize_cert(self, cert: dict[str, Any]) -> dict[str, Any]:
        """Serialize certification dates to ISO format strings for Firestore.

        Args:
            cert: Certification dict.

        Returns:
            Certification dict with date fields as ISO strings.
        """
        result = dict(cert)
        if result.get("issued_date") and hasattr(result["issued_date"], "isoformat"):
            result["issued_date"] = result["issued_date"].isoformat()
        if result.get("expiry_date") and hasattr(result["expiry_date"], "isoformat"):
            result["expiry_date"] = result["expiry_date"].isoformat()
        return result

    def create(self, company_id: str, data: WorkerCreate, user_id: str) -> Worker:
        """Create a new worker.

        Args:
            company_id: The owning company ID.
            data: Validated worker creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Worker with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        worker_id = self._generate_id()

        worker_dict: dict[str, Any] = {
            "id": worker_id,
            "company_id": company_id,
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
            "certifications": [],
            "total_certifications": 0,
            "expiring_soon": 0,
            "expired": 0,
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "deleted": False,
        }

        self._collection(company_id).document(worker_id).set(worker_dict)
        return Worker(**worker_dict)

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
        doc = self._collection(company_id).document(worker_id).get()
        if not doc.exists:
            raise WorkerNotFoundError(worker_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        data = self._compute_worker_fields(data)
        return Worker(**data)

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
        base_query: firestore.Query = self._collection(company_id).where(
            "deleted", "==", False
        )

        if status is not None:
            base_query = base_query.where("status", "==", status.value)

        if role is not None:
            base_query = base_query.where("role", "==", role)

        if trade is not None:
            base_query = base_query.where("trade", "==", trade)

        # Fetch all matching docs for count and search filtering
        all_docs = []
        for doc in base_query.stream():
            data = doc.to_dict()
            data = self._compute_worker_fields(data)
            all_docs.append(data)

        # Apply name search filter in-memory (Firestore doesn't support contains)
        if search:
            search_lower = search.lower()
            all_docs = [
                d
                for d in all_docs
                if search_lower in d.get("first_name", "").lower()
                or search_lower in d.get("last_name", "").lower()
            ]

        total = len(all_docs)

        # Sort by created_at descending, then paginate
        all_docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        paginated = all_docs[offset : offset + limit]

        workers = [Worker(**d) for d in paginated]
        return {"workers": workers, "total": total}

    def update(
        self, company_id: str, worker_id: str, data: WorkerUpdate, user_id: str
    ) -> Worker:
        """Update an existing worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Worker model.

        Raises:
            WorkerNotFoundError: If the worker does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id).document(worker_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name == "hire_date" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            else:
                update_data[field_name] = value

        if not update_data:
            worker_data = self._compute_worker_fields(doc.to_dict())
            return Worker(**worker_data)

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        worker_data = self._compute_worker_fields(updated_doc.to_dict())
        return Worker(**worker_data)

    def delete(self, company_id: str, worker_id: str) -> None:
        """Soft-delete a worker by setting status to terminated and deleted flag.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID to delete.

        Raises:
            WorkerNotFoundError: If the worker does not exist.
        """
        doc_ref = self._collection(company_id).document(worker_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        doc_ref.update(
            {
                "status": WorkerStatus.TERMINATED.value,
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

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
        doc_ref = self._collection(company_id).document(worker_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        cert_id = self._generate_cert_id()
        cert_dict: dict[str, Any] = {
            "id": cert_id,
            "certification_type": cert_data.certification_type.value,
            "custom_name": cert_data.custom_name,
            "issued_date": cert_data.issued_date.isoformat(),
            "expiry_date": (
                cert_data.expiry_date.isoformat() if cert_data.expiry_date else None
            ),
            "issuing_body": cert_data.issuing_body,
            "certificate_number": cert_data.certificate_number,
            "proof_document_url": None,
            "status": self._compute_cert_status(cert_data.expiry_date),
            "notes": cert_data.notes,
        }

        worker_data = doc.to_dict()
        certs = worker_data.get("certifications", [])
        certs.append(cert_dict)

        doc_ref.update(
            {
                "certifications": [self._serialize_cert(c) for c in certs],
                "updated_at": datetime.now(timezone.utc),
            }
        )

        updated_doc = doc_ref.get()
        updated_data = self._compute_worker_fields(updated_doc.to_dict())
        return Worker(**updated_data)

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
        doc_ref = self._collection(company_id).document(worker_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        worker_data = doc.to_dict()
        certs = worker_data.get("certifications", [])

        cert_found = False
        for cert in certs:
            if cert["id"] == cert_id:
                cert_found = True
                for field_name, value in cert_data.model_dump(
                    exclude_none=True
                ).items():
                    if field_name == "certification_type" and value is not None:
                        cert[field_name] = (
                            value.value if hasattr(value, "value") else value
                        )
                    elif field_name in ("issued_date", "expiry_date") and value is not None:
                        cert[field_name] = (
                            value.isoformat() if hasattr(value, "isoformat") else value
                        )
                    else:
                        cert[field_name] = value
                break

        if not cert_found:
            raise ValueError(f"Certification not found: {cert_id}")

        doc_ref.update(
            {
                "certifications": [self._serialize_cert(c) for c in certs],
                "updated_at": datetime.now(timezone.utc),
            }
        )

        updated_doc = doc_ref.get()
        updated_data = self._compute_worker_fields(updated_doc.to_dict())
        return Worker(**updated_data)

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
        doc_ref = self._collection(company_id).document(worker_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise WorkerNotFoundError(worker_id)

        worker_data = doc.to_dict()
        certs = worker_data.get("certifications", [])
        new_certs = [c for c in certs if c["id"] != cert_id]

        if len(new_certs) == len(certs):
            raise ValueError(f"Certification not found: {cert_id}")

        doc_ref.update(
            {
                "certifications": [self._serialize_cert(c) for c in new_certs],
                "updated_at": datetime.now(timezone.utc),
            }
        )

        updated_doc = doc_ref.get()
        updated_data = self._compute_worker_fields(updated_doc.to_dict())
        return Worker(**updated_data)

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

        base_query = self._collection(company_id).where("deleted", "==", False)
        results = []

        for doc in base_query.stream():
            worker_data = doc.to_dict()
            worker_name = (
                f"{worker_data.get('first_name', '')} {worker_data.get('last_name', '')}"
            ).strip()
            worker_id = worker_data.get("id", "")

            for cert in worker_data.get("certifications", []):
                expiry = cert.get("expiry_date")
                if expiry is None:
                    continue
                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)

                cert_status = self._compute_cert_status(expiry)
                if cert_status in ("expiring_soon", "expired") or expiry <= cutoff:
                    cert_copy = dict(cert)
                    cert_copy["status"] = cert_status
                    results.append(
                        {
                            "worker_id": worker_id,
                            "worker_name": worker_name,
                            "certification": cert_copy,
                        }
                    )

        # Sort by expiry date ascending (most urgent first)
        results.sort(
            key=lambda r: r["certification"].get("expiry_date", "9999-12-31")
        )

        return {"certifications": results, "total": len(results)}

    def get_certification_matrix(self, company_id: str) -> dict:
        """Get a certification matrix: workers x cert types with status.

        Args:
            company_id: The owning company ID.

        Returns:
            A dict with 'matrix' entries, 'workers' list, and 'certification_types'.
        """
        base_query = self._collection(company_id).where("deleted", "==", False)
        all_cert_types = [ct.value for ct in CertificationType]

        workers_list = []
        matrix = []

        for doc in base_query.stream():
            worker_data = doc.to_dict()
            worker_id = worker_data.get("id", "")
            worker_name = (
                f"{worker_data.get('first_name', '')} {worker_data.get('last_name', '')}"
            ).strip()
            workers_list.append({"id": worker_id, "name": worker_name})

            # Build a map of cert_type -> best cert for this worker
            cert_map: dict[str, dict] = {}
            for cert in worker_data.get("certifications", []):
                cert_type = cert.get("certification_type", "")
                expiry = cert.get("expiry_date")
                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)
                cert_status = self._compute_cert_status(expiry)
                cert["status"] = cert_status

                # Keep the best status (valid > expiring_soon > expired)
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
