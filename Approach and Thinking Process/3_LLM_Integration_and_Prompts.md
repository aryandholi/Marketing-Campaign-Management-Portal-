# LLM Integration and Prompt Engineering

## 1. Architectural Framing: This System Does Not Use LLMs

> **Critical Accuracy Disclosure (Zero Hallucination Policy):** **this codebase does not integrate any Large Language Model (LLM) APIs, prompt templates, or AI-driven text generation pipelines.** There are no imports of `openai`, `anthropic`, `google.generativeai`, `langchain`, `llamaindex`, or any other LLM SDK. There are no API calls to GPT, Claude, Gemini, or any inference endpoint. There are no prompt template strings, system instructions, temperature parameters, or JSON-mode parsing configurations anywhere in the codebase.

This is a deliberate and important architectural distinction. The system I designed is a **deterministic campaign orchestration platform**, not an AI-powered content generation tool. The "intelligence" in this system lies in the **human-designed algorithms and engineering patterns** I implemented to solve complex operational problems: audience resolution heuristics, finite state machine governance, multi-channel adapter abstraction, template interpolation engines, and real-time engagement analytics aggregation. Every output of this system is **fully deterministic and traceable** — the same inputs will always produce the same outputs, which is a critical property for a campaign management system where message content must be predictable, auditable, and compliant.

The following sections detail the **template rendering engine**, **audience resolution intelligence**, and **analytics computation logic** that serve as the "intelligent" processing cores of this system — fulfilling the role that LLMs might play in other architectures, but implemented here through explicit algorithmic design.

## 2. Template Rendering Engine: Dynamic Content Personalization

### Architecture

The template rendering system is implemented in `OrchestrationService._render_template()` within `api/services/orchestration_service.py`. Rather than delegating content generation to an LLM, I designed a deterministic **token substitution engine** that renders personalized message content from campaign templates.

### Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Campaign Template                                        │
│ "Hello {{first_name}}, welcome to our {{channel}} campaign!"    │
│                                                                 │
│ INPUT: Resolved Contact                                         │
│ { "first_name": "Alice", "last_name": "Wonderland",            │
│   "email": "alice@example.com", "phone": "+1-555-0101" }       │
├─────────────────────────────────────────────────────────────────┤
│ PROCESSING: _render_template()                                  │
│ for key in ("first_name", "last_name", "email", "phone",       │
│             "username"):                                        │
│     placeholder = "{{" + key + "}}"                             │
│     rendered = rendered.replace(placeholder, value or "")       │
├─────────────────────────────────────────────────────────────────┤
│ OUTPUT: Rendered Message                                        │
│ "Hello Alice, welcome to our email campaign!"                   │
└─────────────────────────────────────────────────────────────────┘
```

### Design Rationale

The template engine supports five substitution tokens — `{{first_name}}`, `{{last_name}}`, `{{email}}`, `{{phone}}`, and `{{username}}` — matching exactly the fields present in the `ResolvedContact` Pydantic schema. The `or ""` fallback ensures that missing contact fields are silently replaced with empty strings rather than rendering `None` or raising exceptions. This is a conscious engineering decision: in a campaign context, a message with a missing personalization field (`"Hello , welcome..."`) is preferable to a failed send, since the campaign operator explicitly approved the template.

The rendering is invoked once per contact within the dispatch loop in `OrchestrationService.send_campaign()`, and the rendered output is persisted in `MessageInstance.rendered_content` — creating a complete audit trail of exactly what was sent to each recipient.

## 3. Audience Resolution Intelligence: Multi-Identifier Heuristic Engine

### Architecture

The audience resolution engine in `api/services/audience_service.py` implements a **classification-then-lookup pipeline** that accepts heterogeneous identifier lists and resolves them to delivery-ready contact profiles. This is the closest analog to an "intelligent processing" layer in the system.

### Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Mixed Identifiers                                        │
│ ["alice@example.com", "+1-555-0102", "charlie_choco",           │
│  "unknown@nowhere.com"]                                         │
├─────────────────────────────────────────────────────────────────┤
│ PROCESSING STAGE 1: Classification (_classify_identifier)       │
│                                                                 │
│ EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]   │
│               {2,}$"                                            │
│ PHONE_REGEX = r"^\+?[\d\s\-()]{7,20}$"                         │
│                                                                 │
│ "alice@example.com"    → email                                  │
│ "+1-555-0102"          → phone                                  │
│ "charlie_choco"        → username (fallback)                    │
│ "unknown@nowhere.com"  → email                                  │
├─────────────────────────────────────────────────────────────────┤
│ PROCESSING STAGE 2: Resolution (MockContactStore.lookup)        │
│                                                                 │
│ "alice@example.com"    → contact_01_alice  ✓ RESOLVED           │
│ "+1-555-0102"          → contact_02_bob    ✓ RESOLVED           │
│ "charlie_choco"        → contact_03_charlie ✓ RESOLVED          │
│ "unknown@nowhere.com"  → None              ✗ UNRESOLVED         │
├─────────────────────────────────────────────────────────────────┤
│ PROCESSING STAGE 3: Deduplication (seen_ids set)                │
│                                                                 │
│ Prevents duplicate contacts when same person is identified      │
│ by both email and phone in the same audience list.              │
├─────────────────────────────────────────────────────────────────┤
│ OUTPUT: AudienceResolveResponse                                 │
│ { "resolved": [ResolvedContact×3], "unresolved": ["unknown@.."],│
│   "total_resolved": 3, "total_unresolved": 1 }                 │
└─────────────────────────────────────────────────────────────────┘
```

### Design Rationale

The classification heuristic uses a **priority-ordered regex cascade**: email format is checked first (most specific), then phone format, with username as the catch-all fallback. This ordering prevents false positive classifications — a string like `"user+tag@domain.com"` correctly matches as email rather than being misclassified by the phone regex. The `MockContactStore` uses a **multi-key indexing strategy** where each contact is registered under three separate keys (email, phone, username), enabling O(1) lookup regardless of which identifier type the caller provides. The `all_contacts()` method deduplicates by `id` using a `seen_ids` set to return unique contacts despite the multi-key storage.

## 4. Analytics Computation Engine: SQL-Level Aggregation

### Architecture

The `ReportingService.get_campaign_metrics()` in `api/services/reporting_service.py` implements **server-side analytics computation** using SQLAlchemy's expression language to generate complex aggregate queries.

### Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: campaign_id (string UUID)                                │
├─────────────────────────────────────────────────────────────────┤
│ PROCESSING: Two-Phase SQL Aggregation                           │
│                                                                 │
│ PHASE 1 — Message Metrics:                                      │
│   SELECT                                                        │
│     COUNT(id)                       AS total_recipients,        │
│     COUNT(CASE WHEN status IN       AS total_sent,              │
│       ('sent','delivered','failed','bounced')),                 │
│     COUNT(CASE WHEN status =        AS total_delivered,         │
│       'delivered'),                                             │
│     COUNT(CASE WHEN status IN       AS total_failed             │
│       ('failed','bounced'))                                     │
│   FROM message_instances                                        │
│   WHERE campaign_id = :campaign_id                              │
│                                                                 │
│ PHASE 2 — Engagement Metrics:                                   │
│   SELECT                                                        │
│     COUNT(CASE WHEN event_type IN   AS total_opened,            │
│       ('opened','read')),                                       │
│     COUNT(CASE WHEN event_type =    AS total_replied,           │
│       'replied'),                                               │
│     COUNT(CASE WHEN event_type IN   AS total_clicked            │
│       ('link_clicked','button_clicked'))                        │
│   FROM engagement_events                                        │
│   WHERE message_id IN (subquery)                                │
│                                                                 │
│ PHASE 3 — Rate Computation (Python):                            │
│   delivery_rate = total_delivered / total_sent × 100            │
│   open_rate = total_opened / total_delivered × 100              │
│   click_rate = total_clicked / total_opened × 100               │
│   (with division-by-zero guards on each)                        │
├─────────────────────────────────────────────────────────────────┤
│ OUTPUT: CampaignMetrics                                         │
│ { campaign_id, campaign_name,                                   │
│   total_recipients, total_sent, total_delivered, total_failed,  │
│   total_opened, total_replied, total_clicked,                   │
│   delivery_rate, open_rate, click_rate }                        │
└─────────────────────────────────────────────────────────────────┘
```

### Design Rationale

The aggregation logic uses SQLAlchemy's `func.count()` combined with `case()` expressions to compute multiple conditional counts in a single query, minimizing database round-trips. The message metrics and engagement metrics are executed as two separate queries (rather than a single complex JOIN) to avoid the N×M multiplication effect that would inflate counts when joining `MessageInstance` with `EngagementEvent`. The engagement query uses a subquery (`select(MessageInstance.id).where(MessageInstance.campaign_id == campaign_id)`) to scope events to the campaign's messages. All rates are rounded to two decimal places with explicit `or 0` null-coalescing on each metric value.

## 5. Channel-Specific Message Formatting

### Email HTML Rendering

The `EmailAdapter._send_real()` method in `api/adapters/email_adapter.py` constructs **multipart/alternative** MIME messages containing both plain text and HTML renditions. The HTML template wraps the rendered message content in a styled container:

```python
html_body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
  <div style="background:#f8f9fa;border-radius:8px;padding:20px">
    {body.replace(chr(10), '<br>')}
  </div>
  <p style="color:#999;font-size:11px;margin-top:20px">
    Sent via Nexus Portal
  </p>
</body></html>
"""
```

This is a **programmatic template**, not an LLM-generated output. The newline-to-`<br>` conversion (`body.replace(chr(10), '<br>')`) ensures that multi-line plain text messages render correctly in HTML email clients.

### SMS Body Truncation

The `SMSAdapter` implements a **160-character truncation** (`sms_body = body[:160] if len(body) > 160 else body`) in both `_send_real()` and `_send_mock()`, reflecting the SMS protocol's per-segment character limit. The mock mode also calculates segment count (`max(1, len(body) // 160)`) and includes it in the `provider_response` payload for cost estimation purposes.

## 6. Summary: Intelligence Through Engineering, Not AI

The "intelligence" of this system is embedded in its **architectural patterns and algorithmic design** rather than in LLM inference calls. The audience resolution engine demonstrates classification heuristics and multi-key indexing. The template engine demonstrates deterministic personalization. The analytics engine demonstrates efficient SQL aggregation with derived metric computation. The channel adapters demonstrate polymorphic dispatch with graceful degradation. Each of these components produces **predictable, auditable, reproducible outputs** — a property that is essential for a campaign management platform where message content must be verifiable and compliant.

This architectural choice was deliberate: campaign systems operate under regulatory constraints (CAN-SPAM, GDPR, TCPA) where every message sent must be attributable to a specific template, a specific audience resolution, and a specific operator action. LLM-generated content introduces non-determinism that would complicate compliance auditing. The engineering patterns I chose optimize for **auditability, predictability, and extensibility** while still demonstrating sophisticated processing logic.
