"""GP05 — Warehouse Fitout (AU — New South Wales).

Industrial warehouse fitout in Homebush, NSW. Medium-high complexity:
18 workers (own crew of 10 + 3 sub companies), SafeWork NSW regulations,
White Card required for all, confined space protocols, heavy equipment.

Exercises:
- Australian jurisdiction (SafeWork NSW, White Card)
- 18 workers across GC + 3 subs (electrical, plumbing, steelwork)
- Confined space protocols (mezzanine crawl spaces)
- Equipment with inspection logs (forklift, scissor lift)
- Environmental monitoring (dust/silica exposure)
- 5 inspections (daily + equipment)
- 1 near-miss incident
- 4 daily logs
- 2 toolbox talks
- Sub performance scoring (varied pass rates)
- Some workers with expired White Cards
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP05_COMPANY, GP05_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP05Seeder(GoldenProjectSeeder):
    """Seed GP05: Warehouse Fitout — Homebush, NSW."""

    GP_SLUG = "gp05"
    COMPANY_ID = "comp_gp05"
    PROJECT_ID = "proj_gp05"

    def seed(self) -> dict[str, int]:
        """Seed all GP05 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP05_COMPANY)
        self.seed_user(GP05_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Homebush Industrial Warehouse Fitout — Unit 7",
            "address": "7/45 Underwood Road, Homebush, NSW 2140",
            "client_name": "Parramatta Logistics Group Pty Ltd",
            "project_type": "commercial_fitout",
            "trade_types": ["general", "electrical", "plumbing", "steelwork"],
            "start_date": days_ago(35),
            "end_date": days_from_now(55),
            "estimated_workers": 18,
            "description": "Full industrial warehouse fitout including mezzanine "
                "level construction, office partition walls, loading dock "
                "upgrades, three-phase electrical distribution, compressed air "
                "system, and amenities block with plumbing rough-in. "
                "2,400 sqm warehouse floor plus 600 sqm mezzanine.",
            "special_hazards": "Confined spaces in mezzanine crawl spaces and "
                "ceiling void above office area. Silica dust from concrete "
                "cutting for new floor drains. Working at height on mezzanine "
                "steel erection. Forklift and scissor lift traffic management "
                "on active warehouse floor. Existing asbestos-containing "
                "materials identified in original roof sheeting — "
                "encapsulated, do not disturb.",
            "nearest_hospital": "Concord Repatriation General Hospital, "
                "Hospital Road, Concord, NSW 2139",
            "emergency_contact_name": "Emma Walsh",
            "emergency_contact_phone": "+61-2-9746-5521",
            "state": "active",
            "status": "normal",
            "compliance_score": 68,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP05_USER["uid"],
            "actor_type": "human",
            "updated_by": GP05_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (18 across own crew + subs) ---
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
        """Build worker list: 10 own crew + 8 across 3 subs."""
        uid = GP05_USER["uid"]
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
            # --- Own crew (Southern Cross Industrial) ---
            {
                **base,
                "id": stable_id("wkr", "gp05_emma"),
                "first_name": "Emma",
                "last_name": "Walsh",
                "email": "emma@southerncrossindustrial.com.au",
                "phone": "+61-2-9746-5521",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 10),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_emma_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 8),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2018-44521",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_emma_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(165),
                        "issuing_body": "St John Ambulance Australia",
                        "certificate_number": "SJA-FA-2025-78234",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_emma_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(915),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "CS-NSW-2025-11234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_darren"),
                "first_name": "Darren",
                "last_name": "McAllister",
                "email": "darren@southerncrossindustrial.com.au",
                "phone": "+61-4-1234-5678",
                "role": "foreman",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_darren_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2021-22345",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_darren_forklift"),
                        "certification_type": "forklift_license",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "FL-NSW-2023-88912",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_darren_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(400),
                        "expiry_date": days_ago(35),  # EXPIRED
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "CS-NSW-2024-09821",
                        "status": "expired",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_liam"),
                "first_name": "Liam",
                "last_name": "O'Connor",
                "email": "liam@southerncrossindustrial.com.au",
                "phone": "+61-4-2345-6789",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_liam_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2023-33456",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_priya"),
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "priya@southerncrossindustrial.com.au",
                "phone": "+61-4-3456-7890",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_priya_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-44567",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_priya_ewp"),
                        "certification_type": "ewp_license",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(795),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "EWP-NSW-2025-11234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_jake"),
                "first_name": "Jake",
                "last_name": "Brennan",
                "email": "",
                "phone": "+61-4-4567-8901",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_jake_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2025-55678",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_tran"),
                "first_name": "Tran",
                "last_name": "Nguyen",
                "email": "",
                "phone": "+61-4-5678-9012",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(180),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_tran_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(500),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-66789",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_ben"),
                "first_name": "Ben",
                "last_name": "Khoury",
                "email": "ben.k@southerncrossindustrial.com.au",
                "phone": "+61-4-6789-0123",
                "role": "laborer",
                "trade": "steelwork",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_ben_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2022-77890",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_ben_rigging"),
                        "certification_type": "rigging_basic",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "RIG-NSW-2024-22345",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_sam"),
                "first_name": "Sam",
                "last_name": "Patel",
                "email": "",
                "phone": "+61-4-7890-1234",
                "role": "laborer",
                "trade": "steelwork",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_sam_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-88901",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_chloe"),
                "first_name": "Chloe",
                "last_name": "Adams",
                "email": "chloe@southerncrossindustrial.com.au",
                "phone": "+61-4-8901-2345",
                "role": "safety_officer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_chloe_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2021-99012",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_chloe_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(100),
                        "expiry_date": days_from_now(265),
                        "issuing_body": "St John Ambulance Australia",
                        "certificate_number": "SJA-FA-2026-11567",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_chloe_confined"),
                        "certification_type": "confined_space",
                        "issued_date": days_ago(150),
                        "expiry_date": days_from_now(945),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "CS-NSW-2025-33456",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_matt"),
                "first_name": "Matt",
                "last_name": "Sullivan",
                "email": "",
                "phone": "+61-4-9012-3456",
                "role": "apprentice",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(60),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_matt_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(90),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2026-00123",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Harbour City Electrical ---
            {
                **base,
                "id": stable_id("wkr", "gp05_greg_elec"),
                "first_name": "Greg",
                "last_name": "Foster",
                "email": "greg@harbourcityelectrical.com.au",
                "phone": "+61-4-1111-2222",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "notes": "Sub: Harbour City Electrical",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_greg_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2020-11234",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_greg_eleclicense"),
                        "certification_type": "electrical_license",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "NSW Fair Trading",
                        "certificate_number": "EL-NSW-2021-45678",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_daniel_elec"),
                "first_name": "Daniel",
                "last_name": "Wu",
                "email": "",
                "phone": "+61-4-2222-3333",
                "role": "journeyman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "notes": "Sub: Harbour City Electrical",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_daniel_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(500),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-22345",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_amy_elec"),
                "first_name": "Amy",
                "last_name": "Tran",
                "email": "",
                "phone": "+61-4-3333-4444",
                "role": "apprentice",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(120),
                "notes": "Sub: Harbour City Electrical",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_amy_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(400),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2025-33456",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Metro Plumbing Services ---
            {
                **base,
                "id": stable_id("wkr", "gp05_steve_plumb"),
                "first_name": "Steve",
                "last_name": "Papadopoulos",
                "email": "steve@metroplumbing.com.au",
                "phone": "+61-4-4444-5555",
                "role": "foreman",
                "trade": "plumbing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "notes": "Sub: Metro Plumbing Services",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_steve_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 7),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2019-44567",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_steve_plumblicense"),
                        "certification_type": "plumbing_license",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": days_from_now(180),
                        "issuing_body": "NSW Fair Trading",
                        "certificate_number": "PL-NSW-2020-55678",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_nick_plumb"),
                "first_name": "Nick",
                "last_name": "Kovac",
                "email": "",
                "phone": "+61-4-5555-6666",
                "role": "journeyman",
                "trade": "plumbing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "notes": "Sub: Metro Plumbing Services",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_nick_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(600),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-55789",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Ironbark Steel Fabrication ---
            {
                **base,
                "id": stable_id("wkr", "gp05_tony_steel"),
                "first_name": "Tony",
                "last_name": "Marchetti",
                "email": "tony@ironbarksteel.com.au",
                "phone": "+61-4-6666-7777",
                "role": "foreman",
                "trade": "steelwork",
                "language_preference": "en",
                "hire_date": days_ago(365 * 9),
                "notes": "Sub: Ironbark Steel Fabrication",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_tony_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(365 * 8),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2018-66890",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp05_tony_rigging"),
                        "certification_type": "rigging_intermediate",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "RIG-INT-NSW-2022-11234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_kai_steel"),
                "first_name": "Kai",
                "last_name": "Thompson",
                "email": "",
                "phone": "+61-4-7777-8888",
                "role": "laborer",
                "trade": "steelwork",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "notes": "Sub: Ironbark Steel Fabrication",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_kai_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(500),
                        "expiry_date": None,
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2024-77901",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp05_marco_steel"),
                "first_name": "Marco",
                "last_name": "De Luca",
                "email": "",
                "phone": "+61-4-8888-9999",
                "role": "laborer",
                "trade": "steelwork",
                "language_preference": "en",
                "hire_date": days_ago(60),
                "notes": "Sub: Ironbark Steel Fabrication",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp05_marco_whitecard"),
                        "certification_type": "white_card",
                        "issued_date": days_ago(400),
                        "expiry_date": days_ago(10),  # EXPIRED White Card
                        "issuing_body": "SafeWork NSW",
                        "certificate_number": "WC-NSW-2025-88012",
                        "status": "expired",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 5 inspections: 3 daily, 1 equipment, 1 confined space."""
        uid = GP05_USER["uid"]
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
                "id": stable_id("insp", "gp05_daily_d7"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(7),
                "inspector_name": "Chloe Adams",
                "inspector_id": stable_id("wkr", "gp05_chloe"),
                "weather_conditions": "Overcast, mild",
                "temperature": "19C",
                "workers_on_site": 14,
                "overall_status": "pass",
                "overall_notes": "All areas housekeeping acceptable. "
                    "PPE compliance 100%. Silica dust controls in place "
                    "for floor drain cutting — wet cutting method verified.",
                "items": "[]",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(7),
            },
            {
                **base,
                "id": stable_id("insp", "gp05_daily_d3"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "Chloe Adams",
                "inspector_id": stable_id("wkr", "gp05_chloe"),
                "weather_conditions": "Sunny, warm",
                "temperature": "28C",
                "workers_on_site": 16,
                "overall_status": "fail",
                "overall_notes": "Ironbark Steel crew member (Marco De Luca) "
                    "found on site with expired White Card. "
                    "Removed from site pending renewal. "
                    "Electrical sub left cable trays unsecured overnight.",
                "corrective_actions_needed": "Marco De Luca to renew White Card "
                    "before returning to site. "
                    "Harbour City Electrical to secure all cable trays daily.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("insp", "gp05_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Chloe Adams",
                "inspector_id": stable_id("wkr", "gp05_chloe"),
                "weather_conditions": "Clear",
                "temperature": "24C",
                "workers_on_site": 17,
                "overall_status": "pass",
                "overall_notes": "Cable tray issue corrected. Marco De Luca "
                    "still off site — White Card renewal pending. "
                    "All other compliance items satisfactory.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base,
                "id": stable_id("insp", "gp05_equipment1"),
                "inspection_type": "equipment_prestart",
                "inspection_date": days_ago(1),
                "inspector_name": "Darren McAllister",
                "inspector_id": stable_id("wkr", "gp05_darren"),
                "weather_conditions": "Clear",
                "temperature": "24C",
                "workers_on_site": 17,
                "overall_status": "pass",
                "overall_notes": "Forklift pre-start check complete — tyres, "
                    "hydraulics, lights, horn, seatbelt all OK. "
                    "Scissor lift pre-start passed. "
                    "Load charts posted and legible on both machines.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base,
                "id": stable_id("insp", "gp05_confined1"),
                "inspection_type": "confined_space",
                "inspection_date": days_ago(5),
                "inspector_name": "Emma Walsh",
                "inspector_id": stable_id("wkr", "gp05_emma"),
                "weather_conditions": "Overcast",
                "temperature": "20C",
                "workers_on_site": 15,
                "overall_status": "partial",
                "overall_notes": "Mezzanine crawl space entry permit reviewed. "
                    "Atmospheric monitoring in place (O2, LEL, CO, H2S). "
                    "Standby person assigned. "
                    "Issue: rescue plan references old emergency number — "
                    "needs updating.",
                "corrective_actions_needed": "Update confined space rescue plan "
                    "with current hospital and SES contact numbers. "
                    "Re-brief confined space team before next entry.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        """Build 1 near-miss incident."""
        uid = GP05_USER["uid"]
        return [{
            "id": stable_id("inc", "gp05_nearmiss1"),
            "incident_date": days_ago(6),
            "incident_time": "11:15",
            "location": "Warehouse floor, near loading dock B",
            "severity": "near_miss",
            "status": "investigating",
            "description": "Forklift reversed into material stack while "
                "repositioning steel beams. Stack partially collapsed. "
                "No workers in immediate vicinity. Two 6m steel beams "
                "fell to floor. No injuries, minor damage to warehouse "
                "floor coating.",
            "persons_involved": "Darren McAllister (forklift operator)",
            "involved_worker_ids": [
                stable_id("wkr", "gp05_darren"),
            ],
            "witnesses": "Ben Khoury, Tony Marchetti",
            "immediate_actions_taken": "Area cordoned off. Forklift operations "
                "suspended for remainder of day. Material restacked and "
                "secured with rated chains.",
            "root_cause": "Under investigation. Possible contributing factors: "
                "limited rear visibility on forklift due to load height, "
                "material stack positioned too close to traffic lane, "
                "no spotter used for reversing manoeuvre.",
            "corrective_actions": "Implement mandatory spotter for all forklift "
                "reversing near material stacks. Reposition material staging "
                "areas minimum 2m from traffic lanes. Install convex mirrors "
                "at loading dock intersections.",
            "osha_recordable": False,
            "osha_reportable": False,
            "photo_urls": [],
            "created_at": datetime_days_ago(6),
            "updated_at": datetime_days_ago(4),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build 2 equipment items: forklift and scissor lift."""
        uid = GP05_USER["uid"]
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
                "id": stable_id("eq", "gp05_forklift1"),
                "name": "Toyota 8FG25 Counterbalance Forklift",
                "equipment_type": "forklift",
                "make": "Toyota",
                "model": "8FG25",
                "year": 2022,
                "serial_number": "TOY-8FG25-2022-44521",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "annual_inspection_date": days_ago(60),
                "annual_inspection_due": days_from_now(305),
                "annual_inspection_vendor": "Clark Equipment Australia",
                "notes": "2.5 tonne capacity. Used for steel beam and "
                    "material handling on warehouse floor. "
                    "All operators must hold current forklift licence.",
            },
            {
                **base,
                "id": stable_id("eq", "gp05_scissorlift1"),
                "name": "JLG 3246ES Electric Scissor Lift",
                "equipment_type": "aerial_lift",
                "make": "JLG",
                "model": "3246ES",
                "year": 2023,
                "serial_number": "JLG-3246ES-2023-55632",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "annual_inspection_date": days_ago(45),
                "annual_inspection_due": days_from_now(320),
                "annual_inspection_vendor": "Kennards Hire",
                "notes": "Rented from Kennards Hire. 9.92m working height. "
                    "Operators must hold EWP licence. "
                    "Used for mezzanine steelwork and electrical cable tray install.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 2 toolbox talks."""
        uid = GP05_USER["uid"]
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
                "id": stable_id("talk", "gp05_silica"),
                "topic": "Silica Dust Exposure — Wet Cutting Controls",
                "scheduled_date": days_ago(10),
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "language": "en",
                "status": "completed",
                "presented_at": datetime_days_ago(10, hour=7),
                "presented_by": "Chloe Adams",
                "overall_notes": "Reviewed SafeWork NSW silica dust WES limits. "
                    "Demonstrated wet cutting technique for concrete floor "
                    "drains. Covered RPE selection and fit testing requirements. "
                    "All workers signed attendance register.",
                "created_at": datetime_days_ago(11),
                "updated_at": datetime_days_ago(10),
            },
            {
                **base,
                "id": stable_id("talk", "gp05_confined_space"),
                "topic": "Confined Space Entry Procedures — Mezzanine Crawl Spaces",
                "scheduled_date": days_ago(4),
                "target_audience": "all_workers",
                "duration_minutes": 20,
                "language": "en",
                "status": "completed",
                "presented_at": datetime_days_ago(4, hour=7),
                "presented_by": "Emma Walsh",
                "overall_notes": "Reviewed confined space entry permit process. "
                    "Demonstrated atmospheric monitoring equipment "
                    "(four-gas detector). Covered rescue procedures and "
                    "standby person responsibilities. Identified mezzanine "
                    "crawl space access points on floor plan.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
            },
        ]

    # -----------------------------------------------------------------
    # Hazard Reports
    # -----------------------------------------------------------------

    def _build_hazards(self) -> list[dict]:
        """Build 1 hazard report for dust exposure concern."""
        uid = GP05_USER["uid"]
        return [{
            "id": stable_id("haz", "gp05_dust1"),
            "description": "Concrete cutting for new floor drains generating "
                "visible dust plume despite wet cutting method. "
                "RPE usage inconsistent among general labourers. "
                "Dust settling on lunch area surfaces 15m away.",
            "location": "Warehouse floor, bays 3-4 near new drain locations",
            "status": "open",
            "hazard_count": 1,
            "highest_severity": "high",
            "corrective_action_taken": "Additional water suppression added to "
                "cutting stations. Temporary barrier erected between cutting "
                "zone and lunch area. All workers re-briefed on mandatory "
                "RPE use during cutting operations.",
            "corrected_at": None,
            "corrected_by": None,
            "created_at": datetime_days_ago(8),
            "updated_at": datetime_days_ago(3),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build 4 daily logs."""
        uid = GP05_USER["uid"]
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
                "id": stable_id("dlog", "gp05_d7"),
                "log_date": days_ago(7),
                "superintendent_name": "Emma Walsh",
                "status": "approved",
                "workers_on_site": 14,
                "work_performed": "Mezzanine steel erection continued — north bay "
                    "columns and primary beams installed. "
                    "Electrical sub started conduit runs for three-phase "
                    "distribution board. Concrete cutting for floor drains "
                    "50% complete. Plumbing rough-in for amenities started.",
                "notes": "Silica dust controls working well with wet cutting. "
                    "All atmospheric monitoring within WES limits.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
                "submitted_at": datetime_days_ago(7, hour=17),
                "approved_at": datetime_days_ago(6, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp05_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "Emma Walsh",
                "status": "approved",
                "workers_on_site": 15,
                "work_performed": "Mezzanine steel 60% complete. Confined space "
                    "entry for crawl space above office area — atmospheric "
                    "monitoring clear. Electrical conduit 40% complete. "
                    "Floor drain cutting complete — drains set in concrete.",
                "notes": "Confined space entry permit issued for mezzanine crawl "
                    "space. Rescue plan needs emergency contact update.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=9),
            },
            {
                **base,
                "id": stable_id("dlog", "gp05_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Emma Walsh",
                "status": "submitted",
                "workers_on_site": 16,
                "work_performed": "Marco De Luca removed from site — expired "
                    "White Card identified during daily inspection. "
                    "Steel erection continued with remaining Ironbark crew. "
                    "Office partition framing started on ground floor. "
                    "Electrical cable tray install on mezzanine level.",
                "notes": "Expired White Card issue flagged to Ironbark Steel "
                    "management. Cable tray securing issue also raised with "
                    "Harbour City Electrical.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp05_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Emma Walsh",
                "status": "submitted",
                "workers_on_site": 17,
                "work_performed": "Mezzanine steel 80% complete. Loading dock B "
                    "upgrade — new dock leveller installed. "
                    "Plumbing amenities block rough-in 60% complete. "
                    "Office partition framing 40% complete. "
                    "Compressed air main line run started.",
                "notes": "Good progress across all trades. Marco De Luca still "
                    "off site — Ironbark arranging White Card renewal course.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
        ]

    # -----------------------------------------------------------------
    # Work Items
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active warehouse fitout.

        Active project — items reflect the in-flight scope.
        All values in cents (AUD).
        """
        uid = GP05_USER["uid"]
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
                "id": stable_id("wi", "gp05_item_1"),
                "description": "Warehouse floor coating \u2014 epoxy system 1200 sqm",
                "quantity": 1200,
                "unit": "SM",
                "margin_pct": 20,
                "labour_total_cents": 330000,
                "items_total_cents": 2640000,
                "sell_price_cents": 3564000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp05_lab_1"),
                        "task": "Surface prep, prime, topcoat",
                        "rate_cents": 5500,
                        "hours": 60,
                        "cost_cents": 330000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp05_item_1_mat_1"),
                        "description": "Epoxy resin system and aggregates",
                        "quantity": 1200,
                        "unit": "SM",
                        "unit_cost_cents": 2200,
                        "total_cents": 2640000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp05_item_2"),
                "description": "LED high-bay lighting upgrade",
                "quantity": 48,
                "unit": "EA",
                "margin_pct": 22,
                "labour_total_cents": 208000,
                "items_total_cents": 1368000,
                "sell_price_cents": 1922720,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp05_lab_2"),
                        "task": "Remove existing, install new fixtures",
                        "rate_cents": 6500,
                        "hours": 32,
                        "cost_cents": 208000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp05_item_2_mat_1"),
                        "description": "150W LED high-bay fixtures",
                        "quantity": 48,
                        "unit": "EA",
                        "unit_cost_cents": 28500,
                        "total_cents": 1368000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp05_item_3"),
                "description": "Racking installation \u2014 480 pallet positions",
                "quantity": 480,
                "unit": "EA",
                "margin_pct": 18,
                "labour_total_cents": 440000,
                "items_total_cents": 2160000,
                "sell_price_cents": 3068000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp05_lab_3"),
                        "task": "Install and certify racking",
                        "rate_cents": 5500,
                        "hours": 80,
                        "cost_cents": 440000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp05_item_3_mat_1"),
                        "description": "Heavy-duty pallet racking system",
                        "quantity": 480,
                        "unit": "EA",
                        "unit_cost_cents": 4500,
                        "total_cents": 2160000,
                    },
                ],
            },
        ]
