"""
Orchestration Service — coordinates message delivery across channels.

Responsible for:
1. Resolving the campaign audience
2. Rendering message templates per recipient
3. Dispatching messages through the appropriate channel adapter
4. Recording MessageInstance and DeliveryAttempt records

In a production system, this would publish to a message queue (Kafka/RabbitMQ)
and workers would process deliveries asynchronously. For this POC, delivery
is performed synchronously to demonstrate the full flow.
"""

import re
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.adapters.factory import ChannelAdapterFactory
from api.models.campaign import Campaign
from api.models.delivery import DeliveryAttempt, DeliveryStatus
from api.models.message import MessageInstance, MessageStatus
from api.models.recipient import RecipientList
from api.services.audience_service import AudienceService
from api.schemas.schemas import SendCampaignResponse
from api.core.exceptions import AudienceResolutionError
from api.core.logging import get_logger

logger = get_logger(__name__)


class OrchestrationService:
    """
    Orchestrates message delivery for a campaign.

    Follows the pipeline: Resolve Audience → Render Template → Send → Record Results.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _render_template(self, template: str, contact: Dict[str, Any]) -> str:
        """
        Render a message template by substituting {{placeholder}} tokens.

        Supports: {{first_name}}, {{last_name}}, {{email}}, {{phone}}, {{username}}
        """
        rendered = template
        for key in ("first_name", "last_name", "email", "phone", "username"):
            placeholder = "{{" + key + "}}"
            value = contact.get(key, "")
            rendered = rendered.replace(placeholder, value or "")
        return rendered

    def _get_recipient_address(self, contact: Dict[str, Any], channel: str) -> Optional[str]:
        """Extract the appropriate delivery address based on channel type."""
        if channel == "email":
            return contact.get("email")
        elif channel == "sms":
            return contact.get("phone")
        return None

    async def send_campaign(
        self,
        campaign: Campaign,
        recipient_identifiers: Optional[List[str]] = None,
    ) -> SendCampaignResponse:
        """
        Execute the full delivery pipeline for a campaign.

        Args:
            campaign: Campaign entity to send.
            recipient_identifiers: Optional override list. If None,
                uses campaign.target_audience.

        Returns:
            SendCampaignResponse with delivery statistics.
        """
        # ── Step 1: Resolve Audience ──────────────────────────────────
        if recipient_identifiers:
            identifiers = recipient_identifiers
        elif campaign.target_audience:
            identifiers = [
                i.strip() for i in campaign.target_audience.split(",") if i.strip()
            ]
        else:
            raise AudienceResolutionError("No audience specified for campaign")

        audience_result = AudienceService.resolve(identifiers)

        if audience_result.total_resolved == 0:
            raise AudienceResolutionError(
                f"No contacts resolved from {len(identifiers)} identifiers"
            )

        # ── Step 2: Get Channel Adapter ───────────────────────────────
        channel = campaign.channel
        if hasattr(channel, 'value'):
            channel = channel.value
        adapter = ChannelAdapterFactory.get_adapter(channel)

        # ── Step 3: Deliver Messages ──────────────────────────────────
        messages_summary: List[Dict[str, Any]] = []
        total_sent = 0
        total_delivered = 0
        total_failed = 0

        for contact in audience_result.resolved:
            contact_dict = contact.model_dump()
            recipient_address = self._get_recipient_address(contact_dict, channel)

            if not recipient_address:
                logger.warning(
                    f"No {channel} address for contact {contact.id}, skipping"
                )
                total_failed += 1
                continue

            # Render the template
            rendered_content = self._render_template(
                campaign.message_template, contact_dict
            )

            # Create MessageInstance record
            message = MessageInstance(
                campaign_id=campaign.id,
                contact_id=contact.id,
                rendered_content=rendered_content,
                channel=channel,
                recipient_address=recipient_address,
                status=MessageStatus.PENDING,
            )
            self.db.add(message)
            await self.db.flush()
            await self.db.refresh(message)

            # Create RecipientList entry
            recipient_entry = RecipientList(
                campaign_id=campaign.id,
                contact_id=contact.id,
            )
            self.db.add(recipient_entry)

            # Send via adapter
            subject = f"Campaign: {campaign.name}" if channel == "email" else None
            result = await adapter.send(
                recipient_address=recipient_address,
                subject=subject,
                body=rendered_content,
                metadata={"campaign_id": campaign.id, "contact_id": contact.id},
            )

            total_sent += 1

            # Record DeliveryAttempt
            delivery = DeliveryAttempt(
                message_id=message.id,
                attempt_number=1,
                status=DeliveryStatus.SUCCESS if result.success else DeliveryStatus.FAILURE,
                provider_response=result.provider_response,
                latency_ms=result.latency_ms,
                error_message=result.error_message,
            )
            self.db.add(delivery)

            # Update message status
            if result.success:
                message.status = MessageStatus.DELIVERED
                total_delivered += 1
            else:
                message.status = MessageStatus.FAILED
                total_failed += 1

            messages_summary.append({
                "message_id": message.id,
                "contact_id": contact.id,
                "recipient_address": recipient_address,
                "status": message.status.value,
                "provider_message_id": result.provider_message_id,
                "latency_ms": result.latency_ms,
                "error": result.error_message,
            })

        await self.db.flush()

        logger.info(
            f"Campaign {campaign.id} send complete: "
            f"{total_sent} sent, {total_delivered} delivered, {total_failed} failed"
        )

        return SendCampaignResponse(
            campaign_id=campaign.id,
            total_recipients=audience_result.total_resolved,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            messages=messages_summary,
        )
