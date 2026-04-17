"""Base service class for Neo4j-backed services.

Provides common infrastructure shared by all domain services:
- Neo4j driver access and transaction helpers
- ID generation with domain prefixes
- Provenance field generation for create/update mutations
- Audit event emission for mutations and state transitions
"""

import json
import re
import secrets
from datetime import datetime, timezone
from typing import Any

from neo4j import Driver, Session, ManagedTransaction

from app.models.actor import Actor


# Valid Neo4j label identifier (letter followed by alphanumerics).
# Used to sanitise entity_type values before string-interpolating them
# into Cypher queries in _emit_audit.
_VALID_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


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
        the creator was a human or agent.  When the actor is an agent,
        model_id, confidence, agent_cost_cents, and agent_version are
        read from the Actor instance so the provenance trail is complete.

        The cost field is named ``agent_cost_cents`` (not ``cost_cents``)
        to avoid colliding with domain cost fields on nodes like Labour
        and Item.

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
            "agent_version": actor.agent_version,
            "model_id": actor.model_id,
            "confidence": actor.confidence,
            "agent_cost_cents": actor.cost_cents,
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

    def _emit_audit(
        self,
        event_type: str,
        entity_id: str,
        entity_type: str,
        company_id: str,
        actor: Actor,
        summary: str,
        changes: dict[str, Any] | None = None,
        prev_state: str | None = None,
        new_state: str | None = None,
        related_entity_ids: list[str] | None = None,
        caused_by_event_id: str | None = None,
    ) -> str:
        """Emit an AuditEvent node linked to the entity via EMITTED.

        Creates an append-only event record for any mutation on a tenant-scoped
        entity. See docs/design/phase-0-foundations.md §3.3.

        Args:
            event_type: One of 'entity.created', 'entity.updated',
                'state.transitioned', 'entity.archived', 'field.changed',
                'relationship.added', 'relationship.removed'.
            entity_id: ID of the entity the event concerns.
            entity_type: Neo4j node label (e.g. 'WorkItem', 'Project'). Validated
                against an alphanumeric pattern to prevent injection.
            company_id: Tenant scope.
            actor: Who performed the action (human or agent).
            summary: Human-readable one-liner (e.g. 'Moved WorkItem to in_progress').
            changes: Optional dict shaped as { 'field_name': { 'from': old, 'to': new } }.
            prev_state: Previous state for state.transitioned events.
            new_state: New state for state.transitioned events.
            related_entity_ids: Additional entities referenced by this event.
            caused_by_event_id: Parent event ID for causal chains.

        Returns:
            The newly created event ID (prefix 'evt_').

        Raises:
            ValueError: If entity_type is not a valid Neo4j label identifier, or
                if the target entity cannot be found.
        """
        if not _VALID_LABEL_RE.match(entity_type):
            raise ValueError(
                f"Invalid entity_type (not a valid Neo4j label): {entity_type!r}"
            )

        event_id = self._generate_id("evt")
        now = datetime.now(timezone.utc).isoformat()
        # Neo4j has no nested-dict property type — serialise as JSON string
        changes_json = json.dumps(changes) if changes is not None else None

        props: dict[str, Any] = {
            "id": event_id,
            "event_type": event_type,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "company_id": company_id,
            "occurred_at": now,
            "actor_type": actor.type,
            "actor_id": actor.id,
            "agent_id": actor.agent_id,
            "agent_version": actor.agent_version,
            "model_id": actor.model_id,
            "confidence": actor.confidence,
            "cost_cents": actor.cost_cents,
            "summary": summary,
            "changes": changes_json,
            "prev_state": prev_state,
            "new_state": new_state,
            "caused_by_event_id": caused_by_event_id,
            "related_entity_ids": related_entity_ids,
        }

        # Label interpolation is safe: entity_type is validated above against
        # _VALID_LABEL_RE which rejects anything non-alphanumeric.
        result = self._write_tx_single(
            f"""
            MATCH (e:{entity_type} {{id: $entity_id}})
            CREATE (ev:AuditEvent $props)
            CREATE (e)-[:EMITTED]->(ev)
            WITH ev
            OPTIONAL MATCH (a:AgentIdentity {{agent_id: $agent_id}})
            FOREACH (_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END |
                CREATE (ev)-[:PERFORMED_BY]->(a)
            )
            RETURN ev.id AS event_id
            """,
            {
                "entity_id": entity_id,
                "props": props,
                "agent_id": actor.agent_id,
            },
        )
        if result is None:
            raise ValueError(
                f"Entity {entity_type}:{entity_id} not found when emitting audit event"
            )
        return event_id
