"""Lead capture and qualification service (Neo4j-backed).

Handles the "Find & Qualify Work" process — converting incoming leads
into qualified projects by checking company capacity, worker certifications,
and scheduling availability.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class LeadService(BaseService):
    """Manages lead capture and qualification via graph traversal.

    A lead is a Project node with status='lead'. Qualification checks
    traverse the graph to assess capacity, cert coverage, and payment history.
    """

    def capture_lead(
        self,
        company_id: str,
        data: dict[str, Any],
        actor: Actor,
    ) -> dict[str, Any]:
        """Create a new lead (Project with status='lead').

        Also creates a Contact node for the client if contact info is provided,
        and links it via CLIENT_IS.

        Args:
            company_id: The owning company ID.
            data: Lead fields — name, description, project_type, address,
                client_name, client_email, client_phone.
            actor: The actor performing the action.

        Returns:
            The created lead/project dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        project_id = self._generate_id("proj")
        provenance = self._provenance_create(actor)

        # Address is optional at lead stage but required downstream — use a
        # placeholder so the Project model validates on read. Users fill it in
        # later during qualification.
        raw_address = (data.get("address") or "").strip()
        address = raw_address if len(raw_address) >= 5 else "Address TBC"

        project_props: dict[str, Any] = {
            "id": project_id,
            "name": data.get("name", "Untitled Lead"),
            "description": data.get("description") or "",
            "project_type": data.get("project_type") or "commercial",
            "address": address,
            "client_name": data.get("client_name") or "",
            # state = lifecycle stage, status = operating condition. Do NOT
            # conflate — Project model treats them as separate enums.
            "state": "lead",
            "status": "normal",
            "contract_type": data.get("contract_type"),
            "compliance_score": 0,
            "deleted": False,
            **provenance,
        }

        # Check if we need to create a contact
        client_email = data.get("client_email")
        client_phone = data.get("client_phone")
        client_name = data.get("client_name", "")

        if client_email or client_phone:
            contact_id = self._generate_id("cont")
            contact_props: dict[str, Any] = {
                "id": contact_id,
                "name": client_name,
                "email": client_email,
                "phone": client_phone,
                "company_name": data.get("client_company"),
                "role_description": data.get("client_role"),
                "deleted": False,
                **provenance,
            }

            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                CREATE (p:Project $project_props)
                CREATE (c)-[:OWNS_PROJECT]->(p)
                CREATE (cont:Contact $contact_props)
                CREATE (c)-[:HAS_CONTACT]->(cont)
                CREATE (p)-[:CLIENT_IS]->(cont)
                RETURN p {.*, company_id: c.id} AS project,
                       cont.id AS contact_id
                """,
                {
                    "company_id": company_id,
                    "project_props": project_props,
                    "contact_props": contact_props,
                },
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                CREATE (p:Project $project_props)
                CREATE (c)-[:OWNS_PROJECT]->(p)
                RETURN p {.*, company_id: c.id} AS project
                """,
                {
                    "company_id": company_id,
                    "project_props": project_props,
                },
            )

        if result is None:
            raise CompanyNotFoundError(company_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            actor=actor,
            summary=f"Captured lead '{project_props['name']}'",
        )
        return {
            "project_id": project_id,
            "project_name": project_props["name"],
            "name": project_props["name"],
            "state": "lead",
            "status": "normal",
            "contract_type": project_props.get("contract_type"),
            "project_type": project_props.get("project_type"),
            "address": project_props.get("address"),
            "client_name": client_name,
            "contact_id": result.get("contact_id"),
            "created_at": provenance["created_at"],
        }

    def qualify_project(
        self,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Run qualification checks on a lead/project.

        Checks:
        1. Does the company have workers with relevant trades?
        2. Are certifications current?
        3. Is there scheduling capacity?
        4. What is the GC's payment history (if known)?

        Args:
            company_id: The owning company ID.
            project_id: The project/lead to qualify.

        Returns:
            Dict with qualification assessment.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            // Count active workers and their cert status
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)
                WHERE w.deleted = false AND w.status = 'active'
                OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
                WHERE cert.expiry_date IS NOT NULL AND cert.expiry_date < $today
                WITH count(DISTINCT w) AS total_workers,
                     count(DISTINCT cert) AS expired_certs
                RETURN total_workers, expired_certs
            }

            // Count active projects (capacity check)
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(ap:Project)
                WHERE ap.deleted = false AND ap.status = 'active'
                RETURN count(ap) AS active_projects
            }

            // Check GC payment history if there's a client contact
            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:CLIENT_IS]->(cont:Contact)
                RETURN cont.name AS client_name, cont.company_name AS client_company
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.project_type AS project_type,
                   total_workers, expired_certs, active_projects,
                   client_name, client_company
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        issues: list[str] = []
        strengths: list[str] = []

        total_workers = result["total_workers"]
        expired_certs = result["expired_certs"]
        active_projects = result["active_projects"]

        # Worker availability
        if total_workers == 0:
            issues.append("No active workers on roster")
        elif total_workers < 3:
            issues.append(f"Low workforce: only {total_workers} active workers")
        else:
            strengths.append(f"{total_workers} active workers available")

        # Certification health
        if expired_certs > 0:
            issues.append(f"{expired_certs} expired certifications need renewal")
        else:
            strengths.append("All certifications current")

        # Capacity
        if active_projects >= 5:
            issues.append(f"High workload: {active_projects} active projects")
        elif active_projects >= 3:
            issues.append(f"Moderate workload: {active_projects} active projects")
        else:
            strengths.append(f"Available capacity ({active_projects} active projects)")

        qualified = len(issues) == 0
        qualification_status = "qualified" if qualified else (
            "at_risk" if len(issues) <= 1 else "not_qualified"
        )

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "project_type": result["project_type"],
            "qualification_status": qualification_status,
            "qualified": qualified,
            "issues": issues,
            "strengths": strengths,
            "total_workers": total_workers,
            "expired_certifications": expired_certs,
            "active_projects": active_projects,
            "client_name": result.get("client_name"),
            "client_company": result.get("client_company"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def check_capacity(
        self,
        company_id: str,
    ) -> dict[str, Any]:
        """Assess whether the company can take on new work.

        Looks at active projects, assigned workers, and upcoming schedule.

        Args:
            company_id: The owning company ID.

        Returns:
            Dict with capacity assessment.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})

            // Active projects
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)
                WHERE p.deleted = false AND p.status = 'active'
                RETURN count(p) AS active_projects,
                       collect({id: p.id, name: p.name}) AS project_list
            }

            // Lead projects (pipeline)
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)
                WHERE p.deleted = false AND p.status = 'lead'
                RETURN count(p) AS leads_in_pipeline
            }

            // Quoted projects
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)
                WHERE p.deleted = false AND p.status = 'quoted'
                RETURN count(p) AS quoted_projects
            }

            // Total workers and assigned workers
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)
                WHERE w.deleted = false AND w.status = 'active'
                OPTIONAL MATCH (w)-[:ASSIGNED_TO_PROJECT]->(ap:Project)
                WHERE ap.deleted = false AND ap.status = 'active'
                WITH count(DISTINCT w) AS total_workers,
                     count(DISTINCT CASE WHEN ap IS NOT NULL THEN w END) AS assigned_workers
                RETURN total_workers, assigned_workers
            }

            // Upcoming work items with dates in next 4 weeks
            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                      AND wi.state IN ['scheduled', 'in_progress']
                      AND wi.planned_start IS NOT NULL
                      AND wi.planned_start <= $four_weeks_out
                RETURN count(wi) AS upcoming_work_items
            }

            RETURN active_projects, project_list, leads_in_pipeline,
                   quoted_projects, total_workers, assigned_workers,
                   upcoming_work_items
            """,
            {
                "company_id": company_id,
                "four_weeks_out": (
                    datetime.now(timezone.utc) + timedelta(weeks=4)
                ).strftime("%Y-%m-%d"),
            },
        )

        if result is None:
            return {"error": f"Company {company_id} not found"}

        total_workers = result["total_workers"]
        assigned_workers = result["assigned_workers"]
        unassigned = total_workers - assigned_workers
        utilisation_pct = round(
            (assigned_workers / total_workers * 100) if total_workers > 0 else 0, 1
        )

        can_take_work = unassigned > 0 and result["active_projects"] < 10

        return {
            "active_projects": result["active_projects"],
            "leads_in_pipeline": result["leads_in_pipeline"],
            "quoted_projects": result["quoted_projects"],
            "total_workers": total_workers,
            "assigned_workers": assigned_workers,
            "unassigned_workers": unassigned,
            "utilisation_pct": utilisation_pct,
            "upcoming_work_items_4w": result["upcoming_work_items"],
            "can_take_new_work": can_take_work,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
