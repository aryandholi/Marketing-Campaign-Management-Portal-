"""
Async SQLAlchemy engine, session factory, and dependency injection.

Uses asyncpg as the database driver connecting to Supabase PostgreSQL.
Provides a `get_db` async generator for FastAPI dependency injection.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from api.core.config import get_settings

settings = get_settings()

# ── Async Engine ──────────────────────────────────────────────────────────
engine_args = {
    "echo": not settings.is_production,
    "pool_pre_ping": True,
}

if not settings.database_url.startswith("sqlite"):
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10

engine = create_async_engine(settings.database_url, **engine_args)

# ── Session Factory ───────────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    FastAPI dependency that yields a database session.

    The session is automatically closed after the request completes,
    with rollback on unhandled exceptions.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. Used for local dev; Supabase migrations are preferred in prod."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
