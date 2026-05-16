"""
Reporting Service — generates aggregated campaign delivery and engagement metrics.

Queries MessageInstance, DeliveryAttempt, and EngagementEvent tables
to produce a comprehensive performance report for a given campaign.
"""

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.campaign import Campaign
from api.models.message import MessageInstance, MessageStatus
from api.models.delivery import DeliveryAttempt, DeliveryStatus
from api.models.engagement import EngagementEvent, EngagementEventType
from api.schemas.schemas import CampaignMetrics
from api.core.exceptions import EntityNotFoundError
from api.core.logging import get_logger

logger = get_logger(__name__)


class ReportingService:
    """Service for generating campaign performance analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_campaign_metrics(self, campaign_id: str) -> CampaignMetrics:
        """
        Compute aggregated metrics for a campaign.

        Returns counts for: total recipients, sent, delivered, failed,
        opened, replied, clicked — plus derived rates.
        """
        # ── Verify campaign exists ────────────────────────────────────
        campaign_result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = campaign_result.scalar_one_or_none()
        if campaign is None:
            raise EntityNotFoundError("Campaign", campaign_id)

        # ── Message-level metrics ─────────────────────────────────────
        msg_query = select(
            func.count(MessageInstance.id).label("total_recipients"),
            func.count(
                case(
                    (MessageInstance.status.in_([
                        MessageStatus.SENT,
                        MessageStatus.DELIVERED,
                        MessageStatus.FAILED,
                        MessageStatus.BOUNCED,
                    ]), MessageInstance.id)
                )
            ).label("total_sent"),
            func.count(
                case(
                    (MessageInstance.status == MessageStatus.DELIVERED, MessageInstance.id)
                )
            ).label("total_delivered"),
            func.count(
                case(
                    (MessageInstance.status.in_([
                        MessageStatus.FAILED,
                        MessageStatus.BOUNCED,
                    ]), MessageInstance.id)
                )
            ).label("total_failed"),
        ).where(MessageInstance.campaign_id == campaign_id)

        msg_result = await self.db.execute(msg_query)
        msg_row = msg_result.one()

        total_recipients = msg_row.total_recipients or 0
        total_sent = msg_row.total_sent or 0
        total_delivered = msg_row.total_delivered or 0
        total_failed = msg_row.total_failed or 0

        # ── Engagement-level metrics ──────────────────────────────────
        # Get message IDs for this campaign
        msg_ids_query = select(MessageInstance.id).where(
            MessageInstance.campaign_id == campaign_id
        )

        engagement_query = select(
            func.count(
                case(
                    (EngagementEvent.event_type.in_([
                        EngagementEventType.OPENED,
                        EngagementEventType.READ,
                    ]), EngagementEvent.id)
                )
            ).label("total_opened"),
            func.count(
                case(
                    (EngagementEvent.event_type == EngagementEventType.REPLIED, EngagementEvent.id)
                )
            ).label("total_replied"),
            func.count(
                case(
                    (EngagementEvent.event_type.in_([
                        EngagementEventType.LINK_CLICKED,
                        EngagementEventType.BUTTON_CLICKED,
                    ]), EngagementEvent.id)
                )
            ).label("total_clicked"),
        ).where(EngagementEvent.message_id.in_(msg_ids_query))

        eng_result = await self.db.execute(engagement_query)
        eng_row = eng_result.one()

        total_opened = eng_row.total_opened or 0
        total_replied = eng_row.total_replied or 0
        total_clicked = eng_row.total_clicked or 0

        # ── Computed rates ────────────────────────────────────────────
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
        open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
        click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0.0

        metrics = CampaignMetrics(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            total_recipients=total_recipients,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            total_opened=total_opened,
            total_replied=total_replied,
            total_clicked=total_clicked,
            delivery_rate=round(delivery_rate, 2),
            open_rate=round(open_rate, 2),
            click_rate=round(click_rate, 2),
        )

        logger.info(
            f"Metrics generated for campaign {campaign_id}: "
            f"sent={total_sent}, delivered={total_delivered}, "
            f"opened={total_opened}, clicked={total_clicked}"
        )

        return metrics
