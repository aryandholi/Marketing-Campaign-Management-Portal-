"""
FastAPI Application Entry Point — adapted for Vercel Serverless Functions.

This module creates and configures the FastAPI application instance:
- Mounts all API routers (auth, campaigns, contacts, events, reports, settings)
- Registers centralized exception handlers
- Configures CORS middleware
- Adds request logging middleware with correlation IDs
- Provides a health check endpoint

Vercel deploys this as a serverless function via the `app` variable.
"""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.core.exceptions import register_exception_handlers
from api.core.logging import (
    get_logger,
    generate_correlation_id,
    correlation_id_ctx,
)
from api.schemas.schemas import HealthResponse

# ── Import Routers ────────────────────────────────────────────────────────
from api.routes.auth import router as auth_router
from api.routes.campaigns import router as campaigns_router
from api.routes.contacts import router as contacts_router
from api.routes.events import router as events_router
from api.routes.reports import router as reports_router
from api.routes.settings import router as settings_router

settings = get_settings()
logger = get_logger("campaign_portal")

# ═══════════════════════════════════════════════════════════════════════════
# Application Factory
# ═══════════════════════════════════════════════════════════════════════════
from contextlib import asynccontextmanager
from api.core.database import init_db
# Import all ORM models so SQLAlchemy metadata is fully populated before
# create_all is called during startup.
import api.models  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup (create tables if they don't exist)
    await init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Marketing Campaign Management Portal",
    description=(
        "A production-grade API for managing multi-channel marketing campaigns. "
        "Supports campaign lifecycle management, audience resolution, "
        "notification orchestration, and engagement analytics.\n\n"
        "**Demo Credentials:**\n"
        "- Email: `admin@campaignportal.io` / Password: `any non-empty value`\n"
        "- Email: `marketer@campaignportal.io` / Password: `any non-empty value`"
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ═══════════════════════════════════════════════════════════════════════════
# Middleware
# ═══════════════════════════════════════════════════════════════════════════

# Build CORS origins list — always include localhost for dev
cors_origins = settings.cors_origins_list
# Wildcard support: if "*" is in the list, allow all origins
allow_all = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins,
    allow_credentials=not allow_all,  # credentials can't be used with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Middleware that:
    1. Generates and sets a correlation ID for distributed tracing
    2. Logs request start/end with method, path, status, and duration
    3. Adds correlation ID to response headers
    """
    correlation_id = generate_correlation_id()
    correlation_id_ctx.set(correlation_id)

    start_time = time.monotonic()

    logger.info(
        f"→ {request.method} {request.url.path}",
        extra={
            "request_method": request.method,
            "request_path": request.url.path,
        },
    )

    response = await call_next(request)

    duration_ms = round((time.monotonic() - start_time) * 1000, 2)

    logger.info(
        f"← {request.method} {request.url.path} [{response.status_code}] {duration_ms}ms",
        extra={
            "request_method": request.method,
            "request_path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    # Attach correlation ID to response for client-side tracing
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-Duration-Ms"] = str(duration_ms)

    return response


# ═══════════════════════════════════════════════════════════════════════════
# Exception Handlers
# ═══════════════════════════════════════════════════════════════════════════

register_exception_handlers(app)


# ═══════════════════════════════════════════════════════════════════════════
# Router Registration
# ═══════════════════════════════════════════════════════════════════════════

app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(contacts_router)
app.include_router(events_router)
app.include_router(reports_router)
app.include_router(settings_router)


# ═══════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint",
)
async def health_check():
    """
    Returns the application health status, version, and environment.
    Used by Vercel and external monitoring to verify deployment health.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.app_env,
    )


@app.get(
    "/",
    tags=["System"],
    summary="Root endpoint",
)
async def root():
    """Root endpoint returning API information and links."""
    return {
        "name": "Marketing Campaign Management Portal",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs",
        "health": "/api/health",
        "endpoints": {
            "auth": "/api/auth/login",
            "campaigns": "/api/campaigns",
            "contacts": "/api/contacts",
            "events": "/api/events",
            "reports": "/api/reports/campaigns/{campaign_id}",
            "settings": "/api/settings/channels/status",
        },
    }
