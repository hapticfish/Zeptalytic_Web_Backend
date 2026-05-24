# Email Delivery Events and Webhooks

**Target file:** `docs/architecture/Email_Delivery_Events_And_Webhooks.md`  
**Status:** Draft / Architecture Reference  
**Project:** Zeptalytic Web Backend  
**Service:** Parent/backend application, not Pay Service  
**Provider:** Brevo transactional email  
**Mailbox/reply system:** Google Workspace  
**Primary future spec:** `specs/transactional_email_service_brevo.json`

---

## 1. Purpose

This document defines the architecture for receiving, validating, normalizing, storing, and safely using Brevo transactional email delivery events in the Zeptalytic Web Backend.

The purpose is to give future spec-author, plan, and build agent runs complete context for implementing the email delivery webhook portion of the transactional email service workstream.

This document covers:

- Brevo webhook route shape
- webhook security model
- webhook secret handling
- delivery event normalization
- delivery event persistence
- webhook deduplication
- raw payload storage
- relationship between send attempts and delivery events
- operational debugging goals
- privacy and sensitive-data handling
- tests required for implementation
- out-of-scope items
- future expansion paths

This document is an architecture/reference document. It is not itself the implementation spec.

Future implementation specs must absorb this document before creating webhook-related implementation tasks.

---

## 2. Related Architecture Documents

This document is part of the Zeptalytic transactional email architecture set.

Related docs:

```text
docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

Expected division of responsibility:

Brevo_Google_Workspace_Email_Decision_Record.md defines provider/mailbox/sender decisions.
Transactional_Email_Service_Architecture.md defines the overall backend email service architecture.
Auth_Email_Verification_Flow.md defines auth flow integration.
Email_Delivery_Events_And_Webhooks.md defines Brevo webhook ingestion and delivery event storage.
Email_Template_Catalog.md defines templates, senders, parameters, and trigger rules.
Transactional_Email_Agent_Run_Guidance.md defines harness/spec-generation/build instructions.
3. Current Backend Context

The Zeptalytic Web Backend already has partial auth and email-verification functionality.

Known existing backend pieces include:

POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/verify-email
POST /api/v1/auth/resend-verification
AuthService.verify_email()
AuthService.resend_email_verification()
AuthService.forgot_password()
AuthService.reset_password()
EmailVerificationToken model/table
password reset token logic
auth route tests for verification/resend behavior
pending-verification access flags

The backend does not yet have the complete transactional email delivery tracking architecture.

Missing pieces expected from this workstream:

email_delivery_events model/table
email_delivery_event_repository
Brevo webhook route
webhook secret validation
webhook event normalization
webhook deduplication
raw webhook payload persistence
tests for valid/invalid/duplicate/malformed webhook handling
OpenAPI/runtime route coverage for webhook route if project convention includes public webhook routes
4. Current Repository and Environment

Backend repo:

~/Desktop/Dev/Zeptalytic_Web_Backend

Backend stack:

FastAPI
SQLAlchemy
PostgreSQL
Alembic
Docker Compose
Poetry

Local backend URL:

http://localhost:8000

Local frontend URL:

http://localhost:5173

Typical local backend startup:

cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api

Health check:

curl -i http://localhost:8000/health

OpenAPI check:

curl -i http://localhost:8000/openapi.json

Authoritative backend test gates:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

Frontend repo is separate:

~/Desktop/Dev/Zeptalytic_Web

This webhook/delivery-events workstream must not edit frontend code.

5. Provider and Responsibility Split

Zeptalytic email architecture uses three separate responsibility layers:

Google Workspace = mailboxes, aliases, human reply handling
Brevo = transactional sending and provider delivery telemetry
Zeptalytic Web Backend = application logic, provider API calls, webhook ingestion, operational records

Brevo does not log into Google Workspace.

Google Workspace does not send transactional application emails directly.

The backend sends transactional email through Brevo.

Brevo sends webhook events back to the backend when messages are sent, delivered, opened, clicked, bounced, blocked, complained about, unsubscribed, or otherwise fail.

DNS authorizes Brevo to send as zeptalytic.com.

6. Core Architecture Decision

The backend will store two separate email operational facts:

email_send_attempts
Records what the backend attempted to send.
email_delivery_events
Records what Brevo later reported happened.

These must remain separate because a provider API send response and a provider delivery event are not the same fact.

A successful call to Brevo’s transactional send API means the backend submitted a send request and Brevo accepted or processed it.

It does not prove that the recipient received the email.

Delivery, bounce, open, click, complaint, blocked, and unsubscribe events are later asynchronous provider events.

7. Target Backend Files

Future implementation specs should prefer this layout unless the actual project structure indicates a better project-conventional location.

app/
  api/
    routers/
      v1/
        email_webhooks.py

  db/
    models/
      email_delivery_events.py

    repositories/
      email_delivery_event_repository.py

  schemas/
    email.py

Potential files that may need updates:

app/api/routers/v1/__init__.py
app/db/models/__init__.py
app/db/models/import_models.py
app/core/config.py
tests/
alembic/versions/
.env.example

If email_send_attempts has not yet been implemented, the implementation spec should coordinate with:

app/db/models/email_send_attempts.py
app/db/repositories/email_send_attempt_repository.py
app/services/email_service.py
app/integrations/brevo_client.py

Future agents must search the repository before editing.

Do not assume exact current filenames without inspecting the codebase.

8. Webhook Route Decision

First implementation route:

POST /api/v1/email/webhooks/brevo

First-phase local/public URL shape:

POST /api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Expected router file:

app/api/routers/v1/email_webhooks.py

The route should be registered under the existing v1 API router pattern.

Future agents must inspect existing router registration conventions before adding this route.

9. Webhook Security Model

The Brevo webhook route is intentionally different from normal user-authenticated API routes.

The route is:

public
provider-facing
not browser-session authenticated
not protected by CSRF
not protected by user session cookies
not protected by internal service token
protected by webhook secret

First-phase secret validation:

?secret=<BREVO_WEBHOOK_SECRET>

The webhook must validate the secret before processing payload content.

Invalid or missing secret must return an unauthorized or forbidden response consistent with project conventions.

The route must not require:

logged-in user session
CSRF token
frontend auth state
parent account permissions
internal service token

Reason:

Brevo is an external provider. It will not have a user session cookie, CSRF token, or internal service token.

10. Webhook Secret Configuration

Required environment variable:

BREVO_WEBHOOK_SECRET=

Secret storage rules:

real value belongs only in local .env, Fly secrets, or secure runtime secret storage
real value must not be committed
real value must not appear in docs
real value must not appear in specs
real value must not appear in progress logs
real value must not appear in docker-compose.yml
real value must not appear in fly.toml
real value must not appear in GitHub Actions workflow bodies

.env.example should include only a placeholder:

BREVO_WEBHOOK_SECRET=

Do not use a real value in examples.

11. Local Webhook Testing Context

A Cloudflare Quick Tunnel may be used for local Brevo webhook testing.

Start backend:

cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api
curl -i http://localhost:8000/health

Start tunnel:

cloudflared tunnel --url http://localhost:8000

Test public tunnel health:

curl -i https://<trycloudflare-domain>.trycloudflare.com/health

Expected Brevo webhook URL shape:

https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

If the tunnel returns 502 Bad Gateway, the backend is probably not running or not reachable at:

http://localhost:8000

If the Brevo webhook test returns 404 Not Found before implementation, that is expected because the route likely does not exist yet.

A previously used tunnel base URL was:

https://bright-damages-empirical-art.trycloudflare.com

That specific tunnel URL should be treated as temporary. Cloudflare Quick Tunnel URLs change unless a named tunnel/domain is configured.

Do not commit temporary tunnel URLs into production configuration.

12. Webhook Processing Flow

The first implementation should process each webhook request using this sequence:

Receive POST /api/v1/email/webhooks/brevo.
Validate secret query parameter against BREVO_WEBHOOK_SECRET.
Reject missing/invalid secret before doing meaningful processing.
Parse JSON body.
Validate that body is an object or supported event payload shape.
Extract provider event fields.
Normalize provider event type into Zeptalytic event type.
Extract provider message ID if available.
Extract provider event ID if available.
Extract recipient email if available.
Extract template ID if available.
Extract subject if available.
Extract provider event timestamp if available.
Compute deterministic dedupe key.
Insert event into email_delivery_events.
If duplicate, return successful duplicate-safe response.
Do not execute heavy downstream business logic inline.
Return success quickly.

The webhook route should be ingestion-focused.

It should not become a broad business workflow processor in the first implementation.

13. Webhook Route Must Not Do These Things

The first implementation webhook route must not:

require user session
require CSRF
require frontend auth
require internal service token
mutate account verification status
verify user accounts based on open/click/delivered events
reset passwords
mutate billing/payment state
mutate Pay Service state
mutate support ticket state
send additional user emails as a reaction to delivery events
unsubscribe users from product/account communications unless future communication-preferences spec defines this
implement newsletter suppression logic
implement bounce suppression logic
launch a large retry worker
expose raw webhook payloads in public responses
log secrets
log raw security tokens
store rendered email bodies
block for slow downstream processing
14. Events to Track

Brevo webhook configuration should track transactional email events corresponding to:

Sent
Delivered
Opened
Clicked
Soft Bounce
Hard Bounce
Invalid Email
Deferred
Complaint / Spam
Unsubscribed
Blocked
Error

If Brevo UI labels differ, choose the closest available transactional event labels.

Do not configure unrelated marketing campaign events unless a future newsletter/marketing spec explicitly includes them.

15. Normalized Event Types

The backend should normalize provider-specific Brevo event labels into a stable internal set.

Required normalized event types:

sent
delivered
opened
clicked
soft_bounce
hard_bounce
invalid_email
deferred
complaint
unsubscribed
blocked
error
unknown

The implementation should preserve unknown events instead of failing.

Unknown events should be stored with:

event_type = "unknown"

and the raw payload should be retained.

This allows future event mapping updates without losing evidence.

16. Example Event Mapping

Provider labels must be confirmed against actual Brevo payloads during implementation, but conceptual mapping should follow this pattern.

Brevo/provider value	Normalized value
sent	sent
delivered	delivered
opened	opened
open	opened
click	clicked
clicked	clicked
soft_bounce	soft_bounce
softBounce	soft_bounce
hard_bounce	hard_bounce
hardBounce	hard_bounce
invalid	invalid_email
invalid_email	invalid_email
deferred	deferred
spam	complaint
complaint	complaint
unsubscribed	unsubscribed
blocked	blocked
error	error
unrecognized	unknown

Future agents must inspect real Brevo webhook payload examples or provider docs during implementation if available in the repo context or tests.

17. Delivery Event Table
17.1 Table Name
email_delivery_events
17.2 Purpose

This table records provider-reported email events.

It answers:

Did Brevo report the email as sent?
Did Brevo report the email as delivered?
Did the recipient open or click it?
Did it bounce?
Was it blocked?
Was it marked as spam/complaint?
Did the recipient unsubscribe?
Did Brevo report an error?
What raw payload did Brevo send?
Was the event already processed?
17.3 Proposed Model File
app/db/models/email_delivery_events.py
17.4 Proposed Repository File
app/db/repositories/email_delivery_event_repository.py
17.5 Proposed Fields

Field names should follow existing project conventions, but conceptually the table should include:

Field	Type	Required	Notes
id	UUID	yes	primary key
provider	string	yes	default brevo
event_type	string	yes	normalized internal event type
provider_message_id	string	no	Brevo message/message-id if available
provider_event_id	string	no	provider event id if available
email	string	no	recipient email if provided
template_id	integer	no	Brevo template ID if provided
subject	string	no	subject if provided
event_timestamp	timestamp	no	provider event time
dedupe_key	string	yes	unique deterministic dedupe key
raw_payload	JSONB	yes	original webhook payload
created_at	timestamp	yes	backend ingestion time
17.6 Optional Future Fields

Future specs may add:

Field	Purpose
send_attempt_id	optional FK to email_send_attempts.id if correlation is reliable
account_id	optional denormalized account reference if safely derivable
ip_address	if Brevo provides it and privacy policy allows storage
user_agent	if Brevo provides it and privacy policy allows storage
link_url	for clicked events if needed and privacy policy allows storage
campaign_id	future newsletter/campaign support
tags	provider tags/categories if used later

Do not add optional fields unless they are needed by the implementation spec or are directly available and useful.

18. Raw Payload Storage

The backend should store the full Brevo webhook payload as JSONB in:

email_delivery_events.raw_payload

Reasons:

preserves provider evidence
helps debug delivery issues
supports future mapping changes
helps support investigate bounce/blocked/complaint cases
avoids losing provider fields not modeled yet

Raw payload storage restrictions:

raw payload is sensitive operational data
do not expose raw payload through public APIs
do not include raw payload in normal user-facing responses
do not dump raw payload to normal logs
do not include raw payload in docs/specs except sanitized examples
do not store rendered email body separately
do not store Brevo API keys or webhook secrets

If the raw payload includes URLs, user agents, IPs, or recipient metadata, treat them as sensitive operational data.

19. Dedupe Strategy
19.1 Requirement

Webhook ingestion must be idempotent.

Duplicate Brevo webhook deliveries must not create duplicate email_delivery_events rows.

Duplicate webhook deliveries should return successful HTTP responses so Brevo does not keep retrying already-processed valid events.

19.2 Dedupe Key

The table should include:

dedupe_key

with a unique constraint or unique index.

The dedupe key should be deterministic and stable for the same provider event.

19.3 Preferred Dedupe Inputs

Use the strongest available provider identifier first.

Preferred inputs:

provider event ID, if Brevo supplies a stable unique event ID
provider message ID + event type + provider event timestamp
provider message ID + event type + recipient email + provider event timestamp
stable hash of selected normalized payload fields
stable hash of raw payload as fallback

Potential conceptual format:

brevo:<provider_event_id>

or:

brevo:<provider_message_id>:<event_type>:<event_timestamp>:<email>

Do not use non-deterministic values like backend insertion time in dedupe key.

19.4 Duplicate Response

If duplicate insert is detected:

do not raise a 500
return success
optionally include a safe response like {"status": "duplicate"} if project response style supports it
do not expose raw payload
do not expose internals
20. Relationship to Email Send Attempts

The delivery event system should be designed to correlate with email_send_attempts when possible.

email_send_attempts records:

backend attempted to send an email

email_delivery_events records:

Brevo reported a later event about an email

Potential correlation field:

provider_message_id

If Brevo returns a message ID from POST /smtp/email, store it in:

email_send_attempts.provider_message_id

If Brevo webhook provides the same value, store it in:

email_delivery_events.provider_message_id

This allows later support/debug joins.

Important:

delivery events may arrive before a send-attempt update is committed
delivery events may not include a provider message ID
provider message ID format may differ across API response and webhook event
a delivery event may not be reliably linked to a send attempt in all cases

Therefore, email_delivery_events should not require a foreign key to email_send_attempts in the first implementation unless reliable correlation is confirmed.

Use nullable correlation.

Do not drop delivery events just because no matching send attempt is found.

21. Auth Flow Relationship

Delivery events must not drive account verification.

Auth verification must be based on backend token verification through:

POST /api/v1/auth/verify-email

Do not verify an account based on:

sent
delivered
opened
clicked

A clicked event only means Brevo detected a click. It is not sufficient for account verification because:

link scanners may click links
email security gateways may prefetch URLs
click tracking may not prove the user completed backend token verification
provider events are not the source of truth for account state

Account verification source of truth:

valid backend verification token submitted to auth endpoint

Password reset source of truth:

valid backend reset token submitted to reset-password endpoint

Webhook delivery events are telemetry only in the first implementation.

22. Billing and Pay Service Relationship

Billing-related templates exist, including:

Order Confirmation
Payment Failed
Subscription Expiring

The webhook delivery-event system may store delivery events for these templates once billing emails are sent in the future.

However, this workstream must not:

implement billing email triggers
mutate Pay Service state
mutate payment state
mutate subscription state
duplicate Pay commercial logic
infer payment status from email delivery status

Pay Service remains the source of truth for payments, subscriptions, entitlements, and commercial finality.

A delivered order confirmation email does not prove payment success.

A bounced payment failed email does not change payment status.

Email delivery telemetry is not billing truth.

23. Newsletter and Updates Relationship

The template catalog includes:

News & Updates

Delivery events for updates/newsletter emails may be stored in the same email_delivery_events table in the future if the backend sends those emails through Brevo transactional APIs or a future campaign integration.

However, this workstream must not:

implement newsletter campaign automation
implement marketing list synchronization
implement subscription preference center
implement unsubscribe enforcement
mutate communication preferences from Brevo unsubscribe events

Future newsletter/communications specs must define how unsubscribe and preference events affect Zeptalytic account communication preferences.

In the first implementation, unsubscribed events should be stored but should not automatically mutate account preferences unless explicitly defined by a future spec.

24. Complaint, Spam, and Unsubscribe Events

The backend should store complaint/spam and unsubscribe events because they are operationally important.

Normalized events:

complaint
unsubscribed

First implementation behavior:

store event
preserve raw payload
dedupe event
do not mutate communication preferences automatically
do not disable accounts automatically
do not suppress all future email automatically

Future specs may define:

communication preference updates
suppression lists
support alerts
compliance workflows
account security notifications
admin review flows

Do not invent those workflows in the first implementation.

25. Bounce and Invalid Email Events

The backend should store bounce and invalid email events.

Normalized events:

soft_bounce
hard_bounce
invalid_email
blocked
error
deferred

First implementation behavior:

store event
preserve raw payload
dedupe event
do not automatically change account email verification state
do not automatically close/suspend accounts
do not automatically suppress future sends unless a future suppression spec defines it

Reason:

Email provider bounce state is useful telemetry, but automatic account mutation has product and support implications that need separate specification.

Future specs may define:

marking email as undeliverable
prompting user to update email
internal alert on repeated hard bounces
suppression list behavior
support dashboard flags
26. Open and Click Events

The backend should store open and click events if Brevo sends them.

Normalized events:

opened
clicked

First implementation behavior:

store event
preserve raw payload
dedupe event
do not use open/click as proof of verification
do not use open/click as proof of user intent
do not trigger account state changes

Open/click events can be caused by:

user action
link scanners
privacy proxies
security gateways
automated email clients

Treat them as telemetry only.

27. Webhook Response Behavior

Expected response behavior:

Condition	Expected response
Missing secret	reject with unauthorized/forbidden
Invalid secret	reject with unauthorized/forbidden
Malformed JSON	controlled client error
Unsupported payload shape	controlled client error or stored as unknown if parseable
Unknown event type	store as unknown, return success
Valid new event	insert and return success
Duplicate event	return success
Database transient failure	return server error so provider may retry
Internal normalization bug	return server error and log sanitized details

Do not expose:

webhook secret
stack trace
database internals
raw payload
provider secrets
28. Error Handling Rules
28.1 Missing or Invalid Secret

If the secret is missing or invalid:

do not process payload
do not store payload
return unauthorized/forbidden according to project convention
log only sanitized event such as invalid webhook secret attempt
do not log supplied secret value
28.2 Malformed JSON

If JSON parsing fails:

return controlled client error
do not create delivery event
log sanitized parse failure
do not dump raw body to normal logs
28.3 Unknown Event Type

If event type is unknown:

store event as unknown
store raw payload
return success
do not fail ingestion
28.4 Duplicate Event

If dedupe key already exists:

return success
do not create duplicate row
do not treat as error
28.5 Database Failure

If database insert fails for reasons other than duplicate:

return server error
allow provider retry
log sanitized failure
29. Logging Rules

Logs should support operational debugging without exposing sensitive data.

Allowed log concepts:

normalized event type
provider
delivery event ID
dedupe status
provider message ID if safe
provider template ID
sanitized recipient email if existing project logging permits it
high-level parse/validation failure
invalid webhook secret attempt without secret value

Do not log:

Brevo API key
webhook secret
supplied invalid secret
raw verification token
raw password reset token
full verification URL with token
full reset URL with token
session cookie
rendered email body
full raw webhook payload in normal logs
30. PII and Sensitive Data Handling

The delivery event system may store:

recipient email
provider message ID
provider event ID
event type
template ID
subject
raw webhook payload
provider timestamp

These are operational data and may contain personal or sensitive information.

Handling rules:

do not expose raw delivery event records through public user APIs in the first implementation
do not expose raw payloads through public APIs
do not add admin APIs unless a separate admin/support spec defines access controls
do not include raw payloads in user-facing errors
do not include raw payloads in normal logs
avoid storing rendered email body
avoid storing raw security-token URLs

Retention:

Retain send attempts and delivery events indefinitely for the first implementation.

Retention/archive/purge policies are future scope.

31. Database and Migration Expectations

Future specs must include an Alembic migration for email_delivery_events if the table does not already exist.

Migration requirements:

UUID primary key consistent with backend convention
provider field
event_type field
provider_message_id nullable field
provider_event_id nullable field
email nullable field
template_id nullable field
subject nullable field
event_timestamp nullable field
dedupe_key required field
unique constraint/index on dedupe_key
raw_payload JSONB required field
created_at timestamp field
indexes for operational/support queries
model import registration for Alembic/autogenerate

Recommended indexes:

email_delivery_events.provider_message_id
email_delivery_events.email
email_delivery_events.event_type
email_delivery_events.template_id
email_delivery_events.event_timestamp
email_delivery_events.created_at
email_delivery_events.dedupe_key unique

Potential optional index:

email_delivery_events.provider_event_id

Future agents must inspect existing timestamp, UUID, JSONB, and naming conventions before writing the migration.

32. Repository Layer Expectations

A repository should encapsulate delivery-event persistence.

Suggested file:

app/db/repositories/email_delivery_event_repository.py

Suggested repository responsibilities:

create event row
compute or accept dedupe key
handle duplicate insert safely
retrieve event by dedupe key if needed
support tests without exposing raw SQL everywhere
keep route handler thin

Potential method concepts:

class EmailDeliveryEventRepository:
    def create_event_if_new(
        self,
        *,
        provider: str,
        event_type: str,
        dedupe_key: str,
        raw_payload: dict,
        provider_message_id: str | None = None,
        provider_event_id: str | None = None,
        email: str | None = None,
        template_id: int | None = None,
        subject: str | None = None,
        event_timestamp: datetime | None = None,
    ) -> EmailDeliveryEventCreateResult:
        ...

Exact types and method names should follow existing project style.

33. Schema Layer Expectations

A schema module may define request/response structures for webhook ingestion.

Suggested file:

app/schemas/email.py

Potential schema concepts:

BrevoWebhookResponse
EmailDeliveryEventOut for internal tests/admin future
EmailWebhookIngestResult
provider-neutral event normalization result

Do not overbuild public response schemas.

The webhook response can be simple, such as:

{
  "status": "ok"
}

or:

{
  "status": "duplicate"
}

based on project style.

Do not expose raw payload in response.

34. Normalization Helper Expectations

Event normalization can live in the router, repository, service, or helper module depending on project conventions.

Preferred architecture:

email_webhooks.py
→ small route handler
→ normalization/helper function or service
→ repository

Do not put large parsing and normalization logic directly inside a long route handler if the project has service/helper conventions.

Potential helper responsibilities:

extract event name
map event to normalized event type
parse provider timestamp
extract provider message ID
extract provider event ID
extract recipient email
extract template ID
compute dedupe key
preserve raw payload

The implementation should be testable without requiring a live HTTP request.

35. Brevo Payload Handling

Future agents must inspect Brevo’s actual webhook payload shape during implementation if possible.

The architecture should not assume one exact shape without tests.

Common provider webhook payload fields may include concepts like:

event
email
id
message-id
messageId
date
ts
timestamp
template_id
templateId
subject
reason
tag
link
sending_ip

The implementation should be tolerant of missing optional fields.

Required behavior:

missing optional fields should not fail ingestion
missing event type should produce controlled error or unknown, depending on parseability
missing provider message ID should not fail ingestion
missing template ID should not fail ingestion
missing email should not fail ingestion if dedupe key can still be computed
36. OpenAPI Expectations

The route should appear in runtime OpenAPI unless existing backend convention intentionally excludes webhook routes.

Expected route:

POST /api/v1/email/webhooks/brevo

OpenAPI docs should not include real secrets.

The query parameter should be documented generically:

secret=<webhook-secret>

Do not include:

real Brevo webhook secret
real API key
full raw production payload with sensitive data
raw verification/reset token examples

Runtime OpenAPI should be checked:

curl -i http://localhost:8000/openapi.json

If the backend has prior OpenAPI surface regression tests, update them according to project convention.

37. Testing Requirements

Future implementation specs must include webhook tests.

37.1 Security Tests

Verify:

missing secret is rejected
invalid secret is rejected
valid secret is accepted
supplied invalid secret is not logged
no user session is required
no CSRF token is required
no internal service token is required
37.2 Valid Event Tests

Verify:

valid Brevo event creates delivery event
raw payload is stored
event type is normalized
provider message ID is stored when available
provider event ID is stored when available
recipient email is stored when available
template ID is stored when available
subject is stored when available
provider timestamp is parsed when available
response is successful
37.3 Duplicate Event Tests

Verify:

duplicate webhook does not create second row
duplicate webhook returns success
dedupe key unique constraint works
duplicate handling does not produce 500
37.4 Unknown Event Tests

Verify:

unknown provider event is stored as unknown
raw payload is retained
response is successful
37.5 Malformed Payload Tests

Verify:

malformed JSON returns controlled client error
unsupported payload shape returns controlled error or controlled unknown behavior
malformed payload does not create invalid DB row unless intentionally stored as unknown
raw invalid body is not dumped into normal logs
37.6 Event Mapping Tests

Verify mapping for at least:

sent
delivered
opened
clicked
soft_bounce
hard_bounce
invalid_email
deferred
complaint
unsubscribed
blocked
error
unknown
37.7 Database Tests

Verify:

migration applies cleanly
model imports correctly
JSONB raw payload stores correctly
unique dedupe key prevents duplicate events
indexes do not break test DB setup
37.8 Auth Separation Tests

Verify delivery webhook events do not:

verify account
reset password
activate account
change billing/payment state
mutate support ticket state
37.9 Required Gates

Before marking implementation complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

Agents must not mark spec items complete unless relevant tests/gates pass or blockers are explicitly documented.

38. Manual Smoke Test Plan

After implementation, local smoke testing can use Cloudflare tunnel and Brevo webhook test features.

38.1 Start Backend
cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api
curl -i http://localhost:8000/health
38.2 Start Tunnel
cloudflared tunnel --url http://localhost:8000
38.3 Confirm Tunnel
curl -i https://<trycloudflare-domain>.trycloudflare.com/health
38.4 Configure Brevo Webhook Test URL
https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>
38.5 Confirm Event Storage

Use project-conventional DB access to inspect email_delivery_events.

Potential Docker psql pattern, adjusted to actual DB env variables:

docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

Then inspect:

SELECT
    id,
    provider,
    event_type,
    provider_message_id,
    email,
    template_id,
    event_timestamp,
    created_at
FROM email_delivery_events
ORDER BY created_at DESC
LIMIT 20;

Do not paste real secrets into commands committed to docs or progress logs.

39. Production Deployment Context

Future production target:

React frontend container
Python backend API container
single-node Fly Postgres with persistent NVMe volume
future product apps/workers on Fly private mesh
GitHub Actions deployment to Fly.io

Deployment path:

local Docker Compose
→ git push main or tags
→ GitHub Actions
→ Fly.io production

Production secrets should use Fly secrets:

fly secrets set BREVO_API_KEY="..." -a zeptalytic-backend
fly secrets set BREVO_WEBHOOK_SECRET="..." -a zeptalytic-backend

Do not place secrets in:

fly.toml
docker-compose.yml
GitHub Actions workflow body
docs
specs
progress logs
source code defaults

Static outbound IP / Brevo authorized IP allowlisting is deferred until Fly production networking is ready.

Webhook delivery from Brevo to Zeptalytic does not depend on static outbound egress IP. Static egress matters for outbound backend-to-Brevo API allowlisting if configured later.

40. Future Hardening

Future specs may improve webhook security and processing with:

provider-supported signature validation if Brevo offers a suitable signed webhook scheme
header-based secret instead of query parameter
rotating webhook secrets
separate webhook service layer
event processing queue
retry/dead-letter handling
admin delivery-event inspection UI/API
bounce suppression policy
communication-preference updates from unsubscribe events
complaint/spam escalation alerts
support dashboard indicators
delivery metrics dashboard
retention/archive/purge policy
production named tunnel/domain setup for local-like testing
Fly production smoke-test checklist

These are not first implementation requirements unless a future spec explicitly includes them.

41. Suggested Future Spec Items

A future implementation spec may include items like:

email-webhook-001: Add Brevo webhook configuration and .env.example placeholders
email-webhook-002: Add email_delivery_events model and Alembic migration
email-webhook-003: Register email delivery event model for Alembic/model import
email-webhook-004: Add email delivery event repository with dedupe-safe insert
email-webhook-005: Add Brevo event normalization helper/service
email-webhook-006: Add POST /api/v1/email/webhooks/brevo route with secret validation
email-webhook-007: Store valid Brevo webhook events with raw payload
email-webhook-008: Handle duplicate webhook events idempotently
email-webhook-009: Add tests for invalid secret, valid event, duplicate event, malformed payload, and unknown event
email-webhook-010: Add OpenAPI/runtime route coverage if project convention requires it
email-webhook-999: Run compileall and Docker test gate

These are suggestions only.

The actual spec-author run should inspect the repository and generate a final implementation spec based on real code.

42. Implementation Constraints for Future Agents

Future spec-author, plan, and build agents must obey these constraints:

Search before editing.
Inspect existing router conventions before adding webhook route.
Inspect existing config patterns before adding settings.
Inspect existing model/migration conventions before adding tables.
Use Alembic for schema changes.
Register new models through existing model import mechanism.
Do not commit real secrets.
Do not expose real webhook secret in docs/specs/tests.
Do not require user session for Brevo webhook route.
Do not require CSRF for Brevo webhook route.
Do not require internal service token for Brevo webhook route.
Validate webhook secret before processing payload.
Store raw payload as JSONB.
Deduplicate webhook events.
Return success for duplicates.
Normalize unknown events as unknown.
Do not mutate auth/account state from delivery events.
Do not mutate billing/payment state from delivery events.
Do not mutate Pay Service state.
Do not mutate support-ticket state.
Do not implement frontend code.
Do not edit frontend repo.
Do not invent newsletter automation.
Do not invent billing triggers.
Do not implement automatic retry worker in this phase.
Do not expose raw payloads through public APIs.
Do not log secrets or raw security tokens.
Run required test gates before marking complete.
Append progress entries to EOF if using progress/progress.txt.
Do not mark incomplete spec items complete.
43. Summary Decision

The Zeptalytic Web Backend will expose a public, secret-protected Brevo webhook endpoint at:

POST /api/v1/email/webhooks/brevo

The route will validate BREVO_WEBHOOK_SECRET, normalize Brevo transactional delivery events, deduplicate them, and store them in email_delivery_events with the raw payload preserved as JSONB.

Delivery events are operational telemetry.

They must not verify accounts, reset passwords, mutate billing state, mutate support state, or serve as source-of-truth for product access.

The first implementation will focus on safe ingestion, storage, deduplication, normalization, and testing.

Future specs may add retry workers, suppression logic, communication-preference updates, admin inspection tools, or stronger webhook signature validation.