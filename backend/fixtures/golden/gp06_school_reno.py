"""GP06 — School Renovation, Mid-Project (CA — British Columbia).

The "busy mid-project" golden project: 15 workers, 2 subs (HVAC,
electrical), WorkSafeBC regulations. Lots of in-progress state:
active daily logs, pending timesheet approvals, open RFIs (one overdue),
change order for discovered asbestos, quality deficiencies being tracked.

Exercises:
- Canadian jurisdiction (WorkSafeBC, BC regulations)
- 15 workers across GC + 2 subs (HVAC, electrical)
- Mid-project busy state (many items in-progress)
- 3 open RFIs (one overdue by 5 days)
- Change order in progress (asbestos discovery)
- Quality deficiencies (2 open, 1 corrected)
- 6 inspections with history
- 1 first-aid incident (closed)
- 5 daily logs (mix of approved, submitted, draft)
- 2 toolbox talks (1 completed, 1 scheduled for tomorrow)
- Equipment: scaffold system
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP06_COMPANY, GP06_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP06Seeder(GoldenProjectSeeder):
    """Seed GP06: School Renovation — Victoria, BC."""

    GP_SLUG = "gp06"
    COMPANY_ID = "comp_gp06"
    PROJECT_ID = "proj_gp06"

    def seed(self) -> dict[str, int]:
        """Seed all GP06 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP06_COMPANY)
        self.seed_user(GP06_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Westshore Elementary School Renovation — Phase 2",
            "address": "2100 Goldstream Avenue, Victoria, BC V9B 2Y3",
            "client_name": "Greater Victoria School District No. 61",
            "project_type": "renovation",
            "trade_types": ["general", "electrical", "hvac"],
            "start_date": days_ago(45),
            "end_date": days_from_now(75),
            "estimated_workers": 15,
            "description": "Phase 2 renovation of Westshore Elementary School. "
                "Scope includes classroom wing interior renovation (12 rooms), "
                "HVAC system replacement, electrical panel upgrades, "
                "new fire alarm system, accessibility upgrades (ramps, "
                "washrooms), and gymnasium floor refinishing. "
                "Work performed during summer break with partial occupancy "
                "by school admin staff.",
            "special_hazards": "Asbestos-containing materials discovered in "
                "ceiling tiles (rooms 204-208) — abatement required before "
                "demolition. Lead paint on window frames (pre-1990 wing). "
                "Partial school occupancy — admin office staff on site "
                "weekdays. Playground adjacent to work area — fencing "
                "required during school term. Working at height for "
                "HVAC ductwork in gymnasium (9m ceiling).",
            "nearest_hospital": "Victoria General Hospital, "
                "1 Hospital Way, Victoria, BC V8Z 6R5",
            "emergency_contact_name": "Ryan Patel",
            "emergency_contact_phone": "250-555-0178",
            "state": "active",
            "status": "normal",
            "compliance_score": 78,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP06_USER["uid"],
            "actor_type": "human",
            "updated_by": GP06_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (15 across own crew + subs) ---
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
        """Build worker list: 10 own crew + 5 across 2 subs."""
        uid = GP06_USER["uid"]
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
            # --- Own crew (Fraser Valley Contracting) ---
            {
                **base,
                "id": stable_id("wkr", "gp06_ryan"),
                "first_name": "Ryan",
                "last_name": "Patel",
                "email": "ryan@fraservalleycontracting.ca",
                "phone": "250-555-0178",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 12),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_ryan_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2023-44521",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_ryan_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(185),
                        "issuing_body": "St John Ambulance Canada",
                        "certificate_number": "SJA-OFA3-2025-88912",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_ryan_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-FP-2025-22345",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_kevin"),
                "first_name": "Kevin",
                "last_name": "Mcdonald",
                "email": "kevin@fraservalleycontracting.ca",
                "phone": "250-555-0192",
                "role": "foreman",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_kevin_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2024-55632",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_kevin_scaffold"),
                        "certification_type": "scaffold_competent",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-SC-2025-33456",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_lisa"),
                "first_name": "Lisa",
                "last_name": "Cheng",
                "email": "lisa@fraservalleycontracting.ca",
                "phone": "250-555-0205",
                "role": "safety_officer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_lisa_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2022-66743",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_lisa_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(90),
                        "expiry_date": days_from_now(275),
                        "issuing_body": "St John Ambulance Canada",
                        "certificate_number": "SJA-OFA3-2026-11234",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_lisa_asbestos"),
                        "certification_type": "asbestos_awareness",
                        "issued_date": days_ago(150),
                        "expiry_date": days_from_now(215),
                        "issuing_body": "WorkSafeBC",
                        "certificate_number": "WSBC-AA-2025-44567",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_tyler"),
                "first_name": "Tyler",
                "last_name": "Brooks",
                "email": "tyler@fraservalleycontracting.ca",
                "phone": "250-555-0218",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_tyler_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2024-77854",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_amir"),
                "first_name": "Amir",
                "last_name": "Hassan",
                "email": "",
                "phone": "250-555-0231",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_amir_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2025-88965",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_amir_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(795),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-FP-2025-33456",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_jordan"),
                "first_name": "Jordan",
                "last_name": "Williams",
                "email": "",
                "phone": "250-555-0244",
                "role": "laborer",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_jordan_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2025-99076",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_maria"),
                "first_name": "Maria",
                "last_name": "Santos",
                "email": "",
                "phone": "250-555-0257",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(180),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_maria_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2025-00187",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_connor"),
                "first_name": "Connor",
                "last_name": "Reid",
                "email": "connor@fraservalleycontracting.ca",
                "phone": "250-555-0270",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(90),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_connor_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(120),
                        "expiry_date": days_from_now(975),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2026-11298",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_dave"),
                "first_name": "Dave",
                "last_name": "Olsen",
                "email": "",
                "phone": "250-555-0283",
                "role": "apprentice",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(60),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_dave_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(75),
                        "expiry_date": days_from_now(1020),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2026-22409",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_sarah"),
                "first_name": "Sarah",
                "last_name": "Blackwood",
                "email": "sarah@fraservalleycontracting.ca",
                "phone": "250-555-0296",
                "role": "project_coordinator",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_sarah_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2023-33510",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Island Air Mechanical (HVAC) ---
            {
                **base,
                "id": stable_id("wkr", "gp06_pete_hvac"),
                "first_name": "Pete",
                "last_name": "Larson",
                "email": "pete@islandairmech.ca",
                "phone": "250-555-0321",
                "role": "foreman",
                "trade": "hvac",
                "language_preference": "en",
                "hire_date": days_ago(365 * 9),
                "notes": "Sub: Island Air Mechanical",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_pete_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2024-44621",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_pete_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(250),
                        "expiry_date": days_from_now(845),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-FP-2025-55732",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_james_hvac"),
                "first_name": "James",
                "last_name": "Firth",
                "email": "",
                "phone": "250-555-0334",
                "role": "journeyman",
                "trade": "hvac",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "notes": "Sub: Island Air Mechanical",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_james_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2025-66843",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Capital City Electric ---
            {
                **base,
                "id": stable_id("wkr", "gp06_nadia_elec"),
                "first_name": "Nadia",
                "last_name": "Kowalski",
                "email": "nadia@capitalcityelectric.ca",
                "phone": "250-555-0347",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "notes": "Sub: Capital City Electric",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_nadia_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2024-77954",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp06_nadia_eleclicense"),
                        "certification_type": "electrical_license",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "BC Safety Authority",
                        "certificate_number": "BCSA-FSR-A-2022-88065",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp06_ben_elec"),
                "first_name": "Ben",
                "last_name": "Lawson",
                "email": "",
                "phone": "250-555-0360",
                "role": "journeyman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "notes": "Sub: Capital City Electric",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp06_ben_cst"),
                        "certification_type": "construction_safety_training",
                        "issued_date": days_ago(400),
                        "expiry_date": days_ago(35),  # EXPIRED
                        "issuing_body": "BC Construction Safety Alliance",
                        "certificate_number": "BCCSA-CST-2024-99176",
                        "status": "expired",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 6 inspections with good history."""
        uid = GP06_USER["uid"]
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
                "id": stable_id("insp", "gp06_daily_d14"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(14),
                "inspector_name": "Lisa Cheng",
                "inspector_id": stable_id("wkr", "gp06_lisa"),
                "weather_conditions": "Rainy",
                "temperature": "12C",
                "workers_on_site": 10,
                "overall_status": "pass",
                "overall_notes": "Rain plan in effect — exterior work suspended. "
                    "Interior demo proceeding in classrooms 201-203. "
                    "All workers in proper PPE including dust masks for "
                    "drywall removal.",
                "items": "[]",
                "created_at": datetime_days_ago(14),
                "updated_at": datetime_days_ago(14),
            },
            {
                **base,
                "id": stable_id("insp", "gp06_daily_d10"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(10),
                "inspector_name": "Lisa Cheng",
                "inspector_id": stable_id("wkr", "gp06_lisa"),
                "weather_conditions": "Overcast",
                "temperature": "14C",
                "workers_on_site": 13,
                "overall_status": "pass",
                "overall_notes": "Asbestos abatement crew completed rooms 204-206. "
                    "Air monitoring results within acceptable limits. "
                    "Containment barriers intact. "
                    "HVAC sub started ductwork demo in gymnasium.",
                "items": "[]",
                "created_at": datetime_days_ago(10),
                "updated_at": datetime_days_ago(10),
            },
            {
                **base,
                "id": stable_id("insp", "gp06_daily_d7"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(7),
                "inspector_name": "Lisa Cheng",
                "inspector_id": stable_id("wkr", "gp06_lisa"),
                "weather_conditions": "Partly cloudy",
                "temperature": "16C",
                "workers_on_site": 14,
                "overall_status": "fail",
                "overall_notes": "Capital City Electric worker (Ben Lawson) found "
                    "with expired Construction Safety Training certificate. "
                    "Quality issue: drywall in room 201 not meeting level 4 "
                    "finish specification.",
                "corrective_actions_needed": "Ben Lawson to renew CST before "
                    "returning to active work. Drywall in room 201 to be "
                    "re-finished to level 4 specification.",
                "items": "[]",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(7),
            },
            {
                **base,
                "id": stable_id("insp", "gp06_daily_d3"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "Lisa Cheng",
                "inspector_id": stable_id("wkr", "gp06_lisa"),
                "weather_conditions": "Sunny",
                "temperature": "19C",
                "workers_on_site": 15,
                "overall_status": "pass",
                "overall_notes": "Full crew on site. Asbestos abatement complete "
                    "for all affected rooms. Clearance air monitoring passed. "
                    "Scaffold in gymnasium inspected and cleared for HVAC "
                    "ductwork installation at height.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("insp", "gp06_scaffold1"),
                "inspection_type": "scaffold",
                "inspection_date": days_ago(4),
                "inspector_name": "Kevin Mcdonald",
                "inspector_id": stable_id("wkr", "gp06_kevin"),
                "weather_conditions": "Clear",
                "temperature": "18C",
                "workers_on_site": 14,
                "overall_status": "pass",
                "overall_notes": "Gymnasium scaffold system inspected. "
                    "All guardrails, mid-rails, and toe boards in place. "
                    "Base plates on firm footing. "
                    "Cross-bracing secure. Access ladder secured at top. "
                    "Load rating posted.",
                "items": "[]",
                "created_at": datetime_days_ago(4),
                "updated_at": datetime_days_ago(4),
            },
            {
                **base,
                "id": stable_id("insp", "gp06_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Lisa Cheng",
                "inspector_id": stable_id("wkr", "gp06_lisa"),
                "weather_conditions": "Clear",
                "temperature": "20C",
                "workers_on_site": 14,
                "overall_status": "partial",
                "overall_notes": "Ben Lawson CST still expired — working under "
                    "direct supervision of Nadia Kowalski per WorkSafeBC "
                    "allowance. RFI-003 response overdue from architect "
                    "by 5 days — blocking electrical panel location.",
                "corrective_actions_needed": "Follow up with architect on "
                    "RFI-003 (electrical panel relocation). "
                    "Ben Lawson CST renewal scheduled for next week.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        """Build 1 first-aid incident (closed)."""
        uid = GP06_USER["uid"]
        return [{
            "id": stable_id("inc", "gp06_firstaid1"),
            "incident_date": days_ago(12),
            "incident_time": "10:45",
            "location": "Classroom 203, ground floor",
            "severity": "first_aid",
            "status": "closed",
            "description": "Worker (Tyler Brooks) sustained minor laceration "
                "to left forearm while removing old window frame. "
                "Exposed nail on frame caught arm during lifting. "
                "Wound approximately 3cm, superficial. First aid "
                "administered on site — wound cleaned, butterfly "
                "closure applied, tetanus status confirmed current.",
            "persons_involved": "Tyler Brooks (injured worker)",
            "involved_worker_ids": [
                stable_id("wkr", "gp06_tyler"),
            ],
            "witnesses": "Jordan Williams, Amir Hassan",
            "immediate_actions_taken": "First aid administered by Lisa Cheng "
                "(OFA Level 3). Wound cleaned with saline, butterfly "
                "closures applied, sterile dressing. Worker cleared to "
                "return to modified duties (no demolition) for remainder "
                "of shift. Incident area inspected — protruding nails "
                "identified on three additional window frames.",
            "root_cause": "Nails left protruding from window frames during "
                "previous phase of demolition. Worker not wearing "
                "cut-resistant sleeves (recommended but not mandated "
                "for this task).",
            "corrective_actions": "All remaining window frames inspected and "
                "protruding nails removed or bent over before handling. "
                "Cut-resistant sleeves added to PPE requirements for "
                "window frame removal. Toolbox talk on sharp hazard "
                "awareness delivered next morning.",
            "osha_recordable": False,
            "osha_reportable": False,
            "photo_urls": [],
            "created_at": datetime_days_ago(12),
            "updated_at": datetime_days_ago(10),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build 1 equipment item: scaffold system."""
        uid = GP06_USER["uid"]
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
        return [{
            **base,
            "id": stable_id("eq", "gp06_scaffold1"),
            "name": "Layher Allround Scaffold System — Gymnasium",
            "equipment_type": "scaffold_system",
            "make": "Layher",
            "model": "Allround",
            "serial_number": "LAY-AR-2023-11234",
            "current_project_id": self.PROJECT_ID,
            "inspection_frequency": "daily",
            "last_inspection_date": days_ago(1),
            "next_inspection_due": days_ago(0),
            "notes": "4-tier scaffold in gymnasium for HVAC ductwork "
                "installation at 9m ceiling height. "
                "Daily inspection required per WorkSafeBC. "
                "Rented from Winslow Scaffold Solutions.",
        }]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 2 toolbox talks: 1 completed, 1 scheduled for tomorrow."""
        uid = GP06_USER["uid"]
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
                "id": stable_id("talk", "gp06_asbestos"),
                "topic": "Asbestos Awareness — Working Near ACM in Schools",
                "scheduled_date": days_ago(15),
                "target_audience": "all_workers",
                "duration_minutes": 20,
                "language": "en",
                "status": "completed",
                "presented_at": datetime_days_ago(15, hour=7),
                "presented_by": "Lisa Cheng",
                "overall_notes": "Reviewed WorkSafeBC asbestos regulations and "
                    "school-specific protocols. Covered identification of "
                    "asbestos-containing ceiling tiles in rooms 204-208. "
                    "Explained abatement timeline and containment barriers. "
                    "All workers signed acknowledgement of no-disturbance "
                    "policy for identified ACM areas.",
                "created_at": datetime_days_ago(16),
                "updated_at": datetime_days_ago(15),
            },
            {
                **base,
                "id": stable_id("talk", "gp06_scaffold_safety"),
                "topic": "Scaffold Safety and Fall Prevention — Gymnasium Work",
                "scheduled_date": days_from_now(1),
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "language": "en",
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
        """Build 2 hazard reports: 1 corrected, 1 open."""
        uid = GP06_USER["uid"]
        return [
            {
                "id": stable_id("haz", "gp06_leadpaint1"),
                "description": "Lead paint identified on window frames in "
                    "rooms 201-208. Paint chips observed on floor below "
                    "window sills where demolition has started. "
                    "Potential lead exposure risk for workers and "
                    "adjacent admin staff.",
                "location": "Classroom wing, rooms 201-208 window frames",
                "status": "corrected",
                "hazard_count": 1,
                "highest_severity": "high",
                "corrective_action_taken": "Lead paint stabilisation applied to "
                    "all window frames before removal. HEPA vacuum used "
                    "for all paint chip cleanup. Workers issued P100 "
                    "respirators for window frame removal. Air monitoring "
                    "installed in corridor outside work zone.",
                "corrected_at": datetime_days_ago(13),
                "corrected_by": "Lisa Cheng",
                "created_at": datetime_days_ago(18),
                "updated_at": datetime_days_ago(13),
                "created_by": uid,
                "actor_type": "human",
                "updated_by": uid,
                "updated_actor_type": "human",
            },
            {
                "id": stable_id("haz", "gp06_egress1"),
                "description": "Emergency exit from gymnasium partially blocked "
                    "by scaffold material staging. Exit door opens but "
                    "clearance reduced to approximately 60cm — below "
                    "minimum 80cm required. School admin staff use this "
                    "corridor during weekday hours.",
                "location": "Gymnasium east exit, corridor to admin wing",
                "status": "open",
                "hazard_count": 1,
                "highest_severity": "high",
                "corrective_action_taken": None,
                "corrected_at": None,
                "corrected_by": None,
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
                "created_by": uid,
                "actor_type": "human",
                "updated_by": uid,
                "updated_actor_type": "human",
            },
        ]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build 5 daily logs with varied statuses."""
        uid = GP06_USER["uid"]
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
                "id": stable_id("dlog", "gp06_d14"),
                "log_date": days_ago(14),
                "superintendent_name": "Ryan Patel",
                "status": "approved",
                "workers_on_site": 10,
                "work_performed": "Interior demo continued in classrooms 201-203. "
                    "Rain plan in effect — no exterior work. "
                    "Asbestos abatement crew mobilising for rooms 204-206. "
                    "Electrical sub running temporary power for demo tools.",
                "notes": "Rain expected through Wednesday. Adjusted schedule to "
                    "prioritise interior work. RFI-001 submitted to architect "
                    "regarding classroom 205 structural column conflict with "
                    "new partition layout.",
                "created_at": datetime_days_ago(14),
                "updated_at": datetime_days_ago(13),
                "submitted_at": datetime_days_ago(14, hour=17),
                "approved_at": datetime_days_ago(13, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp06_d10"),
                "log_date": days_ago(10),
                "superintendent_name": "Ryan Patel",
                "status": "approved",
                "workers_on_site": 13,
                "work_performed": "Asbestos abatement complete for rooms 204-206. "
                    "Clearance air monitoring passed — rooms released for "
                    "general demolition. HVAC sub started ductwork removal "
                    "in gymnasium. Electrical panel survey completed — "
                    "RFI-002 submitted for panel relocation due to new "
                    "accessibility ramp conflict.",
                "notes": "Change order pending for asbestos abatement in rooms "
                    "207-208 (discovered additional ACM in ceiling cavity). "
                    "RFI-001 response received — column to remain, partition "
                    "adjusted. RFI-002 submitted.",
                "created_at": datetime_days_ago(10),
                "updated_at": datetime_days_ago(9),
                "submitted_at": datetime_days_ago(10, hour=17),
                "approved_at": datetime_days_ago(9, hour=9),
            },
            {
                **base,
                "id": stable_id("dlog", "gp06_d7"),
                "log_date": days_ago(7),
                "superintendent_name": "Ryan Patel",
                "status": "approved",
                "workers_on_site": 14,
                "work_performed": "Rooms 207-208 asbestos abatement in progress "
                    "(change order CO-001 approved). Drywall installation "
                    "started in rooms 201-203. Quality issue identified — "
                    "room 201 drywall finish not meeting spec. "
                    "HVAC ductwork demo 80% complete in gymnasium. "
                    "Scaffold erected in gymnasium for new ductwork install.",
                "notes": "Ben Lawson (Capital City Electric) expired CST "
                    "identified — working under direct supervision until "
                    "renewal. RFI-003 submitted for electrical panel "
                    "relocation — architect response pending. "
                    "Quality deficiency logged for room 201 drywall.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
                "submitted_at": datetime_days_ago(7, hour=17),
                "approved_at": datetime_days_ago(6, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp06_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Ryan Patel",
                "status": "submitted",
                "workers_on_site": 15,
                "work_performed": "All asbestos abatement complete. Final clearance "
                    "monitoring passed for rooms 207-208. New HVAC ductwork "
                    "installation started in gymnasium — scaffold in use. "
                    "Electrical rough-in 40% complete in classroom wing. "
                    "Accessibility ramp framing started at main entrance. "
                    "Fire alarm system conduit running in corridor.",
                "notes": "RFI-003 now overdue by 2 days — blocking electrical "
                    "panel final location. Quality deficiency in room 201 "
                    "drywall being re-worked. Second quality issue found — "
                    "fire-stopping missing at corridor penetrations.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp06_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Ryan Patel",
                "status": "submitted",
                "workers_on_site": 14,
                "work_performed": "HVAC ductwork install 30% complete in gymnasium. "
                    "Classroom wing electrical rough-in 60% complete. "
                    "Room 201 drywall re-finish in progress. "
                    "Accessibility ramp concrete pour scheduled for tomorrow. "
                    "Fire-stopping at corridor penetrations 50% corrected.",
                "notes": "RFI-003 now 5 days overdue. Escalated to project "
                    "manager. Temporary panel location being used — will "
                    "require rework if architect response differs from "
                    "assumption. Gymnasium east exit egress concern raised "
                    "as hazard report — scaffold materials to be relocated.",
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
        """Build work items for the active school renovation.

        Active project — items reflect the in-flight scope.
        All values in cents (CAD).
        """
        uid = GP06_USER["uid"]
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
                "id": stable_id("wi", "gp06_item_1"),
                "description": "Classroom envelope \u2014 window replacement 24 units",
                "quantity": 24,
                "unit": "EA",
                "margin_pct": 20,
                "labour_total_cents": 468000,
                "items_total_cents": 3480000,
                "sell_price_cents": 4737600,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp06_lab_1"),
                        "task": "Remove and install windows",
                        "rate_cents": 6500,
                        "hours": 72,
                        "cost_cents": 468000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp06_item_1_mat_1"),
                        "description": "Double-glazed units with frames",
                        "quantity": 24,
                        "unit": "EA",
                        "unit_cost_cents": 145000,
                        "total_cents": 3480000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp06_item_2"),
                "description": "HVAC rooftop unit replacement \u2014 4 units 10 ton each",
                "quantity": 4,
                "unit": "EA",
                "margin_pct": 25,
                "labour_total_cents": 456000,
                "items_total_cents": 5800000,
                "sell_price_cents": 7820000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp06_lab_2"),
                        "task": "Remove, install, commission RTUs",
                        "rate_cents": 9500,
                        "hours": 48,
                        "cost_cents": 456000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp06_item_2_mat_1"),
                        "description": "10-ton packaged RTU with controls",
                        "quantity": 4,
                        "unit": "EA",
                        "unit_cost_cents": 1450000,
                        "total_cents": 5800000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp06_item_3"),
                "description": "Flooring replacement \u2014 VCT in corridors and common areas",
                "quantity": 2800,
                "unit": "SF",
                "margin_pct": 22,
                "labour_total_cents": 352000,
                "items_total_cents": 980000,
                "sell_price_cents": 1625040,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp06_lab_3"),
                        "task": "Strip, prep, install VCT",
                        "rate_cents": 5500,
                        "hours": 64,
                        "cost_cents": 352000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp06_item_3_mat_1"),
                        "description": "VCT tile and adhesive",
                        "quantity": 2800,
                        "unit": "SF",
                        "unit_cost_cents": 350,
                        "total_cents": 980000,
                    },
                ],
            },
        ]
