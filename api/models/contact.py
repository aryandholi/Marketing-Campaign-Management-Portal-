"""
ContactProfile entity — represents target audience members.

A contact can have multiple communication channels (email, phone, etc.)
and optional metadata stored as JSONB for extensibility.
"""

from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base
from api.models.base import TimestampMixin, generate_ulid


class ContactProfile(Base, TimestampMixin):
    __tablename__ = "contact_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_ulid
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=True, index=True
    )
    phone: Mapped[str] = mapped_column(
        String(20), nullable=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=dict,
        doc="Extensible JSONB field for channel-specific contact attributes"
    )


    def __repr__(self) -> str:
        return f"<ContactProfile(id={self.id}, username={self.username}, email={self.email})>"
