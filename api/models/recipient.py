"""
RecipientList entity — junction table linking Campaigns to ContactProfiles.

Each row represents one recipient in a campaign's target audience.
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class RecipientList(Base, TimestampMixin):
    __tablename__ = "recipient_lists"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )

    # ── Foreign Keys ──────────────────────────────────────────────────
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # ── Relationships ─────────────────────────────────────────────────
    campaign = relationship("Campaign", back_populates="recipients")

    def __repr__(self) -> str:
        return f"<RecipientList(campaign={self.campaign_id}, contact={self.contact_id})>"
