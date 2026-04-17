"""Exclusion CRUD service (Neo4j-backed).

Exclusions are structured scope boundaries attached to Projects during quoting.
Graph model: (Project)-[:HAS_EXCLUSION]->(Exclusion)
Company templates: (Company)-[:EXCLUSION_TEMPLATE_OF]->(Exclusion {is_template: true})
"""

from typing import Any

from app.exceptions import ExclusionNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ExclusionService(BaseService):
    """Manages Exclusion nodes on Projects and company-level templates."""

    # -- Project-scoped CRUD -------------------------------------------------------

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create an exclusion on a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Exclusion fields.
            user_id: Clerk user ID.

        Returns:
            The created exclusion dict.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        actor = Actor.human(user_id)
        excl_id = self._generate_id("excl")

        props: dict[str, Any] = {
            "id": excl_id,
            "category": data["category"],
            "statement": data["statement"],
            "partial_inclusion": data.get("partial_inclusion", ""),
            "is_template": False,
            "trade_type": data.get("trade_type", ""),
            "source": data.get("source", ""),
            "sort_order": data.get("sort_order", 0),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (e:Exclusion $props)
            CREATE (p)-[:HAS_EXCLUSION]->(e)
            RETURN e {.*, project_id: p.id} AS exclusion
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
            entity_id=excl_id,
            entity_type="Exclusion",
            company_id=company_id,
            actor=actor,
            summary=f"Created exclusion in category '{data['category']}'",
            related_entity_ids=[project_id],
        )
        return result["exclusion"]

    def get(
        self, company_id: str, project_id: str, exclusion_id: str
    ) -> dict[str, Any]:
        """Fetch a single exclusion.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            exclusion_id: The exclusion ID.

        Returns:
            The exclusion dict.

        Raises:
            ExclusionNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_EXCLUSION]->(e:Exclusion {id: $exclusion_id})
            RETURN e {.*, project_id: p.id} AS exclusion
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "exclusion_id": exclusion_id,
            },
        )
        if result is None:
            raise ExclusionNotFoundError(exclusion_id)
        return result["exclusion"]

    def list_by_project(
        self, company_id: str, project_id: str, category: str | None = None
    ) -> dict[str, Any]:
        """List exclusions for a project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            category: Optional category filter.

        Returns:
            A dict with 'exclusions' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
        }
        cat_filter = ""
        if category:
            cat_filter = " AND e.category = $category"
            params["category"] = category

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_EXCLUSION]->(e:Exclusion)
            WHERE e.is_template = false{cat_filter}
            RETURN e {{.*, project_id: p.id}} AS exclusion
            ORDER BY e.sort_order ASC, e.created_at ASC
            """,
            params,
        )
        exclusions = [r["exclusion"] for r in results]
        return {"exclusions": exclusions, "total": len(exclusions)}

    def update(
        self,
        company_id: str,
        project_id: str,
        exclusion_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update an exclusion.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            exclusion_id: The exclusion ID.
            data: Fields to update.
            user_id: Clerk user ID.

        Returns:
            The updated exclusion dict.

        Raises:
            ExclusionNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_EXCLUSION]->(e:Exclusion {id: $exclusion_id})
            SET e += $props
            RETURN e {.*, project_id: p.id} AS exclusion
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "exclusion_id": exclusion_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ExclusionNotFoundError(exclusion_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=exclusion_id,
            entity_type="Exclusion",
            company_id=company_id,
            actor=actor,
            summary=f"Updated exclusion {exclusion_id}",
        )
        return result["exclusion"]

    def delete(
        self, company_id: str, project_id: str, exclusion_id: str
    ) -> None:
        """Delete an exclusion (hard delete).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            exclusion_id: The exclusion ID.

        Raises:
            ExclusionNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_EXCLUSION]->(e:Exclusion {id: $exclusion_id})
            DETACH DELETE e
            RETURN p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "exclusion_id": exclusion_id,
            },
        )
        if result is None:
            raise ExclusionNotFoundError(exclusion_id)

    # -- Template management -------------------------------------------------------

    def create_template(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create a company-level exclusion template.

        Args:
            company_id: The owning company ID.
            data: Template fields.
            user_id: Clerk user ID.

        Returns:
            The created template dict.
        """
        actor = Actor.human(user_id)
        excl_id = self._generate_id("excl")

        props: dict[str, Any] = {
            "id": excl_id,
            "category": data["category"],
            "statement": data["statement"],
            "partial_inclusion": data.get("partial_inclusion", ""),
            "is_template": True,
            "trade_type": data.get("trade_type", ""),
            "source": data.get("source", ""),
            "sort_order": data.get("sort_order", 0),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (e:Exclusion $props)
            CREATE (c)-[:EXCLUSION_TEMPLATE_OF]->(e)
            RETURN e {.*, company_id: c.id} AS template
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=excl_id,
            entity_type="Exclusion",
            company_id=company_id,
            actor=actor,
            summary=f"Created exclusion template in category '{data['category']}'",
        )
        return result["template"]

    def list_templates(
        self, company_id: str, trade_type: str | None = None
    ) -> dict[str, Any]:
        """List company exclusion templates.

        Args:
            company_id: The owning company ID.
            trade_type: Optional trade filter.

        Returns:
            A dict with 'templates' list and 'total' count.
        """
        params: dict[str, Any] = {"company_id": company_id}
        trade_filter = ""
        if trade_type:
            trade_filter = " AND e.trade_type = $trade_type"
            params["trade_type"] = trade_type

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:EXCLUSION_TEMPLATE_OF]->(e:Exclusion)
            WHERE e.is_template = true{trade_filter}
            RETURN e {{.*, company_id: c.id}} AS template
            ORDER BY e.sort_order ASC, e.created_at ASC
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
        """Copy a company template to a project as a project-scoped exclusion.

        Creates an EXCLUSION_FROM_TEMPLATE relationship for traceability.

        Args:
            company_id: The owning company ID.
            project_id: The target project ID.
            template_id: The template exclusion ID.
            user_id: Clerk user ID.

        Returns:
            The created project exclusion dict.

        Raises:
            ExclusionNotFoundError: If template not found.
        """
        actor = Actor.human(user_id)
        excl_id = self._generate_id("excl")

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:EXCLUSION_TEMPLATE_OF]->(tmpl:Exclusion {id: $template_id})
            MATCH (c)-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (e:Exclusion {
                id: $new_id,
                category: tmpl.category,
                statement: tmpl.statement,
                partial_inclusion: tmpl.partial_inclusion,
                is_template: false,
                trade_type: tmpl.trade_type,
                source: tmpl.source,
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
            CREATE (p)-[:HAS_EXCLUSION]->(e)
            CREATE (e)-[:EXCLUSION_FROM_TEMPLATE]->(tmpl)
            RETURN e {.*, project_id: p.id} AS exclusion
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "template_id": template_id,
                "new_id": excl_id,
                **self._provenance_create(actor),
            },
        )
        if result is None:
            raise ExclusionNotFoundError(template_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=excl_id,
            entity_type="Exclusion",
            company_id=company_id,
            actor=actor,
            summary=f"Copied exclusion template {template_id} to project {project_id}",
            related_entity_ids=[template_id, project_id],
        )
        return result["exclusion"]
