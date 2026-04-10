"""Context assembler service — efficient graph traversals for composite services.

Replaces the scattered data-gathering pattern where 5+ composite services
each independently call 3-8 sub-services with redundant queries. Instead,
goes directly to Neo4j with batched Cypher queries returning structured
context that consumers pick from.

Used by: analytics, morning_brief, mock_inspection, gc_portal, prequalification.
Future: MCP tools, agents.
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.models.context import (
    ActivityCounts,
    AssembledContext,
    DocumentCounts,
    DocumentSummary,
    MockInspectionSummary,
    OshaContext,
    ProjectActivitySummary,
    ProjectCounts,
    ProjectSummary,
    WorkerCounts,
    WorkerDetail,
)
from app.services.base_service import BaseService


# Default incident rate multiplier (US OSHA)
_DEFAULT_MULTIPLIER = 200_000


class ContextAssemblerService(BaseService):
    """Assembles structured context from Neo4j graph traversals.

    Tier 1 service — depends only on the Neo4j driver, no sub-services.
    This is the key architectural win: composite services that previously
    depended on 4-8 sub-services can instead use a single assembler call.
    """

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def assemble_lightweight(self, company_id: str) -> AssembledContext:
        """Assemble count-only context for a company.

        Single batched query returning project, worker, document counts
        plus latest mock inspection. Used by analytics and gc_portal.

        Args:
            company_id: The company ID to assemble context for.

        Returns:
            AssembledContext with counts populated, no full object lists.
        """
        now = datetime.now(timezone.utc)

        counts = self._query_lightweight_counts(company_id)
        doc_counts = self._query_document_counts(company_id)
        latest_mock = self._query_latest_mock(company_id)

        return AssembledContext(
            company_id=company_id,
            assembled_at=now,
            project_counts=ProjectCounts(
                total=counts.get("total_projects", 0),
                active=counts.get("active_projects", 0),
            ),
            worker_counts=WorkerCounts(
                total=counts.get("total_workers", 0),
                active=counts.get("active_workers", 0),
                expired_certs=counts.get("expired_certs", 0),
                expiring_certs=counts.get("expiring_certs", 0),
                has_training_records=counts.get("has_training", False),
            ),
            document_counts=doc_counts,
            latest_mock=latest_mock,
        )

    def assemble_activity_counts(self, company_id: str) -> AssembledContext:
        """Assemble cross-project activity counts.

        Single query aggregating inspections, talks, hazards, and incidents
        across all projects. Replaces the N+1 loop in analytics_service.

        Args:
            company_id: The company ID to aggregate for.

        Returns:
            AssembledContext with activity_counts populated.
        """
        now = datetime.now(timezone.utc)
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false
                RETURN count(i) AS total_inspections,
                       sum(CASE WHEN i.created_at >= $month_start THEN 1 ELSE 0 END) AS inspections_this_month
            }

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)-[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
                WHERE t.deleted = false
                RETURN count(t) AS total_talks,
                       sum(CASE WHEN t.created_at >= $month_start THEN 1 ELSE 0 END) AS talks_this_month
            }

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)-[:HAS_HAZARD_REPORT]->(h:HazardReport)
                WHERE h.deleted = false
                RETURN count(h) AS total_hazards,
                       sum(CASE WHEN h.status IN ['open', 'in_progress'] THEN 1 ELSE 0 END) AS open_hazards
            }

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INCIDENT]->(inc:Incident)
                RETURN count(inc) AS total_incidents,
                       sum(CASE WHEN inc.created_at >= $month_start THEN 1 ELSE 0 END) AS incidents_this_month
            }

            RETURN total_inspections, inspections_this_month,
                   total_talks, talks_this_month,
                   total_hazards, open_hazards,
                   total_incidents, incidents_this_month
            """,
            {"company_id": company_id, "month_start": month_start},
        )

        r = result or {}

        return AssembledContext(
            company_id=company_id,
            assembled_at=now,
            activity_counts=ActivityCounts(
                total_inspections=r.get("total_inspections", 0) or 0,
                inspections_this_month=r.get("inspections_this_month", 0) or 0,
                total_talks=r.get("total_talks", 0) or 0,
                talks_this_month=r.get("talks_this_month", 0) or 0,
                total_hazard_reports=r.get("total_hazards", 0) or 0,
                open_hazard_reports=r.get("open_hazards", 0) or 0,
                total_incidents=r.get("total_incidents", 0) or 0,
                incidents_this_month=r.get("incidents_this_month", 0) or 0,
            ),
        )

    def assemble_full(
        self,
        company_id: str,
        project_id: str | None = None,
        include_content: bool = False,
        inspection_days: int = 7,
        talk_days: int = 7,
    ) -> AssembledContext:
        """Assemble full context with object lists.

        Executes 4-5 focused queries for documents, workers+certs,
        projects+activity, OSHA data, and mock inspection. Used by
        mock_inspection and prequalification.

        Args:
            company_id: The company ID.
            project_id: Optional project scope (None = company-wide).
            include_content: Whether to include document content JSON.
            inspection_days: Days to check for recent inspections.
            talk_days: Days to check for recent toolbox talks.

        Returns:
            AssembledContext with full object lists populated.
        """
        now = datetime.now(timezone.utc)

        documents = self._query_documents(company_id, include_content)
        workers = self._query_workers_full(company_id)
        projects_activity = self._query_projects_with_activity(
            company_id, inspection_days, talk_days
        )
        osha = self._query_osha(company_id)
        latest_mock = self._query_latest_mock(company_id)
        doc_counts = self._query_document_counts(company_id)

        projects = [
            ProjectSummary(
                id=pa.project_id,
                name=pa.project_name,
                status="active",  # only non-deleted returned
            )
            for pa in projects_activity
        ]

        return AssembledContext(
            company_id=company_id,
            project_id=project_id,
            assembled_at=now,
            project_counts=ProjectCounts(
                total=len(projects),
                active=len(projects),
            ),
            worker_counts=WorkerCounts(
                total=len(workers),
                active=sum(1 for w in workers if w.status == "active"),
                expired_certs=sum(
                    1
                    for w in workers
                    for c in w.certifications
                    if c.get("expiry_date") and c["expiry_date"] < date.today().isoformat()
                ),
                expiring_certs=sum(
                    1
                    for w in workers
                    for c in w.certifications
                    if c.get("expiry_date")
                    and date.today().isoformat() <= c["expiry_date"] <= (date.today() + timedelta(days=30)).isoformat()
                ),
                has_training_records=any(len(w.certifications) > 0 for w in workers),
            ),
            document_counts=doc_counts,
            project_activity=projects_activity,
            projects=projects,
            workers=workers,
            documents=documents,
            osha=osha,
            latest_mock=latest_mock,
        )

    def assemble_project_scoped(
        self,
        company_id: str,
        project_id: str,
        inspection_days: int = 2,
        talk_days: int = 7,
    ) -> AssembledContext:
        """Assemble project-scoped lightweight context.

        Single query returning cert counts (company-wide) and project
        activity checks. Used by morning_brief.

        Args:
            company_id: The company ID.
            project_id: The project to scope to.
            inspection_days: Days to check for recent inspections.
            talk_days: Days to check for recent toolbox talks.

        Returns:
            AssembledContext with worker_counts and project_activity.
        """
        now = datetime.now(timezone.utc)
        inspection_cutoff = (now - timedelta(days=inspection_days)).isoformat()
        talk_cutoff = (date.today() - timedelta(days=talk_days)).isoformat()

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)-[:HOLDS_CERT]->(cert:Certification)
                WHERE w.deleted = false AND cert.expiry_date IS NOT NULL
                WITH
                    sum(CASE WHEN cert.expiry_date < $today THEN 1 ELSE 0 END) AS expired,
                    sum(CASE WHEN cert.expiry_date >= $today
                              AND cert.expiry_date <= $expiry_cutoff THEN 1 ELSE 0 END) AS expiring
                RETURN expired, expiring
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false AND i.created_at >= $inspection_cutoff
                RETURN count(i) > 0 AS has_recent_inspection
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
                WHERE t.deleted = false AND t.scheduled_date >= $talk_cutoff
                RETURN count(t) > 0 AS has_recent_talk
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   expired, expiring,
                   has_recent_inspection, has_recent_talk
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": date.today().isoformat(),
                "expiry_cutoff": (date.today() + timedelta(days=14)).isoformat(),
                "inspection_cutoff": inspection_cutoff,
                "talk_cutoff": talk_cutoff,
            },
        )

        r = result or {}

        return AssembledContext(
            company_id=company_id,
            project_id=project_id,
            assembled_at=now,
            worker_counts=WorkerCounts(
                expired_certs=r.get("expired", 0) or 0,
                expiring_certs=r.get("expiring", 0) or 0,
            ),
            project_activity=[
                ProjectActivitySummary(
                    project_id=r.get("project_id", project_id),
                    project_name=r.get("project_name", ""),
                    has_recent_inspection=r.get("has_recent_inspection", False),
                    has_recent_talk=r.get("has_recent_talk", False),
                ),
            ] if result else [],
        )

    # ------------------------------------------------------------------
    # Internal query helpers
    # ------------------------------------------------------------------

    def _query_lightweight_counts(self, company_id: str) -> dict[str, Any]:
        """Query project, worker, and cert counts in a single traversal.

        Args:
            company_id: The company ID.

        Returns:
            Dict with count fields.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)
                WHERE p.deleted = false
                RETURN count(p) AS total_projects,
                       sum(CASE WHEN p.status = 'active' THEN 1 ELSE 0 END) AS active_projects
            }

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)
                WHERE w.deleted = false
                RETURN count(w) AS total_workers,
                       sum(CASE WHEN w.status = 'active' THEN 1 ELSE 0 END) AS active_workers
            }

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)-[:HOLDS_CERT]->(cert:Certification)
                WHERE w.deleted = false AND cert.expiry_date IS NOT NULL
                WITH
                    sum(CASE WHEN cert.expiry_date < $today THEN 1 ELSE 0 END) AS expired_certs,
                    sum(CASE WHEN cert.expiry_date >= $today
                              AND cert.expiry_date <= $expiry_cutoff THEN 1 ELSE 0 END) AS expiring_certs,
                    CASE WHEN count(cert) > 0 THEN true ELSE false END AS has_training
                RETURN expired_certs, expiring_certs, has_training
            }

            RETURN total_projects, active_projects,
                   total_workers, active_workers,
                   expired_certs, expiring_certs, has_training
            """,
            {
                "company_id": company_id,
                "today": date.today().isoformat(),
                "expiry_cutoff": (date.today() + timedelta(days=30)).isoformat(),
            },
        )
        return result or {}

    def _query_document_counts(self, company_id: str) -> DocumentCounts:
        """Query document statistics.

        Args:
            company_id: The company ID.

        Returns:
            DocumentCounts model.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false
            RETURN d.document_type AS doc_type, d.status AS doc_status
            """,
            {"company_id": company_id},
        )

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for r in results:
            dt = r.get("doc_type", "unknown")
            ds = r.get("doc_status", "unknown")
            by_type[dt] = by_type.get(dt, 0) + 1
            by_status[ds] = by_status.get(ds, 0) + 1

        return DocumentCounts(
            total=len(results),
            by_type=by_type,
            by_status=by_status,
        )

    def _query_latest_mock(self, company_id: str) -> MockInspectionSummary | None:
        """Query the latest mock inspection result.

        Args:
            company_id: The company ID.

        Returns:
            MockInspectionSummary or None if no results exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_MOCK_INSPECTION]->(r:MockInspectionResult)
            RETURN r.overall_score AS score, r.grade AS grade, r.created_at AS created_at
            ORDER BY r.created_at DESC
            LIMIT 1
            """,
            {"company_id": company_id},
        )
        if result is None:
            return None
        return MockInspectionSummary(
            score=result.get("score"),
            grade=result.get("grade"),
            created_at=result.get("created_at"),
        )

    def _query_documents(
        self, company_id: str, include_content: bool = False
    ) -> list[DocumentSummary]:
        """Query all non-deleted documents for a company.

        Args:
            company_id: The company ID.
            include_content: Whether to include content JSON.

        Returns:
            List of DocumentSummary models.
        """
        content_field = ", d._content_json AS content_json" if include_content else ""

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false
            RETURN d.id AS id, d.title AS title, d.document_type AS document_type
                   {content_field}
            ORDER BY d.created_at DESC
            """,
            {"company_id": company_id},
        )

        docs = []
        for r in results:
            content = None
            if include_content:
                cj = r.get("content_json", "{}")
                content = json.loads(cj) if cj else {}
            docs.append(
                DocumentSummary(
                    id=r["id"],
                    title=r["title"],
                    document_type=r["document_type"],
                    content=content,
                )
            )
        return docs

    def _query_workers_full(self, company_id: str) -> list[WorkerDetail]:
        """Query all workers with their certifications.

        Args:
            company_id: The company ID.

        Returns:
            List of WorkerDetail models with nested cert data.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORKER]->(w:Worker)
            WHERE w.deleted = false
            OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
            WITH w, collect(
                CASE WHEN cert IS NOT NULL
                THEN {
                    certification_type: cert.certification_type,
                    expiry_date: cert.expiry_date,
                    issue_date: cert.issue_date,
                    status: cert.status
                }
                ELSE null
                END
            ) AS certs
            RETURN w.id AS id, w.first_name AS first_name, w.last_name AS last_name,
                   w.role AS role, w.status AS status, certs
            """,
            {"company_id": company_id},
        )

        workers = []
        for r in results:
            certs = [c for c in r.get("certs", []) if c is not None]
            workers.append(
                WorkerDetail(
                    id=r["id"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    role=r.get("role"),
                    status=r.get("status", "active"),
                    certifications=certs,
                )
            )
        return workers

    def _query_projects_with_activity(
        self,
        company_id: str,
        inspection_days: int = 7,
        talk_days: int = 7,
    ) -> list[ProjectActivitySummary]:
        """Query projects with recent inspection/talk activity checks.

        Args:
            company_id: The company ID.
            inspection_days: Days to check for recent inspections.
            talk_days: Days to check for recent talks.

        Returns:
            List of ProjectActivitySummary models.
        """
        now = datetime.now(timezone.utc)
        inspection_cutoff = (now - timedelta(days=inspection_days)).isoformat()
        talk_cutoff = (date.today() - timedelta(days=talk_days)).isoformat()

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false AND i.created_at >= $inspection_cutoff
                WITH max(i.created_at) AS latest_insp, count(i) AS cnt
                RETURN cnt > 0 AS has_recent_inspection, latest_insp
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
                WHERE t.deleted = false AND t.scheduled_date >= $talk_cutoff
                WITH max(t.created_at) AS latest_talk, count(t) AS cnt
                RETURN cnt > 0 AS has_recent_talk, latest_talk
            }

            RETURN p.id AS project_id, p.name AS project_name, p.status AS status,
                   has_recent_inspection, latest_insp,
                   has_recent_talk, latest_talk
            """,
            {
                "company_id": company_id,
                "inspection_cutoff": inspection_cutoff,
                "talk_cutoff": talk_cutoff,
            },
        )

        return [
            ProjectActivitySummary(
                project_id=r["project_id"],
                project_name=r["project_name"],
                has_recent_inspection=r.get("has_recent_inspection", False),
                has_recent_talk=r.get("has_recent_talk", False),
                latest_inspection_date=r.get("latest_insp"),
                latest_talk_date=r.get("latest_talk"),
            )
            for r in results
        ]

    def _query_osha(
        self,
        company_id: str,
        years: int = 3,
    ) -> OshaContext:
        """Query OSHA log data across multiple years.

        Args:
            company_id: The company ID.
            years: Number of years to look back (default 3 for prequal).

        Returns:
            OshaContext model with multi-year metrics.
        """
        current_year = date.today().year
        year_list = [current_year - i for i in range(years)]

        # Get years with entries
        year_results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_OSHA_ENTRY]->(e:OshaLogEntry)
            RETURN DISTINCT e.year AS year
            ORDER BY year DESC
            """,
            {"company_id": company_id},
        )
        years_with_entries = [r["year"] for r in year_results]

        # Count current year entries
        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_OSHA_ENTRY]->(e:OshaLogEntry)
            WHERE e.year = $year
            RETURN count(e) AS cnt
            """,
            {"company_id": company_id, "year": current_year},
        )
        entry_count = count_result["cnt"] if count_result else 0

        # Check posting status for previous year
        summary_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_OSHA_SUMMARY]->(s:OshaSummary {year: $year})
            RETURN s.posted AS posted, s.total_hours_worked AS hours,
                   s.annual_average_employees AS employees
            """,
            {"company_id": company_id, "year": current_year - 1},
        )
        posted = summary_result["posted"] if summary_result else False

        # Compute TRIR/DART per year
        trir_by_year: dict[int, float] = {}
        dart_by_year: dict[int, float] = {}

        for yr in year_list:
            agg = self._read_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_OSHA_ENTRY]->(e:OshaLogEntry)
                WHERE e.year = $year
                RETURN count(e) AS total,
                       sum(CASE WHEN e.classification = 'death' THEN 1 ELSE 0 END) +
                       sum(CASE WHEN e.classification = 'days_away_from_work' THEN 1 ELSE 0 END) +
                       sum(CASE WHEN e.classification = 'job_transfer_or_restriction' THEN 1 ELSE 0 END) +
                       sum(CASE WHEN e.classification = 'other_recordable' THEN 1 ELSE 0 END) AS recordable,
                       sum(CASE WHEN e.classification = 'days_away_from_work' THEN 1 ELSE 0 END) +
                       sum(CASE WHEN e.classification = 'job_transfer_or_restriction' THEN 1 ELSE 0 END) AS dart_cases
                """,
                {"company_id": company_id, "year": yr},
            )

            # Get hours from summary
            hrs_result = self._read_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_OSHA_SUMMARY]->(s:OshaSummary {year: $year})
                RETURN s.total_hours_worked AS hours
                """,
                {"company_id": company_id, "year": yr},
            )
            hours = hrs_result["hours"] if hrs_result and hrs_result["hours"] else 0

            recordable = (agg["recordable"] if agg and agg["recordable"] else 0)
            dart_cases = (agg["dart_cases"] if agg and agg["dart_cases"] else 0)

            if hours > 0:
                trir_by_year[yr] = round((recordable * _DEFAULT_MULTIPLIER) / hours, 2)
                dart_by_year[yr] = round((dart_cases * _DEFAULT_MULTIPLIER) / hours, 2)
            else:
                trir_by_year[yr] = 0.0
                dart_by_year[yr] = 0.0

        return OshaContext(
            entry_count_current_year=entry_count,
            years_with_entries=years_with_entries,
            trir=trir_by_year.get(current_year, 0.0),
            dart=dart_by_year.get(current_year, 0.0),
            posted_previous_year=posted or False,
            trir_by_year=trir_by_year,
            dart_by_year=dart_by_year,
        )
