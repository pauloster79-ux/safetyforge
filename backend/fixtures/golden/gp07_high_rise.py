"""GP07 — Commercial High-Rise Phase 2 (US — New York).

The LARGEST golden project: 45-worker commercial tower (22 stories),
Phase 2 covering structural steel erection and curtain wall installation.
6 subcontractors, crew-based time entry, full sub management with COI
tracking, submittal log, tower crane + heavy equipment fleet.

Exercises complex features including:
- 15 representative workers across key roles/trades (45 total implied by headcount)
- 6 subs: steel erection, curtain wall, concrete, electrical, plumbing, elevator
- NY DOB requirements, fall protection as critical focus
- Multi-phase scheduling with safety-schedule conflicts
- Crew-based time entry (foreman enters for entire crew)
- Full sub management: COI tracking, lien waivers, performance scores
- Submittal log (3 submittals: steel shop drawings, curtain wall, elevator)
- Equipment: tower crane, concrete pump, personnel hoist, multiple aerial lifts
- 8 inspections (daily, scaffold, fall protection, equipment)
- 2 incidents (1 near-miss, 1 first-aid)
- 6 daily logs, 3 toolbox talks, 2 hazard reports (1 corrected, 1 open)
- Certification states: expired OSHA 30, crane operator cert expiring
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP07_COMPANY, GP07_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP07Seeder(GoldenProjectSeeder):
    """Seed GP07: Commercial High-Rise Phase 2 — New York."""

    GP_SLUG = "gp07"
    COMPANY_ID = "comp_gp07"
    PROJECT_ID = "proj_gp07"

    def seed(self) -> dict[str, int]:
        """Seed all GP07 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP07_COMPANY)
        self.seed_user(GP07_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "450 West 33rd — Phase 2 Structural & Envelope",
            "address": "450 West 33rd Street, New York, NY 10001",
            "client_name": "Hudson Yards Development Group LLC",
            "project_type": "commercial",
            "trade_types": [
                "general", "steel_erection", "curtain_wall",
                "concrete", "electrical", "plumbing", "elevator",
            ],
            "start_date": days_ago(90),
            "end_date": days_from_now(270),
            "estimated_workers": 45,
            "description": "22-story commercial office tower, Phase 2: "
                "structural steel erection (floors 8-22), curtain wall "
                "installation (floors 1-10), concrete decks, core MEP "
                "risers, and elevator installation. Steel topping out "
                "targeted in 14 weeks.",
            "special_hazards": "High-rise fall exposure above 6 stories. "
                "Tower crane swing radius over active street. "
                "Steel erection with bolted connections at height. "
                "Curtain wall panel lifting in high-wind corridor. "
                "Concrete pumping to upper floors. "
                "NY DOB controlled inspection requirements. "
                "Adjacent occupied building within 15 feet on east side.",
            "nearest_hospital": "NYC Health + Hospitals/Bellevue, "
                "462 First Avenue, New York, NY 10016",
            "emergency_contact_name": "Anthony Russo",
            "emergency_contact_phone": "212-555-0634",
            "state": "active",
            "status": "normal",
            "compliance_score": 68,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP07_USER["uid"],
            "actor_type": "human",
            "updated_by": GP07_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (15 representative of 45 total) ---
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
        """Build 15 representative workers across GC crew and 6 subs.

        The project has 45 workers total; these 15 represent key roles
        and certification states. Remaining 30 are implied by project
        headcount and crew-based time entry.
        """
        uid = GP07_USER["uid"]
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
                "id": stable_id("wkr", "gp07_anthony"),
                "first_name": "Anthony",
                "last_name": "Russo",
                "email": "arusso@manhattanskyline.com",
                "phone": "212-555-0634",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 12),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_anthony_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-21-5578",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_anthony_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2022-44812",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_anthony_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(185),
                        "issuing_body": "American Red Cross",
                        "certificate_number": "ARC-CPR-2025-78234",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp07_frank"),
                "first_name": "Frank",
                "last_name": "DeLuca",
                "email": "fdeluca@manhattanskyline.com",
                "phone": "212-555-0641",
                "role": "safety_manager",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 9),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_frank_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-20-3321",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_frank_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2022-44813",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_frank_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "OSHA",
                        "certificate_number": "FP-NY-2025-8812",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp07_jimmy"),
                "first_name": "Jimmy",
                "last_name": "Costello",
                "email": "jcostello@manhattanskyline.com",
                "phone": "212-555-0655",
                "role": "foreman",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "notes": "Concrete crew foreman. Enters crew time for 8 laborers.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_jimmy_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-20-3322",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_jimmy_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-55901",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp07_pawel"),
                "first_name": "Pawel",
                "last_name": "Kowalski",
                "email": "",
                "phone": "718-555-0702",
                "role": "laborer",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "notes": "GC laborer, concrete crew",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_pawel_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-23-9923",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_pawel_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-55902",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Empire Steel Erectors (steel erection) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_ray_steel"),
                "first_name": "Ray",
                "last_name": "Mahoney",
                "email": "ray@empiresteel.com",
                "phone": "718-555-0801",
                "role": "foreman",
                "trade": "steel_erection",
                "language_preference": "en",
                "hire_date": days_ago(365 * 10),
                "notes": "Sub: Empire Steel Erectors. Ironworker foreman, "
                    "crew of 12. Enters crew time.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_ray_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-19-2245",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_ray_fall"),
                        "certification_type": "fall_protection",
                        "issued_date": days_ago(150),
                        "expiry_date": days_from_now(945),
                        "issuing_body": "OSHA",
                        "certificate_number": "FP-NY-2025-9901",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_ray_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2022-67012",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_ray_rigging"),
                        "certification_type": "rigging_signalperson",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(730),
                        "issuing_body": "NCCCO",
                        "certificate_number": "NCCCO-RIG-2023-4421",
                        "status": "valid",
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wkr", "gp07_sean_steel"),
                "first_name": "Sean",
                "last_name": "O'Malley",
                "email": "",
                "phone": "718-555-0815",
                "role": "journeyman",
                "trade": "steel_erection",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "notes": "Sub: Empire Steel Erectors. Connector/bolter.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_sean_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-21-5601",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_sean_osha30_expired"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 8),
                        "expiry_date": days_ago(365 * 3),
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-17-1102",
                        "status": "expired",
                    },
                ],
            },
            # --- Sub: Metro Curtain Wall Systems (curtain wall) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_marco_cw"),
                "first_name": "Marco",
                "last_name": "Bianchi",
                "email": "marco@metrocurtainwall.com",
                "phone": "212-555-0901",
                "role": "foreman",
                "trade": "curtain_wall",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "notes": "Sub: Metro Curtain Wall Systems. Crew of 6.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_marco_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-22-7789",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_marco_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-71201",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Gotham Concrete Corp (concrete) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_hector_conc"),
                "first_name": "Hector",
                "last_name": "Reyes",
                "email": "hreyes@gothamconcrete.com",
                "phone": "718-555-0934",
                "role": "foreman",
                "trade": "concrete",
                "language_preference": "both",
                "hire_date": days_ago(365 * 9),
                "notes": "Sub: Gotham Concrete Corp. Crew of 8.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_hector_osha30"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-20-4489",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_hector_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-71202",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Five Boroughs Electric (electrical) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_vince_elec"),
                "first_name": "Vincent",
                "last_name": "Moretti",
                "email": "vmoretti@fiveboroughselectric.com",
                "phone": "718-555-0967",
                "role": "foreman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 11),
                "notes": "Sub: Five Boroughs Electric. Crew of 5.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_vince_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-22-8834",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_vince_electrical"),
                        "certification_type": "electrical_safety",
                        "issued_date": days_ago(250),
                        "expiry_date": days_from_now(480),
                        "issuing_body": "NFPA",
                        "certificate_number": "NFPA-70E-2025-6601",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_vince_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-71203",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Hudson Mechanical (plumbing) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_pete_plumb"),
                "first_name": "Pete",
                "last_name": "Gallagher",
                "email": "pgallagher@hudsonmechanical.com",
                "phone": "212-555-0988",
                "role": "foreman",
                "trade": "plumbing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 8),
                "notes": "Sub: Hudson Mechanical. Crew of 4.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_pete_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 4),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-21-5612",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_pete_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2024-89012",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Vertical Transport Inc (elevator) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_dan_elev"),
                "first_name": "Dan",
                "last_name": "Kessler",
                "email": "dkessler@verticaltransport.com",
                "phone": "516-555-1012",
                "role": "foreman",
                "trade": "elevator",
                "language_preference": "en",
                "hire_date": days_ago(365 * 14),
                "notes": "Sub: Vertical Transport Inc. Crew of 3. "
                    "Elevator installation floors 1-10.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_dan_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-20-3345",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_dan_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-71204",
                        "status": "valid",
                    },
                ],
            },
            # --- Tower crane operator (GC-employed) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_mike_crane"),
                "first_name": "Mike",
                "last_name": "Santoro",
                "email": "msantoro@manhattanskyline.com",
                "phone": "347-555-1045",
                "role": "operator",
                "trade": "crane_operation",
                "language_preference": "en",
                "hire_date": days_ago(365 * 15),
                "notes": "Tower crane operator. NCCCO certified. "
                    "Crane operator cert expiring in 20 days.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_mike_crane_nccco"),
                        "certification_type": "crane_operator",
                        "issued_date": days_ago(365 * 5),
                        "expiry_date": days_from_now(20),  # EXPIRING SOON
                        "issuing_body": "NCCCO",
                        "certificate_number": "NCCCO-TLL-2021-7823",
                        "status": "expiring_soon",
                    },
                    {
                        "id": stable_id("cert", "gp07_mike_crane_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-19-4490",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_mike_crane_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2022-67013",
                        "status": "valid",
                    },
                ],
            },
            # --- Laborer with EXPIRED OSHA 30 (problem state) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_carlos_labor"),
                "first_name": "Carlos",
                "last_name": "Mendoza",
                "email": "",
                "phone": "347-555-1067",
                "role": "laborer",
                "trade": "general",
                "language_preference": "both",
                "hire_date": days_ago(365 * 4),
                "notes": "GC laborer. OSHA 30 expired — needs renewal.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_carlos_osha30_exp"),
                        "certification_type": "osha_30",
                        "issued_date": days_ago(365 * 6),
                        "expiry_date": days_ago(60),  # EXPIRED
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA30-NY-19-6678",
                        "status": "expired",
                    },
                    {
                        "id": stable_id("cert", "gp07_carlos_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2023-71205",
                        "status": "valid",
                    },
                ],
            },
            # --- Concrete laborer (Spanish-speaking) ---
            {
                **base,
                "id": stable_id("wkr", "gp07_edgar_conc"),
                "first_name": "Edgar",
                "last_name": "Dominguez",
                "email": "",
                "phone": "347-555-1089",
                "role": "laborer",
                "trade": "concrete",
                "language_preference": "es",
                "hire_date": days_ago(365 * 2),
                "notes": "Sub: Gotham Concrete Corp.",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp07_edgar_osha10"),
                        "certification_type": "osha_10",
                        "issued_date": days_ago(365),
                        "expiry_date": None,
                        "issuing_body": "OSHA Authorized Trainer",
                        "certificate_number": "OSHA10-NY-24-2291",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp07_edgar_sst"),
                        "certification_type": "nyc_sst",
                        "issued_date": days_ago(300),
                        "expiry_date": None,
                        "issuing_body": "NYC DOB",
                        "certificate_number": "SST-NY-2025-91001",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build 8 inspections: daily, scaffold, fall protection, equipment."""
        uid = GP07_USER["uid"]
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
                "id": stable_id("insp", "gp07_daily_d7"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(7),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Clear, windy",
                "temperature": "42°F",
                "workers_on_site": 38,
                "overall_status": "pass",
                "overall_notes": "All trades working. Steel crew on floors 14-15. "
                    "Curtain wall crew floors 5-6. Wind gusts to 22 mph — "
                    "monitored but within limits for steel erection.",
                "items": "[]",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(7),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_daily_d5"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(5),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Overcast, light rain AM",
                "temperature": "48°F",
                "workers_on_site": 35,
                "overall_status": "pass",
                "overall_notes": "Rain delay until 10 AM. Steel crew stood down "
                    "for wet conditions on upper floors. Concrete pour on "
                    "floor 12 completed after delay.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_daily_d3"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Sunny",
                "temperature": "55°F",
                "workers_on_site": 42,
                "overall_status": "partial",
                "overall_notes": "Near-miss incident on floor 16 — bolt dropped "
                    "from connection. Exclusion zone not fully established below. "
                    "See incident report. All other areas compliant.",
                "corrective_actions_needed": "Steel crew to establish overhead "
                    "protection netting on floors where bolting is active. "
                    "Review controlled decking zone procedures.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_daily_d1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(1),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Partly cloudy",
                "temperature": "52°F",
                "workers_on_site": 44,
                "overall_status": "pass",
                "overall_notes": "Overhead netting installed on floors 15-16. "
                    "Controlled decking zone signage updated. "
                    "All corrective actions from scaffold inspection complete. "
                    "Full crew on site.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_scaffold1"),
                "inspection_type": "scaffold",
                "inspection_date": days_ago(6),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Clear",
                "temperature": "50°F",
                "workers_on_site": 40,
                "overall_status": "fail",
                "overall_notes": "Suspended scaffold on east elevation (curtain wall) "
                    "missing outrigger counterweight on north end. "
                    "Guardrail not secured at re-entry point floor 7.",
                "corrective_actions_needed": "Add counterweight to north outrigger. "
                    "Secure guardrail gate at floor 7 re-entry. "
                    "Re-inspect before use. Tag out until corrected.",
                "items": "[]",
                "created_at": datetime_days_ago(6),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_fall1"),
                "inspection_type": "fall_protection",
                "inspection_date": days_ago(4),
                "inspector_name": "Frank DeLuca",
                "inspector_id": stable_id("wkr", "gp07_frank"),
                "weather_conditions": "Sunny",
                "temperature": "53°F",
                "workers_on_site": 41,
                "overall_status": "partial",
                "overall_notes": "Steel erection crew using proper 100% tie-off. "
                    "Connector harness inspections passed. "
                    "Perimeter cable on floor 14 missing at 2 column bays. "
                    "Controlled decking zone signage faded on floor 15.",
                "corrective_actions_needed": "Install perimeter cable at floor 14 "
                    "bays C3-C4 and D2-D3. Replace faded CDZ signage on floor 15.",
                "items": "[]",
                "created_at": datetime_days_ago(4),
                "updated_at": datetime_days_ago(4),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_equip_crane"),
                "inspection_type": "equipment",
                "inspection_date": days_ago(2),
                "inspector_name": "Mike Santoro",
                "inspector_id": stable_id("wkr", "gp07_mike_crane"),
                "weather_conditions": "Clear",
                "temperature": "49°F",
                "workers_on_site": 43,
                "overall_status": "pass",
                "overall_notes": "Tower crane daily pre-shift inspection. "
                    "All limit switches tested. Wire rope condition good. "
                    "Swing radius clear. Load charts posted.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("insp", "gp07_equip_hoist"),
                "inspection_type": "equipment",
                "inspection_date": days_ago(2),
                "inspector_name": "Anthony Russo",
                "inspector_id": stable_id("wkr", "gp07_anthony"),
                "weather_conditions": "Clear",
                "temperature": "49°F",
                "workers_on_site": 43,
                "overall_status": "pass",
                "overall_notes": "Personnel hoist monthly inspection. "
                    "Safety devices tested — all functional. "
                    "Door interlocks working. Emergency stop tested. "
                    "Capacity placard current.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
        ]

    # -----------------------------------------------------------------
    # Incidents
    # -----------------------------------------------------------------

    def _build_incidents(self) -> list[dict]:
        """Build 2 incidents: 1 near-miss (bolt drop), 1 first-aid."""
        uid = GP07_USER["uid"]
        return [
            {
                "id": stable_id("inc", "gp07_nearmiss1"),
                "incident_date": days_ago(3),
                "incident_time": "11:15",
                "location": "Floor 16, steel erection zone — column bay C4",
                "severity": "near_miss",
                "status": "investigating",
                "description": "A 3/4-inch structural bolt fell approximately "
                    "160 feet from floor 16 connection work to grade level. "
                    "Bolt landed inside the controlled access zone on West 33rd "
                    "sidewalk bridge. No pedestrians or workers struck. "
                    "Sidewalk bridge canopy prevented bolt from reaching street.",
                "persons_involved": "Sean O'Malley (was making connection)",
                "involved_worker_ids": [
                    stable_id("wkr", "gp07_sean_steel"),
                ],
                "witnesses": "Ray Mahoney (steel foreman), "
                    "Frank DeLuca (safety manager)",
                "immediate_actions_taken": "Stopped steel erection. "
                    "Expanded exclusion zone below active connection areas. "
                    "Reviewed bolt bag procedures with all connectors. "
                    "Notified NY DOB site safety manager.",
                "root_cause": "Under investigation. Contributing factors: "
                    "bolt bag not secured to harness during connection, "
                    "overhead protection netting not installed at floor 16.",
                "corrective_actions": "Install overhead debris netting at all "
                    "active steel floors. Bolt bags to be tethered to harness "
                    "at all times. Daily bolt bag inspection added to pre-shift.",
                "osha_recordable": False,
                "osha_reportable": False,
                "photo_urls": [],
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(2),
                "created_by": uid,
                "actor_type": "human",
                "updated_by": uid,
                "updated_actor_type": "human",
            },
            {
                "id": stable_id("inc", "gp07_firstaid1"),
                "incident_date": days_ago(8),
                "incident_time": "14:45",
                "location": "Floor 9, curtain wall staging area",
                "severity": "first_aid",
                "status": "closed",
                "description": "Worker sustained a laceration to right forearm "
                    "while handling curtain wall panel aluminum framing. "
                    "Cut approximately 3 inches long, superficial. "
                    "First aid administered on site — cleaned, butterfly "
                    "bandage applied. Worker returned to work.",
                "persons_involved": "Marco Bianchi (curtain wall foreman)",
                "involved_worker_ids": [
                    stable_id("wkr", "gp07_marco_cw"),
                ],
                "witnesses": "Frank DeLuca (safety manager)",
                "immediate_actions_taken": "First aid administered. "
                    "Cut-resistant gloves issued to curtain wall crew. "
                    "Sharp edges on panel framing flagged with tape.",
                "root_cause": "Worker was not wearing cut-resistant gloves "
                    "while handling aluminum extrusion with burrs from shop cut.",
                "corrective_actions": "Cut-resistant gloves (ANSI A4) mandatory "
                    "for all curtain wall panel handling. "
                    "Curtain wall sub to deburr all shop-cut edges before delivery.",
                "osha_recordable": False,
                "osha_reportable": False,
                "photo_urls": [],
                "created_at": datetime_days_ago(8),
                "updated_at": datetime_days_ago(6),
                "created_by": uid,
                "actor_type": "human",
                "updated_by": uid,
                "updated_actor_type": "human",
            },
        ]

    # -----------------------------------------------------------------
    # Equipment
    # -----------------------------------------------------------------

    def _build_equipment(self) -> list[dict]:
        """Build equipment: tower crane, concrete pump, personnel hoist, aerial lifts."""
        uid = GP07_USER["uid"]
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
                "id": stable_id("eq", "gp07_tower_crane"),
                "name": "Liebherr 280 EC-H Tower Crane",
                "equipment_type": "tower_crane",
                "make": "Liebherr",
                "model": "280 EC-H 12 Litronic",
                "year": 2020,
                "serial_number": "LH-280EC-2020-11892",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(0),
                "next_inspection_due": days_from_now(1),
                "annual_inspection_date": days_ago(45),
                "annual_inspection_due": days_from_now(320),
                "annual_inspection_vendor": "Crane Industry Services",
                "notes": "Max capacity 12 metric tons. Boom length 65m. "
                    "Swing radius impacts West 33rd St and adjacent building. "
                    "NY DOB crane notice permit CN-2025-4421 on file.",
            },
            {
                **base,
                "id": stable_id("eq", "gp07_concrete_pump"),
                "name": "Putzmeister BSF 42-5 Concrete Pump",
                "equipment_type": "concrete_pump",
                "make": "Putzmeister",
                "model": "BSF 42-5.16H",
                "year": 2022,
                "serial_number": "PM-BSF42-2022-7834",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_pour",
                "last_inspection_date": days_ago(5),
                "next_inspection_due": days_ago(0),
                "notes": "Truck-mounted boom pump. 42m vertical reach. "
                    "Requires street closure permit for setup on 33rd St.",
            },
            {
                **base,
                "id": stable_id("eq", "gp07_hoist"),
                "name": "Alimak SC 65/32 Personnel Hoist",
                "equipment_type": "personnel_hoist",
                "make": "Alimak",
                "model": "SC 65/32",
                "year": 2021,
                "serial_number": "ALM-SC65-2021-3345",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "daily",
                "last_inspection_date": days_ago(0),
                "next_inspection_due": days_from_now(1),
                "annual_inspection_date": days_ago(60),
                "annual_inspection_due": days_from_now(305),
                "annual_inspection_vendor": "Alimak Service Group",
                "notes": "Dual car, 6500 lb capacity each car. "
                    "Current height serves floors 1-18. "
                    "Jump scheduled when steel reaches floor 20.",
            },
            {
                **base,
                "id": stable_id("eq", "gp07_lift_boom1"),
                "name": "JLG 600S Telescopic Boom Lift",
                "equipment_type": "aerial_lift",
                "make": "JLG",
                "model": "600S",
                "year": 2022,
                "serial_number": "JLG-600S-2022-44521",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "annual_inspection_date": days_ago(120),
                "annual_inspection_due": days_from_now(245),
                "annual_inspection_vendor": "United Rentals",
                "notes": "60 ft platform height. Used for curtain wall "
                    "installation on lower floors. Operators must hold "
                    "aerial lift certification.",
            },
            {
                **base,
                "id": stable_id("eq", "gp07_lift_scissor1"),
                "name": "Genie GS-4047 Scissor Lift",
                "equipment_type": "aerial_lift",
                "make": "Genie",
                "model": "GS-4047",
                "year": 2023,
                "serial_number": "GEN-GS40-2023-8921",
                "current_project_id": self.PROJECT_ID,
                "inspection_frequency": "pre_shift",
                "last_inspection_date": days_ago(1),
                "next_inspection_due": days_ago(0),
                "notes": "40 ft platform height. Interior use on completed "
                    "concrete decks for MEP overhead work.",
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build 3 toolbox talks."""
        uid = GP07_USER["uid"]
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
                "id": stable_id("talk", "gp07_fall_protection"),
                "topic": "Fall Protection — 100% Tie-Off and Controlled Decking Zones",
                "scheduled_date": days_ago(6),
                "target_audience": "all_workers",
                "duration_minutes": 20,
                "language": "both",
                "status": "completed",
                "presented_at": datetime_days_ago(6, hour=6),
                "presented_by": "Frank DeLuca",
                "overall_notes": "Reviewed OSHA 1926.760 steel erection fall "
                    "protection requirements. Demonstrated proper connector "
                    "harness inspection. Reviewed controlled decking zone "
                    "boundaries and signage requirements.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
            },
            {
                **base,
                "id": stable_id("talk", "gp07_dropped_objects"),
                "topic": "Dropped Object Prevention — Overhead Protection",
                "scheduled_date": days_ago(2),
                "target_audience": "all_workers",
                "duration_minutes": 15,
                "language": "both",
                "status": "completed",
                "presented_at": datetime_days_ago(2, hour=6),
                "presented_by": "Frank DeLuca",
                "overall_notes": "Following near-miss bolt drop on floor 16. "
                    "Reviewed tool tethering requirements. Bolt bag procedures. "
                    "Exclusion zone protocols. All steel crew signed attendance.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("talk", "gp07_crane_safety"),
                "topic": "Tower Crane Safety — Signal Person Communication",
                "scheduled_date": days_from_now(2),
                "target_audience": "steel_erection",
                "duration_minutes": 20,
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
        uid = GP07_USER["uid"]
        return [
            {
                "id": stable_id("haz", "gp07_perimeter1"),
                "description": "Perimeter cable missing at two column bays on "
                    "floor 14 (bays C3-C4 and D2-D3). Open edge with "
                    "160+ foot fall exposure. Discovered during fall "
                    "protection inspection.",
                "location": "Floor 14, column bays C3-C4 and D2-D3",
                "status": "corrected",
                "hazard_count": 2,
                "highest_severity": "critical",
                "corrective_action_taken": "Perimeter cable installed at both "
                    "locations. Steel erection foreman verified all column "
                    "bays on floors 13-16 have perimeter protection.",
                "corrected_at": datetime_days_ago(3),
                "corrected_by": "Ray Mahoney",
                "created_at": datetime_days_ago(4),
                "updated_at": datetime_days_ago(3),
                "created_by": uid,
                "actor_type": "human",
                "updated_by": uid,
                "updated_actor_type": "human",
            },
            {
                "id": stable_id("haz", "gp07_sidewalk1"),
                "description": "Sidewalk bridge on West 33rd St showing signs "
                    "of ponding water after rain. Drainage not clearing "
                    "properly. Potential for ice formation in cold weather. "
                    "Pedestrian slip hazard.",
                "location": "West 33rd St sidewalk bridge, south side",
                "status": "open",
                "hazard_count": 1,
                "highest_severity": "medium",
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
        """Build 6 daily logs with good history."""
        uid = GP07_USER["uid"]
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
                "id": stable_id("dlog", "gp07_d10"),
                "log_date": days_ago(10),
                "superintendent_name": "Anthony Russo",
                "status": "approved",
                "workers_on_site": 36,
                "work_performed": "Steel erection floors 13-14 connections. "
                    "Curtain wall panels installed floors 4-5. "
                    "Concrete deck pour floor 11 — 85 yards placed. "
                    "Electrical conduit run in core, floors 6-8.",
                "notes": "Steel delivery delayed 2 hours — truck stuck at Holland "
                    "Tunnel. Adjusted crane schedule to prioritize curtain wall "
                    "panels until steel arrived.",
                "created_at": datetime_days_ago(10),
                "updated_at": datetime_days_ago(9),
                "submitted_at": datetime_days_ago(10, hour=17),
                "approved_at": datetime_days_ago(9, hour=7),
            },
            {
                **base,
                "id": stable_id("dlog", "gp07_d7"),
                "log_date": days_ago(7),
                "superintendent_name": "Anthony Russo",
                "status": "approved",
                "workers_on_site": 38,
                "work_performed": "Steel erection floors 14-15 commenced. "
                    "Curtain wall floors 5-6. "
                    "Scaffold erected east elevation for curtain wall access. "
                    "Elevator shaft work started — rail brackets floors 1-5.",
                "notes": "Wind gusts to 22 mph PM — steel crew monitored, "
                    "remained within safe limits. "
                    "Scaffold inspection conducted — see report.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
                "submitted_at": datetime_days_ago(7, hour=17),
                "approved_at": datetime_days_ago(6, hour=7),
            },
            {
                **base,
                "id": stable_id("dlog", "gp07_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "Anthony Russo",
                "status": "approved",
                "workers_on_site": 35,
                "work_performed": "Rain delay until 10 AM — steel crew stood down. "
                    "Concrete pour floor 12 after delay — 92 yards placed. "
                    "Curtain wall crew worked interior staging (weather protected). "
                    "Plumbing risers core, floors 7-9.",
                "notes": "Scaffold corrective actions completed and re-inspected. "
                    "Cleared for use.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=7),
            },
            {
                **base,
                "id": stable_id("dlog", "gp07_d3"),
                "log_date": days_ago(3),
                "superintendent_name": "Anthony Russo",
                "status": "submitted",
                "workers_on_site": 42,
                "work_performed": "Steel erection floors 15-16 — connections in progress. "
                    "Curtain wall floors 6-7. Concrete deck prep floor 13. "
                    "Electrical panel rooms framed floors 5-6. "
                    "Elevator rail brackets floors 5-8.",
                "notes": "NEAR-MISS INCIDENT: bolt dropped from floor 16 to "
                    "sidewalk bridge. No injuries. Work stopped, exclusion zones "
                    "expanded, bolt bag procedures reviewed. See incident report.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp07_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Anthony Russo",
                "status": "submitted",
                "workers_on_site": 44,
                "work_performed": "Overhead debris netting installed floors 15-16. "
                    "Steel erection floor 16 connections completed. "
                    "Floor 17 columns set by crane. "
                    "Curtain wall floors 7-8. Concrete pour floor 13 — 88 yards. "
                    "Personnel hoist jump scheduled for next week.",
                "notes": "All corrective actions from fall protection and scaffold "
                    "inspections now complete. Crane operator cert renewal "
                    "scheduled — expires in 20 days.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
            {
                **base,
                "id": stable_id("dlog", "gp07_today"),
                "log_date": days_ago(0),
                "superintendent_name": "Anthony Russo",
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
        """Build work items for the active high-rise tower build.

        Active project — items reflect the in-flight scope.
        All values in cents (USD).
        """
        uid = GP07_USER["uid"]
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
                "id": stable_id("wi", "gp07_item_1"),
                "description": "Structural steel \u2014 columns and beams for Phase 2",
                "quantity": 85,
                "unit": "TON",
                "margin_pct": 18,
                "labour_total_cents": 5250000,
                "items_total_cents": 32725000,
                "sell_price_cents": 44810500,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp07_lab_1"),
                        "task": "Erect and connect steel",
                        "rate_cents": 12500,
                        "hours": 420,
                        "cost_cents": 5250000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp07_item_1_mat_1"),
                        "description": "Fabricated structural steel delivered",
                        "quantity": 85,
                        "unit": "TON",
                        "unit_cost_cents": 385000,
                        "total_cents": 32725000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp07_item_2"),
                "description": "Concrete decking \u2014 12 floors, post-tension",
                "quantity": 98000,
                "unit": "SF",
                "margin_pct": 20,
                "labour_total_cents": 17100000,
                "items_total_cents": 48500000,
                "sell_price_cents": 78720000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp07_lab_2"),
                        "task": "Form, place, pour, finish",
                        "rate_cents": 9500,
                        "hours": 1800,
                        "cost_cents": 17100000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp07_item_2_mat_1"),
                        "description": "Concrete, PT tendons, rebar, formwork",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 48500000,
                        "total_cents": 48500000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp07_item_3"),
                "description": "Envelope \u2014 curtain wall and glazing installation",
                "quantity": 42000,
                "unit": "SF",
                "margin_pct": 22,
                "labour_total_cents": 11040000,
                "items_total_cents": 357000000,
                "sell_price_cents": 449008800,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp07_lab_3"),
                        "task": "Install unitised curtain wall",
                        "rate_cents": 11500,
                        "hours": 960,
                        "cost_cents": 11040000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp07_item_3_mat_1"),
                        "description": "Unitised curtain wall panels",
                        "quantity": 42000,
                        "unit": "SF",
                        "unit_cost_cents": 8500,
                        "total_cents": 357000000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp07_item_4"),
                "description": "Elevator pits and shaft fit-out \u2014 4 cars",
                "quantity": 4,
                "unit": "EA",
                "margin_pct": 25,
                "labour_total_cents": 1260000,
                "items_total_cents": 1140000,
                "sell_price_cents": 3000000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp07_lab_4"),
                        "task": "Pit and shaft finishing work",
                        "rate_cents": 10500,
                        "hours": 120,
                        "cost_cents": 1260000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp07_item_4_mat_1"),
                        "description": "Waterproofing, rails, hardware",
                        "quantity": 4,
                        "unit": "EA",
                        "unit_cost_cents": 285000,
                        "total_cents": 1140000,
                    },
                ],
            },
        ]
