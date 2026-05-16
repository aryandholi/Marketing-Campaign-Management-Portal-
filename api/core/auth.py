"""
Mock JWT authentication middleware and utilities.

Provides token creation, validation, and a FastAPI dependency
(`get_current_user`) that protects routes behind JWT auth.

NOTE: This is a mocked implementation for POC purposes.
In production, integrate with Supabase Auth or an IdP like Auth0.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
security_scheme = HTTPBearer()

# ── Mock User Store ───────────────────────────────────────────────────────
# In production, this would query the `users` table via SQLAlchemy.
MOCK_USERS = {
    "admin@campaignportal.io": {
        "id": "usr_01HQXK3M7N8P9R0S1T2U3V4W5X",
        "email": "admin@campaignportal.io",
        "full_name": "Portal Administrator",
        "role": "admin",
        "password_hash": "mocked-bcrypt-hash",  # Accept any password in POC
    },
    "marketer@campaignportal.io": {
        "id": "usr_06YABCDE7F8G9H0I1J2K3L4M5N",
        "email": "marketer@campaignportal.io",
        "full_name": "Jane Marketer",
        "role": "marketer",
        "password_hash": "mocked-bcrypt-hash",
    },
}


def create_access_token(
    subject: str,
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Token subject (typically user email).
        user_id: Unique user identifier.
        role: User role for RBAC.
        expires_delta: Custom expiration window.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "campaign-portal-api",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    logger.info("Access token created", extra={"user_id": user_id})
    return token


def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        HTTPException 401 on invalid or expired tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject claim",
            )
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    FastAPI dependency that extracts and validates the JWT from the
    Authorization header, returning the decoded user payload.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            ...
    """
    payload = verify_token(credentials.credentials)
    return {
        "user_id": payload["user_id"],
        "email": payload["sub"],
        "role": payload.get("role", "viewer"),
    }


from google.oauth2 import id_token
from google.auth.transport import requests

def verify_google_token(token: str) -> dict:
    """
    Verify Google ID token and return user info.
    Auto-registers new users into MOCK_USERS if they don't exist.
    """
    try:
        # Verify the token against Google's public keys
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.google_client_id
        )

        email = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token missing email",
            )

        # Auto-register if not exists
        if email not in MOCK_USERS:
            new_id = f"usr_{int(datetime.now(timezone.utc).timestamp())}"
            MOCK_USERS[email] = {
                "id": new_id,
                "email": email,
                "full_name": idinfo.get("name", "Google User"),
                "role": "marketer",
            }
            logger.info(f"Auto-registered new Google user: {email}")

        return MOCK_USERS[email]

    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google authentication token",
        )

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Mock authentication — validates credentials against the in-memory store.
    """
    user = MOCK_USERS.get(email)
    if user is None:
        logger.warning(f"Authentication failed: unknown user {email}")
        return None

    if not password:
        logger.warning(f"Authentication failed: empty password for {email}")
        return None

    logger.info(f"User authenticated successfully", extra={"user_id": user["id"]})
    return user
