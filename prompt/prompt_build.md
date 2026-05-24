# Zeptalytic Web Backend Build Prompt

You are Codex working in this repository.

Run ONE build iteration only.

End the run with one of:

```text
ITERATION_DONE
ALL_DONE
ITERATION_BLOCKED
```

## 0) Current mission

The active backend workstream is transactional email service implementation using Brevo.

The intended active spec is:

```text
specs/transactional_email_service_brevo.json
```

This build pass must implement exactly one incomplete item from the active spec.

The work must remain backend-only.

Do not edit the frontend repo.

Do not edit the Pay Service repo.

Do not create frontend API clients.

Do not modify React/Vite files.

Do not redesign frontend pages.

## 1) Rehydrate context mandatory

Read:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. Determine the ACTIVE SPEC from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the ACTIVE SPEC file
7. Read `specs/next_phase_spec_sequence.json` if present
8. Read `docs/architecture/Brevo_Google_Workspace_Email_Decision_Record.md`
9. Read `docs/architecture/Transactional_Email_Service_Architecture.md`
10. Read `docs/architecture/Auth_Email_Verification_Flow.md`
11. Read `docs/architecture/Email_Delivery_Events_And_Webhooks.md`
12. Read `docs/architecture/Email_Template_Catalog.md`
13. Read `docs/architecture/Transactional_Email_Agent_Run_Guidance.md`
14. Read `docs/architecture/Auth_Session_and_Security_Flows.md` if present
15. Read `docs/architecture/Parent_Backend_Application_Architecture.md` if present
16. Read `docs/architecture/Parent_Backend_API_Contract_Standards.md` if present
17. Read `docs/architecture/Parent_Backend_Repository_Layer_Design.md` if present
18. Read `docs/architecture/Parent_Backend_Service_Layer_Design.md` if present
19. Read `docs/architecture/Security_Operational_Control_Guide.md` if present
20. Read `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md` if present
21. Read `docs/architecture/Spec_Authoring_and_Harness_Workflow.md` if present
22. Run `git status`
23. Run `git log -5 --oneline`

If the active spec file does not exist, append a blocker entry to `progress/progress.txt`, do not modify implementation files, print exactly `ITERATION_BLOCKED`, and stop.

## 2) Pick ONE item to work on

Choose exactly one item in the ACTIVE SPEC where:

```json
"passes": false
```

Prefer earlier items first unless a later item is clearly blocking.

Do not work on more than one item in a single build iteration unless the active spec item itself explicitly requires a tiny companion change.

Do not mark any item complete unless its acceptance criteria are fully satisfied and required verification passes.

## 3) Search before editing mandatory

Use:

```bash
git ls-files
git grep
rg
find
grep -R
```

Before changing anything, summarize what you found:

- file paths
- key functions/classes/models/schemas/repositories/services involved
- current config/settings structure
- current router registration
- current auth/signup/verification/password reset behavior
- current model/import/migration structure
- current repository/service patterns
- current provider integration patterns
- current OpenAPI behavior
- existing tests that already cover the target area
- gaps the selected spec item should address

Use relevant commands such as:

```bash
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
find alembic -maxdepth 3 -type f | sort || true
```

Do not assume something is missing until you search for it.

## 4) Implement the smallest safe change

- Keep changes small and localized.
- Match repository patterns and architecture docs.
- Do not add dependencies unless John explicitly approved them.
- Do not delete files unless the active plan/spec explicitly says to.
- Do not guess unresolved business rules.
- Leave TODO markers only when the decision record has not locked the rule yet.
- Do not modify unrelated files.
- Do not implement future spec work early.
- Do not duplicate existing patterns without searching first.
- Do not edit the frontend repo.
- Do not edit the Pay Service repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.

## 5) Transactional email guardrails

- Follow the ACTIVE SPEC exactly.
- Preserve `/api/v1` API versioning.
- Preserve HTTP-only cookie auth.
- Preserve pending-verification access restrictions.
- Use Brevo as the transactional email provider.
- Use Google Workspace only as mailbox/alias/reply-handling context.
- Use real reply-capable senders.
- Do not use `no-reply@zeptalytic.com`.
- Do not commit real Brevo API keys.
- Do not commit real webhook secrets.
- Do not place real secrets in `.env.example`, docs, specs, progress logs, `docker-compose.yml`, `fly.toml`, tests, fixtures, OpenAPI examples, or source defaults.
- Route email sends through `EmailService`; do not call Brevo directly from `AuthService`.
- Keep Brevo-specific HTTP logic isolated in `BrevoClient`.
- Store backend send attempts in `email_send_attempts`.
- Store Brevo delivery webhook events in `email_delivery_events`.
- Store raw Brevo webhook payloads as JSONB.
- Do not expose raw webhook payloads through public APIs.
- Do not store rendered email bodies.
- Do not store raw verification tokens.
- Do not store raw password reset tokens.
- Do not store full verification/reset URLs with tokens in send-attempt metadata.
- Signup must succeed even if verification email sending fails.
- Forgot-password must remain account-enumeration safe.
- Welcome email must be sent after successful email verification, not before.
- Welcome email failure must not undo verification.
- Do not verify accounts based on Brevo sent/delivered/opened/clicked events.
- Do not mutate billing/payment/Pay state from email delivery events.
- Do not mutate support-ticket state from email delivery events.
- Do not invent billing/order/payment email triggers.
- Do not invent newsletter/update email triggers.
- Do not invent support workflow email triggers.
- Do not invent an email-change workflow if it does not already exist.
- Do not implement automatic retry/outbox worker in this phase.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment data in parent.
- Do not implement admin dashboards unless explicitly scoped.
- Do not make Discord linkage affect rewards or product access unless explicitly scoped.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not implement unrelated routers/services/repositories outside the ACTIVE SPEC.
- Do not return raw ORM objects from routers.
- Use explicit safe DTOs for API responses.

## 6) Tests required

Add or update tests for the behavior/structure you changed.

For structural refactors, add regression tests that prove the intended layout and registration still work.

Expected test areas by item:

- Config/settings: email provider, Brevo base URL, timeout, webhook secret, frontend base URL, senders, template IDs, `.env.example` placeholders.
- Template catalog/sender resolver: all 11 template keys, correct sender profiles, no no-reply sender, future-scope templates not accidentally triggered.
- BrevoClient: correct endpoint/payload, success response, provider message ID, timeout/HTTP/unexpected response failure mapping, no secret logging.
- EmailService: send attempt creation/update, success/failure status, template key/provider template ID/sender/reply-to stored, raw tokens not stored.
- Send-attempt persistence: model/repository/migration fields, statuses, JSONB metadata, no rendered body/token storage.
- Delivery-event persistence: model/repository/migration fields, raw payload JSONB, unique dedupe key.
- Auth integration: signup verification, resend verification, forgot-password, successful verification welcome email, account-details-changed notification if safely wired.
- Webhook route: missing/invalid secret rejected, valid event stored, duplicate event returns success, unknown event stored as unknown, malformed payload handled safely.
- OpenAPI surface: webhook route included or intentionally excluded according to project convention.
- Full verification item: no code behavior change required, but required commands must pass.

If tests fail, fix them in this same iteration; do not move on while tests are failing.

At minimum, run:

```bash
python -m compileall app tests alembic
```

Then run the authoritative Docker test suite:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

## 7) If Docker or verification is blocked

If Docker is unavailable or the authoritative command cannot run:

- append a blocker entry to `progress/progress.txt`
- verify the blocker entry is appended at EOF
- do not mark any spec item complete
- do not update `IMPLEMENTATION_PLAN.md` as complete
- print exactly:

```text
ITERATION_BLOCKED
```

- stop the iteration

If the topology or command is missing/unusable:

- append the blocker and repo-reality evidence to `progress/progress.txt`
- do not mark any spec item complete
- print exactly:

```text
ITERATION_BLOCKED
```

- stop the iteration

## 8) Update durable artifacts only when not blocked

Only when tests are green:

- Update only the ACTIVE SPEC item you fully completed:
  - `passes=true`
  - `completed_at=<ISO 8601 timestamp with timezone>`
  - `completed_by="codex"`
- Update `IMPLEMENTATION_PLAN.md` checkbox/status only if needed.
- Append an iteration entry to `progress/progress.txt`.
- Verify the new entry is appended at EOF.
- Commit only if tests are green and a commit is appropriate.

The progress entry must include:

- date/time with timezone
- active spec
- selected item
- repo search summary
- files changed
- tests run and results
- blockers if any
- next recommended item

Do not include secrets, raw tokens, or full token URLs in progress entries.

## 9) Completion marker

If the active spec is fully complete, end with exactly:

```text
ALL_DONE
```

Otherwise end with exactly:

```text
ITERATION_DONE
```

If blocked, end with exactly:

```text
ITERATION_BLOCKED
```