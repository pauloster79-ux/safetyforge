"""Seed the Neo4j regulatory knowledge graph from jurisdiction YAML packs.

Reads the 4 jurisdiction packs (US, UK, CA, AU) and creates shared
regulatory nodes: Jurisdiction, Region, RegulatoryGroup, Regulation,
CertificationType, ComplianceProgram, DocumentType, Activity, TradeType,
Role, HazardCategory, InspectionType.

All statements use MERGE for idempotency — safe to run multiple times.
Every node carries a `source` property for citation provenance.
Aligned with Kerf Ontology v3.0.

Usage:
    python -m scripts.seed_regulatory_graph
    python -m scripts.seed_regulatory_graph --uri bolt://localhost:7687
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml
from neo4j import Driver, GraphDatabase, ManagedTransaction

logger = logging.getLogger(__name__)

JURISDICTIONS_DIR = Path(__file__).resolve().parent.parent / "jurisdictions"
JURISDICTION_CODES = ["us", "uk", "ca", "au"]


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML as a dict.
    """
    with open(path) as f:
        return yaml.safe_load(f) or {}


def seed_jurisdiction(tx: ManagedTransaction, manifest: dict[str, Any]) -> None:
    """Create a Jurisdiction node from a manifest.

    Args:
        tx: Neo4j managed transaction.
        manifest: Parsed manifest.yaml contents.
    """
    code = manifest["code"]
    tx.run(
        """
        MERGE (j:Jurisdiction {code: $code})
        SET j.name = $name,
            j.regulatory_body = $regulatory_body,
            j.primary_legislation = $primary_legislation,
            j.construction_legislation = $construction_legislation,
            j.languages = $languages,
            j.default_currency = $default_currency,
            j.measurement_system = $measurement_system,
            j.date_format = $date_format,
            j.source = $source
        """,
        code=code,
        name=manifest["name"],
        regulatory_body=manifest.get("regulatory_body", ""),
        primary_legislation=manifest.get("primary_legislation", ""),
        construction_legislation=manifest.get("construction_legislation", ""),
        languages=manifest.get("languages", ["en"]),
        default_currency=manifest.get("default_currency", "USD"),
        measurement_system=manifest.get("measurement_system", "imperial"),
        date_format=manifest.get("date_format", "MM/DD/YYYY"),
        source=f"jurisdictions/{code.lower()}/manifest.yaml",
    )


def seed_regulations(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    regulations: dict[str, Any],
) -> None:
    """Create Regulation and RegulatoryGroup nodes from a regulations.yaml.

    Handles both flat regulation lists and grouped structures (primary,
    construction, etc.).

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code (e.g. 'US').
        regulations: Parsed regulations.yaml contents.
    """
    for group_key, reg_list in regulations.items():
        if not isinstance(reg_list, list):
            continue

        group_id = f"{jurisdiction_code}_{group_key}"
        tx.run(
            """
            MERGE (g:RegulatoryGroup {id: $id})
            SET g.name = $name,
                g.jurisdiction_code = $jurisdiction_code,
                g.source = $source
            MERGE (j:Jurisdiction {code: $jurisdiction_code})
            MERGE (j)-[:HAS_GROUP]->(g)
            """,
            id=group_id,
            name=group_key.replace("_", " ").title(),
            jurisdiction_code=jurisdiction_code,
            source=f"jurisdictions/{jurisdiction_code.lower()}/regulations.yaml",
        )

        for reg in reg_list:
            reg_id = reg.get("id", "")
            reference = reg.get("short", reg_id)
            tx.run(
                """
                MERGE (r:Regulation {reference: $reference})
                SET r.id = $id,
                    r.full_name = $full_name,
                    r.jurisdiction_code = $jurisdiction_code,
                    r.group_id = $group_id,
                    r.url = $url,
                    r.enforced_by = $enforced_by,
                    r.summary = $summary,
                    r.valid_from = date('2020-01-01'),
                    r.valid_until = date('9999-12-31'),
                    r.source = $source
                MERGE (g:RegulatoryGroup {id: $group_id})
                MERGE (g)-[:BELONGS_TO_GROUP]->(r)
                """,
                reference=reference,
                id=reg_id,
                full_name=reg.get("full", reg.get("full_name", reference)),
                jurisdiction_code=jurisdiction_code,
                group_id=group_id,
                url=reg.get("url", ""),
                enforced_by=reg.get("enforced_by", ""),
                summary=reg.get("summary", ""),
                source=f"jurisdictions/{jurisdiction_code.lower()}/regulations.yaml",
            )


def seed_certifications(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create CertificationType nodes from a certifications.yaml.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed certifications.yaml contents.
    """
    certs = data.get("certifications", [])
    for cert in certs:
        cert_id = f"{jurisdiction_code}_{cert['id']}"
        tx.run(
            """
            MERGE (ct:CertificationType {id: $id})
            SET ct.name = $name,
                ct.full_name = $full_name,
                ct.jurisdiction_code = $jurisdiction_code,
                ct.expires = $expires,
                ct.validity_years = $validity_years,
                ct.required_for = $required_for,
                ct.issuing_body = $issuing_body,
                ct.source = $source
            MERGE (j:Jurisdiction {code: $jurisdiction_code})
            MERGE (j)-[:DEFINES_CERTIFICATION]->(ct)
            """,
            id=cert_id,
            name=cert.get("name", ""),
            full_name=cert.get("full_name", cert.get("name", "")),
            jurisdiction_code=jurisdiction_code,
            expires=cert.get("expires", False),
            validity_years=cert.get("validity_years", 0),
            required_for=cert.get("required_for", ""),
            issuing_body=cert.get("issuing_body", ""),
            source=f"jurisdictions/{jurisdiction_code.lower()}/certifications.yaml",
        )


def seed_document_types(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create DocumentType nodes from a document_types.yaml.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed document_types.yaml contents.
    """
    doc_types = data.get("document_types", [])
    for dt in doc_types:
        dt_id = f"{jurisdiction_code}_{dt['id']}"
        tx.run(
            """
            MERGE (d:DocumentType {id: $id})
            SET d.name = $name,
                d.abbreviation = $abbreviation,
                d.jurisdiction_code = $jurisdiction_code,
                d.regulation = $regulation,
                d.required = $required,
                d.source = $source
            MERGE (j:Jurisdiction {code: $jurisdiction_code})
            MERGE (j)-[:DEFINES_DOCUMENT_TYPE]->(d)
            """,
            id=dt_id,
            name=dt.get("name", ""),
            abbreviation=dt.get("abbreviation", ""),
            jurisdiction_code=jurisdiction_code,
            regulation=dt.get("regulation", ""),
            required=dt.get("required", False),
            source=f"jurisdictions/{jurisdiction_code.lower()}/document_types.yaml",
        )


def seed_activities(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create Activity nodes and link them to regulations via REGULATED_BY.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed activities.yaml contents.
    """
    activities = data.get("activities", [])
    for act in activities:
        act_id = act.get("id", "")
        if not act_id:
            continue
        tx.run(
            """
            MERGE (a:Activity {id: $id})
            SET a.name = $name,
                a.description = $description,
                a.source = $source
            """,
            id=act_id,
            name=act.get("name", ""),
            description=act.get("description", ""),
            source=f"jurisdictions/{jurisdiction_code.lower()}/activities.yaml",
        )
        for reg_ref in act.get("regulated_by", []):
            tx.run(
                """
                MATCH (a:Activity {id: $act_id})
                MATCH (r:Regulation {reference: $reg_ref})
                MERGE (a)-[:REGULATED_BY]->(r)
                """,
                act_id=act_id,
                reg_ref=reg_ref,
            )
        for cert_id in act.get("requires_control", []):
            cond = cert_id if isinstance(cert_id, dict) else {"cert_id": cert_id}
            tx.run(
                """
                MATCH (r:Regulation)-[:REGULATED_BY]-(a:Activity {id: $act_id})
                MATCH (ct:CertificationType {id: $cert_id})
                MERGE (r)-[:REQUIRES_CONTROL {when: $when}]->(ct)
                """,
                act_id=act_id,
                cert_id=cond.get("cert_id", cond) if isinstance(cond, dict) else cond,
                when=cond.get("when", "") if isinstance(cond, dict) else "",
            )


def seed_trade_types(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create TradeType nodes.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed trades.yaml contents.
    """
    trades = data.get("trades", [])
    for trade in trades:
        tx.run(
            """
            MERGE (t:TradeType {id: $id})
            SET t.name = $name,
                t.source = $source
            """,
            id=trade.get("id", ""),
            name=trade.get("name", ""),
            source=f"jurisdictions/{jurisdiction_code.lower()}/trades.yaml",
        )


def seed_hazard_categories(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create HazardCategory nodes.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed hazard_categories.yaml contents.
    """
    categories = data.get("hazard_categories", [])
    for cat in categories:
        tx.run(
            """
            MERGE (h:HazardCategory {id: $id})
            SET h.name = $name,
                h.description = $description,
                h.source = $source
            """,
            id=cat.get("id", ""),
            name=cat.get("name", ""),
            description=cat.get("description", ""),
            source=f"jurisdictions/{jurisdiction_code.lower()}/hazard_categories.yaml",
        )


def seed_inspection_types(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create InspectionType nodes and link to regulations.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed inspection_types.yaml contents.
    """
    types = data.get("inspection_types", [])
    for it in types:
        tx.run(
            """
            MERGE (i:InspectionType {id: $id})
            SET i.name = $name,
                i.description = $description,
                i.source = $source
            """,
            id=it.get("id", ""),
            name=it.get("name", ""),
            description=it.get("description", ""),
            source=f"jurisdictions/{jurisdiction_code.lower()}/inspection_types.yaml",
        )
        for reg_ref in it.get("required_by", []):
            freq = reg_ref if isinstance(reg_ref, dict) else {"reference": reg_ref}
            tx.run(
                """
                MATCH (r:Regulation {reference: $ref})
                MATCH (i:InspectionType {id: $it_id})
                MERGE (r)-[:REQUIRES_INSPECTION {frequency: $frequency}]->(i)
                """,
                ref=freq.get("reference", freq) if isinstance(freq, dict) else freq,
                it_id=it.get("id", ""),
                frequency=freq.get("frequency", "as_required") if isinstance(freq, dict) else "as_required",
            )


def seed_compliance_programs(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    data: dict[str, Any],
) -> None:
    """Create ComplianceProgram nodes from a compliance_rules.yaml.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        data: Parsed compliance_rules.yaml contents.
    """
    programs = data.get("required_programs", [])
    for prog in programs:
        tx.run(
            """
            MERGE (cp:ComplianceProgram {name: $name})
            SET cp.jurisdiction_code = $jurisdiction_code,
                cp.regulation = $regulation,
                cp.check = $check,
                cp.severity = $severity,
                cp.description = $description,
                cp.applies_when = $applies_when,
                cp.source = $source
            MERGE (j:Jurisdiction {code: $jurisdiction_code})
            MERGE (j)-[:REQUIRES_PROGRAM]->(cp)
            """,
            name=prog.get("name", ""),
            jurisdiction_code=jurisdiction_code,
            regulation=prog.get("regulation", ""),
            check=prog.get("check", ""),
            severity=prog.get("severity", ""),
            description=prog.get("description", ""),
            applies_when=prog.get("applies_when", "always"),
            source=f"jurisdictions/{jurisdiction_code.lower()}/compliance_rules.yaml",
        )


def seed_regions(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    regions_dir: Path,
) -> None:
    """Create Region nodes from regional YAML files.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        regions_dir: Path to the regions/ subdirectory.
    """
    if not regions_dir.exists():
        return

    for region_file in sorted(regions_dir.glob("*.yaml")):
        data = load_yaml(region_file)
        code = data.get("code", region_file.stem.upper())
        tx.run(
            """
            MERGE (r:Region {code: $code})
            SET r.name = $name,
                r.jurisdiction_code = $jurisdiction_code,
                r.source = $source
            MERGE (j:Jurisdiction {code: $jurisdiction_code})
            MERGE (j)-[:HAS_REGION]->(r)
            """,
            code=code,
            name=data.get("name", code),
            jurisdiction_code=jurisdiction_code,
            source=f"jurisdictions/{jurisdiction_code.lower()}/regions/{region_file.name}",
        )


def seed_region_requirements(
    tx: ManagedTransaction,
    jurisdiction_code: str,
    regions_dir: Path,
) -> None:
    """Create Regulation nodes from regional YAML requirements.

    Reads the `requirements` array from each regional YAML file and
    creates Regulation nodes linked to their Region via HAS_REQUIREMENT.

    Args:
        tx: Neo4j managed transaction.
        jurisdiction_code: Two-letter jurisdiction code.
        regions_dir: Path to the regions/ subdirectory.
    """
    if not regions_dir.exists():
        return

    for region_file in sorted(regions_dir.glob("*.yaml")):
        data = load_yaml(region_file)
        region_code = data.get("code", region_file.stem.upper())
        requirements = data.get("requirements", [])

        for req in requirements:
            req_id = req.get("id", "")
            if not req_id:
                continue
            tx.run(
                """
                MERGE (reg:Regulation {id: $id})
                SET reg.requirement_name = $requirement_name,
                    reg.description = $description,
                    reg.federal_equivalent = $federal_equivalent,
                    reg.state_standard = $state_standard,
                    reg.additional_details = $additional_details,
                    reg.applies_to = $applies_to,
                    reg.severity = $severity,
                    reg.jurisdiction_code = $jurisdiction_code,
                    reg.region_code = $region_code,
                    reg.valid_from = date('2020-01-01'),
                    reg.valid_until = date('9999-12-31'),
                    reg.source = $source
                MERGE (r:Region {code: $region_code})
                MERGE (r)-[:HAS_REQUIREMENT]->(reg)
                """,
                id=req_id,
                requirement_name=req.get("requirement_name", ""),
                description=req.get("description", ""),
                federal_equivalent=req.get("federal_equivalent"),
                state_standard=req.get("state_standard", ""),
                additional_details=req.get("additional_details", ""),
                applies_to=req.get("applies_to", "all"),
                severity=req.get("severity", "mandatory"),
                jurisdiction_code=jurisdiction_code,
                region_code=region_code,
                source=f"jurisdictions/{jurisdiction_code.lower()}/regions/{region_file.name}",
            )

        if requirements:
            logger.info(
                "  Seeded %d requirements for region %s",
                len(requirements),
                region_code,
            )


def seed_all(driver: Driver, database: str = "neo4j") -> dict[str, int]:
    """Seed the full regulatory graph from all jurisdiction packs.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A dict of node label counts after seeding.
    """
    # Seed industry productivity baselines (shared across all tenants,
    # low-confidence Layer 3 source-cascade fallback)
    try:
        from fixtures.industry_productivity_baselines import seed_industry_baselines

        baseline_count = seed_industry_baselines(driver, database)
        logger.info("Seeded %d IndustryProductivityBaseline nodes", baseline_count)
    except Exception as exc:
        logger.warning("Failed to seed industry productivity baselines: %s", exc)

    for jcode in JURISDICTION_CODES:
        jdir = JURISDICTIONS_DIR / jcode
        if not jdir.exists():
            logger.warning("Jurisdiction directory not found: %s", jdir)
            continue

        logger.info("Seeding jurisdiction: %s", jcode.upper())
        jcode_upper = jcode.upper()

        manifest = load_yaml(jdir / "manifest.yaml") if (jdir / "manifest.yaml").exists() else {}
        if not manifest:
            logger.warning("No manifest.yaml for %s, skipping", jcode)
            continue

        with driver.session(database=database) as session:
            session.execute_write(seed_jurisdiction, manifest)

            regulations_path = jdir / "regulations.yaml"
            if regulations_path.exists():
                regs = load_yaml(regulations_path)
                session.execute_write(seed_regulations, jcode_upper, regs)

            certs_path = jdir / "certifications.yaml"
            if certs_path.exists():
                certs = load_yaml(certs_path)
                session.execute_write(seed_certifications, jcode_upper, certs)

            doc_types_path = jdir / "document_types.yaml"
            if doc_types_path.exists():
                doc_types = load_yaml(doc_types_path)
                session.execute_write(seed_document_types, jcode_upper, doc_types)

            compliance_path = jdir / "compliance_rules.yaml"
            if compliance_path.exists():
                compliance = load_yaml(compliance_path)
                session.execute_write(seed_compliance_programs, jcode_upper, compliance)

            activities_path = jdir / "activities.yaml"
            if activities_path.exists():
                activities = load_yaml(activities_path)
                session.execute_write(seed_activities, jcode_upper, activities)

            trades_path = jdir / "trades.yaml"
            if trades_path.exists():
                trades = load_yaml(trades_path)
                session.execute_write(seed_trade_types, jcode_upper, trades)

            hazards_path = jdir / "hazard_categories.yaml"
            if hazards_path.exists():
                hazards = load_yaml(hazards_path)
                session.execute_write(seed_hazard_categories, jcode_upper, hazards)

            insp_types_path = jdir / "inspection_types.yaml"
            if insp_types_path.exists():
                insp_types = load_yaml(insp_types_path)
                session.execute_write(seed_inspection_types, jcode_upper, insp_types)

            regions_dir = jdir / "regions"
            if regions_dir.exists():
                session.execute_write(seed_regions, jcode_upper, regions_dir)
                session.execute_write(seed_region_requirements, jcode_upper, regions_dir)

    counts = _get_node_counts(driver, database)
    logger.info("Seed complete. Node counts: %s", counts)
    return counts


def _get_node_counts(driver: Driver, database: str) -> dict[str, int]:
    """Query node counts for regulatory labels.

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        A dict mapping label names to node counts.
    """
    labels = [
        "Jurisdiction", "Region", "RegulatoryGroup", "Regulation",
        "CertificationType", "ComplianceProgram", "DocumentType",
        "Activity", "TradeType", "HazardCategory", "InspectionType",
        "IndustryProductivityBaseline",
    ]
    counts = {}
    with driver.session(database=database) as session:
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            record = result.single()
            counts[label] = record["c"] if record else 0
    return counts


def main() -> None:
    """CLI entrypoint for seeding the regulatory graph."""
    parser = argparse.ArgumentParser(description="Seed Neo4j regulatory graph from YAML packs")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="password", help="Neo4j password")
    parser.add_argument("--database", default="neo4j", help="Neo4j database name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", args.uri)
        counts = seed_all(driver, args.database)
        print("\nRegulatory graph seeded successfully:")
        for label, count in sorted(counts.items()):
            print(f"  {label}: {count}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
