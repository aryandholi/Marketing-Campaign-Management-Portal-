"""
Campaign management routes — CRUD operations and lifecycle management.

All routes are protected by JWT authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.auth import get_current_user
from api.core.database import get_db
from api.schemas.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    SendCampaignRequest,
    SendCampaignResponse,
    AudienceResolveRequest,
    AudienceResolveResponse,
)
from api.services.campaign_service import CampaignService
from api.services.audience_service import AudienceService
from api.services.orchestration_service import OrchestrationService
from api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


# ═══════════════════════════════════════════════════════════════════════════
# CRUD Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=CampaignResponse,
    status_code=201,
    summary="Create a new campaign",
)
async def create_campaign(
    data: CampaignCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new marketing campaign in DRAFT status."""
    service = CampaignService(db)
    campaign = await service.create(data, owner_id=current_user["user_id"])
    return CampaignResponse.model_validate(campaign)


@router.get(
    "",
    response_model=CampaignListResponse,
    summary="List all campaigns",
)
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns with optional filtering and pagination."""
    service = CampaignService(db)
    campaigns, total = await service.list_all(
        owner_id=current_user["user_id"],
        status=status,
        limit=limit,
        offset=offset,
    )
    return CampaignListResponse(
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get campaign details",
)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single campaign by ID."""
    service = CampaignService(db)
    campaign = await service.get_by_id(campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update campaign details",
)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a campaign (only allowed in DRAFT status)."""
    service = CampaignService(db)
    campaign = await service.update(campaign_id, data)
    return CampaignResponse.model_validate(campaign)


@router.delete(
    "/{campaign_id}",
    status_code=204,
    summary="Delete a campaign",
)
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a campaign and all associated data."""
    service = CampaignService(db)
    await service.delete(campaign_id)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Lifecycle Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post(
    "/{campaign_id}/start",
    response_model=CampaignResponse,
    summary="Start a campaign (DRAFT → ACTIVE)",
)
async def start_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a draft campaign, making it ready for message dispatch."""
    service = CampaignService(db)
    campaign = await service.start(campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.post(
    "/{campaign_id}/pause",
    response_model=CampaignResponse,
    summary="Pause a campaign (ACTIVE → PAUSED)",
)
async def pause_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause an active campaign, halting message dispatch."""
    service = CampaignService(db)
    campaign = await service.pause(campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.post(
    "/{campaign_id}/resume",
    response_model=CampaignResponse,
    summary="Resume a campaign (PAUSED → ACTIVE)",
)
async def resume_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused campaign."""
    service = CampaignService(db)
    campaign = await service.resume(campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.post(
    "/{campaign_id}/stop",
    response_model=CampaignResponse,
    summary="Stop a campaign permanently",
)
async def stop_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently stop a campaign. This action cannot be undone."""
    service = CampaignService(db)
    campaign = await service.stop(campaign_id)
    return CampaignResponse.model_validate(campaign)


# ═══════════════════════════════════════════════════════════════════════════
# Dispatch & Audience Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post(
    "/{campaign_id}/send",
    response_model=SendCampaignResponse,
    summary="Trigger campaign message dispatch",
)
async def send_campaign(
    campaign_id: str,
    request: SendCampaignRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger delivery for a campaign. Resolves audience, renders templates,
    and dispatches through the appropriate channel adapter.
    """
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_by_id(campaign_id)

    orchestrator = OrchestrationService(db)
    result = await orchestrator.send_campaign(
        campaign=campaign,
        recipient_identifiers=request.recipient_identifiers,
    )
    return result


@router.post(
    "/audience/resolve",
    response_model=AudienceResolveResponse,
    summary="Resolve audience identifiers to contacts",
)
async def resolve_audience(
    request: AudienceResolveRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Resolve a list of emails, phone numbers, or usernames to contact profiles.
    Useful for previewing campaign audience before dispatch.
    """
    return AudienceService.resolve(request.identifiers)
