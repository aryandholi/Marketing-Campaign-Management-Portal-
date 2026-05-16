"""
Authentication routes — login and current-user endpoints.

Provides mock JWT token issuance for POC demonstration.
"""

from fastapi import APIRouter, HTTPException, Depends, status

from api.core.auth import (
    authenticate_user,
    verify_google_token,
    create_access_token,
    get_current_user,
)
from api.schemas.schemas import LoginRequest, GoogleLoginRequest, TokenResponse, UserResponse
from api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT token",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
async def login(request: LoginRequest):
    """
    Authenticate with email and password, returning a JWT access token.

    **POC Note:** Any non-empty password is accepted for known mock users:
    - `admin@campaignportal.io`
    - `marketer@campaignportal.io`
    """
    user = authenticate_user(request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user["email"],
        user_id=user["id"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
        ),
    )

@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Authenticate via Google ID Token",
)
async def google_login(request: GoogleLoginRequest):
    """
    Validates a Google ID token and issues a JWT token.
    """
    user = verify_google_token(request.credential)
    
    token = create_access_token(
        subject=user["email"],
        user_id=user["id"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        id=current_user["user_id"],
        email=current_user["email"],
        full_name="Authenticated User",
        role=current_user["role"],
    )
