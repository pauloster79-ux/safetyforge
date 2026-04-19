"""Load canonical WorkCategory trees from jurisdiction YAML seed files.

Reads ``backend/jurisdictions/{code}/work_categories.yaml`` for each Wave 1
jurisdiction and upserts the nodes + PARENT_CATEGORY hierarchy into Neo4j.

Canonical categories carry the :Canonical label (in addition to :WorkCategory)
and are shared across all tenants. Extension categories (company-scoped leaves)
are created separately via the work_category_service — not by this loader.

The loader is idempotent: re-running it MERGEs by (jurisdiction_code, code)
so seed data can be refreshed without duplicating nodes.

``inherits_from`` stubs (CA, IE, NZ) delegate to their parent jurisdiction's
tree: the loader copies the parent's canonical nodes under the stub jurisdiction
and applies any declared label_overrides.

Usage:
    python -m backend.scripts.load_canonical_work_categories
"""

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from neo4j import Driver, GraphDatabase


# Wave 1 jurisdictions — order matters because inherits_from needs the parent
# loaded first.
WAVE_1_ORDER = ["us", "ca", "uk", "ie", "au", "nz"]

JURISDICTIONS_DIR = Path(__file__).resolve().parent.parent / "jurisdictions"


def _load_yaml(code: str) -> dict[str, Any]:
    """Load a jurisdiction's work_categories.yaml.

    Args:
        code: Jurisdiction code (e.g. 'us').

    Returns:
        Parsed YAML as a dict.

    Raises:
        FileNotFoundError: If the YAML file doesn't exist.
    """
    path = JURISDICTIONS_DIR / code / "work_categories.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No work_categories.yaml for jurisdiction '{code}' at {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _flatten_categories(
    tree: list[dict[str, Any]],
    parent_code: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten a hierarchical category tree into a list of (node, parent) records.

    Args:
        tree: List of category dicts with optional ``children``.
        parent_code: Code of the parent node (None for top-level).

    Returns:
        Flat list of dicts with keys: code, name, level, parent_code, activity_refs.
    """
    flat: list[dict[str, Any]] = []
    for entry in tree:
        flat.append(
            {
                "code": entry["code"],
                "name": entry["name"],
                "level": entry.get("level", 1),
                "parent_code": parent_code,
                "unit_note": entry.get("unit_note"),
                "activity_refs": entry.get("activity_refs") or [],
            }
        )
        children = entry.get("children") or []
        if children:
            flat.extend(_flatten_categories(children, parent_code=entry["code"]))
    return flat


def _upsert_canonical_nodes(
    driver: Driver,
    jurisdiction_code: str,
    source_reference: str,
    version: str,
    nodes: list[dict[str, Any]],
) -> int:
    """Upsert a flat list of canonical category nodes for one jurisdiction.

    Uses MERGE on (jurisdiction_code, code) so re-running the loader
    updates titles/levels without duplicating.

    Args:
        driver: Neo4j driver.
        jurisdiction_code: The jurisdiction these nodes belong to.
        source_reference: Citation string for the taxonomy source.
        version: Taxonomy version.
        nodes: Flat list from _flatten_categories.

    Returns:
        Count of nodes upserted.
    """
    with driver.session() as session:
        result = session.execute_write(
            _upsert_canonical_tx,
            jurisdiction_code=jurisdiction_code,
            source_reference=source_reference,
            version=version,
            nodes=nodes,
        )
    return result


def _upsert_canonical_tx(
    tx: Any,
    jurisdiction_code: str,
    source_reference: str,
    version: str,
    nodes: list[dict[str, Any]],
) -> int:
    """Transaction function that does the actual upsert + PARENT_CATEGORY wiring."""
    count = 0
    for n in nodes:
        # Deterministic ID per (jurisdiction_code, code) so idempotent
        node_id = f"wcat_{jurisdiction_code}_{n['code'].replace(' ', '_').replace('.', '_')}"
        tx.run(
            """
            MERGE (c:WorkCategory:Canonical {jurisdiction_code: $jurisdiction_code, code: $code})
            ON CREATE SET
                c.id = $id,
                c.created_at = datetime()
            SET
                c.name = $name,
                c.level = $level,
                c.source_reference = $source_reference,
                c.version = $version,
                c.unit_note = $unit_note,
                c.activity_refs = $activity_refs,
                c.updated_at = datetime()
            """,
            id=node_id,
            jurisdiction_code=jurisdiction_code,
            code=n["code"],
            name=n["name"],
            level=n["level"],
            source_reference=source_reference,
            version=version,
            unit_note=n.get("unit_note"),
            activity_refs=n["activity_refs"],
        )
        count += 1

    # Second pass: wire PARENT_CATEGORY
    for n in nodes:
        if n["parent_code"] is None:
            continue
        tx.run(
            """
            MATCH (child:WorkCategory:Canonical {jurisdiction_code: $jurisdiction_code, code: $child_code})
            MATCH (parent:WorkCategory:Canonical {jurisdiction_code: $jurisdiction_code, code: $parent_code})
            MERGE (child)-[:PARENT_CATEGORY]->(parent)
            """,
            jurisdiction_code=jurisdiction_code,
            child_code=n["code"],
            parent_code=n["parent_code"],
        )
    return count


def load_jurisdiction(driver: Driver, code: str, loaded: set[str]) -> int:
    """Load a single jurisdiction's YAML (resolving inherits_from if present).

    Args:
        driver: Neo4j driver.
        code: Jurisdiction code.
        loaded: Set of already-loaded jurisdiction codes (for inherits_from resolution).

    Returns:
        Count of nodes upserted.
    """
    data = _load_yaml(code)
    source_reference = data.get("source_reference", data.get("source", "unknown"))
    version = data.get("version", "unreleased")

    # inherits_from stubs (CA → US, IE → UK, NZ → AU)
    if "inherits_from" in data:
        parent_code = data["inherits_from"]
        if parent_code not in loaded:
            raise ValueError(
                f"Jurisdiction '{code}' inherits_from '{parent_code}' but '{parent_code}' not yet loaded."
            )
        parent_data = _load_yaml(parent_code)
        categories = parent_data["categories"]
        # Apply any label_overrides from the stub
        label_overrides = (data.get("deltas") or {}).get("label_overrides") or {}
        flat = _flatten_categories(categories)
        if label_overrides:
            for n in flat:
                if n["code"] in label_overrides:
                    n["name"] = label_overrides[n["code"]]
    else:
        categories = data.get("categories") or []
        flat = _flatten_categories(categories)

    count = _upsert_canonical_nodes(
        driver,
        jurisdiction_code=code,
        source_reference=source_reference,
        version=version,
        nodes=flat,
    )
    return count


def load_all(driver: Driver, jurisdictions: list[str] | None = None) -> dict[str, int]:
    """Load all Wave 1 jurisdictions (or a specified subset).

    Args:
        driver: Neo4j driver.
        jurisdictions: Optional list of jurisdiction codes to load.
            Defaults to WAVE_1_ORDER.

    Returns:
        Dict of jurisdiction code -> node count.
    """
    codes = jurisdictions or WAVE_1_ORDER
    results: dict[str, int] = {}
    loaded: set[str] = set()
    for code in codes:
        count = load_jurisdiction(driver, code, loaded)
        results[code] = count
        loaded.add(code)
    return results


def main() -> int:
    """Entry point for `python -m backend.scripts.load_canonical_work_categories`."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "kerf-dev-password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Cannot connect to Neo4j at {uri}: {exc}", file=sys.stderr)
        return 1

    print(f"Loading canonical WorkCategory trees from {JURISDICTIONS_DIR}")
    results = load_all(driver)
    for code, count in results.items():
        print(f"  {code}: {count} categories")
    total = sum(results.values())
    print(f"Total: {total} canonical categories loaded across {len(results)} jurisdictions")
    driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
