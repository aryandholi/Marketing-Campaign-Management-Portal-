"""
ChannelConfiguration entity — stores provider credentials and settings per channel.

Each channel (email, SMS, WhatsApp, etc.) can have its own configuration
including API keys, sender identifiers, and provider-specific settings.
"""

from sqlalchemy import String, Boolean, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid
from api.models.campaign import ChannelType


class ChannelConfiguration(Base, TimestampMixin):
    __tablename__ = "channel_configurations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    channel: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType, name="channel_type_config", native_enum=False),
        nullable=False, unique=True, index=True,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="e.g. 'sendgrid', 'twilio', 'vonage'"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Provider Settings ─────────────────────────────────────────────
    api_key_encrypted: Mapped[str] = mapped_column(
        String(1024), nullable=True,
        doc="Encrypted API key for the provider (use KMS in production)"
    )
    sender_identity: Mapped[str] = mapped_column(
        String(255), nullable=True,
        doc="From address for email or sender ID for SMS"
    )
    provider_config: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=dict,
        doc="Provider-specific configuration: {'region': 'us-east-1', 'pool_id': '...'}"
    )
    webhook_url: Mapped[str] = mapped_column(
        String(512), nullable=True,
        doc="Callback URL for delivery status webhooks from the provider"
    )

    def __repr__(self) -> str:
        return f"<ChannelConfiguration(channel={self.channel}, provider={self.provider_name})>"
