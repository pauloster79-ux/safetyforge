"""Clerk JWT verification service.

Replaces Firebase Auth token verification with Clerk JWTs.
Uses PyJWT with JWKS for RS256 token verification.
"""

import logging
from functools import lru_cache

import httpx
import jwt
from jwt import PyJWKClient

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_jwk_client: PyJWKClient | None = None


def _get_jwk_client(settings: Settings) -> PyJWKClient:
    """Return a cached JWKS client for Clerk token verification.

    Args:
        settings: Application settings containing Clerk JWKS URL.

    Returns:
        A PyJWKClient configured for Clerk's JWKS endpoint.
    """
    global _jwk_client
    if _jwk_client is None:
        jwks_url = settings.clerk_jwks_url
        if not jwks_url and settings.clerk_jwt_issuer:
            # Derive JWKS URL from issuer (standard Clerk pattern)
            jwks_url = f"{settings.clerk_jwt_issuer.rstrip('/')}/.well-known/jwks.json"
        if not jwks_url:
            raise ValueError(
                "CLERK_JWKS_URL or CLERK_JWT_ISSUER must be set for JWT verification"
            )
        _jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
        logger.info("JWKS client created for %s", jwks_url)
    return _jwk_client


class ClerkAuthError(Exception):
    """Raised when Clerk JWT verification fails."""

    def __init__(self, message: str = "Invalid or expired authentication token") -> None:
        super().__init__(message)


class ClerkTokenExpiredError(ClerkAuthError):
    """Raised when the Clerk JWT has expired."""

    def __init__(self) -> None:
        super().__init__("Authentication token has expired")


def verify_clerk_token(token: str, settings: Settings | None = None) -> dict:
    """Verify a Clerk JWT and return decoded claims.

    Validates the token signature against Clerk's JWKS endpoint,
    checks expiration, and returns the decoded payload.

    Args:
        token: The raw JWT string (without 'Bearer ' prefix).
        settings: Application settings. Uses default if not provided.

    Returns:
        A dict with user claims:
            - uid: The Clerk user ID (sub claim)
            - email: User's primary email (if present)
            - email_verified: Whether the email is verified

    Raises:
        ClerkTokenExpiredError: If the token has expired.
        ClerkAuthError: If the token is invalid for any other reason.
    """
    if settings is None:
        settings = get_settings()

    try:
        jwk_client = _get_jwk_client(settings)
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        decode_options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": False,  # Clerk JWTs may not always have aud
        }

        # Build issuer for verification if configured
        issuer = settings.clerk_jwt_issuer or None

        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options=decode_options,
        )

        return {
            "uid": decoded.get("sub", ""),
            "email": decoded.get("email", decoded.get("primary_email", "")),
            "email_verified": decoded.get("email_verified", False),
            "metadata": decoded.get("public_metadata", {}),
        }

    except jwt.ExpiredSignatureError:
        raise ClerkTokenExpiredError()
    except jwt.InvalidTokenError as exc:
        logger.warning("Clerk token verification failed: %s", exc)
        raise ClerkAuthError(f"Invalid authentication token: {exc}")
    except Exception as exc:
        logger.error("Unexpected error verifying Clerk token: %s", exc)
        raise ClerkAuthError("Could not verify authentication token")


def reset_jwk_client() -> None:
    """Reset the cached JWKS client. Useful for testing."""
    global _jwk_client
    _jwk_client = None
