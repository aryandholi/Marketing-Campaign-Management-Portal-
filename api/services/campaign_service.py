"""
Campaign Service — business logic for campaign CRUD and lifecycle management.

Implements a state machine for campaign status transitions and provides
all database operations for campaign entities.
"""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.campaign import Campaign, CampaignStatus
from api.schemas.schemas import CampaignCreate, CampaignUpdate
from api.core.exceptions import EntityNotFoundError, InvalidStateTransitionError
from api.core.logging import get_logger

logger = get_logger(__name__)

# ── State Machine ─────────────────────────────────────────────────────────
# Defines valid status transitions for campaign lifecycle management
VALID_TRANSITIONS = {
    CampaignStatus.DRAFT: {CampaignStatus.ACTIVE, CampaignStatus.STOPPED},
    CampaignStatus.ACTIVE: {CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.STOPPED},
    CampaignStatus.PAUSED: {CampaignStatus.ACTIVE, CampaignStatus.STOPPED},
    CampaignStatus.COMPLETED: set(),  # Terminal state
    CampaignStatus.STOPPED: set(),    # Terminal state
}


class CampaignService:
    """Service layer for campaign management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CampaignCreate, owner_id: str) -> Campaign:
        """Create a new campaign in DRAFT status."""
        campaign = Campaign(
            name=data.name,
            description=data.description,
            channel=data.channel,
            message_template=data.message_template,
            target_audience=data.target_audience,
            schedule_time=data.schedule_time,
            status=CampaignStatus.DRAFT,
            owner_id=owner_id,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        logger.info(f"Campaign created: {campaign.id} by user {owner_id}")
        return campaign

    async def get_by_id(self, campaign_id: str) -> Campaign:
        """Retrieve a single campaign by ID or raise 404."""
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if campaign is None:
            raise EntityNotFoundError("Campaign", campaign_id)
        return campaign

    async def list_all(
        self,
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Campaign], int]:
        """List campaigns with optional filtering by owner and status."""
        query = select(Campaign)
        count_query = select(func.count(Campaign.id))

        if owner_id:
            query = query.where(Campaign.owner_id == owner_id)
            count_query = count_query.where(Campaign.owner_id == owner_id)
        if status:
            query = query.where(Campaign.status == status)
            count_query = count_query.where(Campaign.status == status)

        query = query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        campaigns = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return campaigns, total

    async def update(self, campaign_id: str, data: CampaignUpdate) -> Campaign:
        """Update a campaign's editable fields (only in DRAFT status)."""
        campaign = await self.get_by_id(campaign_id)

        if campaign.status != CampaignStatus.DRAFT:
            logger.warning(f"Attempted to edit non-draft campaign {campaign_id}")
            raise InvalidStateTransitionError(
                campaign.status.value,
                "edit (only DRAFT campaigns can be edited)"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        await self.db.flush()
        await self.db.refresh(campaign)
        logger.info(f"Campaign updated: {campaign_id}")
        return campaign

    async def delete(self, campaign_id: str) -> None:
        """Delete a campaign (soft-delete can be added later)."""
        campaign = await self.get_by_id(campaign_id)
        await self.db.delete(campaign)
        await self.db.flush()
        logger.info(f"Campaign deleted: {campaign_id}")

    async def transition_status(
        self, campaign_id: str, target_status: CampaignStatus
    ) -> Campaign:
        """
        Transition a campaign to a new status using the state machine.

        Validates that the transition is allowed before applying.
        """
        campaign = await self.get_by_id(campaign_id)
        current = campaign.status

        allowed = VALID_TRANSITIONS.get(current, set())
        if target_status not in allowed:
            raise InvalidStateTransitionError(current.value, target_status.value)

        campaign.status = target_status
        await self.db.flush()
        await self.db.refresh(campaign)
        logger.info(f"Campaign {campaign_id}: {current.value} → {target_status.value}")
        return campaign

    async def start(self, campaign_id: str) -> Campaign:
        """Start a campaign (DRAFT → ACTIVE)."""
        return await self.transition_status(campaign_id, CampaignStatus.ACTIVE)

    async def pause(self, campaign_id: str) -> Campaign:
        """Pause an active campaign (ACTIVE → PAUSED)."""
        return await self.transition_status(campaign_id, CampaignStatus.PAUSED)

    async def resume(self, campaign_id: str) -> Campaign:
        """Resume a paused campaign (PAUSED → ACTIVE)."""
        return await self.transition_status(campaign_id, CampaignStatus.ACTIVE)

    async def stop(self, campaign_id: str) -> Campaign:
        """Stop a campaign permanently (any → STOPPED)."""
        return await self.transition_status(campaign_id, CampaignStatus.STOPPED)
