# Marketing Campaign Management Portal

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black)
![Supabase](https://img.shields.io/badge/Supabase-DB-3ecf8e)

A production-grade, multi-channel Marketing Campaign Management Portal. This Proof of Concept (POC) enables users to create campaigns, resolve audiences, orchestrate notifications via extensible channel adapters (Email/SMS), and track downstream engagement metrics. 

Designed for **extensibility, observability, and cloud-native deployment on Vercel**.

---

## 📑 Table of Contents
1. [Architecture Note](#architecture-note)
2. [Data Model](#data-model)
3. [Setup & Run Instructions](#setup--run-instructions)
4. [Scope Covered](#scope-covered)
5. [Design Decisions & Limitations](#design-decisions--limitations)
6. [Future Evolution](#future-evolution)
7. [Demo Walkthrough](#demo-walkthrough)

---

## 🏗️ Architecture Note

The system is built as a decoupled Full-Stack application using a **layered, domain-driven architecture**.

### Logical Components
- **Portal / UI**: Next.js 14 (App Router) providing a premium, "Google-level" responsive dashboard.
- **API Gateway**: FastAPI acting as the core orchestration and integration layer.
- **Authentication**: JWT-based session management protecting dashboard routes.
- **Campaign Service**: Manages the campaign state machine (Draft → Active → Paused → Stopped) and CRUD operations.
- **Audience Resolution**: Resolves arbitrary identifiers (usernames, IDs) to concrete contact profiles (emails, phone numbers).
- **Notification Orchestration**: Manages template rendering and dispatches messages to the Channel Adapters.
- **Channel Adapters**: A Factory-pattern based registry for channels. Currently implemented: Mock `EmailAdapter` and `SMSAdapter`.
- **Event Ingestion**: Webhook receiver for engagement signals (Delivered, Opened, Clicked).
- **Reporting**: Aggregates engagement events into campaign performance metrics.

### Physical Design (Vercel Deployment)
- **Frontend**: Deployed on Vercel Edge Network.
- **Backend APIs**: Python FastAPI running as Vercel Serverless Functions (`api/index.py`).
- **Database**: Supabase PostgreSQL.

> For an in-depth visual architecture and request lifecycle, please see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## 🗄️ Data Model

The application uses an asynchronous SQLAlchemy ORM connected to PostgreSQL. The core entities include:

- `User`: Authenticated portal operators.
- `Contact`: End-users receiving marketing messages.
- `Campaign`: The core marketing effort entity, linking to rules and templates.
- `Message`: Individual outbound notification attempts.
- `Event`: Downstream engagement signals tied back to a specific `Message`.

> For the detailed ER Diagram and Schema definitions, please see [DATA_MODEL.md](./DATA_MODEL.md).

---

## 🚀 Setup & Run Instructions

This project is a monorepo containing both the Next.js frontend and the FastAPI backend.

### Prerequisites
- Node.js 18+ & npm
- Python 3.12+
- PostgreSQL database (or a free Supabase instance)

### 1. Environment Setup
Clone the repository and configure your `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and JWT_SECRET
```

### 2. Backend (FastAPI) Setup
The backend requires Python dependencies and database initialization.

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Seed the database with mock data (Users, Contacts, and past Events)
python seed_data.py

# Run the backend locally
fastapi dev api/index.py
```
*The API will be available at `http://localhost:8000`. Swagger docs at `/api/docs`.*

### 3. Frontend (Next.js) Setup
In a new terminal window:

```bash
# Install Node dependencies
npm install

# Start the frontend dev server
npm run dev
```
*The UI will be available at `http://localhost:3000`.*

---

## 🎯 Scope Covered

This implementation fully demonstrates the core design ideas expected in a robust proof of concept:
- **A minimal authenticated portal/API**: Full UI dashboard backed by JWT session management.
- **Campaign creation and management**: Complete state machine (Draft → Active → Paused → Stopped) via frontend and API.
- **Recipient ingestion & resolution**: Flexible `Audience Service` that resolves arbitrary identifiers (e.g., handles, emails, phones) against contact profiles.
- **Message sending flow**: End-to-end orchestration utilizing an extensible Adapter Pattern (demonstrated via Email and SMS).
- **Clear extensibility**: A Factory Registry makes dropping in new channel adapters (WhatsApp, Push) trivial without altering core orchestration.
- **Engagement event capture**: Robust webhook endpoints capable of ingesting downstream signals (delivered, clicked, opened).
- **Persistence for core entities**: Structured Supabase (PostgreSQL) implementation handling Users, Contacts, Campaigns, Messages, and Events.
- **A simple view of metrics**: Frontend reporting UI visualizing aggregate campaign performance and delivery rates.

---

## 🧠 Design Decisions & Limitations

### Strategic Design Decisions
1. **Layered, Domain-Driven Architecture**: The codebase cleanly separates presentation, business orchestration, and infrastructure. This ensures the UI can evolve independently from the API, and channel providers can be swapped with zero core logic changes.
2. **Python Serverless (FastAPI) on Vercel**: Chosen to balance rapid POC delivery with robust Pydantic data validation and OpenAPI schema generation.
3. **Adapter Factory Pattern**: Decouples the core campaign logic from the volatility of external vendor APIs (e.g., Twilio, SendGrid).
4. **Tailwind + Next.js App Router**: Used to deliver a "Google-level", high-performance, responsive UI with minimal overhead.

### Current Limitations (POC Scope)
- **Synchronous Dispatch**: In this POC, hitting "Send" processes messages synchronously. This limits high-throughput scalability. *Production Mitigation:* Transition to an async queue (Kafka/Celery).
- **Mock Channel Adapters**: Integrations with SendGrid/Twilio are currently mocked. *Production Mitigation:* Inject real API keys and use vendor SDKs.
- **Basic Rate Limiting**: No robust API request rate limiting is implemented. *Production Mitigation:* Implement Redis-based token bucket middleware.
- **Authentication Simplicity**: Relies on a basic JWT implementation with static user seeds rather than a fully-fledged IdP (like Auth0 or Supabase Auth).

---

## 🔮 Future Evolution

The system is explicitly designed to evolve in the following ways:

### New Channels (e.g., WhatsApp)
Due to the **Adapter Factory Pattern**, adding a new channel does not require altering the Orchestrator. 
1. Create `WhatsAppAdapter` inheriting from `BaseChannelAdapter`.
2. Register it in `ChannelAdapterFactory`.
3. Add it to the Channel Enum.

### Complex Campaign Rules
To support throttling, time windows, and Do-Not-Disturb (DND):
1. Introduce a **Redis cache** for sliding window rate limits and rule evaluations.
2. Decouple the Orchestrator to push intents to a **Kafka/RabbitMQ queue**.
3. Use **Celery Workers** to evaluate rules (Is it within the time window? Has the daily cap been hit?) before popping off the queue and invoking the adapter.
4. Introduce automated **State Machine Triggers** (e.g., automatically pause campaigns if bounce rates exceed thresholds).

---

## 🎬 Demo Walkthrough

To fully experience the POC, follow these steps after completing the **Setup & Run Instructions**:

1. **Login**: Navigate to `http://localhost:3000`. Login using the seeded credentials (`admin@campaignportal.io` / `password123`).
2. **Explore Dashboard**: View the aggregate metrics on the home dashboard, showcasing past campaign performance (generated via the seed script).
3. **Create Campaign**: Click "New Campaign". Fill in details, selecting 'Email' as the channel. Provide target audience identifiers (e.g., `alice@example.com`, `bob_builder`).
4. **Preview Audience**: In the API (or via Postman), hit the `/api/campaigns/audience/resolve` endpoint to see how `bob_builder` is mapped to an actual contact profile.
5. **Send Campaign**: Start the campaign, then trigger the send action. The UI will reflect the synchronous processing, and the terminal will output structured logs demonstrating the Adapter Pattern routing the messages.
6. **Review Reports**: Click into the specific campaign to view the delivery success rate and engagement metrics.

> **Note on Sample Data:** The database is pre-seeded with Contacts, Users, and simulated historical Campaigns/Events via the `seed_data.py` script. This provides an immediate, populated environment for evaluation.

---
*Built as a professional Proof of Concept for Marketing Campaign System Evaluation.*
