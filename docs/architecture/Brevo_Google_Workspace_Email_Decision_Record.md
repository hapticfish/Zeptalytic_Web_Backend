# Brevo + Google Workspace Email Decision Record

## Status

Accepted.

## Purpose

This document records the Zeptalytic transactional email decision for the parent web backend.

It defines how Zeptalytic will use Brevo, Google Workspace, DNS authentication, sender identities, webhook security, environment variables, and deployment-specific secret handling.

This document is intended to guide future spec-author, plan, and build harness runs. Agents must read this document before generating or implementing transactional email specs.

## Scope

This decision applies to the Zeptalytic Web Backend transactional email system, including:

- Email verification
- Password reset request emails
- Password reset/change notifications
- Email changed notifications
- Account details changed notifications
- Failed signup/security alert notifications
- Initial welcome emails
- Support response emails
- Order confirmation emails
- Payment failed emails
- Subscription expiring emails
- News and updates emails
- Future transactional email workflows

This document does not implement:

- Frontend verification-required pages
- Frontend verify-email pages
- Newsletter campaign automation
- Billing/payment lifecycle trigger logic
- Fly.io production deployment
- Fly static egress IP setup
- Brevo static IP allowlisting
- Admin email-delivery dashboards
- Background retry workers
- Provider failover

Those are separate future workstreams unless explicitly included in a later spec.

## Decision Summary

Zeptalytic will use:

```text
Google Workspace = human inboxes, aliases, and reply handling
Brevo = transactional email delivery provider
Zeptalytic Web Backend = application email logic, template selection, send attempts, and webhook ingestion
DNS = domain authorization for Brevo to send as zeptalytic.com

Brevo will not log into Google Workspace, authenticate through Google Workspace, or send through Gmail SMTP.

Brevo will send transactional email as authorized Zeptalytic domain addresses after zeptalytic.com is authenticated in Brevo/DNS.

Google Workspace remains the mailbox and reply-handling system for Zeptalytic business addresses.

Current Sender and Mailbox Inventory

The current Google Workspace address inventory includes:

John Quinlan <john.quinlan@zeptalytic.com>
Zeptalytic Alerts <alerts@zeptalytic.com>
Zeptalytic Billing <billing@zeptalytic.com>
Zeptalytic Finance <finance@zeptalytic.com>
Zeptalytic <hello@zeptalytic.com>
Zeptalytic Security <security@zeptalytic.com>
Zeptalytic Support <support@zeptalytic.com>
Zeptalytic Updates <updates@zeptalytic.com>

These addresses are treated as reply-capable Google Workspace-managed identities.

The backend must not assume these are SMTP accounts. The backend sends through Brevo’s transactional API.

Google Workspace vs Brevo Responsibility Split
Google Workspace Owns

Google Workspace owns:

Business inboxes
Human-readable sender identities
Alias/group/mailbox routing
Reply handling
Support/billing inbox management
Receiving replies from users

Examples:

support@zeptalytic.com
billing@zeptalytic.com
hello@zeptalytic.com
alerts@zeptalytic.com
updates@zeptalytic.com
Brevo Owns

Brevo owns:

Transactional email delivery
Template rendering through Brevo templates
Delivery tracking
Bounce tracking
Open/click tracking when enabled
Transactional webhook event delivery
Sender reputation and deliverability tooling
Backend Owns

The Zeptalytic Web Backend owns:

Which email should be sent
Which sender identity to use
Which template ID to use
Which template parameters to pass
Creation of send-attempt records
Handling provider send success/failure
Handling Brevo webhook events
Deduplication of webhook events
Linking sends/events to accounts when available
No-Reply Decision

Do not use no-reply@zeptalytic.com in the first transactional email architecture.

Use real reply-capable senders instead.

Rationale:

Users can reply to important account/security emails.
Support can help users who cannot verify or reset passwords.
Avoids dead-end reply behavior.
Simplifies current Google Workspace routing.
Better support and trust posture.
Sender Matrix
Auth and Account Emails

Use:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com

Applies to:

Email verification
Password reset request
Password reset/change notifications
Email changed notifications
Account details changed notifications
Failed signup/security alerts

Rationale:

These are account-access-sensitive emails.
Users need a real reply path if they cannot verify or reset their account.
Support should handle account-access issues.
General Product and Account Emails

Use:

From: Zeptalytic <hello@zeptalytic.com>
Reply-To: support@zeptalytic.com

Applies to:

Initial welcome response
General product/account messages that are not support, billing, alerts, or newsletters
Support Emails

Use:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com

Applies to:

Support response
Support ticket updates
Support escalations
User-facing support communication
Billing, Order, and Payment Emails

Use:

From: Zeptalytic Billing <billing@zeptalytic.com>
Reply-To: billing@zeptalytic.com

Applies to:

Order confirmation
Payment failed
Subscription expiring
Future billing/payment lifecycle emails

Billing-related templates may be configured in the email-service foundation, but actual billing/payment trigger behavior must not be invented in this workstream. Billing triggers must come from a future Pay/billing-specific spec or an existing confirmed backend flow.

Updates, News, and Newsletter Emails

Use:

From: Zeptalytic Updates <updates@zeptalytic.com>
Reply-To: support@zeptalytic.com

Applies to:

News and updates
Product update messages
Future newsletter-style communication

Newsletter campaign automation is out of scope unless a later spec explicitly includes it.

System and Operational Alerts

Use:

From: Zeptalytic Alerts <alerts@zeptalytic.com>
Reply-To: support@zeptalytic.com

Applies to:

Internal operational alerts
System alerts
Future incident/status notifications, if applicable

Operational alert delivery behavior must be explicitly defined before implementation. Agents must not invent alert triggers.

Brevo Template Catalog

All current Brevo templates should be represented in backend configuration from the start.

Current template IDs:

1  Initial Welcome Response
2  Support Response
3  Order Confirmation
4  News & Updates
5  Failed Sign-up
6  email Changed
7  Password Reset Request
8  Account details Changed
9  eMail Verification
10 Payment Failed
11 Subscription Expiring

Current decision:

All templates are active in Brevo.
All template IDs should be represented in backend config.
The EmailService may expose methods for all templates.
Agents must not invent business triggers for templates whose owning domain is not ready.
Billing/payment templates must wait for Pay/billing integration context.
News/newsletter templates must wait for newsletter/product-update context.
Failed signup/security alert behavior must avoid account-enumeration risks.
Failed Signup Template Decision

Template:

#5 Failed Sign-up

Meaning:

A failed signup means an attempt was made to sign up, but a generic internal error or non-user-actionable failure prevented normal completion.

Security caution:

Failed-signup emails can create account-enumeration and abuse risk if sent externally to arbitrary submitted email addresses.

First implementation guidance:

Prefer treating this template as an internal support/security alert.
Do not send failed-signup messages externally unless a later security review/spec explicitly allows it.
Do not include sensitive internal error details.
Do not reveal whether an account already exists.
Do not reveal duplicate-account details beyond existing approved signup behavior.
Brevo API Key Decision

Use separate Brevo API keys for local/dev and production.

Local/Dev Key

The local/dev Brevo API key is used for local development and pre-production testing.

Rules:

- Store only in local .env.
- Do not commit.
- Do not place in .env.example.
- Do not place in docker-compose.yml.
- Do not place in docs/specs/progress files.
- Rotate if accidentally exposed.
Production Key

The production Brevo API key is used only by the deployed production backend.

Rules:

- Store in Fly secrets when production deployment is ready.
- Do not commit.
- Do not place in fly.toml.
- Do not place in GitHub Actions workflow files.
- Do not expose in logs.
- Rotate separately from the dev key.

Rationale for separate keys:

Limits blast radius if a dev key leaks.
Allows independent rotation.
Separates dev/test traffic from production traffic.
Reduces operational risk.
Supports future Brevo account-level auditing.
Secret Storage Rules

Secrets must not be stored in:

docker-compose.yml
fly.toml
.env.example
README files
docs/
specs/
progress/
source code
tests
Git-tracked files
GitHub Actions workflow files unless they reference GitHub Secrets by name only

Secrets may be stored in:

Local development:
.env

Production runtime:
Fly secrets

CI/CD deployment authentication:
GitHub repository secrets, for example FLY_API_TOKEN

Sensitive values include:

BREVO_API_KEY
BREVO_WEBHOOK_SECRET
EMAIL_WEBHOOK_SECRET
FLY_API_TOKEN
Any future provider keys
Any OAuth client secrets
Any signing secrets
Required Environment Variables

The backend should support these environment variables.

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

Do not put real secret values in .env.example.

.env.example may contain empty placeholders and non-sensitive defaults only.

Brevo API Base URL

Use:

https://api.brevo.com/v3

The Brevo transactional email send endpoint should be built from this base URL:

POST /smtp/email

Full endpoint:

https://api.brevo.com/v3/smtp/email

The base URL must be configurable.

Rationale:

Supports testing with mocked provider URLs.
Avoids hardcoding provider endpoints throughout the codebase.
Keeps provider details centralized in the Brevo client.
Supports future provider migration or test harness overrides.
Domain Authentication Decision

Zeptalytic must authenticate zeptalytic.com in Brevo/DNS before production sending.

Required concepts:

SPF
DKIM
DMARC
Brevo domain verification records
Optional tracking domain
Optional bounce/return-path domain

Because Zeptalytic also uses Google Workspace, SPF must be merged into a single SPF TXT record. The project must not create multiple SPF TXT records for the same domain.

Do not blindly paste SPF examples into DNS. Use the exact values provided by Brevo and merge them with the existing Google Workspace SPF policy.

Static Egress IP Decision

Static egress IP allowlisting in Brevo is deferred.

Decision:

Do not configure Brevo Authorized IPs until Fly production deployment is ready.

Expected future production flow:

1. Deploy backend app on Fly.io.
2. Allocate app-scoped static egress IP for the backend app.
3. Add that IP to Brevo Security > Authorized IPs.
4. Validate production transactional email sends.

Static egress IP is not required for:

Architecture docs
Spec generation
Local backend development
Local Docker Compose testing
Initial Brevo client implementation
Initial webhook implementation
Deployment Context

The broader Zeptalytic deployment direction is:

Local Docker Compose development
→ Git push / tag
→ GitHub Actions
→ Fly.io production

Initial Fly.io production architecture:

React frontend container
Python backend API container
Single-node Fly Postgres with persistent volume
Future product apps/workers on Fly private mesh
Later backend static egress IP for Brevo security allowlisting

The email-service architecture must not assume a non-Fly deployment platform.

The implementation should remain portable and container-friendly.

Webhook URL Decision

The backend will expose:

POST /api/v1/email/webhooks/brevo

First-phase local and production webhook verification will use query-secret verification:

POST /api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Local tunnel example:

https://<trycloudflare-subdomain>.trycloudflare.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Production example:

https://api.zeptalytic.com/api/v1/email/webhooks/brevo?secret=<BREVO_WEBHOOK_SECRET>

Do not hardcode local tunnel URLs in source code.

The current local Cloudflare quick tunnel pattern is acceptable for testing, but quick tunnel URLs are temporary and not production-stable.

Webhook Route Security Decision

The Brevo webhook route is public but secret-protected.

It must not require:

User session cookie
Authenticated user context
CSRF browser-session validation
Internal service token
Google Workspace credentials
Brevo API key in the request

First-phase verification:

Request query parameter `secret` must match BREVO_WEBHOOK_SECRET.

If Brevo later supports custom webhook headers or signed payload verification in the available account/plan, a future hardening spec may migrate to header/signature verification.

Webhook Events to Track

The backend should ingest and normalize these Brevo transactional webhook events:

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

Brevo UI may display similar events with slightly different labels. The backend should normalize provider names into the internal event vocabulary above.

Webhook Handling Rules

The webhook route must:

Validate the webhook secret before processing.
Return quickly.
Store the event.
Store raw payload.
Deduplicate repeated events.
Return success for duplicate events.
Avoid heavy business logic inside the webhook request.
Avoid sending emails from inside the webhook route.
Avoid mutating unrelated account/billing/support state unless a later spec explicitly adds a processor.

Recommended duplicate behavior:

If dedupe_key already exists:
- Return 200 OK.
- Do not insert a duplicate row.

Recommended invalid-secret behavior:

- Return 401 or 403.
- Do not store the payload.
- Do not reveal internal details.
Raw Webhook Payload Decision

Store full raw Brevo webhook payloads in the database as JSONB.

Rationale:

Operational evidence.
Support troubleshooting.
Provider payloads may change.
Future reconciliation may need raw fields.
Delivery evidence is useful when users report missing emails.

Raw payloads may contain PII and must be treated as sensitive operational data.

Email Send Attempt and Delivery Event Retention

First implementation should keep email send attempts and delivery events indefinitely.

Rationale:

Initial email volume is expected to be low.
Early-stage support/debugging requires visibility.
Delivery evidence is useful for account access issues.
Retention/archive policy can be introduced later.
Premature deletion complicates troubleshooting.

A future retention/archive policy may define:

Time-based retention
PII minimization
Admin export
Deletion/anonymization
Compliance-based retention windows
PII Handling Decision

Email-related records may contain PII.

Rules:

Store recipient email addresses when needed for support/debugging.
Store account ID when available.
Store provider message ID when available.
Store provider template ID.
Store template key.
Store provider response metadata.
Store raw webhook payload.
Do not store raw rendered email body content.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not expose delivery logs through public APIs.
Do not log secrets or raw tokens.
Brevo Webhook vs Brevo UI

Brevo UI may show delivery, bounce, open, click, and transactional logs.

The backend should still ingest webhooks because Brevo UI is not Zeptalytic’s application-level source of truth.

Backend webhook ingestion is needed for:

Support troubleshooting
Delivery evidence
Future admin/support views
Future suppression handling
Future bounce/complaint workflows
Internal auditability
Provider-independent operational records
Signup Email Failure Decision

Signup must follow Option B:

Account/session creation succeeds even if Brevo send fails.
Send attempt is recorded as failed.
User can resend verification.

Rationale:

Better user experience.
Prevents provider outage from blocking account creation.
Allows recovery through resend verification.
Separates critical account creation from non-critical email delivery.
Password Reset Email Failure Decision

Forgot-password must remain account-enumeration safe.

If Brevo sending fails:

- Record failed send attempt.
- Return the generic forgot-password response.
- Do not reveal account existence.
- Do not reveal provider failure to the requester.
Template Activation Decision

All current Brevo templates are active and final for the first implementation.

Template IDs should be treated as stable for now, but the backend must still read them from config instead of hardcoding them into domain logic.

Agent Instructions

Spec-author, plan, and build agents must:

Read this decision record before generating transactional email specs.
Respect Google Workspace vs Brevo separation.
Never commit real secrets.
Use environment-variable names only in docs/specs.
Keep Brevo provider details behind a Brevo client abstraction.
Keep business-level email behavior in an EmailService abstraction.
Avoid direct Brevo calls inside AuthService or other domain services.
Add or update .env.example with placeholders only.
Keep real secrets in local .env or Fly secrets only.
Avoid inventing Pay/billing triggers in this workstream.
Avoid implementing frontend code in the backend repository.
Search existing code before editing.
Follow existing project structure.
Use Alembic migrations for new database tables.
Add tests for config, sending, failure handling, webhook security, and webhook deduplication.
Do not mark spec items complete unless compile/test gates pass.