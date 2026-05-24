# Zeptalytic Web Backend Spec Author Prompt

You are Codex working in this repository as the Spec Author Agent.

Run ONE spec-authoring iteration only.

Your job is to create exactly one focused implementation spec JSON for the next backend workstream.

You are not implementing runtime application code.

End the run with exactly:

```text
SPEC_DONE
0) Current mission

The active backend workstream is transactional email service implementation using Brevo.

Create or refine this spec:

specs/transactional_email_service_brevo.json

This spec prepares the FastAPI parent backend to send transactional email through Brevo, record send attempts, ingest Brevo delivery webhooks, and wire approved auth/account email flows.

The spec should focus on:

email/Brevo configuration
stable template catalog
centralized sender profile resolver
Brevo API client abstraction
provider-neutral EmailService
email_send_attempts model/table/repository/migration
email_delivery_events model/table/repository/migration
Brevo webhook route with secret validation
delivery event normalization and deduplication
auth integration for signup verification, resend verification, forgot-password, and post-verification welcome email
account-details-changed notification only where the existing reset/account flow safely supports it
provider failure handling
compile/test verification

This spec must stay backend-only.

Do not edit the frontend repo.

Do not edit the Pay Service repo.

Do not create frontend API clients.

Do not modify React/Vite files.

Do not redesign frontend pages.

Do not implement runtime application code in this run.

Do not modify database models, Alembic migrations, routers, services, repositories, schemas, workers, integrations, tests, frontend files, or Pay Service files in this run unless John explicitly instructs otherwise.

1) Rehydrate context mandatory

Read these first:

AGENTS.md
IMPLEMENTATION_PLAN.md
PROMPT.md if present
progress/progress.txt last 1–3 entries
specs/next_phase_spec_sequence.json if present
specs/_template_next_phase_spec.json if present
docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md
docs/architecture/Auth_Session_and_Security_Flows.md if present
docs/architecture/Parent_Backend_Application_Architecture.md if present
docs/architecture/Parent_Backend_API_Contract_Standards.md if present
docs/architecture/Parent_Backend_Repository_Layer_Design.md if present
docs/architecture/Parent_Backend_Service_Layer_Design.md if present
docs/architecture/Security_Operational_Control_Guide.md if present
docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md if present
docs/architecture/Spec_Authoring_and_Harness_Workflow.md if present

Also inspect current repo structure before drafting:

git status
git log -5 --oneline
git ls-files
find app -maxdepth 5 -type f | sort
find tests -maxdepth 5 -type f | sort
find specs -maxdepth 1 -type f | sort
find docs -maxdepth 3 -type f | sort
find alembic -maxdepth 3 -type f | sort || true
2) Determine the spec to author

Create exactly this spec unless it already exists and is materially complete:

specs/transactional_email_service_brevo.json

If it already exists but is incomplete, do not create a second spec. Instead, refine only that spec if needed.

If it already exists and all items have passes=true, append a progress entry explaining that no new transactional email spec was needed and stop with SPEC_DONE.

Do not create multiple implementation specs in one run.

Do not update frontend files.

Do not update Pay Service files.

Do not update IMPLEMENTATION_PLAN.md unless John explicitly asks you to activate the generated spec in the same run.

3) Search before writing the spec mandatory

Before writing or refining the spec, search for current repo reality related to transactional email, auth, config, services, repositories, models, migrations, tests, and router registration.

Use commands such as:

git grep -n "EmailService\|email_service\|Brevo\|brevo\|Sendinblue\|sendinblue" app tests docs specs || true
git grep -n "EMAIL_PROVIDER\|BREVO_\|FRONTEND_BASE_URL\|EMAIL_FROM\|EMAIL_SUPPORT\|EMAIL_BILLING\|EMAIL_ALERTS\|EMAIL_UPDATES" app tests docs .env.example || true
git grep -n "EmailVerificationToken\|email verification\|verify_email\|resend_email_verification" app tests docs || true
git grep -n "forgot_password\|reset_password\|PasswordReset\|password reset" app tests docs || true
git grep -n "signup\|create_account\|pending_verification\|email_verification_required" app tests docs || true
git grep -n "APIRouter\|include_router\|api_v1_prefix" app tests docs || true
git grep -n "Base\|declarative_base\|metadata\|import_models\|models" app/db app tests alembic || true
git grep -n "repository\|Repository\|Repo" app tests docs || true
git grep -n "JSONB\|UUID\|created_at\|updated_at" app/db app tests alembic || true
git grep -n "httpx\|requests\|AsyncClient\|Client" app tests pyproject.toml poetry.lock || true
git grep -n "openapi\|app.openapi\|include_in_schema" app tests docs || true
find app/api -maxdepth 5 -type f | sort || true
find app/services -maxdepth 5 -type f | sort || true
find app/integrations -maxdepth 5 -type f | sort || true
find app/db -maxdepth 5 -type f | sort || true
find tests -maxdepth 5 -type f | sort || true
find alembic -maxdepth 3 -type f | sort || true

Adjust searches if the repo uses different naming.

Summarize findings in the generated spec under context.repo_reality_summary.

Do not assume something is missing until you search for it.

4) Create exactly one spec JSON

Create or refine exactly one spec file:

specs/transactional_email_service_brevo.json

Use specs/_template_next_phase_spec.json as the structure guide if it exists.

Do not create multiple specs in one run.

5) Required spec structure

The spec JSON must include:

{
  "id": "transactional_email_service_brevo",
  "title": "Transactional Email Service with Brevo",
  "status": "active",
  "owner": "Zeptalytic Web Backend",
  "purpose": "<purpose>",
  "context": {
    "summary": "<summary>",
    "source_docs": [],
    "previous_specs_or_dependencies": [],
    "repo_reality_summary": []
  },
  "global_guardrails": [],
  "expected_paths": {
    "may_create_or_update": [],
    "must_not_modify_without_strong_reason": []
  },
  "items": [],
  "completion_definition": []
}

Each item must include:

{
  "id": "<item_id>",
  "title": "<item title>",
  "description": "<description>",
  "acceptance_criteria": [],
  "passes": false,
  "completed_at": null,
  "completed_by": null
}

Use passes=false for all new items.

Do not use only status=pending because the build prompt selects items by passes=false.

6) Recommended spec items

Use repo search results to adjust exact paths and item ordering, but the spec should normally contain these focused items.

email-010 Add email and Brevo configuration

Purpose:

Add backend settings for provider, Brevo API base URL/key, webhook secret, frontend base URL, sender addresses, reply-to addresses, template IDs, and request timeout.
Add .env.example placeholders only.
Do not commit real secrets.

Expected behavior:

all known template IDs are configurable
FRONTEND_BASE_URL is available for verification/reset links
real API keys and webhook secrets are not included in committed files
configuration follows existing backend settings conventions
email-020 Add template catalog and sender profile resolver

Purpose:

Add stable backend template keys for all 11 Brevo templates.
Add centralized sender profile mapping.
Use real reply-capable senders.
Do not use no-reply@zeptalytic.com.

Expected behavior:

all templates are represented
auth/security uses support sender
welcome/general account uses hello sender
billing templates use billing sender
updates template uses updates sender
support template uses support sender
future-scope templates are configured but not triggered
email-030 Add BrevoClient abstraction

Purpose:

Add a provider-specific Brevo client for transactional template sends.
Use Brevo /smtp/email endpoint under BREVO_API_BASE_URL.
Apply timeout.
Parse success response and provider message ID where available.
Normalize provider failures.

Expected behavior:

auth header/secrets are not logged
timeout maps to provider_timeout
HTTP errors map to provider_http_error
unexpected responses map to provider_unexpected_response
no business service calls Brevo directly
email-040 Add email_send_attempts model, repository, and migration

Purpose:

Add persistence for backend email send attempts.

Expected behavior:

table/model/repository/migration exist
records include account, recipient, sender, template key, provider template ID, provider message ID, status, failure code/message, metadata JSONB, and timestamps
statuses include pending, sent, failed, skipped
raw verification tokens, raw reset tokens, full token URLs, rendered email bodies, API keys, and webhook secrets are not stored
email-050 Add email_delivery_events model, repository, and migration

Purpose:

Add persistence for Brevo webhook delivery events.

Expected behavior:

table/model/repository/migration exist
records include provider, normalized event type, provider message ID, provider event ID, recipient email, template ID, subject, event timestamp, dedupe key, raw payload JSONB, and timestamps
dedupe_key is unique
unknown events can be stored as unknown
raw payload is stored but not exposed publicly
email-060 Add EmailService with approved template method coverage

Purpose:

Add provider-neutral email service.
Route all email sends through EmailService.
Use template catalog and sender profiles.
Create/update send-attempt records.
Call BrevoClient.
Normalize provider failures.

Expected behavior:

methods exist for approved auth flows
methods may exist for the complete template catalog
future-scope methods are not wired to live triggers
raw tokens/full token URLs are not stored in metadata
rendered email bodies are not stored
email-070 Wire signup verification email

Purpose:

Wire signup verification email through EmailService.

Expected behavior:

signup creates a verification token and sends email_verification
signup succeeds even if Brevo send fails
account remains pending_verification
session behavior remains unchanged
failed send attempt is recorded when send fails
raw token is not stored in metadata
email-080 Wire resend verification email

Purpose:

Wire resend verification through EmailService.

Expected behavior:

pending user can request resend according to existing auth rules
new verification token is generated
previous unused token is invalidated if existing architecture supports it or spec explicitly scopes it
email send attempt is recorded
provider failure is handled safely
account is not activated by resend
email-090 Wire forgot-password password reset email

Purpose:

Wire forgot-password to send password_reset email through EmailService.

Expected behavior:

unknown account returns generic success
eligible existing account creates reset token and sends password reset email
provider failure still returns generic success
send attempt is recorded
raw reset token/full reset URL is not stored in metadata
account existence is not revealed
email-100 Wire successful verification welcome email

Purpose:

Send welcome email after successful email verification.

Expected behavior:

backend token verification remains source of truth
Brevo open/click/delivery events do not verify account
welcome email is sent after successful verification
welcome email failure does not undo verification
send attempt is recorded
email-110 Wire account details changed notification where existing flow safely supports it

Purpose:

Wire account_details_changed after successful password reset only if current reset flow has a safe integration point.

Expected behavior:

password reset remains successful if notification send fails
no password/token/secrets included in notification metadata
if existing flow is not ready, document blocker and do not invent unrelated account-change workflow
email-120 Add Brevo webhook route with secret validation

Purpose:

Add POST /api/v1/email/webhooks/brevo.
Validate BREVO_WEBHOOK_SECRET query secret before processing.

Expected behavior:

missing/invalid secret rejected
no user session required
no CSRF required
no internal service token required
route does not mutate auth/billing/support state
route stores delivery events through repository
email-130 Add delivery event normalization and deduplication

Purpose:

Normalize Brevo webhook events.
Store raw payload.
Deduplicate events by deterministic key.

Expected behavior:

supported normalized events include sent, delivered, opened, clicked, soft_bounce, hard_bounce, invalid_email, deferred, complaint, unsubscribed, blocked, error, and unknown
duplicate events return success and do not create duplicate rows
unknown events are stored as unknown
malformed payloads are handled safely
email-140 Add tests for transactional email behavior

Purpose:

Add tests across config, catalog, sender mapping, BrevoClient, EmailService, persistence, auth integration, webhook security, event normalization, and dedupe.

Expected behavior:

tests prove approved auth email flows work
tests prove failure policies are preserved
tests prove raw tokens are not stored in metadata
tests prove no future-scope triggers are accidentally wired
tests prove webhook route is secret-protected and idempotent
email-999 Run full backend verification

Purpose:

Run compile and Docker test verification.
Do not mark complete unless required checks pass.

Required commands:

python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
7) Required guardrails for generated spec

Include these guardrails unless a stronger workstream-specific version is needed:

Search before editing.
Do not expand scope beyond this spec.
Do not add dependencies unless John explicitly approves them.
Do not edit the frontend repo.
Do not create frontend API clients.
Do not modify React/Vite files.
Do not redesign stable frontend pages.
Do not edit the Pay Service repo.
Do not duplicate Pay commercial business rules in parent.
Do not store sensitive payment details in parent.
Do not invent billing/order/payment email triggers.
Do not invent newsletter/update email triggers.
Do not invent support workflow email triggers.
Do not invent an account email-change workflow if one does not already exist.
Do not build admin dashboards unless explicitly scoped.
Do not return raw ORM objects from routers.
Use explicit safe DTOs for API responses.
Preserve HTTP-only cookie auth.
Preserve pending-verification access restrictions.
Signup must succeed even if verification email sending fails.
Forgot-password must remain account-enumeration safe.
Do not verify accounts based on Brevo delivered/opened/clicked events.
Do not mutate billing/payment state from email delivery events.
Do not mutate Pay Service state from email delivery events.
Do not mutate support-ticket state from email delivery events.
Do not implement automatic retry/outbox worker in this phase.
Do not use no-reply@zeptalytic.com.
Do not store rendered email bodies.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not store full token URLs in send-attempt metadata.
Do not commit real Brevo API keys.
Do not commit real webhook secrets.
Do not mark incomplete items complete.
Append progress entries to the absolute end of progress/progress.txt.
Run python -m compileall app tests alembic before marking implementation items complete.
Run docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test before marking implementation items complete.
8) Expected paths

The generated spec should normally allow updates to paths like:

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
IMPLEMENTATION_PLAN.md
.env.example

Only include paths that make sense after repo inspection.

The generated spec should normally forbid or strongly discourage changes to:

../zeptalytic_web/*
frontend repo files
Zeptalytic_Pay_Service/*
Pay Service repo files
node_modules/
venv/
.venv/
unrelated routers/services/repositories
unrelated database models/migrations
payment provider secret handling outside email config placeholders
9) Progress entry mandatory

Append a progress entry to the absolute end of:

progress/progress.txt

The entry must include:

date/time with timezone
mode: spec_author
selected workstream
spec file created or refined
architecture docs used
repo search summary
files changed
non-goals
risks/assumptions
next command to run

The newest progress entry must be the final content in the file.

Do not insert the progress entry above older entries.

Do not keep a footer after it.

Do not include secrets, raw tokens, or full token URLs in progress entries.

10) Final response requirements

In the final response, summarize:

which workstream was selected
which spec file was created or refined
which docs were used
which repo reality was found
which files were changed
major non-goals
risks/assumptions
exact next command

End the final response with exactly:

SPEC_DONE