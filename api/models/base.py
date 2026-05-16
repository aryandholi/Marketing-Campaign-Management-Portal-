"""
Base model mixin providing common columns for all entities.

Every entity inherits `TimestampMixin` to get automatic
`created_at` and `updated_at` columns.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from api.core.database import Base


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_ulid() -> str:
    """Generate a UUID4-based string ID (placeholder for ULID in production)."""
    return str(uuid.uuid4())


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


# Re-export Base for convenience
__all__ = ["Base", "TimestampMixin", "generate_ulid", "utcnow"]
