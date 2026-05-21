# Evaluation, Refinement, and Edge Case Handling

## 1. Defense-in-Depth Error Handling Architecture

The system implements a **four-tier error handling architecture** that intercepts failures at progressively higher abstraction levels, ensuring that no exception — whether from database operations, external provider APIs, or malformed user input — can surface as an unstructured error or crash the application. This architecture was designed to be the last line of defense in a serverless environment where each function invocation is isolated and cannot rely on a persistent supervisor process for recovery.

### Tier 1: Domain Exception Hierarchy

The `api/core/exceptions.py` module defines a purpose-built exception taxonomy rooted at `CampaignPortalError`, which carries three structured fields: `message` (human-readable description), `status_code` (HTTP status), and `error_code` (machine-readable classification string). Each subclass maps to a specific domain failure mode:

**`EntityNotFoundError`** (status 404, code `ENTITY_NOT_FOUND`) — Raised by `CampaignService.get_by_id()` when `select(Campaign).where(Campaign.id == campaign_id)` returns `scalar_one_or_none() → None`. The exception message is dynamically constructed: `f"{entity_type} with id '{entity_id}' not found"`, providing context-specific error messages for any entity type. This same pattern is replicated in `EventService.ingest_event()` for `MessageInstance` lookups and in `ReportingService.get_campaign_metrics()` for campaign existence verification.

**`InvalidStateTransitionError`** (status 409, code `INVALID_STATE_TRANSITION`) — Raised by `CampaignService.transition_status()` when the requested target status is not in the `VALID_TRANSITIONS[current_status]` set. This prevents illegal lifecycle transitions such as attempting to pause a completed campaign or editing an active campaign (the `update()` method checks `campaign.status != CampaignStatus.DRAFT` and raises this error with a custom message: `"edit (only DRAFT campaigns can be edited)"`). The 409 Conflict status code was chosen deliberately to signal that the request is well-formed but conflicts with the current resource state.

**`AudienceResolutionError`** (status 422, code `AUDIENCE_RESOLUTION_FAILED`) — Raised at two distinct points in `OrchestrationService.send_campaign()`: first when no audience is specified (`"No audience specified for campaign"`), and second when resolution yields zero contacts (`f"No contacts resolved from {len(identifiers)} identifiers"`). This prevents the dispatch pipeline from proceeding with an empty recipient list, which would result in a misleading success response with zero messages sent.

**`ChannelNotSupportedError`** (status 400, code `CHANNEL_NOT_SUPPORTED`) — Raised by `ChannelAdapterFactory.get_adapter()` when the requested channel string does not match any registered adapter in the `_registry`. The error message explicitly lists supported channels: `f"Channel '{channel}' is not supported. Supported: email, sms"`.

### Tier 2: Centralized Exception Handlers

The `register_exception_handlers()` function in `api/core/exceptions.py` installs three exception handlers on the FastAPI application instance:

**Handler 1 — `CampaignPortalError` handler:** Catches all domain exceptions and returns a structured JSON response:

```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Campaign with id 'abc-123' not found",
    "correlation_id": "e7b3f8a2-..."
  }
}
```

The `correlation_id` is extracted from the `correlation_id_ctx` context variable, enabling the caller to reference the exact request in server logs. The handler logs the error with structured fields including `request_path` and `status_code`.

**Handler 2 — `RequestValidationError` handler:** Intercepts Pydantic validation failures from FastAPI's automatic request parsing. Returns a 422 response with the full validation error details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [{"loc": ["body", "channel"], "msg": "Channel must be 'email' or 'sms'", "type": "value_error"}],
    "correlation_id": "..."
  }
}
```

This handler logs the error at `WARNING` level (not `ERROR`) since validation failures are expected operational events, not system faults.

**Handler 3 — Catch-all `Exception` handler:** The ultimate safety net. Catches any unhandled exception, logs the full traceback with `exc_info=True` at `ERROR` level, and returns a generic 500 response:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again or contact support.",
    "correlation_id": "..."
  }
}
```

This handler deliberately obscures the internal error details in the response (preventing information leakage) while preserving the full diagnostic information in the server logs, indexed by the correlation ID.

### Tier 3: Adapter-Level Error Isolation

Both `EmailAdapter` and `SMSAdapter` implement **per-delivery error containment** that prevents a single failed send from aborting the entire campaign dispatch. In `EmailAdapter._send_real()`, the actual SMTP call is wrapped in a `try/except Exception` block:

```python
try:
    import aiosmtplib
    await aiosmtplib.send(msg, hostname=settings.smtp_host, ...)
    return DeliveryResult(success=True, ...)
except Exception as exc:
    latency_ms = int((time.monotonic() - start) * 1000)
    error_msg = str(exc)
    logger.error(f"[EmailAdapter] SMTP delivery failed to {recipient_address}: {error_msg}", ...)
    return DeliveryResult(success=False, error_message=error_msg, ...)
```

Critically, this handler **does not re-raise** the exception. It converts the failure into a `DeliveryResult(success=False)` with the error message captured in `error_message` and the raw provider response in `provider_response`. This allows the `OrchestrationService.send_campaign()` loop to continue processing remaining recipients even when individual deliveries fail. The same pattern is implemented in `SMSAdapter._send_real()` for Twilio API errors.

This design ensures **graceful degradation**: a campaign with 100 recipients where 3 fail due to SMTP timeouts will still deliver to the remaining 97, with all 100 delivery attempts fully recorded in the database.

### Tier 4: Database Transaction Safety

The `get_db()` dependency in `api/core/database.py` implements a **commit-on-success, rollback-on-exception** pattern:

```python
async with async_session_factory() as session:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

This ensures that if any exception propagates during a request (including exceptions raised by the exception handlers themselves), all database modifications within that request are rolled back atomically. The `finally: await session.close()` guarantees connection pool cleanup even in catastrophic failure scenarios — critical for preventing connection exhaustion in a serverless environment where connections are a scarce resource.

## 2. Input Validation and Data Integrity Safeguards

### Pydantic Schema Validation

The `api/schemas/schemas.py` module implements **multi-layer input validation** using Pydantic v2's constraint system:

**Field-level constraints:**
- `CampaignCreate.name`: `min_length=1, max_length=255` — prevents empty names and database overflow
- `CampaignCreate.message_template`: `min_length=1` — prevents campaigns with empty templates
- `LoginRequest.password`: `min_length=1` — enforces non-empty password requirement
- `AudienceResolveRequest.identifiers`: `min_length=1` — prevents empty audience resolution requests
- `SMTPSettings.smtp_port`: `ge=1, le=65535` — enforces valid TCP port range
- Campaign list pagination: `limit: int = Query(50, ge=1, le=100)` and `offset: int = Query(0, ge=0)` in `api/routes/campaigns.py`

**Cross-field validators:**
- `CampaignCreate.validate_channel()`: `@model_validator(mode="after")` that raises `ValueError("Channel must be 'email' or 'sms'")` if the channel is not in the allowed set
- `EngagementEventCreate.validate_event_type()`: `@model_validator(mode="after")` that validates the event type against the set `{"delivered", "opened", "read", "replied", "link_clicked", "page_navigated", "button_clicked"}`

### Service-Layer Business Rule Enforcement

Beyond schema validation, the service layer enforces business rules that depend on database state:

**Campaign edit guard:** `CampaignService.update()` checks `campaign.status != CampaignStatus.DRAFT` before applying updates, raising `InvalidStateTransitionError` if the campaign has already been activated. This prevents data corruption where a campaign's template is modified after messages have already been rendered and dispatched.

**State machine enforcement:** `CampaignService.transition_status()` validates every transition against the `VALID_TRANSITIONS` dictionary, preventing invalid lifecycle jumps. The state machine defines `COMPLETED` and `STOPPED` as terminal states with empty transition sets, making them permanently immutable.

**Audience existence validation:** `OrchestrationService.send_campaign()` raises `AudienceResolutionError` if `audience_result.total_resolved == 0`, preventing zero-recipient dispatch operations.

**Message existence validation:** `EventService.ingest_event()` executes `select(MessageInstance).where(MessageInstance.id == data.message_id)` and raises `EntityNotFoundError` if the message doesn't exist, preventing orphaned engagement events.

**Contact address validation:** `OrchestrationService.send_campaign()` checks `self._get_recipient_address(contact_dict, channel)` for each contact, skipping contacts without the appropriate address type (e.g., a contact without an email address is skipped for email campaigns) and incrementing `total_failed`.

### Frontend-Side Validation

The contacts creation route (`api/routes/contacts.py`) implements a manual email format validation (`"@" not in data.email or "." not in data.email.split("@")[-1]`) that returns 422 for invalid email addresses. Each adapter also provides a `validate_address()` method: `EmailAdapter` checks for `@` and a `.` in the domain, while `SMSAdapter` strips formatting characters and validates digit-only content with length constraints (7–15 digits).

## 3. Mock Mode Simulation Fidelity

The mock delivery modes in both adapters are designed to **simulate realistic production behavior**, not just return hardcoded success responses:

**Realistic latency simulation:** Mock deliveries inject `random.randint(50, 300)` milliseconds of simulated latency for email and `random.randint(30, 200)` for SMS, approximating real provider response times.

**Probabilistic failure injection:** Email mock uses a 95% success rate (`random.random() < 0.95`) and SMS uses 90% (`random.random() < SMS_SUCCESS_RATE` where `SMS_SUCCESS_RATE = 0.90`). These rates were chosen to reflect realistic deliverability metrics — SMS has inherently lower deliverability due to carrier filtering and number portability issues.

**Diverse failure scenarios:** Failed mock deliveries select from provider-realistic error messages:
- Email: `["Mailbox full", "Invalid domain", "Provider timeout"]`
- SMS: `["Invalid phone number format", "Carrier rejected message", "Number is on DNC list", "Provider timeout", "Insufficient account balance"]`

This ensures that the analytics and reporting pipeline receives a **representative distribution** of success and failure events during demonstration, rather than showing unrealistic 100% delivery rates.

## 4. Observability and Debugging Infrastructure

### Structured Logging

The `StructuredJsonFormatter` in `api/core/logging.py` ensures every log record is a **machine-parseable JSON line** containing:
- `timestamp`: UTC ISO 8601
- `level`: Python log level name
- `logger`: Module-qualified logger name
- `message`: Human-readable description
- `correlation_id`: Request-scoped UUID from `correlation_id_ctx`
- `module`, `function`, `line`: Source location
- Optional: `request_method`, `request_path`, `status_code`, `duration_ms`, `user_id`
- Optional: `exception`: Full traceback string (attached when `exc_info=True`)

### Request-Level Observability

The `request_logging_middleware` in `api/index.py` provides comprehensive per-request instrumentation:

1. Generates a UUID4 correlation ID at request start
2. Logs request entry: `"→ GET /api/campaigns"` with method and path
3. Measures duration using `time.monotonic()` (monotonic clock, immune to wall-clock adjustments)
4. Logs request completion: `"← GET /api/campaigns [200] 12.34ms"` with status and duration
5. Writes `X-Correlation-ID` and `X-Request-Duration-Ms` response headers

This provides a **complete request lifecycle trace** without requiring external APM tooling, suitable for debugging in Vercel's serverless log viewer.

### Adapter-Level Telemetry

Both real and mock adapters capture `latency_ms` using `time.monotonic()` measurements and include it in the `DeliveryResult`. This data flows into the `DeliveryAttempt.latency_ms` column, enabling latency analysis per provider. The adapters also log structured entries with `request_method: "SEND"` and `request_path: f"smtp:{recipient_address}"` or `f"sms:{recipient_address}"`, creating a searchable log trail of all delivery operations.

## 5. Configuration Resilience and Runtime Adaptability

### Dynamic Channel Configuration

The Settings API endpoints (`POST /api/settings/smtp` and `POST /api/settings/twilio` in `api/routes/settings.py`) allow **runtime reconfiguration** of channel credentials without redeployment. The implementation directly mutates the `lru_cache`-cached `Settings` singleton:

```python
settings = get_settings()
settings.smtp_host = data.smtp_host
settings.smtp_port = data.smtp_port
# ... etc
```

Each adapter checks `settings.smtp_configured` (or `settings.twilio_configured`) **at send time** (inside the `send()` method), not at initialization time. These computed properties use `bool()` checks against all required credential fields:

```python
@property
def smtp_configured(self) -> bool:
    return bool(self.smtp_host and self.smtp_username 
                and self.smtp_password and self.smtp_from_email)
```

This design allows a **seamless transition from mock to real delivery** during a live demo: start with simulated sends, configure SMTP via the Settings UI, and subsequent sends will use real SMTP delivery — without restarting the application.

### Channel Status Endpoint

The `GET /api/settings/channels/status` endpoint provides a programmatic way to query the current configuration state, returning:

```json
{
  "email_configured": true,
  "sms_configured": false,
  "email_provider": "smtp",
  "sms_provider": "mock"
}
```

The frontend can use this to display configuration status indicators and guide the user to configure missing channels.

### Environment-Aware Defaults

The `Settings` class provides safe defaults for every configuration value:
- `database_url`: Falls back to SQLite (`"sqlite+aiosqlite:///./campaign_portal.db"`)
- `jwt_secret_key`: Development placeholder (annotated with production guidance)
- `cors_origins`: Defaults to `"*"` (with production-hardening via env var)
- All SMTP/Twilio fields: Default to empty strings, causing `smtp_configured` / `twilio_configured` to return `False` and triggering mock mode

The `extra="ignore"` setting in `SettingsConfigDict` prevents the application from crashing when unknown environment variables are present — a critical property for Vercel deployments where system-injected variables (`VERCEL_*`, `CI`, etc.) would otherwise trigger Pydantic validation errors.

## 6. End-to-End Testing and Verification

The `test_e2e.py` script implements a **sequential integration test** that exercises the complete happy path without external testing frameworks:

1. **Authentication:** `POST /api/auth/login` with `{"email": "admin@campaignportal.io", "password": "test"}` — validates token issuance
2. **Contact Registration:** `POST /api/contacts` with a test contact — validates contact creation and deduplication
3. **Campaign Creation:** `POST /api/campaigns` with template `"Hello {{first_name}}, this is a real test."` — validates campaign persistence
4. **Campaign Activation:** `POST /api/campaigns/{id}/start` — validates state machine transition (DRAFT → ACTIVE)
5. **Campaign Dispatch:** `POST /api/campaigns/{id}/send` — validates the complete orchestration pipeline

Each step uses `urllib.request.Request` (zero external dependencies) and checks for successful HTTP responses. The test serves as both a **smoke test** for local development verification and a **living documentation** of the API contract, demonstrating the exact request payloads and sequence required for end-to-end campaign execution.

The `seed_data.py` script complements this by providing a **deterministic data seeding mechanism** that populates the `MockContactStore` with 10 contacts (5 pre-seeded + 5 additional), each indexed by email, phone, and username. This ensures a consistent, reproducible test environment.

## 7. Architectural Safeguards Summary

| Safeguard | Implementation Location | What It Prevents |
|---|---|---|
| State machine enforcement | `CampaignService.transition_status()` | Illegal lifecycle transitions |
| Draft-only editing | `CampaignService.update()` | Post-activation template modification |
| Empty audience guard | `OrchestrationService.send_campaign()` | Zero-recipient dispatch operations |
| Per-delivery error isolation | `EmailAdapter._send_real()`, `SMSAdapter._send_real()` | Single failure aborting batch dispatch |
| Transaction rollback | `get_db()` in `database.py` | Partial data corruption on errors |
| Correlation ID propagation | `request_logging_middleware` | Untraceable errors in serverless logs |
| Catch-all exception handler | `unhandled_exception_handler()` | Unstructured error responses to clients |
| Channel validation | `CampaignCreate.validate_channel()` | Unsupported channel in campaign creation |
| Event type validation | `EngagementEventCreate.validate_event_type()` | Invalid engagement event ingestion |
| Address-type guard | `OrchestrationService._get_recipient_address()` | Sending email to phone-only contacts |
| Mock mode fallback | `EmailAdapter.send()`, `SMSAdapter.send()` | Service failure when providers aren't configured |
| Lazy dependency import | `import aiosmtplib`, `from twilio.rest import Client` | Import errors when optional packages are missing |
