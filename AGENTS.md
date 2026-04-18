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

This service does not own commercial payment truth.

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

## Locked architecture boundaries

- Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, Stripe, and Coinbase Commerce.
- Parent backend owns auth/settings/addresses/support/rewards/announcements/testimonials/dashboard aggregation.
- Parent may initiate checkout, plan change, cancellation, pause, restart, or payment-method-management flows, but Pay executes commercial behavior.
- Stripe.js / Elements + SetupIntents is the intended payment-method update path.
- Parent must not store full card numbers, CVV/CVC, raw payment credentials, private wallet keys, or sensitive provider secrets in normal app tables.
- Discord current active linkage is modeled on `profiles`, with preserved historical connection state tracked separately.
- Discord linkage does not affect rewards or product access in phase 1.
- The docs under `docs/architecture/` are durable reference material; do not contradict them without updating the relevant decision record first.

## Required rehydrate behavior every run

Read these first:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. Determine the active spec from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the active spec file when the run mode is `plan` or `build`
7. Read `specs/next_phase_spec_sequence.json` when the run mode is `spec_author`, `plan`, or `build`
8. Rehydrate the architecture docs named in `IMPLEMENTATION_PLAN.md`
9. Run `git status`
10. Run `git log -5 --oneline`

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

Read these when relevant to application-layer, API, service, repository, integration, dashboard, billing, support, rewards, Discord, worker, security, or frontend-contract work:

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

The spec-authoring run must not implement runtime application code.

The spec-authoring run must not modify database models, Alembic migrations, routers, services, repositories, schemas, workers, integrations, or tests unless explicitly instructed.

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

Build mode must end with one of:

```text
ITERATION_DONE
ALL_DONE
ITERATION_BLOCKED
```

## Search-before-edit rule

Before changing code, search the repo for:

- existing router patterns
- existing service patterns
- existing repository patterns
- existing model patterns
- existing schema/DTO patterns
- existing tests that already cover the same surface
- existing migration/bootstrap conventions
- existing integration/client conventions

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

## Next-phase workstream strategy

Use `specs/next_phase_spec_sequence.json` as the roadmap.

Recommended order:

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

Do not create one giant backend implementation spec.

Use a small foundation spec first, then prefer vertical capability specs.

## Next-phase non-goals unless explicitly scoped

Do not implement these unless the active spec explicitly requires them:

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