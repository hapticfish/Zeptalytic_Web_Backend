# Zeptalytic Web Backend Implementation Plan

Active spec: specs/auth_session_account_security.json

## Current phase

The parent DB foundation, model file separation refactor, parent DB verification/regression hardening, Discord identity schema correction, rewards DB schema, rewards verification/regression, and rewards API/application-layer schema phase are now treated as complete.

The next phase is the broader parent backend application buildout.

The application-layer foundation spec is complete.

The auth/session/account security spec is now complete:

```text
specs/auth_session_account_security.json
```

The next recommended action is to author or activate the profile/settings/addresses/preferences workstream in roadmap order.

## Next-phase roadmap

Use this roadmap file:

```text
specs/next_phase_spec_sequence.json
```

Recommended sequence:

1. application-layer foundation
2. auth/session/account security
3. profile/settings/addresses/preferences
4. parent-to-Pay integration and projection foundation
5. dashboard/launcher/billing aggregation
6. support/announcements/service status
7. rewards/objectives/badges application APIs
8. Discord integration application flow
9. background jobs/security hardening
10. frontend/backend contract alignment

## Spec authoring

Run:

```bash
./scripts/ralph-loop.sh spec_author 1
```

The spec-authoring agent must:

- read the next-phase architecture docs
- read `specs/next_phase_spec_sequence.json`
- inspect repo reality
- create exactly one focused spec JSON
- append a progress entry at EOF
- not implement runtime code
- not modify database models or migrations
- not modify tests
- end with `SPEC_DONE`

## Planning

Run:

```bash
./scripts/ralph-loop.sh plan 1
```

The planning agent must:

- read the active spec
- read the relevant architecture docs
- inspect repo reality
- refine only planning/spec/doc artifacts if needed
- avoid runtime code implementation
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
- implement the smallest safe change
- add/update tests
- run required verification
- update only completed spec items
- append progress at EOF
- end with `ITERATION_DONE`, `ALL_DONE`, or `ITERATION_BLOCKED`

## Full tests

Required verification before marking implementation complete:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

## Locked next-phase architecture references

Read these before every relevant spec-authoring, planning, or build run:

- `docs/architecture/Spec_Authoring_and_Harness_Workflow.md`
- `docs/architecture/Parent_Backend_Application_Architecture.md`
- `docs/architecture/Parent_Backend_API_Contract_Standards.md`
- `docs/architecture/Parent_Backend_Repository_Layer_Design.md`
- `docs/architecture/Parent_Backend_Service_Layer_Design.md`
- `docs/architecture/Parent_Pay_Integration_and_Projection_Strategy.md`
- `docs/architecture/Frontend_Backend_Contract_Map.md`
- `docs/architecture/Auth_Session_and_Security_Flows.md`
- `docs/architecture/Dashboard_Launcher_Billing_Aggregation_Design.md`
- `docs/architecture/Support_Announcements_and_Status_Design.md`
- `docs/architecture/Rewards_Application_and_Notification_Flows.md`
- `docs/architecture/Discord_Integration_Application_Flow.md`
- `docs/architecture/Background_Jobs_Sync_and_Event_Processing.md`
- `docs/architecture/Security_Operational_Control_Guide.md`
- `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md`

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

## Locked next-phase decisions

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

## Completed prior workstreams

The following workstreams are treated as complete and should not be re-opened unless a later spec explicitly requires corrections:

- Parent DB foundation
- Model file separation refactor
- Parent DB verification and regression hardening
- Discord identity schema correction
- Rewards DB schema
- Rewards verification/regression
- Rewards API/application-layer schema work

## Next workstream to author

The next spec to author or activate should be the profile/settings/addresses/preferences workstream from the roadmap:

```text
specs/profile_settings_addresses_preferences_api.json
```

That follow-on spec should stay focused on profile/settings/addresses/preferences behavior and preserve the roadmap order from `specs/next_phase_spec_sequence.json`.

## Progress rule

Every non-blocked run that changes files must append a progress entry to the absolute end of:

```text
progress/progress.txt
```

The newest progress entry must be the final content in the file.
