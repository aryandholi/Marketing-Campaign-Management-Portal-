"""
Pydantic schemas (request/response models) for all API entities.

Provides input validation, serialization, and OpenAPI documentation.
Uses Pydantic v2 with `model_config` for ORM compatibility.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr, model_validator


# ═══════════════════════════════════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address", examples=["admin@campaignportal.io"])
    password: str = Field(..., description="User password", min_length=1)

class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: str
    role: str


# ═══════════════════════════════════════════════════════════════════════════
# Campaign Schemas
# ═══════════════════════════════════════════════════════════════════════════

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    description: Optional[str] = Field(None, max_length=2000)
    channel: str = Field(..., description="Delivery channel: email or sms", examples=["email"])
    message_template: str = Field(..., min_length=1, description="Message template with {{placeholders}}")
    target_audience: Optional[str] = Field(
        None,
        description="Comma-separated emails, phones, or usernames for audience resolution"
    )
    schedule_time: Optional[datetime] = Field(None, description="Scheduled send time (UTC ISO 8601)")

    @model_validator(mode="after")
    def validate_channel(self):
        if self.channel not in ("email", "sms"):
            raise ValueError("Channel must be 'email' or 'sms'")
        return self


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    message_template: Optional[str] = None
    target_audience: Optional[str] = None
    schedule_time: Optional[datetime] = None


class CampaignResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: Optional[str]
    channel: str
    message_template: str
    target_audience: Optional[str]
    schedule_time: Optional[datetime]
    status: str
    owner_id: str
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════
# Audience Schemas
# ═══════════════════════════════════════════════════════════════════════════

class AudienceResolveRequest(BaseModel):
    identifiers: List[str] = Field(
        ...,
        min_length=1,
        description="List of emails, phone numbers, or usernames to resolve"
    )


class ResolvedContact(BaseModel):
    id: str
    identifier: str
    email: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    resolved: bool = True


class AudienceResolveResponse(BaseModel):
    resolved: List[ResolvedContact]
    unresolved: List[str]
    total_resolved: int
    total_unresolved: int


# ═══════════════════════════════════════════════════════════════════════════
# Engagement Event Schemas
# ═══════════════════════════════════════════════════════════════════════════

class EngagementEventCreate(BaseModel):
    message_id: str = Field(..., description="ID of the message instance")
    event_type: str = Field(
        ...,
        description="Event type: delivered, opened, read, replied, link_clicked, page_navigated, button_clicked"
    )
    event_details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Channel-specific event payload"
    )
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None

    @model_validator(mode="after")
    def validate_event_type(self):
        valid_types = {
            "delivered", "opened", "read", "replied",
            "link_clicked", "page_navigated", "button_clicked",
        }
        if self.event_type not in valid_types:
            raise ValueError(f"event_type must be one of: {', '.join(sorted(valid_types))}")
        return self


class EngagementEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    message_id: str
    event_type: str
    event_details: Optional[Dict[str, Any]]
    source_ip: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════
# Reporting Schemas
# ═══════════════════════════════════════════════════════════════════════════

class CampaignMetrics(BaseModel):
    campaign_id: str
    campaign_name: str
    total_recipients: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_opened: int = 0
    total_replied: int = 0
    total_clicked: int = 0
    delivery_rate: float = Field(0.0, description="Percentage of messages delivered")
    open_rate: float = Field(0.0, description="Percentage of delivered messages opened")
    click_rate: float = Field(0.0, description="Percentage of opened messages clicked")


# ═══════════════════════════════════════════════════════════════════════════
# Send / Orchestration Schemas
# ═══════════════════════════════════════════════════════════════════════════

class SendCampaignRequest(BaseModel):
    recipient_identifiers: Optional[List[str]] = Field(
        None,
        description="Override audience; if None, uses campaign's target_audience"
    )


class SendCampaignResponse(BaseModel):
    campaign_id: str
    total_recipients: int
    total_sent: int
    total_delivered: int
    total_failed: int
    messages: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════
# Health / Generic Schemas
# ═══════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    environment: str


class ErrorResponse(BaseModel):
    error: Dict[str, Any]
