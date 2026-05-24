Full replacement for IMPLEMENTATION_PLAN.md, based on the current file you pasted.

# Zeptalytic Web Backend Implementation Plan

Active spec: specs/transactional_email_service_brevo.json

## Current phase

The parent backend architecture/reference documents for the Brevo-backed transactional email workstream are now drafted.

The next phase is a focused backend implementation-spec generation and spec-driven development pass for transactional email functionality.

This pass prepares the FastAPI parent backend to send transactional emails through Brevo, log send attempts, ingest Brevo delivery webhooks, and wire approved auth/account email flows without expanding into frontend, Pay Service, billing, newsletter, or support workflow implementation.

The frontend repo is separate and must not be edited by this backend harness run.

The Zeptalytic Pay Service repo is separate and must not be edited by this backend harness run.

## Current active workstream

The active workstream is:

```text
specs/transactional_email_service_brevo.json

The target outcomes are:

Add explicit backend email/Brevo runtime configuration.
Add a stable template catalog and centralized sender profile resolver.
Add a Brevo API client abstraction.
Add a provider-neutral EmailService.
Add email_send_attempts persistence for backend send attempts.
Add email_delivery_events persistence for Brevo webhook delivery events.
Add Brevo webhook ingestion with secret validation, event normalization, and deduplication.
Wire only approved auth-related email flows:
signup email verification
resend email verification
forgot-password password reset email
post-verification welcome email
account-details-changed notification only where the existing reset/account flow safely supports it
Preserve signup success when verification email sending fails.
Preserve forgot-password account-enumeration safety.
Preserve pending-verification access restrictions.
Add tests for configuration, template mapping, sender mapping, Brevo client behavior, send-attempt logging, auth integration, webhook ingestion, and failure handling.
Run backend compile and Docker verification before marking implementation complete.
Required email/Brevo configuration

The backend should support these configuration values:

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

Recommended additional configuration:

BREVO_REQUEST_TIMEOUT_SECONDS=10

.env.example must contain placeholders only.

Real secrets must not be committed.

Real secrets must not appear in:

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
Sender identity contract

Brevo is the transactional sending provider.

Google Workspace owns mailboxes, aliases, and human reply handling.

The backend sends through Brevo.

Brevo does not log into Google Workspace.

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
Brevo template catalog

All current Brevo templates are active and should be represented in backend configuration from the start.

Template ID	Brevo template name	Backend template key	First-phase trigger
1	Initial Welcome Response	welcome	after successful email verification
2	Support Response	support_response	configure only unless support spec defines trigger
3	Order Confirmation	order_confirmation	configure only; no trigger until Pay/billing spec
4	News & Updates	news_updates	configure only; no newsletter automation yet
5	Failed Sign-up	failed_signup	internal/security only unless future spec approves external use
6	email Changed	email_changed	configure; wire only if existing email-change flow supports it
7	Password Reset Request	password_reset	forgot-password flow
8	Account details Changed	account_details_changed	password/account detail change where existing flow safely supports it
9	eMail Verification	email_verification	signup and resend verification
10	Payment Failed	payment_failed	configure only; no trigger until Pay/billing spec
11	Subscription Expiring	subscription_expiring	configure only; no trigger until Pay/billing spec
Backend-only scope

This backend workstream may update backend files such as:

app/core/config.py
app/integrations/brevo_client.py
app/services/email_service.py
app/schemas/email.py
app/api/routers/v1/email_webhooks.py
app/api/routers/v1/*
app/db/models/email_send_attempts.py
app/db/models/email_delivery_events.py
app/db/models/__init__.py
app/db/models/import_models.py
app/db/repositories/email_send_attempt_repository.py
app/db/repositories/email_delivery_event_repository.py
alembic/versions/*
tests/*
docs/architecture/*
docs/openapi/*
specs/transactional_email_service_brevo.json
progress/progress.txt
.env.example

Exact paths must be confirmed by repo search before editing.

This backend workstream must not modify:

../zeptalytic_web/*
frontend repo files
React/Vite source files
frontend API client files
frontend route files
frontend static data files
Zeptalytic Pay Service repo/files
unrelated service repos
Completed prior workstreams

The following workstreams are treated as complete and should not be re-opened unless a later spec explicitly requires corrections:

Parent DB foundation
Model file separation refactor
Parent DB verification and regression hardening
Discord identity schema correction
Rewards DB schema
Rewards verification/regression
Rewards API/application-layer schema work
Application-layer foundation
Auth/session/account security
Parent-to-Pay integration and projection foundation
Profile/settings/addresses/preferences API
Dashboard/launcher/billing aggregation API
Support/announcements/service status API
Rewards/objectives/badges application API
Discord integration application flow
Background jobs/security hardening
Frontend/backend contract alignment
Frontend runtime integration readiness, if completed in the repository
Spec authoring

Run:

./scripts/ralph-loop.sh spec_author 1

The spec-authoring agent must:

read the transactional email architecture docs
read relevant backend architecture/security/API contract docs
inspect repo reality
create or refine exactly one focused spec JSON
target specs/transactional_email_service_brevo.json
append a progress entry at EOF
not implement runtime code
not modify database models or migrations
not modify routers/services/repositories/schemas/integrations/workers
not modify tests
not edit frontend files
not edit Pay Service files
end with SPEC_DONE
Planning

After the spec exists, run:

./scripts/ralph-loop.sh plan 1

The planning agent must:

read the active spec
read transactional email architecture docs
inspect repo reality
refine only planning/spec/doc artifacts if needed
avoid runtime code implementation
avoid frontend repo edits
avoid Pay Service edits
append progress at EOF
end with PLAN_DONE
Build

After the plan is reviewed:

./scripts/ralph-loop.sh build 1

The build agent must:

read the active spec
choose exactly one item where passes=false
search before editing
implement the smallest safe backend change
add/update tests
run required verification
update only completed spec items
append progress at EOF
avoid frontend repo edits
avoid Pay Service edits
end with ITERATION_DONE, ALL_DONE, or ITERATION_BLOCKED
Full tests

Required verification before marking implementation complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

If either command cannot run, record the blocker in progress/progress.txt, do not mark the item complete, and stop safely.

Required architecture references

Read these before every relevant spec-authoring, planning, or build run:

docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md
docs/architecture/Auth_Session_and_Security_Flows.md
docs/architecture/Parent_Backend_Application_Architecture.md
docs/architecture/Parent_Backend_API_Contract_Standards.md
docs/architecture/Parent_Backend_Repository_Layer_Design.md
docs/architecture/Parent_Backend_Service_Layer_Design.md
docs/architecture/Security_Operational_Control_Guide.md
docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md
docs/architecture/Spec_Authoring_and_Harness_Workflow.md

Also read these when relevant:

docs/architecture/Parent_Pay_Integration_and_Projection_Strategy.md
docs/architecture/Frontend_Backend_Contract_Map.md
docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md
docs/architecture/Dashboard_Launcher_Billing_Aggregation_Design.md
docs/architecture/Support_Announcements_and_Status_Design.md
docs/architecture/Rewards_Application_and_Notification_Flows.md
docs/architecture/Discord_Integration_Application_Flow.md
docs/architecture/Background_Jobs_Sync_and_Event_Processing.md

Legacy/foundation references remain valid where relevant:

docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md
docs/architecture/Zeptalytic_Feature_Ownership_Register.md
docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md
docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md
docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md
docs/architecture/Discord_Integration_Decision_Record.md
docs/architecture/Rewards_Objectives_Badges_Domain_Decision_Record.md
docs/architecture/Rewards_Objectives_Badges_Data_Model_Reference.md
docs/architecture/Rewards_Objectives_Badges_UI_Interaction_Reference.md
docs/architecture/Discord_Rewards_Workstream_Sequence.md

docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md remains the canonical source for parent-site vocabulary, enum values, and status names.

Locked decisions
Parent backend is a domain backend with its own state and business logic.
Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, Stripe, and Coinbase Commerce.
Parent may initiate checkout/change/cancel/restart flows, but Pay executes commercial behavior.
Parent must not duplicate Pay commercial business rules.
Parent is the sole login authority for Zeptalytic accounts.
Product apps will trust parent-issued identity/session state.
Email verification is required for all normal actions except opening a support ticket.
Suspended users may log in and access billing/support.
account_id links parent and Pay.
Pay profile/customer identity should be created when parent account is created.
Account-link failures are internal operational issues.
APIs should be versioned under /api/v1.
Use domain routers plus aggregation routers.
Use standard error shape and simple mutation success/status responses.
Billing/payment method/transaction truth should come from Pay live reads where required.
Parent may mirror subscription/payment/entitlement/payment-method/product-access summaries as projections, but those are not editable commercial truth.
If Pay is unavailable, dashboard/billing should return safe null/empty values, launcher should not launch, and manage-subscription critical actions should be blocked.
Rewards APIs are read-oriented for frontend.
Reward writes come from backend jobs, admin/internal operations, Pay-derived events, or product-originated events.
Discord linkage is profile/settings display and signup capture only for phase 1.
Discord linkage does not affect rewards or product access.
Browser integration uses HTTP-only cookie sessions, not frontend-stored raw tokens.
Credentialed CORS must use explicit origins, not wildcard origins.
Brevo is the transactional email provider.
Google Workspace is the mailbox, alias, and human reply-handling system.
The backend sends transactional email through Brevo.
Brevo does not log into Google Workspace.
Use real reply-capable senders, not no-reply@zeptalytic.com.
Auth/account/security emails use Zeptalytic Support <support@zeptalytic.com> with support@zeptalytic.com reply-to.
General product/account emails use Zeptalytic <hello@zeptalytic.com> with support@zeptalytic.com reply-to.
Billing/order/payment emails use Zeptalytic Billing <billing@zeptalytic.com> with billing@zeptalytic.com reply-to.
Updates/news/newsletter emails use Zeptalytic Updates <updates@zeptalytic.com> with support@zeptalytic.com reply-to.
System/operational alerts use Zeptalytic Alerts <alerts@zeptalytic.com> with support@zeptalytic.com reply-to.
Signup must succeed even if verification email sending fails.
Forgot-password must remain account-enumeration safe.
Welcome email is sent after successful email verification, not before.
Email delivery webhook events are telemetry and must not verify accounts, reset passwords, mutate billing state, mutate Pay state, or mutate support state.
Billing/order/payment email triggers are future scope until a Pay/billing integration spec defines them.
Newsletter/update email triggers are future scope until a communications/newsletter spec defines them.
Support workflow email triggers are future scope until a support spec defines them.
Automatic email retry/outbox worker is future scope.
Raw verification tokens, raw password reset tokens, full token URLs, rendered email bodies, Brevo API keys, and webhook secrets must not be stored in operational metadata or committed files.
Progress rule

Every non-blocked run that changes files must append a progress entry to the absolute end of:

progress/progress.txt

The newest progress entry must be the final content in the file.