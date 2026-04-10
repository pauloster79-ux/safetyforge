"""Shared test fixtures for Kerf backend tests.

Provides Neo4j driver, schema application, per-test cleanup,
service fixtures, and FastAPI TestClient with auth overrides.
"""

import os

# Set ENVIRONMENT=test early so the rate limiter is disabled at import time
os.environ["ENVIRONMENT"] = "test"

from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from neo4j import Driver, GraphDatabase

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_neo4j_driver
from app.main import app


TEST_USER = {
    "uid": "test_user_001",
    "email": "test@example.com",
    "email_verified": True,
}

TEST_SETTINGS = Settings(
    neo4j_uri=os.environ.get("NEO4J_TEST_URI", "bolt://localhost:7687"),
    neo4j_user=os.environ.get("NEO4J_TEST_USER", "neo4j"),
    neo4j_password=os.environ.get("NEO4J_TEST_PASSWORD", "password"),
    neo4j_database=os.environ.get("NEO4J_TEST_DATABASE", "neo4j"),
    anthropic_api_key="test-key",
    paddle_webhook_secret="test-paddle-webhook-secret",
    paddle_api_key="test-paddle-key",
    paddle_price_starter="pri_starter_test",
    paddle_price_professional="pri_professional_test",
    paddle_price_business="pri_business_test",
    cors_origins="http://localhost:5173",
    environment="test",
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "graph" / "schema.cypher"


# ---------------------------------------------------------------------------
# Neo4j driver (session-scoped — one driver for all tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def neo4j_driver() -> Generator[Driver, None, None]:
    """Create a Neo4j driver for the test session.

    Applies schema.cypher constraints/indexes on first use.

    Yields:
        A Neo4j Driver connected to the test database.
    """
    driver = GraphDatabase.driver(
        TEST_SETTINGS.neo4j_uri,
        auth=(TEST_SETTINGS.neo4j_user, TEST_SETTINGS.neo4j_password),
    )
    driver.verify_connectivity()

    _apply_schema(driver)

    yield driver

    driver.close()


def _apply_schema(driver: Driver) -> None:
    """Apply schema.cypher constraints and indexes.

    Each statement is executed individually. Failures are logged
    but not raised (IF NOT EXISTS makes this idempotent).

    Args:
        driver: The Neo4j driver.
    """
    if not SCHEMA_PATH.exists():
        return

    content = SCHEMA_PATH.read_text()
    statements = [
        stmt.strip()
        for stmt in content.split(";")
        if stmt.strip() and not stmt.strip().startswith("//")
    ]

    with driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        for stmt in statements:
            lines = [
                line for line in stmt.split("\n")
                if line.strip() and not line.strip().startswith("//")
            ]
            if not lines:
                continue
            clean = "\n".join(lines)
            try:
                session.run(clean)
            except Exception:
                pass  # IF NOT EXISTS handles idempotency


# ---------------------------------------------------------------------------
# Per-test cleanup — wipe all nodes after each test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cleanup_neo4j(neo4j_driver: Driver) -> Generator[None, None, None]:
    """Delete all nodes and relationships after each test.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.
    """
    yield

    with neo4j_driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run("MATCH (n) DETACH DELETE n")


# ---------------------------------------------------------------------------
# Test company and project fixtures (graph nodes)
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_company(neo4j_driver: Driver) -> dict:
    """Create a test company node and return its properties.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        A dict with the company node properties.
    """
    from app.models.actor import Actor

    actor = Actor.human(TEST_USER["uid"])
    now = datetime.now(timezone.utc).isoformat()

    company_data = {
        "id": "comp_test_000001",
        "name": "Test Construction Co",
        "address": "123 Test Street, Testville, TX 75001",
        "license_number": "TX-12345",
        "trade_type": "general",
        "owner_name": "Test Owner",
        "phone": "555-123-4567",
        "email": "owner@testconstruction.com",
        "jurisdiction_code": "US",
        "subscription_status": "active",
        "subscription_plan": "Professional",
        "created_by": actor.id,
        "actor_type": actor.type,
        "agent_id": None,
        "model_id": None,
        "confidence": None,
        "created_at": now,
        "updated_by": actor.id,
        "updated_actor_type": actor.type,
        "updated_at": now,
    }

    with neo4j_driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            "CREATE (c:Company $props) RETURN c",
            props=company_data,
        )

    return company_data


@pytest.fixture()
def test_project(neo4j_driver: Driver, test_company: dict) -> dict:
    """Create a test project node linked to the test company.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.
        test_company: The test company fixture.

    Returns:
        A dict with the project node properties.
    """
    from app.models.actor import Actor

    actor = Actor.human(TEST_USER["uid"])
    now = datetime.now(timezone.utc).isoformat()

    project_data = {
        "id": "proj_test_000001",
        "name": "Test Construction Site",
        "address": "456 Build Avenue, Construction City, TX 75002",
        "status": "active",
        "deleted": False,
        "created_by": actor.id,
        "actor_type": actor.type,
        "agent_id": None,
        "model_id": None,
        "confidence": None,
        "created_at": now,
        "updated_by": actor.id,
        "updated_actor_type": actor.type,
        "updated_at": now,
    }

    with neo4j_driver.session(database=TEST_SETTINGS.neo4j_database) as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (p:Project $props)
            CREATE (c)-[:OWNS_PROJECT]->(p)
            RETURN p
            """,
            company_id=test_company["id"],
            props=project_data,
        )

    return project_data


# ---------------------------------------------------------------------------
# FastAPI TestClient with DI overrides
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(neo4j_driver: Driver) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient with auth and Neo4j overrides.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Yields:
        A TestClient configured for testing.
    """

    async def override_get_current_user() -> dict:
        return TEST_USER

    def override_get_neo4j_driver() -> Driver:
        return neo4j_driver

    def override_get_settings() -> Settings:
        return TEST_SETTINGS

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_neo4j_driver] = override_get_neo4j_driver
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Service fixtures for tests that need direct service access
# ---------------------------------------------------------------------------


@pytest.fixture()
def company_service(neo4j_driver: Driver) -> "CompanyService":
    """Provide a CompanyService instance for direct test usage.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        A CompanyService instance.
    """
    from app.services.company_service import CompanyService
    return CompanyService(neo4j_driver)


@pytest.fixture()
def document_service(neo4j_driver: Driver) -> "DocumentService":
    """Provide a DocumentService instance for direct test usage.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        A DocumentService instance.
    """
    from app.services.document_service import DocumentService
    return DocumentService(neo4j_driver)


@pytest.fixture()
def billing_service(neo4j_driver: Driver) -> "BillingService":
    """Provide a BillingService instance for direct test usage.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        A BillingService instance.
    """
    from app.services.billing_service import BillingService
    return BillingService(neo4j_driver, TEST_SETTINGS)


@pytest.fixture()
def context_assembler(neo4j_driver: Driver) -> "ContextAssemblerService":
    """Provide a ContextAssemblerService instance for direct test usage.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        A ContextAssemblerService instance.
    """
    from app.services.context_assembler import ContextAssemblerService
    return ContextAssemblerService(neo4j_driver)
