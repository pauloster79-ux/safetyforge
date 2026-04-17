"""Project CRUD service (Neo4j-backed)."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from neo4j import Driver

from app.exceptions import (
    CompanyNotFoundError,
    ProjectActivationError,
    ProjectNotFoundError,
)
from app.models.actor import Actor
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectState,
    ProjectStatus,
    ProjectUpdate,
)
from app.services.base_service import BaseService

if TYPE_CHECKING:
    from app.services.event_bus import EventBus


class ProjectService(BaseService):
    """Manages construction projects as Neo4j nodes.

    Projects connect to companies via (Company)-[:OWNS_PROJECT]->(Project).
    company_id is NOT stored on the node — it is derived from the relationship.

    Attributes:
        event_bus: Optional EventBus for emitting high-level events
            (e.g. project.actuals_ready on completion). When None,
            event emission is silently skipped.
    """

    def __init__(
        self, driver: Driver, event_bus: "EventBus | None" = None
    ) -> None:
        """Initialise the service.

        Args:
            driver: Neo4j driver.
            event_bus: Optional EventBus for emitting project-level events.
                Injected by the DI layer when available; None-safe so tests
                and standalone callers can use the service without it.
        """
        super().__init__(driver)
        self.event_bus = event_bus

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

    def _verify_has_work_items(self, project_id: str) -> None:
        """Verify that a project has at least one WorkItem.

        Args:
            project_id: The project ID to check.

        Raises:
            ProjectActivationError: If the project has no work items.
        """
        result = self._read_tx_single(
            """
            MATCH (p:Project {id: $project_id})-[:HAS_WORK_ITEM]->(wi:WorkItem)
            RETURN count(wi) AS wi_count
            """,
            {"project_id": project_id},
        )
        wi_count = result["wi_count"] if result else 0
        if wi_count == 0:
            raise ProjectActivationError(
                project_id,
                "Cannot activate project without work items \u2014 build a quote first",
            )

    def create(self, company_id: str, data: ProjectCreate, user_id: str) -> Project:
        """Create a new project linked to a company.

        Args:
            company_id: The owning company ID.
            data: Validated project creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created Project with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        project_id = self._generate_id("proj")

        props: dict[str, Any] = {
            "id": project_id,
            "name": data.name,
            "address": data.address,
            "city": data.city,
            "us_state": data.us_state,
            "region": data.region,
            "client_name": data.client_name,
            "project_type": data.project_type,
            "trade_types": data.trade_types,
            "start_date": data.start_date.isoformat() if data.start_date else None,
            "end_date": data.end_date.isoformat() if data.end_date else None,
            "estimated_workers": data.estimated_workers,
            "description": data.description,
            "special_hazards": data.special_hazards,
            "nearest_hospital": data.nearest_hospital,
            "emergency_contact_name": data.emergency_contact_name,
            "emergency_contact_phone": data.emergency_contact_phone,
            "state": ProjectState.LEAD.value,
            "status": ProjectStatus.NORMAL.value,
            "compliance_score": 0,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (p:Project $props)
            CREATE (c)-[:OWNS_PROJECT]->(p)
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            actor=actor,
            summary=f"Created project '{data.name}'",
        )
        return Project(**result["project"])

    def get(self, company_id: str, project_id: str) -> Project:
        """Fetch a single project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to fetch.

        Returns:
            The Project model.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        return Project(**result["project"])

    def list_projects(
        self,
        company_id: str,
        status: ProjectStatus | None = None,
        state: ProjectState | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List projects for a company with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            status: Filter by operating condition (normal, on_hold, etc.).
            state: Filter by lifecycle state (lead, active, completed, etc.).
            limit: Maximum number of projects to return.
            offset: Number of projects to skip.

        Returns:
            A dict with 'projects' list and 'total' count.
        """
        where_clauses = ["p.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if state is not None:
            where_clauses.append("p.state = $state")
            params["state"] = state.value

        if status is not None:
            where_clauses.append("p.status = $status")
            params["status"] = status.value

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
            WHERE {where_str}
            RETURN count(p) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
            WHERE {where_str}
            RETURN p {{.*, company_id: c.id}} AS project
            ORDER BY p.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        projects = [Project(**r["project"]) for r in results]
        return {"projects": projects, "total": total}

    def update(
        self, company_id: str, project_id: str, data: ProjectUpdate, user_id: str
    ) -> Project:
        """Update an existing project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated Project model.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        # Snapshot current state/status for transition detection
        current = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.name AS name, p.state AS state, p.status AS status
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if current is None:
            raise ProjectNotFoundError(project_id)

        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            elif field_name in ("start_date", "end_date") and value is not None:
                update_fields[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(user_id)
        update_fields.update(self._provenance_update(actor))

        # Enforce: cannot activate a project without work items
        new_state = update_fields.get("state")
        if new_state == ProjectState.ACTIVE.value and current["state"] != ProjectState.ACTIVE.value:
            self._verify_has_work_items(project_id)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            SET p += $props
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "project_id": project_id, "props": update_fields},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

        self._emit_project_update_audit(
            company_id=company_id,
            project_id=project_id,
            project_name=current["name"],
            prev_state=current["state"],
            prev_status=current["status"],
            new_project=result["project"],
            update_fields=update_fields,
            actor=actor,
        )

        # Knowledge accumulation: on transition into COMPLETED state,
        # derive actuals for every work item and stash a summary on the
        # Project node so the chat agent / Knowledge page can surface
        # rate-update offers later. Silently tolerates any failure so a
        # transient issue with actuals derivation can't block a legitimate
        # state transition.
        transitioned_to_completed = (
            update_fields.get("state") == ProjectState.COMPLETED.value
            and current["state"] != ProjectState.COMPLETED.value
        )
        if transitioned_to_completed:
            try:
                self._derive_actuals_summary(company_id, project_id, actor)
            except Exception:  # noqa: BLE001 — best-effort side effect
                pass

        return Project(**result["project"])

    def _derive_actuals_summary(
        self,
        company_id: str,
        project_id: str,
        actor: Actor,
    ) -> dict[str, Any]:
        """Walk every WorkItem on a project and derive actuals vs estimate.

        For each WorkItem, computes:
        - Estimated hours (sum of Labour.hours children).
        - Actual hours (sum of hours_regular + hours_overtime from TimeEntry).
        - Implied rate (work_item.quantity / actual_hours) when both are > 0.
        - Variance pct vs the linked ProductivityRate (if any).

        The summary dict is serialised to JSON and stored on the Project as
        ``actuals_summary_json`` so frontends can render the offer and the
        chat agent can cite it.

        Also emits ``project.actuals_ready`` on the shared event bus when
        any work item has ``should_update`` set to True — carries the
        summary so subscribers (chat, notifications) don't need to re-query.

        Args:
            company_id: Tenant scope.
            project_id: The project that just transitioned to completed.
            actor: The actor who triggered the state change (for event
                provenance).

        Returns:
            The summary dict with per-work-item derivations and a flag
            ``has_updates`` indicating whether any rate needs updating.
        """
        # Sum Labour + TimeEntry per WorkItem in one pass, plus the
        # productivity_source_id that was used for each. Flat projection —
        # we bucket by work_item.
        rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            WITH wi, p,
                 coalesce(sum(lab.hours), 0.0) AS estimated_hours,
                 [src IN collect(DISTINCT lab.productivity_source_id) WHERE src IS NOT NULL][0] AS productivity_source_id
            OPTIONAL MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
            WHERE coalesce(te.deleted, false) = false
            WITH wi, p, estimated_hours, productivity_source_id,
                 coalesce(sum(coalesce(te.hours_regular, 0.0) + coalesce(te.hours_overtime, 0.0)), 0.0) AS actual_hours
            RETURN wi.id AS work_item_id,
                   wi.description AS description,
                   wi.quantity AS quantity,
                   wi.unit AS unit,
                   estimated_hours,
                   actual_hours,
                   productivity_source_id
            ORDER BY wi.description
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        # Fetch all linked ProductivityRates in one go
        rate_ids = [
            r["productivity_source_id"] for r in rows
            if r.get("productivity_source_id")
        ]
        rates_by_id: dict[str, dict[str, Any]] = {}
        if rate_ids:
            rate_rows = self._read_tx(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
                WHERE pr.id IN $rate_ids
                RETURN pr {.*, company_id: c.id} AS rate
                """,
                {"company_id": company_id, "rate_ids": rate_ids},
            )
            rates_by_id = {
                r["rate"]["id"]: r["rate"] for r in rate_rows
            }

        derivations: list[dict[str, Any]] = []
        updates_count = 0
        for row in rows:
            estimated_quantity = float(row.get("quantity") or 0.0)
            estimated_hours = float(row.get("estimated_hours") or 0.0)
            actual_hours = float(row.get("actual_hours") or 0.0)
            productivity_source_id = row.get("productivity_source_id")
            rate_info = (
                rates_by_id.get(productivity_source_id)
                if productivity_source_id else None
            )

            implied_rate: float | None = None
            variance_pct: float | None = None
            should_update = False

            if actual_hours > 0 and estimated_quantity > 0:
                implied_rate = estimated_quantity / actual_hours
                current_rate = (
                    rate_info.get("rate") if rate_info else None
                )
                if current_rate and current_rate > 0:
                    variance_pct = (
                        (implied_rate - current_rate) / current_rate
                    ) * 100.0
                    if abs(variance_pct) > 10.0:
                        should_update = True

            if should_update:
                updates_count += 1

            derivations.append({
                "work_item_id": row["work_item_id"],
                "description": row["description"],
                "estimated_quantity": estimated_quantity,
                "unit": row.get("unit"),
                "estimated_hours": estimated_hours,
                "actual_hours": actual_hours,
                "productivity_rate_id": productivity_source_id,
                "current_rate": (
                    rate_info.get("rate") if rate_info else None
                ),
                "current_sample_size": (
                    int(rate_info.get("sample_size") or 0)
                    if rate_info else 0
                ),
                "implied_rate": implied_rate,
                "variance_pct": variance_pct,
                "should_update": should_update,
            })

        summary = {
            "project_id": project_id,
            "derived_at": datetime.now(timezone.utc).isoformat(),
            "work_items": derivations,
            "total_work_items": len(derivations),
            "updates_available": updates_count,
            "has_updates": updates_count > 0,
        }

        # Persist the summary on the Project node for the frontend + chat.
        # Stored as JSON string because Neo4j has no native nested-dict
        # property type (same approach as AuditEvent.changes_json).
        import json as _json
        self._write_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            SET p.actuals_summary_json = $summary_json,
                p.actuals_summary_at = $derived_at
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "summary_json": _json.dumps(summary),
                "derived_at": summary["derived_at"],
            },
        )

        # Emit project.actuals_ready only if at least one rate update is
        # available — no-op notifications are noise.
        if updates_count > 0:
            self._emit_actuals_ready_event(
                company_id=company_id,
                project_id=project_id,
                actor=actor,
                summary=summary,
            )

        return summary

    def _emit_actuals_ready_event(
        self,
        *,
        company_id: str,
        project_id: str,
        actor: Actor,
        summary: dict[str, Any],
    ) -> None:
        """Publish a ``project.actuals_ready`` event on the injected bus.

        No-op when ``self.event_bus`` is None (standalone tests, scripts).
        Best-effort: any error is swallowed so a broken subscriber can't
        roll back a legitimate state transition.
        """
        if self.event_bus is None:
            return
        try:
            from app.models.events import EventType

            event = self.event_bus.create_event(
                event_type=EventType.PROJECT_ACTUALS_READY,
                entity_id=project_id,
                entity_type="Project",
                company_id=company_id,
                actor=actor,
                project_id=project_id,
                summary={
                    "updates_available": summary.get("updates_available", 0),
                    "total_work_items": summary.get("total_work_items", 0),
                    "work_items_needing_update": [
                        {
                            "work_item_id": d["work_item_id"],
                            "description": d["description"],
                            "variance_pct": d["variance_pct"],
                            "productivity_rate_id": d["productivity_rate_id"],
                        }
                        for d in summary.get("work_items", [])
                        if d.get("should_update")
                    ],
                },
            )
            self.event_bus.emit(event)
        except Exception:  # noqa: BLE001 — best effort
            return

    def _emit_project_update_audit(
        self,
        *,
        company_id: str,
        project_id: str,
        project_name: str,
        prev_state: str | None,
        prev_status: str | None,
        new_project: dict[str, Any],
        update_fields: dict[str, Any],
        actor: Actor,
    ) -> None:
        """Emit audit events for a project update, splitting state/status transitions."""
        new_state = new_project.get("state")
        new_status = new_project.get("status")

        if new_state != prev_state:
            self._emit_audit(
                event_type="state.transitioned",
                entity_id=project_id,
                entity_type="Project",
                company_id=company_id,
                actor=actor,
                summary=f"Project '{project_name}': {prev_state} → {new_state}",
                prev_state=prev_state,
                new_state=new_state,
            )
            return

        if new_status != prev_status:
            self._emit_audit(
                event_type="state.transitioned",
                entity_id=project_id,
                entity_type="Project",
                company_id=company_id,
                actor=actor,
                summary=f"Project '{project_name}' status: {prev_status} → {new_status}",
                prev_state=prev_status,
                new_state=new_status,
            )
            return

        # Generic update — note which fields changed
        changed = [
            k for k in update_fields
            if k not in ("updated_by", "updated_actor_type", "updated_at")
        ]
        suffix = f" ({', '.join(changed)})" if changed else ""
        self._emit_audit(
            event_type="entity.updated",
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            actor=actor,
            summary=f"Updated project '{project_name}'{suffix}",
        )

    def delete(self, company_id: str, project_id: str, user_id: str = "system") -> None:
        """Soft-delete a project by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to delete.
            user_id: Clerk user ID of the deleting user (defaults to 'system' for
                legacy callers; callers should pass the actual user).

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            SET p.deleted = true, p.updated_at = $now
            RETURN p.name AS name, p.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

        self._emit_audit(
            event_type="entity.archived",
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived project '{result['name']}'",
        )

    def get_compliance_score(self, company_id: str, project_id: str) -> int:
        """Calculate a compliance score (0-100) for a project.

        Factors:
        - Recent inspections (last 7 days) contribute up to 40 points
        - Inspection pass rate contributes up to 40 points
        - Document completeness contributes up to 20 points

        Args:
            company_id: The owning company ID.
            project_id: The project ID.

        Returns:
            An integer score from 0 to 100.
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
            WHERE i.deleted = false
            WITH c, p,
                 count(i) AS total_inspections,
                 sum(CASE WHEN i.created_at >= $cutoff THEN 1 ELSE 0 END) AS recent_count,
                 sum(CASE WHEN i.overall_status = 'pass' THEN 1 ELSE 0 END) AS pass_count
            OPTIONAL MATCH (c)-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false
            WITH total_inspections, recent_count, pass_count, count(d) AS doc_count
            RETURN total_inspections, recent_count, pass_count, doc_count
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "cutoff": seven_days_ago,
            },
        )
        if result is None:
            return 0

        score = 0

        recent_count = result["recent_count"]
        if recent_count >= 3:
            score += 40
        elif recent_count >= 1:
            score += 20

        total_inspections = result["total_inspections"]
        if total_inspections > 0:
            pass_rate = result["pass_count"] / total_inspections
            score += int(pass_rate * 40)

        doc_count = result["doc_count"]
        if doc_count >= 3:
            score += 20
        elif doc_count >= 1:
            score += 10

        return min(score, 100)
