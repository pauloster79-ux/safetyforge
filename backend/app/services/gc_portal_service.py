"""GC/Sub Portal service.

Manages relationships between general contractors and sub-contractors,
providing real-time compliance visibility for GCs.
"""

import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import (
    CompanyNotFoundError,
    GcRelationshipNotFoundError,
    GcInvitationNotFoundError,
)
from app.models.gc_portal import (
    GcInvitation,
    GcRelationship,
    GcRelationshipCreate,
    RelationshipStatus,
    SubComplianceSummary,
)
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.osha_log_service import OshaLogService
from app.services.worker_service import WorkerService


class GcPortalService:
    """Manages GC/Sub relationships and compliance visibility.

    Args:
        db: Firestore client instance.
        company_service: CompanyService for company profile lookups.
        document_service: DocumentService for document counts.
        osha_log_service: OshaLogService for OSHA metrics.
        worker_service: WorkerService for training/cert data.
    """

    def __init__(
        self,
        db: firestore.Client,
        company_service: CompanyService,
        document_service: DocumentService,
        osha_log_service: OshaLogService,
        worker_service: WorkerService,
    ) -> None:
        self.db = db
        self.company_service = company_service
        self.document_service = document_service
        self.osha_log_service = osha_log_service
        self.worker_service = worker_service

    def _relationships_collection(self) -> firestore.CollectionReference:
        """Return the top-level gc_relationships collection.

        Returns:
            Firestore collection reference.
        """
        return self.db.collection("gc_relationships")

    def _invitations_collection(self) -> firestore.CollectionReference:
        """Return the top-level gc_invitations collection.

        Returns:
            Firestore collection reference.
        """
        return self.db.collection("gc_invitations")

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with the given prefix.

        Args:
            prefix: The ID prefix string.

        Returns:
            A prefixed hex ID string.
        """
        return f"{prefix}_{secrets.token_hex(8)}"

    def create_relationship(
        self,
        gc_company_id: str,
        data: GcRelationshipCreate,
    ) -> GcRelationship:
        """Create a new GC/Sub relationship.

        Args:
            gc_company_id: The GC's company ID.
            data: Validated relationship creation data.

        Returns:
            The created GcRelationship.

        Raises:
            CompanyNotFoundError: If either company does not exist.
        """
        # Verify both companies exist
        gc_company = self.company_service.get(gc_company_id)
        sub_company = self.company_service.get(data.sub_company_id)

        now = datetime.now(timezone.utc)
        rel_id = self._generate_id("gcrel")

        relationship = GcRelationship(
            id=rel_id,
            gc_company_id=gc_company_id,
            sub_company_id=data.sub_company_id,
            gc_company_name=gc_company.name,
            sub_company_name=sub_company.name,
            project_name=data.project_name,
            status=RelationshipStatus.ACTIVE,
            can_view_documents=data.can_view_documents,
            can_view_inspections=data.can_view_inspections,
            can_view_training=data.can_view_training,
            can_view_incidents=data.can_view_incidents,
            can_view_osha_log=data.can_view_osha_log,
            created_at=now,
            updated_at=now,
        )

        rel_dict = relationship.model_dump()
        rel_dict["status"] = relationship.status.value
        rel_dict["created_at"] = now
        rel_dict["updated_at"] = now

        self._relationships_collection().document(rel_id).set(rel_dict)
        return relationship

    def get_relationships_as_gc(self, gc_company_id: str) -> dict:
        """List all sub-contractor relationships for a GC.

        Args:
            gc_company_id: The GC's company ID.

        Returns:
            A dict with 'relationships' list and 'total' count.
        """
        query = self._relationships_collection().where(
            "gc_company_id", "==", gc_company_id
        )
        results = []
        for doc in query.stream():
            results.append(GcRelationship(**doc.to_dict()))

        results.sort(key=lambda r: r.created_at, reverse=True)
        return {"relationships": results, "total": len(results)}

    def get_relationships_as_sub(self, sub_company_id: str) -> dict:
        """List all GC relationships for a sub-contractor.

        Args:
            sub_company_id: The sub's company ID.

        Returns:
            A dict with 'relationships' list and 'total' count.
        """
        query = self._relationships_collection().where(
            "sub_company_id", "==", sub_company_id
        )
        results = []
        for doc in query.stream():
            results.append(GcRelationship(**doc.to_dict()))

        results.sort(key=lambda r: r.created_at, reverse=True)
        return {"relationships": results, "total": len(results)}

    def get_sub_compliance_summary(
        self, gc_company_id: str, sub_company_id: str
    ) -> SubComplianceSummary:
        """Pull live compliance data for a sub-contractor.

        Aggregates data from multiple services to build a compliance
        summary visible to the GC.

        Args:
            gc_company_id: The GC's company ID (for access verification).
            sub_company_id: The sub's company ID to get data for.

        Returns:
            A SubComplianceSummary with live compliance data.

        Raises:
            GcRelationshipNotFoundError: If no active relationship exists.
            CompanyNotFoundError: If the sub company does not exist.
        """
        # Verify relationship exists
        query = (
            self._relationships_collection()
            .where("gc_company_id", "==", gc_company_id)
            .where("sub_company_id", "==", sub_company_id)
            .where("status", "==", RelationshipStatus.ACTIVE.value)
        )
        rels = list(query.stream())
        if not rels:
            raise GcRelationshipNotFoundError(
                f"gc={gc_company_id},sub={sub_company_id}"
            )

        # Get sub company profile
        sub_company = self.company_service.get(sub_company_id)

        # Get worker/cert data
        worker_result = self.worker_service.list_workers(
            company_id=sub_company_id, limit=500
        )
        workers = worker_result.get("workers", [])
        active_workers = sum(1 for w in workers if w.status.value == "active")
        expired_certs = sum(w.expired for w in workers)
        expiring_certs = sum(w.expiring_soon for w in workers)
        training_current = expired_certs == 0

        # Get OSHA metrics
        current_year = datetime.now(timezone.utc).year
        trir = None
        try:
            summary = self.osha_log_service.get_300a_summary(
                sub_company_id, current_year
            )
            trir = summary.trir
        except Exception:
            pass

        # Get document count
        doc_stats = self.document_service.get_stats(sub_company_id)
        documents_on_file = doc_stats.get("total", 0)

        # Get latest mock inspection
        mock_score = None
        mock_grade = None
        mock_ref = (
            self.db.collection("companies")
            .document(sub_company_id)
            .collection("mock_inspection_results")
        )
        mock_docs = list(
            mock_ref.order_by(
                "created_at", direction=firestore.Query.DESCENDING
            )
            .limit(1)
            .stream()
        )
        if mock_docs:
            mock_data = mock_docs[0].to_dict()
            mock_score = mock_data.get("overall_score")
            mock_grade = mock_data.get("overall_grade")

        # Get latest inspection date
        last_inspection_date = None
        last_talk_date = None

        # Check inspections across projects
        projects_ref = (
            self.db.collection("companies")
            .document(sub_company_id)
            .collection("projects")
        )
        for project_doc in projects_ref.stream():
            # Inspections
            insp_ref = project_doc.reference.collection("inspections")
            insp_docs = list(
                insp_ref.order_by(
                    "created_at", direction=firestore.Query.DESCENDING
                )
                .limit(1)
                .stream()
            )
            if insp_docs:
                insp_data = insp_docs[0].to_dict()
                created = insp_data.get("created_at")
                if isinstance(created, datetime):
                    dt_str = created.isoformat()
                    if last_inspection_date is None or dt_str > last_inspection_date:
                        last_inspection_date = dt_str

            # Toolbox talks
            talk_ref = project_doc.reference.collection("toolbox_talks")
            talk_docs = list(
                talk_ref.order_by(
                    "created_at", direction=firestore.Query.DESCENDING
                )
                .limit(1)
                .stream()
            )
            if talk_docs:
                talk_data = talk_docs[0].to_dict()
                created = talk_data.get("created_at")
                if isinstance(created, datetime):
                    dt_str = created.isoformat()
                    if last_talk_date is None or dt_str > last_talk_date:
                        last_talk_date = dt_str

        # Determine currency (within last 7 days)
        now = datetime.now(timezone.utc)
        inspection_current = False
        talks_current = False

        if last_inspection_date:
            try:
                last_insp_dt = datetime.fromisoformat(last_inspection_date)
                if hasattr(last_insp_dt, "tzinfo") and last_insp_dt.tzinfo is None:
                    last_insp_dt = last_insp_dt.replace(tzinfo=timezone.utc)
                inspection_current = (now - last_insp_dt).days <= 7
            except (ValueError, TypeError):
                pass

        if last_talk_date:
            try:
                last_talk_dt = datetime.fromisoformat(last_talk_date)
                if hasattr(last_talk_dt, "tzinfo") and last_talk_dt.tzinfo is None:
                    last_talk_dt = last_talk_dt.replace(tzinfo=timezone.utc)
                talks_current = (now - last_talk_dt).days <= 7
            except (ValueError, TypeError):
                pass

        # Determine overall status
        if expired_certs > 0 or (trir is not None and trir > 6.0):
            overall_status = "non_compliant"
        elif expiring_certs > 0 or not inspection_current or not talks_current:
            overall_status = "at_risk"
        else:
            overall_status = "compliant"

        return SubComplianceSummary(
            sub_company_id=sub_company_id,
            sub_company_name=sub_company.name,
            compliance_score=0,
            emr=None,
            trir=trir,
            active_workers=active_workers,
            expired_certifications=expired_certs,
            expiring_certifications=expiring_certs,
            last_inspection_date=last_inspection_date,
            last_toolbox_talk_date=last_talk_date,
            mock_inspection_score=mock_score,
            mock_inspection_grade=mock_grade,
            documents_on_file=documents_on_file,
            inspection_current=inspection_current,
            talks_current=talks_current,
            training_current=training_current,
            overall_status=overall_status,
        )

    def get_all_sub_summaries(self, gc_company_id: str) -> dict:
        """Get compliance summaries for all subs of a GC.

        Args:
            gc_company_id: The GC's company ID.

        Returns:
            A dict with 'summaries' list and 'total' count.
        """
        rel_result = self.get_relationships_as_gc(gc_company_id)
        relationships = rel_result.get("relationships", [])

        summaries = []
        for rel in relationships:
            if rel.status != RelationshipStatus.ACTIVE:
                continue
            try:
                summary = self.get_sub_compliance_summary(
                    gc_company_id, rel.sub_company_id
                )
                summaries.append(summary)
            except Exception:
                # If we can't get data for a sub, include a minimal summary
                summaries.append(
                    SubComplianceSummary(
                        sub_company_id=rel.sub_company_id,
                        sub_company_name=rel.sub_company_name,
                        overall_status="unknown",
                    )
                )

        return {"summaries": summaries, "total": len(summaries)}

    def invite_sub(
        self,
        gc_company_id: str,
        sub_email: str,
        project_name: str,
    ) -> GcInvitation:
        """Send an invitation to a sub-contractor to connect.

        Args:
            gc_company_id: The GC's company ID.
            sub_email: Email address of the sub-contractor.
            project_name: Optional project name for context.

        Returns:
            The created GcInvitation.

        Raises:
            CompanyNotFoundError: If the GC company does not exist.
        """
        gc_company = self.company_service.get(gc_company_id)

        now = datetime.now(timezone.utc)
        invite_id = self._generate_id("gcinv")

        invitation = GcInvitation(
            id=invite_id,
            gc_company_id=gc_company_id,
            gc_company_name=gc_company.name,
            sub_email=sub_email,
            project_name=project_name,
            status="pending",
            created_at=now,
        )

        inv_dict = invitation.model_dump()
        inv_dict["created_at"] = now

        self._invitations_collection().document(invite_id).set(inv_dict)
        return invitation

    def accept_invitation(
        self, invitation_id: str, sub_company_id: str
    ) -> GcRelationship:
        """Accept a GC invitation and create the relationship.

        Args:
            invitation_id: The invitation ID to accept.
            sub_company_id: The sub's company ID.

        Returns:
            The created GcRelationship.

        Raises:
            GcInvitationNotFoundError: If the invitation does not exist.
            CompanyNotFoundError: If the sub company does not exist.
        """
        doc = self._invitations_collection().document(invitation_id).get()
        if not doc.exists:
            raise GcInvitationNotFoundError(invitation_id)

        inv_data = doc.to_dict()
        if inv_data.get("status") != "pending":
            raise GcInvitationNotFoundError(invitation_id)

        # Update invitation status
        self._invitations_collection().document(invitation_id).update(
            {"status": "accepted"}
        )

        # Create the relationship
        create_data = GcRelationshipCreate(
            sub_company_id=sub_company_id,
            project_name=inv_data.get("project_name", ""),
        )

        return self.create_relationship(
            gc_company_id=inv_data["gc_company_id"],
            data=create_data,
        )
