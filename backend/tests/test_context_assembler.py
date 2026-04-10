"""Tests for ContextAssemblerService — efficient graph context assembly."""

from datetime import date, datetime, timedelta, timezone

import pytest
from neo4j import Driver

from app.services.context_assembler import ContextAssemblerService
from tests.conftest import TEST_SETTINGS


def _create_worker_with_cert(
    driver: Driver,
    company_id: str,
    worker_id: str,
    first_name: str,
    role: str = "laborer",
    cert_type: str = "osha_10",
    expiry_date: str | None = None,
) -> None:
    """Helper to create a Worker node with an optional Certification."""
    now = datetime.now(timezone.utc).isoformat()
    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (w:Worker {
                id: $worker_id, first_name: $first_name, last_name: 'Test',
                role: $role, status: 'active', deleted: false,
                created_at: $now, updated_at: $now,
                created_by: 'test', actor_type: 'human',
                agent_id: null, model_id: null, confidence: null,
                updated_by: 'test', updated_actor_type: 'human'
            })
            CREATE (c)-[:HAS_WORKER]->(w)
            """,
            {
                "company_id": company_id,
                "worker_id": worker_id,
                "first_name": first_name,
                "role": role,
                "now": now,
            },
        )
        if expiry_date:
            session.run(
                """
                MATCH (w:Worker {id: $worker_id})
                CREATE (cert:Certification {
                    id: $cert_id, certification_type: $cert_type,
                    expiry_date: $expiry_date, status: 'active',
                    issue_date: '2024-01-01'
                })
                CREATE (w)-[:HOLDS_CERT]->(cert)
                """,
                {
                    "worker_id": worker_id,
                    "cert_id": f"cert_{worker_id}",
                    "cert_type": cert_type,
                    "expiry_date": expiry_date,
                },
            )


def _create_document(
    driver: Driver,
    company_id: str,
    doc_id: str,
    title: str,
    doc_type: str = "sssp",
) -> None:
    """Helper to create a Document node linked to a company."""
    now = datetime.now(timezone.utc).isoformat()
    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (d:Document {
                id: $doc_id, title: $title, document_type: $doc_type,
                status: 'draft', deleted: false,
                _content_json: '{}', _project_info_json: '{}',
                created_at: $now, updated_at: $now,
                created_by: 'test', updated_by: 'test',
                actor_type: 'human', updated_actor_type: 'human',
                agent_id: null, model_id: null, confidence: null,
                generated_at: null, pdf_url: null
            })
            CREATE (c)-[:HAS_DOCUMENT]->(d)
            """,
            {
                "company_id": company_id,
                "doc_id": doc_id,
                "title": title,
                "doc_type": doc_type,
                "now": now,
            },
        )


def _create_inspection(
    driver: Driver,
    company_id: str,
    project_id: str,
    insp_id: str,
    created_at: str | None = None,
) -> None:
    """Helper to create an Inspection node linked to a project."""
    now = created_at or datetime.now(timezone.utc).isoformat()
    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (i:Inspection {
                id: $insp_id, inspection_type: 'daily',
                inspection_date: $today, inspector_name: 'Test Inspector',
                overall_status: 'pass', deleted: false,
                _items_json: '[]',
                created_at: $now, updated_at: $now,
                created_by: 'test', updated_by: 'test',
                actor_type: 'human', updated_actor_type: 'human',
                agent_id: null, model_id: null, confidence: null
            })
            CREATE (p)-[:HAS_INSPECTION]->(i)
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "insp_id": insp_id,
                "today": date.today().isoformat(),
                "now": now,
            },
        )


def _create_toolbox_talk(
    driver: Driver,
    company_id: str,
    project_id: str,
    talk_id: str,
    scheduled_date: str | None = None,
) -> None:
    """Helper to create a ToolboxTalk node linked to a project."""
    now = datetime.now(timezone.utc).isoformat()
    sched = scheduled_date or date.today().isoformat()
    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (t:ToolboxTalk {
                id: $talk_id, topic: 'Test Topic',
                scheduled_date: $sched, status: 'completed', deleted: false,
                _attendee_ids_json: '[]', _sign_offs_json: '[]',
                created_at: $now, updated_at: $now,
                created_by: 'test', updated_by: 'test',
                actor_type: 'human', updated_actor_type: 'human',
                agent_id: null, model_id: null, confidence: null
            })
            CREATE (p)-[:HAS_TOOLBOX_TALK]->(t)
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "sched": sched,
                "now": now,
            },
        )


def _create_mock_inspection_result(
    driver: Driver,
    company_id: str,
    result_id: str,
    score: int,
    grade: str,
    created_at: str | None = None,
) -> None:
    """Helper to create a MockInspectionResult node."""
    now = created_at or datetime.now(timezone.utc).isoformat()
    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (r:MockInspectionResult {
                id: $result_id, overall_score: $score, grade: $grade,
                total_findings: 0, critical_findings: 0,
                high_findings: 0, medium_findings: 0,
                low_findings: 0, info_findings: 0,
                _findings_json: '[]', _areas_checked_json: '[]',
                executive_summary: 'Test summary',
                deep_audit: false, documents_reviewed: 0,
                training_records_reviewed: 0, inspections_reviewed: 0,
                created_at: $now, created_by: 'test'
            })
            CREATE (c)-[:HAS_MOCK_INSPECTION]->(r)
            """,
            {
                "company_id": company_id,
                "result_id": result_id,
                "score": score,
                "grade": grade,
                "now": now,
            },
        )


# ===========================================================================
# Tests
# ===========================================================================


class TestAssembleLightweight:
    """Tests for lightweight count-only assembly."""

    def test_empty_company(self, context_assembler, test_company):
        """Returns zero counts for a company with no data."""
        ctx = context_assembler.assemble_lightweight(test_company["id"])
        assert ctx.company_id == test_company["id"]
        assert ctx.project_counts.total == 0
        assert ctx.worker_counts.total == 0
        assert ctx.document_counts.total == 0
        assert ctx.latest_mock is None

    def test_counts_reflect_nodes(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """Counts reflect created graph nodes."""
        _create_worker_with_cert(
            neo4j_driver, test_company["id"], "wkr_1", "Alice",
            expiry_date=(date.today() + timedelta(days=60)).isoformat(),
        )
        _create_document(
            neo4j_driver, test_company["id"], "doc_1", "Safety Plan", "sssp"
        )

        ctx = context_assembler.assemble_lightweight(test_company["id"])
        assert ctx.project_counts.total == 1
        assert ctx.project_counts.active == 1
        assert ctx.worker_counts.total == 1
        assert ctx.worker_counts.active == 1
        assert ctx.document_counts.total == 1

    def test_expired_cert_counted(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Expired certifications are counted correctly."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        _create_worker_with_cert(
            neo4j_driver, test_company["id"], "wkr_exp", "Expired Worker",
            expiry_date=yesterday,
        )

        ctx = context_assembler.assemble_lightweight(test_company["id"])
        assert ctx.worker_counts.expired_certs == 1
        assert ctx.worker_counts.has_training_records is True

    def test_expiring_cert_counted(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Expiring-soon certifications are counted correctly."""
        in_10_days = (date.today() + timedelta(days=10)).isoformat()
        _create_worker_with_cert(
            neo4j_driver, test_company["id"], "wkr_soon", "Expiring Worker",
            expiry_date=in_10_days,
        )

        ctx = context_assembler.assemble_lightweight(test_company["id"])
        assert ctx.worker_counts.expiring_certs == 1

    def test_latest_mock_returned(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Returns the most recent mock inspection result."""
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        _create_mock_inspection_result(
            neo4j_driver, test_company["id"], "mock_old", 60, "C",
            created_at=old_time,
        )
        _create_mock_inspection_result(
            neo4j_driver, test_company["id"], "mock_new", 85, "B",
        )

        ctx = context_assembler.assemble_lightweight(test_company["id"])
        assert ctx.latest_mock is not None
        assert ctx.latest_mock.score == 85
        assert ctx.latest_mock.grade == "B"


class TestAssembleActivityCounts:
    """Tests for cross-project activity aggregation."""

    def test_empty_company(self, context_assembler, test_company):
        """Returns zero activity counts for a company with no data."""
        ctx = context_assembler.assemble_activity_counts(test_company["id"])
        assert ctx.activity_counts.total_inspections == 0
        assert ctx.activity_counts.total_talks == 0
        assert ctx.activity_counts.total_hazard_reports == 0
        assert ctx.activity_counts.total_incidents == 0

    def test_inspections_counted(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """Inspections are counted across projects."""
        _create_inspection(
            neo4j_driver, test_company["id"], test_project["id"], "insp_1"
        )
        _create_inspection(
            neo4j_driver, test_company["id"], test_project["id"], "insp_2"
        )

        ctx = context_assembler.assemble_activity_counts(test_company["id"])
        assert ctx.activity_counts.total_inspections == 2
        assert ctx.activity_counts.inspections_this_month == 2

    def test_talks_counted(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """Toolbox talks are counted across projects."""
        _create_toolbox_talk(
            neo4j_driver, test_company["id"], test_project["id"], "talk_1"
        )

        ctx = context_assembler.assemble_activity_counts(test_company["id"])
        assert ctx.activity_counts.total_talks == 1
        assert ctx.activity_counts.talks_this_month == 1


class TestAssembleFull:
    """Tests for full object assembly."""

    def test_documents_returned(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Full assembly returns document list."""
        _create_document(neo4j_driver, test_company["id"], "doc_a", "Fall Protection Plan", "fall_protection")
        _create_document(neo4j_driver, test_company["id"], "doc_b", "Safety Program", "sssp")

        ctx = context_assembler.assemble_full(test_company["id"])
        assert len(ctx.documents) == 2
        titles = {d.title for d in ctx.documents}
        assert "Fall Protection Plan" in titles
        assert "Safety Program" in titles

    def test_content_excluded_by_default(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Document content is None when include_content=False."""
        _create_document(neo4j_driver, test_company["id"], "doc_c", "Test Doc")

        ctx = context_assembler.assemble_full(test_company["id"], include_content=False)
        assert ctx.documents[0].content is None

    def test_content_included_when_requested(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Document content populated when include_content=True."""
        _create_document(neo4j_driver, test_company["id"], "doc_d", "Test Doc")

        ctx = context_assembler.assemble_full(test_company["id"], include_content=True)
        assert ctx.documents[0].content is not None

    def test_workers_with_certs(
        self, context_assembler, neo4j_driver, test_company
    ):
        """Workers include nested certification data."""
        _create_worker_with_cert(
            neo4j_driver, test_company["id"], "wkr_full", "Bob",
            cert_type="osha_30",
            expiry_date=(date.today() + timedelta(days=90)).isoformat(),
        )

        ctx = context_assembler.assemble_full(test_company["id"])
        assert len(ctx.workers) == 1
        assert ctx.workers[0].first_name == "Bob"
        assert len(ctx.workers[0].certifications) == 1
        assert ctx.workers[0].certifications[0]["certification_type"] == "osha_30"

    def test_project_activity_detected(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """Recent inspection/talk activity detected per project."""
        _create_inspection(
            neo4j_driver, test_company["id"], test_project["id"], "insp_act"
        )

        ctx = context_assembler.assemble_full(test_company["id"])
        assert len(ctx.project_activity) == 1
        assert ctx.project_activity[0].has_recent_inspection is True


class TestAssembleProjectScoped:
    """Tests for project-scoped assembly (morning brief)."""

    def test_recent_inspection_detected(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """has_recent_inspection is True when inspection exists within cutoff."""
        _create_inspection(
            neo4j_driver, test_company["id"], test_project["id"], "insp_recent"
        )

        ctx = context_assembler.assemble_project_scoped(
            test_company["id"], test_project["id"], inspection_days=2
        )
        assert len(ctx.project_activity) == 1
        assert ctx.project_activity[0].has_recent_inspection is True

    def test_no_recent_inspection(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """has_recent_inspection is False when no recent inspection."""
        # Create an old inspection (10 days ago)
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        _create_inspection(
            neo4j_driver, test_company["id"], test_project["id"],
            "insp_old", created_at=old_date,
        )

        ctx = context_assembler.assemble_project_scoped(
            test_company["id"], test_project["id"], inspection_days=2
        )
        assert ctx.project_activity[0].has_recent_inspection is False

    def test_cert_counts_company_wide(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """Cert counts come from company-wide workers."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        _create_worker_with_cert(
            neo4j_driver, test_company["id"], "wkr_scope", "Scoped Worker",
            expiry_date=yesterday,
        )

        ctx = context_assembler.assemble_project_scoped(
            test_company["id"], test_project["id"]
        )
        assert ctx.worker_counts.expired_certs == 1

    def test_recent_talk_detected(
        self, context_assembler, neo4j_driver, test_company, test_project
    ):
        """has_recent_talk is True when talk exists within cutoff."""
        _create_toolbox_talk(
            neo4j_driver, test_company["id"], test_project["id"], "talk_recent",
            scheduled_date=date.today().isoformat(),
        )

        ctx = context_assembler.assemble_project_scoped(
            test_company["id"], test_project["id"], talk_days=7
        )
        assert ctx.project_activity[0].has_recent_talk is True
