"""GP09 -- Apartment Complex, Active Incident (UK -- Scotland).

Medium-high complexity golden project: 10 representative workers (from
pool of 20), 3 subs (roofing, plumbing, electrical), Scottish Building
Standards, RIDDOR reporting.

Key scenario: **ACTIVE INCIDENT** -- a worker fell from scaffolding
two days ago.  Severity: hospitalisation (broken arm, head laceration).
The scaffold was inspected 3 days before and *passed* -- this matters
for the investigation.

Workers: 20 total (10 seeded as representative sample)
Inspections: 5 (including the critical pre-incident scaffold pass)
Incidents: 1 (active, investigating, RIDDOR filed)
Toolbox Talks: 2 (one scaffold safety delivered BEFORE the incident)
Daily Logs: 4 (including the incident-day log)
Hazard Reports: 1 (open, related to the incident area)
Equipment: scaffold system (barricaded), tower crane
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP09_COMPANY, GP09_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP09Seeder(GoldenProjectSeeder):
    """Seed GP09: Apartment Complex -- Active Incident (Scotland)."""

    GP_SLUG = "gp09"
    COMPANY_ID = "comp_gp09"
    PROJECT_ID = "proj_gp09"

    def seed(self) -> dict[str, int]:
        """Seed all GP09 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP09_COMPANY)
        self.seed_user(GP09_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Craigmillar Gardens -- 24-Unit Apartment Complex",
            "address": "45 Craigmillar Castle Road, Edinburgh EH16 5PQ",
            "client_name": "Craigmillar Residential Trust",
            "project_type": "residential",
            "trade_types": ["general", "roofing", "plumbing", "electrical"],
            "start_date": days_ago(120),
            "end_date": days_from_now(90),
            "estimated_workers": 20,
            "description": "New-build 24-unit apartment complex over 4 storeys. "
                "Timber frame with brick cladding, pitched roof. "
                "Currently in second-fix and external works phase. "
                "Scaffold work BLOCKED pending incident investigation.",
            "special_hazards": "Working at height on all four storeys. "
                "Scaffold access on all elevations. "
                "Confined space in basement plant room. "
                "Proximity to public footpath on east boundary. "
                "ACTIVE INCIDENT -- scaffold work suspended.",
            "nearest_hospital": "Royal Infirmary of Edinburgh, "
                "51 Little France Crescent, Edinburgh EH16 4SA",
            "emergency_contact_name": "Fiona MacLeod",
            "emergency_contact_phone": "+44-131-555-0456",
            "state": "active",
            "status": "normal",
            "compliance_score": 58,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP09_USER["uid"],
            "actor_type": "human",
            "updated_by": GP09_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (10 representative from 20-person workforce) ---
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
        """Build 10 representative workers across GC crew and 3 subs."""
        uid = GP09_USER["uid"]
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
                "id": stable_id("wkr", "gp09_fiona"),
                "first_name": "Fiona",
                "last_name": "MacLeod",
                "email": "fiona@highlanddevelopments.co.uk",
                "phone": "+44-131-555-0456",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 10),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_fiona_cscs_black"),
                        "certification_type": "cscs_black",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLK-SC-22-4410",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_fiona_smsts"),
                        "certification_type": "smsts",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CITB",
                        "certificate_number": "SMSTS-SC-2025-1192",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_fiona_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(165),
                        "issuing_body": "St Andrew's First Aid",
                        "certificate_number": "SAFA-2025-33891",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp09_callum"),
                "first_name": "Callum",
                "last_name": "Fraser",
                "email": "callum@highlanddevelopments.co.uk",
                "phone": "+44-131-555-0461",
                "role": "foreman",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_callum_cscs_gold"),
                        "certification_type": "cscs_gold",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GLD-SC-23-8812",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_callum_sssts"),
                        "certification_type": "sssts",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CITB",
                        "certificate_number": "SSSTS-SC-2025-0456",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp09_rory"),
                "first_name": "Rory",
                "last_name": "Campbell",
                "email": "",
                "phone": "+44-131-555-0472",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_rory_cscs_green"),
                        "certification_type": "cscs_green",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GRN-SC-23-2291",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp09_hamish"),
                "first_name": "Hamish",
                "last_name": "Stewart",
                "email": "",
                "phone": "+44-131-555-0478",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_hamish_cscs_green"),
                        "certification_type": "cscs_green",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GRN-SC-24-1178",
                        "status": "valid",
                    },
                ],
            },
            # --- INCIDENT WORKER: suspended pending investigation ---
            {
                **base,
                "id": stable_id("wkr", "gp09_gregor"),
                "first_name": "Gregor",
                "last_name": "Mackenzie",
                "email": "",
                "phone": "+44-131-555-0485",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "status": "suspended",
                "notes": "Suspended pending incident investigation. "
                    "Fell from scaffold on north elevation. "
                    "Hospitalised with broken right arm and head laceration.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_gregor_cscs_green"),
                        "certification_type": "cscs_green",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GRN-SC-25-0034",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_gregor_wah"),
                        "certification_type": "working_at_height",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(65),
                        "issuing_body": "CITB",
                        "certificate_number": "WAH-SC-2025-7721",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Caledonian Roofing (roofing) ---
            {
                **base,
                "id": stable_id("wkr", "gp09_neil_roof"),
                "first_name": "Neil",
                "last_name": "Henderson",
                "email": "neil@caledonianroofing.co.uk",
                "phone": "+44-131-555-0521",
                "role": "foreman",
                "trade": "roofing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "notes": "Sub: Caledonian Roofing Ltd",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_neil_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-SC-23-5567",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_neil_scaffold"),
                        "certification_type": "scaffold_inspection",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "CISRS",
                        "certificate_number": "CISRS-SC-2025-0445",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp09_ewan_roof"),
                "first_name": "Ewan",
                "last_name": "Douglas",
                "email": "",
                "phone": "+44-131-555-0528",
                "role": "laborer",
                "trade": "roofing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "notes": "Sub: Caledonian Roofing Ltd",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_ewan_cscs_green"),
                        "certification_type": "cscs_green",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GRN-SC-23-6689",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Forth Plumbing (plumbing) ---
            {
                **base,
                "id": stable_id("wkr", "gp09_moira_plumb"),
                "first_name": "Moira",
                "last_name": "Grant",
                "email": "moira@forthplumbing.co.uk",
                "phone": "+44-131-555-0541",
                "role": "foreman",
                "trade": "plumbing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "notes": "Sub: Forth Plumbing Services",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_moira_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-SC-24-7723",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_moira_water_regs"),
                        "certification_type": "water_regulations",
                        "issued_date": days_ago(500),
                        "expiry_date": days_ago(135),  # EXPIRED
                        "issuing_body": "SNIPEF",
                        "certificate_number": "WREG-SC-2024-0098",
                        "status": "expired",
                    },
                ],
            },
            # --- Sub: Lothian Electrical (electrical) ---
            {
                **base,
                "id": stable_id("wkr", "gp09_ross_elec"),
                "first_name": "Ross",
                "last_name": "Murray",
                "email": "ross@lothianelectrical.co.uk",
                "phone": "+44-131-555-0562",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "notes": "Sub: Lothian Electrical Contractors",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_ross_cscs_gold"),
                        "certification_type": "cscs_gold",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GLD-SC-23-8891",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp09_ross_17th_edition"),
                        "certification_type": "bs7671_18th_edition",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "EAL / IET",
                        "certificate_number": "BS7671-SC-2025-2201",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp09_craig_elec"),
                "first_name": "Craig",
                "last_name": "Wilson",
                "email": "",
                "phone": "+44-131-555-0571",
                "role": "journeyman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "notes": "Sub: Lothian Electrical Contractors",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp09_craig_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(365 * 2),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-SC-22-4457",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 5 inspections.

        CRITICAL: The scaffold inspection 3 days before the incident
        showed PASS.  This is important for the investigation narrative.
        """
        uid = GP09_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            # Daily site inspection -- 5 days ago
            {
                **base,
                "id": stable_id("insp", "gp09_daily_d5"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(5),
                "inspector_name": "Fiona MacLeod",
                "inspector_id": stable_id("wkr", "gp09_fiona"),
                "weather_conditions": "Overcast, light rain",
                "temperature": "9C",
                "workers_on_site": 14,
                "overall_status": "pass",
                "overall_notes": "All PPE in use. Wet conditions -- "
                    "non-slip mats deployed on scaffold access points. "
                    "Housekeeping acceptable.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            # CRITICAL: Scaffold inspection 3 days ago -- PASSED
            {
                **base,
                "id": stable_id("insp", "gp09_scaffold_d3"),
                "inspection_type": "scaffold",
                "inspection_date": days_ago(3),
                "inspector_name": "Neil Henderson",
                "inspector_id": stable_id("wkr", "gp09_neil_roof"),
                "weather_conditions": "Dry, overcast",
                "temperature": "11C",
                "workers_on_site": 16,
                "overall_status": "pass",
                "overall_notes": "North elevation scaffold inspected per "
                    "NASC TG20 guidance. All standards, ledgers, and "
                    "transoms secure. Toe boards and guardrails in place. "
                    "Scaffold ties adequate for wind loading. "
                    "Scaffold tag updated to green.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            # Daily site -- day of incident (2 days ago)
            {
                **base,
                "id": stable_id("insp", "gp09_daily_d2_am"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(2),
                "inspector_name": "Callum Fraser",
                "inspector_id": stable_id("wkr", "gp09_callum"),
                "weather_conditions": "Windy, gusts to 40 mph, rain",
                "temperature": "7C",
                "workers_on_site": 18,
                "overall_status": "partial",
                "overall_notes": "Morning inspection before incident. "
                    "Wind conditions borderline for work at height. "
                    "Scaffold appeared intact. "
                    "NOTE: Incident occurred at 11:15 -- see incident report.",
                "corrective_actions_needed": "ALL scaffold work suspended "
                    "following incident at 11:15. Competent person review "
                    "of all scaffold structures required before resuming.",
                "items": "[]",
                "created_at": datetime_days_ago(2, hour=7),
                "updated_at": datetime_days_ago(2, hour=12),
            },
            # Post-incident safety stand-down inspection (2 days ago PM)
            {
                **base,
                "id": stable_id("insp", "gp09_postincident_d2"),
                "inspection_type": "scaffold",
                "inspection_date": days_ago(2),
                "inspector_name": "Fiona MacLeod",
                "inspector_id": stable_id("wkr", "gp09_fiona"),
                "weather_conditions": "Windy, rain easing",
                "temperature": "8C",
                "workers_on_site": 0,
                "overall_status": "fail",
                "overall_notes": "Post-incident scaffold inspection. "
                    "North elevation scaffold: guardrail coupling found "
                    "loose at Level 3, bay 4 -- possible point of failure. "
                    "Board missing from platform at Level 3, bay 3 "
                    "(unclear if displaced during incident or before). "
                    "Entire north scaffold barricaded and tagged red. "
                    "HSE notified per RIDDOR.",
                "corrective_actions_needed": "Full scaffold strip-down "
                    "and re-erection of north elevation scaffold required "
                    "before any re-access. Independent scaffold inspection "
                    "by CISRS advanced scaffolder. HSE investigation "
                    "must conclude before scaffold remediation.",
                "items": "[]",
                "created_at": datetime_days_ago(2, hour=14),
                "updated_at": datetime_days_ago(2, hour=16),
            },
            # Daily site -- yesterday (limited work, no scaffold)
            {
                **base,
                "id": stable_id("insp", "gp09_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Fiona MacLeod",
                "inspector_id": stable_id("wkr", "gp09_fiona"),
                "weather_conditions": "Dry, cloudy",
                "temperature": "10C",
                "workers_on_site": 8,
                "overall_status": "pass",
                "overall_notes": "Reduced crew -- ground-level work only. "
                    "No scaffold access. Electrical second-fix and "
                    "plumbing work on lower floors continuing. "
                    "North elevation exclusion zone maintained. "
                    "All barricading intact.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        """Build the active scaffold fall incident."""
        uid = GP09_USER["uid"]
        return [{
            "id": stable_id("inc", "gp09_scaffold_fall"),
            "incident_date": days_ago(2),
            "incident_time": "11:15",
            "location": "North elevation scaffold, Level 3, bay 3-4",
            "severity": "hospitalization",
            "status": "investigating",
            "description": "Worker Gregor Mackenzie fell approximately 6 metres "
                "from Level 3 of the north elevation scaffold while "
                "carrying brickwork materials along the platform. "
                "Worker struck intermediate platform at Level 2 before "
                "landing on ground-level debris netting. "
                "Injuries sustained: fractured right humerus (closed), "
                "laceration to left temple requiring sutures. "
                "Ambulance called at 11:17, arrived 11:28. "
                "Worker transported to Royal Infirmary of Edinburgh. "
                "Admitted to orthopaedic ward.",
            "persons_involved": "Gregor Mackenzie (injured party), "
                "Hamish Stewart (working nearby on Level 3)",
            "involved_worker_ids": [
                stable_id("wkr", "gp09_gregor"),
                stable_id("wkr", "gp09_hamish"),
            ],
            "witnesses": "Hamish Stewart, Callum Fraser (ground level)",
            "immediate_actions_taken": "First aid administered by Fiona MacLeod "
                "(appointed first aider). Ambulance called. "
                "All work at height stopped immediately. "
                "North scaffold barricaded and tagged red. "
                "All workers stood down for safety briefing. "
                "Scene preserved for HSE investigation.",
            "root_cause": "Under investigation. Preliminary findings: "
                "guardrail coupling at Level 3 bay 4 found loose during "
                "post-incident inspection. A platform board at Level 3 "
                "bay 3 was displaced. Wind gusts were recorded at 40 mph "
                "at time of incident. Contributing factors being assessed: "
                "wind speed vs safe working limits for scaffold access, "
                "scaffold inspection regime adequacy, "
                "material handling procedures at height.",
            "corrective_actions": "1. North scaffold barricaded -- no access. "
                "2. RIDDOR report filed with HSE (reference RID-2026-SC-04412). "
                "3. Worker Gregor Mackenzie suspended pending investigation. "
                "4. Independent CISRS scaffold inspection commissioned. "
                "5. All scaffold competent person records under review. "
                "6. Wind policy to be revised (current threshold 45 mph, "
                "proposed reduction to 35 mph for loaded scaffold access). "
                "7. Toolbox talk on scaffold safety to be re-delivered "
                "to all workers before scaffold work resumes.",
            "riddor_reference": "RID-2026-SC-04412",
            "riddor_filed": True,
            "riddor_filed_date": days_ago(2),
            "regulatory_body_notified": "HSE Scotland",
            "osha_recordable": False,
            "osha_reportable": False,
            "photo_urls": [],
            "created_at": datetime_days_ago(2, hour=12),
            "updated_at": datetime_days_ago(1, hour=10),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build equipment list including the barricaded scaffold."""
        uid = GP09_USER["uid"]
        base = {
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
                "id": stable_id("eq", "gp09_scaffold_north"),
                "name": "HAKI Universal Scaffold -- North Elevation",
                "equipment_type": "scaffold_system",
                "make": "HAKI",
                "model": "Universal System Scaffold",
                "serial_number": "HAKI-2024-SC-7721",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "weekly",
                "last_inspection_date": days_ago(2),
                "next_inspection_due": None,
                "status": "out_of_service",
                "notes": "BARRICADED -- tagged red following incident. "
                    "No access until HSE investigation concludes and "
                    "independent CISRS inspection completed. "
                    "Guardrail coupling at L3 bay 4 found loose. "
                    "Platform board at L3 bay 3 displaced.",
            },
            {
                **base,
                "id": stable_id("eq", "gp09_scaffold_south"),
                "name": "HAKI Universal Scaffold -- South Elevation",
                "equipment_type": "scaffold_system",
                "make": "HAKI",
                "model": "Universal System Scaffold",
                "serial_number": "HAKI-2024-SC-7722",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "weekly",
                "last_inspection_date": days_ago(2),
                "next_inspection_due": days_from_now(5),
                "status": "active",
                "notes": "South elevation scaffold cleared for use after "
                    "post-incident review. Independent of north scaffold.",
            },
            {
                **base,
                "id": stable_id("eq", "gp09_crane"),
                "name": "Liebherr 65K Tower Crane",
                "equipment_type": "tower_crane",
                "make": "Liebherr",
                "model": "65 K.1",
                "year": 2022,
                "serial_number": "LBH-65K-2022-SC-3345",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "weekly",
                "last_inspection_date": days_ago(3),
                "next_inspection_due": days_from_now(4),
                "status": "active",
                "notes": "Tower crane for material lifts. "
                    "Operations suspended during high winds (>38 mph). "
                    "Weekly thorough examination per LOLER 1998.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 2 toolbox talks.

        One scaffold safety talk delivered BEFORE the incident (important
        for showing that training was given), and one post-incident
        safety stand-down briefing.
        """
        uid = GP09_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            # Scaffold safety -- delivered 5 days ago (BEFORE incident)
            {
                **base,
                "id": stable_id("talk", "gp09_scaffold_safety"),
                "topic": "Working at Height and Scaffold Safety",
                "scheduled_date": days_ago(5),
                "target_audience": "all_workers",
                "duration_minutes": 20,
                "language": "en",
                "status": "completed",
                "presented_at": datetime_days_ago(5, hour=7),
                "presented_by": "Fiona MacLeod",
                "overall_notes": "Covered Work at Height Regulations 2005. "
                    "Reviewed scaffold access and egress procedures. "
                    "Discussed guardrail inspection responsibilities. "
                    "Reminded all workers to check scaffold tag before access. "
                    "Attendance: 16 workers signed.",
                "created_at": datetime_days_ago(6),
                "updated_at": datetime_days_ago(5),
            },
            # Post-incident stand-down briefing (incident day)
            {
                **base,
                "id": stable_id("talk", "gp09_postincident_standown"),
                "topic": "Post-Incident Safety Stand-Down Briefing",
                "scheduled_date": days_ago(2),
                "target_audience": "all_workers",
                "duration_minutes": 30,
                "language": "en",
                "status": "completed",
                "presented_at": datetime_days_ago(2, hour=14),
                "presented_by": "Fiona MacLeod",
                "overall_notes": "Mandatory stand-down following scaffold incident. "
                    "Reviewed what happened (factual, no blame). "
                    "Reminded all workers of stop-work authority. "
                    "Discussed wind speed limits and scaffold access rules. "
                    "All scaffold work suspended until further notice. "
                    "Workers to report any concerns about other scaffolds. "
                    "Attendance: all 18 workers on site.",
                "created_at": datetime_days_ago(2, hour=13),
                "updated_at": datetime_days_ago(2, hour=15),
            },
        ]

    # -----------------------------------------------------------------
    # Hazard Reports
    # -----------------------------------------------------------------

    def _build_hazards(self) -> list[dict]:
        """Build 1 open hazard report related to the incident area."""
        uid = GP09_USER["uid"]
        return [{
            "id": stable_id("haz", "gp09_north_scaffold"),
            "description": "North elevation scaffold -- structural integrity "
                "compromised following worker fall incident. "
                "Guardrail coupling loose at Level 3 bay 4. "
                "Platform board displaced at Level 3 bay 3. "
                "Risk of further material falling from scaffold.",
            "location": "North elevation, Levels 1-4",
            "status": "open",
            "hazard_count": 3,
            "highest_severity": "critical",
            "corrective_action_taken": "Scaffold barricaded and tagged red. "
                "Exclusion zone established at ground level beneath. "
                "HSE investigation in progress. "
                "Independent CISRS inspection commissioned.",
            "corrected_at": None,
            "corrected_by": None,
            "created_at": datetime_days_ago(2, hour=13),
            "updated_at": datetime_days_ago(1, hour=10),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build 4 daily logs including the incident-day log."""
        uid = GP09_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            # 5 days ago -- normal operations
            {
                **base,
                "id": stable_id("dlog", "gp09_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "Fiona MacLeod",
                "status": "approved",
                "workers_on_site": 14,
                "work_performed": "Brickwork cladding continued on south and "
                    "east elevations -- 3rd storey 40% complete. "
                    "Electrical first-fix on ground floor flats 1-6. "
                    "Plumbing risers installed in blocks A and B. "
                    "Toolbox talk delivered on scaffold safety.",
                "notes": "Rainy conditions -- non-slip measures on scaffold. "
                    "All trades progressing to programme.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=8),
            },
            # 3 days ago -- normal day before incident
            {
                **base,
                "id": stable_id("dlog", "gp09_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Fiona MacLeod",
                "status": "approved",
                "workers_on_site": 16,
                "work_performed": "North elevation scaffold passed weekly "
                    "inspection. Brickwork started on north elevation "
                    "ground and first storey. Roofing sub started felt "
                    "and batten on block A. Electrical second-fix "
                    "commenced on ground floor.",
                "notes": "Good progress. Scaffold inspection report filed.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(2),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": datetime_days_ago(2, hour=7),
            },
            # 2 days ago -- INCIDENT DAY
            {
                **base,
                "id": stable_id("dlog", "gp09_d2_incident"),
                "log_date": days_ago(2),
                "superintendent_name": "Fiona MacLeod",
                "status": "submitted",
                "workers_on_site": 18,
                "work_performed": "Morning: brickwork on north elevation "
                    "continued. Roofing battens on block A. "
                    "Electrical and plumbing work on upper floors. "
                    "11:15 -- INCIDENT: Worker Gregor Mackenzie fell "
                    "from north scaffold Level 3. Work stopped. "
                    "Ambulance called. All scaffold work suspended. "
                    "Afternoon: safety stand-down briefing for all workers. "
                    "Post-incident scaffold inspection conducted. "
                    "RIDDOR report filed.",
                "notes": "CRITICAL: Scaffold incident -- see incident report "
                    "inc_gp09_scaffold_fall. RIDDOR reference: "
                    "RID-2026-SC-04412. HSE notified. "
                    "North scaffold barricaded. "
                    "Only ground-level work permitted until further notice.",
                "created_at": datetime_days_ago(2, hour=17),
                "updated_at": datetime_days_ago(2, hour=18),
                "submitted_at": datetime_days_ago(2, hour=18),
                "approved_at": None,
            },
            # Yesterday -- restricted operations
            {
                **base,
                "id": stable_id("dlog", "gp09_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Fiona MacLeod",
                "status": "submitted",
                "workers_on_site": 8,
                "work_performed": "Reduced crew -- ground-level and internal "
                    "work only. Electrical second-fix on floors 1-2. "
                    "Plumbing second-fix in ground-floor flats. "
                    "No work at height. No scaffold access. "
                    "North exclusion zone maintained.",
                "notes": "Awaiting HSE visit -- expected tomorrow. "
                    "Independent scaffold inspector booked for Thursday. "
                    "Gregor Mackenzie visited in hospital -- condition "
                    "stable, surgery scheduled for tomorrow.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
        ]

    # -----------------------------------------------------------------
    # Work Items (quote / scope of works)
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active multi-unit residential build.

        Active project — items reflect the in-flight scope.
        All values in cents (GBP / pence).
        """
        uid = GP09_USER["uid"]
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
                "id": stable_id("wi", "gp09_item_1"),
                "description": "Foundation and ground floor slab \u2014 24 units",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 18,
                "labour_total_cents": 1260000,
                "items_total_cents": 2850000,
                "sell_price_cents": 4849800,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp09_lab_1"),
                        "task": "Excavate, form, pour, cure",
                        "rate_cents": 4500,
                        "hours": 280,
                        "cost_cents": 1260000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp09_item_1_mat_1"),
                        "description": "Concrete, rebar, DPM, blockwork",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 2850000,
                        "total_cents": 2850000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp09_item_2"),
                "description": "Superstructure masonry \u2014 4 storeys, 24 units",
                "quantity": 2400,
                "unit": "SM",
                "margin_pct": 20,
                "labour_total_cents": 3696000,
                "items_total_cents": 1850000,
                "sell_price_cents": 6655200,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp09_lab_2"),
                        "task": "Block and brick masonry",
                        "rate_cents": 4200,
                        "hours": 880,
                        "cost_cents": 3696000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp09_item_2_mat_1"),
                        "description": "Blocks, brick, mortar, ties",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 1850000,
                        "total_cents": 1850000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp09_item_3"),
                "description": "MEP rough-in \u2014 all 24 units",
                "quantity": 24,
                "unit": "EA",
                "margin_pct": 25,
                "labour_total_cents": 2640000,
                "items_total_cents": 4440000,
                "sell_price_cents": 8850000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp09_lab_3"),
                        "task": "MEP first fix",
                        "rate_cents": 5500,
                        "hours": 480,
                        "cost_cents": 2640000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp09_item_3_mat_1"),
                        "description": "MEP materials package",
                        "quantity": 24,
                        "unit": "EA",
                        "unit_cost_cents": 185000,
                        "total_cents": 4440000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp09_item_4"),
                "description": "Internal finishes \u2014 flooring, decoration, doors",
                "quantity": 24,
                "unit": "EA",
                "margin_pct": 22,
                "labour_total_cents": 2736000,
                "items_total_cents": 3480000,
                "sell_price_cents": 7583520,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp09_lab_4"),
                        "task": "Install finishes",
                        "rate_cents": 3800,
                        "hours": 720,
                        "cost_cents": 2736000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp09_item_4_mat_1"),
                        "description": "Flooring, paint, doors, ironmongery",
                        "quantity": 24,
                        "unit": "EA",
                        "unit_cost_cents": 145000,
                        "total_cents": 3480000,
                    },
                ],
            },
        ]
