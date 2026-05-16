"""
SMS channel adapter — real Twilio delivery with mock fallback.

When Twilio credentials are configured (via .env or Settings page),
this adapter sends actual SMS messages. If not configured, it falls back
to a simulated delivery for demo purposes.

Supported providers:
  - Twilio (primary, configured via TWILIO_* env vars)
  - Future: Vonage, AWS SNS, MessageBird
"""

import random
import time
import uuid
from typing import Any, Dict, Optional

from api.adapters.base import BaseChannelAdapter, DeliveryResult
from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)

# Simulated success rate: 90% of SMS messages delivered successfully
SMS_SUCCESS_RATE = 0.90


class SMSAdapter(BaseChannelAdapter):
    """
    SMS delivery adapter with real Twilio support.

    Checks settings.twilio_configured to decide whether to
    use real Twilio delivery or fall back to simulation.
    """

    @property
    def channel_name(self) -> str:
        return "sms"

    async def send(
        self,
        recipient_address: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Send an SMS message.

        Prefers real Twilio delivery when credentials are configured,
        falls back to simulation for demo/development.
        """
        settings = get_settings()

        if settings.twilio_configured:
            return await self._send_real(recipient_address, body, settings)
        else:
            return await self._send_mock(recipient_address, body)

    async def _send_real(
        self, recipient_address: str, body: str, settings
    ) -> DeliveryResult:
        """Send a real SMS via Twilio REST API."""
        start = time.monotonic()
        provider_message_id = f"twilio-{uuid.uuid4().hex[:16]}"

        # Truncate SMS body to 160 chars per segment
        sms_body = body[:160] if len(body) > 160 else body

        try:
            # Lazy import — only needed when Twilio is configured
            from twilio.rest import Client as TwilioClient  # type: ignore

            client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
            message = client.messages.create(
                body=sms_body,
                from_=settings.twilio_from_number,
                to=recipient_address,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            provider_message_id = message.sid or provider_message_id

            logger.info(
                f"[SMSAdapter] REAL SMS sent to {recipient_address} via Twilio (SID={message.sid})",
                extra={"request_method": "SEND", "request_path": f"sms:{recipient_address}"},
            )
            return DeliveryResult(
                success=True,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "twilio",
                    "status": message.status,
                    "sid": message.sid,
                    "to": recipient_address,
                    "body_length": len(sms_body),
                    "real_delivery": True,
                },
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            error_msg = str(exc)
            logger.error(
                f"[SMSAdapter] Twilio delivery failed to {recipient_address}: {error_msg}",
                extra={"request_method": "SEND", "request_path": f"sms:{recipient_address}"},
            )
            return DeliveryResult(
                success=False,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "twilio",
                    "status": "failed",
                    "error": error_msg,
                    "to": recipient_address,
                },
                error_message=error_msg,
                latency_ms=latency_ms,
            )

    async def _send_mock(self, recipient_address: str, body: str) -> DeliveryResult:
        """Simulate SMS delivery when Twilio is not configured."""
        start_time = time.monotonic()
        simulated_latency_ms = random.randint(30, 200)

        # Truncate body for SMS length limits
        sms_body = body[:160] if len(body) > 160 else body
        is_success = random.random() < SMS_SUCCESS_RATE

        provider_message_id = f"mock-twilio-{uuid.uuid4().hex[:16]}"
        latency_ms = int((time.monotonic() - start_time) * 1000) + simulated_latency_ms

        if is_success:
            logger.info(
                f"[SMSAdapter] MOCK SMS delivered to {recipient_address} (Twilio not configured)",
                extra={"request_method": "SEND", "request_path": f"sms:{recipient_address}"},
            )
            return DeliveryResult(
                success=True,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "mock-twilio",
                    "status": "delivered",
                    "sid": provider_message_id,
                    "to": recipient_address,
                    "body_length": len(sms_body),
                    "segments": max(1, len(body) // 160),
                    "note": "Configure Twilio credentials in Settings for real delivery",
                },
                latency_ms=latency_ms,
            )
        else:
            error_reasons = [
                "Invalid phone number format",
                "Carrier rejected message",
                "Number is on DNC list",
                "Provider timeout",
                "Insufficient account balance",
            ]
            error_msg = random.choice(error_reasons)
            logger.warning(
                f"[SMSAdapter] MOCK SMS delivery failed to {recipient_address}: {error_msg}",
                extra={"request_method": "SEND", "request_path": f"sms:{recipient_address}"},
            )
            return DeliveryResult(
                success=False,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "mock-twilio",
                    "status": "failed",
                    "error_code": "21211",
                    "error": error_msg,
                    "to": recipient_address,
                },
                error_message=error_msg,
                latency_ms=latency_ms,
            )

    async def validate_address(self, address: str) -> bool:
        """Basic phone number format validation."""
        cleaned = address.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15
