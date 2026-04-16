# Zeptalytic Web Backend Implementation Plan

Active spec: specs/discord_identity_schema_correction.json

## Current workstream
Correct the Discord identity schema placement, then build the rewards/objectives/badges workstream as a separate sequence: domain DB schema, verification/regression hardening, and API/application layer.

## Locked architecture references
Read these before every planning/build run:
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
- `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` is the canonical source for parent-site vocabulary, enum values, and status names.

## Locked decisions
- Current active Discord linkage belongs in `profiles`:
  - `discord_user_id` (internal only)
  - `discord_username`
  - `discord_integration_status`
- Discord historical connection state should be preserved in a separate history table.
- One parent account may have at most one currently connected Discord account.
- Rewards use one global points balance per user.
- Tiers are `Bronze`, `Silver`, `Gold`, `Platinum`, `Plus`.
- Each tier spans 1000 points; every 100 points is a milestone; every 1000 points grants a larger tier reward.
- Points do not expire.
- Points may be reversed in qualifying cases.
- Some objectives are repeatable.
- Milestone rewards are the only automatic modal-driven reward flow.
- Non-milestone objective completions queue notification-driven presentation on the objectives page.

## Workstreams
### A. Completed prior workstreams
- Parent DB foundation
- Model file separation refactor
- Parent DB verification and regression hardening

### B. Active workstream — Discord identity schema correction
- Active spec: `specs/discord_identity_schema_correction.json`
- Immediate next build target: `disc-030`

### C. Queued next workstream — Rewards DB schema
- Next spec after B is green:
  - `specs/rewards_domain_db_schema.json`

### D. Queued next workstream — Rewards verification / regression
- Next spec after C is green:
  - `specs/rewards_verification_and_regression.json`

### E. Queued next workstream — Rewards API / application layer
- Next spec after D is green:
  - `specs/rewards_api_application_layer.json`

### F. Later workstreams
After the rewards API layer is green:
1. parent backend route list / broader contract buildout
2. parent ↔ Pay integration contract refinement
3. dashboard / launcher / billing aggregation API buildout
4. frontend/backend contract alignment

## Command references
- Planning:
  - `./scripts/ralph-loop.sh plan 1`
- One build iteration:
  - `./scripts/ralph-loop.sh build 1`
- Full tests:
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
