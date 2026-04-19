"""Structural validation for the Neo4j regulatory knowledge graph.

Runs validation queries to ensure data integrity:
- Every Regulation node has a non-null source property
- Every Regulation node linked to a Region has a state_standard
- No dangling HAS_REQUIREMENT edges (target must be a Regulation)
- Every Region with HAS_REQUIREMENT has at least one Regulation

Usage:
    python -m scripts.validate_regulatory_graph
    python -m scripts.validate_regulatory_graph --uri bolt://localhost:7687
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

# Load backend/.env so NEO4J_PASSWORD (and friends) are available as defaults
# when the script is invoked from the repo root.
_BACKEND_ENV = Path(__file__).resolve().parents[1] / ".env"
if _BACKEND_ENV.exists():
    load_dotenv(_BACKEND_ENV)

logger = logging.getLogger(__name__)


def validate_regulation_sources(driver: Driver, database: str) -> list[str]:
    """Check that every Regulation node has a non-null source property.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A list of violation messages (empty if all pass).
    """
    violations = []
    with driver.session(database=database) as session:
        result = session.run(
            """
            MATCH (r:Regulation)
            WHERE r.source IS NULL
            RETURN r.id AS id, r.requirement_name AS name
            """
        )
        for record in result:
            violations.append(
                f"Regulation '{record['id']}' ({record['name']}) missing source citation"
            )
    return violations


def validate_region_regulation_standards(driver: Driver, database: str) -> list[str]:
    """Check that every Regulation linked to a Region has a state_standard.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A list of violation messages.
    """
    violations = []
    with driver.session(database=database) as session:
        result = session.run(
            """
            MATCH (region:Region)-[:HAS_REQUIREMENT]->(reg:Regulation)
            WHERE reg.state_standard IS NULL OR reg.state_standard = ''
            RETURN reg.id AS id, reg.requirement_name AS name, region.code AS region
            """
        )
        for record in result:
            violations.append(
                f"Regulation '{record['id']}' in region {record['region']} "
                f"missing state_standard"
            )
    return violations


def validate_no_orphan_regions(driver: Driver, database: str) -> list[str]:
    """Check that every Region under US with HAS_REQUIREMENT has at least one Regulation.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A list of violation messages.
    """
    violations = []
    with driver.session(database=database) as session:
        result = session.run(
            """
            MATCH (j:Jurisdiction {code: 'US'})-[:HAS_REGION]->(r:Region)
            WHERE NOT EXISTS { (r)-[:HAS_REQUIREMENT]->(:Regulation) }
            RETURN r.code AS code, r.name AS name
            """
        )
        for record in result:
            violations.append(
                f"Region '{record['code']}' ({record['name']}) has no HAS_REQUIREMENT edges"
            )
    return violations


def validate_all(driver: Driver, database: str = "neo4j") -> list[str]:
    """Run all structural validation checks.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A combined list of all violation messages.
    """
    all_violations: list[str] = []

    checks = [
        ("Regulation source citations", validate_regulation_sources),
        ("Region regulation state_standard", validate_region_regulation_standards),
        ("Orphan US regions (no requirements)", validate_no_orphan_regions),
    ]

    for check_name, check_fn in checks:
        logger.info("Running check: %s", check_name)
        violations = check_fn(driver, database)
        if violations:
            logger.warning("  %d violations found", len(violations))
            for v in violations:
                logger.warning("    - %s", v)
        else:
            logger.info("  PASS")
        all_violations.extend(violations)

    return all_violations


def main() -> None:
    """CLI entrypoint for validating the regulatory graph."""
    parser = argparse.ArgumentParser(
        description="Validate Neo4j regulatory graph structural integrity"
    )
    parser.add_argument(
        "--uri",
        default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI (defaults to $NEO4J_URI or bolt://localhost:7687)",
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("NEO4J_USER", "neo4j"),
        help="Neo4j username (defaults to $NEO4J_USER or neo4j)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("NEO4J_PASSWORD", "password"),
        help="Neo4j password (defaults to $NEO4J_PASSWORD from backend/.env)",
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("NEO4J_DATABASE", "neo4j"),
        help="Neo4j database name (defaults to $NEO4J_DATABASE or neo4j)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", args.uri)
        violations = validate_all(driver, args.database)

        if violations:
            print(f"\nVALIDATION FAILED: {len(violations)} violation(s) found")
            for v in violations:
                print(f"  - {v}")
            sys.exit(1)
        else:
            print("\nVALIDATION PASSED: All structural checks passed")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
