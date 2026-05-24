# Zeptalytic Web Backend Planning Prompt

You are Codex working in this repository.

This run is PLANNING ONLY.

End the run with exactly:

```text
PLAN_DONE
Rules
Do NOT modify runtime application code in this run.
Allowed changes: specs/, docs/, README.md, PROMPT.md, prompt/*, scripts/*, IMPLEMENTATION_PLAN.md, progress/*, and other planning-only files.
Keep changes small and reviewable.
Do not implement application behavior in planning mode.
Do not add dependencies unless John explicitly approved them.
Do not edit the frontend repo.
Do not edit the Pay Service repo.
Do not create frontend API clients.
Do not modify React/Vite files.
Do not redesign stable frontend pages.
0) Current mission

The active backend workstream is transactional email service implementation using Brevo.

The intended active spec is:

specs/transactional_email_service_brevo.json

This backend planning pass should confirm that the active spec is ready for build iterations that implement Brevo-backed transactional email functionality in the parent FastAPI backend.

The planning pass may refine the spec, docs, prompts, or implementation plan if repo reality requires it.

The planning pass must not implement transactional email runtime code directly.

The planning pass must remain backend-only and must not expand into frontend, Pay Service, billing lifecycle, newsletter automation, support workflow automation, or production deployment work.

1) Rehydrate context mandatory

Read:

AGENTS.md
IMPLEMENTATION_PLAN.md
PROMPT.md if present
progress/progress.txt last 1–3 entries
Determine the ACTIVE SPEC from the Active spec: line in IMPLEMENTATION_PLAN.md
Read the ACTIVE SPEC file
Read specs/next_phase_spec_sequence.json if present
Read docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
Read docs/architecture/Transactional_Email_Service_Architecture.md
Read docs/architecture/Auth_Email_Verification_Flow.md
Read docs/architecture/Email_Delivery_Events_And_Webhooks.md
Read docs/architecture/Email_Template_Catalog.md
Read docs/architecture/Transactional_Email_Agent_Run_Guidance.md
Read docs/architecture/Auth_Session_and_Security_Flows.md if present
Read docs/architecture/Parent_Backend_Application_Architecture.md if present
Read docs/architecture/Parent_Backend_API_Contract_Standards.md if present
Read docs/architecture/Parent_Backend_Repository_Layer_Design.md if present
Read docs/architecture/Parent_Backend_Service_Layer_Design.md if present
Read docs/architecture/Security_Operational_Control_Guide.md if present
Read docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md if present
Read docs/architecture/Spec_Authoring_and_Harness_Workflow.md if present
Run git status
Run git log -5 --oneline

If the active spec file does not exist, append a blocker/planning entry explaining that spec-authoring must be run first, then end with PLAN_DONE.

2) Confirm repo reality before editing

Search before editing and summarize current related code, file layout, wiring, and tests.

Use relevant commands such as:

git ls-files
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
find app -maxdepth 5 -type f | sort
find tests -maxdepth 5 -type f | sort
find docs -maxdepth 3 -type f | sort
find alembic -maxdepth 3 -type f | sort || true

When config/provider integration is in scope, inspect at minimum:

the backend settings/config module
.env.example
existing integration/client patterns
existing test patterns for config and provider failures
existing dependency stack before suggesting any new dependency
existing timeout and external-service error-handling conventions

When auth email integration is in scope, inspect at minimum:

signup/login/logout/session routes
email verification routes
resend verification flow
forgot-password flow
reset-password flow
token model/repository/service logic
account status and pending-verification behavior
tests that assert auth behavior and pending-verification behavior

When persistence is in scope, inspect at minimum:

SQLAlchemy model conventions
one-table-per-file model placement
model import registration mechanism
repository conventions
Alembic migration conventions
UUID, JSONB, enum/string status, and timestamp patterns
test database setup and migration/test fixture patterns

When webhook route is in scope, inspect at minimum:

router registration conventions
public webhook route conventions if any
OpenAPI inclusion conventions
request validation/error-response conventions
tests for public provider callbacks if any

Do not assume the current workstream still matches repo reality until you verify it.

Do not assume something is missing until you search for it.

3) Planning output

Refine the ACTIVE SPEC only if repo reality, blocker history, command drift, topology drift, or architecture-doc drift requires it.

Keep items focused enough for one build iteration each.

Expected implementation sequence normally remains:

email/Brevo configuration
template catalog and sender profile resolver
BrevoClient abstraction
email_send_attempts model/repository/migration
email_delivery_events model/repository/migration
provider-neutral EmailService
auth integration for signup verification
auth integration for resend verification
auth integration for forgot-password
post-verification welcome email
account-details-changed notification only if safely supported by existing flow
Brevo webhook route with secret validation
delivery event normalization and deduplication
tests for configuration, catalog, sender mapping, BrevoClient, EmailService, persistence, auth integration, webhook security, event normalization, and dedupe
full backend verification

Do not expand the spec into frontend implementation.

Do not add a broad UI integration spec in the backend repo.

Do not add a broad billing integration spec.

Do not add newsletter automation.

Do not add support workflow email automation.

Do not add automatic retry/outbox worker implementation.

Do not collapse unrelated future work into this transactional email spec.

Record blockers, command drift, topology drift, missing docs, or architecture-doc drift in repo docs when relevant.

4) Scope guardrails
Do not edit the frontend repo.
Do not edit the Pay Service repo.
Do not create frontend API clients.
Do not modify React/Vite files.
Do not redesign stable frontend pages.
Do not duplicate Pay commercial business rules in parent.
Do not store sensitive payment details in parent.
Do not implement billing/order/payment email triggers unless the ACTIVE SPEC explicitly scopes them.
Do not implement newsletter/update triggers unless the ACTIVE SPEC explicitly scopes them.
Do not implement support email workflow triggers unless the ACTIVE SPEC explicitly scopes them.
Do not invent an account email-change workflow if one does not already exist.
Do not create broad unused repositories/services detached from the active spec.
Do not implement runtime code in planning mode.
Do not add dependencies unless John explicitly approved them.
Do not modify database schema in planning mode.
Do not use no-reply@zeptalytic.com.
Do not store raw verification tokens.
Do not store raw password reset tokens.
Do not store full token URLs in operational metadata.
Do not store rendered email bodies.
Do not commit real Brevo API keys.
Do not commit real webhook secrets.
Preserve HTTP-only cookie auth.
Preserve signup success when email send fails.
Preserve forgot-password account-enumeration safety.
Preserve pending-verification restrictions.
Do not verify accounts from Brevo sent/delivered/opened/clicked events.
Do not mutate account state from delivery webhooks.
Do not mutate billing/payment/Pay state from delivery webhooks.
Do not mutate support-ticket state from delivery webhooks.
Do not implement automatic retry/outbox worker in this phase.
5) Durable artifacts
Append a planning entry to progress/progress.txt.
Verify the progress entry is appended at EOF.
If docs/specs are refined, keep changes small and reviewable.
If tests are required for a docs-only planning run, use the authoritative Docker command only if appropriate.
If the topology is missing or unusable, record the blocker and stop safely.
Commit only planning/doc files if tests are green and a commit is appropriate.

Do not put secrets, raw tokens, or full token URLs in progress entries.

Do not mark incomplete spec items complete.

Do not update runtime application files in planning mode.

6) Final response requirements

In the final response, summarize:

active spec
repo search summary
planning changes made
files changed
non-goals preserved
blockers or assumptions
exact next command

End the final response with exactly:

PLAN_DONE