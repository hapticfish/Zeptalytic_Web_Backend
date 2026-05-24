# Auth Email Verification Flow

**Target file:** `docs/architecture/Auth_Email_Verification_Flow.md`  
**Status:** Draft / Architecture Reference  
**Project:** Zeptalytic Web Backend  
**Service:** Parent/backend application, not Pay Service  
**Provider:** Brevo transactional email  
**Mailbox/reply system:** Google Workspace  
**Related docs:**

- `docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md`
- `docs/architecture/Transactional_Email_Service_Architecture.md`
- `docs/architecture/Auth_Email_Verification_Flow.md`
- `docs/architecture/Email_Delivery_Events_And_Webhooks.md`
- `docs/architecture/Email_Template_Catalog.md`
- `docs/architecture/Transactional_Email_Agent_Run_Guidance.md`

---

## 1. Purpose

This document defines the Zeptalytic Web Backend architecture for authentication-related transactional emails.

The main purpose is to guide future spec-author, plan, and build agent runs when they generate and implement specs for Brevo-backed auth email functionality.

This document focuses on:

- signup verification email
- resend verification email
- email verification completion
- post-verification welcome email
- forgot-password password reset email
- successful password reset/account change notification
- failed signup handling
- pending-verification user behavior
- token safety
- provider failure behavior
- send-attempt logging
- interaction with future delivery-event webhook tracking

This document is an architecture/reference document. It is not itself the implementation spec.

Future implementation specs must absorb this document before making auth/email changes.

---

## 2. Current Backend Context

The Zeptalytic Web Backend already has partial authentication and email verification infrastructure.

Known existing pieces include:

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
- account pending-verification behavior
- route-level access flags for pending-verification users

The backend does **not yet** have the complete transactional email service architecture.

Missing pieces expected from the transactional email workstream include:

- general `EmailService`
- Brevo API client abstraction
- send-attempt table/model/repository
- delivery-event table/model/repository
- Brevo webhook router
- delivery event normalization
- provider failure classification
- template catalog configuration
- tests covering email send success/failure behavior

This document defines how existing auth flows should integrate with the future `EmailService`.

---

## 3. Current Repository and Environment

Backend repo:

```bash
~/Desktop/Dev/Zeptalytic_Web_Backend    

Existing Auth Behavior to Preserve

Current intended signup behavior:

User signs up.
Backend creates account.
Account status is pending_verification.
Backend creates a session cookie.
User is authenticated but restricted.
Pending-verification users can access support and resend verification.
Pending-verification users cannot access normal dashboard/product launch.

Current important auth response concepts include:

email_verification_required
can_access_support
can_access_billing
can_access_normal_authenticated_routes
can_access_product_launch

These concepts must be preserved.

The transactional email implementation must not weaken the pending-verification access model.

5. Account Status Model

The parent account lifecycle includes statuses such as:

active
pending_verification
suspended
closed

For auth email verification:

new user accounts should begin as pending_verification
pending users should be authenticated but restricted
successful email verification should promote the account to the correct verified/active state according to existing backend model
suspended or closed accounts must not be reactivated by email flows unless a separate account lifecycle spec explicitly allows it

Implementation agents must inspect the existing account model and auth service before changing status transitions.

6. Core Design Decision

The auth system should not call Brevo directly.

Auth-related email sending should go through:

AuthService
→ EmailService
→ BrevoClient
→ Brevo API

The auth service owns:

account creation
account lookup
password handling
token generation
token hashing
token verification
account status transitions
session behavior
security-safe API responses

The email service owns:

template selection
sender/reply-to selection
provider call
send-attempt logging
provider failure classification
safe provider result reporting

The Brevo client owns:

HTTP calls to Brevo
Brevo API payload shape
provider response parsing
provider-level error mapping
7. Auth Email Template Usage

Auth-related flows should use these Brevo templates:

Flow	Template ID	Template name	Template key	Sender
Signup verification	9	eMail Verification	email_verification	support/security
Resend verification	9	eMail Verification	email_verification	support/security
Forgot password	7	Password Reset Request	password_reset	support/security
Post-verification welcome	1	Initial Welcome Response	welcome	general/account
Password/account details changed	8	Account details Changed	account_details_changed	support/security
Email changed	6	email Changed	email_changed	support/security
Failed signup internal alert	5	Failed Sign-up	failed_signup	support/security/internal

Template IDs must come from configuration, not hardcoded business logic.

Required config keys:

BREVO_TEMPLATE_WELCOME_ID=1
BREVO_TEMPLATE_FAILED_SIGNUP_ID=5
BREVO_TEMPLATE_EMAIL_CHANGED_ID=6
BREVO_TEMPLATE_PASSWORD_RESET_ID=7
BREVO_TEMPLATE_ACCOUNT_DETAILS_CHANGED_ID=8
BREVO_TEMPLATE_EMAIL_VERIFICATION_ID=9
8. Sender Identity Rules for Auth Emails

Auth/account/security emails should use:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com

Post-verification welcome email may use:

From: Zeptalytic <hello@zeptalytic.com>
Reply-To: support@zeptalytic.com

Do not use:

no-reply@zeptalytic.com

Zeptalytic will use real reply-capable sender identities.

Google Workspace owns the actual human inboxes and aliases.

Brevo owns transactional email sending infrastructure.

The backend sends through Brevo.

Brevo does not log into Google Workspace.

DNS authorizes Brevo to send as zeptalytic.com.

9. Required Email Configuration

The backend should support these environment variables for auth email flows:

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

Recommended:

BREVO_REQUEST_TIMEOUT_SECONDS=10

Secrets must not be committed.

Real values belong only in:

local .env, ignored by Git
Fly production secrets
secure runtime secret storage

Real values must not appear in:

.env.example
Markdown docs
JSON specs
progress logs
docker-compose.yml
fly.toml
GitHub Actions workflow bodies
source code defaults
10. Frontend URL Construction

The backend needs to generate links that point to the frontend.

The link base should come from:

FRONTEND_BASE_URL=http://localhost:5173

Local email verification URL shape:

http://localhost:5173/verify-email?token=<token>

Production email verification URL shape:

https://zeptalytic.com/verify-email?token=<token>

Local password reset URL shape:

http://localhost:5173/reset-password?token=<token>

Production password reset URL shape:

https://zeptalytic.com/reset-password?token=<token>

Potential future pending-verification page:

/verify-email-required

Potential successful verification redirect:

/dashboard

The backend can generate URLs using FRONTEND_BASE_URL, but this workstream must not implement frontend pages.

11. Token Safety Rules

Auth email flows rely on sensitive one-time tokens.

Required token rules:

raw verification token must only exist long enough to build the verification URL
raw password reset token must only exist long enough to build the reset URL
only token hashes should be stored in the database
raw tokens must not be logged in production
raw tokens must not be stored in email_send_attempts.metadata_json
raw token URLs must not be stored in send-attempt metadata
raw token URLs must not be stored in delivery-event records
raw token URLs must not be exposed in error responses
raw token URLs must not be added to progress logs
raw token URLs must not be added to docs/spec examples except as <token> placeholders

Recommended token TTLs:

Email verification token TTL: 24 hours
Password reset token TTL: 2 hours

If existing code already has TTL constants, future agents must inspect and preserve or intentionally align them through a clear spec item.

12. Send Attempt Logging

Every attempted auth email should create an email_send_attempts row.

This applies to:

signup verification email
resend verification email
forgot-password email when account exists and is eligible
welcome email after successful verification
password/account details changed email if wired
email changed notification if wired
failed signup internal alert if wired

The send-attempt table is defined by the broader transactional email architecture.

Conceptual fields:

Field	Type	Required	Notes
id	UUID	yes	primary key
account_id	UUID	no	FK to accounts.id when account is known
to_email	string	yes	recipient
from_email	string	yes	sender
from_name	string	no	sender display name
reply_to_email	string	no	reply-to
template_key	string	yes	internal template key
provider	string	yes	default brevo
provider_template_id	integer	no	Brevo template ID
provider_message_id	string	no	Brevo message ID if returned
status	string/enum	yes	pending, sent, failed, skipped
failure_code	string	no	normalized failure code
failure_message	text	no	sanitized failure message
metadata_json	JSONB	no	safe non-token metadata
created_at	timestamp	yes	creation time
sent_at	timestamp	no	provider accepted/sent time
failed_at	timestamp	no	failure time

Allowed first-phase statuses:

pending
sent
failed
skipped

Auth-related metadata may include safe context like:

{
  "flow": "signup",
  "template_key": "email_verification"
}

Auth-related metadata must not include:

raw verification token
raw password reset token
full verification URL
full password reset URL
user password
Brevo API key
webhook secret
rendered email body
internal stack trace
13. Delivery Event Relationship

Delivery events are separate from auth flow completion.

For example:

signup can succeed even if email send fails
Brevo can accept a verification email and later report a bounce
verification can complete if the user had the valid token
delivery event ingestion must not itself activate or deactivate accounts
open/click events must not be treated as verification

Important distinction:

Clicking the email link and submitting token verification through backend auth route verifies the account.
Brevo clicked/opened events do not verify the account.

The future delivery-event webhook system may store events like:

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

But auth state transitions must still be driven by authenticated backend token verification logic, not by webhook engagement events.

14. Signup Flow
14.1 Required Behavior

Signup should follow this target sequence:

Receive signup request.
Validate request.
Create account.
Create profile/preferences/security records as existing architecture requires.
Set account status to pending_verification.
Create session cookie according to existing auth behavior.
Generate email verification token.
Store only token hash.
Build verification URL using FRONTEND_BASE_URL.
Call EmailService.send_email_verification().
Record send attempt as sent or failed.
Return successful signup response even if email sending failed.
Response should indicate that email verification is required.
User remains authenticated but restricted.
14.2 Chosen Failure Policy

Signup uses Option B:

Account/session creation succeeds even if the verification email send fails.

Reason:

account creation should not be blocked by temporary email provider failure
user can resend verification
provider failure is operationally visible through send-attempt logs
this avoids a poor UX where the user cannot create an account because Brevo is briefly unavailable
14.3 Signup Must Not

Signup must not:

fail solely because Brevo is unavailable
expose Brevo API errors to the user
store raw token in database
store raw token in send-attempt metadata
log raw token in production
send welcome email before verification
activate account before email verification
allow pending user to access dashboard/product launch
convert unrelated database errors into misleading duplicate-account errors
14.4 Existing Bug Context to Avoid Regressing

A previous backend issue caused signup to return a misleading duplicate-account 409 Conflict when the real failure was a profile insert problem:

null value in column "discord_integration_status" of relation "profiles"

The fix involved ensuring discord_integration_status="pending" was set when creating profile records.

Future agents must avoid reintroducing misleading error mapping.

Unrelated IntegrityError cases should not be blindly converted to duplicate-account errors.

15. Signup Verification Email
15.1 Template

Use:

Template ID: 9
Template name: eMail Verification
Template key: email_verification
15.2 Sender

Use:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
15.3 Required Template Parameters

Exact Brevo template parameter names should match the configured template, but conceptually the email needs:

recipient display name if available
verification URL
expiration information if the template includes it
support contact context if needed

Potential params:

{
  "displayName": "John",
  "verificationUrl": "https://zeptalytic.com/verify-email?token=<token>",
  "expiresIn": "24 hours"
}

Do not persist the full verificationUrl with raw token in send-attempt metadata.

15.4 Send Attempt Metadata

Safe metadata example:

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

16. Resend Verification Flow

Existing endpoint:

POST /api/v1/auth/resend-verification
16.1 Required Behavior

Resend verification should:

Validate session/auth context.
Confirm account is eligible for resend.
Confirm account is still pending verification.
Invalidate previous unused verification tokens if existing token architecture supports it.
Generate a new verification token.
Store only token hash.
Build verification URL using FRONTEND_BASE_URL.
Call EmailService.send_email_verification().
Record send attempt.
Return a safe response.
16.2 Token Invalidation Decision

Preferred behavior:

Invalidate previous unused verification tokens when a new resend token is created.

Reason:

reduces number of valid outstanding verification links
simplifies support/security reasoning
matches common auth security practice

If current implementation already supports token invalidation, use it.

If not, future specs should include it explicitly or document the decision not to change token behavior in this phase.

16.3 Resend Failure Policy

If Brevo send fails during resend:

record failed send attempt
return controlled response
do not leak Brevo internals
do not log raw token
do not activate account
do not change account status to active

The exact user-facing response can follow existing backend style, but provider internals must remain hidden.

16.4 Rate Limiting

This architecture document does not define full rate limiting, but future specs should search for existing rate-limit middleware or auth throttling.

If no rate limiting exists, a future security-hardening spec should add it.

Potential future controls:

limit resend attempts per account
limit resend attempts per IP
cooldown between resend attempts
generic response after excessive attempts
audit event for repeated resend attempts

Do not invent a large rate-limiting subsystem in the first transactional email implementation unless the spec explicitly includes it.

17. Verify Email Flow

Existing endpoint:

POST /api/v1/auth/verify-email
17.1 Required Behavior

Verify email should:

Receive raw token from request.
Hash token using existing token verification logic.
Find valid unexpired unused verification token.
Confirm account is eligible.
Mark token as used.
Update account verification status according to existing model.
Return successful verification response.
Trigger post-verification welcome email.
Record welcome email send attempt.
Keep verification successful even if welcome email send fails.
17.2 Verification Must Not Depend on Brevo Events

Account verification must be based on backend token verification.

Do not verify account based on:

Brevo delivered event
Brevo opened event
Brevo clicked event
Brevo sent event
any email delivery webhook event

Email delivery telemetry is not account verification.

17.3 Successful Verification Welcome Email

After successful verification, send:

Template ID: 1
Template name: Initial Welcome Response
Template key: welcome

Sender:

From: Zeptalytic <hello@zeptalytic.com>
Reply-To: support@zeptalytic.com

Failure policy:

Welcome email failure must not undo successful verification.
17.4 Duplicate Verification

If a user submits an already-used or expired token, behavior should follow existing auth semantics.

Future agents must inspect current tests and service behavior before changing responses.

Security posture:

do not reveal unnecessary token internals
do not expose raw token hash
do not leak account existence more than current endpoint already permits
return controlled errors for invalid/expired tokens
18. Forgot Password Flow

Existing target endpoint:

POST /api/v1/auth/forgot-password
18.1 Required Behavior

Forgot-password must be account-enumeration safe.

Target sequence:

Receive forgot-password request.
Normalize submitted email according to existing account lookup conventions.
If account does not exist, return generic success.
If account exists but is closed/ineligible, return generic success.
If account exists and is eligible:
create password reset token
store only token hash
build reset URL using FRONTEND_BASE_URL
call EmailService.send_password_reset()
record send attempt
If Brevo send fails, still return generic success.
18.2 Required Generic Response

The response must not reveal whether the email exists.

Conceptual response:

If an account exists for that email, password reset instructions have been sent.

Future agents should follow existing response schema and wording.

18.3 Template

Use:

Template ID: 7
Template name: Password Reset Request
Template key: password_reset
18.4 Sender

Use:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com
18.5 Reset URL

Local:

http://localhost:5173/reset-password?token=<token>

Production:

https://zeptalytic.com/reset-password?token=<token>
18.6 Password Reset Token TTL

Recommended:

2 hours

Future agents must check existing token TTL before changing it.

18.7 Forgot Password Must Not

Forgot-password must not:

reveal account existence
reveal account status
reveal provider failure
log raw reset token
store raw reset token
store full reset URL in send-attempt metadata
return different status codes for existing vs non-existing accounts unless existing code already does and a spec explicitly changes it
send failed-signup or unrelated templates
19. Reset Password Completion Flow

Existing target endpoint:

POST /api/v1/auth/reset-password
19.1 Required Behavior

Reset password should:

Receive raw reset token and new password.
Verify token using existing hashed token logic.
Confirm token is valid/unexpired/unused.
Update password securely.
Mark token used.
Invalidate relevant sessions if existing architecture supports it.
Send account/security notification if the implementation safely supports it.
Return safe success response.
19.2 Account Change Notification

Use:

Template ID: 8
Template name: Account details Changed
Template key: account_details_changed

Sender:

From: Zeptalytic Support <support@zeptalytic.com>
Reply-To: support@zeptalytic.com

Failure policy:

Notification email failure must not undo successful password reset.
19.3 Notification Scope

The notification should not include the new password.

It may include safe context such as:

account email
timestamp
general statement that account details/password changed
support contact if the user did not make the change

Do not include:

password
password hash
reset token
reset URL
session cookie
sensitive internal IDs unless existing user-facing style includes them
20. Email Changed Flow

Template exists:

Template ID: 6
Template name: email Changed
Template key: email_changed

This document does not assume a complete email-change flow already exists.

If the backend already has email-change functionality, future specs may wire this template there.

If the backend does not have email-change functionality, do not invent it as part of the transactional email service implementation.

Potential future behavior:

notify old email address
notify new email address
require verification of new email
avoid exposing sensitive account details
record send attempts for each notification

This is future scope unless an implementation spec explicitly includes it.

21. Failed Signup Flow

Template exists:

Template ID: 5
Template name: Failed Sign-up
Template key: failed_signup
21.1 First-Phase Meaning

For first implementation, failed-signup email should be treated as:

Internal support/security alert only.

It should not automatically send externally to arbitrary submitted email addresses.

21.2 Why External Failed Signup Emails Are Risky

Sending failed-signup emails to submitted addresses can create risks:

account enumeration
email bombing
confusing users
confirming signup attempts
exposing internal failures
sending messages to mistyped or maliciously submitted addresses
21.3 Allowed Internal Alert Concept

A future implementation may send an internal alert to a controlled Zeptalytic mailbox, such as support/security, when signup fails due to non-user-actionable backend errors.

Internal alert content may include safe operational details:

failure category
timestamp
correlation ID/request ID if available
sanitized submitted email
environment
high-level failure location

Internal alert must not include:

raw password
raw token
stack trace with secrets
full database error with sensitive values
Brevo API key
webhook secret
session cookie
21.4 First Implementation Constraint

Do not wire failed-signup external user emails unless a future security-reviewed spec explicitly requires it.

22. Pending Verification Access Rules

Pending-verification users should remain authenticated but restricted.

Allowed for pending-verification users:

access session information needed to show pending-verification state
resend verification
access support/contact paths
access limited billing/account routes only if existing backend already allows it
logout

Not allowed for pending-verification users:

normal dashboard access
product launch
full authenticated application access
privileged user actions
admin actions
entitlement-gated product actions

Current known expected behavior:

GET /api/v1/dashboard/summary
→ 403 Forbidden

for pending-verification users.

Future agents must preserve this.

23. Error Handling Rules
23.1 Provider Failure Classifications

Email provider failures should be normalized.

Required first-phase failure codes:

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
23.2 Signup Error Handling

Signup should only fail for real signup/domain/database validation reasons.

Signup must not fail solely because:

Brevo timed out
Brevo returned HTTP error
Brevo API key was missing in local/dev mode if project config allows degraded email behavior
Brevo returned unexpected response
email provider was unavailable

Instead:

record failed send attempt
return signup success with verification required
allow resend verification
23.3 Forgot Password Error Handling

Forgot-password should return generic success even if:

account does not exist
account is ineligible/closed
Brevo send failed
provider is unavailable

Do not expose provider errors or account existence.

23.4 Verify Email Error Handling

Verification should fail only based on token/account verification rules.

Welcome email failure after verification should not roll back verification.

23.5 Reset Password Error Handling

Password reset should fail based on token/password/account rules.

Notification email failure after successful reset should not roll back password change.

24. Logging Rules

Logs should help debug without exposing secrets.

Allowed log concepts:

email send attempt ID
account ID when safe and consistent with existing logging
template key
provider
provider failure classification
sanitized provider status code
webhook event type
delivery event ID

Do not log:

raw verification token
raw password reset token
full verification URL with token
full reset URL with token
Brevo API key
webhook secret
user password
session cookie
full rendered email body
sensitive raw webhook payload in normal logs
25. Database and Migration Expectations

Auth email integration depends on the transactional email tables:

email_send_attempts
email_delivery_events

This document does not redefine the full schema, but the auth integration must use email_send_attempts.

Future implementation specs should include Alembic migrations if these tables do not already exist.

Migration requirements:

UUID primary keys consistent with project convention
account FK where possible
JSONB metadata/raw payload fields
indexes supporting account/email/template/status lookups
unique dedupe key for delivery events
model import registration for Alembic/autogenerate
non-destructive migration behavior

Auth email flows should not add separate one-off auth email tables unless future specs justify it.

26. OpenAPI Expectations

Existing auth routes should continue to appear in OpenAPI according to current project conventions:

POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/verify-email
POST /api/v1/auth/resend-verification
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password

Future implementation may update response schemas to reflect:

email verification required
pending-verification state
resend verification behavior

Do not expose:

raw token examples
real secrets
real provider payloads
Brevo API keys
webhook secrets

Use placeholders like:

<token>
27. Test Expectations

Future implementation specs must include tests for auth email behavior.

27.1 Signup Tests

Verify:

signup creates pending-verification account
signup creates verification token
signup calls EmailService.send_email_verification()
signup records send attempt on success
signup records failed send attempt on provider failure
signup still succeeds when provider fails
response indicates email verification required
pending-verification user remains restricted
raw token is not stored in send-attempt metadata
welcome email is not sent before verification
unrelated IntegrityError is not converted into false duplicate-account error
27.2 Resend Verification Tests

Verify:

pending user can request resend
resend creates a new verification token
previous unused token is invalidated if supported/implemented
resend sends verification email through EmailService
resend records send attempt
provider failure is handled safely
raw token is not logged/stored in metadata
verified users cannot unnecessarily resend verification unless existing behavior allows it
27.3 Verify Email Tests

Verify:

valid token verifies account
token is marked used
expired token fails safely
used token fails safely
invalid token fails safely
successful verification triggers welcome email
welcome email send attempt is recorded
welcome email provider failure does not undo verification
Brevo delivery webhook events are not required for verification
27.4 Forgot Password Tests

Verify:

unknown email returns generic success
existing email returns generic success
closed/ineligible account returns generic success
existing eligible account creates password reset token
existing eligible account sends password reset email
send attempt is recorded
provider failure still returns generic success
raw reset token is not stored in send-attempt metadata
account existence is not revealed through status code/body/timing-sensitive obvious behavior where practical
27.5 Reset Password Tests

Verify:

valid reset token allows password reset
token is marked used
expired/invalid/used token fails safely
successful reset can send account details changed notification
notification failure does not undo password reset
notification does not include password or raw token
27.6 Failed Signup Tests

If internal failed-signup alert is implemented, verify:

it is internal-only
it does not send externally to arbitrary submitted email
it uses sanitized metadata
it does not include raw password/token/secrets
it records send attempt

If not implemented in first spec, verify no external failed-signup emails are accidentally sent.

27.7 Required Gates

Before marking implementation complete:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

Agents must not mark spec items complete unless relevant tests/gates pass or blockers are explicitly documented.

28. Implementation Constraints for Future Agents

Future spec-author, plan, and build agents must obey these constraints:

Search before editing.
Inspect current auth service before changing flow behavior.
Preserve pending-verification access restrictions.
Use EmailService; do not call Brevo directly from AuthService.
Use Brevo template IDs from configuration.
Do not hardcode real secrets.
Do not commit .env.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not log token URLs in production.
Do not store rendered email bodies.
Do not send welcome email before verification.
Do not make signup fail solely because email send failed.
Do not reveal account existence in forgot-password flow.
Do not verify accounts based on Brevo open/click/delivery events.
Do not edit frontend repo.
Do not implement frontend pages.
Do not edit Pay Service.
Do not invent billing email triggers.
Do not invent newsletter email triggers.
Do not invent support email workflow triggers.
Do not implement automatic retry worker in this phase.
Use Alembic for schema changes.
Import new models through existing model import mechanism.
Run required test gates before completion.
Append progress entries to EOF if using progress/progress.txt.
Do not mark incomplete spec items complete.
29. Suggested Future Spec Items

A future implementation spec may include items like:

auth-email-001: Add/verify auth email configuration values
auth-email-002: Add EmailService auth email methods
auth-email-003: Wire signup verification email through EmailService
auth-email-004: Preserve signup success when provider send fails
auth-email-005: Wire resend verification through EmailService
auth-email-006: Wire successful verification welcome email
auth-email-007: Wire forgot-password password reset email
auth-email-008: Wire password/account details changed notification where existing flow supports it
auth-email-009: Add tests for signup/resend/verify/forgot/reset email behavior
auth-email-010: Add token-safety assertions for send-attempt metadata
auth-email-999: Run compileall and Docker test gate

These are suggestions only. The actual spec-author run should inspect the current repository and generate a final implementation spec based on real code.

30. Relationship to Later Email Docs

This auth flow document is one part of the email architecture set.

Remaining related documents should cover:

docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md

Expected division:

Auth_Email_Verification_Flow.md defines auth business flow integration.
Email_Delivery_Events_And_Webhooks.md defines Brevo webhook ingestion and delivery event storage.
Email_Template_Catalog.md defines all templates, senders, parameters, and trigger rules.
Transactional_Email_Agent_Run_Guidance.md defines how the spec-author/plan/build agents should run the implementation workstream.
31. Summary Decision

The Zeptalytic Web Backend will integrate auth-related transactional emails through a provider-neutral EmailService backed by Brevo.

Signup must create a pending-verification account and authenticated restricted session even if verification email sending fails.

Resend verification should create a new token and send through EmailService.

Email verification must be based on backend token validation, not Brevo delivery/open/click events.

Welcome email should be sent only after successful verification.

Forgot-password must remain account-enumeration safe and must not reveal whether email sending failed.

Password reset/account change notifications should be sent only after successful sensitive account changes and must not include secrets.

All auth email send attempts should be recorded, but raw tokens and token URLs must never be persisted in operational metadata.

The first implementation must not add frontend code, billing triggers, newsletter automation, support workflow triggers, or automatic retry workers unless separate specs explicitly define those areas.