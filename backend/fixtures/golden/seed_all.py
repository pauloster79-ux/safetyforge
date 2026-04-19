"""Orchestrator: seed regulatory graph + all 10 golden projects.

Usage:
    python -m backend.fixtures.golden.seed_all
    python -m backend.fixtures.golden.seed_all --uri bolt://localhost:7687
    python -m backend.fixtures.golden.seed_all --only gp01 gp04
    python -m backend.fixtures.golden.seed_all --clean
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Type

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

# Load backend/.env so NEO4J_PASSWORD (and friends) are available as defaults
# when the script is invoked from the repo root.
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
if _BACKEND_ENV.exists():
    load_dotenv(_BACKEND_ENV)

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.gp01_solo_handyman import GP01Seeder
from backend.fixtures.golden.gp02_deck_build import GP02Seeder
from backend.fixtures.golden.gp03_shop_fitout import GP03Seeder
from backend.fixtures.golden.gp04_custom_home import GP04Seeder
from backend.fixtures.golden.gp05_warehouse import GP05Seeder
from backend.fixtures.golden.gp06_school_reno import GP06Seeder
from backend.fixtures.golden.gp07_high_rise import GP07Seeder
from backend.fixtures.golden.gp08_bridge import GP08Seeder
from backend.fixtures.golden.gp09_incident import GP09Seeder
from backend.fixtures.golden.gp10_closeout import GP10Seeder

logger = logging.getLogger(__name__)

SEEDERS: dict[str, Type[GoldenProjectSeeder]] = {
    "gp01": GP01Seeder,
    "gp02": GP02Seeder,
    "gp03": GP03Seeder,
    "gp04": GP04Seeder,
    "gp05": GP05Seeder,
    "gp06": GP06Seeder,
    "gp07": GP07Seeder,
    "gp08": GP08Seeder,
    "gp09": GP09Seeder,
    "gp10": GP10Seeder,
}


def clean_golden_data(driver: Driver, database: str = "neo4j") -> int:
    """Remove all nodes tagged with source='golden_project'.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        Number of nodes deleted.
    """
    with driver.session(database=database) as session:
        result = session.run(
            """
            MATCH (n {source: 'golden_project'})
            DETACH DELETE n
            RETURN count(n) AS deleted
            """,
        )
        record = result.single()
        count = record["deleted"] if record else 0

    logger.info("Cleaned %d golden project nodes", count)
    return count


def seed_regulatory_graph(driver: Driver, database: str = "neo4j") -> None:
    """Seed the regulatory knowledge graph (prerequisite for golden projects).

    Args:
        driver: Neo4j driver.
        database: Target database name.
    """
    from backend.scripts.seed_regulatory_graph import seed_all
    counts = seed_all(driver, database)
    logger.info("Regulatory graph seeded: %s", counts)


def seed_golden_projects(
    driver: Driver,
    database: str = "neo4j",
    only: list[str] | None = None,
) -> dict[str, dict[str, int]]:
    """Seed golden project data.

    Args:
        driver: Neo4j driver.
        database: Target database name.
        only: If provided, only seed these GP slugs (e.g. ['gp01', 'gp04']).

    Returns:
        Dict of GP slug to entity counts.
    """
    results: dict[str, dict[str, int]] = {}

    slugs = only if only else list(SEEDERS.keys())
    for slug in slugs:
        seeder_cls = SEEDERS.get(slug)
        if not seeder_cls:
            logger.warning("Unknown golden project: %s", slug)
            continue

        logger.info("Seeding %s...", slug)
        seeder = seeder_cls(driver, database)
        try:
            counts = seeder.seed()
            results[slug] = counts
            logger.info("  %s complete: %s", slug, counts)
        except Exception:
            logger.exception("  %s FAILED", slug)
            results[slug] = {"error": -1}

    return results


def main() -> None:
    """CLI entrypoint for seeding golden projects."""
    parser = argparse.ArgumentParser(
        description="Seed golden project test data into Neo4j",
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
    parser.add_argument(
        "--only", nargs="+", metavar="GP",
        help="Only seed specific GPs (e.g. --only gp01 gp04)",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Remove all golden project data before seeding",
    )
    parser.add_argument(
        "--skip-regulatory", action="store_true",
        help="Skip regulatory graph seeding (if already done)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", args.uri)

        if args.clean:
            clean_golden_data(driver, args.database)

        if not args.skip_regulatory:
            seed_regulatory_graph(driver, args.database)

        results = seed_golden_projects(driver, args.database, args.only)

        print("\nGolden project seeding complete:")
        print("-" * 50)
        for slug, counts in sorted(results.items()):
            if "error" in counts:
                print(f"  {slug}: FAILED")
            else:
                total = sum(counts.values())
                print(f"  {slug}: {total} entities ({counts})")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
