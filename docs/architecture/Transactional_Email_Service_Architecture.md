# Transactional Email Service Architecture

**Target file:** `docs/architecture/Transactional_Email_Service_Architecture.md`  
**Status:** Draft / Architecture Reference  
**Project:** Zeptalytic Web Backend  
**Service:** Parent/backend application, not Pay Service  
**Provider:** Brevo transactional email  
**Mailbox/reply system:** Google Workspace  
**Primary future spec:** `specs/transactional_email_service_brevo.json`

---

## 1. Purpose

This document defines the backend architecture for Zeptalytic transactional email functionality.

The goal is to give future spec-author, plan, and build agent runs enough context to generate high-quality implementation specs for a Brevo-backed transactional email service in the Zeptalytic Web Backend.

This document is not an implementation spec by itself. It is a reference document that future implementation specs must absorb before making code changes.

The architecture must support:

- email verification emails
- password reset emails
- post-verification welcome emails
- account/security change notifications
- support-related transactional emails
- billing/order/payment templates configured for future integration
- news/update templates configured for future integration
- send-attempt logging
- delivery event ingestion from Brevo webhooks
- safe provider failure handling
- future retry/outbox worker expansion

The backend must be designed comprehensively enough to support the full template catalog from the start, while avoiding invented business triggers that have not yet been defined by product, billing, or newsletter workflows.

---

## 2. Current Context

The Zeptalytic Web Backend already has partial authentication and email-verification infrastructure.

Known existing backend capabilities include:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/verify-email`
- `POST /api/v1/auth/resend-verification`
- `AuthService.verify_email()`
- `AuthService.resend_email_verification()`
- `AuthService.forgot_password()`
- `AuthService.reset_password()`
- `EmailVerificationToken` model/table
- password reset token logic
- auth route tests for verification/resend behavior
- pending-verification account behavior

The backend does **not yet** have the complete transactional email architecture.

Missing pieces expected from this workstream:

- general `EmailService`
- Brevo API client abstraction
- Brevo configuration model/settings
- email send-attempt persistence
- email delivery event persistence
- Brevo webhook router
- delivery event normalization
- provider failure classification
- template catalog configuration
- tests covering send success, send failure, and webhook ingestion

---

## 3. Current Repository and Environment

Backend repo:

```bash
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

Authoritative test gates for this backend workstream:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

The frontend repo is separate:

~/Desktop/Dev/Zeptalytic_Web

This email-service workstream must not edit frontend code.

4. Relationship to Existing Email Decision Record

This architecture document depends on the decisions in:

docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md

That decision record establishes:

Brevo is the transactional email provider.
Google Workspace is the mailbox, alias, and human reply-handling system.
The backend sends through Brevo API.
Brevo does not log into Google Workspace.
DNS authorizes Brevo to send as zeptalytic.com.
Real reply-capable senders are used.
no-reply@zeptalytic.com is intentionally avoided.
Static Brevo authorized IP / allowlisting is deferred until Fly production static egress exists.
Send-attempt and delivery-event tracking are required from the first implementation.
Signup must not fail if email delivery fails.
Password-reset request responses must remain account-enumeration safe.

Future agents must read that decision record before generating or implementing email specs.

5. Scope
5.1 In Scope

The first implementation should include:

email configuration settings
Brevo client abstraction
EmailService abstraction
send-attempt table/model/repository
delivery-event table/model/repository
Alembic migrations for email tables
template catalog configuration
Brevo transactional send support
AuthService integration for:
signup verification email
resend verification email
forgot-password email
post-verification welcome email
password/account change notification where existing flow permits
Brevo webhook ingestion route
webhook secret validation
webhook event normalization
webhook deduplication
provider failure classification
tests for core service behavior
docs/OpenAPI alignment where applicable
5.2 Out of Scope for First Implementation

The first implementation must not include:

frontend page changes
frontend routing changes
newsletter automation
marketing campaign automation
billing/order/payment trigger implementation unless a separate Pay/billing integration spec defines it
support-ticket email workflow unless a separate support spec defines trigger rules
automatic retry worker
background outbox publisher
static egress IP setup
Fly.io deployment implementation
Brevo authorized IP configuration
Brevo DNS setup
email body rendering/storage
storing raw verification tokens
storing raw password reset tokens
changing the Pay Service
duplicating Pay commercial business rules
6. Primary Architectural Decision

The Zeptalytic Web Backend will use a provider-neutral internal EmailService that sends transactional emails through a Brevo-specific BrevoClient.

The backend will persist two separate operational records:

email_send_attempts
Records what the backend attempted to send.
email_delivery_events
Records what Brevo later reports through webhooks.

This separation is important because sending an email and receiving later delivery/open/click/bounce/spam events are separate operational facts.

A successful Brevo API response does not prove final delivery. It only proves that Brevo accepted or processed the send request. Final delivery state is reported later through Brevo delivery events.

7. Target Module Layout

Future implementation specs should prefer this structure unless existing project conventions strongly require a different location.

app/
  api/
    routers/
      v1/
        email_webhooks.py

  db/
    models/
      email_send_attempts.py
      email_delivery_events.py

    repositories/
      email_send_attempt_repository.py
      email_delivery_event_repository.py

  integrations/
    brevo_client.py

  schemas/
    email.py

  services/
    email_service.py

Potential existing files that may need updates:

app/core/config.py
app/api/routers/v1/__init__.py
app/db/models/__init__.py
app/db/models/import_models.py
app/services/auth_service.py
app/api/routers/v1/auth.py
tests/
alembic/versions/
.env.example

Future agents must search the repository before editing because exact project structure may differ.

8. Configuration Architecture

The backend should expose explicit configuration for the email provider, Brevo API, sender identities, frontend URL construction, and template IDs.

8.1 Required Environment Variables
EMAIL_PROVIDER=brevo
BREVO_API_BASE_URL=https://api.brevo.com/v3
BREVO_API_KEY=
BREVO_WEBHOOK_SECRET=

FRONTEND_BASE_URL=http://localhost:5173

EMAIL_FROM_ADDRESS=hello@zeptalytic.com
EMAIL_FROM_NAME=Zeptalytic
EMAIL_REPLY_TO_ADDRESS=support@zeptalytic.com

EMAIL_SUPPORT_FROM_ADDRESS=support@zeptalytic.com
EMAIL_BILLING_FROM_ADDRESS=billing@zeptalytic.com
EMAIL_ALERTS_FROM_ADDRESS=alerts@zeptalytic.com
EMAIL_UPDATES_FROM_ADDRESS=updates@zeptalytic.com

BREVO_TEMPLATE_WELCOME_ID=1
BREVO_TEMPLATE_SUPPORT_RESPONSE_ID=2
BREVO_TEMPLATE_ORDER_CONFIRMATION_ID=3
BREVO_TEMPLATE_NEWS_UPDATES_ID=4
BREVO_TEMPLATE_FAILED_SIGNUP_ID=5
BREVO_TEMPLATE_EMAIL_CHANGED_ID=6
BREVO_TEMPLATE_PASSWORD_RESET_ID=7
BREVO_TEMPLATE_ACCOUNT_DETAILS_CHANGED_ID=8
BREVO_TEMPLATE_EMAIL_VERIFICATION_ID=9
BREVO_TEMPLATE_PAYMENT_FAILED_ID=10
BREVO_TEMPLATE_SUBSCRIPTION_EXPIRING_ID=11
8.2 Recommended Additional Environment Variable
BREVO_REQUEST_TIMEOUT_SECONDS=10
8.3 Secret Handling Rules

Real secrets must only be stored in:

local .env, ignored by Git
Fly production secrets
secure runtime secret storage

Real secrets must not be stored in:

.env.example
Markdown docs
JSON specs
progress logs
docker-compose.yml
fly.toml
GitHub Actions workflow bodies
source code defaults

.env.example should contain placeholders only.

Example placeholder style:

BREVO_API_KEY=
BREVO_WEBHOOK_SECRET=

Do not include a real Brevo API key, webhook secret, or any value resembling xkeysib-*.

9. Sender Identity Architecture

The backend should route sender identity by email category.

9.1 Sender Matrix
Email category	From name/address	Reply-To
Auth/account/security	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com
General product/account	Zeptalytic <hello@zeptalytic.com>	support@zeptalytic.com
Support escalations/responses	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com
Billing/order/payment	Zeptalytic Billing <billing@zeptalytic.com>	billing@zeptalytic.com
Updates/news/newsletter	Zeptalytic Updates <updates@zeptalytic.com>	support@zeptalytic.com
System/operational alerts	Zeptalytic Alerts <alerts@zeptalytic.com>	support@zeptalytic.com
9.2 Important Rule

Do not use:

no-reply@zeptalytic.com

Zeptalytic will use real reply-capable sender identities.

10. Brevo Template Catalog

All known Brevo templates are active and should be represented in backend configuration from the start.

Template ID	Template name	Backend template key	Sender category	First-phase trigger
1	Initial Welcome Response	welcome	general/account	after successful email verification
2	Support Response	support_response	support	configured only unless support spec defines trigger
3	Order Confirmation	order_confirmation	billing	configured only; no trigger until Pay/billing spec
4	News & Updates	news_updates	updates	configured only; no newsletter automation yet
5	Failed Sign-up	failed_signup	support/security/internal	internal/security only unless future spec approves external use
6	email Changed	email_changed	auth/security	when email-change flow exists
7	Password Reset Request	password_reset	auth/security	forgot-password flow
8	Account details Changed	account_details_changed	auth/security	password/account detail change where existing flow permits
9	eMail Verification	email_verification	auth/security	signup and resend verification
10	Payment Failed	payment_failed	billing	configured only; no trigger until Pay/billing spec
11	Subscription Expiring	subscription_expiring	billing	configured only; no trigger until Pay/billing spec

The implementation should avoid hardcoding template IDs directly inside business logic. Template IDs should come from configuration.

11. EmailService Abstraction
11.1 Purpose

EmailService should be the backend’s main application-facing email interface.

Other services, such as AuthService, should call EmailService rather than calling Brevo directly.

This keeps provider-specific logic isolated.

11.2 Responsibilities

EmailService should:

select the correct template
select the correct sender and reply-to identity
build template parameters
call the provider client
create send-attempt records
update send-attempt state after provider response
classify provider failures
avoid leaking provider-specific details into domain services
avoid raising provider errors in flows where email failure should not fail the user action
11.3 Non-Responsibilities

EmailService should not:

own account lifecycle rules
verify auth tokens
generate raw verification tokens by itself unless existing code delegates that responsibility
generate raw password reset tokens by itself unless existing code delegates that responsibility
implement billing business rules
implement newsletter campaign rules
implement support-ticket lifecycle rules
mutate unrelated account/billing/support state based only on a Brevo event
store rendered email bodies
store raw security tokens
12. Suggested EmailService Methods

Future specs may adjust exact method names to match existing project style, but the first implementation should cover these concepts.

class EmailService:
    def send_email_verification(
        self,
        *,
        account_id: UUID,
        to_email: str,
        verification_url: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_password_reset(
        self,
        *,
        account_id: UUID | None,
        to_email: str,
        reset_url: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_welcome(
        self,
        *,
        account_id: UUID,
        to_email: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_account_details_changed(
        self,
        *,
        account_id: UUID,
        to_email: str,
        change_summary: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_email_changed(
        self,
        *,
        account_id: UUID,
        to_email: str,
        old_email: str | None = None,
        new_email: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_failed_signup_internal_alert(
        self,
        *,
        submitted_email: str | None,
        failure_code: str,
        correlation_id: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_support_response(
        self,
        *,
        account_id: UUID | None,
        to_email: str,
        ticket_code: str,
        subject: str,
        message: str,
    ) -> EmailSendResult:
        ...

    def send_order_confirmation(
        self,
        *,
        account_id: UUID,
        to_email: str,
        order_reference: str,
    ) -> EmailSendResult:
        ...

    def send_payment_failed(
        self,
        *,
        account_id: UUID,
        to_email: str,
        payment_reference: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_subscription_expiring(
        self,
        *,
        account_id: UUID,
        to_email: str,
        subscription_reference: str | None = None,
    ) -> EmailSendResult:
        ...

    def send_news_updates(
        self,
        *,
        account_id: UUID | None,
        to_email: str,
        params: dict,
    ) -> EmailSendResult:
        ...
12.1 Trigger Restrictions

Even if the service exposes methods for all templates, future build agents must only wire methods to existing flows where a trigger has been explicitly defined.

Allowed first-phase triggers:

signup email verification
resend email verification
forgot-password password reset email
post-verification welcome email
existing password reset/change notification if the current service already has a safe place to wire it

Not allowed without a separate spec:

billing order confirmation trigger
payment failed trigger
subscription expiring trigger
newsletter/news trigger
support response workflow trigger
account email-change trigger if no email-change flow currently exists
13. BrevoClient Abstraction
13.1 Purpose

BrevoClient should isolate all direct calls to Brevo.

Business services should not import httpx, Brevo endpoint URLs, or Brevo payload shapes directly.

13.2 Provider Endpoint

Brevo transactional send endpoint:

POST https://api.brevo.com/v3/smtp/email

Base URL should come from:

BREVO_API_BASE_URL=https://api.brevo.com/v3
13.3 Expected Client Responsibilities

BrevoClient should:

build authenticated Brevo API requests
apply request timeout
send transactional email payloads
parse Brevo responses
return a provider-neutral result object
raise or return classified provider errors in a controlled way
avoid logging secrets
avoid logging raw token URLs
avoid logging full rendered personal email contents
13.4 Recommended Timeout
10 seconds

The value should be configurable as:

BREVO_REQUEST_TIMEOUT_SECONDS=10
13.5 Brevo Payload Concept

The payload should conceptually include:

{
  "sender": {
    "name": "Zeptalytic Support",
    "email": "support@zeptalytic.com"
  },
  "to": [
    {
      "email": "user@example.com",
      "name": "User Display Name"
    }
  ],
  "replyTo": {
    "email": "support@zeptalytic.com",
    "name": "Zeptalytic Support"
  },
  "templateId": 9,
  "params": {
    "verificationUrl": "https://zeptalytic.com/verify-email?token=..."
  }
}

Exact payload shape must follow Brevo’s API and existing project conventions.

13.6 Provider Message ID

The client should capture the provider message identifier when Brevo returns one.

The exact field name may vary by Brevo response shape. Future implementation should confirm by inspecting actual API response and tests.

Store this value as:

email_send_attempts.provider_message_id

Delivery webhook events may later reference this provider message ID.

14. Send Attempt Persistence
14.1 Purpose

email_send_attempts records backend send attempts.

This table answers:

What did the backend try to send?
To whom?
From which sender?
Which template?
Which account, if known?
Did Brevo accept the request?
Did the provider request fail?
What provider message ID was returned?
What failure classification occurred?
14.2 Proposed Table Name
email_send_attempts
14.3 Proposed Model File
app/db/models/email_send_attempts.py
14.4 Proposed Repository File
app/db/repositories/email_send_attempt_repository.py
14.5 Proposed Fields

The implementation should adapt field names to existing backend naming conventions, but the table should conceptually include:

Field	Type	Required	Notes
id	UUID	yes	primary key
account_id	UUID	no	FK to accounts.id when account is known
to_email	string	yes	recipient
from_email	string	yes	sender address
from_name	string	no	sender display name
reply_to_email	string	no	reply-to address
template_key	string	yes	internal template key
provider	string	yes	default brevo
provider_template_id	integer	no	Brevo template ID
provider_message_id	string	no	Brevo message ID if returned
status	string/enum	yes	pending, sent, failed, skipped
failure_code	string	no	normalized failure code
failure_message	text	no	sanitized failure message
metadata_json	JSONB	no	safe non-token metadata
created_at	timestamp	yes	creation time
sent_at	timestamp	no	when provider accepted/sent
failed_at	timestamp	no	when send failed
14.6 Send Attempt Statuses

Required first-phase statuses:

pending
sent
failed
skipped

Meaning:

pending: backend created the attempt but provider result has not been recorded yet
sent: Brevo request succeeded or was accepted
failed: Brevo request failed or configuration prevented sending
skipped: backend intentionally skipped send due to disabled provider/configuration/future policy
14.7 Metadata Rules

metadata_json may store safe operational context, such as:

{
  "flow": "signup",
  "template_key": "email_verification",
  "correlation_id": "..."
}

metadata_json must not store:

raw verification tokens
raw password reset tokens
full verification URLs containing tokens
full reset URLs containing tokens
rendered email bodies
API keys
webhook secrets
sensitive provider authentication data
15. Delivery Event Persistence
15.1 Purpose

email_delivery_events records events Brevo later reports through webhooks.

This table answers:

What happened to an email after sending?
Was it delivered?
Was it opened or clicked?
Did it bounce?
Was it blocked?
Was it reported as spam/complaint?
Did Brevo provide an event ID or message ID?
What was the raw webhook payload?
15.2 Proposed Table Name
email_delivery_events
15.3 Proposed Model File
app/db/models/email_delivery_events.py
15.4 Proposed Repository File
app/db/repositories/email_delivery_event_repository.py
15.5 Proposed Fields
Field	Type	Required	Notes
id	UUID	yes	primary key
provider	string	yes	default brevo
event_type	string	yes	normalized event type
provider_message_id	string	no	message ID if provided
provider_event_id	string	no	provider event ID if provided
email	string	no	recipient email if provided
template_id	integer	no	Brevo template ID if provided
subject	string	no	subject if provided
event_timestamp	timestamp	no	provider event time
dedupe_key	string	yes	unique deduplication key
raw_payload	JSONB	yes	full provider webhook payload
created_at	timestamp	yes	ingestion time
15.6 Normalized Delivery Events

The first implementation should support these normalized event types:

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
15.7 Raw Payload Decision

Store the raw Brevo webhook payload as JSONB.

Reason:

improves debugging
supports future event fields without schema changes
enables support investigation
preserves provider evidence for delivery/bounce/complaint events

Restrictions:

raw payloads are sensitive operational data
do not expose raw payloads through public APIs
do not include raw payloads in normal user-facing responses
avoid logging raw payloads unless sanitized or in controlled debug/test output
15.8 Retention

First implementation should retain send attempts and delivery events indefinitely.

Retention, archive, or purge policies are future scope.

16. Alembic Migration Expectations

Future specs must include Alembic migrations for:

email_send_attempts
email_delivery_events

Migration requirements:

use UUID primary keys consistent with existing backend conventions
use timestamps consistent with existing backend conventions
use JSONB for metadata/raw payload fields in PostgreSQL
include indexes for common support/debug queries
include uniqueness on email_delivery_events.dedupe_key
include foreign key to accounts.id for email_send_attempts.account_id if account table is available and project conventions support it
avoid destructive migration behavior
ensure models are imported by the model-import registration system so SQLAlchemy/Alembic sees them

Recommended indexes:

email_send_attempts.account_id
email_send_attempts.to_email
email_send_attempts.template_key
email_send_attempts.status
email_send_attempts.provider_message_id
email_send_attempts.created_at

email_delivery_events.provider_message_id
email_delivery_events.email
email_delivery_events.event_type
email_delivery_events.template_id
email_delivery_events.event_timestamp
email_delivery_events.created_at
email_delivery_events.dedupe_key unique

Future agents must inspect existing migration style before creating migrations.

17. Brevo Webhook Ingestion Architecture
17.1 Route

First implementation route:

POST /api/v1/email/webhooks/brevo

First-phase secret-protected URL shape:

POST /api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>
17.2 Router File
app/api/routers/v1/email_webhooks.py
17.3 Security

The route is:

public
not user-session authenticated
not CSRF protected
not protected by internal service token
protected by webhook secret

The first implementation uses a query parameter secret.

Future hardening can switch to a better provider-supported signature/header pattern if Brevo configuration supports it cleanly.

17.4 Behavior

The route should:

validate the webhook secret first
reject invalid or missing secret
parse JSON payload
normalize Brevo event type
compute deterministic dedupe key
insert delivery event if new
return success for duplicate events
store raw payload
return quickly
avoid heavy business processing inside the route
17.5 Duplicate Handling

Duplicate webhook events should not create duplicate rows.

Duplicates should return HTTP 200 or an equivalent successful response so Brevo does not keep retrying valid already-processed events.

The unique key should be based on the best available provider identity.

Potential dedupe inputs, depending on Brevo payload:

provider event ID
provider message ID
email
event type
provider event timestamp
template ID
stable hash of raw payload if provider does not provide a clean event ID

Future implementation must inspect actual Brevo payload examples and tests.

17.6 Webhook Route Must Not

The webhook route must not:

require logged-in user session
require CSRF token
call frontend code
mutate billing/payment state
mutate support-ticket state
automatically unsubscribe users from Zeptalytic communication preferences unless a future communication-preferences spec defines this behavior
launch heavy background processing inline
expose webhook raw payloads publicly
18. Brevo Webhook Events to Track

The Brevo webhook should track transactional events corresponding to:

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

Event normalization should map provider-specific names into the backend normalized event types.

Example mapping concept:

Brevo/provider event	Normalized event
sent	sent
delivered	delivered
opened	opened
click / clicked	clicked
soft_bounce	soft_bounce
hard_bounce	hard_bounce
invalid / invalid_email	invalid_email
deferred	deferred
spam / complaint	complaint
unsubscribed	unsubscribed
blocked	blocked
error	error
unknown/unrecognized	unknown
19. Auth Integration Rules
19.1 Signup Flow

Current behavior to preserve:

user signs up
backend creates account
account status is pending_verification
backend creates session cookie
user is authenticated but restricted
pending-verification users can access support/resend verification
pending-verification users cannot access dashboard/product launch

Target email behavior:

create account/session/profile/preferences/security records
create email verification token
build verification URL
call EmailService.send_email_verification()
record send attempt
if email send succeeds, continue normally
if email send fails, still complete signup
user can use resend-verification endpoint

Signup must not fail only because Brevo send failed.

This is the chosen Option B behavior.

19.2 Verification URL

Local verification URL:

http://localhost:5173/verify-email?token=<token>

Production verification URL:

https://zeptalytic.com/verify-email?token=<token>

The backend should build this from:

FRONTEND_BASE_URL
19.3 Token Rules

Verification token rules:

raw token is generated server-side
only token hash is stored in DB
raw token exists only long enough to build verification URL
raw token is not logged in production
raw token is not stored in email_send_attempts.metadata_json
raw token is not stored in delivery events
verification token TTL should be 24 hours unless existing code already defines a different TTL
19.4 Resend Verification

Existing endpoint:

POST /api/v1/auth/resend-verification

Target behavior:

require appropriate authenticated pending-verification context
invalidate previous unused verification tokens where existing architecture permits
generate new token
build verification URL
send verification email through EmailService
record send attempt
return safe response

If Brevo send fails, return a controlled response consistent with existing UX/security behavior. Do not expose provider internals.

19.5 Successful Verification

On successful email verification:

mark account verified/active according to existing auth model
send Initial Welcome Response template #1
welcome email send failure must not undo verification
record welcome email send attempt

Welcome email timing decision:

Send welcome email after successful verification, not before.
20. Password Reset Integration Rules

Existing target endpoint:

POST /api/v1/auth/forgot-password

Target behavior:

always return generic success response
never reveal whether account exists
if account does not exist, return generic success without sending
if account is closed/ineligible, return generic success without revealing status
if account exists and is eligible, create password reset token
build reset URL
send Password Reset Request template #7
record send attempt
if Brevo send fails, still return generic success

Password reset URL:

http://localhost:5173/reset-password?token=<token>

Production reset URL:

https://zeptalytic.com/reset-password?token=<token>

Password reset token TTL:

2 hours

Token rules:

store only token hash
do not store raw reset token
do not log raw reset token in production
do not store full reset URL with token in send-attempt metadata

After successful password reset, send an account/security notification where existing service flow safely supports it, likely using:

Template #8 Account details Changed
21. Failed Signup Template Decision

Template:

#5 Failed Sign-up

This template should be treated as an internal support/security alert for first implementation.

Use case:

signup fails due to a generic internal or non-user-actionable error after a submitted signup attempt

Security posture:

do not send externally to arbitrary submitted email addresses unless future security review approves it
do not reveal account existence
do not include sensitive internal stack traces
do not include secrets
do not include raw password values
do not include raw tokens
do not include full database error messages

Future specs may add an internal alert behavior, but should avoid sending external failed-signup messages by default.

22. Provider Failure Handling
22.1 First-Phase Failure Policy

The first implementation should not include an automatic retry worker.

Instead:

create send attempt
call Brevo
mark send attempt sent or failed
return flow-appropriate response
allow user-triggered retry where applicable, such as resend verification or forgot password
22.2 Required Failure Codes

Normalize failures into controlled codes such as:

provider_timeout
provider_http_error
provider_invalid_config
provider_unavailable
provider_unexpected_response

Optional additional failure codes:

provider_auth_error
provider_rate_limited
template_not_configured
recipient_invalid
provider_disabled
unknown_error
22.3 User-Facing Failure Behavior

Signup:

account/session creation succeeds
verification email failure is recorded
user can resend verification

Forgot password:

response remains generic
do not reveal whether account exists
provider failure does not change generic response

Verification success welcome email:

verification remains successful
welcome email failure is recorded
do not roll back verification

Billing/news/support future triggers:

future specs must define user-facing failure behavior before wiring these triggers
23. Future Outbox Worker Support

The first implementation should not build a retry worker, but the schema and service design should not block one.

Future outbox-style support may include:

queued email jobs
retry count
next retry time
max retry policy
exponential backoff
dead-letter state
provider outage handling
admin/internal replay endpoint
worker process entrypoint

Current first-phase email_send_attempts table is a send log, not a full retry queue.

If future agents implement retries, they should either:

extend email_send_attempts carefully, or
introduce a separate email_outbox table.

Do not invent the retry worker in the first implementation.

24. PII and Sensitive Data Handling

The email system necessarily handles personal and operational data.

Allowed to store:

recipient email address
account ID when known
template key
provider template ID
provider message ID
normalized send status
normalized delivery event
raw Brevo webhook payload
safe operational metadata

Do not store:

rendered email body
raw verification token
raw password reset token
full verification URL containing token
full password reset URL containing token
Brevo API key
webhook secret
user passwords
sensitive stack traces
provider authorization headers

Raw webhook payloads are sensitive operational data and must not be returned from normal public APIs.

25. OpenAPI and API Surface Expectations

The Brevo webhook route should appear in OpenAPI unless the project intentionally excludes public webhook routes by established convention.

Future agents must check existing OpenAPI behavior and docs before deciding.

Expected public webhook route:

POST /api/v1/email/webhooks/brevo

The route should document:

purpose
secret query parameter
expected JSON body
successful duplicate handling
invalid secret response
malformed payload response

Do not expose secret values in generated OpenAPI examples.

26. Testing Expectations

Future implementation specs should require tests for the following.

26.1 Configuration Tests

Verify:

required config fields load correctly
missing Brevo API key is handled safely in test/dev mode according to project conventions
template IDs are read from configuration
frontend base URL is used for token links
no real secrets appear in test fixtures
26.2 BrevoClient Tests

Mock Brevo API and verify:

correct endpoint path
correct template ID
correct sender
correct reply-to
correct recipient
correct params
successful provider response returns normalized result
timeout maps to provider_timeout
HTTP error maps to provider_http_error
invalid response maps to provider_unexpected_response
API key is not logged
26.3 EmailService Tests

Verify:

send attempt is created
successful send marks attempt sent
failed send marks attempt failed
provider message ID is stored when available
raw tokens are not stored in metadata
correct template is selected for email verification
correct template is selected for password reset
correct sender category is selected
welcome email is separate from verification email
26.4 Auth Integration Tests

Verify:

signup succeeds even when EmailService/Brevo send fails
signup records failed send attempt when provider fails
signup records sent attempt when provider succeeds
resend verification sends new verification email
resend verification does not expose raw token
forgot-password returns generic response for unknown email
forgot-password returns generic response even when provider fails
password reset email send attempt is recorded when account exists
successful verification can trigger welcome email
welcome email failure does not undo verification
26.5 Webhook Tests

Verify:

missing secret is rejected
invalid secret is rejected
valid secret accepts event
raw payload is stored
event type is normalized
dedupe key prevents duplicate inserts
duplicate event returns success
unknown provider event maps to unknown
malformed payload returns controlled error
no user session is required
26.6 Migration/Model Tests

Verify:

migrations apply cleanly
models import correctly
Alembic autogenerate sees models
JSONB fields work under PostgreSQL
unique dedupe key works
indexes do not break test DB setup
26.7 Required Gates

Before marking implementation complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

Future agents must not mark spec items complete unless the relevant tests/gates pass or the blocker is explicitly documented.

27. Local Brevo Webhook Testing Context

A Cloudflare Quick Tunnel may be used for local Brevo webhook testing.

Backend must be running locally:

cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api
curl -i http://localhost:8000/health

Tunnel command:

cloudflared tunnel --url http://localhost:8000

Then test public tunnel health:

curl -i https://<trycloudflare-domain>.trycloudflare.com/health

Expected future webhook URL shape:

https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

If tunnel returns 502, the backend is likely not running or not reachable at http://localhost:8000.

If Brevo webhook test returns 404 before implementation, that is expected because the webhook route does not exist yet.

28. Deployment Context

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

Production Brevo secrets should be configured through Fly secrets, for example:

fly secrets set BREVO_API_KEY="..." -a zeptalytic-backend
fly secrets set BREVO_WEBHOOK_SECRET="..." -a zeptalytic-backend

Do not place these secrets in fly.toml.

Static outbound IP / Brevo authorized IP allowlisting is deferred until Fly production networking is ready.

29. Agent Workflow Expectations

This architecture document is intended to support the established harness-driven workflow.

Expected process:

write/update architecture reference docs
write/update harness guidance docs
run spec-author harness
generate implementation spec
run plan harness
run build harness
verify with compile/test/Docker gates
append progress entries to EOF if using progress/progress.txt

Likely future spec:

specs/transactional_email_service_brevo.json

Likely future spec items:

email-001: Add email/Brevo configuration
email-002: Add Brevo API client abstraction
email-003: Add email send attempt and delivery event models/migrations
email-004: Add email repositories
email-005: Add EmailService with template methods
email-006: Wire AuthService signup/resend/forgot-password/verify success to EmailService
email-007: Add Brevo transactional webhook route
email-008: Add tests for send success/failure and webhook ingestion
email-009: Add docs/OpenAPI/runtime surface checks
email-999: Run compileall and Docker test gate

The implementation plan usually contains an active spec line:

Active spec: specs/transactional_email_service_brevo.json

Agents must follow the existing project harness conventions.

30. Agent Constraints

Future spec-author, plan, and build agents must obey these constraints:

Search before editing.
Inspect existing project structure before adding files.
Follow existing naming conventions.
Use Alembic for schema changes.
Import new models through the existing model import mechanism.
Do not commit secrets.
Do not place real secrets in docs/specs/progress files.
Do not edit frontend repo.
Do not implement frontend routes/pages.
Do not edit Pay Service.
Do not duplicate Pay commercial logic.
Do not invent billing triggers.
Do not invent newsletter triggers.
Do not invent support-response triggers unless support spec defines them.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not store rendered email bodies.
Do not expose raw webhook payloads through public APIs.
Do not require user session for Brevo webhook route.
Do not add automatic retry worker in first implementation.
Do not mark incomplete spec items complete.
Append progress entries to EOF when progress logging is used.
Run required tests before marking items complete.
31. Security Requirements

The email architecture must preserve existing auth security expectations.

Required security properties:

pending-verification users remain restricted
signup does not expose internal email provider failures
forgot-password does not reveal whether account exists
raw tokens are not stored or logged
provider secrets are never committed
webhook route validates secret before processing
duplicate webhook events are safely handled
webhook route does not require session cookies
webhook route does not mutate unrelated business state
delivery events are treated as operational data
sender identities are explicit and controlled
provider failures are normalized and sanitized
32. Operational Debugging Goals

The implementation should make future support/debugging possible.

Support/debug questions the data model should answer:

Was a verification email attempted?
Did Brevo accept the send request?
Which template was used?
Which recipient was used?
Which sender was used?
Did the send fail due to provider timeout/config/HTTP error?
Did Brevo later report delivered/opened/clicked/bounced/blocked?
Did the user request resend verification?
Was a password reset email attempted without exposing account enumeration?
Did Brevo send duplicate webhook events?
What raw webhook payload did Brevo send?

The implementation does not need a frontend/admin UI for this in the first phase. Database inspection and logs are acceptable for first-phase operational visibility.

33. Future Work

Future specs may add:

retry/outbox worker
admin/internal email send inspection endpoint
support-ticket email workflow
billing email integration from Pay projections/events
newsletter/update campaign workflow
communication preference enforcement
unsubscribe/preference center logic
webhook signature hardening if Brevo supports the desired mechanism
delivery dashboard
bounce suppression logic
static egress IP and Brevo authorized IP allowlisting
production Fly smoke tests
richer email audit trails
data retention/archive policy

These are not part of the first implementation unless explicitly added by a future spec.

34. Implementation Readiness Checklist

Before generating implementation specs, confirm the following documents exist or are planned:

docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

Before building code, confirm:

Brevo template IDs are known
sender matrix is documented
secret handling rules are documented
webhook route shape is documented
signup failure behavior is documented
forgot-password account-enumeration behavior is documented
send-attempt and delivery-event schema expectations are documented
tests/gates are documented
frontend work is explicitly out of scope
35. Summary Decision

Zeptalytic Web Backend will implement transactional email through a provider-neutral EmailService backed by a Brevo-specific client.

The system will persist send attempts and delivery events separately.

The first implementation will integrate email verification, resend verification, forgot password, and post-verification welcome email behavior while configuring the full Brevo template catalog for future use.

Email provider failures must be recorded but must not break signup, forgot-password generic responses, or successful verification.

The first implementation will include Brevo webhook ingestion and delivery event storage, but will not include automatic retry workers, frontend changes, billing triggers, newsletter automation, or support workflow triggers unless separately specified.