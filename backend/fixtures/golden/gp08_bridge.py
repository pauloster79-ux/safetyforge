"""GP08 — Highway Bridge Replacement (US — Texas).

Heavy civil / infrastructure golden project: highway bridge replacement
on I-35 near Austin. 30 workers, 4 subcontractors, heavy equipment fleet,
environmental permits (SWPPP), and Texas-specific safety concerns
including heat illness prevention and fatigue analysis.

Exercises features including:
- 12 representative workers across GC crew and 4 subs
- 4 subs: piling, concrete, guardrail, traffic control
- Heat illness prevention (Texas heat), confined space (bridge abutments)
- Environmental permits: SWPPP for creek crossing, erosion control
- Heavy equipment fleet: crawler crane, excavator, concrete pump, pile driver, generator
- GPS-verified time tracking scenario, fatigue analysis triggers (11+ hour workers)
- Complex daily logs with material deliveries and weather delays
- 7 inspections, 1 medical treatment incident (heat-related, OSHA recordable)
- 5 daily logs, 2 toolbox talks (heat illness, confined space entry)
- 1 hazard report (excavation shoring concern, open)
- Spanish-speaking crew members (language_preference: "es" or "both")
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP08_COMPANY, GP08_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP08Seeder(GoldenProjectSeeder):
    """Seed GP08: Highway Bridge Replacement — Texas."""

    GP_SLUG = "gp08"
    COMPANY_ID = "comp_gp08"
    PROJECT_ID = "proj_gp08"

    def seed(self) -> dict[str, int]:
        """Seed all GP08 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP08_COMPANY)
        self.seed_user(GP08_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "I-35 Onion Creek Bridge Replacement — SH 45 to Slaughter Ln",
            "address": "I-35 Southbound at Onion Creek, Austin, TX 78748",
            "client_name": "Texas Department of Transportation (TxDOT)",
            "project_type": "infrastructure",
            "trade_types": [
                "general", "piling", "concrete", "guardrail", "traffic_control",
            ],
            "start_date": days_ago(75),
            "end_date": days_from_now(240),
            "estimated_workers": 30,
            "description": "Full replacement of 4-span prestressed concrete bridge "
                "over Onion Creek on I-35 southbound. Includes demolition of "
                "existing structure, drilled shaft foundations, cast-in-place "
                "bent caps, prestressed concrete beams, and composite deck. "
                "Currently in foundation and substructure phase. "
                "Maintained traffic on 2 lanes during construction.",
            "special_hazards": "Active highway traffic — 2 lanes maintained at all times. "
                "Work over water (Onion Creek, seasonal flow). "
                "Confined space entry for bridge abutment interiors. "
                "Heat illness prevention critical (Texas summer, 100+ degrees). "
                "Fatigue management — extended shifts common for concrete pours. "
                "SWPPP required for creek crossing — erosion/sediment control. "
                "Drilled shaft work — cave-in risk, crane proximity to travel lanes.",
            "nearest_hospital": "Ascension Seton Southwest Hospital, "
                "7900 FM 1826, Austin, TX 78737",
            "emergency_contact_name": "Maria Gonzalez",
            "emergency_contact_phone": "512-555-0891",
            "state": "active",
            "status": "normal",
            "compliance_score": 74,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP08_USER["uid"],
            "actor_type": "human",
            "updated_by": GP08_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (12 representative of 30 total) ---
        workers = self._build_workers()
        worker_ids = [w["id"] for w in workers]
        counts["workers"] = self.seed_workers(workers)
        self.assign_workers_to_project(worker_ids)

        # --- Inspections ---
        counts["inspections"] = self.seed_inspections(self._build_inspections())

        # --- Incidents ---
        counts["incidents"] = self.seed_incidents(self._build_incidents())

        # --- Equipment ---
        counts["equipment"] = self.seed_equipment(self._build_equipment())

        # --- Toolbox Talks ---
        counts["toolbox_talks"] = self.seed_toolbox_talks(self._build_talks())

        # --- Hazard Reports ---
        counts["hazard_reports"] = self.seed_hazard_reports(self._build_hazards())

        # --- Daily Logs ---
        counts["daily_logs"] = self.seed_daily_logs(self._build_daily_logs())

        # --- Work Items ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        return counts

    # -----------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------

    def _build_workers(self) -> list[dict]:
        """Build 12 representative workers across GC crew and 4 subs.

        The project has 30 workers total; these 12 represent key roles,
        trades, and language preferences. Remaining 18 are implied by
        headcount and GPS-verified time tracking.
        """
        uid = GP08_USER["uid"]
        base = {
            "status": "active",
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            # --- GC own crew ---
            {
                **base,
                "id": stable_id("wkr", "gp08_maria"),
                "first_name": "Maria",
                "last_name": "Gonzalez",
                "email": "mgonzalez@lonestarinfra.com",
                "phone": "512-555-0891",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "both",
                "hire_date": days_ago(365 * 10),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_maria_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-TX-22-8845",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_maria_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(150),
                        "expiry_date": days_from_now(215),
                        "issuing_body": "American Red Cross",
                        "certificate_number": "ARC-CPR-2025-55678",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_maria_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "OSHA",
                        "certificate_number": "CS-TX-2025-3321",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp08_randy"),
                "first_name": "Randy",
                "last_name": "Holbrook",
                "email": "rholbrook@lonestarinfra.com",
                "phone": "512-555-0903",
                "role": "safety_manager",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_randy_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-TX-21-5534",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_randy_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(915),
                        "issuing_body": "OSHA",
                        "certificate_number": "CS-TX-2025-3322",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp08_jorge"),
                "first_name": "Jorge",
                "last_name": "Salazar",
                "email": "jsalazar@lonestarinfra.com",
                "phone": "512-555-0917",
                "role": "foreman",
                "trade": "general",
                "language_preference": "both",
                "hire_date": days_ago(365 * 6),
                "notes": "GC foreman, concrete crew. Bilingual crew lead. "
                    "Logged 11.5 hours yesterday — fatigue flag triggered.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_jorge_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-TX-22-8846",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp08_roberto"),
                "first_name": "Roberto",
                "last_name": "Castillo",
                "email": "",
                "phone": "512-555-0928",
                "role": "laborer",
                "trade": "general",
                "language_preference": "es",
                "hire_date": days_ago(365 * 3),
                "notes": "GC laborer, concrete crew. Spanish-speaking. "
                    "GPS time tracking active.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_roberto_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-23-4421",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp08_miguel"),
                "first_name": "Miguel",
                "last_name": "Hernandez",
                "email": "",
                "phone": "512-555-0935",
                "role": "laborer",
                "trade": "general",
                "language_preference": "es",
                "hire_date": days_ago(365 * 2),
                "notes": "GC laborer. Spanish-speaking. "
                    "Logged 12 hours two days ago — fatigue analysis triggered.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_miguel_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-24-7723",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Texas Foundation Specialists (piling) ---
            {
                **base,
                "id": stable_id("wkr", "gp08_travis_pile"),
                "first_name": "Travis",
                "last_name": "McCoy",
                "email": "tmccoy@txfoundation.com",
                "phone": "512-555-1001",
                "role": "foreman",
                "trade": "piling",
                "language_preference": "en",
                "hire_date": days_ago(365 * 9),
                "notes": "Sub: Texas Foundation Specialists. Drilled shaft crew of 6.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_travis_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-TX-20-2245",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_travis_crane"),
                        "certification_type": "crane_operator",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "NCCCO",
                        "certificate_number": "NCCCO-CCO-2023-8921",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp08_enrique_pile"),
                "first_name": "Enrique",
                "last_name": "Morales",
                "email": "",
                "phone": "512-555-1015",
                "role": "laborer",
                "trade": "piling",
                "language_preference": "es",
                "hire_date": days_ago(365 * 4),
                "notes": "Sub: Texas Foundation Specialists. Spanish-speaking.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_enrique_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-22-5578",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Capital City Concrete (concrete) ---
            {
                **base,
                "id": stable_id("wkr", "gp08_wayne_conc"),
                "first_name": "Wayne",
                "last_name": "Patterson",
                "email": "wpatterson@capcityconcrete.com",
                "phone": "512-555-1034",
                "role": "foreman",
                "trade": "concrete",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "notes": "Sub: Capital City Concrete. Crew of 5.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_wayne_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-TX-21-4489",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Hill Country Guardrail (guardrail) ---
            {
                **base,
                "id": stable_id("wkr", "gp08_billy_guard"),
                "first_name": "Billy",
                "last_name": "Atkins",
                "email": "batkins@hillcountryguardrail.com",
                "phone": "512-555-1056",
                "role": "foreman",
                "trade": "guardrail",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "notes": "Sub: Hill Country Guardrail. Crew of 4. "
                    "Not yet mobilized — guardrail install starts in 8 weeks.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_billy_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-23-9912",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_billy_flagger"),
                        "certification_type": "flagger_certification",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(65),
                        "issuing_body": "ATSSA",
                        "certificate_number": "ATSSA-FLAG-2025-4421",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Austin Traffic Management (traffic control) ---
            {
                **base,
                "id": stable_id("wkr", "gp08_darren_traffic"),
                "first_name": "Darren",
                "last_name": "Webb",
                "email": "dwebb@austintrafficmgmt.com",
                "phone": "512-555-1078",
                "role": "foreman",
                "trade": "traffic_control",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "notes": "Sub: Austin Traffic Management. TMP crew of 4. "
                    "Responsible for lane closures, flagging, signage.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_darren_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-22-8801",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_darren_flagger"),
                        "certification_type": "flagger_certification",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(530),
                        "issuing_body": "ATSSA",
                        "certificate_number": "ATSSA-FLAG-2025-4422",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_darren_tmp"),
                        "certification_type": "traffic_management_plan",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "TxDOT",
                        "certificate_number": "TXDOT-TMP-2024-5567",
                        "status": "valid",
                    },
                ],
            },
            # --- Crane operator (GC-employed, crawler crane) ---
            {
                **base,
                "id": stable_id("wkr", "gp08_dale_crane"),
                "first_name": "Dale",
                "last_name": "Hutchins",
                "email": "dhutchins@lonestarinfra.com",
                "phone": "512-555-1090",
                "role": "operator",
                "trade": "crane_operation",
                "language_preference": "en",
                "hire_date": days_ago(365 * 12),
                "notes": "Crawler crane operator. NCCCO certified.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp08_dale_crane"),
                        "certification_type": "crane_operator",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "NCCCO",
                        "certificate_number": "NCCCO-CCO-2023-6654",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_dale_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-TX-20-3345",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp08_dale_rigging"),
                        "certification_type": "rigging_signalperson",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "NCCCO",
                        "certificate_number": "NCCCO-RIG-2022-7789",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 7 inspections: daily, excavation, equipment, confined space."""
        uid = GP08_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            {
                **base,
                "id": stable_id("insp", "gp08_daily_d8"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(8),
                "inspector_name": "Randy Holbrook",
                "inspector_id": stable_id("wkr", "gp08_randy"),
                "weather_conditions": "Sunny, hot",
                "temperature": "98°F",
                "workers_on_site": 26,
                "overall_status": "pass",
                "overall_notes": "All traffic control measures in place. "
                    "Erosion control silt fence intact. "
                    "Water coolers stocked at 3 locations. "
                    "Shade structures in place at rest areas.",
                "items": "[]",
                "created_at": datetime_days_ago(8),
                "updated_at": datetime_days_ago(8),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_daily_d5"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(5),
                "inspector_name": "Randy Holbrook",
                "inspector_id": stable_id("wkr", "gp08_randy"),
                "weather_conditions": "Sunny, very hot",
                "temperature": "103°F",
                "workers_on_site": 28,
                "overall_status": "partial",
                "overall_notes": "Heat index exceeded 105. Mandatory rest breaks "
                    "increased to 15 min per hour. One worker showed early signs "
                    "of heat exhaustion — see incident report. "
                    "SWPPP inspection passed — silt fence and erosion control OK.",
                "corrective_actions_needed": "Increase water station frequency. "
                    "Move afternoon concrete pour start to 5 AM to avoid peak heat.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_daily_d3"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "Randy Holbrook",
                "inspector_id": stable_id("wkr", "gp08_randy"),
                "weather_conditions": "Partly cloudy, hot",
                "temperature": "96°F",
                "workers_on_site": 27,
                "overall_status": "pass",
                "overall_notes": "Early start schedule working well (5 AM). "
                    "Concrete pour for bent cap 2 completed by 1 PM. "
                    "Traffic control lane shift executed successfully.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Randy Holbrook",
                "inspector_id": stable_id("wkr", "gp08_randy"),
                "weather_conditions": "Sunny, hot",
                "temperature": "100°F",
                "workers_on_site": 29,
                "overall_status": "pass",
                "overall_notes": "All crews acclimatized. Heat illness prevention "
                    "plan followed. Drilled shaft 4 completed — casing removed. "
                    "Rebar cage set for shaft 5. "
                    "Fatigue flags on 2 workers — reviewed schedules.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_excavation1"),
                "inspection_type": "excavation",
                "inspection_date": days_ago(6),
                "inspector_name": "Maria Gonzalez",
                "inspector_id": stable_id("wkr", "gp08_maria"),
                "weather_conditions": "Sunny",
                "temperature": "95°F",
                "workers_on_site": 25,
                "overall_status": "partial",
                "overall_notes": "Abutment 1 excavation: shoring system in place "
                    "but east wall showing tension cracks in soil. "
                    "Competent person (Travis McCoy) evaluated — adding "
                    "supplemental shoring. No workers in excavation during "
                    "shoring modification.",
                "corrective_actions_needed": "Install supplemental shoring on "
                    "east wall of abutment 1 excavation before re-entry. "
                    "Increase monitoring frequency to every 2 hours.",
                "items": "[]",
                "created_at": datetime_days_ago(6),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_equip_crane"),
                "inspection_type": "equipment",
                "inspection_date": days_ago(2),
                "inspector_name": "Dale Hutchins",
                "inspector_id": stable_id("wkr", "gp08_dale_crane"),
                "weather_conditions": "Sunny",
                "temperature": "97°F",
                "workers_on_site": 28,
                "overall_status": "pass",
                "overall_notes": "Crawler crane daily inspection. "
                    "All limit switches operational. Wire rope condition good. "
                    "Outrigger pads stable on compacted gravel. "
                    "Load chart posted and current. Ground conditions firm.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("insp", "gp08_confined1"),
                "inspection_type": "confined_space",
                "inspection_date": days_ago(4),
                "inspector_name": "Randy Holbrook",
                "inspector_id": stable_id("wkr", "gp08_randy"),
                "weather_conditions": "Sunny",
                "temperature": "99°F",
                "workers_on_site": 26,
                "overall_status": "pass",
                "overall_notes": "Abutment 2 interior classified as permit-required "
                    "confined space. Atmospheric testing: O2 20.9%, LEL 0%, "
                    "CO 0 ppm, H2S 0 ppm. Ventilation blower running. "
                    "Attendant posted. Rescue plan reviewed. "
                    "Entry permit signed by Maria Gonzalez.",
                "items": "[]",
                "created_at": datetime_days_ago(4),
                "updated_at": datetime_days_ago(4),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        """Build 1 incident: heat-related medical treatment (OSHA recordable)."""
        uid = GP08_USER["uid"]
        return [{
            "id": stable_id("inc", "gp08_heat1"),
            "incident_date": days_ago(5),
            "incident_time": "13:40",
            "location": "Bent cap 2 concrete pour area, south abutment",
            "severity": "medical_treatment",
            "status": "closed",
            "description": "Worker (Roberto Castillo) exhibited signs of heat "
                "exhaustion during concrete pour — dizziness, heavy sweating, "
                "nausea. Temperature at time of incident: 103 degrees F, "
                "heat index 108. Worker had been on site since 5 AM (8.5 hours). "
                "Worker moved to shade, given water and electrolytes. "
                "Paramedics called as precaution. Worker transported to "
                "Ascension Seton Southwest for IV fluid replacement. "
                "Released same day. Missed next day of work.",
            "persons_involved": "Roberto Castillo (affected worker)",
            "involved_worker_ids": [
                stable_id("wkr", "gp08_roberto"),
            ],
            "witnesses": "Jorge Salazar (foreman), Miguel Hernandez (laborer)",
            "immediate_actions_taken": "Moved worker to shade structure. "
                "Applied cold compresses. Provided water and electrolytes. "
                "Called 911. Stopped concrete pour for 30 minutes while "
                "crew rotated and hydrated. Resumed with additional rest breaks.",
            "root_cause": "Worker did not take scheduled rest break at 12:30 PM "
                "due to urgency of completing concrete pour before truck return "
                "deadline. Heat index exceeded 105 degrees. Worker had only "
                "consumed 2 of recommended 4 water bottles by that point.",
            "corrective_actions": "Mandatory monitored rest breaks — foreman "
                "tracks compliance, no exceptions during pours. "
                "Water consumption tracking added to daily log. "
                "Buddy system during heat index >100. "
                "Concrete pour schedule shifted to 5 AM start to complete "
                "before noon when possible.",
            "osha_recordable": True,
            "osha_reportable": False,
            "photo_urls": [],
            "created_at": datetime_days_ago(5),
            "updated_at": datetime_days_ago(3),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build equipment: crawler crane, excavator, concrete pump, pile driver, generator."""
        uid = GP08_USER["uid"]
        base = {
            "status": "active",
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {
                **base,
                "id": stable_id("eq", "gp08_crawler_crane"),
                "name": "Link-Belt 248 HSL Crawler Crane",
                "equipment_type": "crawler_crane",
                "make": "Link-Belt",
                "model": "248 HSL",
                "year": 2019,
                "serial_number": "LB-248HSL-2019-5567",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(0),
                "next_inspection_due": days_from_now(1),
                "annual_inspection_date": days_ago(90),
                "annual_inspection_due": days_from_now(275),
                "annual_inspection_vendor": "ALL Crane Service",
                "notes": "200-ton capacity. Used for drilled shaft casing, "
                    "rebar cage setting, and beam placement. "
                    "Positioned on compacted gravel pad south of bridge.",
            },
            {
                **base,
                "id": stable_id("eq", "gp08_excavator"),
                "name": "CAT 330 GC Hydraulic Excavator",
                "equipment_type": "excavator",
                "make": "Caterpillar",
                "model": "330 GC",
                "year": 2022,
                "serial_number": "CAT-330GC-2022-89234",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(0),
                "next_inspection_due": days_from_now(1),
                "notes": "Used for abutment excavation and material handling. "
                    "Equipped with GPS grade control for precision grading.",
            },
            {
                **base,
                "id": stable_id("eq", "gp08_concrete_pump"),
                "name": "Schwing S 43 SX Concrete Pump",
                "equipment_type": "concrete_pump",
                "make": "Schwing",
                "model": "S 43 SX",
                "year": 2021,
                "serial_number": "SCH-S43SX-2021-4478",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_pour",
                "last_inspection_date": days_ago(3),
                "next_inspection_due": days_from_now(4),
                "notes": "Truck-mounted boom pump, 43m reach. "
                    "Rented from Schwing of Texas for pour days only.",
            },
            {
                **base,
                "id": stable_id("eq", "gp08_pile_driver"),
                "name": "APE D30-42 Diesel Pile Hammer",
                "equipment_type": "pile_driver",
                "make": "APE",
                "model": "D30-42",
                "year": 2020,
                "serial_number": "APE-D30-2020-1123",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "notes": "Diesel impact hammer for sheet pile cofferdam installation. "
                    "Noise monitoring required — 85 dB boundary at travel lanes.",
            },
            {
                **base,
                "id": stable_id("eq", "gp08_generator"),
                "name": "Doosan G25WMI-2V Generator",
                "equipment_type": "generator",
                "make": "Doosan",
                "model": "G25WMI-2V",
                "year": 2023,
                "serial_number": "DSN-G25-2023-6612",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "weekly",
                "last_inspection_date": days_ago(4),
                "next_inspection_due": days_from_now(3),
                "notes": "25kW generator for temporary lighting, pumps, and "
                    "traffic signal power. Located at north staging area.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 2 toolbox talks: heat illness, confined space entry."""
        uid = GP08_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            {
                **base,
                "id": stable_id("talk", "gp08_heat_illness"),
                "topic": "Heat Illness Prevention — Recognition and Response",
                "scheduled_date": days_ago(6),
                "target_audience": "all_workers",
                "duration_minutes": 20,
                "language": "both",
                "status": "completed",
                "presented_at": datetime_days_ago(6, hour=5),
                "presented_by": "Randy Holbrook",
                "overall_notes": "Delivered in English and Spanish. "
                    "Reviewed heat exhaustion vs heat stroke symptoms. "
                    "Demonstrated water consumption tracking log. "
                    "Reviewed buddy system for heat index above 100. "
                    "Delivered after heat illness incident earlier that week.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
            },
            {
                **base,
                "id": stable_id("talk", "gp08_confined_space"),
                "topic": "Confined Space Entry — Bridge Abutment Procedures",
                "scheduled_date": days_ago(4),
                "target_audience": "all_workers",
                "duration_minutes": 25,
                "language": "both",
                "status": "completed",
                "presented_at": datetime_days_ago(4, hour=5),
                "presented_by": "Randy Holbrook",
                "overall_notes": "Reviewed permit-required confined space procedures "
                    "for abutment interiors. Atmospheric testing demonstrated. "
                    "Rescue plan walkthrough with retrieval system. "
                    "All entrants verified confined space certification.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
            },
        ]

    # -----------------------------------------------------------------
    # Hazard Reports
    # -----------------------------------------------------------------

    def _build_hazards(self) -> list[dict]:
        """Build 1 hazard report: excavation shoring concern (open)."""
        uid = GP08_USER["uid"]
        return [{
            "id": stable_id("haz", "gp08_shoring1"),
            "description": "Tension cracks observed in east wall of abutment 1 "
                "excavation, approximately 8 feet below grade. Soil type is "
                "sandy clay (Type B per competent person classification). "
                "Existing shoring system was designed for Type A soil conditions "
                "based on original geotechnical report. Supplemental shoring "
                "installed as interim measure. Geotechnical engineer notified "
                "for updated soil classification and shoring redesign.",
            "location": "Abutment 1 excavation, east wall, 8 ft depth",
            "status": "open",
            "hazard_count": 1,
            "highest_severity": "critical",
            "corrective_action_taken": "Supplemental shoring installed. "
                "Workers prohibited from excavation until geotechnical "
                "engineer provides updated classification. "
                "Monitoring frequency increased to every 2 hours.",
            "corrected_at": None,
            "corrected_by": None,
            "created_at": datetime_days_ago(6),
            "updated_at": datetime_days_ago(5),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build 5 daily logs with material deliveries and weather delays."""
        uid = GP08_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            {
                **base,
                "id": stable_id("dlog", "gp08_d8"),
                "log_date": days_ago(8),
                "superintendent_name": "Maria Gonzalez",
                "status": "approved",
                "workers_on_site": 26,
                "work_performed": "Drilled shaft 3 — casing installed, drilling to "
                    "30 ft depth completed. Rebar cage fabricated on site. "
                    "Traffic control lane shift from north to south config. "
                    "Concrete delivery: 45 yards from Martin Marietta for "
                    "bent cap 1 forms. Erosion control silt fence repaired "
                    "after overnight rain.",
                "notes": "Material deliveries: 45 CY concrete (Martin Marietta), "
                    "8 tons rebar (#8 and #11 bars, CMC Steel). "
                    "Weather: sunny, 98 degrees. All heat precautions followed.",
                "created_at": datetime_days_ago(8),
                "updated_at": datetime_days_ago(7),
                "submitted_at": datetime_days_ago(8, hour=16),
                "approved_at": datetime_days_ago(7, hour=6),
            },
            {
                **base,
                "id": stable_id("dlog", "gp08_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "Maria Gonzalez",
                "status": "approved",
                "workers_on_site": 28,
                "work_performed": "Bent cap 2 concrete pour — 62 yards placed. "
                    "Pour started 5 AM, completed 12:30 PM. "
                    "HEAT ILLNESS INCIDENT at 1:40 PM — Roberto Castillo "
                    "transported to hospital. See incident report. "
                    "Drilled shaft 4 drilling in progress. "
                    "Abutment 1 excavation shoring concern identified.",
                "notes": "Material deliveries: 62 CY concrete (Martin Marietta), "
                    "delivered in 7 trucks starting 4:45 AM. "
                    "Weather: sunny, 103 degrees, heat index 108. "
                    "OSHA recordable incident — heat exhaustion.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=16),
                "approved_at": datetime_days_ago(4, hour=6),
            },
            {
                **base,
                "id": stable_id("dlog", "gp08_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Maria Gonzalez",
                "status": "submitted",
                "workers_on_site": 27,
                "work_performed": "Drilled shaft 4 completed — casing pulled, "
                    "concrete tremie pour 38 yards. "
                    "Bent cap 2 forms stripped. "
                    "Abutment 1 supplemental shoring installed. "
                    "Traffic control — nighttime lane closure for beam delivery "
                    "staging area prep.",
                "notes": "Material deliveries: 38 CY concrete (Martin Marietta), "
                    "12 ea steel H-piles (Nucor, 40 ft lengths). "
                    "Weather: partly cloudy, 96 degrees. "
                    "Roberto Castillo returned to light duty.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "submitted_at": datetime_days_ago(3, hour=16),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp08_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Maria Gonzalez",
                "status": "submitted",
                "workers_on_site": 29,
                "work_performed": "Drilled shaft 5 rebar cage set by crane. "
                    "Shaft 5 concrete tremie pour scheduled for tomorrow. "
                    "Abutment 2 confined space entry — rebar placement inside "
                    "abutment walls, 6 workers entered with permit. "
                    "Geotechnical engineer visited abutment 1 — report pending.",
                "notes": "Material deliveries: 14 tons rebar (#5, #8, #11 bars, "
                    "CMC Steel). Weather: sunny, 100 degrees. "
                    "Fatigue flags: Jorge Salazar 11.5 hrs, "
                    "Miguel Hernandez 12 hrs (previous day carry-over). "
                    "Both workers counseled on rest requirements.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=16),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp08_today"),
                "log_date": days_ago(0),
                "superintendent_name": "Maria Gonzalez",
                "status": "draft",
                "workers_on_site": 0,
                "work_performed": "",
                "notes": "",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "submitted_at": None,
                "approved_at": None,
            },
        ]

    # -----------------------------------------------------------------
    # Work Items (quote / scope of works)
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active bridge replacement.

        Active project — items reflect the in-flight scope.
        All values in cents (USD).
        """
        uid = GP08_USER["uid"]
        base = {
            "state": "in_progress",
            "deleted": False,
            "is_alternate": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
            "agent_version": None,
            "agent_cost_cents": None,
        }
        lab_base = {
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
            "agent_version": None,
            "agent_cost_cents": None,
        }

        return [
            {
                **base,
                "id": stable_id("wi", "gp08_item_1"),
                "description": "Bridge deck demolition \u2014 existing 2-lane structure",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 18,
                "labour_total_cents": 2720000,
                "items_total_cents": 1850000,
                "sell_price_cents": 5392600,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp08_lab_1"),
                        "task": "Traffic control, demo, removal",
                        "rate_cents": 8500,
                        "hours": 320,
                        "cost_cents": 2720000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp08_item_1_mat_1"),
                        "description": "Demolition and disposal",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 1850000,
                        "total_cents": 1850000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp08_item_2"),
                "description": "Abutment and pier construction \u2014 2 abutments, 3 piers",
                "quantity": 5,
                "unit": "EA",
                "margin_pct": 20,
                "labour_total_cents": 6800000,
                "items_total_cents": 4850000,
                "sell_price_cents": 13980000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp08_lab_2"),
                        "task": "Form, rebar, pour, cure",
                        "rate_cents": 8500,
                        "hours": 800,
                        "cost_cents": 6800000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp08_item_2_mat_1"),
                        "description": "Concrete, rebar, formwork",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 4850000,
                        "total_cents": 4850000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp08_item_3"),
                "description": "Superstructure \u2014 precast girders and CIP deck",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 22,
                "labour_total_cents": 11040000,
                "items_total_cents": 8850000,
                "sell_price_cents": 24265800,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp08_lab_3"),
                        "task": "Set girders and pour deck",
                        "rate_cents": 11500,
                        "hours": 960,
                        "cost_cents": 11040000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp08_item_3_mat_1"),
                        "description": "PC girders, deck concrete, rebar",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 8850000,
                        "total_cents": 8850000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp08_item_4"),
                "description": "Approach work and tie-ins",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 20,
                "labour_total_cents": 3600000,
                "items_total_cents": 1450000,
                "sell_price_cents": 6060000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp08_lab_4"),
                        "task": "Earthwork, paving, striping",
                        "rate_cents": 7500,
                        "hours": 480,
                        "cost_cents": 3600000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp08_item_4_mat_1"),
                        "description": "Aggregate, asphalt, signage",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 1450000,
                        "total_cents": 1450000,
                    },
                ],
            },
        ]
