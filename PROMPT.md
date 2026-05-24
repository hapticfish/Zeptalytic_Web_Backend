Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, the active spec file when present, and `progress/progress.txt`.

The active backend workstream is transactional email service implementation using Brevo.

The target active spec is:

```text
specs/transactional_email_service_brevo.json
```

The following architecture docs are the primary source for this transactional email workstream:

```text
docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md
docs/architecture/Transactional_Email_Service_Architecture.md
docs/architecture/Auth_Email_Verification_Flow.md
docs/architecture/Email_Delivery_Events_And_Webhooks.md
docs/architecture/Email_Template_Catalog.md
docs/architecture/Transactional_Email_Agent_Run_Guidance.md
```

These backend architecture, security, API, service, and repository references should also be used when present:

```text
docs/architecture/Auth_Session_and_Security_Flows.md
docs/architecture/Parent_Backend_Application_Architecture.md
docs/architecture/Parent_Backend_API_Contract_Standards.md
docs/architecture/Parent_Backend_Repository_Layer_Design.md
docs/architecture/Parent_Backend_Service_Layer_Design.md
docs/architecture/Security_Operational_Control_Guide.md
docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md
docs/architecture/Spec_Authoring_and_Harness_Workflow.md
```

`docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` remains the canonical source for parent-site vocabulary, enum values, and status names where domain terminology is involved.

Then:

- for spec-authoring runs, follow `prompt/prompt_spec_author.md`
- for planning runs, follow `prompt/prompt_plan.md`
- for build runs, follow `prompt/prompt_build.md`

The active backend workstream sequence is:

1. transactional email spec authoring
2. planning review/refinement
3. email/Brevo runtime configuration
4. template catalog and sender profile resolver
5. Brevo API client abstraction
6. `email_send_attempts` model/repository/migration
7. `email_delivery_events` model/repository/migration
8. provider-neutral `EmailService`
9. auth integration for signup verification
10. auth integration for resend verification
11. auth integration for forgot-password/password reset email
12. post-verification welcome email
13. account-details-changed notification only where the existing reset/account flow safely supports it
14. Brevo webhook route with secret validation
15. delivery event normalization and deduplication
16. tests for configuration, template mapping, sender mapping, Brevo client behavior, send-attempt logging, auth integration, webhook ingestion, deduplication, and failure handling
17. full backend compile and Docker test verification

This backend harness run must not edit the frontend repo.

Do not create frontend API clients here.

Do not modify React/Vite files here.

Do not redesign frontend pages here.

This backend harness run must not edit the Zeptalytic Pay Service repo.

Do not duplicate Pay commercial business rules in parent.

Do not store sensitive payment details in parent.

Do not invent billing/order/payment email triggers.

Do not invent newsletter/update email triggers.

Do not invent support workflow email triggers.

Do not implement automatic retry/outbox worker in this phase.

Do not use `no-reply@zeptalytic.com`.

Do not commit real Brevo API keys.

Do not commit real webhook secrets.

Do not place real secrets in `.env.example`, docs, specs, progress logs, tests, fixtures, OpenAPI examples, source defaults, `docker-compose.yml`, `fly.toml`, or GitHub Actions workflow bodies.

Do not store raw verification tokens.

Do not store raw password reset tokens.

Do not store full verification/reset URLs with tokens in send-attempt metadata.

Do not store rendered email bodies.

Signup must succeed even if verification email sending fails.

Forgot-password must remain account-enumeration safe.

Pending-verification access restrictions must be preserved.

Welcome email must be sent after successful email verification, not before.

Welcome email failure must not undo successful verification.

Brevo delivery webhook events are telemetry only.

Brevo delivery webhook events must not verify accounts, reset passwords, mutate billing state, mutate Pay state, or mutate support-ticket state.

The expected final verification commands before implementation completion are:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```