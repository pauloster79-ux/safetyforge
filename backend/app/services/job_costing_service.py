"""Job costing service — graph traversal for cost rollup.

Calculates actual vs estimated costs by traversing:
  Project → WorkItems → TimeEntries (labour)
  Project → WorkItems → USES_ITEM (materials)

Costs are calculated at query time per the ontology design decision:
costing lives on the WorkItem, not on a separate Estimate entity.
"""

import logging
from typing import Any

from neo4j import Driver

from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class JobCostingService(BaseService):
    """Calculates job costs from graph traversals.

    Labour costs come from TimeEntry hours × worker rate.
    Material costs come from USES_ITEM relationships (qty × unit_cost).
    Estimated costs come from WorkItem properties.

    Attributes:
        driver: Neo4j driver.
    """

    def __init__(self, driver: Driver) -> None:
        """Initialise the job costing service.

        Args:
            driver: Neo4j driver.
        """
        super().__init__(driver)

    def get_job_cost_summary(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Calculate actual vs estimated costs for a project.

        Traverses Project → WorkItems → TimeEntries + USES_ITEM.

        Args:
            company_id: Tenant scope.
            project_id: The project to cost.

        Returns:
            Dict with estimated and actual cost breakdowns per work item.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false

                OPTIONAL MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
                WHERE te.deleted = false
                WITH wi,
                     sum(COALESCE(te.regular_hours, 0)) AS actual_hours,
                     count(te) AS time_entry_count

                OPTIONAL MATCH (wi)-[:USES_ITEM]->(item)
                WITH wi, actual_hours, time_entry_count,
                     sum(COALESCE(item.quantity, 0) * COALESCE(item.unit_cost, 0)) AS actual_material_cost

                WITH collect({
                    id: wi.id,
                    description: wi.description,
                    state: wi.state,
                    estimated_labour_hours: COALESCE(wi.labour_hours, 0),
                    estimated_labour_rate: COALESCE(wi.labour_rate, 0),
                    estimated_labour_cost: COALESCE(wi.labour_hours, 0) * COALESCE(wi.labour_rate, 0),
                    estimated_materials: COALESCE(wi.materials_allowance, 0),
                    actual_hours: actual_hours,
                    actual_labour_cost: actual_hours * COALESCE(wi.labour_rate, 0),
                    actual_material_cost: actual_material_cost,
                    time_entry_count: time_entry_count
                }) AS work_items
                RETURN work_items
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.status AS status,
                   p.contract_value AS contract_value,
                   work_items
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        items = [wi for wi in result["work_items"] if wi.get("id")]

        total_estimated_labour = sum(wi["estimated_labour_cost"] for wi in items)
        total_estimated_materials = sum(wi["estimated_materials"] for wi in items)
        total_actual_labour = sum(wi["actual_labour_cost"] for wi in items)
        total_actual_materials = sum(wi["actual_material_cost"] for wi in items)

        total_estimated = total_estimated_labour + total_estimated_materials
        total_actual = total_actual_labour + total_actual_materials
        contract_value = result.get("contract_value") or 0

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "contract_value": contract_value,
            "estimated_cost": {
                "labour": total_estimated_labour,
                "materials": total_estimated_materials,
                "total": total_estimated,
            },
            "actual_cost": {
                "labour": total_actual_labour,
                "materials": total_actual_materials,
                "total": total_actual,
            },
            "variance": total_actual - total_estimated,
            "margin": contract_value - total_actual if contract_value else None,
            "burn_rate": (
                round(total_actual / total_estimated * 100, 1)
                if total_estimated > 0
                else 0
            ),
            "work_items": items,
            "work_item_count": len(items),
        }

    def get_financial_overview(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Project-level financial summary.

        Assembles: contract value, estimated cost, actual cost,
        variations total, invoiced total, paid total.

        Args:
            company_id: Tenant scope.
            project_id: The project.

        Returns:
            Dict with full financial overview.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                WITH sum(COALESCE(wi.labour_hours, 0) * COALESCE(wi.labour_rate, 0)
                         + COALESCE(wi.materials_allowance, 0)) AS estimated_total
                RETURN estimated_total
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
                WHERE wi.deleted = false AND te.deleted = false
                WITH sum(COALESCE(te.regular_hours, 0) * COALESCE(wi.labour_rate, 0)) AS actual_labour
                RETURN actual_labour
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)-[:USES_ITEM]->(item)
                WHERE wi.deleted = false
                WITH sum(COALESCE(item.quantity, 0) * COALESCE(item.unit_cost, 0)) AS actual_materials
                RETURN actual_materials
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_VARIATION]->(v:Variation)
                WHERE v.deleted = false AND v.status = 'approved'
                WITH sum(COALESCE(v.amount, 0)) AS approved_variations,
                     count(v) AS variation_count
                RETURN approved_variations, variation_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_VARIATION]->(v:Variation)
                WHERE v.deleted = false AND v.status IN ['draft', 'submitted']
                RETURN count(v) AS pending_variations
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)
                WHERE inv.deleted = false AND inv.direction = 'receivable'
                WITH sum(COALESCE(inv.total_amount, 0)) AS invoiced_total,
                     count(inv) AS invoice_count
                RETURN invoiced_total, invoice_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)-[:PAID_BY]->(pay:Payment)
                WHERE inv.deleted = false AND inv.direction = 'receivable'
                WITH sum(COALESCE(pay.amount, 0)) AS paid_total
                RETURN paid_total
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.status AS status,
                   COALESCE(p.contract_value, 0) AS contract_value,
                   estimated_total, actual_labour, actual_materials,
                   approved_variations, variation_count, pending_variations,
                   invoiced_total, invoice_count, paid_total
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        actual_total = (result["actual_labour"] or 0) + (result["actual_materials"] or 0)
        contract_value = result["contract_value"] or 0
        approved_variations = result["approved_variations"] or 0
        adjusted_contract = contract_value + approved_variations
        invoiced = result["invoiced_total"] or 0
        paid = result["paid_total"] or 0

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "contract_value": contract_value,
            "approved_variations": approved_variations,
            "adjusted_contract_value": adjusted_contract,
            "estimated_cost": result["estimated_total"] or 0,
            "actual_cost": actual_total,
            "actual_labour": result["actual_labour"] or 0,
            "actual_materials": result["actual_materials"] or 0,
            "projected_profit": adjusted_contract - actual_total,
            "profit_margin_pct": (
                round((adjusted_contract - actual_total) / adjusted_contract * 100, 1)
                if adjusted_contract > 0
                else 0
            ),
            "variation_count": result["variation_count"] or 0,
            "pending_variations": result["pending_variations"] or 0,
            "invoiced_total": invoiced,
            "invoice_count": result["invoice_count"] or 0,
            "paid_total": paid,
            "outstanding": invoiced - paid,
        }
