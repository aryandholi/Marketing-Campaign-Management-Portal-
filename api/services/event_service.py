"""
Event Ingestion Service — processes incoming engagement webhook events.

Validates event types, maps them to the correct message instance,
and persists EngagementEvent records for analytics.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.engagement import EngagementEvent, EngagementEventType
from api.models.message import MessageInstance
from api.schemas.schemas import EngagementEventCreate, EngagementEventResponse
from api.core.exceptions import EntityNotFoundError
from api.core.logging import get_logger

logger = get_logger(__name__)

# Map string event type names to enum values
EVENT_TYPE_MAP = {
    "delivered": EngagementEventType.DELIVERED,
    "opened": EngagementEventType.OPENED,
    "read": EngagementEventType.READ,
    "replied": EngagementEventType.REPLIED,
    "link_clicked": EngagementEventType.LINK_CLICKED,
    "page_navigated": EngagementEventType.PAGE_NAVIGATED,
    "button_clicked": EngagementEventType.BUTTON_CLICKED,
}


class EventService:
    """Service for ingesting and storing engagement events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_event(self, data: EngagementEventCreate) -> EngagementEvent:
        """
        Process and store a single engagement event.

        Validates that the referenced message exists and the event type
        is supported, then persists the event with optional metadata.

        Args:
            data: Validated event payload from the webhook.

        Returns:
            The created EngagementEvent entity.

        Raises:
            EntityNotFoundError: If the referenced message_id doesn't exist.
        """
        # Verify message exists
        result = await self.db.execute(
            select(MessageInstance).where(MessageInstance.id == data.message_id)
        )
        message = result.scalar_one_or_none()
        if message is None:
            raise EntityNotFoundError("MessageInstance", data.message_id)

        # Map string event type to enum
        event_type_enum = EVENT_TYPE_MAP.get(data.event_type)
        if event_type_enum is None:
            raise ValueError(f"Invalid event type: {data.event_type}")

        # Create engagement event
        event = EngagementEvent(
            message_id=data.message_id,
            event_type=event_type_enum,
            event_details=data.event_details or {},
            source_ip=data.source_ip,
            user_agent=data.user_agent,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)

        logger.info(
            f"Engagement event ingested: {event.event_type.value} "
            f"for message {data.message_id}",
            extra={"request_method": "WEBHOOK", "request_path": "/api/events"},
        )

        return event

    async def get_events_for_message(self, message_id: str) -> list:
        """Retrieve all engagement events for a specific message."""
        result = await self.db.execute(
            select(EngagementEvent)
            .where(EngagementEvent.message_id == message_id)
            .order_by(EngagementEvent.created_at.desc())
        )
        return list(result.scalars().all())
