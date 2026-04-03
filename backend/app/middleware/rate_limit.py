"""Rate limiting configuration for SafetyForge API."""

import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_user_or_ip(request: Request) -> str:
    """Extract user UID from auth header, fall back to IP.

    Uses a hash of the Bearer token as the rate-limit key so that
    authenticated users get per-user limits while anonymous callers
    are limited by IP address.

    Args:
        request: The incoming Starlette/FastAPI request.

    Returns:
        A string key identifying the caller for rate-limiting purposes.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 20:
        return hashlib.sha256(auth[7:].encode()).hexdigest()[:16]
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_or_ip, default_limits=["100/minute"])
