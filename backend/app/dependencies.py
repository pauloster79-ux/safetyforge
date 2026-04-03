"""FastAPI dependency injection providers."""

import logging
from typing import Annotated

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth, credentials
from google.cloud import firestore

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_firestore_client: firestore.Client | None = None
_firebase_initialized: bool = False


def _init_firebase(settings: Settings) -> None:
    """Initialize Firebase Admin SDK if not already initialized."""
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(
            credentials.ApplicationDefault(),
            {"projectId": settings.google_cloud_project},
        )
    _firebase_initialized = True


def get_firestore_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> firestore.Client:
    """Return a singleton Firestore client instance.

    Args:
        settings: Application settings with project configuration.

    Returns:
        A Firestore client connected to the configured project.
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=settings.google_cloud_project)
    return _firestore_client


async def get_current_user(
    authorization: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Verify Firebase ID token and return user information.

    Extracts the Bearer token from the Authorization header, verifies it
    against Firebase Auth, and returns the decoded user claims.

    Args:
        authorization: The Authorization header value (Bearer <token>).
        settings: Application settings for Firebase initialization.

    Returns:
        A dict containing uid, email, and email_verified from the token.

    Raises:
        HTTPException: 401 if the token is missing, malformed, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[7:]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing from Authorization header",
        )

    _init_firebase(settings)

    try:
        decoded_token = auth.verify_id_token(token)
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
        )
    except Exception as exc:
        logger.error("Unexpected error verifying Firebase token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify authentication token",
        )

    return {
        "uid": decoded_token["uid"],
        "email": decoded_token.get("email", ""),
        "email_verified": decoded_token.get("email_verified", False),
    }
