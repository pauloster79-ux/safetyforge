"""Query Canvas service — registered graph queries for the analytics canvas.

Provides a catalog of parameterised Cypher queries that users can browse
and execute from the Query Canvas frontend. Each query is scoped to the
caller's company via ``$company_id``.
"""

from dataclasses import dataclass, field
from typing import Any

from neo4j import Driver

from app.services.base_service import BaseService


@dataclass(frozen=True, slots=True)
class RegisteredQuery:
    """A pre-built Cypher query exposed through the Query Canvas.

    Attributes:
        id: URL-safe slug identifying this query (e.g. 'workers-expiring-certs').
        name: Human-readable label shown in the UI.
        description: One-line explanation of what the query returns.
        category: Grouping key — 'compliance', 'cost', 'schedule', or 'safety'.
        cypher: Parameterised Cypher query string. Must accept ``$company_id``.
        columns: Ordered list of column names for the result table header.
    """

    id: str
    name: str
    description: str
    category: str
    cypher: str
    columns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Query catalog
# ---------------------------------------------------------------------------

_QUERIES: list[RegisteredQuery] = [
    RegisteredQuery(
        id="workers-expiring-certs",
        name="Workers with Expiring Certifications",
        description="Workers whose certifications expire within 30 days.",
        category="compliance",
        cypher="""
            MATCH (w:Worker)-[:HAS_CERTIFICATION]->(c:Certification)
            WHERE w.company_id = $company_id
              AND c.expiry_date IS NOT NULL
              AND date(c.expiry_date) <= date() + duration('P30D')
              AND date(c.expiry_date) >= date()
            RETURN w.first_name + ' ' + w.last_name AS worker,
                   c.certification_type AS certification,
                   c.expiry_date AS expiry_date
            ORDER BY c.expiry_date ASC
        """,
        columns=["worker", "certification", "expiry_date"],
    ),
    RegisteredQuery(
        id="workers-expired-certs",
        name="Workers with Expired Certifications",
        description="Workers holding certifications that have already expired.",
        category="compliance",
        cypher="""
            MATCH (w:Worker)-[:HAS_CERTIFICATION]->(c:Certification)
            WHERE w.company_id = $company_id
              AND c.expiry_date IS NOT NULL
              AND date(c.expiry_date) < date()
            RETURN w.first_name + ' ' + w.last_name AS worker,
                   c.certification_type AS certification,
                   c.expiry_date AS expiry_date,
                   duration.between(date(c.expiry_date), date()).days AS days_expired
            ORDER BY c.expiry_date ASC
        """,
        columns=["worker", "certification", "expiry_date", "days_expired"],
    ),
    RegisteredQuery(
        id="open-corrective-actions",
        name="Open Corrective Actions",
        description="Inspections with unresolved corrective actions.",
        category="safety",
        cypher="""
            MATCH (p:Project)-[:HAS_INSPECTION]->(i:Inspection)
            WHERE p.company_id = $company_id
              AND i.overall_status = 'fail'
              AND i.corrective_actions_needed IS NOT NULL
              AND i.corrective_actions_needed <> ''
            RETURN p.name AS project,
                   i.inspection_type AS type,
                   i.inspection_date AS date,
                   i.corrective_actions_needed AS corrective_actions
            ORDER BY i.inspection_date DESC
        """,
        columns=["project", "type", "date", "corrective_actions"],
    ),
    RegisteredQuery(
        id="projects-by-compliance",
        name="Projects by Compliance Score",
        description="All projects ranked by compliance score, lowest first.",
        category="compliance",
        cypher="""
            MATCH (p:Project)
            WHERE p.company_id = $company_id
              AND p.state = 'active'
            RETURN p.name AS project,
                   p.compliance_score AS compliance_score,
                   p.state AS state,
                   p.address AS address
            ORDER BY p.compliance_score ASC
        """,
        columns=["project", "compliance_score", "state", "address"],
    ),
    RegisteredQuery(
        id="failed-inspections-7d",
        name="Failed Inspections (Last 7 Days)",
        description="Inspections that failed in the last 7 days.",
        category="safety",
        cypher="""
            MATCH (p:Project)-[:HAS_INSPECTION]->(i:Inspection)
            WHERE p.company_id = $company_id
              AND i.overall_status = 'fail'
              AND date(i.inspection_date) >= date() - duration('P7D')
            RETURN p.name AS project,
                   i.inspection_type AS type,
                   i.inspection_date AS date,
                   i.inspector_name AS inspector,
                   i.corrective_actions_needed AS corrective_actions
            ORDER BY i.inspection_date DESC
        """,
        columns=["project", "type", "date", "inspector", "corrective_actions"],
    ),
    RegisteredQuery(
        id="unassigned-work-items",
        name="Work Items Without Assigned Workers",
        description="Work items that have no worker assigned.",
        category="schedule",
        cypher="""
            MATCH (p:Project)-[:HAS_ITEM]->(wi:WorkItem)
            WHERE p.company_id = $company_id
              AND wi.status IN ['pending', 'in_progress']
              AND NOT (wi)<-[:ASSIGNED_TO]-(:Worker)
            RETURN p.name AS project,
                   wi.title AS work_item,
                   wi.status AS status,
                   wi.due_date AS due_date
            ORDER BY wi.due_date ASC
        """,
        columns=["project", "work_item", "status", "due_date"],
    ),
    RegisteredQuery(
        id="missing-daily-logs-7d",
        name="Missing Daily Logs (Last 7 Days)",
        description="Active projects missing daily logs in the last 7 days.",
        category="schedule",
        cypher="""
            MATCH (p:Project)
            WHERE p.company_id = $company_id
              AND p.state = 'active'
            OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)
            WHERE date(dl.log_date) >= date() - duration('P7D')
            WITH p, count(dl) AS log_count
            WHERE log_count < 5
            RETURN p.name AS project,
                   p.address AS address,
                   log_count AS logs_this_week,
                   5 - log_count AS missing
            ORDER BY log_count ASC
        """,
        columns=["project", "address", "logs_this_week", "missing"],
    ),
    RegisteredQuery(
        id="equipment-overdue-inspections",
        name="Equipment with Overdue Inspections",
        description="Equipment whose next inspection date has passed.",
        category="compliance",
        cypher="""
            MATCH (e:Equipment)
            WHERE e.company_id = $company_id
              AND e.next_inspection_due IS NOT NULL
              AND date(e.next_inspection_due) < date()
            RETURN e.name AS equipment,
                   e.equipment_type AS type,
                   e.next_inspection_due AS due_date,
                   duration.between(date(e.next_inspection_due), date()).days AS days_overdue
            ORDER BY e.next_inspection_due ASC
        """,
        columns=["equipment", "type", "due_date", "days_overdue"],
    ),
    RegisteredQuery(
        id="incidents-by-severity-30d",
        name="Incidents by Severity (Last 30 Days)",
        description="Incidents from the last 30 days grouped by severity.",
        category="safety",
        cypher="""
            MATCH (p:Project)-[:HAS_INCIDENT]->(inc:Incident)
            WHERE p.company_id = $company_id
              AND date(inc.incident_date) >= date() - duration('P30D')
            RETURN inc.severity AS severity,
                   p.name AS project,
                   inc.incident_date AS date,
                   inc.description AS description,
                   inc.status AS status
            ORDER BY
                CASE inc.severity
                    WHEN 'fatality' THEN 0
                    WHEN 'hospitalization' THEN 1
                    WHEN 'medical_treatment' THEN 2
                    WHEN 'first_aid' THEN 3
                    WHEN 'near_miss' THEN 4
                    WHEN 'property_damage' THEN 5
                    ELSE 6
                END ASC,
                inc.incident_date DESC
        """,
        columns=["severity", "project", "date", "description", "status"],
    ),
    RegisteredQuery(
        id="workers-unassigned",
        name="Workers Not Assigned to Any Project",
        description="Active workers without a current project assignment.",
        category="schedule",
        cypher="""
            MATCH (w:Worker)
            WHERE w.company_id = $company_id
              AND w.status = 'active'
              AND NOT (w)-[:ASSIGNED_TO]->(:Project)
            RETURN w.first_name + ' ' + w.last_name AS worker,
                   w.role AS role,
                   w.trade AS trade,
                   w.phone AS phone
            ORDER BY w.last_name ASC
        """,
        columns=["worker", "role", "trade", "phone"],
    ),
]

_QUERY_INDEX: dict[str, RegisteredQuery] = {q.id: q for q in _QUERIES}


class QueryCanvasService(BaseService):
    """Service for listing and executing registered graph queries.

    All queries are read-only and scoped to the caller's company via
    graph-native permission (the ``$company_id`` parameter).
    """

    def list_queries(self) -> list[dict[str, str]]:
        """Return metadata for all registered queries (no execution).

        Returns:
            A list of dicts with id, name, description, category, and columns.
        """
        return [
            {
                "id": q.id,
                "name": q.name,
                "description": q.description,
                "category": q.category,
                "columns": q.columns,
            }
            for q in _QUERIES
        ]

    def execute_query(
        self, query_id: str, company_id: str
    ) -> dict[str, Any]:
        """Execute a registered query scoped to a company.

        Args:
            query_id: The slug of the registered query.
            company_id: The tenant scope.

        Returns:
            A dict with 'query_id', 'name', 'columns', 'rows' (list of dicts),
            and 'total' (row count).

        Raises:
            ValueError: If query_id is not a registered query.
        """
        query = _QUERY_INDEX.get(query_id)
        if query is None:
            raise ValueError(f"Unknown query: {query_id}")

        rows = self._read_tx(query.cypher, {"company_id": company_id})

        return {
            "query_id": query.id,
            "name": query.name,
            "columns": query.columns,
            "rows": rows,
            "total": len(rows),
        }
