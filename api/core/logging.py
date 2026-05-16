"""
Structured JSON logging with correlation ID support.

Provides a configured logger that outputs structured JSON lines,
making it easy to parse in cloud logging systems (Vercel, GCP, Datadog).
"""

import logging
import json
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable for per-request correlation IDs
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="no-correlation-id")


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Attach exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Attach extra fields passed via logger.info("msg", extra={...})
        for key in ("request_method", "request_path", "status_code", "duration_ms", "user_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


def get_logger(name: str = "campaign_portal") -> logging.Logger:
    """
    Returns a structured JSON logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("Campaign created", extra={"user_id": "abc-123"})
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


def generate_correlation_id() -> str:
    """Generate a new UUID v4 correlation ID for request tracing."""
    return str(uuid.uuid4())
