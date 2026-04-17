"""GP01 — Solo Handyman, Kitchen Renovation (US — Florida).

The simplest golden project: one owner-operator, Starter tier,
minimal data. Validates onboarding flow, single-user daily log,
basic inspection, no subs.

Workers: 1 (owner does everything)
Equipment: Basic hand tools only (no heavy equipment)
Inspections: 2 (one passed, one in-progress)
Incidents: 0
Toolbox Talks: 1 (completed, self-delivered)
Daily Logs: 3 (one submitted, one draft, one approved)
"""

from backend.fixtures.golden.base import GoldenProjectSeeder
from backend.fixtures.golden.companies import GP01_COMPANY, GP01_USER
from backend.fixtures.golden.helpers import (
    days_ago,
    days_from_now,
    datetime_days_ago,
    now_iso,
    stable_id,
)


class GP01Seeder(GoldenProjectSeeder):
    """Seed GP01: Solo Handyman — Kitchen Reno."""

    GP_SLUG = "gp01"
    COMPANY_ID = "comp_gp01"
    PROJECT_ID = "proj_gp01"

    def seed(self) -> dict[str, int]:
        """Seed all GP01 data.

        Returns:
            Dict of entity type to count seeded.
        """
        counts: dict[str, int] = {}

        self.seed_company(GP01_COMPANY)
        self.seed_user(GP01_USER)

        self.seed_project({
            "id": self.PROJECT_ID,
            "name": "Martinez Kitchen Renovation",
            "address": "1524 Coconut Drive, Fort Myers, FL 33901",
            "client_name": "Elena Martinez",
            "project_type": "renovation",
            "trade_types": ["general"],
            "start_date": days_ago(21),
            "end_date": days_from_now(14),
            "estimated_workers": 1,
            "description": "Full kitchen renovation including cabinet replacement, "
                "countertop installation, backsplash tiling, and electrical "
                "updates for new appliances.",
            "special_hazards": "Electrical work near water supply lines. "
                "Asbestos testing required for older home (built 1978).",
            "nearest_hospital": "Lee Health - Lee Memorial Hospital, "
                "2776 Cleveland Ave, Fort Myers, FL 33901",
            "emergency_contact_name": "Elena Martinez",
            "emergency_contact_phone": "239-555-0298",
            "state": "active",
            "status": "normal",
            "compliance_score": 85,
            "company_id": self.COMPANY_ID,
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP01_USER["uid"],
            "actor_type": "human",
            "updated_by": GP01_USER["uid"],
            "updated_actor_type": "human",
            "agent_id": None,
            "model_id": None,
            "confidence": None,
        })

        # --- Workers (just the owner) ---
        mike_id = stable_id("wkr", "gp01_mike")
        workers = [{
            "id": mike_id,
            "first_name": "Mike",
            "last_name": "Torres",
            "email": "mike@mikeshandyman.com",
            "phone": "239-555-0147",
            "role": "superintendent",
            "trade": "general",
            "language_preference": "both",
            "hire_date": days_ago(365 * 5),
            "status": "active",
            "deleted": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": GP01_USER["uid"],
            "actor_type": "human",
            "updated_by": GP01_USER["uid"],
            "updated_actor_type": "human",
            "certifications": [
                {
                    "id": stable_id("cert", "gp01_mike_osha10"),
                    "certification_type": "osha_10",
                    "issued_date": days_ago(365 * 3),
                    "expiry_date": None,
                    "issuing_body": "OSHA Authorized Trainer",
                    "certificate_number": "OSHA10-FL-22-4478",
                    "status": "valid",
                },
                {
                    "id": stable_id("cert", "gp01_mike_first_aid"),
                    "certification_type": "first_aid_cpr",
                    "issued_date": days_ago(200),
                    "expiry_date": days_from_now(165),
                    "issuing_body": "American Red Cross",
                    "certificate_number": "ARC-CPR-2025-11234",
                    "status": "valid",
                },
                {
                    "id": stable_id("cert", "gp01_mike_electrical"),
                    "certification_type": "electrical_safety",
                    "issued_date": days_ago(400),
                    "expiry_date": days_ago(35),  # EXPIRED — problem state
                    "issuing_body": "NFPA",
                    "certificate_number": "NFPA-70E-2024-8821",
                    "status": "expired",
                },
            ],
        }]
        counts["workers"] = self.seed_workers(workers)
        self.assign_workers_to_project([mike_id])

        # --- Inspections ---
        inspections = [
            {
                "id": stable_id("insp", "gp01_daily1"),
                "inspection_type": "daily_site",
                "inspection_date": days_ago(5),
                "inspector_name": "Mike Torres",
                "inspector_id": mike_id,
                "weather_conditions": "Sunny, humid",
                "temperature": "88°F",
                "workers_on_site": 1,
                "overall_status": "pass",
                "overall_notes": "Site clean, all PPE in place. "
                    "Electrical panel locked out properly.",
                "items": "[]",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(5),
                "created_by": GP01_USER["uid"],
                "actor_type": "human",
                "updated_by": GP01_USER["uid"],
                "updated_actor_type": "human",
                "deleted": False,
            },
            {
                "id": stable_id("insp", "gp01_electrical1"),
                "inspection_type": "electrical",
                "inspection_date": days_ago(1),
                "inspector_name": "Mike Torres",
                "inspector_id": mike_id,
                "weather_conditions": "Overcast",
                "temperature": "82°F",
                "workers_on_site": 1,
                "overall_status": "partial",
                "overall_notes": "GFCI outlets installed correctly. "
                    "Need to verify grounding on new circuit before closing wall.",
                "corrective_actions_needed": "Complete grounding verification "
                    "on kitchen island circuit before drywall.",
                "items": "[]",
                "created_at": datetime_days_ago(1),
                "updated_at": datetime_days_ago(1),
                "created_by": GP01_USER["uid"],
                "actor_type": "human",
                "updated_by": GP01_USER["uid"],
                "updated_actor_type": "human",
                "deleted": False,
            },
        ]
        counts["inspections"] = self.seed_inspections(inspections)

        # --- Toolbox Talk (self-delivered) ---
        talks = [{
            "id": stable_id("talk", "gp01_electrical_safety"),
            "topic": "Electrical Safety in Wet Environments",
            "scheduled_date": days_ago(7),
            "target_audience": "all_workers",
            "duration_minutes": 10,
            "status": "completed",
            "presented_at": datetime_days_ago(7),
            "presented_by": "Mike Torres",
            "overall_notes": "Reviewed GFCI requirements for kitchen renovations. "
                "Lockout/tagout refresher.",
            "created_at": datetime_days_ago(7),
            "updated_at": datetime_days_ago(7),
            "created_by": GP01_USER["uid"],
            "actor_type": "human",
            "updated_by": GP01_USER["uid"],
            "updated_actor_type": "human",
            "deleted": False,
        }]
        counts["toolbox_talks"] = self.seed_toolbox_talks(talks)

        # --- Daily Logs ---
        logs = [
            {
                "id": stable_id("dlog", "gp01_day1"),
                "log_date": days_ago(5),
                "superintendent_name": "Mike Torres",
                "status": "approved",
                "workers_on_site": 1,
                "work_performed": "Completed demo of existing cabinets and countertops. "
                    "Removed old backsplash tile. Inspected plumbing connections — "
                    "all in good condition, no replacement needed.",
                "notes": "Client approved keeping existing plumbing layout.",
                "created_at": datetime_days_ago(5),
                "updated_at": datetime_days_ago(4),
                "created_by": GP01_USER["uid"],
                "actor_type": "human",
                "updated_by": GP01_USER["uid"],
                "updated_actor_type": "human",
                "submitted_at": datetime_days_ago(5, hour=17),
                "approved_at": datetime_days_ago(4, hour=9),
                "deleted": False,
            },
            {
                "id": stable_id("dlog", "gp01_day2"),
                "log_date": days_ago(3),
                "superintendent_name": "Mike Torres",
                "status": "submitted",
                "workers_on_site": 1,
                "work_performed": "Installed new base cabinets (6 of 8). "
                    "Leveled and shimmed. Ran electrical rough-in for "
                    "under-cabinet lighting.",
                "notes": "Waiting on 2 corner cabinets — supplier delayed to Friday.",
                "created_at": datetime_days_ago(3),
                "updated_at": datetime_days_ago(3),
                "created_by": GP01_USER["uid"],
                "actor_type": "human",
                "updated_by": GP01_USER["uid"],
                "updated_actor_type": "human",
                "submitted_at": datetime_days_ago(3, hour=17),
                "approved_at": None,
                "deleted": False,
            },
            {
                "id": stable_id("dlog", "gp01_today"),
                "log_date": days_ago(0),
                "superintendent_name": "Mike Torres",
                "status": "draft",
                "workers_on_site": 1,
                "work_performed": "",
                "notes": "",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "created_by": GP01_USER["uid"],
                "actor_type": "human",
                "updated_by": GP01_USER["uid"],
                "updated_actor_type": "human",
                "submitted_at": None,
                "approved_at": None,
                "deleted": False,
            },
        ]
        counts["daily_logs"] = self.seed_daily_logs(logs)

        counts["incidents"] = 0
        counts["equipment"] = 0
        counts["hazard_reports"] = 0

        # --- Work Items ---
        counts["work_items"] = self.seed_work_items(self._build_work_items())

        return counts

    # -----------------------------------------------------------------
    # Work Items
    # -----------------------------------------------------------------

    def _build_work_items(self) -> list[dict]:
        """Build work items for the active kitchen renovation.

        Active project — items reflect the in-flight scope.
        """
        uid = GP01_USER["uid"]
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
                "id": stable_id("wi", "gp01_item_1"),
                "description": "Kitchen demolition \u2014 strip out existing cabinets, counters, appliances",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 20,
                "labour_total_cents": 60000,
                "items_total_cents": 45000,
                "sell_price_cents": 126000,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp01_lab_1"),
                        "task": "Demo and haul away",
                        "rate_cents": 7500,
                        "hours": 8,
                        "cost_cents": 60000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp01_item_1_mat_1"),
                        "description": "Dumpster and disposal fees",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 45000,
                        "total_cents": 45000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp01_item_2"),
                "description": "Cabinet installation \u2014 12 upper, 14 lower shaker-style",
                "quantity": 26,
                "unit": "EA",
                "margin_pct": 25,
                "labour_total_cents": 240000,
                "items_total_cents": 481000,
                "sell_price_cents": 901250,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp01_lab_2"),
                        "task": "Cabinet install and trim",
                        "rate_cents": 7500,
                        "hours": 32,
                        "cost_cents": 240000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp01_item_2_mat_1"),
                        "description": "Shaker cabinets (stock)",
                        "quantity": 26,
                        "unit": "EA",
                        "unit_cost_cents": 18500,
                        "total_cents": 481000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp01_item_3"),
                "description": "Quartz countertop \u2014 42 LF including island",
                "quantity": 42,
                "unit": "LF",
                "margin_pct": 22,
                "labour_total_cents": 75000,
                "items_total_cents": 357000,
                "sell_price_cents": 527040,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp01_lab_3"),
                        "task": "Template, install, seal",
                        "rate_cents": 7500,
                        "hours": 10,
                        "cost_cents": 75000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp01_item_3_mat_1"),
                        "description": "Quartz slab Cat A",
                        "quantity": 42,
                        "unit": "LF",
                        "unit_cost_cents": 8500,
                        "total_cents": 357000,
                    },
                ],
            },
            {
                **base,
                "id": stable_id("wi", "gp01_item_4"),
                "description": "Electrical \u2014 recircuit for new appliances, GFCI, under-cabinet lighting",
                "quantity": 1,
                "unit": "LS",
                "margin_pct": 25,
                "labour_total_cents": 119000,
                "items_total_cents": 42000,
                "sell_price_cents": 201250,
                "labour": [
                    {
                        **lab_base,
                        "id": stable_id("lab", "gp01_lab_4"),
                        "task": "Rough and trim electrical",
                        "rate_cents": 8500,
                        "hours": 14,
                        "cost_cents": 119000,
                    },
                ],
                "items": [
                    {
                        **lab_base,
                        "id": stable_id("item", "gp01_item_4_mat_1"),
                        "description": "Wire, devices, fixtures",
                        "quantity": 1,
                        "unit": "LS",
                        "unit_cost_cents": 42000,
                        "total_cents": 42000,
                    },
                ],
            },
        ]
