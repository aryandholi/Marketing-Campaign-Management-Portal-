"""
EngagementEvent entity — tracks recipient interactions with messages.

Supports a wide range of event types and uses a JSONB column
to capture channel-specific event details (e.g., link URL clicked,
button label, page navigated to).
"""

import enum

from sqlalchemy import String, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class EngagementEventType(str, enum.Enum):
    """Types of engagement events tracked by the system."""
    DELIVERED = "delivered"
    OPENED = "opened"
    READ = "read"
    REPLIED = "replied"
    LINK_CLICKED = "link_clicked"
    PAGE_NAVIGATED = "page_navigated"
    BUTTON_CLICKED = "button_clicked"


class EngagementEvent(Base, TimestampMixin):
    __tablename__ = "engagement_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    event_type: Mapped[EngagementEventType] = mapped_column(
        Enum(EngagementEventType, name="engagement_event_type", native_enum=False),
        nullable=False, index=True,
    )
    event_details: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=dict,
        doc="Channel-specific event payload. Examples: "
            "{'link_url': 'https://...', 'user_agent': 'Mozilla/5.0'} for link_clicked, "
            "{'button_label': 'Buy Now', 'page': '/checkout'} for button_clicked"
    )
    source_ip: Mapped[str] = mapped_column(
        String(45), nullable=True,
        doc="IP address of the event origin (for geo-analytics)"
    )
    user_agent: Mapped[str] = mapped_column(
        String(512), nullable=True,
        doc="Browser/client user agent string"
    )

    # ── Foreign Keys ──────────────────────────────────────────────────
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("message_instances.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────
    message = relationship("MessageInstance", back_populates="engagement_events")

    def __repr__(self) -> str:
        return f"<EngagementEvent(id={self.id}, type={self.event_type}, message={self.message_id})>"
