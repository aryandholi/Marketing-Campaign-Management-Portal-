"""
MessageInstance entity — individual rendered message per recipient.

Each message is a concrete instantiation of the campaign template
personalized for a specific contact.
"""

import enum

from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class MessageStatus(str, enum.Enum):
    """Message lifecycle states."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class MessageInstance(Base, TimestampMixin):
    __tablename__ = "message_instances"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    rendered_content: Mapped[str] = mapped_column(
        Text, nullable=False,
        doc="The final rendered message content after template interpolation"
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status", native_enum=False),
        nullable=False,
        default=MessageStatus.PENDING,
    )
    recipient_address: Mapped[str] = mapped_column(
        String(255), nullable=False,
        doc="Resolved email address or phone number for delivery"
    )

    # ── Foreign Keys ──────────────────────────────────────────────────
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────
    campaign = relationship("Campaign", back_populates="messages")
    delivery_attempts = relationship(
        "DeliveryAttempt", back_populates="message", lazy="selectin", cascade="all, delete-orphan"
    )
    engagement_events = relationship(
        "EngagementEvent", back_populates="message", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MessageInstance(id={self.id}, status={self.status}, to={self.recipient_address})>"
