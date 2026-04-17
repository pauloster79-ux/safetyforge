"""GP04 — Custom Home Build (US — California).

Medium-complexity golden project: 12 workers, 4 subs, Cal/OSHA state
regs, mixed certification states (valid, expired, expiring soon),
time tracking with cost codes, sub COI tracking, quality inspections,
daily logs auto-populated, weekly lookahead schedule.

Exercises most current features including:
- Workers with varied cert states
- Multiple inspection types (daily, scaffold, fall protection)
- One near-miss incident (investigating)
- Equipment (scaffold system, aerial lift)
- Toolbox talks (completed + scheduled)
- Daily logs with multi-day history
- Hazard report (corrected)
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP04_COMPANY, GP04_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP04Seeder(GoldenProjectSeeder):
    """Seed GP04: Custom Home Build — California."""

    GP_SLUG = "gp04"
    COMPANY_ID = "comp_gp04"
    PROJECT_ID = "proj_gp04"

    def seed(self) -> dict[str, int]:
        """Seed all GP04 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP04_COMPANY)
        self.seed_user(GP04_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Hillside Custom Residence — Lot 14",
            "address": "14 Skyview Terrace, Woodside, CA 94062",
            "client_name": "Dr. Robert & Lisa Kim",
            "project_type": "residential",
            "trade_types": ["general", "electrical", "plumbing", "hvac"],
            "start_date": days_ago(60),
            "end_date": days_from_now(120),
            "estimated_workers": 12,
            "description": "4,200 sq ft custom residence on hillside lot. "
                "Steel moment frame construction, post-tension slab, "
                "three levels with cantilevered deck. Currently in framing "
                "and MEP rough-in phase.",
            "special_hazards": "Steep hillside grade (35% slope). "
                "Fall hazard on cantilevered deck framing. "
                "Proximity to seasonal creek — erosion control required. "
                "Cal/OSHA heat illness prevention plan required (outdoor work).",
            "nearest_hospital": "Stanford Health Care, "
                "300 Pasteur Drive, Palo Alto, CA 94304",
            "emergency_contact_name": "David Nguyen",
            "emergency_contact_phone": "650-555-0489",
            "state": "active",
            "status": "normal",
            "compliance_score": 72,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP04_USER["uid"],
            "actor_type": "human",
            "updated_by": GP04_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (12 across own crew + subs) ---
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

        # --- Quoting: Work Items with Labour/Item children ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        # --- Quoting: Resource Rates (company library) ---
        counts["resource_rates"] = self.seed_resource_rates(
            self._build_resource_rates()
        )

        # --- Quoting: Productivity Rates (company library) ---
        counts["productivity_rates"] = self.seed_productivity_rates(
            self._build_productivity_rates()
        )

        # --- Quoting: Assumption Templates (company-level) ---
        counts["assumption_templates"] = self.seed_assumption_templates(
            self._build_assumption_templates()
        )

        # --- Quoting: Exclusion Templates (company-level) ---
        counts["exclusion_templates"] = self.seed_exclusion_templates(
            self._build_exclusion_templates()
        )

        # --- Additional Resource Rates (multi-trade library) ---
        counts["resource_rates"] += self.seed_resource_rates(
            self._build_additional_resource_rates()
        )

        # --- Additional Productivity Rates (multi-trade) ---
        counts["productivity_rates"] += self.seed_productivity_rates(
            self._build_additional_productivity_rates()
        )

        # --- Completed Project (for source cascade testing) ---
        completed_pid = "proj_gp04_completed"
        self.seed_project(self._build_completed_project())
        completed_wi = self._build_completed_work_items(completed_pid)
        counts["completed_work_items"] = self.seed_work_items_for_project(
            completed_wi, completed_pid,
        )

        # --- Completed Project: Contract with milestones, conditions, warranty ---
        completed_contract_id = stable_id("contract", "gp04_completed")
        self.seed_contract(
            self._build_completed_contract(completed_contract_id, completed_pid),
            project_id=completed_pid,
        )
        counts["payment_milestones"] = self.seed_payment_milestones(
            self._build_completed_milestones(completed_contract_id),
            contract_id=completed_contract_id,
        )
        counts["conditions"] = self.seed_conditions(
            self._build_completed_conditions(completed_contract_id),
            contract_id=completed_contract_id,
        )
        self.seed_warranty(
            self._build_completed_warranty(completed_contract_id),
            contract_id=completed_contract_id,
        )
        counts["warranty"] = 1

        return counts

    def seed_work_items_for_project(
        self, work_items: list[dict], project_id: str,
    ) -> int:
        """Seed work items into a specific project (not self.PROJECT_ID).

        Args:
            work_items: List of work item dicts with optional children.
            project_id: Target project ID.

        Returns:
            Number of work items seeded.
        """
        with self.driver.session(database=self.database) as session:
            for wi in work_items:
                session.execute_write(
                    self._merge_work_item, wi, self.COMPANY_ID, project_id,
                )
                for lab in wi.get("labour", []):
                    session.execute_write(self._merge_labour, lab, wi["id"])
                for item in wi.get("items", []):
                    session.execute_write(self._merge_item, item, wi["id"])
        return len(work_items)

    # -----------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------

    def _build_workers(self) -> list[dict]:
        uid = GP04_USER["uid"]
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
            # --- Own crew (GC) ---
            {
                **base,
                "id": stable_id("wkr", "gp04_david"),
                "first_name": "David",
                "last_name": "Nguyen",
                "email": "david@pacificcoastconstruction.com",
                "phone": "650-555-0489",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_david_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-CA-23-1192",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_david_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(915),
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "FP-CA-2025-4421",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_david_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(65),
                        "issuing_body": "American Red Cross",
                        "certificate_number": "ARC-CPR-2025-33891",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_carlos"),
                "first_name": "Carlos",
                "last_name": "Ramirez",
                "email": "carlos@pacificcoastconstruction.com",
                "phone": "650-555-0512",
                "role": "foreman",
                "trade": "general",
                "language_preference": "both",
                "hire_date": days_ago(365 * 4),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_carlos_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-22-8834",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_carlos_scaffold"),
                        "certification_type": "scaffold_competent",
                        "issued_date": days_ago(400),
                        "expiry_date": days_ago(35),  # EXPIRED
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "SC-CA-2024-1145",
                        "status": "expired",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_jose"),
                "first_name": "Jose",
                "last_name": "Gutierrez",
                "email": "",
                "phone": "650-555-0534",
                "role": "laborer",
                "trade": "general",
                "language_preference": "es",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_jose_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-24-2291",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_jose_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(100),
                        "expiry_date": days_from_now(995),
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "FP-CA-2026-0221",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_alex"),
                "first_name": "Alex",
                "last_name": "Kim",
                "email": "alex@pacificcoastconstruction.com",
                "phone": "650-555-0578",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(90),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_alex_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(120),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-25-9912",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_miguel"),
                "first_name": "Miguel",
                "last_name": "Santos",
                "email": "",
                "phone": "650-555-0599",
                "role": "apprentice",
                "trade": "general",
                "language_preference": "es",
                "hire_date": days_ago(30),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_miguel_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(45),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-26-0034",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Peninsula Electric (electrical) ---
            {
                **base,
                "id": stable_id("wkr", "gp04_tom_elec"),
                "first_name": "Tom",
                "last_name": "Brennan",
                "email": "tom@peninsulaelectric.com",
                "phone": "650-555-0621",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "notes": "Sub: Peninsula Electric",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_tom_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-23-4456",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_tom_electrical"),
                        "certification_type": "electrical_safety",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(530),
                        "issuing_body": "NFPA",
                        "certificate_number": "NFPA-70E-2025-2201",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_kevin_elec"),
                "first_name": "Kevin",
                "last_name": "O'Brien",
                "email": "",
                "phone": "650-555-0633",
                "role": "journeyman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "notes": "Sub: Peninsula Electric",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_kevin_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-23-4457",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Bay Area Plumbing (plumbing) ---
            {
                **base,
                "id": stable_id("wkr", "gp04_rachel_plumb"),
                "first_name": "Rachel",
                "last_name": "Huang",
                "email": "rachel@bayareaplumbing.com",
                "phone": "408-555-0712",
                "role": "foreman",
                "trade": "plumbing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "notes": "Sub: Bay Area Plumbing",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_rachel_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-24-7723",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_rachel_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(500),
                        "expiry_date": days_from_now(25),  # EXPIRING SOON
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "CS-CA-2024-0098",
                        "status": "expiring_soon",
                    },
                ],
            },
            # --- Sub: SV HVAC Solutions ---
            {
                **base,
                "id": stable_id("wkr", "gp04_jason_hvac"),
                "first_name": "Jason",
                "last_name": "Park",
                "email": "jason@svhvac.com",
                "phone": "408-555-0845",
                "role": "foreman",
                "trade": "hvac",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "notes": "Sub: SV HVAC Solutions",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_jason_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-23-8891",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Summit Framing (framing — under GC general) ---
            {
                **base,
                "id": stable_id("wkr", "gp04_derek_frame"),
                "first_name": "Derek",
                "last_name": "Johnson",
                "email": "derek@summitframing.com",
                "phone": "650-555-0901",
                "role": "foreman",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "notes": "Sub: Summit Framing",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_derek_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-22-1134",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_derek_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "FP-CA-2025-3312",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_derek_scaffold"),
                        "certification_type": "scaffold_competent",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "SC-CA-2025-0445",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_luis_frame"),
                "first_name": "Luis",
                "last_name": "Herrera",
                "email": "",
                "phone": "650-555-0918",
                "role": "laborer",
                "trade": "carpentry",
                "language_preference": "es",
                "hire_date": days_ago(365 * 2),
                "notes": "Sub: Summit Framing",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_luis_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-23-5567",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp04_omar_frame"),
                "first_name": "Omar",
                "last_name": "Vasquez",
                "email": "",
                "phone": "650-555-0925",
                "role": "laborer",
                "trade": "carpentry",
                "language_preference": "es",
                "hire_date": days_ago(365),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp04_omar_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-CA-24-3398",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp04_omar_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "Cal/OSHA",
                        "certificate_number": "FP-CA-2025-3313",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        uid = GP04_USER["uid"]
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
                "id": stable_id("insp", "gp04_daily_d5"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(5),
                "inspector_name": "David Nguyen",
                "inspector_id": stable_id("wkr", "gp04_david"),
                "weather_conditions": "Sunny",
                "temperature": "72°F",
                "workers_on_site": 8,
                "overall_status": "pass",
                "overall_notes": "All PPE in use. Housekeeping good. "
                    "Fall protection systems in place on upper level.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp04_daily_d3"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "David Nguyen",
                "inspector_id": stable_id("wkr", "gp04_david"),
                "weather_conditions": "Foggy morning, clearing",
                "temperature": "61°F",
                "workers_on_site": 10,
                "overall_status": "pass",
                "overall_notes": "All areas compliant. HVAC sub on site for "
                    "ductwork rough-in — verified their PPE compliance.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("insp", "gp04_scaffold1"),
                "inspection_type": "scaffold",
                "inspection_date": days_ago(7),
                "inspector_name": "Derek Johnson",
                "inspector_id": stable_id("wkr", "gp04_derek_frame"),
                "weather_conditions": "Clear",
                "temperature": "68°F",
                "workers_on_site": 6,
                "overall_status": "fail",
                "overall_notes": "Scaffold on south elevation missing mid-rail "
                    "on second tier. Guardrail post loose at NE corner.",
                "corrective_actions_needed": "Install mid-rail on south scaffold "
                    "second tier. Tighten/replace NE guardrail post coupling. "
                    "Re-inspect before use.",
                "items": "[]",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
            },
            {
                **base,
                "id": stable_id("insp", "gp04_fall1"),
                "inspection_type": "fall_protection",
                "inspection_date": days_ago(2),
                "inspector_name": "David Nguyen",
                "inspector_id": stable_id("wkr", "gp04_david"),
                "weather_conditions": "Partly cloudy",
                "temperature": "65°F",
                "workers_on_site": 11,
                "overall_status": "partial",
                "overall_notes": "Guardrails on upper deck framing OK. "
                    "Personal fall arrest systems inspected — 1 lanyard "
                    "showing wear, tagged out. "
                    "Warning line system on lower roof not extending to "
                    "full perimeter.",
                "corrective_actions_needed": "Replace worn lanyard (tagged SN-4421). "
                    "Extend warning line system to cover west edge of lower roof.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("insp", "gp04_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Carlos Ramirez",
                "inspector_id": stable_id("wkr", "gp04_carlos"),
                "weather_conditions": "Sunny",
                "temperature": "74°F",
                "workers_on_site": 12,
                "overall_status": "pass",
                "overall_notes": "Full crew on site. All corrective actions from "
                    "scaffold inspection completed. Scaffold re-inspected and cleared.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        uid = GP04_USER["uid"]
        return [{
            "id": stable_id("inc", "gp04_nearmiss1"),
            "incident_date": days_ago(4),
            "incident_time": "14:30",
            "location": "Upper level deck framing, south side",
            "severity": "near_miss",
            "status": "investigating",
            "description": "Material (2x10 board) slid off upper deck during "
                "wind gust and fell approximately 18 feet to grade below. "
                "No workers in the fall zone at the time. Board landed on "
                "material staging area. No injuries, no property damage.",
            "persons_involved": "Omar Vasquez (was handling material), "
                "Luis Herrera (nearby)",
            "involved_worker_ids": [
                stable_id("wkr", "gp04_omar_frame"),
                stable_id("wkr", "gp04_luis_frame"),
            ],
            "witnesses": "Derek Johnson (foreman)",
            "immediate_actions_taken": "Stopped work on upper deck. "
                "Established exclusion zone below. "
                "Reviewed material handling procedures with framing crew.",
            "root_cause": "Under investigation. Possible contributing factors: "
                "wind speed exceeded safe working threshold for loose materials, "
                "materials not secured with toe boards or netting.",
            "corrective_actions": "Install debris netting on south elevation. "
                "Add toe boards to all open deck edges. "
                "Establish wind speed threshold (20 mph) for material handling "
                "on upper level.",
            "osha_recordable": False,
            "osha_reportable": False,
            "photo_urls": [],
            "created_at": datetime_days_ago(4),
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
        uid = GP04_USER["uid"]
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
                "id": stable_id("eq", "gp04_scaffold1"),
                "name": "Safway Systems Frame Scaffold — South Elevation",
                "equipment_type": "scaffold_system",
                "make": "Safway",
                "model": "Systems Scaffold",
                "serial_number": "SAF-2022-4421",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "daily",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "notes": "3-tier scaffold, south elevation. "
                    "Re-inspected after corrective actions on mid-rail.",
            },
            {
                **base,
                "id": stable_id("eq", "gp04_lift1"),
                "name": "JLG 450AJ Articulating Boom Lift",
                "equipment_type": "aerial_lift",
                "make": "JLG",
                "model": "450AJ",
                "year": 2021,
                "serial_number": "JLG-450AJ-2021-78234",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "annual_inspection_date": days_ago(90),
                "annual_inspection_due": days_from_now(275),
                "annual_inspection_vendor": "United Rentals",
                "notes": "Rented from United Rentals. "
                    "45 ft working height. Operators must have aerial lift cert.",
            },
            {
                **base,
                "id": stable_id("eq", "gp04_generator1"),
                "name": "Honda EU7000iS Generator",
                "equipment_type": "generator",
                "make": "Honda",
                "model": "EU7000iS",
                "year": 2023,
                "serial_number": "HONDA-EU7-2023-11234",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "weekly",
                "last_inspection_date": days_ago(3),
                "next_inspection_due": days_from_now(4),
                "notes": "Powers temporary lighting and tool charging station.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        uid = GP04_USER["uid"]
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
                "id": stable_id("talk", "gp04_fall_protection"),
                "topic": "Fall Protection on Elevated Decks",
                "scheduled_date": days_ago(6),
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "language": "both",
                "status": "completed",
                "presented_at": datetime_days_ago(6, hour=7),
                "presented_by": "David Nguyen",
                "overall_notes": "Reviewed Cal/OSHA 6-foot fall protection rule. "
                    "Demonstrated proper harness inspection and lanyard selection. "
                    "Discussed near-miss from day before.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
            },
            {
                **base,
                "id": stable_id("talk", "gp04_heat_illness"),
                "topic": "Heat Illness Prevention — Cal/OSHA Requirements",
                "scheduled_date": days_from_now(1),
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "language": "both",
                "status": "scheduled",
                "presented_at": None,
                "presented_by": "",
                "overall_notes": "",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            },
        ]

    # -----------------------------------------------------------------
    # Hazard Reports
    # -----------------------------------------------------------------

    def _build_hazards(self) -> list[dict]:
        uid = GP04_USER["uid"]
        return [{
            "id": stable_id("haz", "gp04_tripping1"),
            "description": "Extension cords running across main walkway "
                "between material staging and building entry. "
                "Tripping hazard for all trades.",
            "location": "Main entry walkway, ground level",
            "status": "corrected",
            "hazard_count": 1,
            "highest_severity": "medium",
            "corrective_action_taken": "Installed cord covers on all walkways. "
                "Rerouted two cords overhead using cord hangers. "
                "Added caution tape to remaining ground-level crossing.",
            "corrected_at": datetime_days_ago(8),
            "corrected_by": "Carlos Ramirez",
            "created_at": datetime_days_ago(10),
            "updated_at": datetime_days_ago(8),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        uid = GP04_USER["uid"]
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
                "id": stable_id("dlog", "gp04_d7"),
                "log_date": days_ago(7),
                "superintendent_name": "David Nguyen",
                "status": "approved",
                "workers_on_site": 6,
                "work_performed": "Framing crew continued upper level wall framing. "
                    "Electrical rough-in started on lower level. "
                    "Scaffold erected on south elevation for exterior sheathing.",
                "notes": "Scaffold inspection failed — corrective actions assigned. "
                    "See inspection report.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
                "submitted_at": datetime_days_ago(7, hour=17),
                "approved_at": datetime_days_ago(6, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp04_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "David Nguyen",
                "status": "approved",
                "workers_on_site": 8,
                "work_performed": "Scaffold corrective actions completed — "
                    "mid-rail installed, guardrail post replaced. "
                    "Re-inspection passed. "
                    "Upper level deck framing 60% complete. "
                    "Electrical running circuits for kitchen panel.",
                "notes": "Good progress day. Weather cooperating.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp04_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "David Nguyen",
                "status": "submitted",
                "workers_on_site": 10,
                "work_performed": "HVAC ductwork rough-in started — SV HVAC on site. "
                    "Framing crew completing upper deck cantilever section. "
                    "Plumbing rough-in 80% complete on lower level.",
                "notes": "Near-miss incident yesterday being investigated. "
                    "Debris netting ordered for south elevation.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp04_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "David Nguyen",
                "status": "submitted",
                "workers_on_site": 12,
                "work_performed": "Full crew on site. Debris netting installed "
                    "on south elevation. Upper deck framing 85% complete. "
                    "Electrical panel set in garage. "
                    "HVAC main trunk lines hung on lower level.",
                "notes": "All corrective actions from scaffold and fall protection "
                    "inspections now complete. Warning line extended on lower roof.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp04_today"),
                "log_date": days_ago(0),
                "superintendent_name": "David Nguyen",
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
    # Work Items with Labour & Item children
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        uid = GP04_USER["uid"]
        base = {
            "state": "draft",
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
        }

        return [
            {
                **base,
                "id": stable_id("wi", "gp04_panel_upgrade"),
                "description": "200A Main Panel Upgrade — supply and install",
                "quantity": 1.0,
                "unit": "LS",
                "margin_pct": 15.0,
                "labour_total_cents": 225000,
                "items_total_cents": 165000,
                "sell_price_cents": 448500,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_panel_install"),
                        "task": "Install 200A main panel and 2 sub-panels",
                        "rate_cents": 15000,
                        "hours": 12.0,
                        "cost_cents": 180000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_panel_terminate"),
                        "task": "Terminate circuits and label",
                        "rate_cents": 15000,
                        "hours": 3.0,
                        "cost_cents": 45000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_panel_main"),
                        "description": "200A Main Breaker Panel (Square D HOM3060M200PC)",
                        "product": "Square D HOM3060M200PC",
                        "quantity": 1.0,
                        "unit": "EA",
                        "unit_cost_cents": 85000,
                        "total_cents": 85000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_panel_sub"),
                        "description": "100A Sub-Panel (Square D HOM2040M100PC)",
                        "product": "Square D HOM2040M100PC",
                        "quantity": 2.0,
                        "unit": "EA",
                        "unit_cost_cents": 40000,
                        "total_cents": 80000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04_rough_wiring"),
                "description": "Rough wiring — all circuits per plan E-1 through E-4",
                "quantity": 1.0,
                "unit": "LS",
                "margin_pct": 15.0,
                "labour_total_cents": 960000,
                "items_total_cents": 415000,
                "sell_price_cents": 1581250,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_conduit_run"),
                        "task": "Run EMT conduit — 450 LF",
                        "rate_cents": 15000,
                        "hours": 14.0,
                        "cost_cents": 210000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_romex_pull"),
                        "task": "Pull NM cable — branch circuits",
                        "rate_cents": 12000,
                        "hours": 24.0,
                        "cost_cents": 288000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_box_install"),
                        "task": "Install boxes, receptacles, switches",
                        "rate_cents": 12000,
                        "hours": 18.0,
                        "cost_cents": 216000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_fixture_rough"),
                        "task": "Rough in light fixture locations",
                        "rate_cents": 12300,
                        "hours": 20.0,
                        "cost_cents": 246000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_emt_conduit"),
                        "description": "3/4\" EMT Conduit",
                        "product": "",
                        "quantity": 450.0,
                        "unit": "LF",
                        "unit_cost_cents": 250,
                        "total_cents": 112500,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_nm_cable"),
                        "description": "14/2 NM-B Cable (Romex)",
                        "product": "Southwire 14/2 NM-B",
                        "quantity": 2000.0,
                        "unit": "LF",
                        "unit_cost_cents": 55,
                        "total_cents": 110000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_receptacles"),
                        "description": "Duplex receptacles — 20A spec grade",
                        "product": "Leviton 5362-W",
                        "quantity": 85.0,
                        "unit": "EA",
                        "unit_cost_cents": 850,
                        "total_cents": 72250,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_switches"),
                        "description": "Decora switches — single pole",
                        "product": "Leviton 5601-2W",
                        "quantity": 40.0,
                        "unit": "EA",
                        "unit_cost_cents": 300,
                        "total_cents": 12000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_boxes"),
                        "description": "Device boxes — single gang",
                        "product": "",
                        "quantity": 125.0,
                        "unit": "EA",
                        "unit_cost_cents": 865,
                        "total_cents": 108125,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04_lighting"),
                "description": "Lighting package — supply and install per schedule L-1",
                "quantity": 1.0,
                "unit": "LS",
                "margin_pct": 20.0,
                "labour_total_cents": 480000,
                "items_total_cents": 850000,
                "sell_price_cents": 1596000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_light_install"),
                        "task": "Install light fixtures — 42 locations",
                        "rate_cents": 15000,
                        "hours": 24.0,
                        "cost_cents": 360000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_dimmer_install"),
                        "task": "Install dimmer controls and scenes",
                        "rate_cents": 15000,
                        "hours": 8.0,
                        "cost_cents": 120000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_recessed_lights"),
                        "description": "6\" LED recessed downlight (Halo RL6)",
                        "product": "Halo RL6",
                        "quantity": 32.0,
                        "unit": "EA",
                        "unit_cost_cents": 15000,
                        "total_cents": 480000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_pendant_lights"),
                        "description": "Pendant fixtures — kitchen island (owner supplied)",
                        "product": "Restoration Hardware — owner supplied",
                        "quantity": 3.0,
                        "unit": "EA",
                        "unit_cost_cents": 0,
                        "total_cents": 0,
                        "notes": "Owner-supplied — install only",
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_dimmers"),
                        "description": "Lutron Caseta dimmer switches",
                        "product": "Lutron PD-6WCL-WH",
                        "quantity": 12.0,
                        "unit": "EA",
                        "unit_cost_cents": 5500,
                        "total_cents": 66000,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_exterior_lights"),
                        "description": "Exterior wall sconces (LED)",
                        "product": "",
                        "quantity": 8.0,
                        "unit": "EA",
                        "unit_cost_cents": 38000,
                        "total_cents": 304000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04_ev_charger"),
                "description": "EV charger circuit — garage, 60A dedicated",
                "quantity": 1.0,
                "unit": "EA",
                "margin_pct": 15.0,
                "labour_total_cents": 90000,
                "items_total_cents": 45000,
                "sell_price_cents": 155250,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_ev_run"),
                        "task": "Run 60A circuit from sub-panel to garage",
                        "rate_cents": 15000,
                        "hours": 6.0,
                        "cost_cents": 90000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_ev_wire"),
                        "description": "6/3 NM-B Cable for 60A circuit",
                        "product": "",
                        "quantity": 75.0,
                        "unit": "LF",
                        "unit_cost_cents": 450,
                        "total_cents": 33750,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_ev_breaker"),
                        "description": "60A double-pole breaker",
                        "product": "Square D HOM260",
                        "quantity": 1.0,
                        "unit": "EA",
                        "unit_cost_cents": 1500,
                        "total_cents": 1500,
                    },
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_ev_outlet"),
                        "description": "NEMA 14-50 outlet for EV charger",
                        "product": "",
                        "quantity": 1.0,
                        "unit": "EA",
                        "unit_cost_cents": 3500,
                        "total_cents": 3500,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04_smoke_detectors"),
                "description": "Smoke/CO detectors — code compliant layout",
                "quantity": 14.0,
                "unit": "EA",
                "margin_pct": 15.0,
                "labour_total_cents": 105000,
                "items_total_cents": 84000,
                "sell_price_cents": 217350,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp04_smoke_install"),
                        "task": "Install hardwired smoke/CO detectors — 14 locations",
                        "rate_cents": 15000,
                        "hours": 7.0,
                        "cost_cents": 105000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp04_smoke_combo"),
                        "description": "Kidde smoke/CO combo detector (hardwired)",
                        "product": "Kidde 21028075",
                        "quantity": 14.0,
                        "unit": "EA",
                        "unit_cost_cents": 6000,
                        "total_cents": 84000,
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Resource Rates (company library)
    # -----------------------------------------------------------------

    def _build_resource_rates(self) -> list[dict]:
        uid = GP04_USER["uid"]
        base = {
            "active": True,
            "sample_size": None,
            "std_deviation_cents": None,
            "last_derived_at": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            # Note: labour rates for all trades are defined in
            # _build_resource_rates_expanded below. Duplicates removed 2026-04-16.
            {**base, "id": stable_id("rr", "gp04_emt_34"), "resource_type": "material",
             "description": "3/4\" EMT Conduit (10ft stick)", "rate_cents": 250,
             "unit": "per_lf", "source": "supplier_quote", "supplier_name": "Rexel"},
            {**base, "id": stable_id("rr", "gp04_nm14_2"), "resource_type": "material",
             "description": "14/2 NM-B Cable (Romex)", "rate_cents": 55,
             "unit": "per_lf", "source": "supplier_quote", "supplier_name": "Graybar"},
            {**base, "id": stable_id("rr", "gp04_nm12_2"), "resource_type": "material",
             "description": "12/2 NM-B Cable (Romex)", "rate_cents": 75,
             "unit": "per_lf", "source": "supplier_quote", "supplier_name": "Graybar"},
            {**base, "id": stable_id("rr", "gp04_recessed_6"), "resource_type": "material",
             "description": "6\" LED Recessed Downlight (Halo RL6)", "rate_cents": 15000,
             "unit": "per_ea", "source": "supplier_quote", "supplier_name": "CED"},
            {**base, "id": stable_id("rr", "gp04_receptacle_20a"), "resource_type": "material",
             "description": "Duplex Receptacle — 20A spec grade", "rate_cents": 850,
             "unit": "per_ea", "source": "supplier_quote", "supplier_name": "Rexel"},
            {**base, "id": stable_id("rr", "gp04_dimmer_caseta"), "resource_type": "material",
             "description": "Lutron Caseta Dimmer Switch", "rate_cents": 5500,
             "unit": "per_ea", "source": "supplier_quote", "supplier_name": "CED"},
            {**base, "id": stable_id("rr", "gp04_scissor_lift"), "resource_type": "equipment",
             "description": "Scissor Lift rental (19ft)", "rate_cents": 25000,
             "unit": "per_day", "source": "supplier_quote", "supplier_name": "United Rentals"},
        ]

    # -----------------------------------------------------------------
    # Productivity Rates
    # -----------------------------------------------------------------

    def _build_productivity_rates(self) -> list[dict]:
        uid = GP04_USER["uid"]
        base = {
            "active": True,
            "source": "manual_entry",
            "sample_size": None,
            "std_deviation": None,
            "includes_non_productive": False,
            "last_derived_at": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base, "id": stable_id("pr", "gp04_emt_resi"),
             "description": "EMT conduit — residential wood frame",
             "rate": 32.0, "rate_unit": "LF", "time_unit": "per_hour",
             "crew_composition": "1 journeyman + 1 apprentice",
             "conditions": "Standard access, open ceiling or stud bays"},
            {**base, "id": stable_id("pr", "gp04_receptacle_resi"),
             "description": "Receptacle installation — residential",
             "rate": 5.0, "rate_unit": "EA", "time_unit": "per_hour",
             "crew_composition": "1 journeyman",
             "conditions": "Standard outlet with NM cable, open walls"},
            {**base, "id": stable_id("pr", "gp04_panel_resi"),
             "description": "Panel installation — residential",
             "rate": 0.08, "rate_unit": "EA", "time_unit": "per_hour",
             "crew_composition": "1 journeyman + 1 apprentice",
             "conditions": "200A residential, typical 30 circuits"},
        ]

    # -----------------------------------------------------------------
    # Assumption Templates (company-level)
    # -----------------------------------------------------------------

    def _build_assumption_templates(self) -> list[dict]:
        uid = GP04_USER["uid"]
        base = {
            "is_template": True,
            "status": "active",
            "triggered_at": None,
            "triggered_by_event": None,
            "sort_order": 0,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base, "id": stable_id("asmp", "gp04_tmpl_schedule"),
             "category": "schedule", "trade_type": "electrical",
             "statement": "Programme duration as per the construction schedule provided",
             "variation_trigger": True,
             "trigger_description": "Schedule extended beyond original programme duration"},
            {**base, "id": stable_id("asmp", "gp04_tmpl_drawings"),
             "category": "design_completeness", "trade_type": "electrical",
             "statement": "Pricing based on drawings and specifications provided at time of tender",
             "variation_trigger": True,
             "trigger_description": "Drawing revisions issued after tender date"},
            {**base, "id": stable_id("asmp", "gp04_tmpl_access"),
             "category": "access", "trade_type": "electrical",
             "statement": "Unimpeded access to all work areas during normal working hours",
             "variation_trigger": True,
             "trigger_description": "Access restricted or delayed by other trades"},
            {**base, "id": stable_id("asmp", "gp04_tmpl_power"),
             "category": "site_conditions", "trade_type": "electrical",
             "statement": "Temporary power available at commencement of electrical works",
             "variation_trigger": False, "trigger_description": ""},
            {**base, "id": stable_id("asmp", "gp04_tmpl_quantities"),
             "category": "quantities", "trade_type": "electrical",
             "statement": "Quantities measured from drawings provided — field verification not included",
             "variation_trigger": True,
             "trigger_description": "Actual quantities exceed plan quantities by more than 10%"},
            {**base, "id": stable_id("asmp", "gp04_tmpl_pricing"),
             "category": "pricing", "trade_type": "electrical",
             "statement": "Material pricing valid for 30 days from date of quote",
             "variation_trigger": False, "trigger_description": ""},
        ]

    # -----------------------------------------------------------------
    # Exclusion Templates (company-level)
    # -----------------------------------------------------------------

    def _build_exclusion_templates(self) -> list[dict]:
        uid = GP04_USER["uid"]
        base = {
            "is_template": True,
            "sort_order": 0,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base, "id": stable_id("excl", "gp04_tmpl_fire_alarm"),
             "category": "scope", "trade_type": "electrical",
             "statement": "Fire alarm system design, supply, and installation",
             "partial_inclusion": "", "source": "Standard electrical exclusion"},
            {**base, "id": stable_id("excl", "gp04_tmpl_low_voltage"),
             "category": "trade_boundary", "trade_type": "electrical",
             "statement": "Low voltage systems — data, voice, CCTV, access control",
             "partial_inclusion": "Raceways and pull strings only",
             "source": "Standard electrical exclusion"},
            {**base, "id": stable_id("excl", "gp04_tmpl_permits"),
             "category": "scope", "trade_type": "electrical",
             "statement": "Permit fees and inspection fees",
             "partial_inclusion": "", "source": "Standard electrical exclusion"},
            {**base, "id": stable_id("excl", "gp04_tmpl_trenching"),
             "category": "trade_boundary", "trade_type": "electrical",
             "statement": "Trenching, backfill, and concrete work for underground conduit",
             "partial_inclusion": "Conduit and wire within trench only",
             "source": "Added after Hidden Valley project dispute 2024-09"},
            {**base, "id": stable_id("excl", "gp04_tmpl_patching"),
             "category": "scope", "trade_type": "electrical",
             "statement": "Drywall patching and painting after electrical rough-in",
             "partial_inclusion": "",
             "source": "Standard — GC responsibility"},
        ]

    # -----------------------------------------------------------------
    # Additional Resource Rates (multi-trade library)
    # -----------------------------------------------------------------

    def _build_additional_resource_rates(self) -> list[dict]:
        """Multi-trade resource rates for the company library."""
        uid = GP04_USER["uid"]
        base = {
            "active": True,
            "sample_size": None,
            "std_deviation_cents": None,
            "last_derived_at": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base, "id": stable_id("rr", "gp04_gen_labourer"),
             "resource_type": "labour",
             "description": "General Labourer — loaded rate",
             "rate_cents": 4500, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 2800, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
            {**base, "id": stable_id("rr", "gp04_elec_journeyman"),
             "resource_type": "labour",
             "description": "Electrician Journeyman — loaded rate",
             "rate_cents": 8500, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 5500, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
            {**base, "id": stable_id("rr", "gp04_plumber_journeyman"),
             "resource_type": "labour",
             "description": "Plumber Journeyman — loaded rate",
             "rate_cents": 7800, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 5000, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
            {**base, "id": stable_id("rr", "gp04_hvac_tech"),
             "resource_type": "labour",
             "description": "HVAC Technician — loaded rate",
             "rate_cents": 8200, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 5300, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
            {**base, "id": stable_id("rr", "gp04_carpenter"),
             "resource_type": "labour",
             "description": "Carpenter — loaded rate",
             "rate_cents": 6500, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 4200, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
            {**base, "id": stable_id("rr", "gp04_superintendent"),
             "resource_type": "labour",
             "description": "Superintendent — loaded rate",
             "rate_cents": 9500, "unit": "per_hour",
             "source": "manual_entry",
             "base_rate_cents": 6200, "burden_percent": 42.0,
             "non_productive_percent": 10.0},
        ]

    # -----------------------------------------------------------------
    # Additional Productivity Rates (multi-trade)
    # -----------------------------------------------------------------

    def _build_additional_productivity_rates(self) -> list[dict]:
        """Multi-trade productivity rates."""
        uid = GP04_USER["uid"]
        base = {
            "active": True,
            "source": "manual_entry",
            "sample_size": None,
            "std_deviation": None,
            "includes_non_productive": False,
            "last_derived_at": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base, "id": stable_id("pr", "gp04_emt_roughin"),
             "description": "EMT conduit rough-in — residential wood frame",
             "rate": 80.0, "rate_unit": "LF", "time_unit": "per_day",
             "crew_composition": "2-person crew (1 journeyman + 1 apprentice)",
             "conditions": "Standard access, open ceiling or stud bays"},
            {**base, "id": stable_id("pr", "gp04_resi_plumbing"),
             "description": "Residential rough plumbing — fixtures",
             "rate": 2.5, "rate_unit": "fixtures", "time_unit": "per_day",
             "crew_composition": "1 journeyman plumber",
             "conditions": "New construction, standard access"},
            {**base, "id": stable_id("pr", "gp04_concrete_form"),
             "description": "Concrete form and pour",
             "rate": 15.0, "rate_unit": "CY", "time_unit": "per_day",
             "crew_composition": "4-person crew",
             "conditions": "Standard footings and slabs, pump truck available"},
            {**base, "id": stable_id("pr", "gp04_framing_resi"),
             "description": "Wall framing — residential",
             "rate": 250.0, "rate_unit": "SF", "time_unit": "per_day",
             "crew_composition": "3-person crew (1 lead + 2 carpenters)",
             "conditions": "Standard 2x6 exterior, 2x4 interior, single story"},
        ]

    # -----------------------------------------------------------------
    # Completed Project (for source cascade testing)
    # -----------------------------------------------------------------

    def _build_completed_project(self) -> dict:
        """A past completed project for David Nguyen's company."""
        uid = GP04_USER["uid"]
        return {
            "id": "proj_gp04_completed",
            "name": "Palo Alto Office Renovation — Suite 200",
            "address": "200 University Ave, Suite 200, Palo Alto, CA 94301",
            "client_name": "TechVenture Partners LLC",
            "project_type": "commercial",
            "trade_types": ["general", "electrical", "plumbing", "hvac"],
            "start_date": days_ago(365),
            "end_date": days_ago(90),
            "estimated_workers": 8,
            "description": "3,200 sq ft office renovation — "
                "complete electrical upgrade, new HVAC system, "
                "open-plan reconfiguration with 4 glass-front offices.",
            "special_hazards": "Occupied building — adjacent suites active. "
                "Asbestos abatement completed prior to start.",
            "nearest_hospital": "Stanford Health Care, "
                "300 Pasteur Drive, Palo Alto, CA 94304",
            "emergency_contact_name": "David Nguyen",
            "emergency_contact_phone": "650-555-0489",
            "state": "completed",
            "status": "normal",
            "compliance_score": 94,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": datetime_days_ago(365),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        }

    def _build_completed_work_items(self, project_id: str) -> list[dict]:
        """Work items for the completed project with actual costs filled in."""
        uid = GP04_USER["uid"]
        base = {
            "state": "complete",
            "deleted": False,
            "is_alternate": False,
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "agent_id": None, "model_id": None, "confidence": None,
        }
        lab_base = {
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "agent_id": None, "model_id": None, "confidence": None,
        }
        return [
            {
                **base,
                "id": stable_id("wi", "gp04c_demo_strip"),
                "description": "Demo and strip-out — Suite 200",
                "quantity": 1.0, "unit": "LS", "margin_pct": 12.0,
                "labour_total_cents": 320000,
                "items_total_cents": 45000,
                "sell_price_cents": 408800,
                "actual_labour_cents": 335000,
                "actual_items_cents": 42000,
                "labour": [
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_demo_crew"),
                     "task": "Demo crew — strip walls, ceiling, flooring",
                     "rate_cents": 4500, "hours": 40.0,
                     "cost_cents": 180000},
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_demo_haul"),
                     "task": "Debris haul and disposal",
                     "rate_cents": 4500, "hours": 16.0,
                     "cost_cents": 72000},
                ],
                "items": [
                    {**lab_base,
                     "id": stable_id("item", "gp04c_dumpster"),
                     "description": "30-yard roll-off dumpster (2 pulls)",
                     "product": "",
                     "quantity": 2.0, "unit": "EA",
                     "unit_cost_cents": 22500,
                     "total_cents": 45000},
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04c_elec_upgrade"),
                "description": "Electrical upgrade — panel, circuits, lighting",
                "quantity": 1.0, "unit": "LS", "margin_pct": 15.0,
                "labour_total_cents": 580000,
                "items_total_cents": 310000,
                "sell_price_cents": 1023500,
                "actual_labour_cents": 610000,
                "actual_items_cents": 295000,
                "labour": [
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_elec_rough"),
                     "task": "Electrical rough-in — all circuits",
                     "rate_cents": 8500, "hours": 48.0,
                     "cost_cents": 408000},
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_elec_trim"),
                     "task": "Trim out — fixtures, devices, panel terminate",
                     "rate_cents": 8500, "hours": 20.0,
                     "cost_cents": 170000},
                ],
                "items": [
                    {**lab_base,
                     "id": stable_id("item", "gp04c_panel_200a"),
                     "description": "200A Main Panel (Square D)",
                     "product": "Square D HOM3060M200PC",
                     "quantity": 1.0, "unit": "EA",
                     "unit_cost_cents": 85000,
                     "total_cents": 85000},
                    {**lab_base,
                     "id": stable_id("item", "gp04c_led_troffer"),
                     "description": "2x4 LED Troffer — office lighting",
                     "product": "Lithonia 2GTL4",
                     "quantity": 24.0, "unit": "EA",
                     "unit_cost_cents": 8500,
                     "total_cents": 204000},
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04c_hvac_system"),
                "description": "HVAC — new split system, ductwork",
                "quantity": 1.0, "unit": "LS", "margin_pct": 15.0,
                "labour_total_cents": 420000,
                "items_total_cents": 580000,
                "sell_price_cents": 1150000,
                "actual_labour_cents": 445000,
                "actual_items_cents": 565000,
                "labour": [
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_hvac_install"),
                     "task": "HVAC system install — 5-ton split",
                     "rate_cents": 8200, "hours": 32.0,
                     "cost_cents": 262400},
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_duct_run"),
                     "task": "Ductwork fabrication and run",
                     "rate_cents": 8200, "hours": 24.0,
                     "cost_cents": 196800},
                ],
                "items": [
                    {**lab_base,
                     "id": stable_id("item", "gp04c_split_unit"),
                     "description": "Daikin 5-ton split system",
                     "product": "Daikin DZ18TC0601B",
                     "quantity": 1.0, "unit": "EA",
                     "unit_cost_cents": 450000,
                     "total_cents": 450000},
                    {**lab_base,
                     "id": stable_id("item", "gp04c_ductwork"),
                     "description": "Galvanised ductwork — custom fabricated",
                     "product": "",
                     "quantity": 1.0, "unit": "LS",
                     "unit_cost_cents": 130000,
                     "total_cents": 130000},
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp04c_glass_offices"),
                "description": "Glass-front offices — 4 units, framing + glazing",
                "quantity": 4.0, "unit": "EA", "margin_pct": 18.0,
                "labour_total_cents": 360000,
                "items_total_cents": 480000,
                "sell_price_cents": 991200,
                "actual_labour_cents": 380000,
                "actual_items_cents": 470000,
                "labour": [
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_office_frame"),
                     "task": "Metal stud framing — office partitions",
                     "rate_cents": 6500, "hours": 32.0,
                     "cost_cents": 208000},
                    {**lab_base,
                     "id": stable_id("lab", "gp04c_glass_install"),
                     "task": "Glass partition install and hardware",
                     "rate_cents": 7600, "hours": 20.0,
                     "cost_cents": 152000},
                ],
                "items": [
                    {**lab_base,
                     "id": stable_id("item", "gp04c_glass_panels"),
                     "description": "Tempered glass panels — 10mm clear",
                     "product": "",
                     "quantity": 16.0, "unit": "EA",
                     "unit_cost_cents": 25000,
                     "total_cents": 400000},
                    {**lab_base,
                     "id": stable_id("item", "gp04c_hardware"),
                     "description": "Glass door and partition hardware",
                     "product": "",
                     "quantity": 4.0, "unit": "SET",
                     "unit_cost_cents": 20000,
                     "total_cents": 80000},
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Completed Project Contract
    # -----------------------------------------------------------------

    def _build_completed_contract(
        self, contract_id: str, project_id: str,
    ) -> dict:
        """Contract for the completed project."""
        uid = GP04_USER["uid"]
        return {
            "id": contract_id,
            "project_id": project_id,
            "company_id": self.COMPANY_ID,
            "retention_pct": 5.0,
            "payment_terms_days": 30,
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }

    def _build_completed_milestones(self, contract_id: str) -> list[dict]:
        """Payment milestones for the completed project (50/25/25 split)."""
        uid = GP04_USER["uid"]
        base = {
            "contract_id": contract_id,
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base,
             "id": stable_id("pm", "gp04c_deposit"),
             "description": "Deposit — upon contract execution",
             "percentage": 50.0,
             "amount_cents": None,
             "trigger_condition": "Signed contract and notice to proceed",
             "status": "paid",
             "sort_order": 1},
            {**base,
             "id": stable_id("pm", "gp04c_rough_complete"),
             "description": "Rough-in complete — all trades",
             "percentage": 25.0,
             "amount_cents": None,
             "trigger_condition": "Rough inspection passed for electrical, plumbing, HVAC",
             "status": "paid",
             "sort_order": 2},
            {**base,
             "id": stable_id("pm", "gp04c_final"),
             "description": "Final payment — practical completion",
             "percentage": 25.0,
             "amount_cents": None,
             "trigger_condition": "Certificate of occupancy issued and punch list complete",
             "status": "paid",
             "sort_order": 3},
        ]

    def _build_completed_conditions(self, contract_id: str) -> list[dict]:
        """Contract conditions for the completed project."""
        uid = GP04_USER["uid"]
        base = {
            "contract_id": contract_id,
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(360),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
        return [
            {**base,
             "id": stable_id("cond", "gp04c_access"),
             "category": "site_access",
             "description": "Contractor to have access Mon-Fri 7am-6pm. "
                 "Weekend access by prior arrangement with building management.",
             "responsible_party": "Client / Building Manager"},
            {**base,
             "id": stable_id("cond", "gp04c_hours"),
             "category": "working_hours",
             "description": "Noisy works (demo, drilling, cutting) restricted to "
                 "9am-4pm per building management rules.",
             "responsible_party": "Contractor"},
            {**base,
             "id": stable_id("cond", "gp04c_permits"),
             "category": "permits",
             "description": "Client responsible for obtaining building permit. "
                 "Contractor to obtain electrical and mechanical permits.",
             "responsible_party": "Shared"},
            {**base,
             "id": stable_id("cond", "gp04c_insurance"),
             "category": "insurance",
             "description": "Contractor to maintain $2M general liability and "
                 "$1M workers compensation insurance for duration of works.",
             "responsible_party": "Contractor"},
        ]

    def _build_completed_warranty(self, contract_id: str) -> dict:
        """Warranty for the completed project."""
        uid = GP04_USER["uid"]
        return {
            "id": stable_id("warr", "gp04c_warranty"),
            "contract_id": contract_id,
            "period_months": 12,
            "scope": "All workmanship and materials supplied by contractor. "
                "Excludes owner-supplied fixtures, normal wear and tear, "
                "and damage caused by occupant modifications.",
            "start_trigger": "practical_completion",
            "terms": "Contractor to remedy defects within 14 days of written "
                "notice. Emergency defects (water, electrical safety) to be "
                "addressed within 24 hours.",
            "created_at": datetime_days_ago(360),
            "updated_at": datetime_days_ago(90),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }
