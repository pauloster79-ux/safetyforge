"""Neo4j driver singleton and connection management.

Provides a managed Neo4j driver instance with connection pooling,
health checking, and transaction helpers for the Kerf backend.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, AsyncTransaction
from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import get_settings

logger = logging.getLogger(__name__)

_async_driver: AsyncDriver | None = None
_sync_driver: Driver | None = None


def get_sync_driver() -> Driver:
    """Return a singleton synchronous Neo4j driver instance.

    Creates the driver on first call using settings from config.
    Subsequent calls return the same driver.

    Returns:
        A Neo4j synchronous driver with connection pooling.

    Raises:
        ServiceUnavailable: If the Neo4j server cannot be reached.
        AuthError: If the credentials are invalid.
    """
    global _sync_driver
    if _sync_driver is None:
        settings = get_settings()
        _sync_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            database=settings.neo4j_database,
            max_connection_pool_size=settings.neo4j_max_pool_size,
            connection_acquisition_timeout=30,
        )
        logger.info(
            "Neo4j sync driver created (uri=%s, database=%s)",
            settings.neo4j_uri,
            settings.neo4j_database,
        )
    return _sync_driver


async def get_async_driver() -> AsyncDriver:
    """Return a singleton asynchronous Neo4j driver instance.

    Creates the driver on first call using settings from config.
    Subsequent calls return the same driver.

    Returns:
        A Neo4j async driver with connection pooling.

    Raises:
        ServiceUnavailable: If the Neo4j server cannot be reached.
        AuthError: If the credentials are invalid.
    """
    global _async_driver
    if _async_driver is None:
        settings = get_settings()
        _async_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            database=settings.neo4j_database,
            max_connection_pool_size=settings.neo4j_max_pool_size,
            connection_acquisition_timeout=30,
        )
        logger.info(
            "Neo4j async driver created (uri=%s, database=%s)",
            settings.neo4j_uri,
            settings.neo4j_database,
        )
    return _async_driver


async def close_async_driver() -> None:
    """Close the async driver and release all connections.

    Safe to call even if the driver was never created.
    """
    global _async_driver
    if _async_driver is not None:
        await _async_driver.close()
        _async_driver = None
        logger.info("Neo4j async driver closed")


def close_sync_driver() -> None:
    """Close the sync driver and release all connections.

    Safe to call even if the driver was never created.
    """
    global _sync_driver
    if _sync_driver is not None:
        _sync_driver.close()
        _sync_driver = None
        logger.info("Neo4j sync driver closed")


async def check_neo4j_health() -> dict[str, Any]:
    """Check Neo4j connectivity and return server info.

    Returns:
        A dict with connection status and server details.
    """
    try:
        driver = await get_async_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS healthy")
            record = await result.single()
            server_info = await driver.get_server_info()
            return {
                "status": "healthy",
                "server": str(server_info.address),
                "agent": server_info.agent,
                "protocol_version": str(server_info.protocol_version),
            }
    except ServiceUnavailable as exc:
        logger.error("Neo4j health check failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}
    except AuthError as exc:
        logger.error("Neo4j auth failed: %s", exc)
        return {"status": "auth_error", "error": str(exc)}
    except Exception as exc:
        logger.error("Neo4j health check unexpected error: %s", exc)
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Transaction helpers
# ---------------------------------------------------------------------------


@contextmanager
def neo4j_session(database: str | None = None) -> Session:
    """Context manager for a synchronous Neo4j session.

    Args:
        database: Optional database name override.

    Yields:
        A Neo4j Session.
    """
    driver = get_sync_driver()
    settings = get_settings()
    db = database or settings.neo4j_database
    session = driver.session(database=db)
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def async_neo4j_session(database: str | None = None):
    """Context manager for an asynchronous Neo4j session.

    Args:
        database: Optional database name override.

    Yields:
        A Neo4j AsyncSession.
    """
    driver = await get_async_driver()
    settings = get_settings()
    db = database or settings.neo4j_database
    session = driver.session(database=db)
    try:
        yield session
    finally:
        await session.close()


def execute_read(query: str, parameters: dict[str, Any] | None = None) -> list[dict]:
    """Execute a read query and return results as a list of dicts.

    Convenience function for simple read operations.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        List of record dicts.
    """
    with neo4j_session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def execute_write(query: str, parameters: dict[str, Any] | None = None) -> list[dict]:
    """Execute a write query within a transaction and return results.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        List of record dicts.
    """
    def _work(tx: Transaction) -> list[dict]:
        result = tx.run(query, parameters or {})
        return [record.data() for record in result]

    with neo4j_session() as session:
        return session.execute_write(_work)


def execute_write_single(
    query: str, parameters: dict[str, Any] | None = None
) -> dict | None:
    """Execute a write query and return a single result dict.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        A single record dict, or None if no results.
    """
    results = execute_write(query, parameters)
    return results[0] if results else None


def execute_read_single(
    query: str, parameters: dict[str, Any] | None = None
) -> dict | None:
    """Execute a read query and return a single result dict.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        A single record dict, or None if no results.
    """
    results = execute_read(query, parameters)
    return results[0] if results else None


async def async_execute_read(
    query: str, parameters: dict[str, Any] | None = None
) -> list[dict]:
    """Execute an async read query and return results as dicts.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        List of record dicts.
    """
    async with async_neo4j_session() as session:
        result = await session.run(query, parameters or {})
        records = await result.data()
        return records


async def async_execute_write(
    query: str, parameters: dict[str, Any] | None = None
) -> list[dict]:
    """Execute an async write query within a transaction.

    Args:
        query: Cypher query string.
        parameters: Query parameters.

    Returns:
        List of record dicts.
    """
    async def _work(tx: AsyncTransaction) -> list[dict]:
        result = await tx.run(query, parameters or {})
        return await result.data()

    async with async_neo4j_session() as session:
        return await session.execute_write(_work)


def run_schema(cypher_path: str) -> None:
    """Execute a .cypher schema file against Neo4j.

    Each statement is separated by semicolons and executed individually.
    Designed for running schema.cypher (indexes, constraints).

    Args:
        cypher_path: Path to the .cypher file.
    """
    with open(cypher_path) as f:
        content = f.read()

    # Split on semicolons, filter empty statements and comments
    statements = [
        stmt.strip()
        for stmt in content.split(";")
        if stmt.strip() and not stmt.strip().startswith("//")
    ]

    with neo4j_session() as session:
        for stmt in statements:
            # Skip pure comment blocks
            lines = [
                line for line in stmt.split("\n")
                if line.strip() and not line.strip().startswith("//")
            ]
            if not lines:
                continue
            clean_stmt = "\n".join(lines)
            try:
                session.run(clean_stmt)
            except Exception as exc:
                logger.warning("Schema statement failed (may be idempotent): %s — %s", clean_stmt[:80], exc)

    logger.info("Schema applied from %s (%d statements)", cypher_path, len(statements))
