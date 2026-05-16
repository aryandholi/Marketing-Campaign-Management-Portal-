"""
Settings management routes — update channel credentials at runtime.

Allows updating SMTP and Twilio configuration without redeployment.
Settings are stored in memory for the POC; in production these would
be persisted encrypted in the database or a secrets manager.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from api.core.auth import get_current_user
from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class SMTPSettings(BaseModel):
    smtp_host: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(587, ge=1, le=65535)
    smtp_username: str = Field(..., description="SMTP username / email")
    smtp_password: str = Field(..., description="SMTP password or App Password")
    smtp_from_email: str = Field(..., description="From address for sent emails")
    smtp_from_name: str = Field("Nexus Portal", description="Display name for sent emails")
    smtp_use_tls: bool = Field(True)


class TwilioSettings(BaseModel):
    twilio_account_sid: str = Field(..., description="Twilio Account SID (starts with AC)")
    twilio_auth_token: str = Field(..., description="Twilio Auth Token")
    twilio_from_number: str = Field(..., description="Twilio phone number (E.164 format: +1234567890)")


class ChannelStatusResponse(BaseModel):
    email_configured: bool
    sms_configured: bool
    email_provider: str
    sms_provider: str


@router.get(
    "/channels/status",
    response_model=ChannelStatusResponse,
    summary="Get channel configuration status",
)
async def get_channel_status(
    current_user: dict = Depends(get_current_user),
):
    """Returns whether SMTP (email) and Twilio (SMS) are configured."""
    settings = get_settings()
    return ChannelStatusResponse(
        email_configured=settings.smtp_configured,
        sms_configured=settings.twilio_configured,
        email_provider="smtp" if settings.smtp_configured else "mock",
        sms_provider="twilio" if settings.twilio_configured else "mock",
    )


@router.post(
    "/smtp",
    summary="Update SMTP configuration at runtime",
)
async def update_smtp(
    data: SMTPSettings,
    current_user: dict = Depends(get_current_user),
):
    """
    Update SMTP settings at runtime.

    Changes take effect immediately for subsequent campaign sends.
    In production, these would be persisted to an encrypted secrets store.

    **Note:** This updates the in-process settings singleton.
    On serverless (Vercel), each invocation is isolated — set credentials
    via environment variables for persistent configuration.
    """
    settings = get_settings()
    # Mutate the cached settings instance
    settings.smtp_host = data.smtp_host
    settings.smtp_port = data.smtp_port
    settings.smtp_username = data.smtp_username
    settings.smtp_password = data.smtp_password
    settings.smtp_from_email = data.smtp_from_email
    settings.smtp_from_name = data.smtp_from_name
    settings.smtp_use_tls = data.smtp_use_tls

    logger.info(
        f"SMTP settings updated by {current_user['email']}: host={data.smtp_host}",
        extra={"request_method": "POST", "request_path": "/api/settings/smtp"},
    )

    return {
        "message": "SMTP settings updated successfully",
        "smtp_host": data.smtp_host,
        "smtp_port": data.smtp_port,
        "smtp_from_email": data.smtp_from_email,
        "smtp_configured": settings.smtp_configured,
    }


@router.post(
    "/twilio",
    summary="Update Twilio SMS configuration at runtime",
)
async def update_twilio(
    data: TwilioSettings,
    current_user: dict = Depends(get_current_user),
):
    """
    Update Twilio credentials at runtime.

    Changes take effect immediately for subsequent campaign sends.
    """
    settings = get_settings()
    settings.twilio_account_sid = data.twilio_account_sid
    settings.twilio_auth_token = data.twilio_auth_token
    settings.twilio_from_number = data.twilio_from_number

    logger.info(
        f"Twilio settings updated by {current_user['email']}",
        extra={"request_method": "POST", "request_path": "/api/settings/twilio"},
    )

    return {
        "message": "Twilio settings updated successfully",
        "from_number": data.twilio_from_number,
        "sms_configured": settings.twilio_configured,
    }
