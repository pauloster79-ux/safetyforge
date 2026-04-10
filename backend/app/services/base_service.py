"""Base service class for Neo4j-backed services.

Provides common infrastructure shared by all domain services:
- Neo4j driver access and transaction helpers
- ID generation with domain prefixes
- Provenance field generation for create/update mutations
"""

import secrets
from datetime import datetime, timezone
from typing import Any

from neo4j import Driver, Session, ManagedTransaction

from app.models.actor import Actor


class BaseService:
    """Base class for all Neo4j-backed domain services.

    Attributes:
        driver: The Neo4j driver instance for database access.
    """

    def __init__(self, driver: Driver) -> None:
        """Initialise the service with a Neo4j driver.

        Args:
            driver: A Neo4j Driver with connection pooling.
        """
        self.driver = driver

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with a domain prefix.

        Args:
            prefix: Short prefix identifying the entity type (e.g. 'comp', 'proj').

        Returns:
            A string like 'comp_a1b2c3d4e5f6g7h8'.
        """
        return f"{prefix}_{secrets.token_hex(8)}"

    def _provenance_create(self, actor: Actor) -> dict[str, Any]:
        """Generate provenance fields for a new entity.

        Every created entity records who created it, when, and whether
        the creator was a human or agent.

        Args:
            actor: The actor performing the creation.

        Returns:
            A dict of provenance fields to merge into the node properties.
        """
        now = datetime.now(timezone.utc).isoformat()
        return {
            "created_by": actor.id,
            "actor_type": actor.type,
            "agent_id": actor.agent_id,
            "model_id": None,
            "confidence": None,
            "created_at": now,
            "updated_by": actor.id,
            "updated_actor_type": actor.type,
            "updated_at": now,
        }

    def _provenance_update(self, actor: Actor) -> dict[str, Any]:
        """Generate provenance fields for an entity update.

        Only updates the 'updated_*' fields — original creation
        provenance is preserved.

        Args:
            actor: The actor performing the update.

        Returns:
            A dict of update provenance fields.
        """
        now = datetime.now(timezone.utc).isoformat()
        return {
            "updated_by": actor.id,
            "updated_actor_type": actor.type,
            "updated_at": now,
        }

    def _session(self, **kwargs: Any) -> Session:
        """Open a Neo4j session using the service's driver.

        Args:
            **kwargs: Additional keyword arguments passed to driver.session().

        Returns:
            A Neo4j Session.
        """
        return self.driver.session(**kwargs)

    def _read_tx(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a read query in an auto-managed transaction.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            List of result record dicts.
        """
        def _work(tx: ManagedTransaction) -> list[dict[str, Any]]:
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        with self._session() as session:
            return session.execute_read(_work)

    def _write_tx(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a write query in an auto-managed transaction.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            List of result record dicts.
        """
        def _work(tx: ManagedTransaction) -> list[dict[str, Any]]:
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        with self._session() as session:
            return session.execute_write(_work)

    def _write_tx_single(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a write query and return a single result.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            A single record dict, or None if no results.
        """
        results = self._write_tx(query, parameters)
        return results[0] if results else None

    def _read_tx_single(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a read query and return a single result.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            A single record dict, or None if no results.
        """
        results = self._read_tx(query, parameters)
        return results[0] if results else None
