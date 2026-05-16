"""
Campaign entity — the central aggregate for marketing campaigns.

Tracks lifecycle state (draft → active → paused → completed/stopped)
and holds the campaign configuration: channel, template, audience, schedule.
"""

import enum

from sqlalchemy import String, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid, utcnow


class CampaignStatus(str, enum.Enum):
    """Campaign lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ChannelType(str, enum.Enum):
    """Supported delivery channels."""
    EMAIL = "email"
    SMS = "sms"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    channel: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, name="channel_type", native_enum=False),
        nullable=False,
        default=ChannelType.EMAIL,
    )
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(
        Text, nullable=True,
        doc="JSON-encoded audience criteria or comma-separated identifiers"
    )
    schedule_time: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=True,
        doc="Scheduled UTC time for automated campaign dispatch"
    )
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status", native_enum=False),
        nullable=False,
        default=CampaignStatus.DRAFT,
    )

    # ── Owner (no FK constraint — uses mock auth store) ───────────────
    owner_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    recipients = relationship(
        "RecipientList", back_populates="campaign", lazy="selectin", cascade="all, delete-orphan"
    )
    messages = relationship(
        "MessageInstance", back_populates="campaign", lazy="selectin", cascade="all, delete-orphan"
    )
    rules = relationship(
        "CampaignRule", back_populates="campaign", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status})>"
