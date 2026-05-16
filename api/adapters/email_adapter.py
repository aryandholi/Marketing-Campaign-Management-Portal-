"""
Email channel adapter — real SMTP delivery with mock fallback.

When SMTP credentials are configured (via .env or Settings page),
this adapter sends actual emails. If not configured, it falls back
to a simulated delivery for demo purposes.

Supported SMTP providers:
  - Gmail (smtp.gmail.com:587, use App Password)
  - Outlook (smtp.office365.com:587)
  - SendGrid (smtp.sendgrid.net:587)
  - Mailtrap (sandbox.smtp.mailtrap.io:2525, for testing)
  - Any standard SMTP server
"""

import random
import time
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

# aiosmtplib is imported lazily inside _send_real so the module loads
# even if the package is not installed (only matters when SMTP is configured).

from api.adapters.base import BaseChannelAdapter, DeliveryResult
from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)


class EmailAdapter(BaseChannelAdapter):
    """
    Email delivery adapter with real SMTP support.

    Checks settings.smtp_configured to decide whether to
    use real SMTP delivery or fall back to simulation.
    """

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(
        self,
        recipient_address: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        settings = get_settings()

        if settings.smtp_configured:
            return await self._send_real(recipient_address, subject, body, settings)
        else:
            return await self._send_mock(recipient_address, subject, body)

    async def _send_real(self, recipient_address: str, subject: Optional[str], body: str, settings) -> DeliveryResult:
        """Send a real email via SMTP using aiosmtplib."""
        start = time.monotonic()
        provider_message_id = f"smtp-{uuid.uuid4().hex[:16]}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject or "Campaign Message"
        msg["From"]    = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"]      = recipient_address
        msg["Message-ID"] = f"<{provider_message_id}@nexus-portal>"

        # Plain text
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # HTML version (wrap in simple template)
        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
          <div style="background:#f8f9fa;border-radius:8px;padding:20px">
            {body.replace(chr(10), '<br>')}
          </div>
          <p style="color:#999;font-size:11px;margin-top:20px">
            Sent via Nexus Portal
          </p>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            import aiosmtplib  # lazy import — only needed for real SMTP
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=settings.smtp_use_tls,
                timeout=15,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                f"[EmailAdapter] REAL email sent to {recipient_address}",
                extra={"request_method": "SEND", "request_path": f"smtp:{recipient_address}"},
            )
            return DeliveryResult(
                success=True,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "smtp",
                    "host": settings.smtp_host,
                    "status": "sent",
                    "message_id": provider_message_id,
                    "recipient": recipient_address,
                    "subject": subject,
                    "real_delivery": True,
                },
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            error_msg = str(exc)
            logger.error(
                f"[EmailAdapter] SMTP delivery failed to {recipient_address}: {error_msg}",
                extra={"request_method": "SEND", "request_path": f"smtp:{recipient_address}"},
            )
            return DeliveryResult(
                success=False,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "smtp",
                    "status": "failed",
                    "error": error_msg,
                    "recipient": recipient_address,
                },
                error_message=error_msg,
                latency_ms=latency_ms,
            )

    async def _send_mock(self, recipient_address: str, subject: Optional[str], body: str) -> DeliveryResult:
        """Simulate delivery when SMTP is not configured."""
        start = time.monotonic()
        simulated_latency_ms = random.randint(50, 300)
        is_success = random.random() < 0.95  # 95% mock success rate
        provider_message_id = f"mock-{uuid.uuid4().hex[:16]}"
        latency_ms = int((time.monotonic() - start) * 1000) + simulated_latency_ms

        if is_success:
            logger.info(
                f"[EmailAdapter] MOCK email delivered to {recipient_address} (SMTP not configured)",
                extra={"request_method": "SEND", "request_path": f"email:{recipient_address}"},
            )
            return DeliveryResult(
                success=True,
                provider_message_id=provider_message_id,
                provider_response={
                    "provider": "mock",
                    "status": "simulated",
                    "message_id": provider_message_id,
                    "recipient": recipient_address,
                    "note": "Configure SMTP in Settings for real delivery",
                },
                latency_ms=latency_ms,
            )
        else:
            error_msg = random.choice(["Mailbox full", "Invalid domain", "Provider timeout"])
            return DeliveryResult(
                success=False,
                provider_message_id=provider_message_id,
                provider_response={"provider": "mock", "status": "failed", "error": error_msg},
                error_message=error_msg,
                latency_ms=latency_ms,
            )

    async def validate_address(self, address: str) -> bool:
        return bool(address and "@" in address and "." in address.split("@")[-1])
