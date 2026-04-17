"""GP02 — Residential Extension, Deck Build (CA — Ontario).

Small-crew golden project: 3 workers + 1 sub, OHSA Ontario regs,
Working-at-Heights training required, simple punch list at closeout,
small crew time tracking scenario.

Exercises:
- Workers with Ontario certifications (Working at Heights, WHMIS)
- One cert expiring soon (Working at Heights)
- 2 inspections (one pass, one partial)
- 1 toolbox talk (completed)
- 3 daily logs
- Simple punch list (project 75% done)
- No incidents
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP02_COMPANY, GP02_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP02Seeder(GoldenProjectSeeder):
    """Seed GP02: Residential Deck Build — Ontario."""

    GP_SLUG = "gp02"
    COMPANY_ID = "comp_gp02"
    PROJECT_ID = "proj_gp02"

    def seed(self) -> dict[str, int]:
        """Seed all GP02 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP02_COMPANY)
        self.seed_user(GP02_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Kowalski Rear Deck Extension",
            "address": "38 Birchwood Crescent, Etobicoke, ON M9C 3H4",
            "client_name": "Tom & Linda Kowalski",
            "project_type": "renovation",
            "trade_types": ["general", "electrical"],
            "start_date": days_ago(28),
            "end_date": days_from_now(10),
            "estimated_workers": 4,
            "description": "240 sq ft pressure-treated deck addition off rear "
                "sliding door. Includes helical pile foundation (8 piles), "
                "double beam construction, composite decking surface, "
                "aluminum railing system, and one exterior weatherproof "
                "GFCI outlet for patio use.",
            "special_hazards": "Working at heights above 3 metres during "
                "ledger board and beam installation. Excavation for "
                "helical pile caps near municipal easement — locate "
                "buried utilities before drilling.",
            "nearest_hospital": "Etobicoke General Hospital, "
                "101 Humber College Blvd, Toronto, ON M9V 1R8",
            "emergency_contact_name": "Sarah Chen",
            "emergency_contact_phone": "416-555-0233",
            "state": "active",
            "status": "normal",
            "compliance_score": 90,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP02_USER["uid"],
            "actor_type": "human",
            "updated_by": GP02_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers ---
        workers = self._build_workers()
        worker_ids = [w["id"] for w in workers]
        counts["workers"] = self.seed_workers(workers)
        self.assign_workers_to_project(worker_ids)

        # --- Inspections ---
        counts["inspections"] = self.seed_inspections(self._build_inspections())

        # --- Toolbox Talk ---
        counts["toolbox_talks"] = self.seed_toolbox_talks(self._build_talks())

        # --- Daily Logs ---
        counts["daily_logs"] = self.seed_daily_logs(self._build_daily_logs())

        # --- Deficiency List (punch list) ---
        dl_id = stable_id("dlist", "gp02_closeout")
        self.seed_deficiency_lists([self._build_deficiency_list(dl_id)])
        items = self._build_deficiency_items()
        counts["deficiency_items"] = self.seed_deficiency_items(items, dl_id)
        counts["deficiency_lists"] = 1

        counts["incidents"] = 0
        counts["equipment"] = 0
        counts["hazard_reports"] = 0
        counts["rfis"] = 0

        # --- Work Items ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        return counts

    # -----------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------

    def _build_workers(self) -> list[dict]:
        """Build worker data for GP02.

        Returns:
            List of worker dicts.
        """
        uid = GP02_USER["uid"]
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
            # --- Sarah Chen (superintendent / owner) ---
            {
                **base,
                "id": stable_id("wkr", "gp02_sarah"),
                "first_name": "Sarah",
                "last_name": "Chen",
                "email": "sarah@lakeshorebuilders.ca",
                "phone": "416-555-0233",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 6),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp02_sarah_wah"),
                        "certification_type": "working_at_heights",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "IHSA (Infrastructure Health & Safety Association)",
                        "certificate_number": "IHSA-WAH-2024-08821",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp02_sarah_whmis"),
                        "certification_type": "whmis",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(430),
                        "issuing_body": "Ontario MOL Approved Provider",
                        "certificate_number": "WHMIS-ON-2025-3344",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp02_sarah_firstaid"),
                        "certification_type": "first_aid_cpr",
                        "issued_date": days_ago(180),
                        "expiry_date": days_from_now(915),
                        "issuing_body": "Canadian Red Cross",
                        "certificate_number": "CRC-FA-2025-77432",
                        "status": "valid",
                    },
                ],
            },
            # --- Dan Petrov (carpenter) ---
            {
                **base,
                "id": stable_id("wkr", "gp02_dan"),
                "first_name": "Dan",
                "last_name": "Petrov",
                "email": "dan@lakeshorebuilders.ca",
                "phone": "416-555-0245",
                "role": "carpenter",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365 * 3),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp02_dan_wah"),
                        "certification_type": "working_at_heights",
                        "issued_date": days_ago(365 * 3),
                        "expiry_date": days_from_now(18),  # EXPIRING SOON
                        "issuing_body": "IHSA (Infrastructure Health & Safety Association)",
                        "certificate_number": "IHSA-WAH-2023-04412",
                        "status": "expiring_soon",
                    },
                    {
                        "id": stable_id("cert", "gp02_dan_whmis"),
                        "certification_type": "whmis",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "Ontario MOL Approved Provider",
                        "certificate_number": "WHMIS-ON-2024-1189",
                        "status": "valid",
                    },
                ],
            },
            # --- Tyler Osei (apprentice) ---
            {
                **base,
                "id": stable_id("wkr", "gp02_tyler"),
                "first_name": "Tyler",
                "last_name": "Osei",
                "email": "",
                "phone": "416-555-0261",
                "role": "apprentice",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(60),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp02_tyler_wah"),
                        "certification_type": "working_at_heights",
                        "issued_date": days_ago(75),
                        "expiry_date": days_from_now(365 * 3 - 75),
                        "issuing_body": "IHSA (Infrastructure Health & Safety Association)",
                        "certificate_number": "IHSA-WAH-2026-01198",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp02_tyler_whmis"),
                        "certification_type": "whmis",
                        "issued_date": days_ago(75),
                        "expiry_date": days_from_now(365 * 3 - 75),
                        "issuing_body": "Ontario MOL Approved Provider",
                        "certificate_number": "WHMIS-ON-2026-0088",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Marco Rizzo (electrician — outdoor outlet) ---
            {
                **base,
                "id": stable_id("wkr", "gp02_marco"),
                "first_name": "Marco",
                "last_name": "Rizzo",
                "email": "marco@rizzoelectric.ca",
                "phone": "416-555-0289",
                "role": "journeyman",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 10),
                "notes": "Sub: Rizzo Electric — outdoor GFCI outlet install",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp02_marco_wah"),
                        "certification_type": "working_at_heights",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 2),
                        "issuing_body": "IHSA (Infrastructure Health & Safety Association)",
                        "certificate_number": "IHSA-WAH-2025-05567",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp02_marco_309a"),
                        "certification_type": "309a_electrician_license",
                        "issued_date": days_ago(365 * 8),
                        "expiry_date": None,
                        "issuing_body": "Ontario College of Trades (OCOT)",
                        "certificate_number": "OCOT-309A-2018-22134",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp02_marco_whmis"),
                        "certification_type": "whmis",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(530),
                        "issuing_body": "Ontario MOL Approved Provider",
                        "certificate_number": "WHMIS-ON-2025-6678",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build inspection data for GP02.

        Returns:
            List of inspection dicts.
        """
        uid = GP02_USER["uid"]
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
                "id": stable_id("insp", "gp02_framing1"),
                "inspection_type": "structural",
                "inspection_date": days_ago(10),
                "inspector_name": "Sarah Chen",
                "inspector_id": stable_id("wkr", "gp02_sarah"),
                "weather_conditions": "Clear, cool",
                "temperature": "12C",
                "workers_on_site": 3,
                "overall_status": "pass",
                "overall_notes": "Helical piles verified at specified depth "
                    "and torque. Beam connections match engineering drawings. "
                    "Joist hangers properly fastened. All fall protection "
                    "in place for ledger board work.",
                "items": "[]",
                "created_at": datetime_days_ago(10),
                "updated_at": datetime_days_ago(10),
            },
            {
                **base,
                "id": stable_id("insp", "gp02_progress1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(3),
                "inspector_name": "Sarah Chen",
                "inspector_id": stable_id("wkr", "gp02_sarah"),
                "weather_conditions": "Overcast, light rain earlier",
                "temperature": "9C",
                "workers_on_site": 2,
                "overall_status": "partial",
                "overall_notes": "Decking installation 70% complete. "
                    "One railing post anchor not flush with framing — "
                    "needs shimming before railing install. "
                    "Scrap lumber accumulating near lot line, needs cleanup.",
                "corrective_actions_needed": "Shim railing post anchor at "
                    "NE corner before railing installation. "
                    "Clear scrap lumber from lot line area by end of week.",
                "items": "[]",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build toolbox talk data for GP02.

        Returns:
            List of toolbox talk dicts.
        """
        uid = GP02_USER["uid"]
        return [{
            "id": stable_id("talk", "gp02_fall_prevention"),
            "topic": "Working at Heights — Deck Framing Safety",
            "scheduled_date": days_ago(14),
            "target_audience": "all_workers",
            "duration_minutes": 10,
            "status": "completed",
            "presented_at": datetime_days_ago(14, hour=7),
            "presented_by": "Sarah Chen",
            "overall_notes": "Reviewed OHSA requirements for fall protection "
                "above 3 metres. Discussed guardrail setup for beam work "
                "and proper ladder placement on uneven grade. "
                "All three crew members signed attendance.",
            "created_at": datetime_days_ago(14),
            "updated_at": datetime_days_ago(14),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }]

    # -----------------------------------------------------------------
    # Daily Logs
    # -----------------------------------------------------------------

    def _build_daily_logs(self) -> list[dict]:
        """Build daily log data for GP02.

        Returns:
            List of daily log dicts.
        """
        uid = GP02_USER["uid"]
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
                "id": stable_id("dlog", "gp02_d14"),
                "log_date": days_ago(14),
                "superintendent_name": "Sarah Chen",
                "status": "approved",
                "workers_on_site": 3,
                "work_performed": "Installed ledger board to house wall with "
                    "lag bolts per engineering spec. Set first 4 helical "
                    "piles with Techno Metal Post rig — all piles reached "
                    "target torque. Temporary bracing in place.",
                "notes": "Ontario One Call locate marks confirmed — no "
                    "conflicts with pile locations. Client satisfied "
                    "with layout staking.",
                "created_at": datetime_days_ago(14),
                "updated_at": datetime_days_ago(13),
                "submitted_at": datetime_days_ago(14, hour=17),
                "approved_at": datetime_days_ago(13, hour=8),
            },
            {
                **base,
                "id": stable_id("dlog", "gp02_d7"),
                "log_date": days_ago(7),
                "superintendent_name": "Sarah Chen",
                "status": "approved",
                "workers_on_site": 3,
                "work_performed": "Completed beam installation — double 2x10 "
                    "PT beam set on pile caps. Started joist layout "
                    "and installation (12 of 18 joists hung). "
                    "Blocking installed at beam bearing points.",
                "notes": "Composite decking material delivered and staged "
                    "in driveway. Aluminum railing kit on backorder — "
                    "supplier says 5 business days.",
                "created_at": datetime_days_ago(7),
                "updated_at": datetime_days_ago(6),
                "submitted_at": datetime_days_ago(7, hour=17),
                "approved_at": datetime_days_ago(6, hour=9),
            },
            {
                **base,
                "id": stable_id("dlog", "gp02_d1"),
                "log_date": days_ago(1),
                "superintendent_name": "Sarah Chen",
                "status": "submitted",
                "workers_on_site": 2,
                "work_performed": "Decking installation continued — 17 of 24 rows "
                    "complete. Hidden fastener system working well. "
                    "Marco (Rizzo Electric) on site for outlet rough-in — "
                    "ran conduit from panel through crawl space to "
                    "exterior box location.",
                "notes": "Railing kit still not arrived. Following up with "
                    "supplier tomorrow. May need to push final completion "
                    "by 2 days if railing delayed further.",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "submitted_at": datetime_days_ago(1, hour=17),
                "approved_at": None,
            },
        ]

    # -----------------------------------------------------------------
    # Deficiency List (punch list)
    # -----------------------------------------------------------------

    def _build_deficiency_list(self, dl_id: str) -> dict:
        """Build deficiency list header for GP02.

        Args:
            dl_id: Deficiency list ID.

        Returns:
            Deficiency list dict.
        """
        uid = GP02_USER["uid"]
        return {
            "id": dl_id,
            "name": "Deck Closeout Punch List",
            "status": "open",
            "total_items": 3,
            "open_items": 2,
            "closed_items": 1,
            "created_at": datetime_days_ago(3),
            "updated_at": datetime_days_ago(1),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }

    def _build_deficiency_items(self) -> list[dict]:
        """Build deficiency items for GP02.

        Returns:
            List of deficiency item dicts.
        """
        uid = GP02_USER["uid"]
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
                "id": stable_id("ditem", "gp02_shim"),
                "title": "Railing post anchor — NE corner shimming",
                "description": "Railing post anchor at NE corner is not flush "
                    "with joist framing. Needs composite shim before "
                    "railing post can be mounted plumb.",
                "severity": "minor",
                "status": "open",
                "assigned_to": "Dan Petrov",
                "due_date": days_from_now(3),
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
            {
                **base,
                "id": stable_id("ditem", "gp02_gap"),
                "title": "Decking gap at house wall transition",
                "description": "Gap between last decking board and flashing "
                    "at house wall is 18mm — spec calls for 10-12mm. "
                    "Need to rip final board or add filler strip.",
                "severity": "minor",
                "status": "open",
                "assigned_to": "Dan Petrov",
                "due_date": days_from_now(5),
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("ditem", "gp02_scrap"),
                "title": "Scrap lumber cleanup along lot line",
                "description": "Offcuts and scrap PT lumber piled near "
                    "north lot line. Client asked for cleanup before "
                    "weekend. Dispose at yard or arrange bin.",
                "severity": "minor",
                "status": "closed",
                "assigned_to": "Tyler Osei",
                "closed_at": datetime_days_ago(1),
                "due_date": days_ago(1),
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(1),
            },
        ]

    # -----------------------------------------------------------------
    # Work Items
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active deck build.

        Active project — items reflect the in-flight scope.
        All values in cents.
        """
        uid = GP02_USER["uid"]
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
                "id": stable_id("wi", "gp02_item_1"),
                "description": "Deck footings \u2014 8 concrete piers to frost line",
                "quantity": 8,
                "unit": "EA",
                "margin_pct": 20,
                "labour_total_cents": 78000,
                "items_total_cents": 36000,
                "sell_price_cents": 136800,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp02_lab_1"),
                        "task": "Excavate and pour footings",
                        "rate_cents": 6500,
                        "hours": 12,
                        "cost_cents": 78000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp02_item_1_mat_1"),
                        "description": "Concrete, rebar, sonotubes",
                        "quantity": 8,
                        "unit": "EA",
                        "unit_cost_cents": 4500,
                        "total_cents": 36000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp02_item_2"),
                "description": "PT lumber deck framing \u2014 16' x 20'",
                "quantity": 320,
                "unit": "SF",
                "margin_pct": 25,
                "labour_total_cents": 110000,
                "items_total_cents": 185000,
                "sell_price_cents": 368750,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp02_lab_2"),
                        "task": "Frame joists, beams, ledger",
                        "rate_cents": 5500,
                        "hours": 20,
                        "cost_cents": 110000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp02_item_2_mat_1"),
                        "description": "PT 2x10, 2x8, hangers, fasteners",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 185000,
                        "total_cents": 185000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp02_item_3"),
                "description": "Composite decking and railings",
                "quantity": 320,
                "unit": "SF",
                "margin_pct": 25,
                "labour_total_cents": 132000,
                "items_total_cents": 384000,
                "sell_price_cents": 645000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp02_lab_3"),
                        "task": "Install decking and rail system",
                        "rate_cents": 5500,
                        "hours": 24,
                        "cost_cents": 132000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp02_item_3_mat_1"),
                        "description": "TimberTech composite, aluminium rail",
                        "quantity": 320,
                        "unit": "SF",
                        "unit_cost_cents": 1200,
                        "total_cents": 384000,
                    },
                ],
            },
        ]
