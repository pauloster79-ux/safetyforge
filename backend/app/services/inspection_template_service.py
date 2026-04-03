"""Pre-built inspection checklist templates for each inspection type."""

from app.models.inspection import InspectionItem, InspectionType

# -- Daily Site Inspection -------------------------------------------------------

DAILY_SITE_ITEMS: list[dict] = [
    # PPE Compliance
    {
        "item_id": "ds_ppe_01",
        "category": "PPE Compliance",
        "description": "Hard hats worn by all workers in required areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_ppe_02",
        "category": "PPE Compliance",
        "description": "Safety glasses/goggles worn where required",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_ppe_03",
        "category": "PPE Compliance",
        "description": "High-visibility vests worn by all personnel",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_ppe_04",
        "category": "PPE Compliance",
        "description": "Steel-toe boots worn by all workers",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Fall Protection
    {
        "item_id": "ds_fall_01",
        "category": "Fall Protection",
        "description": "Guardrails intact and secure at all open edges",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_fall_02",
        "category": "Fall Protection",
        "description": "Covers over floor openings secured and labeled",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_fall_03",
        "category": "Fall Protection",
        "description": "Harnesses and lanyards inspected and in good condition",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Housekeeping
    {
        "item_id": "ds_house_01",
        "category": "Housekeeping",
        "description": "Walkways and access routes clear of obstructions",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_house_02",
        "category": "Housekeeping",
        "description": "Materials stored properly and stacked securely",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_house_03",
        "category": "Housekeeping",
        "description": "Debris and waste removed from work areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Electrical
    {
        "item_id": "ds_elec_01",
        "category": "Electrical",
        "description": "GFCIs tested and functioning properly",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_elec_02",
        "category": "Electrical",
        "description": "Extension cords in good condition, no splices",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_elec_03",
        "category": "Electrical",
        "description": "Electrical panels covered and accessible",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Fire Safety
    {
        "item_id": "ds_fire_01",
        "category": "Fire Safety",
        "description": "Fire extinguishers accessible and inspection current",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_fire_02",
        "category": "Fire Safety",
        "description": "Hot work permits posted where applicable",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Excavations
    {
        "item_id": "ds_exc_01",
        "category": "Excavations",
        "description": "Shoring or sloping adequate for excavation depth",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_exc_02",
        "category": "Excavations",
        "description": "Spoil piles set back at least 2 feet from edge",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Signage
    {
        "item_id": "ds_sign_01",
        "category": "Signage",
        "description": "Danger and warning signs posted at hazard areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_sign_02",
        "category": "Signage",
        "description": "Barricades in place around hazardous areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    # Emergency
    {
        "item_id": "ds_emerg_01",
        "category": "Emergency",
        "description": "First aid kit stocked and accessible",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ds_emerg_02",
        "category": "Emergency",
        "description": "Emergency contact numbers posted visibly",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Scaffold Inspection ---------------------------------------------------------

SCAFFOLD_ITEMS: list[dict] = [
    {
        "item_id": "sc_01",
        "category": "Foundation",
        "description": "Base plates and mud sills in place and level",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_02",
        "category": "Foundation",
        "description": "Scaffold plumb, level, and square",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_03",
        "category": "Structure",
        "description": "All bracing securely attached",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_04",
        "category": "Structure",
        "description": "Tie-ins to structure at required intervals",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_05",
        "category": "Platform",
        "description": "Platforms fully planked with no gaps greater than 1 inch",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_06",
        "category": "Platform",
        "description": "Planks extend at least 6 inches beyond supports",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_07",
        "category": "Guardrails",
        "description": "Top rail at 42 inches (+/- 3 inches)",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_08",
        "category": "Guardrails",
        "description": "Mid rail installed and secure",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_09",
        "category": "Guardrails",
        "description": "Toeboards in place where required",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_10",
        "category": "Access",
        "description": "Safe access ladder or stairway provided",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_11",
        "category": "Competent Person",
        "description": "Competent person tag current and visible",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "sc_12",
        "category": "Load",
        "description": "Scaffold not overloaded beyond rated capacity",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Excavation Inspection -------------------------------------------------------

EXCAVATION_ITEMS: list[dict] = [
    {
        "item_id": "ex_01",
        "category": "Utilities",
        "description": "Underground utilities located and marked",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_02",
        "category": "Protection System",
        "description": "Protective system in place (sloping, shoring, or shield)",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_03",
        "category": "Protection System",
        "description": "Protective system adequate for soil type",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_04",
        "category": "Access/Egress",
        "description": "Ladder or ramp within 25 feet of all workers",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_05",
        "category": "Spoil Pile",
        "description": "Spoil and equipment set back at least 2 feet from edge",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_06",
        "category": "Water",
        "description": "Water accumulation controlled",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_07",
        "category": "Atmosphere",
        "description": "Atmosphere tested in excavations deeper than 4 feet",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_08",
        "category": "Barricades",
        "description": "Adequate warning system for vehicular traffic",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_09",
        "category": "Inspection",
        "description": "Daily inspection by competent person documented",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "ex_10",
        "category": "Adjacent Structures",
        "description": "Adjacent structures supported or undermining prevented",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Electrical Inspection -------------------------------------------------------

ELECTRICAL_ITEMS: list[dict] = [
    {
        "item_id": "el_01",
        "category": "GFCI",
        "description": "GFCIs installed and tested at all temporary outlets",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_02",
        "category": "Cords",
        "description": "Extension cords are 3-wire type and in good condition",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_03",
        "category": "Cords",
        "description": "No cords run through doorways or holes without protection",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_04",
        "category": "Panels",
        "description": "All panel covers in place and circuits labeled",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_05",
        "category": "Lockout/Tagout",
        "description": "Lockout/tagout procedures followed for de-energized work",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_06",
        "category": "Clearance",
        "description": "Minimum clearance from overhead power lines maintained",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_07",
        "category": "Grounding",
        "description": "All equipment properly grounded",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_08",
        "category": "PPE",
        "description": "Insulated tools and PPE used for electrical work",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_09",
        "category": "Signage",
        "description": "Electrical hazard warning signs posted",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "el_10",
        "category": "Temporary Wiring",
        "description": "Temporary wiring installed per code requirements",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Fall Protection Inspection --------------------------------------------------

FALL_PROTECTION_ITEMS: list[dict] = [
    {
        "item_id": "fp_01",
        "category": "Guardrails",
        "description": "Guardrails installed at all open sides 6 feet or more above lower level",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_02",
        "category": "Guardrails",
        "description": "Top rail height at 42 inches (+/- 3 inches)",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_03",
        "category": "Covers",
        "description": "All floor holes and openings covered and secured",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_04",
        "category": "Harnesses",
        "description": "Full-body harnesses inspected before each use",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_05",
        "category": "Harnesses",
        "description": "Harnesses properly fitted and all buckles secured",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_06",
        "category": "Lanyards",
        "description": "Lanyards and connectors in good condition, no damage",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_07",
        "category": "Anchor Points",
        "description": "Anchor points rated for 5,000 lbs per worker attached",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_08",
        "category": "SRL",
        "description": "Self-retracting lifelines inspected and functioning",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_09",
        "category": "Safety Nets",
        "description": "Safety nets installed where required and in good condition",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_10",
        "category": "Training",
        "description": "Workers trained on fall protection plan and equipment use",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fp_11",
        "category": "Rescue Plan",
        "description": "Rescue plan in place and communicated to workers",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Housekeeping Inspection -----------------------------------------------------

HOUSEKEEPING_ITEMS: list[dict] = [
    {
        "item_id": "hk_01",
        "category": "General",
        "description": "Work areas clean and free of unnecessary materials",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_02",
        "category": "Access",
        "description": "Aisles, stairways, and exits clear of obstructions",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_03",
        "category": "Waste",
        "description": "Waste containers provided and regularly emptied",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_04",
        "category": "Waste",
        "description": "Scrap lumber with nails removed or bent over",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_05",
        "category": "Storage",
        "description": "Materials stacked orderly and secured against collapse",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_06",
        "category": "Storage",
        "description": "Flammable materials stored in approved containers",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_07",
        "category": "Lighting",
        "description": "Adequate lighting in all work and access areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_08",
        "category": "Drainage",
        "description": "Standing water controlled and drained",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_09",
        "category": "Sanitation",
        "description": "Toilet facilities clean and adequate for workforce",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "hk_10",
        "category": "Sanitation",
        "description": "Drinking water available and dispensers sanitary",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Equipment Inspection --------------------------------------------------------

EQUIPMENT_ITEMS: list[dict] = [
    {
        "item_id": "eq_01",
        "category": "General",
        "description": "Equipment inspected before use (daily pre-start)",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_02",
        "category": "General",
        "description": "Operator has valid certification/license for equipment",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_03",
        "category": "Safety Devices",
        "description": "Backup alarms and warning lights functional",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_04",
        "category": "Safety Devices",
        "description": "Seatbelts installed and worn by operators",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_05",
        "category": "Safety Devices",
        "description": "ROPS/FOPS in place and undamaged",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_06",
        "category": "Mechanical",
        "description": "Brakes functioning properly",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_07",
        "category": "Mechanical",
        "description": "No visible fluid leaks (hydraulic, oil, coolant)",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_08",
        "category": "Mechanical",
        "description": "Tires/tracks in acceptable condition",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_09",
        "category": "Operation",
        "description": "Swing radius barricaded on excavators and cranes",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_10",
        "category": "Operation",
        "description": "Spotters used when backing or in congested areas",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "eq_11",
        "category": "Maintenance",
        "description": "Maintenance records current and accessible",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Fire Safety Inspection ------------------------------------------------------

FIRE_SAFETY_ITEMS: list[dict] = [
    {
        "item_id": "fs_01",
        "category": "Extinguishers",
        "description": "Fire extinguishers within 75 feet of travel distance",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_02",
        "category": "Extinguishers",
        "description": "Extinguishers fully charged and inspection tags current",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_03",
        "category": "Extinguishers",
        "description": "Correct type extinguisher for hazards present",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_04",
        "category": "Hot Work",
        "description": "Hot work permits issued and posted",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_05",
        "category": "Hot Work",
        "description": "Fire watch assigned during and 30 minutes after hot work",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_06",
        "category": "Hot Work",
        "description": "Combustibles removed or protected within 35-foot radius",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_07",
        "category": "Storage",
        "description": "Flammable liquids stored in approved containers and cabinets",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_08",
        "category": "Storage",
        "description": "Compressed gas cylinders stored upright and secured",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_09",
        "category": "Egress",
        "description": "Emergency exits clear and marked",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
    {
        "item_id": "fs_10",
        "category": "Alarm",
        "description": "Fire alarm or notification system functional",
        "status": "pass",
        "notes": "",
        "photo_url": None,
    },
]

# -- Template registry -----------------------------------------------------------

TEMPLATES: dict[str, list[dict]] = {
    InspectionType.DAILY_SITE.value: DAILY_SITE_ITEMS,
    InspectionType.SCAFFOLD.value: SCAFFOLD_ITEMS,
    InspectionType.EXCAVATION.value: EXCAVATION_ITEMS,
    InspectionType.ELECTRICAL.value: ELECTRICAL_ITEMS,
    InspectionType.FALL_PROTECTION.value: FALL_PROTECTION_ITEMS,
    InspectionType.HOUSEKEEPING.value: HOUSEKEEPING_ITEMS,
    InspectionType.EQUIPMENT.value: EQUIPMENT_ITEMS,
    InspectionType.FIRE_SAFETY.value: FIRE_SAFETY_ITEMS,
}


class InspectionTemplateService:
    """Provides pre-built checklist templates for inspection types."""

    def get_template(self, inspection_type: InspectionType) -> list[InspectionItem]:
        """Return the checklist template for a given inspection type.

        Args:
            inspection_type: The type of inspection.

        Returns:
            A list of InspectionItem models with default 'pass' status.
        """
        raw_items = TEMPLATES.get(inspection_type.value, [])
        return [InspectionItem(**item) for item in raw_items]

    def get_template_dicts(self, inspection_type: InspectionType) -> list[dict]:
        """Return the checklist template as raw dicts for API response.

        Args:
            inspection_type: The type of inspection.

        Returns:
            A list of dicts representing checklist items.
        """
        return TEMPLATES.get(inspection_type.value, [])
