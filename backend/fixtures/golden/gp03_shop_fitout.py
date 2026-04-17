"""GP03 — Shop Fitout, Retail (UK — England).

Medium-complexity golden project: 5 workers + 1 glazing sub,
CDM 2015 regulations, CSCS cards required, quality punch list,
single RFI to architect.

Exercises:
- Workers with UK certifications (CSCS, SMSTS, SSSTS, ECS)
- CDM 2015 compliance
- 3 inspections (pass, partial, pass)
- 1 toolbox talk (completed)
- 2 daily logs
- Deficiency list with 3 items (1 corrected, 2 open)
- 1 RFI to architect
- No incidents
- Project about 60% complete
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP03_COMPANY, GP03_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP03Seeder(GoldenProjectSeeder):
    """Seed GP03: Retail Shop Fitout — London."""

    GP_SLUG = "gp03"
    COMPANY_ID = "comp_gp03"
    PROJECT_ID = "proj_gp03"

    def seed(self) -> dict[str, int]:
        """Seed all GP03 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP03_COMPANY)
        self.seed_user(GP03_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Mercer & Lane — Shoreditch Flagship",
            "address": "78 Redchurch Street, London E2 7DP",
            "client_name": "Mercer & Lane Retail Ltd",
            "project_type": "fitout",
            "trade_types": ["general", "electrical", "painting", "glazing"],
            "start_date": days_ago(35),
            "end_date": days_from_now(25),
            "estimated_workers": 6,
            "description": "Full retail fitout of 180 sqm ground floor unit "
                "for fashion retailer. Scope includes partition walls, "
                "bespoke timber display fixtures, feature lighting, "
                "painting and decorating, new shopfront glazing, and "
                "fitting room construction. Building is Grade II "
                "adjacent — no structural alterations.",
            "special_hazards": "Shared building access with operating "
                "restaurant on upper floor — coordinate deliveries "
                "via rear lane only. Existing asbestos survey on file "
                "(no ACMs found in fitout zone). Manual handling of "
                "large glass panels for shopfront.",
            "nearest_hospital": "Royal London Hospital, "
                "Whitechapel Road, London E1 1FR",
            "emergency_contact_name": "James Okafor",
            "emergency_contact_phone": "+44-20-7946-0321",
            "state": "active",
            "status": "normal",
            "compliance_score": 88,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP03_USER["uid"],
            "actor_type": "human",
            "updated_by": GP03_USER["uid"],
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
        dl_id = stable_id("dlist", "gp03_quality")
        self.seed_deficiency_lists([self._build_deficiency_list(dl_id)])
        items = self._build_deficiency_items()
        counts["deficiency_items"] = self.seed_deficiency_items(items, dl_id)
        counts["deficiency_lists"] = 1

        # --- RFI ---
        counts["rfis"] = self.seed_rfis(self._build_rfis())

        # --- Work Items ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        counts["incidents"] = 0
        counts["equipment"] = 0
        counts["hazard_reports"] = 0

        return counts

    # -----------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------

    def _build_workers(self) -> list[dict]:
        """Build worker data for GP03.

        Returns:
            List of worker dicts.
        """
        uid = GP03_USER["uid"]
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
            # --- James Okafor (superintendent / principal contractor) ---
            {
                **base,
                "id": stable_id("wkr", "gp03_james"),
                "first_name": "James",
                "last_name": "Okafor",
                "email": "james@brightstone.co.uk",
                "phone": "+44-20-7946-0321",
                "role": "superintendent",
                "trade": "general",
                "language_preference": "en",
                "hire_date": days_ago(365 * 7),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_james_smsts"),
                        "certification_type": "smsts",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CITB",
                        "certificate_number": "CITB-SMSTS-2024-44218",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_james_cscs_black"),
                        "certification_type": "cscs_black",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLK-2024-09912",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_james_firstaid"),
                        "certification_type": "first_aid_at_work",
                        "issued_date": days_ago(200),
                        "expiry_date": days_from_now(895),
                        "issuing_body": "St John Ambulance",
                        "certificate_number": "SJA-FAW-2025-33012",
                        "status": "valid",
                    },
                ],
            },
            # --- Ayo Adeyemi (carpenter — display fixtures) ---
            {
                **base,
                "id": stable_id("wkr", "gp03_ayo"),
                "first_name": "Ayo",
                "last_name": "Adeyemi",
                "email": "ayo@brightstone.co.uk",
                "phone": "+44-7700-900112",
                "role": "carpenter",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365 * 4),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_ayo_sssts"),
                        "certification_type": "sssts",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CITB",
                        "certificate_number": "CITB-SSSTS-2025-11345",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_ayo_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-2025-07789",
                        "status": "valid",
                    },
                ],
            },
            # --- Matt Kelly (carpenter — partitions and fitting rooms) ---
            {
                **base,
                "id": stable_id("wkr", "gp03_matt"),
                "first_name": "Matt",
                "last_name": "Kelly",
                "email": "matt@brightstone.co.uk",
                "phone": "+44-7700-900234",
                "role": "carpenter",
                "trade": "carpentry",
                "language_preference": "en",
                "hire_date": days_ago(365 * 2),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_matt_sssts"),
                        "certification_type": "sssts",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CITB",
                        "certificate_number": "CITB-SSSTS-2024-08823",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_matt_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-2024-05512",
                        "status": "valid",
                    },
                ],
            },
            # --- Priya Sharma (painter / decorator) ---
            {
                **base,
                "id": stable_id("wkr", "gp03_priya"),
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "",
                "phone": "+44-7700-900356",
                "role": "painter",
                "trade": "painting",
                "language_preference": "en",
                "hire_date": days_ago(365),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_priya_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-2025-11890",
                        "status": "valid",
                    },
                ],
            },
            # --- Craig Rowlands (electrician — feature lighting) ---
            {
                **base,
                "id": stable_id("wkr", "gp03_craig"),
                "first_name": "Craig",
                "last_name": "Rowlands",
                "email": "craig@brightstone.co.uk",
                "phone": "+44-7700-900478",
                "role": "electrician",
                "trade": "electrical",
                "language_preference": "en",
                "hire_date": days_ago(365 * 5),
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_craig_ecs"),
                        "certification_type": "ecs_gold",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365),
                        "issuing_body": "JIB / ECS",
                        "certificate_number": "ECS-GLD-2024-34421",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_craig_18th"),
                        "certification_type": "bs7671_18th_edition",
                        "issued_date": days_ago(365),
                        "expiry_date": days_from_now(365 * 4),
                        "issuing_body": "City & Guilds",
                        "certificate_number": "CG-2382-18-2025-8891",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_craig_cscs_blue"),
                        "certification_type": "cscs_blue",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-BLU-2024-22145",
                        "status": "valid",
                    },
                ],
            },
            # --- Sub: Clearview Glazing — shopfront glass ---
            {
                **base,
                "id": stable_id("wkr", "gp03_derek_glaz"),
                "first_name": "Derek",
                "last_name": "Thompson",
                "email": "derek@clearviewglazing.co.uk",
                "phone": "+44-7700-900590",
                "role": "foreman",
                "trade": "glazing",
                "language_preference": "en",
                "hire_date": days_ago(365 * 9),
                "notes": "Sub: Clearview Glazing Ltd — shopfront installation",
                "certifications": [
                    {
                        "id": stable_id("cert", "gp03_derek_sssts"),
                        "certification_type": "sssts",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CITB",
                        "certificate_number": "CITB-SSSTS-2024-14432",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_derek_cscs_gold"),
                        "certification_type": "cscs_gold",
                        "issued_date": days_ago(365 * 2),
                        "expiry_date": days_from_now(365 * 3),
                        "issuing_body": "CSCS",
                        "certificate_number": "CSCS-GLD-2024-06678",
                        "status": "valid",
                    },
                    {
                        "id": stable_id("cert", "gp03_derek_manual"),
                        "certification_type": "manual_handling",
                        "issued_date": days_ago(300),
                        "expiry_date": days_from_now(430),
                        "issuing_body": "CITB",
                        "certificate_number": "CITB-MH-2025-02245",
                        "status": "valid",
                    },
                ],
            },
        ]

    # -----------------------------------------------------------------
    # Inspections
    # -----------------------------------------------------------------

    def _build_inspections(self) -> list[dict]:
        """Build inspection data for GP03.

        Returns:
            List of inspection dicts.
        """
        uid = GP03_USER["uid"]
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
                "id": stable_id("insp", "gp03_site_setup"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(14),
                "inspector_name": "James Okafor",
                "inspector_id": stable_id("wkr", "gp03_james"),
                "weather_conditions": "Overcast",
                "temperature": "11C",
                "workers_on_site": 4,
                "overall_status": "pass",
                "overall_notes": "Site welfare facilities in place — "
                    "portaloo, drying room, first aid kit checked. "
                    "CDM file on site. Deliveries routed via rear lane "
                    "as per logistics plan. All CSCS cards verified.",
                "items": "[]",
                "created_at": datetime_days_ago(14),
                "updated_at": datetime_days_ago(14),
            },
            {
                **base,
                "id": stable_id("insp", "gp03_electrical1"),
                "inspection_type": "electrical",
                "inspection_date": days_ago(5),
                "inspector_name": "James Okafor",
                "inspector_id": stable_id("wkr", "gp03_james"),
                "weather_conditions": "N/A (internal)",
                "temperature": "18C",
                "workers_on_site": 5,
                "overall_status": "partial",
                "overall_notes": "First fix wiring 90% complete. "
                    "Feature lighting track positions marked on ceiling "
                    "but one run conflicts with sprinkler pipe — "
                    "needs re-routing. Consumer unit location approved "
                    "by client.",
                "corrective_actions_needed": "Re-route lighting track "
                    "run 3 to clear sprinkler drop at gridline C4. "
                    "Craig to confirm revised route with architect "
                    "before second fix.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("insp", "gp03_daily_d2"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(2),
                "inspector_name": "James Okafor",
                "inspector_id": stable_id("wkr", "gp03_james"),
                "weather_conditions": "Clear",
                "temperature": "14C",
                "workers_on_site": 5,
                "overall_status": "pass",
                "overall_notes": "Partition walls complete to full height. "
                    "First coat of paint applied to fitting room area. "
                    "Glazing sub confirmed for next week. "
                    "All PPE compliance good — dust masks used "
                    "during sanding.",
                "items": "[]",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
            },
        ]

    # -----------------------------------------------------------------
    # Toolbox Talks
    # -----------------------------------------------------------------

    def _build_talks(self) -> list[dict]:
        """Build toolbox talk data for GP03.

        Returns:
            List of toolbox talk dicts.
        """
        uid = GP03_USER["uid"]
        return [{
            "id": stable_id("talk", "gp03_manual_handling"),
            "topic": "Manual Handling — Large Glass Panel Delivery",
            "scheduled_date": days_ago(7),
            "target_audience": "all_workers",
            "duration_minutes": 15,
            "status": "completed",
            "presented_at": datetime_days_ago(7, hour=8),
            "presented_by": "James Okafor",
            "overall_notes": "Briefed team on safe handling procedures "
                "for shopfront glass panels arriving next week. "
                "Reviewed two-person lift protocol, suction cup "
                "usage, and PPE requirements (cut-resistant gloves, "
                "safety boots). Discussed access route through "
                "rear lane and temporary hoardings.",
            "created_at": datetime_days_ago(7),
            "updated_at": datetime_days_ago(7),
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
        """Build daily log data for GP03.

        Returns:
            List of daily log dicts.
        """
        uid = GP03_USER["uid"]
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
                "id": stable_id("dlog", "gp03_d5"),
                "log_date": days_ago(5),
                "superintendent_name": "James Okafor",
                "status": "approved",
                "workers_on_site": 5,
                "work_performed": "Ayo and Matt completed partition framing "
                    "for fitting rooms 1-3. Craig running first fix "
                    "wiring for feature lighting — identified clash with "
                    "sprinkler at gridline C4. Priya prepping walls in "
                    "main sales area — filling and sanding.",
                "notes": "RFI raised to architect re: shopfront glazing "
                    "spec — need to confirm U-value and tint for "
                    "planning compliance. Waiting on response.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=9),
            },
            {
                **base,
                "id": stable_id("dlog", "gp03_d2"),
                "log_date": days_ago(2),
                "superintendent_name": "James Okafor",
                "status": "submitted",
                "workers_on_site": 5,
                "work_performed": "Partition walls completed to full height "
                    "with plasterboard. Fire stopping installed at "
                    "service penetrations. First coat emulsion applied "
                    "to fitting room walls. Craig began second fix "
                    "prep — back boxes for switches and sockets "
                    "installed throughout.",
                "notes": "Architect responded to RFI — confirmed double "
                    "glazed low-E spec for shopfront. Passed info to "
                    "Clearview Glazing for fabrication. Glazing install "
                    "booked for next Wednesday.",
                "created_at": datetime_days_ago(2),
                "updated_at": datetime_days_ago(2),
                "submitted_at": datetime_days_ago(2, hour=17),
                "approved_at": None,
            },
        ]

    # -----------------------------------------------------------------
    # Deficiency List (punch list)
    # -----------------------------------------------------------------

    def _build_deficiency_list(self, dl_id: str) -> dict:
        """Build deficiency list header for GP03.

        Args:
            dl_id: Deficiency list ID.

        Returns:
            Deficiency list dict.
        """
        uid = GP03_USER["uid"]
        return {
            "id": dl_id,
            "name": "Fitout Quality Snagging List",
            "status": "open",
            "total_items": 3,
            "open_items": 2,
            "closed_items": 1,
            "created_at": datetime_days_ago(5),
            "updated_at": datetime_days_ago(2),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }

    def _build_deficiency_items(self) -> list[dict]:
        """Build deficiency items for GP03.

        Returns:
            List of deficiency item dicts.
        """
        uid = GP03_USER["uid"]
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
                "id": stable_id("ditem", "gp03_plaster"),
                "title": "Plasterboard joint visible — fitting room 2",
                "description": "Taped plasterboard joint on east wall of "
                    "fitting room 2 showing through first coat. "
                    "Needs re-taping and additional skim coat before "
                    "final paint.",
                "severity": "minor",
                "status": "closed",
                "assigned_to": "Priya Sharma",
                "closed_at": datetime_days_ago(2),
                "due_date": days_ago(2),
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(2),
            },
            {
                **base,
                "id": stable_id("ditem", "gp03_track"),
                "title": "Lighting track route clash with sprinkler",
                "description": "Feature lighting track run 3 conflicts "
                    "with sprinkler drop at gridline C4. Track must "
                    "be re-routed 150mm east per architect instruction. "
                    "Second fix cannot proceed on this run until resolved.",
                "severity": "major",
                "status": "open",
                "assigned_to": "Craig Rowlands",
                "due_date": days_from_now(5),
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
            },
            {
                **base,
                "id": stable_id("ditem", "gp03_trim"),
                "title": "Shadow gap trim — display wall alignment",
                "description": "Shadow gap timber trim on main display wall "
                    "has 3mm step at joint between panels 4 and 5. "
                    "Client noted during walkthrough. Needs planing "
                    "or replacing the trim section for flush finish.",
                "severity": "minor",
                "status": "open",
                "assigned_to": "Ayo Adeyemi",
                "due_date": days_from_now(7),
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
            },
        ]

    # -----------------------------------------------------------------
    # RFIs
    # -----------------------------------------------------------------

    def _build_rfis(self) -> list[dict]:
        """Build RFI data for GP03.

        Returns:
            List of RFI dicts.
        """
        uid = GP03_USER["uid"]
        return [{
            "id": stable_id("rfi", "gp03_glazing_spec"),
            "rfi_number": "RFI-001",
            "subject": "Shopfront Glazing Specification Clarification",
            "description": "Tender documents specify double-glazed units "
                "for shopfront but do not state required U-value or "
                "whether low-E coating is needed to meet Part L "
                "requirements. Clearview Glazing need confirmed spec "
                "before fabrication can begin. Please advise U-value "
                "target and whether solar control tint is required "
                "per planning condition 14.",
            "status": "answered",
            "priority": "high",
            "submitted_by": "James Okafor",
            "submitted_to": "Helen Park — Park & Associates Architects",
            "submitted_date": days_ago(5),
            "response": "Confirmed: double-glazed low-E units, U-value "
                "1.2 W/m2K maximum. No solar control tint required — "
                "planning condition 14 relates to signage only, not "
                "glass specification. Refer to updated detail drawing "
                "SK-42 Rev C issued today.",
            "responded_by": "Helen Park",
            "responded_date": days_ago(3),
            "created_at": datetime_days_ago(5),
            "updated_at": datetime_days_ago(3),
            "created_by": uid,
            "actor_type": "human",
            "updated_by": uid,
            "updated_actor_type": "human",
            "deleted": False,
        }]

    # -----------------------------------------------------------------
    # Work Items (quote / scope of works)
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active Shoreditch shop fitout.

        Active project — items reflect the in-flight scope.
        All monetary values in pence (cents equivalent).
        """
        uid = GP03_USER["uid"]
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
                "id": stable_id("wi", "gp03_item_1"),
                "description": "Partition walls and ceilings \u2014 180 sqm fitout shell",
                "quantity": 180,
                "unit": "SM",
                "margin_pct": 18,
                "labour_total_cents": 216000,
                "items_total_cents": 285000,
                "sell_price_cents": 591180,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp03_lab_1"),
                        "task": "Frame and board partitions",
                        "rate_cents": 4500,
                        "hours": 48,
                        "cost_cents": 216000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp03_item_1_mat_1"),
                        "description": "Metal studs, plasterboard, insulation",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 285000,
                        "total_cents": 285000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp03_item_2"),
                "description": "Feature lighting \u2014 display and ambient LED throughout",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 22,
                "labour_total_cents": 176000,
                "items_total_cents": 625000,
                "sell_price_cents": 977220,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp03_lab_2"),
                        "task": "Install fixtures and controls",
                        "rate_cents": 5500,
                        "hours": 32,
                        "cost_cents": 176000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp03_item_2_mat_1"),
                        "description": "LED fixtures, drivers, control system",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 625000,
                        "total_cents": 625000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp03_item_3"),
                "description": "Bespoke timber display fixtures \u2014 8 units",
                "quantity": 8,
                "unit": "EA",
                "margin_pct": 25,
                "labour_total_cents": 260000,
                "items_total_cents": 2280000,
                "sell_price_cents": 3175000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp03_lab_3"),
                        "task": "Assemble and install bespoke joinery",
                        "rate_cents": 6500,
                        "hours": 40,
                        "cost_cents": 260000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp03_item_3_mat_1"),
                        "description": "Fabricated timber units from mill",
                        "quantity": 8,
                        "unit": "EA",
                        "unit_cost_cents": 285000,
                        "total_cents": 2280000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp03_item_4"),
                "description": "Shopfront glazing \u2014 4.2m storefront with door",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 20,
                "labour_total_cents": 120000,
                "items_total_cents": 485000,
                "sell_price_cents": 726000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp03_lab_4"),
                        "task": "Install shopfront system",
                        "rate_cents": 7500,
                        "hours": 16,
                        "cost_cents": 120000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp03_item_4_mat_1"),
                        "description": "Aluminium frame, tempered glass, door",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 485000,
                        "total_cents": 485000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp03_item_5"),
                "description": "Paint and decoration \u2014 walls, ceilings, fixtures",
                "quantity": 180,
                "unit": "SM",
                "margin_pct": 22,
                "labour_total_cents": 136800,
                "items_total_cents": 85000,
                "sell_price_cents": 270596,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp03_lab_5"),
                        "task": "Prep, prime, finish coats",
                        "rate_cents": 3800,
                        "hours": 36,
                        "cost_cents": 136800,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp03_item_5_mat_1"),
                        "description": "Paint, primer, sundries",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 85000,
                        "total_cents": 85000,
                    },
                ],
            },
        ]

