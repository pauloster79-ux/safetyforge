"""Golden project seed data for simulation testing.

Ten realistic construction project scenarios across 4 jurisdictions,
varying company sizes (solo to 45+ workers), project types, and
lifecycle stages. Each golden project seeds a full tenant with
workers, certifications, inspections, incidents, daily logs,
equipment, toolbox talks, and hazard reports.

All operations use MERGE for idempotency — safe to run multiple times.
Every node carries ``source: 'golden_project'`` for easy cleanup.
Date fields use relative offsets from today so data stays fresh.

Usage:
    python -m backend.fixtures.golden.seed_all
    python -m backend.fixtures.golden.seed_all --uri bolt://localhost:7687
"""

from backend.fixtures.golden.helpers import days_ago, days_from_now, generate_id

__all__ = ["days_ago", "days_from_now", "generate_id"]
