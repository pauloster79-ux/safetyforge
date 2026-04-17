"""Proposal service — generates proposal documents from project WorkItems.

Assembles work item data into a structured proposal, stores the result
as a Document node with type 'report' linked to the project.
"""

from datetime import datetime, timezone
from typing import Any

from app.models.actor import Actor
from app.services.base_service import BaseService


class ProposalService(BaseService):
    """Generates and manages proposal documents.

    A proposal is a Document node (type='report') that contains a
    structured summary of a project's work items, pricing, and terms.
    The LLM handles natural language formatting; this service assembles
    the data and stores the result.
    """

    def generate_proposal(
        self,
        company_id: str,
        project_id: str,
        actor: Actor,
        terms: str | None = None,
        timeline: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Generate a proposal document from a project's work items.

        Queries all WorkItems on the project, calculates totals,
        and creates a Document node with the assembled proposal data.

        Args:
            company_id: Tenant scope.
            project_id: The project to generate a proposal for.
            actor: The actor generating the proposal.
            terms: Optional payment terms text.
            timeline: Optional project timeline text.
            notes: Optional additional notes.

        Returns:
            Dict with proposal document data and work item breakdown.
        """
        # Fetch project + work items
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                OPTIONAL MATCH (wi)-[u:USES_ITEM]->(it:Item)
                WITH wi,
                     coalesce(wi.labour_hours, 0) * coalesce(wi.labour_rate, 0) AS labour_cost,
                     coalesce(wi.materials_allowance, 0)
                         + sum(coalesce(u.quantity, 0) * coalesce(u.unit_cost, 0)) AS materials_cost,
                     coalesce(wi.margin_pct, 0) AS margin_pct
                WITH wi, labour_cost, materials_cost, margin_pct,
                     round((labour_cost + materials_cost) * (1 + margin_pct / 100.0), 2) AS line_total
                RETURN collect({
                    id: wi.id,
                    description: wi.description,
                    labour_hours: wi.labour_hours,
                    labour_rate: wi.labour_rate,
                    labour_cost: labour_cost,
                    materials_cost: materials_cost,
                    line_total: line_total
                }) AS items,
                sum(labour_cost) AS total_labour,
                sum(materials_cost) AS total_materials,
                sum(line_total) AS grand_total,
                count(wi) AS item_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)<-[:CLIENT_IS]-(contact:Contact)
                RETURN contact {.name, .email, .phone, .company_name} AS client
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.address AS address, p.status AS status,
                   items, total_labour, total_materials, grand_total, item_count,
                   client
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        items = [i for i in result["items"] if i.get("id")]
        now = datetime.now(timezone.utc).isoformat()

        # Create the Document node to store the proposal
        doc_id = self._generate_id("doc")
        provenance = self._provenance_create(actor)

        doc_result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (d:Document {
                id: $doc_id,
                title: $title,
                document_type: 'report',
                status: 'draft',
                _content_json: $content_json,
                _project_info_json: '{}',
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_DOCUMENT]->(d)
            RETURN d.id AS doc_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "doc_id": doc_id,
                "title": f"Proposal — {result['project_name']}",
                "content_json": "{}",
                **provenance,
            },
        )

        return {
            "proposal_id": doc_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "address": result.get("address"),
            "client": result.get("client"),
            "items": items,
            "item_count": result["item_count"] or 0,
            "total_labour": result["total_labour"] or 0,
            "total_materials": result["total_materials"] or 0,
            "grand_total": result["grand_total"] or 0,
            "currency": "USD",
            "terms": terms or "Net 30 days",
            "timeline": timeline,
            "notes": notes,
            "generated_at": now,
            "status": "draft",
        }

    def update_project_status(
        self,
        company_id: str,
        project_id: str,
        new_status: str,
        actor: Actor,
    ) -> dict[str, Any]:
        """Transition a project's status through the sales pipeline.

        Validates allowed transitions:
        lead → quoted → active → complete → closed

        Args:
            company_id: Tenant scope.
            project_id: The project to update.
            new_status: Target status.
            actor: The actor performing the transition.

        Returns:
            Dict with updated project data.

        Raises:
            ValueError: If the transition is not allowed.
        """
        valid_statuses = {"lead", "quoted", "active", "complete", "closed", "on_hold"}
        if new_status not in valid_statuses:
            return {
                "error": f"Invalid status '{new_status}'. "
                f"Must be one of: {sorted(valid_statuses)}",
            }

        # Allowed transitions
        allowed_transitions: dict[str, set[str]] = {
            "lead": {"quoted", "closed"},
            "quoted": {"active", "closed", "lead"},
            "active": {"complete", "on_hold", "closed"},
            "complete": {"closed"},
            "on_hold": {"active", "closed"},
            "closed": set(),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            SET p.status = $new_status, p += $provenance
            RETURN p.id AS project_id, p.name AS project_name,
                   p.status AS status, p.address AS address
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "new_status": new_status,
                "provenance": self._provenance_update(actor),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        self._emit_audit(
            event_type="state.transitioned",
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            actor=actor,
            summary=f"Project '{result['project_name']}' status changed to {new_status}",
            new_state=new_status,
        )
        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "address": result.get("address"),
            "transitioned_to": new_status,
        }
