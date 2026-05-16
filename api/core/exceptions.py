"""
Custom exception classes and centralized FastAPI exception handlers.

Provides domain-specific exceptions and handlers that return
consistent, structured JSON error responses with correlation IDs.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.core.logging import get_logger, correlation_id_ctx

logger = get_logger(__name__)


# ── Domain Exceptions ─────────────────────────────────────────────────────

class CampaignPortalError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class EntityNotFoundError(CampaignPortalError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            status_code=404,
            error_code="ENTITY_NOT_FOUND",
        )


class InvalidStateTransitionError(CampaignPortalError):
    """Raised when a campaign lifecycle transition is invalid."""

    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Cannot transition from '{current_status}' to '{target_status}'",
            status_code=409,
            error_code="INVALID_STATE_TRANSITION",
        )


class AudienceResolutionError(CampaignPortalError):
    """Raised when audience resolution fails or yields zero contacts."""

    def __init__(self, message: str = "Failed to resolve audience to valid contacts"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="AUDIENCE_RESOLUTION_FAILED",
        )


class ChannelNotSupportedError(CampaignPortalError):
    """Raised when an unsupported delivery channel is requested."""

    def __init__(self, channel: str):
        super().__init__(
            message=f"Channel '{channel}' is not supported. Supported: email, sms",
            status_code=400,
            error_code="CHANNEL_NOT_SUPPORTED",
        )


# ── Exception Handlers ───────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom and built-in exception handlers on the app."""

    @app.exception_handler(CampaignPortalError)
    async def campaign_portal_error_handler(request: Request, exc: CampaignPortalError) -> JSONResponse:
        correlation_id = correlation_id_ctx.get()
        logger.error(
            f"Domain error: {exc.error_code} - {exc.message}",
            extra={"request_path": str(request.url), "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "correlation_id": correlation_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = correlation_id_ctx.get()
        logger.warning(
            f"Validation error on {request.method} {request.url.path}",
            extra={"request_path": str(request.url)},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "correlation_id": correlation_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = correlation_id_ctx.get()
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={"request_path": str(request.url), "status_code": 500},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again or contact support.",
                    "correlation_id": correlation_id,
                }
            },
        )
