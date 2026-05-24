# Email Template Catalog

**Target file:** `docs/architecture/Email_Template_Catalog.md`  
**Status:** Draft / Architecture Reference  
**Project:** Zeptalytic Web Backend  
**Service:** Parent/backend application, not Pay Service  
**Provider:** Brevo transactional email  
**Mailbox/reply system:** Google Workspace  
**Primary future spec:** `specs/transactional_email_service_brevo.json`

<!-- Source context for this architecture document came from the uploaded transactional email / Brevo transfer summary. :contentReference[oaicite:0]{index=0} -->

---

## 1. Purpose

This document defines the Zeptalytic transactional email template catalog for the parent Zeptalytic Web Backend.

The purpose is to give future spec-author, plan, and build agent runs a complete reference for:

- active Brevo templates
- backend template keys
- template IDs
- intended sender identity
- intended reply-to identity
- expected trigger rules
- first-phase versus future-scope behavior
- required backend configuration
- template parameter expectations
- security restrictions
- provider failure behavior
- send-attempt logging expectations
- agent constraints for implementation specs

This document is not an implementation spec. It is an architecture/reference document that future implementation specs must absorb before generating or implementing transactional email work.

The main implementation goal is to configure the full Brevo template catalog from the start, while only wiring templates to backend triggers that are explicitly approved for the first transactional email implementation phase.

---

## 2. Related Architecture Documents

This document belongs to the Zeptalytic transactional email architecture set.

Related docs:

```text
docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

Expected division of responsibility:

Brevo_Google_Workspace_Email_Decision_Record.md defines Brevo, Google Workspace, sender identity, and reply-handling decisions.
Transactional_Email_Service_Architecture.md defines EmailService, BrevoClient, send-attempt logging, delivery-event logging, and provider failure behavior.
Auth_Email_Verification_Flow.md defines auth-specific transactional email behavior.
Email_Delivery_Events_And_Webhooks.md defines Brevo webhook ingestion and delivery event persistence.
Email_Template_Catalog.md defines templates, senders, parameters, trigger rules, and first-phase/future-scope boundaries.
Transactional_Email_Agent_Run_Guidance.md defines how spec-author, plan, and build agent runs should operate.
3. Current Backend Context

The Zeptalytic Web Backend already has partial auth/email-verification infrastructure.

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
pending-verification account behavior

The backend does not yet have a complete general transactional email service.

Missing pieces expected from the transactional email workstream include:

general EmailService
Brevo API client abstraction
template catalog configuration
sender identity resolver
send-attempt table/model/repository
delivery-event table/model/repository
Brevo webhook router
provider failure classification
tests for email send success/failure behavior
tests for template selection and sender selection

This document defines the template catalog that the future EmailService should use.

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

This email template catalog workstream must not edit frontend code.

5. Provider and Mailbox Responsibility Split

Zeptalytic email architecture uses three separate responsibility layers:

Google Workspace = mailboxes, aliases, human reply handling
Brevo = transactional sending infrastructure and delivery telemetry
Zeptalytic Web Backend = application logic, template selection, API calls to Brevo, send-attempt records, webhook ingestion

Brevo does not log into Google Workspace.

Google Workspace does not directly send application transactional emails.

The backend sends transactional emails through Brevo.

DNS authorizes Brevo to send as zeptalytic.com.

Replies should go to real Google Workspace mailboxes or aliases.

Do not use no-reply@zeptalytic.com.

6. Current Google Workspace Sender Inventory

Known Google Workspace identities:

John Quinlan <john.quinlan@zeptalytic.com>
Zeptalytic Alerts <alerts@zeptalytic.com>
Zeptalytic Billing <billing@zeptalytic.com>
Zeptalytic Finance <finance@zeptalytic.com>
Zeptalytic <hello@zeptalytic.com>
Zeptalytic Security <security@zeptalytic.com>
Zeptalytic Support <support@zeptalytic.com>
Zeptalytic Updates <updates@zeptalytic.com>

Not all identities need to be used by the first implementation.

The primary transactional senders for this workstream are:

hello@zeptalytic.com
support@zeptalytic.com
billing@zeptalytic.com
alerts@zeptalytic.com
updates@zeptalytic.com

john.quinlan@zeptalytic.com is a personal/human mailbox and should not be used as an automated transactional sender.

finance@zeptalytic.com exists but is not the selected first-phase billing sender. Billing/order/payment transactional emails should use billing@zeptalytic.com.

7. Sender Matrix

The backend should route sender identity by email category.

Email category	From name/address	Reply-To	First-phase use
Auth/account/security	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com	yes
General product/account	Zeptalytic <hello@zeptalytic.com>	support@zeptalytic.com	yes for welcome
Support escalations/responses	Zeptalytic Support <support@zeptalytic.com>	support@zeptalytic.com	configured only unless support spec defines trigger
Billing/order/payment	Zeptalytic Billing <billing@zeptalytic.com>	billing@zeptalytic.com	configured only; no trigger until billing/Pay spec
Updates/news/newsletter	Zeptalytic Updates <updates@zeptalytic.com>	support@zeptalytic.com	configured only; no newsletter automation yet
System/operational alerts	Zeptalytic Alerts <alerts@zeptalytic.com>	support@zeptalytic.com	configured only unless alert spec defines trigger

Important:

Use real reply-capable senders.
Do not use no-reply@zeptalytic.com.
8. Template Catalog Summary

All current Brevo templates are active.

The backend should represent all template IDs from the start.

Brevo template ID	Brevo template name	Backend template key	Category	First-phase trigger status
1	Initial Welcome Response	welcome	general/account	wire after successful email verification
2	Support Response	support_response	support	configure only; no trigger unless support spec defines it
3	Order Confirmation	order_confirmation	billing	configure only; no trigger until Pay/billing integration spec
4	News & Updates	news_updates	updates/newsletter	configure only; no newsletter automation yet
5	Failed Sign-up	failed_signup	support/security/internal	internal/security only unless future spec approves external use
6	email Changed	email_changed	auth/security	configure; wire only if existing email-change flow supports it
7	Password Reset Request	password_reset	auth/security	wire to forgot-password flow
8	Account details Changed	account_details_changed	auth/security	wire to password/account detail change where existing flow safely supports it
9	eMail Verification	email_verification	auth/security	wire to signup and resend verification
10	Payment Failed	payment_failed	billing	configure only; no trigger until Pay/billing integration spec
11	Subscription Expiring	subscription_expiring	billing	configure only; no trigger until Pay/billing integration spec
9. Required Backend Configuration

The backend should support all template IDs through configuration.

Required environment variables:

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

Template IDs must not be hardcoded inside business logic.

The implementation can map config values into a template catalog object, enum, dataclass, Pydantic settings object, or project-conventional config structure.

10. Secret and Config Safety Rules

Real secrets belong only in:

local .env, ignored by Git
Fly production secrets
secure runtime secret storage

Real secrets must not appear in:

.env.example
Markdown docs
JSON specs
progress logs
docker-compose.yml
fly.toml
GitHub Actions workflow bodies
source code defaults

.env.example should contain placeholders only:

BREVO_API_KEY=
BREVO_WEBHOOK_SECRET=

Do not commit values resembling:

xkeysib-...

Do not commit real webhook secrets.

Do not commit temporary Cloudflare tunnel URLs as production config.

11. Backend Template Key Naming

The backend should use stable internal template keys independent from Brevo display names.

Recommended template keys:

welcome
support_response
order_confirmation
news_updates
failed_signup
email_changed
password_reset
account_details_changed
email_verification
payment_failed
subscription_expiring

Reasons:

Brevo display names may contain inconsistent capitalization.
Brevo display names may change.
Backend logic should not depend on display names.
Tests can assert stable internal keys.
Send-attempt records become easier to query.

The email_send_attempts.template_key field should store these backend keys.

The email_send_attempts.provider_template_id field should store the Brevo numeric template ID.

12. Template Catalog Implementation Shape

Future implementation may represent the catalog using project-conventional patterns.

Acceptable approaches include:

enum of template keys
constants module
Pydantic settings fields
dataclass registry
dictionary mapping template key to provider template ID and sender category

Potential conceptual structure:

class EmailTemplateKey(str, Enum):
    WELCOME = "welcome"
    SUPPORT_RESPONSE = "support_response"
    ORDER_CONFIRMATION = "order_confirmation"
    NEWS_UPDATES = "news_updates"
    FAILED_SIGNUP = "failed_signup"
    EMAIL_CHANGED = "email_changed"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_DETAILS_CHANGED = "account_details_changed"
    EMAIL_VERIFICATION = "email_verification"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"

Potential conceptual registry:

EMAIL_TEMPLATE_CATALOG = {
    "welcome": {
        "provider_template_id_setting": "BREVO_TEMPLATE_WELCOME_ID",
        "category": "general_account",
        "sender_profile": "hello",
        "first_phase_trigger": "after_successful_email_verification",
    },
    "email_verification": {
        "provider_template_id_setting": "BREVO_TEMPLATE_EMAIL_VERIFICATION_ID",
        "category": "auth_security",
        "sender_profile": "support",
        "first_phase_trigger": "signup_and_resend_verification",
    },
}

Exact implementation should follow existing backend code style.

13. Sender Profile Implementation Shape

Future implementation may define sender profiles so the EmailService can select sender/reply-to consistently.

Potential conceptual sender profiles:

class EmailSenderProfile(str, Enum):
    HELLO = "hello"
    SUPPORT = "support"
    BILLING = "billing"
    ALERTS = "alerts"
    UPDATES = "updates"

Potential conceptual mapping:

SENDER_PROFILES = {
    "hello": {
        "from_name": "Zeptalytic",
        "from_email": settings.email_from_address,
        "reply_to_email": settings.email_reply_to_address,
    },
    "support": {
        "from_name": "Zeptalytic Support",
        "from_email": settings.email_support_from_address,
        "reply_to_email": settings.email_support_from_address,
    },
    "billing": {
        "from_name": "Zeptalytic Billing",
        "from_email": settings.email_billing_from_address,
        "reply_to_email": settings.email_billing_from_address,
    },
    "alerts": {
        "from_name": "Zeptalytic Alerts",
        "from_email": settings.email_alerts_from_address,
        "reply_to_email": settings.email_support_from_address,
    },
    "updates": {
        "from_name": "Zeptalytic Updates",
        "from_email": settings.email_updates_from_address,
        "reply_to_email": settings.email_support_from_address,
    },
}

Do not scatter sender logic across unrelated services.

Sender selection should be centralized in EmailService, a catalog helper, or a project-conventional equivalent.

14. Template #1 — Initial Welcome Response
14.1 Catalog Entry
Brevo template ID: 1
Brevo template name: Initial Welcome Response
Backend template key: welcome
Category: general/account
Sender profile: hello
14.2 Sender
From: Zeptalytic <hello@zeptalytic.com>
Reply-To: support@zeptalytic.com
14.3 First-Phase Trigger

Wire this template after successful email verification.

Target flow:

User signs up
→ account status pending_verification
→ user verifies email through backend token endpoint
→ account becomes verified/active according to existing auth model
→ EmailService sends welcome email
14.4 Failure Policy

Welcome email failure must not undo successful verification.

If Brevo send fails:

record failed send attempt
keep account verified
do not expose provider internals to user
do not roll back account status
14.5 Possible Template Parameters

Exact Brevo params should match the actual Brevo template, but conceptually this template may need:

{
  "displayName": "John",
  "loginUrl": "https://zeptalytic.com/login",
  "dashboardUrl": "https://zeptalytic.com/dashboard",
  "supportEmail": "support@zeptalytic.com"
}

Do not include secrets or tokens.

14.6 Explicit Non-Triggers

Do not send welcome email:

before email verification
on every login
on resend verification
on password reset
on billing subscription creation unless future spec defines a product-specific welcome flow
15. Template #2 — Support Response
15.1 Catalog Entry
Brevo template ID: 2
Brevo template name: Support Response
Backend template key: support_response
Category: support
Sender profile: support
15.2 Sender
From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
15.3 First-Phase Trigger

Configure only.

Do not wire a support-response trigger unless a support-ticket or support-message spec explicitly defines it.

15.4 Future Trigger Possibilities

Future support specs may use this template when:

a support ticket is created
a human support response is added
a ticket is updated
a ticket is closed
an escalation occurs

Those rules are not defined in this email implementation phase.

15.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "ticketCode": "SUP-12345",
  "subject": "Support request update",
  "message": "A support response has been added.",
  "supportUrl": "https://zeptalytic.com/support"
}

Do not implement these params until the support flow spec defines actual requirements.

15.6 Explicit Non-Triggers

Do not invent:

support-ticket creation emails
support-ticket assignment emails
support-ticket close emails
support escalation emails

unless a support architecture/spec document explicitly defines them.

16. Template #3 — Order Confirmation
16.1 Catalog Entry
Brevo template ID: 3
Brevo template name: Order Confirmation
Backend template key: order_confirmation
Category: billing/order/payment
Sender profile: billing
16.2 Sender
From: Zeptalytic Billing <billing@zeptalytic.com>
Reply-To: billing@zeptalytic.com
16.3 First-Phase Trigger

Configure only.

Do not wire this template until Pay/billing integration explicitly defines order confirmation trigger rules.

16.4 Reason for Deferral

Pay Service remains the source of truth for:

orders
payments
refunds
subscriptions
entitlements
commercial finality

The parent Zeptalytic Web Backend must not invent order confirmation rules independently.

A future Pay/billing integration spec must define:

when an order is considered confirmed
which payment statuses trigger confirmation
whether Coinbase and Stripe differ
whether one-time and recurring orders differ
how duplicate confirmations are prevented
how refunds/disputes affect later communications
16.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "orderReference": "ORD-12345",
  "productName": "ZardBot",
  "planName": "Premium",
  "amount": "$29.00",
  "billingInterval": "Monthly",
  "receiptUrl": "https://zeptalytic.com/billing"
}

Do not implement or wire these params until the billing spec defines them.

17. Template #4 — News & Updates
17.1 Catalog Entry
Brevo template ID: 4
Brevo template name: News & Updates
Backend template key: news_updates
Category: updates/newsletter
Sender profile: updates
17.2 Sender
From: Zeptalytic Updates <updates@zeptalytic.com>
Reply-To: support@zeptalytic.com
17.3 First-Phase Trigger

Configure only.

Do not implement newsletter or marketing campaign automation in the first transactional email implementation.

17.4 Future Trigger Possibilities

Future communication/newsletter specs may define:

product update emails
release note emails
newsletter campaigns
announcements
product-specific updates
global Zeptalytic updates
Brevo contact/list synchronization
unsubscribe and communication preference handling

These are future scope.

17.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "updateTitle": "Zeptalytic Update",
  "summary": "New features are available.",
  "ctaUrl": "https://zeptalytic.com/announcements",
  "ctaText": "Read more"
}

Do not implement newsletter behavior until a separate spec defines trigger and preference rules.

17.6 Explicit Non-Triggers

Do not send this template from:

signup
email verification
password reset
order confirmation
payment failure
support response

unless a future spec explicitly says so.

18. Template #5 — Failed Sign-up
18.1 Catalog Entry
Brevo template ID: 5
Brevo template name: Failed Sign-up
Backend template key: failed_signup
Category: support/security/internal
Sender profile: support or alerts depending on final spec
18.2 Sender

Preferred first-phase internal alert sender:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com

Alternative future operational alert sender:

From: Zeptalytic Alerts <alerts@zeptalytic.com>
Reply-To: support@zeptalytic.com

The implementation spec should choose one based on the final internal-alert design.

18.3 First-Phase Trigger

Internal/security only if implemented.

Do not send failed-signup emails externally to arbitrary submitted email addresses unless a future security-reviewed spec explicitly approves that behavior.

18.4 Why External Failed Signup Emails Are Risky

External failed-signup emails can create risks:

account enumeration
spam/email bombing
sending emails to mistyped addresses
confirming that a signup attempt occurred
exposing platform instability
confusing legitimate users
leaking internal failure information
18.5 Allowed Internal Alert Use

A future implementation may send an internal alert for non-user-actionable signup failures.

Allowed sanitized content:

{
  "failureCode": "profile_create_failed",
  "submittedEmail": "sanitized@example.com",
  "requestId": "req_123",
  "environment": "local",
  "timestamp": "2026-05-24T00:00:00Z"
}

Do not include:

user password
password hash
raw verification token
raw reset token
session cookie
Brevo API key
webhook secret
stack trace containing secrets
full database error with sensitive values
18.6 Existing Bug Context

A previous signup issue returned misleading duplicate-account 409 Conflict when the real failure was:

null value in column "discord_integration_status" of relation "profiles"

The fix involved setting:

discord_integration_status="pending"

when creating profile records.

Future agents must avoid converting unrelated IntegrityError cases into false duplicate-account errors.

18.7 Explicit Non-Triggers

Do not send this template:

to every user who mistypes a signup form
to arbitrary submitted emails
for duplicate-account signup attempts
for password reset failures
for normal validation errors
for provider email-send failure during signup

unless a future security-reviewed spec explicitly defines those behaviors.

19. Template #6 — email Changed
19.1 Catalog Entry
Brevo template ID: 6
Brevo template name: email Changed
Backend template key: email_changed
Category: auth/security
Sender profile: support
19.2 Sender
From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
19.3 First-Phase Trigger

Configure only unless the existing backend already has a safe email-change flow.

Do not invent an email-change workflow solely to use this template.

19.4 Future Trigger Possibilities

A future account settings/security spec may define:

email change request
old email notification
new email verification
new email confirmation
rollback/security support path
session invalidation after email change
account audit event
19.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "oldEmail": "old@example.com",
  "newEmail": "new@example.com",
  "changedAt": "2026-05-24T00:00:00Z",
  "supportEmail": "support@zeptalytic.com"
}

Do not include:

password
session cookie
raw verification token
reset token
sensitive internal account IDs
19.6 Explicit Non-Triggers

Do not send this template for:

signup verification
forgot password
password reset request
password reset completion
normal login
failed login
billing email changes handled by Pay unless future spec defines the integration
20. Template #7 — Password Reset Request
20.1 Catalog Entry
Brevo template ID: 7
Brevo template name: Password Reset Request
Backend template key: password_reset
Category: auth/security
Sender profile: support
20.2 Sender
From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
20.3 First-Phase Trigger

Wire this template to the forgot-password flow.

Target endpoint:

POST /api/v1/auth/forgot-password
20.4 Required Behavior

Forgot-password must remain account-enumeration safe.

Target behavior:

If account does not exist:
    return generic success

If account exists but is closed/ineligible:
    return generic success

If account exists and is eligible:
    create reset token
    store only token hash
    build reset URL
    send Password Reset Request email
    record send attempt
    return generic success

If Brevo send fails:
    record failed send attempt
    return generic success
20.5 Reset URL

Local:

http://localhost:5173/reset-password?token=<token>

Production:

https://zeptalytic.com/reset-password?token=<token>

The base URL should come from:

FRONTEND_BASE_URL
20.6 Recommended Token TTL
2 hours

Future agents must inspect existing token TTL before changing it.

20.7 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "resetUrl": "https://zeptalytic.com/reset-password?token=<token>",
  "expiresIn": "2 hours",
  "supportEmail": "support@zeptalytic.com"
}
20.8 Token Safety Rules

The raw token may be used only to build the email URL.

Do not store:

raw reset token
full reset URL with raw token
rendered email body

Do not log:

raw reset token
full reset URL with raw token

Safe send-attempt metadata example:

{
  "flow": "forgot_password",
  "template_key": "password_reset",
  "token_type": "password_reset"
}

Unsafe metadata example:

{
  "resetUrl": "https://zeptalytic.com/reset-password?token=raw-token"
}

The unsafe example must not be implemented.

21. Template #8 — Account details Changed
21.1 Catalog Entry
Brevo template ID: 8
Brevo template name: Account details Changed
Backend template key: account_details_changed
Category: auth/security
Sender profile: support
21.2 Sender
From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
21.3 First-Phase Trigger

Wire only where an existing backend flow safely supports it.

Likely first supported trigger:

successful password reset completion

Potential endpoint:

POST /api/v1/auth/reset-password

Future account settings specs may also use it for:

password changed while logged in
phone number changed
timezone changed
profile details changed
2FA changed
account recovery settings changed

Do not invent those flows in this implementation phase.

21.4 Failure Policy

If account-change notification sending fails after the underlying account change succeeds:

record failed send attempt
do not roll back the account change
do not expose provider internals to the user
21.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "changeType": "password_reset",
  "changedAt": "2026-05-24T00:00:00Z",
  "supportEmail": "support@zeptalytic.com"
}

Do not include:

password
password hash
raw reset token
raw verification token
session cookie
sensitive internal stack traces
21.6 Explicit Non-Triggers

Do not send this template for:

every login
failed login
forgot-password request before reset completes
signup before verification
billing changes unless future spec defines billing/account notification linkage
22. Template #9 — eMail Verification
22.1 Catalog Entry
Brevo template ID: 9
Brevo template name: eMail Verification
Backend template key: email_verification
Category: auth/security
Sender profile: support
22.2 Sender
From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
22.3 First-Phase Triggers

Wire this template to:

POST /api/v1/auth/signup
POST /api/v1/auth/resend-verification
22.4 Signup Behavior

Signup target behavior:

create account
create profile/preferences/security records
set account status pending_verification
create authenticated restricted session
create email verification token
store only token hash
build verification URL
send email verification template
record send attempt
return signup success even if email send fails
22.5 Resend Behavior

Resend target behavior:

confirm account is pending verification
invalidate previous unused verification token if supported
create new verification token
store only token hash
build verification URL
send email verification template
record send attempt
return safe response
22.6 Verification URL

Local:

http://localhost:5173/verify-email?token=<token>

Production:

https://zeptalytic.com/verify-email?token=<token>

The base URL should come from:

FRONTEND_BASE_URL
22.7 Recommended Token TTL
24 hours

Future agents must inspect existing token TTL before changing it.

22.8 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "verificationUrl": "https://zeptalytic.com/verify-email?token=<token>",
  "expiresIn": "24 hours",
  "supportEmail": "support@zeptalytic.com"
}
22.9 Failure Policy

Signup verification email failure:

Signup still succeeds.
Account remains pending_verification.
Session remains created according to existing auth behavior.
Send attempt is marked failed.
User can resend verification.

Resend verification email failure:

Record failed send attempt.
Return controlled response.
Do not expose Brevo internals.
Do not activate account.
22.10 Token Safety Rules

Do not store:

raw verification token
full verification URL with raw token
rendered email body

Do not log:

raw verification token
full verification URL with raw token

Safe send-attempt metadata example:

{
  "flow": "signup",
  "template_key": "email_verification",
  "token_type": "email_verification"
}

Unsafe metadata example:

{
  "verificationUrl": "https://zeptalytic.com/verify-email?token=raw-token"
}

The unsafe example must not be implemented.

22.11 Explicit Non-Triggers

Do not send this template:

after successful verification
for password reset
for billing events
for support ticket events
for newsletter updates
23. Template #10 — Payment Failed
23.1 Catalog Entry
Brevo template ID: 10
Brevo template name: Payment Failed
Backend template key: payment_failed
Category: billing/order/payment
Sender profile: billing
23.2 Sender
From: Zeptalytic Billing <billing@zeptalytic.com>
Reply-To: billing@zeptalytic.com
23.3 First-Phase Trigger

Configure only.

Do not wire this template until Pay/billing integration explicitly defines payment-failure trigger rules.

23.4 Reason for Deferral

Pay Service remains the source of truth for:

payment status
subscription status
entitlement state
retries
failure finality
provider-specific payment behavior

The parent backend must not infer payment-failure email triggers from incomplete local projection data unless a future Pay integration spec defines the exact rule.

23.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "productName": "ZardBot",
  "planName": "Premium",
  "amount": "$29.00",
  "paymentMethodSummary": "Card ending in 1234",
  "billingUrl": "https://zeptalytic.com/billing",
  "supportEmail": "billing@zeptalytic.com"
}

Do not include:

full card number
CVV
bank account number
raw provider payment secret
Stripe/Coinbase secret keys
internal risk flags
sensitive fraud details
23.6 Explicit Non-Triggers

Do not send this template:

from email delivery webhook bounce events
from failed email send attempts
from account signup failure
from Pay projection sync unless future spec defines conditions
from frontend billing page actions without backend/Pay confirmation
24. Template #11 — Subscription Expiring
24.1 Catalog Entry
Brevo template ID: 11
Brevo template name: Subscription Expiring
Backend template key: subscription_expiring
Category: billing/subscription
Sender profile: billing
24.2 Sender
From: Zeptalytic Billing <billing@zeptalytic.com>
Reply-To: billing@zeptalytic.com
24.3 First-Phase Trigger

Configure only.

Do not wire this template until a Pay/billing/subscription lifecycle spec defines trigger rules.

24.4 Reason for Deferral

Subscription lifecycle events need exact business rules.

A future spec must define:

what “expiring” means
whether canceled-at-period-end subscriptions qualify
how many days before expiration to notify
whether trial expiration uses this template
whether paused subscriptions use this template
whether failed renewals use this or Payment Failed
how to avoid duplicate notifications
whether bundle subscriptions use different copy
whether product-specific entitlements affect notification content

Do not invent these rules in the first transactional email implementation.

24.5 Possible Template Parameters

Conceptual params:

{
  "displayName": "John",
  "productName": "RustRaptor",
  "planName": "Premium",
  "expirationDate": "2026-06-01",
  "billingUrl": "https://zeptalytic.com/billing",
  "supportEmail": "billing@zeptalytic.com"
}

Do not include:

full payment method details
provider secret IDs
internal commercial-risk notes
unsupported subscription claims
24.6 Explicit Non-Triggers

Do not send this template:

on signup
on email verification
on password reset
on generic account status changes
on email delivery webhook events
unless a subscription lifecycle spec explicitly defines the condition
25. First-Phase Trigger Matrix

The first implementation should wire only these triggers.

Backend flow	Template key	Template ID	Wire in first phase?	Notes
Signup creates pending-verification account	email_verification	9	yes	signup succeeds even if send fails
Pending user requests resend verification	email_verification	9	yes	preferably invalidates previous unused token
User successfully verifies email	welcome	1	yes	failure does not undo verification
User requests password reset	password_reset	7	yes	generic response always
User successfully resets password	account_details_changed	8	maybe	only if existing flow safely supports it
Signup fails due to internal error	failed_signup	5	maybe internal only	do not send externally without future security review
User changes email	email_changed	6	no/maybe	only if existing email-change flow exists
Support sends ticket response	support_response	2	no	future support spec
Order confirmed	order_confirmation	3	no	future Pay/billing spec
Payment failed	payment_failed	10	no	future Pay/billing spec
Subscription expiring	subscription_expiring	11	no	future Pay/billing spec
News/update campaign	news_updates	4	no	future communications/newsletter spec
26. Explicitly Deferred Templates

These templates should be configured but not triggered in the first implementation unless another spec explicitly defines the trigger.

support_response
order_confirmation
news_updates
payment_failed
subscription_expiring

The template service may expose methods for these templates, but future build agents must not wire them into live business flows without separate trigger definitions.

Reason:

The user wants a comprehensive EmailService and complete template catalog from the start, but does not want agents inventing business logic.

27. Template Parameters and Naming

Exact Brevo template parameter names should be confirmed against the actual Brevo template design before implementation.

Until confirmed, backend specs should use conceptual names and require tests/mocks to reflect final expected payload.

Recommended parameter naming style:

displayName
verificationUrl
resetUrl
expiresIn
loginUrl
dashboardUrl
billingUrl
supportEmail
ticketCode
orderReference
productName
planName
amount
billingInterval
expirationDate
changedAt
changeType

Avoid provider-specific or inconsistent parameter names unless Brevo templates already require them.

Do not include raw security-sensitive values except where the email link itself requires a raw one-time token.

The raw token may be placed in the outgoing email URL but must not be stored in operational metadata or logs.

28. URL Parameters

Email templates that need frontend links should use FRONTEND_BASE_URL.

Required URL patterns:

Email verification:
{FRONTEND_BASE_URL}/verify-email?token=<token>

Password reset:
{FRONTEND_BASE_URL}/reset-password?token=<token>

Dashboard:
{FRONTEND_BASE_URL}/dashboard

Login:
{FRONTEND_BASE_URL}/login

Billing:
{FRONTEND_BASE_URL}/billing

Support:
{FRONTEND_BASE_URL}/support

Local FRONTEND_BASE_URL:

http://localhost:5173

Production FRONTEND_BASE_URL:

https://zeptalytic.com

This workstream must not implement frontend routes.

29. Send Attempt Requirements by Template

Every attempted send should create an email_send_attempts record.

Required fields conceptually include:

account_id
to_email
from_email
from_name
reply_to_email
template_key
provider
provider_template_id
provider_message_id
status
failure_code
failure_message
metadata_json
created_at
sent_at
failed_at

Template-specific template_key values should use the backend keys from this catalog.

provider_template_id should store the Brevo numeric template ID.

provider should be:

brevo

Status values:

pending
sent
failed
skipped

Do not store rendered email bodies.

Do not store raw security tokens.

Do not store full token URLs in metadata.

30. Delivery Event Relationship by Template

Brevo delivery webhook events may later reference these template IDs.

Delivery events should store:

provider
event_type
provider_message_id
provider_event_id
email
template_id
subject
event_timestamp
dedupe_key
raw_payload
created_at

Delivery event normalized types:

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

Important:

Email delivery events are telemetry.

They must not independently trigger:

account verification
password reset completion
billing status changes
support ticket state changes
entitlement changes
subscription state changes

A delivered verification email is not the same as a verified account.

A clicked verification email is not the same as successful backend token verification.

31. Provider Failure Policy by Template

General provider failure handling:

Template category	If Brevo send fails
Signup verification	signup still succeeds; account remains pending; failed send attempt recorded
Resend verification	controlled response; failed send attempt recorded; account remains pending
Password reset request	generic success still returned; failed send attempt recorded
Welcome after verification	verification remains successful; failed send attempt recorded
Account details changed	underlying account change remains successful; failed send attempt recorded
Failed signup internal alert	original signup failure handling remains; alert failure logged/recorded if attempted
Billing templates	future spec must define
Support templates	future spec must define
News/update templates	future spec must define

Failure codes should be normalized.

Required failure code concepts:

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
32. Security and Privacy Rules

Do not store:

rendered email body
raw verification token
raw password reset token
full verification URL with token
full reset URL with token
user password
password hash
session cookie
Brevo API key
webhook secret
provider authorization header
CVV
full card number
bank account number

Do not log:

raw verification token
raw password reset token
full token URLs
Brevo API key
webhook secret
user password
rendered email body
supplied invalid webhook secret

Allowed operational storage:

recipient email
account ID when known
sender address
reply-to address
template key
provider template ID
provider message ID
send status
normalized failure code
sanitized failure message
safe metadata
raw webhook payload for delivery events

Raw webhook payloads are sensitive operational data and must not be exposed through public user APIs.

33. Account Enumeration Rules

Auth templates must not weaken account enumeration protections.

Forgot-password behavior:

Always return generic success regardless of account existence or provider send result.

Failed-signup behavior:

Do not send external failed-signup emails to arbitrary submitted addresses unless future security review approves it.

Verification resend behavior:

Preserve existing auth/session requirements and do not leak unnecessary account state.

Password reset request email should only be sent when the account exists and is eligible, but the HTTP response should remain generic.

34. Billing and Pay Boundary

Billing templates exist in Brevo and should be configured in backend settings.

Billing templates:

order_confirmation
payment_failed
subscription_expiring

But Pay Service remains the source of truth for:

orders
payments
refunds
disputes
subscriptions
entitlements
commercial finality
provider payment status
billing lifecycle state

The parent backend must not invent billing email triggers.

Do not send billing templates based only on:

frontend user action
email delivery events
local assumptions
partial projection data
account status
generic payment-like naming

Future Pay/billing integration specs must define exact trigger rules.

35. Newsletter and Communications Boundary

The news_updates template should be configured but not triggered in the first implementation.

Do not implement:

newsletter campaign automation
Brevo contact list sync
marketing subscription management
unsubscribe preference mutation
communication preference center
campaign analytics dashboard

unless a future communications/newsletter spec defines those behaviors.

Brevo unsubscribed webhook events should be stored as delivery events in the first implementation, but should not automatically mutate Zeptalytic communication preferences unless a future spec defines how that should work.

36. Support Boundary

The support_response template should be configured but not triggered in the first implementation unless a support-ticket spec defines exact trigger rules.

Do not invent:

support ticket created email
support response email
support assignment email
support status change email
support close email
support escalation email

unless support architecture/spec docs define those workflows.

37. EmailService Method Coverage

The EmailService may expose methods for the full template catalog so the service is comprehensive from the start.

Conceptual method coverage:

send_email_verification(...)
send_password_reset(...)
send_welcome(...)
send_account_details_changed(...)
send_email_changed(...)
send_failed_signup_internal_alert(...)
send_support_response(...)
send_order_confirmation(...)
send_payment_failed(...)
send_subscription_expiring(...)
send_news_updates(...)

Important distinction:

A method existing is not the same as a live business trigger being wired.

Agents may implement method coverage, but must not wire future-scope methods to live flows without a separate spec.

38. Testing Requirements

Future implementation specs should test the template catalog.

38.1 Configuration Tests

Verify:

all template IDs load from config
default local/test config uses safe placeholder/non-secret values
.env.example contains placeholders only
template IDs are not hardcoded in service business logic where config should be used
missing required template config produces controlled behavior
38.2 Catalog Tests

Verify:

every expected backend template key exists
every template key maps to the correct config setting
every template key maps to the correct sender profile
sender profiles resolve correct from/reply-to addresses
no template uses no-reply@zeptalytic.com
38.3 Auth Template Tests

Verify:

signup uses email_verification
resend verification uses email_verification
forgot-password uses password_reset
successful verification uses welcome
password reset completion uses account_details_changed if wired
failed signup external email is not accidentally sent
38.4 Future-Scope Guard Tests

Where practical, verify no live trigger exists for:

support_response
order_confirmation
news_updates
payment_failed
subscription_expiring

unless a separate spec intentionally adds one.

38.5 Send Attempt Tests

Verify:

correct template_key is stored
correct provider_template_id is stored
correct sender is stored
correct reply-to is stored
provider message ID is stored when available
failed send stores normalized failure code
raw tokens are not stored in metadata
rendered email body is not stored
38.6 Provider Payload Tests

Mock Brevo API and verify:

correct template ID
correct sender
correct recipient
correct reply-to
correct params
correct timeout/error handling
no secrets logged
38.7 Required Gates

Before marking implementation complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

Agents must not mark spec items complete unless relevant tests/gates pass or blockers are explicitly documented.

39. Manual Verification Checklist

After implementation, manually verify:

Template config appears in backend settings.
All 11 template IDs are represented.
Auth templates use support sender.
Welcome template uses hello sender.
Billing templates use billing sender.
Updates template uses updates sender.
Alerts/internal template uses support or alerts sender as specified.
No no-reply sender exists.
Signup verification email send creates email_send_attempt.
Forgot-password email send creates email_send_attempt when account exists.
Provider failure creates failed send_attempt.
Raw token URLs are not stored in send_attempt metadata.
Brevo delivery events store template_id when provided.
Future-scope templates are not accidentally triggered.
40. Suggested Future Spec Items

A future implementation spec may include items like:

template-001: Add email template ID config values and .env.example placeholders
template-002: Add backend template key enum/constants
template-003: Add sender profile resolver
template-004: Add template catalog registry
template-005: Add EmailService methods for all configured templates
template-006: Wire first-phase auth templates only
template-007: Add tests for template key/config/sender mapping
template-008: Add tests preventing accidental future-scope triggers
template-009: Add send-attempt assertions for template_key and provider_template_id
template-999: Run compileall and Docker test gate

These are suggestions only.

The actual spec-author run should inspect the current repository and generate final spec items based on real code.

41. Implementation Constraints for Future Agents

Future spec-author, plan, and build agents must obey these constraints:

Search before editing.
Inspect existing config conventions before adding settings.
Inspect existing service conventions before adding EmailService methods.
Use template IDs from configuration.
Do not hardcode real secrets.
Do not commit .env.
Do not commit real Brevo API key.
Do not commit real webhook secret.
Do not use no-reply@zeptalytic.com.
Do not call Brevo directly from auth/business services.
Route sends through EmailService.
Keep sender selection centralized.
Configure all known templates from the start.
Wire only first-phase approved triggers.
Do not invent billing triggers.
Do not invent newsletter triggers.
Do not invent support triggers.
Do not invent email-change workflow if it does not already exist.
Do not send failed-signup emails externally unless future security-reviewed spec approves.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not store full token URLs in metadata.
Do not store rendered email bodies.
Do not expose provider internals to users.
Preserve forgot-password account-enumeration safety.
Preserve signup success when verification email sending fails.
Preserve pending-verification access restrictions.
Use Alembic for schema changes if template work touches persistence.
Run required test gates before completion.
Append progress entries to EOF if using progress/progress.txt.
Do not mark incomplete spec items complete.
42. Summary Decision

Zeptalytic will represent all active Brevo templates in backend configuration from the start.

The backend will use stable internal template keys and centralized sender profiles.

The first implementation will wire only auth-related and explicitly approved account templates:

email_verification
password_reset
welcome
account_details_changed where existing flow safely supports it
failed_signup internal alert only if explicitly implemented safely

The following templates will be configured but not triggered until future specs define their business rules:

support_response
order_confirmation
news_updates
payment_failed
subscription_expiring

The backend must not invent billing, newsletter, support, or subscription lifecycle triggers.

All sends should go through EmailService, use Brevo through BrevoClient, create send-attempt records, and avoid storing raw tokens, token URLs, rendered email bodies, or secrets.