"""Backfill AuditEvent nodes for existing entities.

Creates a synthetic 'entity.created' event for every entity that doesn't
already have one. Uses the entity's own created_at / created_by fields
to reconstruct what happened. Run once after deploying the audit system.

Usage:
    python -m scripts.backfill_audit_events --uri bolt://localhost:7687
"""

import argparse
import logging
import secrets
from typing import Any

from neo4j import Driver, GraphDatabase, ManagedTransaction

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# Every entity type that should have an activity stream.
# Format: (label, match_clause_no_return, summary_template)
# match_clause must bind `e` (entity) and `c` (company) but NOT include RETURN.
ENTITY_TYPES: list[tuple[str, str, str]] = [
    (
        "Project",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(e:Project)",
        "Created project: {name}",
    ),
    (
        "WorkItem",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_WORK_ITEM]->(e:WorkItem)",
        "Created work item: {name}",
    ),
    (
        "Inspection",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INSPECTION]->(e:Inspection)",
        "Created {category} inspection",
    ),
    (
        "Incident",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INCIDENT]->(e:Incident)",
        "Reported {severity} incident",
    ),
    (
        "DailyLog",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_DAILY_LOG]->(e:DailyLog)",
        "Created daily log for {log_date}",
    ),
    (
        "ToolboxTalk",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_TOOLBOX_TALK]->(e:ToolboxTalk)",
        "Scheduled toolbox talk: {topic}",
    ),
    (
        "HazardReport",
        "MATCH (c:Company)-[:OWNS_PROJECT]->(p:Project)-[:HAS_HAZARD_REPORT]->(e:HazardReport)",
        "Reported hazard: {title}",
    ),
    (
        "Worker",
        "MATCH (c:Company)-[:EMPLOYS]->(e:Worker)",
        "Added worker: {first_name} {last_name}",
    ),
    (
        "Equipment",
        "MATCH (c:Company)-[:HAS_EQUIPMENT]->(e:Equipment)",
        "Added equipment: {name}",
    ),
]


def _generate_id() -> str:
    return f"evt_{secrets.token_hex(8)}"


def _build_summary(template: str, entity_props: dict[str, Any]) -> str:
    """Build a summary string, safely handling missing properties."""
    try:
        return template.format_map(
            {k: (v or "unknown") for k, v in entity_props.items()}
        )
    except KeyError:
        return f"Created {entity_props.get('id', 'entity')}"


def backfill_entity_type(
    driver: Driver,
    label: str,
    match_query: str,
    summary_template: str,
    database: str = "neo4j",
) -> int:
    """Backfill audit events for one entity type.

    Args:
        driver: Neo4j driver.
        label: Node label (e.g. 'Project').
        match_query: Cypher fragment to find entities + company_id.
        summary_template: Python format string for summary.
        database: Neo4j database name.

    Returns:
        Number of events created.
    """
    # Find entities without an existing 'entity.created' audit event
    # Use OPTIONAL MATCH + WHERE null pattern for Neo4j Community compatibility
    find_query = f"""
        {match_query}
        OPTIONAL MATCH (e)-[:EMITTED]->(existing:AuditEvent {{event_type: 'entity.created'}})
        WITH e, c.id AS company_id, existing
        WHERE existing IS NULL
        RETURN e {{.*}} AS entity, company_id
    """

    with driver.session(database=database) as session:
        records = session.run(find_query).data()

    if not records:
        logger.info("  %s: 0 entities need backfill", label)
        return 0

    def _create_events(tx: ManagedTransaction, batch: list[dict]) -> None:
        for rec in batch:
            entity = rec["entity"]
            company_id = rec["company_id"]
            entity_id = entity.get("id")
            if not entity_id:
                continue

            event_id = _generate_id()
            summary = _build_summary(summary_template, entity)

            tx.run(
                f"""
                MATCH (e:{label} {{id: $entity_id}})
                CREATE (ev:AuditEvent {{
                    id: $event_id,
                    event_type: 'entity.created',
                    entity_id: $entity_id,
                    entity_type: $label,
                    company_id: $company_id,
                    occurred_at: COALESCE(e.created_at, datetime().epochMillis),
                    actor_type: COALESCE(e.actor_type, 'human'),
                    actor_id: COALESCE(e.created_by, 'backfill'),
                    agent_id: e.agent_id,
                    agent_version: null,
                    model_id: e.model_id,
                    confidence: e.confidence,
                    cost_cents: null,
                    summary: $summary,
                    changes: null,
                    prev_state: null,
                    new_state: null,
                    caused_by_event_id: null,
                    related_entity_ids: null
                }})
                CREATE (e)-[:EMITTED]->(ev)
                """,
                entity_id=entity_id,
                event_id=event_id,
                label=label,
                company_id=company_id,
                summary=summary,
            )

    # Process in batches of 100
    batch_size = 100
    with driver.session(database=database) as session:
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            session.execute_write(_create_events, batch)

    logger.info("  %s: %d audit events created", label, len(records))
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill AuditEvent nodes for existing entities",
    )
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7687",
        help="Neo4j connection URI (default: bolt://localhost:7687)",
    )
    parser.add_argument("--user", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="password", help="Neo4j password")
    parser.add_argument("--database", default="neo4j", help="Neo4j database name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count entities needing backfill without creating events",
    )
    args = parser.parse_args()

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    logger.info("Connected to %s", args.uri)

    total = 0
    for label, match_query, summary_template in ENTITY_TYPES:
        if args.dry_run:
            # Just count
            find_query = f"""
                {match_query}
                OPTIONAL MATCH (e)-[:EMITTED]->(existing:AuditEvent {{event_type: 'entity.created'}})
                WITH e, existing
                WHERE existing IS NULL
                RETURN count(e) AS cnt
            """
            with driver.session(database=args.database) as session:
                result = session.run(find_query).single()
                count = result["cnt"] if result else 0
            logger.info("  %s: %d entities need backfill", label, count)
            total += count
        else:
            total += backfill_entity_type(
                driver, label, match_query, summary_template, args.database,
            )

    action = "would create" if args.dry_run else "created"
    logger.info("Done. %s %d audit events total.", action.capitalize(), total)
    driver.close()


if __name__ == "__main__":
    main()
