"""
Engagement event webhook routes — ingests tracking events from channels.

This endpoint would typically be called by email/SMS providers
(SendGrid, Twilio webhooks) to report delivery and engagement events.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.schemas.schemas import EngagementEventCreate, EngagementEventResponse
from api.services.event_service import EventService
from api.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/events", tags=["Engagement Events"])


@router.post(
    "",
    response_model=EngagementEventResponse,
    status_code=201,
    summary="Ingest an engagement event",
)
async def ingest_event(
    data: EngagementEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for ingesting engagement events.

    Accepts events such as: `delivered`, `opened`, `read`, `replied`,
    `link_clicked`, `page_navigated`, `button_clicked`.

    This endpoint is intentionally unauthenticated to allow
    third-party provider webhooks. In production, validate
    webhook signatures (e.g., SendGrid signed event webhook).

    **Example payload:**
    ```json
    {
        "message_id": "msg-uuid-here",
        "event_type": "link_clicked",
        "event_details": {
            "link_url": "https://example.com/promo",
            "user_agent": "Mozilla/5.0"
        },
        "source_ip": "203.0.113.42"
    }
    ```
    """
    service = EventService(db)
    event = await service.ingest_event(data)
    return EngagementEventResponse(
        id=event.id,
        message_id=event.message_id,
        event_type=event.event_type.value,
        event_details=event.event_details,
        source_ip=event.source_ip,
        user_agent=event.user_agent,
        created_at=event.created_at,
    )
