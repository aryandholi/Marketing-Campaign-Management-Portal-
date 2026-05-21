# PoC Development Strategy

## 1. Engineering Philosophy and Strategic Scope

The development strategy for the Marketing Campaign Management Portal was driven by a singular objective: to build a **vertically complete Proof of Concept** that demonstrates the full lifecycle of a multi-channel marketing campaign — from user authentication and campaign creation, through audience resolution and message dispatch, to engagement tracking and analytics reporting — within a deployable, production-mimicking architecture. Rather than building a shallow prototype that merely renders static screens, the strategy was to implement every critical backend pipeline with real data persistence, real ORM relationships, real validation logic, and real (or intelligently simulated) channel delivery, so that the system can be evaluated as a genuine engineering artifact rather than a mockup.

The key strategic trade-off was the deliberate use of **in-memory data stores for authentication and contacts** (`MOCK_USERS` in `api/core/auth.py` and `MockContactStore` in `api/services/audience_service.py`) alongside **real SQLAlchemy ORM persistence** for campaigns, messages, delivery attempts, and engagement events. This hybrid approach allowed the system to demonstrate end-to-end data flow through persistent storage while avoiding the operational complexity of user management infrastructure during the PoC phase. Every mock component is annotated with explicit production-path comments (e.g., `"In production, this would query the 'users' table via SQLAlchemy"`) to signal architectural intent.

## 2. Technology Stack Analysis

### Backend: Python/FastAPI Ecosystem

The `requirements.txt` reveals a carefully curated dependency set, each chosen for a specific architectural role:

**`fastapi[standard]`** — The core web framework, selected for its native `async/await` support, automatic OpenAPI documentation generation, and Pydantic-integrated request validation. The `[standard]` extra includes `uvicorn`, `httptools`, and `websockets` for production-grade ASGI serving. FastAPI's dependency injection system (via `Depends()`) is used pervasively throughout the routes layer — `get_current_user` for JWT authentication and `get_db` for database session lifecycle management are injected into every protected endpoint, as visible in routes like `api/routes/campaigns.py` and `api/routes/reports.py`.

**`pydantic` and `pydantic-settings`** — Pydantic v2 is used for two distinct purposes. First, it provides the schema validation layer (`api/schemas/schemas.py`) with 15+ request/response models using `Field` constraints (`min_length`, `max_length`, `ge`, `le`), `model_validator` decorators for cross-field validation (e.g., `validate_channel` ensuring `channel ∈ {"email", "sms"}`, and `validate_event_type` ensuring event types match the `EngagementEventType` enum), and `model_config = {"from_attributes": True}` for seamless ORM-to-schema serialization. Second, `pydantic-settings` powers the centralized `Settings` class in `api/core/config.py`, which uses `SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")` to bind environment variables to typed Python attributes with defaults, computed properties (`smtp_configured`, `twilio_configured`, `cors_origins_list`, `is_production`), and `@lru_cache()` singleton caching via `get_settings()`.

**`sqlalchemy[asyncio]` and `aiosqlite`** — SQLAlchemy 2.0+ with async extensions provides the ORM layer. The `api/core/database.py` module configures the async engine with `create_async_engine()`, applying pool configuration conditionally — `pool_size=5` and `max_overflow=10` are only set for non-SQLite databases, since SQLite doesn't support connection pooling. The `pool_pre_ping=True` setting enables connection health checks. The `async_sessionmaker` is configured with `expire_on_commit=False` to prevent lazy-load issues in async contexts. The `get_db()` dependency generator implements a **commit-on-success, rollback-on-exception** pattern with explicit `finally: await session.close()`.

**`asyncpg`** — Listed as a dependency for the PostgreSQL production path. While the default configuration uses SQLite, the `.env.example` documents the `postgresql+asyncpg://` connection string format for Supabase PostgreSQL, making the production upgrade a configuration-only change.

**`python-jose[cryptography]`** — Provides JWT creation and verification. The `create_access_token()` function in `api/core/auth.py` constructs tokens with a payload containing `sub`, `user_id`, `role`, `exp`, `iat`, and `iss` claims. The `verify_token()` function decodes with algorithm pinning (`algorithms=[settings.jwt_algorithm]`) and validates the `sub` claim presence.

**`passlib[bcrypt]`** — Included for password hashing capability, though the current PoC uses mock credential validation (`authenticate_user()` accepts any non-empty password for known mock users). The presence of this dependency signals the production-ready password hashing infrastructure.

**`google-auth` and `requests`** — Power the Google OAuth 2.0 integration. `verify_google_token()` in `api/core/auth.py` uses `google.oauth2.id_token.verify_oauth2_token()` with `google.auth.transport.requests.Request()` to validate Google ID tokens against Google's public key infrastructure, with the `GOOGLE_CLIENT_ID` configured in settings.

**`aiosmtplib`** — Async SMTP client used by `EmailAdapter._send_real()` in `api/adapters/email_adapter.py` for actual email delivery. It is **lazily imported** inside the `_send_real` method (`import aiosmtplib`) so the module loads even when the package isn't installed — a deliberate decision to prevent import failures when SMTP isn't configured.

**`twilio`** — The Twilio REST SDK used by `SMSAdapter._send_real()` in `api/adapters/sms_adapter.py`. Like `aiosmtplib`, the `twilio.rest.Client` is lazily imported inside `_send_real()` to avoid import errors in environments without Twilio configured.

**`httpx`** — Async HTTP client available for external API communication, though the current PoC primarily uses synchronous Twilio SDK calls. Its inclusion signals preparation for async webhook delivery and external service integration.

### Frontend: Next.js/React Ecosystem

The `package.json` defines a modern React application stack:

**`next` (16.2.6) and `react` (19.2.4)** — The cutting-edge Next.js App Router with React 19. The project uses route groups (`(dashboard)`) for layout composition, with `src/app/(dashboard)/layout.tsx` providing the authenticated shell with sidebar navigation, auth gating, and dynamic page title resolution via the `pageTitles` record.

**`axios` (1.16.1)** — HTTP client wrapped in a centralized `apiClient` singleton (`src/lib/api.ts`) with `baseURL: '/api'`, a 30-second timeout (accommodating serverless cold starts), and request/response interceptors for JWT management and 401 redirect handling.

**`@react-oauth/google` (0.13.5)** — Google Identity Services integration. The `GoogleOAuthProvider` wraps the entire application in `src/app/layout.tsx`, and the `GoogleLogin` component is rendered in `src/app/login/page.tsx` with theme `"filled_black"` and shape `"rectangular"`.

**`recharts` (3.8.1)** — Charting library imported in the dashboard overview page (`src/app/(dashboard)/dashboard/page.tsx`) for data visualization via `AreaChart`, `Area`, `ResponsiveContainer`, and related components.

**`lucide-react` (1.16.0)** — Icon library providing consistent iconography across all UI components (e.g., `Megaphone`, `LayoutDashboard`, `Users`, `Settings`, `Send`, `CheckCircle2`, `AlertTriangle`, `Eye`, `MousePointerClick`).

**`tailwindcss` (v4) with `@tailwindcss/postcss`** — CSS framework with a custom dark theme defined in `src/app/globals.css` using the `@theme` directive for CSS custom properties. A custom `glassmorphism` utility class (`background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px)`) is defined in an `@layer utilities` block for the premium frosted-glass UI aesthetic.

**`clsx` and `tailwind-merge`** — Utility libraries for conditional CSS class composition, used extensively in the `Sidebar` component for active-state styling.

**`date-fns` (4.1.0)** — Date formatting library available for timestamp display across campaign and event views.

## 3. Development Environment and Deployment Configuration

### Local Development Workflow

The development environment is designed for **dual-process execution**: the Next.js dev server on port 3000 (`npm run dev`) and the FastAPI server on port 8000 (via `uvicorn`). The `next.config.ts` conditionally applies API proxy rewrites only in development mode:

```typescript
const isDev = process.env.NODE_ENV === "development";
// In development, proxy /api/* to the local FastAPI server on port 8000.
...(isDev && {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
  },
}),
```

This allows the frontend to make relative API calls to `/api/*` regardless of environment, with the routing layer handling the appropriate destination.

### Production Deployment (Vercel)

The `vercel.json` configures a single rewrite rule that routes all API traffic to the Python serverless function:

```json
{ "rewrites": [{ "source": "/api/(.*)", "destination": "/api/index.py" }] }
```

The FastAPI application factory in `api/index.py` handles CORS configuration dynamically, building the origins list from `settings.cors_origins_list` and toggling between wildcard and explicit origin modes. The `allow_credentials` flag is automatically set to `not allow_all` to comply with CORS specification requirements (credentials cannot be used with wildcard origins).

### Environment Configuration

The `.env.example` file documents all 17 configurable environment variables organized into six categories: Database, JWT, Application, Google OAuth, SMTP Email, and Twilio SMS. The `Settings` class applies sensible defaults for every variable, enabling zero-configuration local startup with SQLite, mock authentication, and simulated channel delivery.

## 4. Engineering Mechanisms for Robustness

### Structured JSON Logging with Correlation IDs

The `api/core/logging.py` module implements a `StructuredJsonFormatter` that outputs log records as single-line JSON objects containing `timestamp`, `level`, `logger`, `message`, `correlation_id`, `module`, `function`, and `line` fields. Additional contextual fields (`request_method`, `request_path`, `status_code`, `duration_ms`, `user_id`) are dynamically attached via the `extra` parameter. The `correlation_id` is propagated using Python's `contextvars.ContextVar`, set by the `request_logging_middleware` in `api/index.py` at the start of each request. This middleware also captures request duration using `time.monotonic()` and writes both the correlation ID (`X-Correlation-ID`) and duration (`X-Request-Duration-Ms`) to response headers for client-side distributed tracing.

### Centralized Exception Handling

The `api/core/exceptions.py` module defines a four-level exception hierarchy rooted at `CampaignPortalError`, with domain-specific subclasses `EntityNotFoundError` (404), `InvalidStateTransitionError` (409), `AudienceResolutionError` (422), and `ChannelNotSupportedError` (400). The `register_exception_handlers()` function installs three FastAPI exception handlers:

1. `CampaignPortalError` → Returns structured JSON with `error.code`, `error.message`, and `error.correlation_id`
2. `RequestValidationError` → Returns 422 with `error.details` containing Pydantic validation errors
3. `Exception` (catch-all) → Returns 500 with generic message, logs full traceback with `exc_info=True`

Every error response includes the current `correlation_id` from the context variable, enabling end-to-end request tracing across error boundaries.

### Dual-Mode Channel Adapters

Both `EmailAdapter` and `SMSAdapter` implement a **real-or-mock duality** pattern. Each adapter's `send()` method checks `settings.smtp_configured` (or `settings.twilio_configured`) at call time — not at import time — to decide whether to route to `_send_real()` or `_send_mock()`. This allows runtime switching of delivery modes via the Settings API endpoints (`POST /api/settings/smtp` and `POST /api/settings/twilio`), which directly mutate the cached `Settings` singleton's attributes. The mock modes use `random.random()` against configurable success rates (95% for email, 90% for SMS as defined by `SMS_SUCCESS_RATE = 0.90`) and simulate realistic failure scenarios with error messages like `"Mailbox full"`, `"Invalid domain"`, `"Provider timeout"`, `"Carrier rejected message"`, and `"Number is on DNC list"`.

### Database Session Lifecycle

The `get_db()` dependency generator in `api/core/database.py` implements a defensive session lifecycle:

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

This guarantees that every request gets its own session scope with automatic commit on success, rollback on any exception, and session closure regardless of outcome — preventing connection leaks in the serverless environment.

### Request Validation at Multiple Layers

Input validation is enforced at three levels: (1) Pydantic `Field` constraints for primitive type/length/range validation, (2) `model_validator` decorators for cross-field business rules, and (3) service-layer validation (e.g., `CampaignService.update()` rejecting edits to non-DRAFT campaigns, `EventService.ingest_event()` verifying message existence before accepting events). This defense-in-depth approach ensures that invalid data is rejected at the earliest possible boundary.

## 5. Data Seeding and Testing Strategy

The `seed_data.py` script provides a programmatic mechanism for populating the `MockContactStore` with additional test contacts beyond the five pre-seeded entries. It registers each contact under three lookup keys (email, phone, username) to demonstrate the multi-key resolution capability of the audience service.

The `test_e2e.py` script implements a sequential integration test using Python's `urllib.request` module (no external test framework dependency), exercising the complete happy path: login → create contact → create campaign → start campaign → dispatch campaign. This script serves as both a smoke test and a living documentation of the API contract.
