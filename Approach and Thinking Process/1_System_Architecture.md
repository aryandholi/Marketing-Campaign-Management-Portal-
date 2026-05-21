# System Architecture

## 1. Architectural Vision and Design Philosophy

The Marketing Campaign Management Portal (referred to throughout the codebase as "Nexus Portal") is architected as a **full-stack, real-time capable campaign orchestration platform** that follows a strict separation of concerns between a Next.js 16 frontend presentation layer and a FastAPI asynchronous backend API layer. The fundamental architectural decision — and one that distinguishes this PoC from trivial CRUD applications — is the design of a **pipeline-oriented orchestration engine** that decomposes the campaign dispatch lifecycle into discrete, composable stages: audience resolution, template rendering, channel-specific delivery, and engagement event ingestion. Each of these stages is implemented as an isolated service module with well-defined contracts, enabling any single stage to be replaced, scaled, or enhanced independently without disrupting the overall system flow.

The system was explicitly designed for **Vercel serverless deployment**. The `vercel.json` configuration routes all `/api/(.*)` requests to `api/index.py`, which serves as the singular Python serverless function entry point. This monolithic-function-with-internal-modularity pattern is a deliberate architectural trade-off: it allows the backend to maintain a rich, layered internal architecture (routes → services → adapters → models) while conforming to Vercel's serverless execution model where each invocation is stateless and isolated. The Next.js frontend is simultaneously built and deployed from the same repository, with `next.config.ts` conditionally applying development-time API proxy rewrites (`/api/:path*` → `http://127.0.0.1:8000/api/:path*`) only when `NODE_ENV === "development"`, ensuring seamless local development while requiring zero configuration changes for production.

## 2. High-Level Data Flow: User Input to Final Output

The end-to-end data flow through the system follows a clearly defined path that can be traced through the codebase:

**Authentication Flow:** A user initiates interaction at the `src/app/login/page.tsx` login page, which supports dual authentication mechanisms. The email/password path issues a `POST /api/auth/login` request handled by `api/routes/auth.py`, which delegates to the `authenticate_user()` function in `api/core/auth.py`. This function validates credentials against the `MOCK_USERS` in-memory dictionary — a deliberate PoC simplification documented with clear production-path annotations. Upon successful authentication, `create_access_token()` mints a JWT with claims `sub` (email), `user_id`, `role`, `exp`, `iat`, and `iss` (hardcoded as `"campaign-portal-api"`), signed using the `HS256` algorithm against `settings.jwt_secret_key`. The Google OAuth path (`POST /api/auth/google`) uses the `google.oauth2.id_token.verify_oauth2_token()` function to validate the Google ID token against the configured `GOOGLE_CLIENT_ID`, with an **auto-registration** mechanism that dynamically adds new Google users to `MOCK_USERS` on first login.

**Campaign Creation Flow:** The authenticated frontend stores the JWT in `localStorage` (managed via the Axios interceptor in `src/lib/api.ts`) and navigates to the dashboard. When creating a campaign, the `CampaignCreate` Pydantic schema in `api/schemas/schemas.py` validates input with constraints including `min_length=1` for `name`, a `model_validator` that enforces `channel ∈ {"email", "sms"}`, and field-level constraints on `message_template`. The validated payload reaches `CampaignService.create()` in `api/services/campaign_service.py`, which instantiates a `Campaign` ORM entity (defined in `api/models/campaign.py`) in `CampaignStatus.DRAFT` state.

**Campaign Dispatch Pipeline:** The critical path begins when `POST /api/campaigns/{campaign_id}/send` is invoked. The route in `api/routes/campaigns.py` instantiates `OrchestrationService` (from `api/services/orchestration_service.py`), which executes a four-stage pipeline:

1. **Audience Resolution** — `AudienceService.resolve()` in `api/services/audience_service.py` accepts mixed identifiers (emails, phone numbers, usernames), classifies each via regex-based heuristics (`EMAIL_REGEX`, `PHONE_REGEX`), and resolves them against `MockContactStore` — a multi-keyed in-memory dictionary that indexes contacts by email, phone, and username simultaneously. The resolution engine deduplicates by `contact_id` using a `seen_ids` set and returns an `AudienceResolveResponse` containing both resolved contacts and unresolved identifiers.

2. **Channel Adapter Selection** — `ChannelAdapterFactory.get_adapter()` in `api/adapters/factory.py` implements the **Factory Pattern** with a static `_registry` dictionary mapping channel names to adapter classes. The factory currently registers `EmailAdapter` and `SMSAdapter`, but includes a `register_adapter()` class method for runtime extension.

3. **Template Rendering & Message Dispatch** — For each resolved contact, `OrchestrationService._render_template()` performs `{{placeholder}}` token substitution using a deterministic loop over `("first_name", "last_name", "email", "phone", "username")`. The rendered message is persisted as a `MessageInstance` entity, then dispatched through the selected adapter. Each adapter returns a standardized `DeliveryResult` dataclass (defined in `api/adapters/base.py`) containing `success`, `provider_message_id`, `provider_response`, `error_message`, and `latency_ms`.

4. **Result Recording** — A `DeliveryAttempt` entity is created for each send operation, capturing the provider response payload, latency measurement, and delivery status. The `MessageInstance.status` is updated to either `MessageStatus.DELIVERED` or `MessageStatus.FAILED` based on the adapter result.

**Engagement Tracking Flow:** External providers (or manual webhook calls) send engagement events to `POST /api/events` (handled by `api/routes/events.py`), which is deliberately unauthenticated to accommodate third-party webhook callbacks. The `EventService.ingest_event()` method in `api/services/event_service.py` validates the referenced `message_id` exists, maps the string `event_type` to the `EngagementEventType` enum via the `EVENT_TYPE_MAP` dictionary, and persists an `EngagementEvent` entity with optional `event_details` (JSON), `source_ip`, and `user_agent`.

**Reporting Flow:** `ReportingService.get_campaign_metrics()` in `api/services/reporting_service.py` executes complex SQL aggregate queries using SQLAlchemy's `func.count()` with `case()` expressions to compute metrics across `MessageInstance`, `DeliveryAttempt`, and `EngagementEvent` tables in a single database round-trip. Derived rates (`delivery_rate`, `open_rate`, `click_rate`) are computed server-side with division-by-zero guards.

## 3. Module Architecture and Isolation Strategy

The backend is organized into six strictly isolated module boundaries, each enforcing single-responsibility:

| Module | Location | Responsibility |
|---|---|---|
| **Core** | `api/core/` | Cross-cutting concerns: configuration (`config.py`), database engine (`database.py`), authentication (`auth.py`), structured logging (`logging.py`), exception hierarchy (`exceptions.py`) |
| **Models** | `api/models/` | SQLAlchemy ORM entities: `Campaign`, `MessageInstance`, `DeliveryAttempt`, `EngagementEvent`, `RecipientList`, `CampaignRule`, `ChannelConfiguration`, `ContactProfile`, `User` |
| **Schemas** | `api/schemas/` | Pydantic v2 request/response models with `model_config = {"from_attributes": True}` for ORM-mode serialization |
| **Services** | `api/services/` | Business logic layer: `CampaignService` (CRUD + state machine), `AudienceService` (resolution engine), `OrchestrationService` (dispatch pipeline), `EventService` (webhook ingestion), `ReportingService` (analytics aggregation) |
| **Adapters** | `api/adapters/` | Strategy Pattern implementations: `BaseChannelAdapter` (ABC), `EmailAdapter` (SMTP/mock), `SMSAdapter` (Twilio/mock), `ChannelAdapterFactory` (registry) |
| **Routes** | `api/routes/` | Thin HTTP transport layer: `auth.py`, `campaigns.py`, `contacts.py`, `events.py`, `reports.py`, `settings.py` |

The dependency flow is strictly **unidirectional**: Routes → Services → Adapters/Models, with Core modules available to all layers. No circular dependencies exist. Routes never directly access ORM models; they always delegate through the service layer.

## 4. State Management Architecture

### Backend State Machine

Campaign lifecycle is governed by a **finite state machine** defined as the `VALID_TRANSITIONS` dictionary in `api/services/campaign_service.py`:

```
DRAFT    → {ACTIVE, STOPPED}
ACTIVE   → {PAUSED, COMPLETED, STOPPED}
PAUSED   → {ACTIVE, STOPPED}
COMPLETED → {}  (terminal)
STOPPED   → {}  (terminal)
```

The `transition_status()` method enforces these transitions programmatically, raising `InvalidStateTransitionError` (HTTP 409) for illegal transitions. Convenience methods `start()`, `pause()`, `resume()`, and `stop()` provide semantically meaningful entry points that delegate to the state machine core.

### Frontend State Management

The frontend uses **React local state** (`useState` hooks) combined with **Axios-based API calls** through the centralized `apiClient` singleton in `src/lib/api.ts`. Authentication state is managed via `localStorage` with the JWT token. The `apiClient` configures two interceptors: a **request interceptor** that attaches the `Authorization: Bearer <token>` header from `localStorage`, and a **response interceptor** that detects 401 responses and redirects to `/login` (while avoiding redirect loops for `/login` and `/` paths). The dashboard layout (`src/app/(dashboard)/layout.tsx`) performs client-side auth gating via a `useEffect` that checks for the presence of the token, rendering a loading spinner until authentication is confirmed.

## 5. Data Model Design

The data model comprises **nine ORM entities** inheriting from a shared `Base` (SQLAlchemy `DeclarativeBase` in `api/core/database.py`) and `TimestampMixin` (providing `created_at` and `updated_at` columns with timezone-aware UTC defaults). Primary keys use UUID4-based strings generated by `generate_ulid()` in `api/models/base.py`. The relational structure is:

```
Campaign (1) ──→ (N) RecipientList  ──→ ContactProfile
Campaign (1) ──→ (N) MessageInstance ──→ (N) DeliveryAttempt
Campaign (1) ──→ (N) CampaignRule        ──→ (N) EngagementEvent
```

`MessageInstance` serves as the **central join entity** linking campaigns to delivery attempts and engagement events, enabling per-recipient granularity in analytics. The `EngagementEvent.event_details` column uses a `JSON` type for schemaless extensibility — different event types store different payloads (e.g., `link_url` for `LINK_CLICKED`, `button_label` for `BUTTON_CLICKED`).

## 6. Deployment Architecture

The system is configured for **monorepo deployment on Vercel** with dual runtimes:

- **Frontend:** Next.js 16 with the App Router, using React 19 and TailwindCSS v4. Route groups (`(dashboard)`) organize authenticated pages with shared layout and sidebar navigation.
- **Backend:** FastAPI deployed as a Vercel Python serverless function. The `vercel.json` rewrite rule `{"source": "/api/(.*)", "destination": "/api/index.py"}` routes all API traffic to the single entry point.
- **Database:** SQLite with `aiosqlite` driver for zero-configuration local and serverless operation, with documented PostgreSQL+asyncpg upgrade path for production.

The FastAPI application uses an `asynccontextmanager` lifespan handler that calls `init_db()` on startup, which executes `Base.metadata.create_all` to auto-create tables. All ORM models are eagerly imported via `import api.models` in `api/index.py` to ensure complete metadata population before table creation.
