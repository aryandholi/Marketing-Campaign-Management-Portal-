"""
CampaignRule entity — configurable rules governing campaign execution.

Supports time-window restrictions, daily sending caps, throttling limits,
and do-not-disturb periods. Designed for future integration with
Redis-backed rate limiting and Celery-based scheduling.
"""

from sqlalchemy import String, Integer, Boolean, Time, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class CampaignRule(Base, TimestampMixin):
    __tablename__ = "campaign_rules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    rule_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="Human-readable rule identifier, e.g. 'business_hours_only'"
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Time Window ───────────────────────────────────────────────────
    send_window_start: Mapped[str] = mapped_column(
        Time, nullable=True,
        doc="Earliest time of day messages can be sent (UTC)"
    )
    send_window_end: Mapped[str] = mapped_column(
        Time, nullable=True,
        doc="Latest time of day messages can be sent (UTC)"
    )

    # ── Rate Limiting ─────────────────────────────────────────────────
    daily_cap: Mapped[int] = mapped_column(
        Integer, nullable=True,
        doc="Maximum messages sent per day for this campaign"
    )
    throttle_per_second: Mapped[int] = mapped_column(
        Integer, nullable=True,
        doc="Max messages dispatched per second (for backpressure)"
    )

    # ── Do Not Disturb ────────────────────────────────────────────────
    dnd_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dnd_config: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=dict,
        doc="DND configuration: {'days': ['saturday','sunday'], 'holidays': ['2025-12-25']}"
    )

    # ── Foreign Keys ──────────────────────────────────────────────────
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────
    campaign = relationship("Campaign", back_populates="rules")

    def __repr__(self) -> str:
        return f"<CampaignRule(id={self.id}, name={self.rule_name}, enabled={self.is_enabled})>"
