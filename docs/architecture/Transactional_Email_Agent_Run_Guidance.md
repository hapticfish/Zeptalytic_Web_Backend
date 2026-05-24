# Transactional Email Agent Run Guidance

**Target file:** `docs/architecture/Transactional_Email_Agent_Run_Guidance.md`  
**Status:** Draft / Architecture Reference  
**Project:** Zeptalytic Web Backend  
**Service:** Parent/backend application, not Pay Service  
**Provider:** Brevo transactional email  
**Mailbox/reply system:** Google Workspace  
**Primary future implementation spec:** `specs/transactional_email_service_brevo.json`

---

## 1. Purpose

This document defines how future spec-author, plan, and build agent runs should create and implement the Zeptalytic Web Backend transactional email service workstream.

The workstream goal is to implement a Brevo-backed transactional email service for the parent Zeptalytic Web Backend while preserving existing auth behavior, protecting secrets, avoiding invented business logic, and following the existing harness-driven development workflow.

This document is intended for use by future agents that generate or execute implementation specs.

It should be read before creating or modifying:

```text
specs/transactional_email_service_brevo.json
IMPLEMENTATION_PLAN.md
prompt/prompt_spec_author.md
prompt/prompt_plan.md
prompt/prompt_build.md
progress/progress.txt
app/services/email_service.py
app/integrations/brevo_client.py
app/api/routers/v1/email_webhooks.py
app/db/models/email_send_attempts.py
app/db/models/email_delivery_events.py
app/db/repositories/email_send_attempt_repository.py
app/db/repositories/email_delivery_event_repository.py

This document is not itself the implementation spec. It is guidance for generating and executing the implementation spec correctly.

2. Related Architecture Documents

Future agents must read the following documents before generating implementation specs for the transactional email workstream:

docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

Expected responsibility of each document:

Brevo_Google_Workspace_Email_Decision_Record.md
Defines provider/mailbox/sender/reply-handling decisions.
Transactional_Email_Service_Architecture.md
Defines the overall backend architecture: EmailService, BrevoClient, send-attempt log, delivery-event log, provider failure behavior, and future retry/outbox boundary.
Auth_Email_Verification_Flow.md
Defines auth flow behavior for signup verification, resend verification, successful verification, welcome email, forgot password, password reset, and token safety.
Email_Delivery_Events_And_Webhooks.md
Defines Brevo webhook route, webhook secret validation, event normalization, deduplication, and delivery-event persistence.
Email_Template_Catalog.md
Defines all active Brevo template IDs, backend template keys, senders, trigger rules, and future-scope boundaries.
Transactional_Email_Agent_Run_Guidance.md
Defines how agents should produce and execute the implementation spec.
3. Current High-Level Goal

The immediate project goal is to prepare the Zeptalytic Web Backend for transactional email functionality using:

Brevo = transactional email provider
Google Workspace = mailbox, alias, and reply-handling system
Zeptalytic Web Backend = application logic, email service, provider API calls, send-attempt logging, webhook ingestion

The current focus is implementation-spec generation and later implementation.

The intended order is:

Capture architecture decisions and reference docs.
Create/update harness guidance docs for the email-service workstream.
Run spec-author harness to generate implementation spec.
Run plan harness.
Run build harness.
Verify with compile/test/Docker test gates.
Later perform local, Brevo, Cloudflare tunnel, and Fly smoke testing.

Architecture documents should come before implementation specs.

Implementation specs should come before code changes.

4. Current Backend Repository and Environment

Backend repo:

~/Desktop/Dev/Zeptalytic_Web_Backend

Known current branch previously shown in terminal:

codex/parent-db-foundation-plan-20260412-223903

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

Frontend repo is separate:

~/Desktop/Dev/Zeptalytic_Web

The transactional email backend workstream must not edit the frontend repo.

5. Local Backend Commands

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

Agents must not mark spec items complete unless the relevant tests pass or a blocker is explicitly documented.

6. Existing Harness Workflow

The project uses a harness-driven workflow similar to prior Zeptalytic backend work.

Known harness-related files and conventions:

scripts/ralph-loop.sh
scripts/ralph-audit.sh
prompt/prompt_spec_author.md
prompt/prompt_plan.md
prompt/prompt_build.md
progress/progress.txt
IMPLEMENTATION_PLAN.md
specs/*.json

The implementation plan usually includes an active spec line such as:

Active spec: specs/<spec_name>.json

For this workstream, the expected active spec should likely be:

Active spec: specs/transactional_email_service_brevo.json

Agents must inspect current project files before assuming exact names or behavior.

7. Expected Future Spec File

Primary expected implementation spec path:

specs/transactional_email_service_brevo.json

The spec-author run should create this file if it does not exist.

If it already exists, the spec-author or plan agent should review it for completeness against the architecture docs and update it if needed.

The spec should be JSON and follow existing project spec schema conventions.

Agents must inspect existing specs before generating a new one.

8. Required “Search Before Edit” Rule

Before modifying or creating implementation files, agents must search the repository.

Search goals:

identify existing auth service behavior
identify existing config/settings conventions
identify existing router conventions
identify existing SQLAlchemy model conventions
identify existing repository conventions
identify existing Alembic migration style
identify existing tests and fixtures
identify existing response schemas
identify existing OpenAPI/runtime surface tests
identify existing .env.example style
identify model import registration mechanism

Agents must not assume file names, class names, enum names, or table naming conventions without checking the repository.

9. Current Auth and Email Verification Context

The backend already has partial auth/email verification infrastructure.

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

Known current auth behavior to preserve:

User signs up.
Backend creates account.
Account status is pending_verification.
Session cookie is set.
User is authenticated but not verified.
Pending-verification users can access support/resend verification.
Pending-verification users cannot access normal dashboard/product launch.

Important auth response concepts already exist or are expected:

email_verification_required
can_access_support
can_access_billing
can_access_normal_authenticated_routes
can_access_product_launch

The transactional email implementation must preserve these behaviors.

10. Known Recent Backend Bug Context

A previous signup issue returned misleading duplicate-account 409 Conflict when the real failure was:

null value in column "discord_integration_status" of relation "profiles"

The fix involved setting:

discord_integration_status="pending"

when creating the profile.

Agents must not reintroduce misleading error handling where unrelated IntegrityError cases are converted into duplicate-account errors.

Signup should fail for real domain/database failures, but should not falsely report duplicate-account errors for unrelated insert failures.

11. Brevo Setup Context

Brevo account is already registered and configured.

Brevo API key has been generated.

Secrets/API values have been added to the backend local .env.

User verified that secrets are safe and .env is ignored/not exposed to Git.

Brevo templates are active.

Brevo webhook has previously been created using a Cloudflare Quick Tunnel URL.

A previous temporary tunnel base URL was:

https://bright-damages-empirical-art.trycloudflare.com

This URL is temporary and must not be committed as permanent configuration.

Expected local Brevo webhook URL shape:

https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

The route likely does not exist until implementation creates it.

If Brevo webhook testing returns 404 Not Found before implementation, that is expected.

12. Cloudflare Tunnel Testing Context

Cloudflare tunnel command:

cloudflared tunnel --url http://localhost:8000

If tunnel gives 502 Bad Gateway, the backend is likely not running or not reachable at:

http://localhost:8000

Testing sequence:

cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api
curl -i http://localhost:8000/health

cloudflared tunnel --url http://localhost:8000

curl -i https://<trycloudflare-domain>.trycloudflare.com/health

Future webhook test URL:

https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Do not commit temporary tunnel URLs.

13. Required Environment Variables

The implementation should support these config values:

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

Recommended additional config:

BREVO_REQUEST_TIMEOUT_SECONDS=10

.env.example should include placeholders only.

Real secrets must not appear in .env.example.

14. Secret Handling Rules

Real secrets belong only in:

local .env
Fly secrets
secure runtime secret storage

Real secrets must not be placed in:

.env.example
Markdown docs
JSON specs
progress logs
docker-compose.yml
fly.toml
GitHub Actions workflow body
source code defaults
tests
fixtures
OpenAPI examples

Never commit:

BREVO_API_KEY real value
BREVO_WEBHOOK_SECRET real value
xkeysib-* values
temporary token URLs
raw verification tokens
raw reset tokens

Recommended Git safety checks:

cd ~/Desktop/Dev/Zeptalytic_Web_Backend

cat .gitignore

git ls-files | grep -E '(^|/)\.env($|\.|-)'

git check-ignore -v .env || true

git grep -n "BREVO_API_KEY\|BREVO_WEBHOOK_SECRET\|xkeysib\|api-key" -- . || true

If .env is tracked:

git rm --cached .env
15. Google Workspace Sender Identities

Current Google Workspace email identities:

John Quinlan <john.quinlan@zeptalytic.com>
Zeptalytic Alerts <alerts@zeptalytic.com>
Zeptalytic Billing <billing@zeptalytic.com>
Zeptalytic Finance <finance@zeptalytic.com>
Zeptalytic <hello@zeptalytic.com>
Zeptalytic Security <security@zeptalytic.com>
Zeptalytic Support <support@zeptalytic.com>
Zeptalytic Updates <updates@zeptalytic.com>

Decision:

Use real reply-capable senders.
Do not use no-reply@zeptalytic.com.

Sender matrix:

Email category	From	Reply-To
Auth/account/security	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com
General product/account	Zeptalytic <hello@zeptalytic.com>	support@zeptalytic.com
Support escalations/responses	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com
Billing/order/payment	Zeptalytic Billing <billing@zeptalytic.com>	billing@zeptalytic.com
Updates/news/newsletter	Zeptalytic Updates <updates@zeptalytic.com>	support@zeptalytic.com
System/operational alerts	Zeptalytic Alerts <alerts@zeptalytic.com>	support@zeptalytic.com

john.quinlan@zeptalytic.com should not be used as an automated transactional sender.

finance@zeptalytic.com exists but is not the selected first-phase billing transactional sender.

16. Brevo Template Catalog

All current Brevo templates are active.

Backend must represent all template IDs from the start.

Template ID	Brevo template name	Backend template key	First-phase trigger
1	Initial Welcome Response	welcome	after successful email verification
2	Support Response	support_response	configure only unless support spec defines trigger
3	Order Confirmation	order_confirmation	configure only; no trigger until Pay/billing spec
4	News & Updates	news_updates	configure only; no newsletter automation yet
5	Failed Sign-up	failed_signup	internal/security only unless future spec approves external use
6	email Changed	email_changed	configure; wire only if existing email-change flow supports it
7	Password Reset Request	password_reset	forgot-password flow
8	Account details Changed	account_details_changed	password/account detail change where existing flow supports it
9	eMail Verification	email_verification	signup and resend verification
10	Payment Failed	payment_failed	configure only; no trigger until Pay/billing spec
11	Subscription Expiring	subscription_expiring	configure only; no trigger until Pay/billing spec

Agents may implement method coverage for all templates, but must not wire live triggers for future-scope templates unless a separate spec explicitly defines those triggers.

17. Primary Implementation Areas

The transactional email implementation spec should likely cover these backend areas:

configuration/settings
BrevoClient
EmailService
template catalog
sender profile resolver
email_send_attempts model/table/repository
email_delivery_events model/table/repository
Brevo webhook route
auth service integration
tests
OpenAPI/runtime route checks
docs/config examples

Expected target files may include:

app/core/config.py
app/integrations/brevo_client.py
app/services/email_service.py
app/schemas/email.py
app/api/routers/v1/email_webhooks.py

app/db/models/email_send_attempts.py
app/db/models/email_delivery_events.py

app/db/repositories/email_send_attempt_repository.py
app/db/repositories/email_delivery_event_repository.py

app/db/models/__init__.py
app/db/models/import_models.py

app/api/routers/v1/__init__.py

alembic/versions/
tests/
.env.example

Agents must inspect the actual project structure before using these paths.

18. EmailService Architecture Requirements

The implementation should introduce or complete a provider-neutral EmailService.

Other business/domain services should call EmailService.

They should not call Brevo directly.

Expected flow:

AuthService or other domain service
→ EmailService
→ BrevoClient
→ Brevo API

EmailService responsibilities:

select template
select sender/reply-to profile
build provider-neutral params
create send-attempt record
call BrevoClient
update send-attempt as sent/failed/skipped
normalize provider failure codes
avoid leaking provider internals to user-facing flows
avoid storing raw tokens in metadata

EmailService must not:

own account lifecycle rules
verify auth tokens
mutate Pay Service state
invent billing rules
invent newsletter rules
invent support ticket rules
store rendered email bodies
store raw verification tokens
store raw password reset tokens
19. BrevoClient Architecture Requirements

The implementation should introduce or complete a Brevo-specific API client.

Expected file:

app/integrations/brevo_client.py

Brevo transactional send endpoint:

POST https://api.brevo.com/v3/smtp/email

Base URL config:

BREVO_API_BASE_URL=https://api.brevo.com/v3

BrevoClient responsibilities:

build authenticated Brevo requests
send transactional template emails
apply timeout
parse provider response
return provider-neutral result
classify provider errors
avoid logging secrets
avoid logging raw token URLs

Recommended timeout:

10 seconds

Config key:

BREVO_REQUEST_TIMEOUT_SECONDS=10
20. Send Attempt Table Requirements

The implementation should add or complete:

email_send_attempts

Purpose:

Record what the backend attempted to send.

Conceptual fields:

Field	Type	Required	Notes
id	UUID	yes	primary key
account_id	UUID	no	FK to accounts.id when known
to_email	string	yes	recipient
from_email	string	yes	sender
from_name	string	no	sender display name
reply_to_email	string	no	reply-to
template_key	string	yes	internal template key
provider	string	yes	default brevo
provider_template_id	integer	no	Brevo template ID
provider_message_id	string	no	Brevo message ID if returned
status	string/enum	yes	send status
failure_code	string	no	normalized failure code
failure_message	text	no	sanitized failure message
metadata_json	JSONB	no	safe non-token metadata
created_at	timestamp	yes	creation time
sent_at	timestamp	no	provider accepted/sent time
failed_at	timestamp	no	failure time

Required statuses:

pending
sent
failed
skipped

Must not store:

raw verification token
raw password reset token
full token URL
rendered email body
Brevo API key
webhook secret
user password
session cookie
21. Delivery Event Table Requirements

The implementation should add or complete:

email_delivery_events

Purpose:

Record what Brevo later reported through webhooks.

Conceptual fields:

Field	Type	Required	Notes
id	UUID	yes	primary key
provider	string	yes	default brevo
event_type	string	yes	normalized event type
provider_message_id	string	no	provider message ID if available
provider_event_id	string	no	provider event ID if available
email	string	no	recipient email if provided
template_id	integer	no	Brevo template ID if provided
subject	string	no	subject if provided
event_timestamp	timestamp	no	provider event time
dedupe_key	string	yes	unique deterministic dedupe key
raw_payload	JSONB	yes	original webhook payload
created_at	timestamp	yes	backend ingestion time

Normalized event types:

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

The dedupe_key must be unique.

Duplicate webhook events should not create duplicate rows.

Duplicate webhook events should return successful response.

22. Alembic Migration Requirements

The implementation spec must include Alembic migrations for new email tables if they do not exist.

Migration requirements:

use UUID primary keys consistent with project convention
use timestamps consistent with project convention
use JSONB for metadata/raw payload fields
add indexes for support/debug queries
add unique constraint/index on email_delivery_events.dedupe_key
add account_id FK where project convention supports it
register new models so Alembic/autogenerate sees them
avoid destructive migrations

Recommended indexes:

email_send_attempts.account_id
email_send_attempts.to_email
email_send_attempts.template_key
email_send_attempts.status
email_send_attempts.provider_message_id
email_send_attempts.created_at

email_delivery_events.provider_message_id
email_delivery_events.provider_event_id
email_delivery_events.email
email_delivery_events.event_type
email_delivery_events.template_id
email_delivery_events.event_timestamp
email_delivery_events.created_at
email_delivery_events.dedupe_key unique

Agents must inspect existing migration style before writing migration files.

23. Brevo Webhook Route Requirements

First implementation route:

POST /api/v1/email/webhooks/brevo

Expected URL shape:

POST /api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Expected router file:

app/api/routers/v1/email_webhooks.py

Webhook route behavior:

validate secret first
reject missing/invalid secret
parse JSON body
normalize event type
extract provider message ID if available
extract provider event ID if available
extract recipient email if available
extract template ID if available
extract subject if available
extract event timestamp if available
compute deterministic dedupe key
store delivery event
store raw payload
return success for duplicate events
return quickly
avoid heavy business logic inline

The webhook route is:

public
provider-facing
not browser-session authenticated
not CSRF protected
not protected by internal service token
secret-protected

The webhook route must not:

verify accounts
reset passwords
mutate billing state
mutate Pay Service state
mutate support ticket state
trigger additional emails
unsubscribe users automatically
launch retry workers
expose raw payload publicly
24. Auth Integration Requirements

The first implementation should wire these auth-related flows.

24.1 Signup Verification

Existing endpoint:

POST /api/v1/auth/signup

Target behavior:

create account/session/profile/preferences/security records
set account status pending_verification
create verification token
store only token hash
build verification URL using FRONTEND_BASE_URL
send eMail Verification template through EmailService
record send attempt
return signup success even if email send fails

Signup must not fail solely because Brevo send failed.

24.2 Resend Verification

Existing endpoint:

POST /api/v1/auth/resend-verification

Target behavior:

confirm account is eligible and pending verification
invalidate previous unused verification tokens where supported
create new verification token
store only token hash
build verification URL
send eMail Verification template through EmailService
record send attempt
return safe response
24.3 Verify Email Success

Existing endpoint:

POST /api/v1/auth/verify-email

Target behavior:

verify backend token
mark token used
activate/verify account according to existing auth model
send Initial Welcome Response template through EmailService
record send attempt
do not undo verification if welcome email fails

Do not verify accounts based on Brevo open/click/delivered webhook events.

24.4 Forgot Password

Existing endpoint:

POST /api/v1/auth/forgot-password

Target behavior:

always return generic success
do not reveal account existence
if eligible account exists:
    create reset token
    store only token hash
    build reset URL
    send Password Reset Request template
    record send attempt
if Brevo send fails:
    still return generic success
24.5 Reset Password Completion

Existing endpoint:

POST /api/v1/auth/reset-password

Potential target behavior:

after successful password reset:
    send Account details Changed template if existing flow safely supports it
    record send attempt
    do not undo password reset if notification send fails

Agents must inspect existing reset-password flow before wiring this notification.

25. URL Construction Requirements

Email verification URL:

{FRONTEND_BASE_URL}/verify-email?token=<token>

Password reset URL:

{FRONTEND_BASE_URL}/reset-password?token=<token>

Local frontend base:

http://localhost:5173

Production frontend base:

https://zeptalytic.com

The backend should construct links using:

FRONTEND_BASE_URL

Agents must not implement frontend routes/pages in this workstream.

26. Token Safety Requirements

Required token rules:

store only token hashes in DB
raw token exists only long enough to build email URL
do not log raw tokens
do not store raw tokens in email_send_attempts.metadata_json
do not store full token URLs in metadata
do not store raw tokens in delivery events
do not expose token values in errors
do not include raw tokens in progress logs
do not include real raw tokens in docs/specs/tests

Use placeholders such as:

<token>

Recommended TTLs:

Email verification token TTL: 24 hours
Password reset token TTL: 2 hours

Agents must inspect existing TTLs before changing them.

27. Provider Failure Handling Requirements

First-phase failure policy:

No automatic retry worker.
Record failed send attempt.
Allow user-triggered retries where applicable.

Normalized failure codes:

provider_timeout
provider_http_error
provider_invalid_config
provider_unavailable
provider_unexpected_response

Optional additional codes:

provider_auth_error
provider_rate_limited
template_not_configured
recipient_invalid
provider_disabled
unknown_error

Failure behavior:

Flow	Provider failure behavior
Signup verification	signup still succeeds; failed send attempt recorded
Resend verification	controlled response; failed send attempt recorded
Forgot password	generic success still returned; failed send attempt recorded if account eligible
Welcome after verification	verification remains successful; failed send attempt recorded
Account details changed	account change remains successful; failed send attempt recorded
Billing/support/news templates	future specs must define

Do not expose provider internals to end users.

28. First-Phase Scope

The first implementation spec should include:

email/Brevo config values
BrevoClient abstraction
EmailService abstraction
template catalog and sender profiles
email_send_attempts table/model/repository
email_delivery_events table/model/repository
Brevo webhook route
event normalization
webhook deduplication
auth integration for signup/resend/forgot/verify success
tests for send success/failure behavior
tests for webhook ingestion behavior
OpenAPI/runtime surface checks if project convention requires them
.env.example placeholders
compile/test/Docker gates
29. Explicitly Out of Scope

The first implementation spec must not include:

frontend page changes
frontend route implementation
frontend repo edits
Pay Service edits
billing trigger implementation
order confirmation trigger implementation
payment failed trigger implementation
subscription expiring trigger implementation
newsletter/news automation
Brevo contact list sync
marketing campaign automation
support ticket workflow triggers
email-change workflow if not already present
automatic retry worker
email outbox worker
admin email dashboard
production Fly deployment
Brevo authorized IP/static egress setup
DNS setup
real secrets in files
rendered email body storage
raw token storage

Agents must avoid expanding scope beyond the approved transactional email backend implementation.

30. Future-Scope Items

Future specs may add:

email retry/outbox worker
email_outbox table
admin/internal delivery inspection API
support ticket email workflow
billing email integration from Pay events/projections
newsletter/update campaign workflow
communication preference enforcement
unsubscribe/preference-center logic
webhook signature hardening
header-based webhook secret
secret rotation
bounce suppression
complaint/spam escalation
static egress IP and Brevo authorized IP allowlisting
Fly production smoke tests
retention/archive/purge policy
delivery metrics dashboard

Do not implement these in the first transactional email spec unless explicitly added.

31. Recommended Spec Item Structure

The future implementation spec should be split into manageable items.

Suggested item list:

email-001: Add email and Brevo configuration
email-002: Add template catalog and sender profile resolver
email-003: Add BrevoClient abstraction
email-004: Add email_send_attempts model, repository, and migration
email-005: Add email_delivery_events model, repository, and migration
email-006: Add EmailService with full template method coverage
email-007: Wire signup verification email through EmailService
email-008: Wire resend verification email through EmailService
email-009: Wire forgot-password password reset email through EmailService
email-010: Wire successful verification welcome email through EmailService
email-011: Wire account details changed notification only if existing reset-password flow safely supports it
email-012: Add Brevo webhook route with secret validation
email-013: Add delivery event normalization and dedupe behavior
email-014: Add tests for config, catalog, sender mapping, BrevoClient, EmailService, auth integration, and webhook ingestion
email-015: Add OpenAPI/runtime surface checks where project convention requires
email-999: Run compileall and Docker test gate

The actual spec-author run should inspect the repository and generate final spec items based on real code.

Do not blindly copy this suggested item list if repository structure suggests a better split.

32. Spec Quality Requirements

The implementation spec should include for each item:

id
title
status/pass flag according to existing schema
category
intent
expected files
implementation steps
tests/verification steps
constraints
completion criteria

Each item should be small enough that a build agent can complete it safely.

Do not create vague items like:

implement email system

Prefer concrete items like:

email-004: Add email_send_attempts SQLAlchemy model, repository, and Alembic migration

Spec items must not be marked complete until work is actually done and verified.

33. Planning Agent Requirements

The plan agent should:

read the active spec
read all transactional email architecture docs
inspect current repo structure
identify existing auth/config/model/router/test conventions
plan implementation order
avoid editing files directly unless the harness expects planning edits
update IMPLEMENTATION_PLAN.md if required by project workflow
preserve Active spec line
document blockers clearly
avoid claiming implementation is complete

The plan agent must not:

invent billing triggers
invent newsletter triggers
invent support triggers
ignore existing tests
skip migration planning
skip model import registration
skip secret handling checks
skip auth pending-verification behavior
34. Build Agent Requirements

The build agent should:

read the active spec
read all transactional email architecture docs
search before editing
complete one or a small number of spec items per run
modify only necessary files
add tests with implementation
run targeted tests where possible
run required final gates before marking complete
append progress entries to EOF if progress logging is used
not mark blocked items complete

The build agent must not:

edit frontend repo
edit Pay Service
commit secrets
hardcode real secrets
store raw tokens
store rendered email bodies
use no-reply sender
call Brevo directly from AuthService
mutate account verification from webhook events
mutate payment state from email events
implement unsupported business triggers
implement retry worker unless future spec says so
35. Progress Logging Requirements

If the harness uses progress/progress.txt, progress entries must be append-only.

Rules:

append new entries to EOF
do not rewrite old progress entries
do not delete old progress entries
do not mark incomplete work complete
document blockers accurately
include verification commands/results where applicable

Do not put secrets in progress logs.

Do not put raw tokens in progress logs.

Do not put temporary full URLs containing secrets in progress logs.

For webhook testing, use placeholders like:

https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

not real secrets.

36. Required Tests by Area
36.1 Config Tests

Verify:

email provider config loads
Brevo API base URL loads
Brevo request timeout loads
Brevo webhook secret config exists
frontend base URL config exists
template IDs load from config
sender addresses load from config
.env.example uses placeholders only
36.2 Template Catalog Tests

Verify:

all 11 template keys exist
template keys map to correct config fields
sender profiles map to correct from/reply-to addresses
no no-reply sender is used
future-scope templates are configured but not accidentally triggered
36.3 BrevoClient Tests

Verify mocked provider behavior:

correct endpoint
correct auth header handling without exposing secret
correct template ID
correct sender
correct reply-to
correct recipient
correct params
success response parsed
provider message ID captured when available
timeout mapped to provider_timeout
HTTP error mapped to provider_http_error
unexpected response mapped to provider_unexpected_response
36.4 EmailService Tests

Verify:

send attempt created
successful send marks attempt sent
failed send marks attempt failed
provider message ID stored
template key stored
provider template ID stored
sender stored
reply-to stored
failure code stored
raw tokens not stored in metadata
rendered email body not stored
36.5 Auth Integration Tests

Verify:

signup sends email_verification through EmailService
signup succeeds when email sending fails
signup records failed send attempt on provider failure
pending-verification user remains restricted
resend verification sends email_verification
resend verification records send attempt
forgot-password returns generic success for unknown account
forgot-password returns generic success on provider failure
forgot-password sends password_reset when eligible account exists
successful verification sends welcome email
welcome email failure does not undo verification
password reset completion sends account_details_changed only if safely wired
raw tokens are not stored in metadata
36.6 Webhook Tests

Verify:

missing secret rejected
invalid secret rejected
valid secret accepted
valid event creates delivery event
raw payload stored
event type normalized
unknown event stored as unknown
duplicate event returns success and does not create duplicate row
malformed JSON returns controlled error
no user session required
no CSRF required
no account/billing/support state mutation occurs
36.7 Migration Tests

Verify:

Alembic migration applies
models import correctly
JSONB fields work in PostgreSQL
dedupe unique constraint works
indexes do not break test DB setup
test DB starts cleanly
36.8 OpenAPI/Runtime Surface Tests

If project convention includes route surface tests, verify:

POST /api/v1/email/webhooks/brevo appears or is intentionally excluded according to convention
auth routes remain present
OpenAPI contains no real secrets
OpenAPI examples use placeholders
37. Required Final Verification Gates

Before the workstream is considered complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

If either command fails:

do not mark spec complete
record blocker
fix issue or leave clearly documented

Agents must not claim success without test evidence.

38. Manual Smoke Testing After Implementation

After implementation and automated tests, local smoke testing can be performed.

38.1 Start Backend
cd ~/Desktop/Dev/Zeptalytic_Web_Backend
docker compose up -d --build db migrate api
curl -i http://localhost:8000/health
38.2 Test OpenAPI
curl -i http://localhost:8000/openapi.json
38.3 Start Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
38.4 Test Tunnel Health
curl -i https://<trycloudflare-domain>.trycloudflare.com/health
38.5 Configure Brevo Webhook Test URL
https://<trycloudflare-domain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>
38.6 Inspect Delivery Events

Use project-conventional DB access.

Example pattern, adjusted to actual DB env:

docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

Example query:

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
38.7 Inspect Send Attempts

Example query:

SELECT
    id,
    account_id,
    to_email,
    from_email,
    reply_to_email,
    template_key,
    provider,
    provider_template_id,
    provider_message_id,
    status,
    failure_code,
    created_at,
    sent_at,
    failed_at
FROM email_send_attempts
ORDER BY created_at DESC
LIMIT 20;

Do not paste real secrets into commands committed to docs, specs, or progress logs.

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

Production secrets should be configured through Fly secrets:

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

Do not configure Brevo Authorized IPs until Fly production static egress exists.

40. Agent Safety Constraints

Agents must obey these constraints:

Do not commit secrets.
Do not expose real secrets in generated files.
Do not edit frontend repo.
Do not edit Pay Service.
Do not implement billing triggers.
Do not implement newsletter triggers.
Do not implement support triggers.
Do not invent account email-change workflow.
Do not use no-reply@zeptalytic.com.
Do not store rendered email bodies.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not store full token URLs in metadata.
Do not log provider secrets.
Do not log webhook secrets.
Do not mutate account state from email delivery webhooks.
Do not mutate billing/payment state from email delivery webhooks.
Do not treat Brevo click/open events as user verification.
Do not create automatic retry worker in first phase.
Do not mark incomplete work complete.
41. Completion Criteria

The transactional email implementation workstream can be considered complete only when:

All required config exists with safe placeholders.
All active Brevo templates are represented in backend config/catalog.
Sender profiles are centralized.
EmailService exists and sends through BrevoClient.
BrevoClient handles success and normalized failures.
email_send_attempts table/model/repository exists.
email_delivery_events table/model/repository exists.
Alembic migrations apply cleanly.
AuthService uses EmailService for approved auth email triggers.
Signup succeeds even if verification email send fails.
Forgot-password remains account-enumeration safe.
Successful verification can send welcome email without rollback on email failure.
Brevo webhook route exists and validates secret.
Webhook route stores normalized/deduped delivery events.
Raw webhook payloads are stored as JSONB.
Tests cover config, templates, send attempts, provider failures, auth integration, and webhook ingestion.
No real secrets are committed.
No raw tokens are stored in operational metadata.
No frontend code is modified.
No Pay Service code is modified.
Compileall gate passes.
Docker test gate passes.
Progress/spec status is updated accurately.
42. Suggested Opening Prompt for Spec-Author Run

When ready to generate the implementation spec, use a prompt similar to:

We are ready to create the implementation spec for the Zeptalytic Web Backend transactional email service using Brevo.

Do not implement code yet. Generate or update the JSON spec for:

specs/transactional_email_service_brevo.json

Read and absorb these architecture docs first:

docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

The spec must cover:
- Brevo/email configuration
- template catalog and sender profiles
- BrevoClient abstraction
- EmailService abstraction
- email_send_attempts table/model/repository/migration
- email_delivery_events table/model/repository/migration
- auth integration for signup verification, resend verification, forgot-password, and post-verification welcome
- Brevo webhook route with secret validation
- delivery event normalization and deduplication
- tests and verification gates

Constraints:
- Do not edit frontend code.
- Do not edit Pay Service.
- Do not commit secrets.
- Do not invent billing/newsletter/support triggers.
- Do not implement automatic retry worker.
- Do not store raw tokens or rendered email bodies.
- Preserve signup success when email send fails.
- Preserve forgot-password account-enumeration safety.
- Preserve pending-verification restrictions.
- Require python -m compileall app tests alembic and docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test before completion.
43. Suggested Opening Prompt for Plan Run

After the spec exists, use a prompt similar to:

We are ready to plan the implementation of:

specs/transactional_email_service_brevo.json

Do not build yet unless the harness explicitly enters build mode.

Read the active spec and all transactional email architecture docs.

Inspect the current repository before planning:
- config/settings
- auth service/routes
- model/import conventions
- Alembic migrations
- repository patterns
- router patterns
- tests/fixtures
- OpenAPI/runtime tests
- .env.example

Create or update the implementation plan according to existing project conventions.

Do not mark anything complete.
Do not invent billing/newsletter/support triggers.
Do not edit frontend or Pay Service.
Preserve secret handling and token safety rules.
44. Suggested Opening Prompt for Build Run

When ready to implement, use a prompt similar to:

Build the next incomplete item from:

specs/transactional_email_service_brevo.json

Follow all architecture docs:
- Brevo_Google_Workspace_Email_Decision_Record.md
- Transactional_Email_Service_Architecture.md
- Auth_Email_Verification_Flow.md
- Email_Delivery_Events_And_Webhooks.md
- Email_Template_Catalog.md
- Transactional_Email_Agent_Run_Guidance.md

Search before editing.
Implement only the current spec item or a small safe group of related items.
Add tests with implementation.
Do not edit frontend repo.
Do not edit Pay Service.
Do not commit secrets.
Do not store raw tokens.
Do not store rendered email bodies.
Do not invent billing/newsletter/support triggers.
Do not mark the item complete unless verification passes.
Append progress to EOF if using progress/progress.txt.
45. Summary Decision

The transactional email implementation must be driven by architecture docs first, then a JSON implementation spec, then plan/build harness runs.

The first implementation should build a Brevo-backed transactional email service for the Zeptalytic Web Backend with:

EmailService
BrevoClient
template catalog
sender profile resolver
send-attempt persistence
delivery-event persistence
Brevo webhook ingestion
auth email integration
tests and verification gates

It must preserve:

signup success even if email send fails
forgot-password account-enumeration safety
pending-verification access restrictions
token hash-only persistence
real reply-capable sender identities
Pay Service commercial source-of-truth boundary
frontend repo separation

It must avoid:

committing secrets
using no-reply
storing raw tokens
storing rendered email bodies
inventing billing triggers
inventing newsletter triggers
inventing support triggers
implementing retry workers prematurely
mutating account/billing/support state from delivery webhooks

The implementation is complete only when the relevant spec items are done, tests pass, final gates pass, and progress/status updates are accurate.