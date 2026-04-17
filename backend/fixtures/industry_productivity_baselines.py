"""Seed data for IndustryProductivityBaseline nodes.

Industry-average productivity rates across the common trades. Values are
rough-but-sensible, derived from RSMeans-style references. Confidence is set
low (0.3) by design — these are the weakest fallback in the Layer 3 source
cascade and should always be overridden by a contractor's own productivity
rates or validated insights when available.

Seeded via ``seed_industry_baselines`` and called from
``scripts/seed_regulatory_graph.py`` as part of the global seed run.
"""

from typing import Any

from neo4j import Driver, ManagedTransaction

# rate units: LF (linear feet), SF (square feet), EA (each), CY (cubic yard),
#             TON, BOARD-FT
# time units: per_hour, per_day (assume 8h shift)

INDUSTRY_PRODUCTIVITY_BASELINES: list[dict[str, Any]] = [
    # ── Electrical ─────────────────────────────────────────────────────────
    {
        "id": "ipb_elec_conduit_emt_half",
        "trade": "electrical",
        "work_description": "conduit rough-in 1/2 inch EMT",
        "rate": 120.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 electrical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_elec_conduit_emt_three_quarter",
        "trade": "electrical",
        "work_description": "conduit rough-in 3/4 inch EMT",
        "rate": 100.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 electrical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_elec_device_rough",
        "trade": "electrical",
        "work_description": "device rough-in (boxes, wire pulls)",
        "rate": 30.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 electrical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_elec_device_trim",
        "trade": "electrical",
        "work_description": "device trim out (switches, receptacles)",
        "rate": 50.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 1,
        "source": "RSMeans 2024 electrical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_elec_fixture_install",
        "trade": "electrical",
        "work_description": "light fixture install (standard commercial)",
        "rate": 12.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 electrical",
        "confidence": 0.3,
    },
    # ── Plumbing ───────────────────────────────────────────────────────────
    {
        "id": "ipb_plumb_rough_pex",
        "trade": "plumbing",
        "work_description": "rough-in PEX water lines",
        "rate": 150.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 plumbing",
        "confidence": 0.3,
    },
    {
        "id": "ipb_plumb_rough_dwv",
        "trade": "plumbing",
        "work_description": "DWV rough-in (PVC waste/vent)",
        "rate": 80.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 plumbing",
        "confidence": 0.3,
    },
    {
        "id": "ipb_plumb_fixture_install",
        "trade": "plumbing",
        "work_description": "plumbing fixture install (toilet, lav, sink)",
        "rate": 6.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 plumbing",
        "confidence": 0.3,
    },
    # ── Framing ────────────────────────────────────────────────────────────
    {
        "id": "ipb_fram_wood_walls",
        "trade": "framing",
        "work_description": "wood-framed interior walls",
        "rate": 400.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 carpentry",
        "confidence": 0.3,
    },
    {
        "id": "ipb_fram_metal_studs",
        "trade": "framing",
        "work_description": "metal stud walls",
        "rate": 500.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 carpentry",
        "confidence": 0.3,
    },
    {
        "id": "ipb_fram_deck",
        "trade": "framing",
        "work_description": "deck framing (joists and beams)",
        "rate": 300.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 carpentry",
        "confidence": 0.3,
    },
    # ── Drywall ────────────────────────────────────────────────────────────
    {
        "id": "ipb_drywall_hang",
        "trade": "drywall",
        "work_description": "drywall hang (standard 1/2 inch)",
        "rate": 800.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 drywall",
        "confidence": 0.3,
    },
    {
        "id": "ipb_drywall_finish",
        "trade": "drywall",
        "work_description": "drywall tape and finish (Level 4)",
        "rate": 500.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 drywall",
        "confidence": 0.3,
    },
    # ── Painting ───────────────────────────────────────────────────────────
    {
        "id": "ipb_paint_walls_interior",
        "trade": "painting",
        "work_description": "interior walls, two coats latex",
        "rate": 800.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 1,
        "source": "RSMeans 2024 painting",
        "confidence": 0.3,
    },
    {
        "id": "ipb_paint_ceiling",
        "trade": "painting",
        "work_description": "ceiling paint, one coat",
        "rate": 1000.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 1,
        "source": "RSMeans 2024 painting",
        "confidence": 0.3,
    },
    # ── Flooring ───────────────────────────────────────────────────────────
    {
        "id": "ipb_floor_lvp",
        "trade": "flooring",
        "work_description": "luxury vinyl plank install",
        "rate": 400.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 flooring",
        "confidence": 0.3,
    },
    {
        "id": "ipb_floor_tile_ceramic",
        "trade": "flooring",
        "work_description": "ceramic tile install (floor)",
        "rate": 150.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 tile",
        "confidence": 0.3,
    },
    {
        "id": "ipb_floor_hardwood",
        "trade": "flooring",
        "work_description": "hardwood floor install, nail-down",
        "rate": 300.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 flooring",
        "confidence": 0.3,
    },
    # ── Concrete ───────────────────────────────────────────────────────────
    {
        "id": "ipb_conc_formwork_walls",
        "trade": "concrete",
        "work_description": "wall formwork, build and strip",
        "rate": 300.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 3,
        "source": "RSMeans 2024 concrete",
        "confidence": 0.3,
    },
    {
        "id": "ipb_conc_pour_slab",
        "trade": "concrete",
        "work_description": "concrete pour, slab on grade",
        "rate": 60.0,
        "rate_unit": "CY",
        "time_unit": "per_day",
        "crew_size": 4,
        "source": "RSMeans 2024 concrete",
        "confidence": 0.3,
    },
    {
        "id": "ipb_conc_pour_footing",
        "trade": "concrete",
        "work_description": "concrete pour, continuous footing",
        "rate": 40.0,
        "rate_unit": "CY",
        "time_unit": "per_day",
        "crew_size": 4,
        "source": "RSMeans 2024 concrete",
        "confidence": 0.3,
    },
    # ── HVAC ───────────────────────────────────────────────────────────────
    {
        "id": "ipb_hvac_ductwork_rect",
        "trade": "hvac",
        "work_description": "rectangular sheet-metal ductwork install",
        "rate": 120.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 mechanical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_hvac_ductwork_round",
        "trade": "hvac",
        "work_description": "round spiral ductwork install",
        "rate": 180.0,
        "rate_unit": "LF",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 mechanical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_hvac_rtu_set",
        "trade": "hvac",
        "work_description": "RTU set and curb-mount (up to 10 tons)",
        "rate": 1.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 3,
        "source": "RSMeans 2024 mechanical",
        "confidence": 0.3,
    },
    {
        "id": "ipb_hvac_diffuser",
        "trade": "hvac",
        "work_description": "ceiling diffuser install",
        "rate": 20.0,
        "rate_unit": "EA",
        "time_unit": "per_day",
        "crew_size": 2,
        "source": "RSMeans 2024 mechanical",
        "confidence": 0.3,
    },
    # ── Roofing ────────────────────────────────────────────────────────────
    {
        "id": "ipb_roof_shingle",
        "trade": "roofing",
        "work_description": "asphalt shingle roofing",
        "rate": 600.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 3,
        "source": "RSMeans 2024 roofing",
        "confidence": 0.3,
    },
    {
        "id": "ipb_roof_tpo",
        "trade": "roofing",
        "work_description": "TPO single-ply roofing",
        "rate": 1500.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 4,
        "source": "RSMeans 2024 roofing",
        "confidence": 0.3,
    },
    # ── Masonry ────────────────────────────────────────────────────────────
    {
        "id": "ipb_mas_cmu",
        "trade": "masonry",
        "work_description": "CMU block wall (8 inch)",
        "rate": 240.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 3,
        "source": "RSMeans 2024 masonry",
        "confidence": 0.3,
    },
    {
        "id": "ipb_mas_brick",
        "trade": "masonry",
        "work_description": "face brick veneer",
        "rate": 200.0,
        "rate_unit": "SF",
        "time_unit": "per_day",
        "crew_size": 3,
        "source": "RSMeans 2024 masonry",
        "confidence": 0.3,
    },
]


def _seed_baseline(tx: ManagedTransaction, baseline: dict[str, Any]) -> None:
    """MERGE a single IndustryProductivityBaseline node (idempotent).

    Args:
        tx: Neo4j managed transaction.
        baseline: One entry from INDUSTRY_PRODUCTIVITY_BASELINES.
    """
    tx.run(
        """
        MERGE (ipb:IndustryProductivityBaseline {id: $id})
        SET ipb.trade = $trade,
            ipb.work_description = $work_description,
            ipb.rate = $rate,
            ipb.rate_unit = $rate_unit,
            ipb.time_unit = $time_unit,
            ipb.crew_size = $crew_size,
            ipb.source = $source,
            ipb.confidence = $confidence
        """,
        **baseline,
    )


def seed_industry_baselines(driver: Driver, database: str = "neo4j") -> int:
    """Seed all industry productivity baselines (idempotent).

    Args:
        driver: Neo4j driver.
        database: Target database name.

    Returns:
        Count of baselines present after the seed run.
    """
    with driver.session(database=database) as session:
        for baseline in INDUSTRY_PRODUCTIVITY_BASELINES:
            session.execute_write(_seed_baseline, baseline)

        count_result = session.run(
            "MATCH (ipb:IndustryProductivityBaseline) RETURN count(ipb) AS c"
        )
        record = count_result.single()
        return record["c"] if record else 0
