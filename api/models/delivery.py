"""
DeliveryAttempt entity — tracks each attempt to send a message.

Records the provider response, latency, and whether the attempt
succeeded or failed, enabling retry and deliverability analytics.
"""

import enum

from sqlalchemy import String, Integer, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class DeliveryStatus(str, enum.Enum):
    """Delivery attempt outcome."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    BOUNCED = "bounced"


class DeliveryAttempt(Base, TimestampMixin):
    __tablename__ = "delivery_attempts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status", native_enum=False),
        nullable=False,
    )
    provider_response: Mapped[dict] = mapped_column(
        JSON, nullable=True,
        doc="Raw response payload from the channel provider (SendGrid, Twilio, etc.)"
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer, nullable=True,
        doc="Round-trip latency to the provider in milliseconds"
    )
    error_message: Mapped[str] = mapped_column(
        String(1024), nullable=True,
        doc="Human-readable error description on failure"
    )

    # ── Foreign Keys ──────────────────────────────────────────────────
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("message_instances.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────
    message = relationship("MessageInstance", back_populates="delivery_attempts")

    def __repr__(self) -> str:
        return f"<DeliveryAttempt(id={self.id}, attempt={self.attempt_number}, status={self.status})>"
