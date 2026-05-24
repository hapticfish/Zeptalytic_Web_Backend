# Codex rules for Zeptalytic Web Backend

## Purpose of this repo

A FastAPI-based parent-site backend for the Zeptalytic ecosystem.

This service owns:

- auth / sessions / account profile / settings / addresses
- support tickets / attachments / announcements / service status
- rewards / objectives / badges / points / progress presentation
- browser-facing aggregation for dashboard / launcher / billing
- parent-side integration contracts to the Zeptalytic Pay service
- parent account identity and product-facing account state
- parent-side transactional email orchestration and delivery telemetry

This service does not own commercial payment truth.

This service does not own mailbox hosting or human reply handling.

## Current backend workstream

The current backend workstream is transactional email service implementation using Brevo.

The target active spec is:

```text
specs/transactional_email_service_brevo.json
```

This workstream prepares the FastAPI parent backend to send transactional email through Brevo, persist email send attempts, ingest Brevo delivery events, and wire approved auth/account email flows.

It is limited to backend-side transactional email infrastructure and approved auth integrations:

- email/Brevo runtime configuration
- template catalog and sender profile resolver
- Brevo API client abstraction
- provider-neutral `EmailService`
- `email_send_attempts` model/table/repository/migration
- `email_delivery_events` model/table/repository/migration
- Brevo webhook route with secret validation
- delivery event normalization and deduplication
- auth integration for signup verification, resend verification, forgot-password, and post-verification welcome email
- account-details-changed notification only where the existing reset/account flow safely supports it
- backend compile/test verification

This workstream must not edit the frontend repo.

This workstream must not edit the Zeptalytic Pay Service repo.

This workstream must not invent billing, newsletter, or support workflow email triggers.

This workstream must not implement automatic email retry/outbox workers unless explicitly scoped by the active spec.

## Non-negotiable rules always

- Do not add new dependencies unless John explicitly approves.
- Do not delete files unless the active implementation plan explicitly says to.
- Prefer small, safe, reviewable changes.
- Keep parent-site ownership separate from Pay ownership.
- Do not move commercial/billing truth into this repo.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment details in parent.
- Do not dump unrelated models into one generic file.
- Default rule: one table/model per file unless a tightly-coupled pair is explicitly justified.
- If sensible directories do not exist, create them rather than collapsing concerns into one file.
- Search before editing.
- Do not assume something is missing until the repo has been searched.
- Do not mark incomplete work complete.
- Keep progress append-only.
- Append progress entries to the absolute end of `progress/progress.txt`.
- Do not edit the frontend repo.
- Do not edit the Pay Service repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.
- Do not commit real secrets.
- Do not commit raw tokens.
- Do not put secrets, raw tokens, or full token URLs in docs, specs, progress logs, tests, fixtures, OpenAPI examples, source defaults, `docker-compose.yml`, `fly.toml`, or GitHub Actions workflow bodies.

## Locked architecture boundaries

- Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, Stripe, and Coinbase Commerce.
- Parent backend owns auth/settings/addresses/support/rewards/announcements/testimonials/dashboard aggregation.
- Parent may initiate checkout, plan change, cancellation, pause, restart, or payment-method-management flows, but Pay executes commercial behavior.
- Stripe.js / Elements + SetupIntents is the intended payment-method update path.
- Parent must not store full card numbers, CVV/CVC, raw payment credentials, private wallet keys, or sensitive provider secrets in normal app tables.
- Discord current active linkage is modeled on `profiles`, with preserved historical connection state tracked separately.
- Discord linkage does not affect rewards or product access in phase 1.
- The docs under `docs/architecture/` are durable reference material; do not contradict them without updating the relevant decision record first.

## Transactional email boundaries

- Brevo is the transactional email provider.
- Google Workspace owns mailboxes, aliases, and human reply handling.
- The backend sends transactional emails through Brevo.
- Brevo does not log into Google Workspace.
- Use real reply-capable senders.
- Do not use `no-reply@zeptalytic.com`.
- Auth/account/security emails use `Zeptalytic Support <support@zeptalytic.com>` with `support@zeptalytic.com` reply-to.
- General product/account emails use `Zeptalytic <hello@zeptalytic.com>` with `support@zeptalytic.com` reply-to.
- Support response emails use `Zeptalytic Support <support@zeptalytic.com>` with `support@zeptalytic.com` reply-to.
- Billing/order/payment emails use `Zeptalytic Billing <billing@zeptalytic.com>` with `billing@zeptalytic.com` reply-to.
- Updates/news/newsletter emails use `Zeptalytic Updates <updates@zeptalytic.com>` with `support@zeptalytic.com` reply-to.
- System/operational alerts use `Zeptalytic Alerts <alerts@zeptalytic.com>` with `support@zeptalytic.com` reply-to.
- Signup must succeed even if verification email sending fails.
- Forgot-password must remain account-enumeration safe.
- Welcome email is sent only after successful email verification.
- Account-details-changed notifications may be wired only where the existing reset/account flow safely supports them.
- Email delivery webhooks are telemetry and must not verify accounts, reset passwords, mutate billing state, mutate Pay state, or mutate support state.
- Billing/order/payment email triggers are future scope until a Pay/billing spec defines them.
- Newsletter/update email triggers are future scope until a communications/newsletter spec defines them.
- Support workflow email triggers are future scope until a support spec defines them.
- Automatic retry/outbox worker is future scope.
- Do not store raw verification tokens, raw password reset tokens, full token URLs, rendered email bodies, Brevo API keys, or webhook secrets in operational metadata or committed files.
- Send-attempt records may store safe operational metadata only.
- Delivery-event records may store raw provider webhook payloads as JSONB, but raw payloads must not be exposed through public APIs.

## Frontend runtime integration boundaries

- The React/Vite frontend is a separate repo and must not be edited by backend harness runs.
- Backend runtime readiness must support browser requests from:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- Credentialed CORS must be explicit and non-wildcard.
- Frontend requests must be able to use `credentials: "include"`.
- Backend auth must preserve HTTP-only cookie session behavior.
- Backend must not expose raw session tokens in browser-readable responses.
- Backend OpenAPI/docs should accurately describe frontend-facing routes.
- Backend route inventory must be based on actual repo reality, not invented endpoints.

## Required rehydrate behavior every run

Read these first:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. Determine the active spec from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the active spec file when the run mode is `plan` or `build`
7. Read `specs/next_phase_spec_sequence.json` when present and relevant
8. Rehydrate the architecture docs named in `IMPLEMENTATION_PLAN.md`
9. Run `git status`
10. Run `git log -5 --oneline`

## Required architecture references for this workstream

Read these when relevant to transactional email service implementation:

- `docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md`
- `docs/architecture/Transactional_Email_Service_Architecture.md`
- `docs/architecture/Auth_Email_Verification_Flow.md`
- `docs/architecture/Email_Delivery_Events_And_Webhooks.md`
- `docs/architecture/Email_Template_Catalog.md`
- `docs/architecture/Transactional_Email_Agent_Run_Guidance.md`
- `docs/architecture/Auth_Session_and_Security_Flows.md`
- `docs/architecture/Parent_Backend_Application_Architecture.md`
- `docs/architecture/Parent_Backend_API_Contract_Standards.md`
- `docs/architecture/Parent_Backend_Repository_Layer_Design.md`
- `docs/architecture/Parent_Backend_Service_Layer_Design.md`
- `docs/architecture/Security_Operational_Control_Guide.md`
- `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md`
- `docs/architecture/Spec_Authoring_and_Harness_Workflow.md`

If any of these files are missing, search for equivalent docs before assuming the information is unavailable.

## Legacy/foundation architecture references

Read these when relevant to parent DB, domain vocabulary, Discord schema placement, rewards schema, rewards verification, or earlier completed workstreams:

- `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
- `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
- `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`
- `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md`
- `docs/architecture/Discord_Integration_Decision_Record.md`
- `docs/architecture/Rewards_Objectives_Badges_Domain_Decision_Record.md`
- `docs/architecture/Rewards_Objectives_Badges_Data_Model_Reference.md`
- `docs/architecture/Rewards_Objectives_Badges_UI_Interaction_Reference.md`
- `docs/architecture/Discord_Rewards_Workstream_Sequence.md`

`docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` is the canonical source for parent-site vocabulary, enum values, and status names.

## Next-phase architecture references

Read these when relevant to application-layer, API, service, repository, integration, dashboard, billing, support, rewards, Discord, worker, security, frontend-contract, or transactional-email-adjacent work:

- `docs/architecture/Spec_Authoring_and_Harness_Workflow.md`
- `docs/architecture/Parent_Backend_Application_Architecture.md`
- `docs/architecture/Parent_Backend_API_Contract_Standards.md`
- `docs/architecture/Parent_Backend_Repository_Layer_Design.md`
- `docs/architecture/Parent_Backend_Service_Layer_Design.md`
- `docs/architecture/Parent_Pay_Integration_and_Projection_Strategy.md`
- `docs/architecture/Frontend_Backend_Contract_Map.md`
- `docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md`
- `docs/architecture/Auth_Session_and_Security_Flows.md`
- `docs/architecture/Dashboard_Launcher_Billing_Aggregation_Design.md`
- `docs/architecture/Support_Announcements_and_Status_Design.md`
- `docs/architecture/Rewards_Application_and_Notification_Flows.md`
- `docs/architecture/Discord_Integration_Application_Flow.md`
- `docs/architecture/Background_Jobs_Sync_and_Event_Processing.md`
- `docs/architecture/Security_Operational_Control_Guide.md`
- `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md`

## Spec-authoring mode

When running:

```bash
./scripts/ralph-loop.sh spec_author 1
```

the agent uses:

```text
prompt/prompt_spec_author.md
```

The spec-authoring run may create or update exactly one spec JSON file and must append a progress entry to the absolute end of `progress/progress.txt`.

For the current phase, the expected spec is:

```text
specs/transactional_email_service_brevo.json
```

The spec-authoring run must not implement runtime application code.

The spec-authoring run must not modify database models, Alembic migrations, routers, services, repositories, schemas, workers, integrations, tests, frontend files, or Pay Service files unless explicitly instructed.

The spec-authoring run must not commit real secrets, raw tokens, or full token URLs.

The spec-authoring run must end with:

```text
SPEC_DONE
```

## Planning mode

When running:

```bash
./scripts/ralph-loop.sh plan 1
```

the agent uses:

```text
prompt/prompt_plan.md
```

Planning mode may update planning-only artifacts such as specs, docs, prompts, scripts, `IMPLEMENTATION_PLAN.md`, and progress files.

Planning mode must not implement runtime application code.

Planning mode must not edit the frontend repo.

Planning mode must not edit the Pay Service repo.

Planning mode must not commit real secrets, raw tokens, or full token URLs.

Planning mode must end with:

```text
PLAN_DONE
```

## Build mode

When running:

```bash
./scripts/ralph-loop.sh build 1
```

the agent uses:

```text
prompt/prompt_build.md
```

Build mode implements exactly one active spec item where `passes=false`.

Build mode must search before editing, keep changes scoped, add/update tests, run verification, update the active spec honestly, and append progress at EOF.

Build mode must not edit the frontend repo.

Build mode must not edit the Pay Service repo.

Build mode must not commit real secrets, raw tokens, or full token URLs.

Build mode must end with one of:

```text
ITERATION_DONE
ALL_DONE
ITERATION_BLOCKED
```

## Search-before-edit rule

Before changing code, search the repo for:

- existing config/settings patterns
- existing provider integration/client patterns
- existing service patterns
- existing repository patterns
- existing schema/DTO patterns
- existing SQLAlchemy model patterns
- existing Alembic migration patterns
- existing model import registration patterns
- existing auth/signup/email verification behavior
- existing resend-verification behavior
- existing forgot-password/reset-password behavior
- existing router registration patterns
- existing public webhook route patterns
- existing OpenAPI behavior
- existing tests that already cover the same surface
- existing documentation for auth, security, provider integrations, and transactional email
- existing frontend/backend contract documentation where auth browser behavior is relevant

Use tools such as:

```bash
git ls-files
git grep
rg
find
grep -R
```

Do not assume something is missing until the repo has been searched.

## Test requirement

Do not claim implementation work is complete until these pass:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

If the command cannot run, record the blocker in `progress/progress.txt`, do not mark any spec item complete, and stop the iteration.

## Durable artifact rule

When a run is successful:

- update only the active spec item that was fully completed
- append a new entry to `progress/progress.txt`
- verify the progress entry is appended at EOF
- keep progress append-only
- do not mark incomplete work complete
- do not introduce unrelated dirty files
- do not introduce frontend repo changes
- do not introduce Pay Service repo changes
- do not introduce real secrets, raw tokens, or full token URLs

## Transactional email workstream strategy

Use this sequence for the transactional email service spec:

1. email/Brevo runtime configuration
2. template catalog and sender profile resolver
3. BrevoClient abstraction
4. `email_send_attempts` model/repository/migration
5. `email_delivery_events` model/repository/migration
6. provider-neutral `EmailService`
7. auth integration for signup verification
8. auth integration for resend verification
9. auth integration for forgot-password
10. post-verification welcome email
11. account-details-changed notification only where existing flow safely supports it
12. Brevo webhook route with secret validation
13. delivery event normalization and deduplication
14. full tests and backend verification

Do not create one giant implementation item.

Do not perform frontend wiring in this repo.

Do not edit the Pay Service repo.

Do not move on to billing, newsletter, support email workflows, retry workers, or production deployment until this transactional email service spec is complete or John explicitly directs otherwise.

## Frontend runtime readiness workstream strategy

Use this sequence for any future backend readiness spec if John explicitly reactivates that workstream:

1. CORS runtime settings
2. FastAPI CORSMiddleware wiring
3. browser cookie auth contract verification/documentation
4. frontend-facing backend API route inventory
5. OpenAPI runtime surface regression coverage
6. full backend verification

Do not create one giant integration spec.

Do not perform frontend wiring in this repo.

Do not move on to frontend harness work until the backend readiness spec is complete or John explicitly directs otherwise.

## Non-goals unless explicitly scoped

Do not implement these unless the active spec explicitly requires them:

- frontend API clients
- React/Vite route changes
- frontend protected route implementation
- frontend data replacement
- admin dashboards
- duplicated Pay commercial logic
- local parent-side payment truth
- raw card/payment credential handling
- frontend APIs that directly award points/rewards/badges
- Discord-based rewards
- Discord-based product access
- product-app event ingestion beyond the active spec
- broad unused repositories/services unrelated to the active spec
- database schema changes outside the active spec
- new dependencies without John’s approval
- billing/order/payment email triggers
- newsletter/update email triggers
- support workflow email triggers
- automatic email retry/outbox worker
- email admin dashboard
- Brevo contact list synchronization
- communication preference mutation from Brevo unsubscribe events
- account verification from Brevo sent/delivered/opened/clicked events
- billing/payment/Pay state mutation from email delivery events
- support-ticket state mutation from email delivery events
- frontend email pages/routes
- Pay Service email integration
- real secrets in committed files
- raw verification token storage
- raw password reset token storage
- full token URL storage in operational metadata
- rendered email body storage
```