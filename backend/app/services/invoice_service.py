"""Invoice CRUD service (Neo4j-backed).

Invoices represent money owed (receivable) or owing (payable) on a project.
Lines on an invoice cover specific WorkItems, enabling progress billing.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class InvoiceNotFoundError(Exception):
    """Raised when an invoice cannot be found."""

    def __init__(self, invoice_id: str) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice not found: {invoice_id}")


VALID_INVOICE_STATUSES = frozenset(
    {"draft", "sent", "partial", "paid", "overdue", "void"}
)


class InvoiceService(BaseService):
    """Manages Invoice and InvoiceLine nodes in the Neo4j graph.

    Invoices connect to projects via (Project)-[:HAS_INVOICE]->(Invoice).
    Lines connect via (Invoice)-[:HAS_LINE]->(InvoiceLine)
    and cover work items via (InvoiceLine)-[:COVERS]->(WorkItem).
    """

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new invoice on a project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Invoice fields — direction ('receivable'|'payable'), number,
                status, amount, due_date, sent_date, paid_date, notes.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created invoice dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
        """
        actor = Actor.human(user_id)
        inv_id = self._generate_id("inv")

        props: dict[str, Any] = {
            "id": inv_id,
            "direction": data.get("direction", "receivable"),
            "number": data.get("number"),
            "status": data.get("status", "draft"),
            "amount": data.get("amount"),
            "currency": data.get("currency", "USD"),
            "due_date": data.get("due_date"),
            "sent_date": data.get("sent_date"),
            "paid_date": None,
            "notes": data.get("notes"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (inv:Invoice $props)
            CREATE (p)-[:HAS_INVOICE]->(inv)
            RETURN inv {.*, project_id: p.id, company_id: c.id} AS invoice
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=inv_id,
            entity_type="Invoice",
            company_id=company_id,
            actor=actor,
            summary=f"Created invoice on project {project_id}",
            related_entity_ids=[project_id],
        )
        return result["invoice"]

    def get(
        self, company_id: str, project_id: str, invoice_id: str
    ) -> dict[str, Any]:
        """Fetch a single invoice with its line items.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            invoice_id: The invoice ID to fetch.

        Returns:
            The invoice dict including a 'lines' list.

        Raises:
            InvoiceNotFoundError: If the invoice does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
            WHERE inv.deleted = false
            OPTIONAL MATCH (inv)-[:HAS_LINE]->(line:InvoiceLine)
            WITH inv, p, c, collect(line {.*}) AS lines
            RETURN inv {.*, project_id: p.id, company_id: c.id, lines: lines} AS invoice
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "invoice_id": invoice_id,
            },
        )
        if result is None:
            raise InvoiceNotFoundError(invoice_id)
        return result["invoice"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        direction: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List invoices for a project with optional direction filter.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            direction: Optional filter — 'receivable' or 'payable'.
            limit: Maximum number of invoices to return.
            offset: Number of invoices to skip.

        Returns:
            A dict with 'invoices' list and 'total' count.
        """
        where_clauses = ["inv.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if direction is not None:
            where_clauses.append("inv.direction = $direction")
            params["direction"] = direction

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_INVOICE]->(inv:Invoice)
            WHERE {where_str}
            RETURN count(inv) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_INVOICE]->(inv:Invoice)
            WHERE {where_str}
            RETURN inv {{.*, project_id: p.id, company_id: c.id}} AS invoice
            ORDER BY inv.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"invoices": [r["invoice"] for r in results], "total": total}

    def update_status(
        self,
        company_id: str,
        project_id: str,
        invoice_id: str,
        new_status: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Transition an invoice to a new status.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            invoice_id: The invoice ID.
            new_status: Target status — one of: draft, sent, partial, paid,
                overdue, void.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated invoice dict.

        Raises:
            ValueError: If new_status is not a valid status.
            InvoiceNotFoundError: If the invoice does not exist or is soft-deleted.
        """
        if new_status not in VALID_INVOICE_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of: {sorted(VALID_INVOICE_STATUSES)}"
            )

        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
            WHERE inv.deleted = false
            SET inv.status = $new_status, inv += $provenance
            RETURN inv {.*, project_id: p.id, company_id: c.id} AS invoice
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "invoice_id": invoice_id,
                "new_status": new_status,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise InvoiceNotFoundError(invoice_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=invoice_id,
            entity_type="Invoice",
            company_id=company_id,
            actor=actor,
            summary=f"Invoice {invoice_id} status changed to {new_status}",
            new_state=new_status,
        )
        return result["invoice"]

    def add_line(
        self,
        company_id: str,
        project_id: str,
        invoice_id: str,
        line_data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Add a line item to an invoice, optionally linked to a WorkItem.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            invoice_id: The invoice ID.
            line_data: Line fields — description, quantity, unit_price, amount,
                work_item_id (optional).
            user_id: Clerk user ID performing the action.

        Returns:
            The created invoice line dict.

        Raises:
            InvoiceNotFoundError: If the invoice does not exist.
        """
        actor = Actor.human(user_id)
        line_id = self._generate_id("invl")
        work_item_id = line_data.get("work_item_id")

        line_props: dict[str, Any] = {
            "id": line_id,
            "description": line_data.get("description", ""),
            "quantity": line_data.get("quantity", 1),
            "unit_price": line_data.get("unit_price"),
            "amount": line_data.get("amount"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": actor.id,
        }

        if work_item_id:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
                WHERE inv.deleted = false
                MATCH (wi:WorkItem {id: $work_item_id})
                CREATE (line:InvoiceLine $props)
                CREATE (inv)-[:HAS_LINE]->(line)
                CREATE (line)-[:COVERS]->(wi)
                RETURN line {.*, invoice_id: inv.id, work_item_id: wi.id} AS line
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "invoice_id": invoice_id,
                    "work_item_id": work_item_id,
                    "props": line_props,
                },
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
                WHERE inv.deleted = false
                CREATE (line:InvoiceLine $props)
                CREATE (inv)-[:HAS_LINE]->(line)
                RETURN line {.*, invoice_id: inv.id} AS line
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "invoice_id": invoice_id,
                    "props": line_props,
                },
            )

        if result is None:
            raise InvoiceNotFoundError(invoice_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=line_id,
            entity_type="InvoiceLine",
            company_id=company_id,
            actor=actor,
            summary=f"Added line to invoice {invoice_id}",
            related_entity_ids=[invoice_id],
        )
        return result["line"]

    def record_payment(
        self,
        company_id: str,
        project_id: str,
        invoice_id: str,
        paid_date: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Record that an invoice has been paid.

        Sets paid_date and transitions status to 'paid'.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            invoice_id: The invoice ID.
            paid_date: ISO date string of when payment was received.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated invoice dict.

        Raises:
            InvoiceNotFoundError: If the invoice does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
            WHERE inv.deleted = false
            SET inv.status = 'paid', inv.paid_date = $paid_date, inv += $provenance
            RETURN inv {.*, project_id: p.id, company_id: c.id} AS invoice
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "invoice_id": invoice_id,
                "paid_date": paid_date,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise InvoiceNotFoundError(invoice_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=invoice_id,
            entity_type="Invoice",
            company_id=company_id,
            actor=actor,
            summary=f"Recorded payment for invoice {invoice_id}",
            new_state="paid",
        )
        return result["invoice"]
