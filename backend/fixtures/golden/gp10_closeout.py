"""GP10 -- Office Refurbishment, Closeout Phase (AU -- Victoria).

Medium-complexity golden project: 8 workers (winding down from peak
of 15), 2 subs (mechanical, data/comms cabling), WorkSafe Victoria
regulations, project nearing practical completion.

Key scenario: **CLOSEOUT** -- punch list 80% complete, final quality
inspections, equipment demobilisation, lien waiver collection,
document generation for practical completion.

Workers: 8 (reduced from peak of 15)
Inspections: 4 (final walkthrough style)
Incidents: 0
Toolbox Talks: 1 (completed -- site cleanup safety)
Daily Logs: 3 (lighter activity reflecting wind-down)
Equipment: 2 items (1 returned, 1 active for final works)
Deficiency List: 1 (8 items: 6 closed, 2 open)
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP10_COMPANY, GP10_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP10Seeder(GoldenProjectSeeder):
    """Seed GP10: Office Refurb -- Closeout (Victoria, AU)."""

    GP_SLUG = "gp10"
    COMPANY_ID = "comp_gp10"
    PROJECT_ID = "proj_gp10"

    def seed(self) -> dict[str, int]:
        """Seed all GP10 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP10_COMPANY)
        self.seed_user(GP10_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Collins Street Level 12 Office Refurbishment",
            "address": "Level 12, 380 Collins Street, Melbourne VIC 3000",
            "client_name": "Meridian Partners Pty Ltd",
            "project_type": "commercial",
            "trade_types": ["general", "mechanical", "electrical"],
            "start_date": days_ago(90),
            "end_date": days_from_now(7),
            "estimated_workers": 15,
            "description": "Full floor office refurbishment -- 1,200 sqm open-plan "
                "office fitout with 4 meeting rooms, breakout area, server "
                "room, and kitchen. Demolition and rebuild of internal "
                "partitions, new HVAC distribution, LED lighting upgrade, "
                "structured data cabling, joinery, and finishes. "
                "Project in CLOSEOUT phase -- punch list 80% complete, "
                "practical completion targeted in 7 days.",
            "special_hazards": "Working in occupied building (other tenants "
                "on adjacent floors). Noise and dust management required. "
                "Asbestos register reviewed -- no ACMs in scope. "
                "Hot works permit required for final HVAC brazing.",
            "nearest_hospital": "The Royal Melbourne Hospital, "
                "300 Grattan Street, Parkville VIC 3050",
            "emergency_contact_name": "Ben Kowalski",
            "emergency_contact_phone": "+61-3-9654-7788",
            "state": "active",
            "status": "normal",
            "compliance_score": 92,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP10_USER["uid"],
            "actor_type": "human",
            "updated_by": GP10_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (8 remaining, down from peak 15) ---
        workers = self._build_workers()
        worker_ids = [w["id"] for w in workers]
        counts["workers"] = self.seed_workers(workers)
        self.assign_workers_to_project(worker_ids)

        # --- Inspections ---
        counts["inspections"] = self.seed_inspections(self._build_inspections())

        # --- Incidents (none) ---
        counts["incidents"] = 0

        # --- Equipment ---
        counts["equipment"] = self.seed_equipment(self._build_equipment())

        # --- Toolbox Talks ---
        counts["toolbox_talks"] = self.seed_toolbox_talks(self._build_talks())

        # --- Hazard Reports (none -- clean closeout) ---
        counts["hazard_reports"] = 0

        # --- Daily Logs ---
        counts["daily_logs"] = self.seed_daily_logs(self._build_daily_logs())

        # --- Deficiency List (punch list) ---
        punch_list_id = stable_id("dlist", "gp10_punch")
        counts["deficiency_lists"] = self.seed_deficiency_lists(
            self._build_deficiency_lists(punch_list_id),
        )
        counts["deficiency_items"] = self.seed_deficiency_items(
            self._build_deficiency_items(), punch_list_id,
        )

        # --- Work Items ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        return counts

    # -----------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------

    def _build_workers(self) -> list[dict]:
        """Build 8 workers remaining on site for closeout."""
        uid = GP10_USER["uid"]
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
                "id": stable_id("wkr", "gp10_ben"),
                "first_name": "Ben",
                "last_name": "Kowalski",
                "email": "ben@yarrafitout.com.au",
                "phone": "+61-3-9654-7788",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 12),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_ben_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 10),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2016-44521",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp10_ben_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(185),
                        "issuing_body": "St John Ambulance Australia",
                        "certificate_number": "SJAA-VIC-2025-8821",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp10_ben_asbestos"),
                        "certification_type": "asbestos_awareness",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(65),
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "AA-VIC-2025-1192",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp10_jack"),
                "first_name": "Jack",
                "last_name": "O'Sullivan",
                "email": "jack@yarrafitout.com.au",
                "phone": "+61-3-9654-7791",
                "role": "foreman",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_jack_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2021-78234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp10_tran"),
                "first_name": "Tran",
                "last_name": "Nguyen",
                "email": "",
                "phone": "+61-3-9654-7795",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_tran_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2023-11234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp10_sam"),
                "first_name": "Sam",
                "last_name": "Papadopoulos",
                "email": "",
                "phone": "+61-3-9654-7798",
                "role": "laborer",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "notes": "Joinery and finishes specialist -- on site for "
                    "punch list items.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_sam_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2024-33891",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Southbank Mechanical (mechanical / HVAC) ---
            {
                **base,
                "id": stable_id("wkr", "gp10_darren_mech"),
                "first_name": "Darren",
                "last_name": "Fletcher",
                "email": "darren@southbankmech.com.au",
                "phone": "+61-3-9654-8812",
                "role": "foreman",
                "trade": "hvac",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "notes": "Sub: Southbank Mechanical Pty Ltd. "
                    "Lien waiver RECEIVED.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_darren_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2020-4421",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp10_darren_refrigerant"),
                        "certification_type": "refrigerant_handling",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "ARC (Australian Refrigeration Council)",
                        "certificate_number": "ARC-VIC-2025-5567",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp10_nathan_mech"),
                "first_name": "Nathan",
                "last_name": "Brooks",
                "email": "",
                "phone": "+61-3-9654-8815",
                "role": "laborer",
                "trade": "hvac",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "notes": "Sub: Southbank Mechanical Pty Ltd",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_nathan_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2024-6689",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Yarra Data Solutions (data / comms cabling) ---
            {
                **base,
                "id": stable_id("wkr", "gp10_priya_data"),
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "priya@yarradata.com.au",
                "phone": "+61-3-9654-9901",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "notes": "Sub: Yarra Data Solutions Pty Ltd. "
                    "Lien waiver OUTSTANDING.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_priya_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2022-7723",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp10_priya_cabling"),
                        "certification_type": "structured_cabling",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "ACMA",
                        "certificate_number": "ACMA-VIC-2025-2201",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp10_liam_data"),
                "first_name": "Liam",
                "last_name": "Chen",
                "email": "",
                "phone": "+61-3-9654-9905",
                "role": "laborer",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "notes": "Sub: Yarra Data Solutions Pty Ltd",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp10_liam_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "WorkSafe Victoria",
                        "certificate_number": "VIC-WC-2025-8891",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 4 final walkthrough-style inspections."""
        uid = GP10_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            # Quality walkthrough -- 5 days ago
            {
                **base,
                "id": stable_id("insp", "gp10_quality_d5"),
                "inspection_type": "quality_walkthrough",
                "inspection_date": days_ago(5),
                "inspector_name": "Ben Kowalski",
                "inspector_id": stable_id("wkr", "gp10_ben"),
                "weather_conditions": "N/A (indoor)",
                "temperature": "22C",
                "workers_on_site": 10,
                "overall_status": "partial",
                "overall_notes": "Walkthrough with client representative. "
                    "Punch list generated -- 8 items identified. "
                    "Joinery touch-ups needed in meeting rooms 2 and 4. "
                    "HVAC commissioning incomplete in server room. "
                    "Overall finish quality rated as good.",
                "corrective_actions_needed": "See punch list dlist_gp10_punch "
                    "for full item list. Target: all items closed within "
                    "5 working days.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            # Fire safety inspection -- 3 days ago
            {
                **base,
                "id": stable_id("insp", "gp10_fire_d3"),
                "inspection_type": "fire_safety",
                "inspection_date": days_ago(3),
                "inspector_name": "Jack O'Sullivan",
                "inspector_id": stable_id("wkr", "gp10_jack"),
                "weather_conditions": "N/A (indoor)",
                "temperature": "22C",
                "workers_on_site": 8,
                "overall_status": "pass",
                "overall_notes": "Fire detection and suppression systems "
                    "tested and commissioned. Emergency lighting operational. "
                    "Exit signage installed and illuminated. "
                    "Fire extinguishers placed per plan. "
                    "Essential Safety Measures report prepared.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            # HVAC commissioning -- 2 days ago
            {
                **base,
                "id": stable_id("insp", "gp10_hvac_d2"),
                "inspection_type": "hvac_commissioning",
                "inspection_date": days_ago(2),
                "inspector_name": "Darren Fletcher",
                "inspector_id": stable_id("wkr", "gp10_darren_mech"),
                "weather_conditions": "N/A (indoor)",
                "temperature": "21C",
                "workers_on_site": 8,
                "overall_status": "pass",
                "overall_notes": "Server room HVAC unit commissioned. "
                    "Airflow balancing completed across all zones. "
                    "BMS integration verified -- all sensors reporting. "
                    "Temperature set-points calibrated per spec. "
                    "Punch list item 5 (server room HVAC) now resolved.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
            # Final walkthrough -- yesterday
            {
                **base,
                "id": stable_id("insp", "gp10_final_d1"),
                "inspection_type": "quality_walkthrough",
                "inspection_date": days_ago(1),
                "inspector_name": "Ben Kowalski",
                "inspector_id": stable_id("wkr", "gp10_ben"),
                "weather_conditions": "N/A (indoor)",
                "temperature": "22C",
                "workers_on_site": 6,
                "overall_status": "partial",
                "overall_notes": "Progress walkthrough -- 6 of 8 punch list "
                    "items corrected and signed off. "
                    "Remaining: meeting room 4 joinery touch-up (paint "
                    "drying), data outlet labelling in open plan (scheduled "
                    "for tomorrow). "
                    "Client expressed satisfaction with progress. "
                    "Practical completion on track for target date.",
                "corrective_actions_needed": "Complete final 2 punch list "
                    "items. Prepare practical completion certificate. "
                    "Collect outstanding lien waiver from Yarra Data.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build equipment -- 1 returned, 1 still active."""
        uid = GP10_USER["uid"]
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
                "id": stable_id("eq", "gp10_scissorlift"),
                "name": "JLG 1930ES Scissor Lift",
                "equipment_type": "scissor_lift",
                "make": "JLG",
                "model": "1930ES",
                "year": 2023,
                "serial_number": "JLG-1930-2023-VIC-4421",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(5),
                "next_inspection_due": None,
                "status": "returned",
                "notes": "Returned to Kennards Hire on "
                    + days_ago(4) + ". "
                    "Used for ceiling grid and HVAC distribution work. "
                    "No longer required -- all overhead work complete.",
            },
            {
                **base,
                "id": stable_id("eq", "gp10_dustextractor"),
                "name": "Festool CTL 36 Dust Extractor",
                "equipment_type": "dust_control",
                "make": "Festool",
                "model": "CTL 36 E AC",
                "year": 2024,
                "serial_number": "FEST-CTL36-2024-VIC-1178",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "daily",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "status": "active",
                "notes": "Required for final joinery and touch-up work. "
                    "M-class extraction for occupied building compliance.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 1 completed toolbox talk on site cleanup safety."""
        uid = GP10_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [{
            **base,
            "id": stable_id("talk", "gp10_cleanup_safety"),
            "topic": "Site Cleanup and Demobilisation Safety",
            "scheduled_date": days_ago(3),
            "target_audience": "all_workers",
            "duration_minutes": 15,
            "language": "en",
            "status": "completed",
            "presented_at": datetime_days_ago(3, hour=7),
            "presented_by": "Ben Kowalski",
            "overall_notes": "Covered safe removal of temporary services. "
                "Manual handling for equipment demobilisation. "
                "Waste segregation for skip collection. "
                "Reminded all workers to maintain housekeeping during "
                "closeout -- client occupying adjacent areas. "
                "Discussed scissor lift return logistics.",
            "created_at": datetime_days_ago(4),
            "updated_at": datetime_days_ago(3),
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build 3 daily logs reflecting lighter closeout activity."""
        uid = GP10_USER["uid"]
        base = {
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }
        return [
            # 3 days ago
            {
                **base,
                "id": stable_id("dlog", "gp10_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Ben Kowalski",
                "status": "approved",
                "workers_on_site": 8,
                "work_performed": "Punch list items 1-3 completed (paint "
                    "touch-ups in reception, carpet edge re-fixed in "
                    "breakout area, door closer adjusted on meeting room 1). "
                    "Scissor lift returned to Kennards Hire. "
                    "Fire safety inspection passed. "
                    "Toolbox talk on cleanup safety delivered.",
                "notes": "Southbank Mechanical lien waiver received. "
                    "Yarra Data lien waiver requested -- follow up required.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(2),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": datetime_days_ago(2, hour=8),
            },
            # Yesterday
            {
                **base,
                "id": stable_id("dlog", "gp10_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Ben Kowalski",
                "status": "submitted",
                "workers_on_site": 6,
                "work_performed": "Punch list items 4-6 completed (server room "
                    "HVAC commissioning signed off, LED dimming recalibrated "
                    "in open plan zone 3, kitchen splashback silicone re-sealed). "
                    "Item 7 (meeting room 4 joinery) in progress -- paint "
                    "applied, drying overnight. "
                    "Final walkthrough with Ben and client rep.",
                "notes": "6 of 8 punch items now closed. 2 remaining for "
                    "tomorrow. Practical completion certificate being drafted. "
                    "Still awaiting Yarra Data lien waiver.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
            # Today (draft)
            {
                **base,
                "id": stable_id("dlog", "gp10_today"),
                "log_date": days_ago(0),
                "superintendent_name": "Ben Kowalski",
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
    # Deficiency Lists (Punch Lists)
    # -----------------------------------------------------------------

    def _build_deficiency_lists(self, list_id: str) -> list[dict]:
        """Build the closeout punch list."""
        uid = GP10_USER["uid"]
        return [{
            "id": list_id,
            "name": "Practical Completion Punch List",
            "description": "Items identified during quality walkthrough "
                "with client on " + days_ago(5) + ". "
                "8 items total: 6 corrected/closed, 2 open.",
            "status": "in_progress",
            "total_items": 8,
            "closed_items": 6,
            "open_items": 2,
            "created_at": datetime_days_ago(5),
            "updated_at": datetime_days_ago(1),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    def _build_deficiency_items(self) -> list[dict]:
        """Build 8 punch list items: 6 closed, 2 open."""
        uid = GP10_USER["uid"]
        base_closed = {
            "status": "closed",
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        base_open = {
            "status": "open",
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            # --- CLOSED items (1-6) ---
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_01"),
                "item_number": 1,
                "description": "Paint touch-up required on reception feature "
                    "wall -- visible roller marks under task lighting.",
                "location": "Reception area, north wall",
                "trade": "painting",
                "priority": "medium",
                "corrected_at": datetime_days_ago(3),
                "corrected_by": "Jack O'Sullivan",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_02"),
                "item_number": 2,
                "description": "Carpet tile edge lifting at transition "
                    "strip in breakout area.",
                "location": "Breakout area, east entrance",
                "trade": "flooring",
                "priority": "low",
                "corrected_at": datetime_days_ago(3),
                "corrected_by": "Sam Papadopoulos",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_03"),
                "item_number": 3,
                "description": "Door closer on meeting room 1 over-tightened "
                    "-- door slamming shut.",
                "location": "Meeting room 1",
                "trade": "carpentry",
                "priority": "medium",
                "corrected_at": datetime_days_ago(3),
                "corrected_by": "Jack O'Sullivan",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_04"),
                "item_number": 4,
                "description": "Server room HVAC unit not commissioned -- "
                    "temperature control not functional.",
                "location": "Server room",
                "trade": "mechanical",
                "priority": "high",
                "corrected_at": datetime_days_ago(2),
                "corrected_by": "Darren Fletcher",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_05"),
                "item_number": 5,
                "description": "LED dimming in open-plan zone 3 not responding "
                    "to BMS schedule -- stuck at 100%.",
                "location": "Open plan, zone 3 (south-west quadrant)",
                "trade": "electrical",
                "priority": "medium",
                "corrected_at": datetime_days_ago(1),
                "corrected_by": "Priya Sharma",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base_closed,
                "id": stable_id("di", "gp10_punch_06"),
                "item_number": 6,
                "description": "Kitchen splashback silicone bead uneven "
                    "behind sink -- visible gap at left corner.",
                "location": "Kitchen, behind main sink",
                "trade": "general",
                "priority": "low",
                "corrected_at": datetime_days_ago(1),
                "corrected_by": "Sam Papadopoulos",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(1),
            },
            # --- OPEN items (7-8) ---
            {
                **base_open,
                "id": stable_id("di", "gp10_punch_07"),
                "item_number": 7,
                "description": "Meeting room 4 joinery -- veneer edge strip "
                    "lifting on credenza. Needs re-gluing and touch-up.",
                "location": "Meeting room 4",
                "trade": "carpentry",
                "priority": "medium",
                "corrected_at": None,
                "corrected_by": None,
                "notes": "Repair in progress -- adhesive applied, "
                    "paint touch-up drying overnight.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base_open,
                "id": stable_id("di", "gp10_punch_08"),
                "item_number": 8,
                "description": "Data outlet labelling incomplete in open-plan "
                    "area -- 12 outlets missing labels per cabling schedule.",
                "location": "Open plan area, various locations",
                "trade": "electrical",
                "priority": "low",
                "corrected_at": None,
                "corrected_by": None,
                "notes": "Scheduled for completion tomorrow. "
                    "Labels printed, awaiting installation by Yarra Data.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Work Items (quote / scope of works)
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active office refurbishment closeout.

        Active project in closeout phase \u2014 items reflect the in-flight scope.
        All values in cents (AUD).
        """
        uid = GP10_USER["uid"]
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
                "id": stable_id("wi", "gp10_item_1"),
                "description": "Strip-out \u2014 existing Level 12 fitout",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 18,
                "labour_total_cents": 220000,
                "items_total_cents": 85000,
                "sell_price_cents": 359900,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp10_lab_1"),
                        "task": "Soft strip and make safe",
                        "rate_cents": 5500,
                        "hours": 40,
                        "cost_cents": 220000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp10_item_1_mat_1"),
                        "description": "Waste removal and hoarding",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 85000,
                        "total_cents": 85000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp10_item_2"),
                "description": "Partitions and glazed offices \u2014 12 meeting rooms",
                "quantity": 12,
                "unit": "EA",
                "margin_pct": 22,
                "labour_total_cents": 520000,
                "items_total_cents": 4620000,
                "sell_price_cents": 6270800,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp10_lab_2"),
                        "task": "Frame and glaze partitions",
                        "rate_cents": 6500,
                        "hours": 80,
                        "cost_cents": 520000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp10_item_2_mat_1"),
                        "description": "Glazed partition system",
                        "quantity": 12,
                        "unit": "EA",
                        "unit_cost_cents": 385000,
                        "total_cents": 4620000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp10_item_3"),
                "description": "Ceiling grid and acoustic tiles",
                "quantity": 1400,
                "unit": "SM",
                "margin_pct": 20,
                "labour_total_cents": 440000,
                "items_total_cents": 1680000,
                "sell_price_cents": 2544000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp10_lab_3"),
                        "task": "Install suspended ceiling",
                        "rate_cents": 5500,
                        "hours": 80,
                        "cost_cents": 440000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp10_item_3_mat_1"),
                        "description": "Ceiling grid and tiles",
                        "quantity": 1400,
                        "unit": "SM",
                        "unit_cost_cents": 1200,
                        "total_cents": 1680000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp10_item_4"),
                "description": "Carpet tile installation throughout",
                "quantity": 1400,
                "unit": "SM",
                "margin_pct": 22,
                "labour_total_cents": 216000,
                "items_total_cents": 5320000,
                "sell_price_cents": 6753920,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp10_lab_4"),
                        "task": "Prep and install carpet tiles",
                        "rate_cents": 4500,
                        "hours": 48,
                        "cost_cents": 216000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp10_item_4_mat_1"),
                        "description": "Carpet tiles Interface Grade A",
                        "quantity": 1400,
                        "unit": "SM",
                        "unit_cost_cents": 3800,
                        "total_cents": 5320000,
                    },
                ],
            },
        ]
