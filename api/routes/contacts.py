"""
Contacts management routes — add and list contacts for campaigns.

Allows users to register real email addresses and phone numbers
as contacts that can receive actual campaign messages.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from api.core.auth import get_current_user
from api.services.audience_service import MockContactStore, AudienceService
from api.schemas.schemas import AudienceResolveRequest, AudienceResolveResponse
from api.core.logging import get_logger
from pydantic import BaseModel, Field, EmailStr

logger = get_logger(__name__)

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    """Schema for creating a new contact."""
    email: str = Field(..., description="Real email address for email campaigns")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field("", max_length=100)
    phone: Optional[str] = Field(None, description="Phone number for SMS campaigns (e.g. +1234567890)")
    username: Optional[str] = Field(None, max_length=100)


class ContactResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    username: Optional[str]


@router.get(
    "",
    summary="List all available contacts",
)
async def list_contacts(
    current_user: dict = Depends(get_current_user),
):
    """Return all contacts available for audience targeting."""
    contacts = MockContactStore.all_contacts()
    return {
        "contacts": contacts,
        "total": len(contacts),
    }


@router.post(
    "",
    response_model=ContactResponse,
    status_code=201,
    summary="Add a new contact (real email address)",
)
async def create_contact(
    data: ContactCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Register a new contact with a real email address.

    Once registered, the contact can be targeted by email campaigns
    and will receive actual emails when SMTP is configured.

    The contact is indexed by email, phone (if provided), and username.
    """
    # Validate email format
    if "@" not in data.email or "." not in data.email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address format",
        )

    # Check if already exists
    existing = MockContactStore.lookup(data.email)

    if existing:
        logger.info(f"Contact already exists for {data.email}, returning existing")
        return ContactResponse(
            id=existing["id"],
            email=existing["email"],
            first_name=existing.get("first_name", ""),
            last_name=existing.get("last_name", ""),
            phone=existing.get("phone"),
            username=existing.get("username"),
        )

    # Generate a unique contact ID
    import uuid as _uuid
    contact_id = f"contact_{_uuid.uuid4().hex[:12]}"

    contact = {
        "id": contact_id,
        "email": data.email.lower().strip(),
        "first_name": data.first_name,
        "last_name": data.last_name,
        "phone": data.phone,
        "username": data.username or data.email.split("@")[0],
    }

    # Register under all lookup keys
    MockContactStore.add_contact(data.email.lower().strip(), contact)
    if data.phone:
        MockContactStore.add_contact(data.phone.strip(), contact)
    if data.username:
        MockContactStore.add_contact(data.username.strip(), contact)

    logger.info(
        f"New contact registered: {contact_id} ({data.email})",
        extra={"request_method": "POST", "request_path": "/api/contacts"},
    )

    return ContactResponse(
        id=contact_id,
        email=contact["email"],
        first_name=contact["first_name"],
        last_name=contact["last_name"],
        phone=contact.get("phone"),
        username=contact.get("username"),
    )
