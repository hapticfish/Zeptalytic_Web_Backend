# Zeptalytic Web Backend Implementation Plan

Active spec: specs/frontend_runtime_integration_readiness.json

## Current phase

The parent backend broad application buildout is treated as complete through the previous frontend/backend contract-alignment slice.

The next phase is a narrow backend runtime-readiness pass for frontend integration.

This pass prepares the FastAPI parent backend to be safely called by the React/Vite frontend during local browser-based integration.

The frontend repo is separate and must not be edited by this backend harness run.

## Current active workstream

The active workstream is:

```text
specs/frontend_runtime_integration_readiness.json
```

The target outcomes are:

1. Add explicit backend CORS runtime settings for local Vite frontend origins.
2. Wire FastAPI `CORSMiddleware` safely using configured origins.
3. Verify and document the HTTP-only cookie browser auth contract.
4. Document the frontend-facing backend API route inventory from actual repo reality.
5. Add runtime OpenAPI surface regression coverage for frontend-critical routes.
6. Run backend compile and Docker verification before marking complete.

## Required local frontend origins

The backend should allow credentialed CORS for these explicit local development origins:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Do not use wildcard credentialed CORS.

## Browser auth contract

The backend auth model is HTTP-only cookie session based.

Frontend requests must use:

```ts
credentials: "include"
```

The frontend must not store raw session tokens in `localStorage` or `sessionStorage`.

The backend must not expose raw session tokens in browser-readable API responses.

The session cookie is expected to remain:

```text
zeptalytic_session
```

unless repo reality proves a different locked name is already in use.

## Backend-only scope

This backend workstream may update backend files such as:

```text
app/core/config.py
app/main.py
app/api/routers/v1/*
app/schemas/*
tests/*
docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md
docs/architecture/Frontend_Backend_Contract_Map.md
docs/openapi/*
specs/frontend_runtime_integration_readiness.json
progress/progress.txt
```

Exact paths must be confirmed by repo search before editing.

This backend workstream must not modify:

```text
../zeptalytic_web/*
frontend repo files
React/Vite source files
frontend API client files
frontend route files
frontend static data files
```

## Completed prior workstreams

The following workstreams are treated as complete and should not be re-opened unless a later spec explicitly requires corrections:

- Parent DB foundation
- Model file separation refactor
- Parent DB verification and regression hardening
- Discord identity schema correction
- Rewards DB schema
- Rewards verification/regression
- Rewards API/application-layer schema work
- Application-layer foundation
- Auth/session/account security
- Parent-to-Pay integration and projection foundation
- Profile/settings/addresses/preferences API
- Dashboard/launcher/billing aggregation API
- Support/announcements/service status API
- Rewards/objectives/badges application API
- Discord integration application flow
- Background jobs/security hardening
- Frontend/backend contract alignment

## Spec authoring

Run:

```bash
./scripts/ralph-loop.sh spec_author 1
```

The spec-authoring agent must:

- read the frontend runtime integration guide
- read relevant backend architecture/security/API contract docs
- inspect repo reality
- create or refine exactly one focused spec JSON
- target `specs/frontend_runtime_integration_readiness.json`
- append a progress entry at EOF
- not implement runtime code
- not modify database models or migrations
- not modify tests
- not edit frontend files
- end with `SPEC_DONE`

## Planning

After the spec exists, run:

```bash
./scripts/ralph-loop.sh plan 1
```

The planning agent must:

- read the active spec
- read relevant architecture docs
- inspect repo reality
- refine only planning/spec/doc artifacts if needed
- avoid runtime code implementation
- avoid frontend repo edits
- append progress at EOF
- end with `PLAN_DONE`

## Build

After the plan is reviewed:

```bash
./scripts/ralph-loop.sh build 1
```

The build agent must:

- read the active spec
- choose exactly one item where `passes=false`
- search before editing
- implement the smallest safe backend change
- add/update tests
- run required verification
- update only completed spec items
- append progress at EOF
- avoid frontend repo edits
- end with `ITERATION_DONE`, `ALL_DONE`, or `ITERATION_BLOCKED`

## Full tests

Required verification before marking implementation complete:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

If either command cannot run, record the blocker in `progress/progress.txt`, do not mark the item complete, and stop safely.

## Required architecture references

Read these before every relevant spec-authoring, planning, or build run:

- `docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md`
- `docs/architecture/Frontend_Backend_Contract_Map.md`
- `docs/architecture/Auth_Session_and_Security_Flows.md`
- `docs/architecture/Parent_Backend_Application_Architecture.md`
- `docs/architecture/Parent_Backend_API_Contract_Standards.md`
- `docs/architecture/Security_Operational_Control_Guide.md`
- `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md`
- `docs/architecture/Spec_Authoring_and_Harness_Workflow.md`

Also read these when relevant:

- `docs/architecture/Parent_Backend_Repository_Layer_Design.md`
- `docs/architecture/Parent_Backend_Service_Layer_Design.md`
- `docs/architecture/Parent_Pay_Integration_and_Projection_Strategy.md`
- `docs/architecture/Dashboard_Launcher_Billing_Aggregation_Design.md`
- `docs/architecture/Support_Announcements_and_Status_Design.md`
- `docs/architecture/Rewards_Application_and_Notification_Flows.md`
- `docs/architecture/Discord_Integration_Application_Flow.md`
- `docs/architecture/Background_Jobs_Sync_and_Event_Processing.md`

Legacy/foundation references remain valid where relevant:

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

`docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` remains the canonical source for parent-site vocabulary, enum values, and status names.

## Locked decisions

- Parent backend is a domain backend with its own state and business logic.
- Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, Stripe, and Coinbase Commerce.
- Parent may initiate checkout/change/cancel/restart flows, but Pay executes commercial behavior.
- Parent must not duplicate Pay commercial business rules.
- Parent is the sole login authority for Zeptalytic accounts.
- Product apps will trust parent-issued identity/session state.
- Email verification is required for all normal actions except opening a support ticket.
- Suspended users may log in and access billing/support.
- `account_id` links parent and Pay.
- Pay profile/customer identity should be created when parent account is created.
- Account-link failures are internal operational issues.
- APIs should be versioned under `/api/v1`.
- Use domain routers plus aggregation routers.
- Use standard error shape and simple mutation success/status responses.
- Billing/payment method/transaction truth should come from Pay live reads where required.
- Parent may mirror subscription/payment/entitlement/payment-method/product-access summaries as projections, but those are not editable commercial truth.
- If Pay is unavailable, dashboard/billing should return safe null/empty values, launcher should not launch, and manage-subscription critical actions should be blocked.
- Rewards APIs are read-oriented for frontend.
- Reward writes come from backend jobs, admin/internal operations, Pay-derived events, or product-originated events.
- Discord linkage is profile/settings display and signup capture only for phase 1.
- Discord linkage does not affect rewards or product access.
- Browser integration uses HTTP-only cookie sessions, not frontend-stored raw tokens.
- Credentialed CORS must use explicit origins, not wildcard origins.

## Progress rule

Every non-blocked run that changes files must append a progress entry to the absolute end of:

```text
progress/progress.txt
```

The newest progress entry must be the final content in the file.