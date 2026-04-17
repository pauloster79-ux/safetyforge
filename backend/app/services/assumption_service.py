"""Assumption CRUD service (Neo4j-backed).

Assumptions are structured qualifications attached to Projects during quoting.
Graph model: (Project)-[:HAS_ASSUMPTION]->(Assumption)
Company templates: (Company)-[:ASSUMPTION_TEMPLATE_OF]->(Assumption {is_template: true})
"""

from typing import Any

from app.exceptions import AssumptionNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class AssumptionService(BaseService):
    """Manages Assumption nodes on Projects and company-level templates."""

    # -- Project-scoped CRUD -------------------------------------------------------

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create an assumption on a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Assumption fields.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created assumption dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        actor = Actor.human(user_id)
        asmp_id = self._generate_id("asmp")

        props: dict[str, Any] = {
            "id": asmp_id,
            "category": data["category"],
            "statement": data["statement"],
            "relied_on_value": data.get("relied_on_value", ""),
            "relied_on_unit": data.get("relied_on_unit", ""),
            "source_document": data.get("source_document", ""),
            "variation_trigger": data.get("variation_trigger", False),
            "trigger_description": data.get("trigger_description", ""),
            "is_template": False,
            "trade_type": data.get("trade_type", ""),
            "status": "active",
            "triggered_at": None,
            "triggered_by_event": None,
            "sort_order": data.get("sort_order", 0),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (a:Assumption $props)
            CREATE (p)-[:HAS_ASSUMPTION]->(a)
            RETURN a {.*, project_id: p.id} AS assumption
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "props": props,
            },
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=asmp_id,
            entity_type="Assumption",
            company_id=company_id,
            actor=actor,
            summary=f"Created assumption in category '{data['category']}'",
            related_entity_ids=[project_id],
        )
        return result["assumption"]

    def get(
        self, company_id: str, project_id: str, assumption_id: str
    ) -> dict[str, Any]:
        """Fetch a single assumption.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            assumption_id: The assumption ID.

        Returns:
            The assumption dict.

        Raises:
            AssumptionNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_ASSUMPTION]->(a:Assumption {id: $assumption_id})
            RETURN a {.*, project_id: p.id} AS assumption
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "assumption_id": assumption_id,
            },
        )
        if result is None:
            raise AssumptionNotFoundError(assumption_id)
        return result["assumption"]

    def list_by_project(
        self, company_id: str, project_id: str, category: str | None = None
    ) -> dict[str, Any]:
        """List assumptions for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            category: Optional category filter.

        Returns:
            A dict with 'assumptions' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
        }
        if category:
            where_clauses.append("a.category = $category")
            params["category"] = category

        where_str = (" AND " + " AND ".join(where_clauses)) if where_clauses else ""

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_ASSUMPTION]->(a:Assumption)
            WHERE a.is_template = false{where_str}
            RETURN a {{.*, project_id: p.id}} AS assumption
            ORDER BY a.sort_order ASC, a.created_at ASC
            """,
            params,
        )
        assumptions = [r["assumption"] for r in results]
        return {"assumptions": assumptions, "total": len(assumptions)}

    def update(
        self,
        company_id: str,
        project_id: str,
        assumption_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update an assumption.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            assumption_id: The assumption ID.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID.

        Returns:
            The updated assumption dict.

        Raises:
            AssumptionNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_ASSUMPTION]->(a:Assumption {id: $assumption_id})
            SET a += $props
            RETURN a {.*, project_id: p.id} AS assumption
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "assumption_id": assumption_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise AssumptionNotFoundError(assumption_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=assumption_id,
            entity_type="Assumption",
            company_id=company_id,
            actor=actor,
            summary=f"Updated assumption {assumption_id}",
        )
        return result["assumption"]

    def delete(
        self, company_id: str, project_id: str, assumption_id: str
    ) -> None:
        """Delete an assumption (hard delete).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            assumption_id: The assumption ID.

        Raises:
            AssumptionNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_ASSUMPTION]->(a:Assumption {id: $assumption_id})
            DETACH DELETE a
            RETURN p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "assumption_id": assumption_id,
            },
        )
        if result is None:
            raise AssumptionNotFoundError(assumption_id)

    # -- Template management -------------------------------------------------------

    def create_template(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create a company-level assumption template.

        Args:
            company_id: The owning company ID.
            data: Template fields.
            user_id: Clerk user ID.

        Returns:
            The created template dict.
        """
        actor = Actor.human(user_id)
        asmp_id = self._generate_id("asmp")

        props: dict[str, Any] = {
            "id": asmp_id,
            "category": data["category"],
            "statement": data["statement"],
            "relied_on_value": data.get("relied_on_value", ""),
            "relied_on_unit": data.get("relied_on_unit", ""),
            "source_document": data.get("source_document", ""),
            "variation_trigger": data.get("variation_trigger", False),
            "trigger_description": data.get("trigger_description", ""),
            "is_template": True,
            "trade_type": data.get("trade_type", ""),
            "status": "active",
            "sort_order": data.get("sort_order", 0),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:Assumption $props)
            CREATE (c)-[:ASSUMPTION_TEMPLATE_OF]->(a)
            RETURN a {.*, company_id: c.id} AS template
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=asmp_id,
            entity_type="Assumption",
            company_id=company_id,
            actor=actor,
            summary=f"Created assumption template in category '{data['category']}'",
        )
        return result["template"]

    def list_templates(
        self, company_id: str, trade_type: str | None = None
    ) -> dict[str, Any]:
        """List company assumption templates.

        Args:
            company_id: The owning company ID.
            trade_type: Optional trade filter.

        Returns:
            A dict with 'templates' list and 'total' count.
        """
        params: dict[str, Any] = {"company_id": company_id}
        trade_filter = ""
        if trade_type:
            trade_filter = " AND a.trade_type = $trade_type"
            params["trade_type"] = trade_type

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:ASSUMPTION_TEMPLATE_OF]->(a:Assumption)
            WHERE a.is_template = true{trade_filter}
            RETURN a {{.*, company_id: c.id}} AS template
            ORDER BY a.sort_order ASC, a.created_at ASC
            """,
            params,
        )
        templates = [r["template"] for r in results]
        return {"templates": templates, "total": len(templates)}

    def copy_template_to_project(
        self,
        company_id: str,
        project_id: str,
        template_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Copy a company template to a project as a project-scoped assumption.

        Creates an ASSUMPTION_FROM_TEMPLATE relationship for traceability.

        Args:
            company_id: The owning company ID.
            project_id: The target project ID.
            template_id: The template assumption ID.
            user_id: Clerk user ID.

        Returns:
            The created project assumption dict.

        Raises:
            AssumptionNotFoundError: If template not found.
        """
        actor = Actor.human(user_id)
        asmp_id = self._generate_id("asmp")

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:ASSUMPTION_TEMPLATE_OF]->(tmpl:Assumption {id: $template_id})
            MATCH (c)-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (a:Assumption {
                id: $new_id,
                category: tmpl.category,
                statement: tmpl.statement,
                relied_on_value: tmpl.relied_on_value,
                relied_on_unit: tmpl.relied_on_unit,
                source_document: tmpl.source_document,
                variation_trigger: tmpl.variation_trigger,
                trigger_description: tmpl.trigger_description,
                is_template: false,
                trade_type: tmpl.trade_type,
                status: 'active',
                triggered_at: null,
                triggered_by_event: null,
                sort_order: tmpl.sort_order,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                model_id: null,
                confidence: null,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_ASSUMPTION]->(a)
            CREATE (a)-[:ASSUMPTION_FROM_TEMPLATE]->(tmpl)
            RETURN a {.*, project_id: p.id} AS assumption
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "template_id": template_id,
                "new_id": asmp_id,
                **self._provenance_create(actor),
            },
        )
        if result is None:
            raise AssumptionNotFoundError(template_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=asmp_id,
            entity_type="Assumption",
            company_id=company_id,
            actor=actor,
            summary=f"Copied assumption template {template_id} to project {project_id}",
            related_entity_ids=[template_id, project_id],
        )
        return result["assumption"]
