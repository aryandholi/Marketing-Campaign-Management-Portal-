"""
Reporting routes — campaign analytics and aggregated metrics.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.auth import get_current_user
from api.core.database import get_db
from api.schemas.schemas import CampaignMetrics
from api.models.campaign import Campaign
from api.models.message import MessageInstance, MessageStatus
from api.models.engagement import EngagementEvent, EngagementEventType
from api.services.reporting_service import ReportingService
from api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get(
    "/campaigns/summary",
    summary="Get aggregated metrics across all campaigns",
)
async def get_overall_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated real summary metrics for the dashboard overview.
    Queries actual campaign, message, and engagement data from the database.
    """
    # Count campaigns
    camp_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.owner_id == current_user["user_id"])
    )
    total_campaigns = camp_result.scalar() or 0

    # Message-level aggregates across all campaigns owned by user
    msg_query = select(
        func.count(MessageInstance.id).label("total_sent"),
        func.count(
            case(
                (MessageInstance.status == MessageStatus.DELIVERED, MessageInstance.id)
            )
        ).label("total_delivered"),
        func.count(
            case(
                (MessageInstance.status.in_([MessageStatus.FAILED, MessageStatus.BOUNCED]), MessageInstance.id)
            )
        ).label("total_failed"),
    ).where(
        MessageInstance.campaign_id.in_(
            select(Campaign.id).where(Campaign.owner_id == current_user["user_id"])
        )
    )
    msg_result = await db.execute(msg_query)
    msg_row = msg_result.one()

    total_sent = msg_row.total_sent or 0
    total_delivered = msg_row.total_delivered or 0
    total_failed = msg_row.total_failed or 0

    # Engagement-level aggregates
    msg_ids_subquery = select(MessageInstance.id).where(
        MessageInstance.campaign_id.in_(
            select(Campaign.id).where(Campaign.owner_id == current_user["user_id"])
        )
    )
    eng_query = select(
        func.count(
            case(
                (EngagementEvent.event_type.in_([
                    EngagementEventType.OPENED, EngagementEventType.READ
                ]), EngagementEvent.id)
            )
        ).label("total_opened"),
        func.count(
            case(
                (EngagementEvent.event_type.in_([
                    EngagementEventType.LINK_CLICKED, EngagementEventType.BUTTON_CLICKED
                ]), EngagementEvent.id)
            )
        ).label("total_clicked"),
    ).where(EngagementEvent.message_id.in_(msg_ids_subquery))

    eng_result = await db.execute(eng_query)
    eng_row = eng_result.one()

    total_opened = eng_row.total_opened or 0
    total_clicked = eng_row.total_clicked or 0

    return {
        "total_campaigns": total_campaigns,
        "total_sent": total_sent,
        "total_delivered": total_delivered,
        "total_failed": total_failed,
        "total_opened": total_opened,
        "total_clicked": total_clicked,
    }


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignMetrics,
    summary="Get campaign performance metrics",
)
async def get_campaign_report(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregated metrics for a campaign:
    - **Total recipients**: Number of contacts targeted
    - **Sent/Delivered/Failed**: Message delivery statistics
    - **Opened/Replied/Clicked**: Engagement metrics
    - **Rates**: Delivery rate, open rate, click-through rate (%)
    """
    service = ReportingService(db)
    return await service.get_campaign_metrics(campaign_id)


@router.get(
    "/campaigns/{campaign_id}/events",
    summary="Get engagement events for a campaign",
)
async def get_campaign_events(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all engagement events for messages belonging to a campaign.
    """
    # Get message IDs for this campaign
    msg_ids_query = select(MessageInstance.id).where(
        MessageInstance.campaign_id == campaign_id
    )
    events_query = (
        select(EngagementEvent)
        .where(EngagementEvent.message_id.in_(msg_ids_query))
        .order_by(EngagementEvent.created_at.desc())
        .limit(100)
    )
    result = await db.execute(events_query)
    events = list(result.scalars().all())

    return {
        "campaign_id": campaign_id,
        "total_events": len(events),
        "events": [
            {
                "id": e.id,
                "message_id": e.message_id,
                "event_type": e.event_type.value,
                "event_details": e.event_details,
                "source_ip": e.source_ip,
                "user_agent": e.user_agent,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }
