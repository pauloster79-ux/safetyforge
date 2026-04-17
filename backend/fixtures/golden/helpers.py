"""Shared helpers for golden project seed scripts.

Provides ID generation, date offset helpers, and common Neo4j
MERGE patterns used across all golden project seeders.
"""

import secrets
from datetime import date, datetime, timedelta, timezone


def generate_id(prefix: str) -> str:
    """Generate a deterministic-length ID with a prefix.

    Args:
        prefix: Short prefix like 'wkr', 'insp', 'inc'.

    Returns:
        ID string like 'wkr_a1b2c3d4e5f6g7h8'.
    """
    return f"{prefix}_{secrets.token_hex(8)}"


def stable_id(prefix: str, slug: str) -> str:
    """Generate a stable, repeatable ID from a prefix and slug.

    Used for golden project entities so IDs are consistent across
    re-runs (MERGE can match on them).

    Args:
        prefix: Short prefix like 'comp', 'proj', 'wkr'.
        slug: A human-readable slug like 'gp01' or 'gp04_mike'.

    Returns:
        ID string like 'comp_gp01'.
    """
    return f"{prefix}_{slug}"


def today() -> date:
    """Return today's date in UTC."""
    return datetime.now(timezone.utc).date()


def now_iso() -> str:
    """Return current UTC datetime as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def days_ago(n: int) -> str:
    """Return a date N days in the past as ISO string.

    Args:
        n: Number of days ago.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return (today() - timedelta(days=n)).isoformat()


def days_from_now(n: int) -> str:
    """Return a date N days in the future as ISO string.

    Args:
        n: Number of days from now.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return (today() + timedelta(days=n)).isoformat()


def datetime_days_ago(n: int, hour: int = 9) -> str:
    """Return a datetime N days in the past as ISO string.

    Args:
        n: Number of days ago.
        hour: Hour of day (24h format).

    Returns:
        Datetime string in ISO 8601 format.
    """
    dt = datetime.now(timezone.utc).replace(
        hour=hour, minute=0, second=0, microsecond=0,
    ) - timedelta(days=n)
    return dt.isoformat()


GOLDEN_SOURCE = "golden_project"
"""Source tag applied to all golden project nodes."""
