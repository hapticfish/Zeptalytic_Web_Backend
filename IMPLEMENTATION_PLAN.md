# Zeptalytic Web Backend Implementation Plan

Active spec: specs/parent_db_verification_and_regression.json

## Current workstream
Harden the parent DB verification and regression layer now that the per-table model split is complete, then move on to parent backend route work.

## Locked architecture references
Read these before every planning/build run:
- `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
- `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
- `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`
- `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md`

The vocabulary decision record is the canonical source for parent-site enums and status values.

## Locked decisions
- Parent backend owns auth/settings/addresses/support/rewards/announcements/testimonials/dashboard aggregation.
- Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, and risk.
- Stripe.js / Elements + SetupIntents is the intended payment-method update path.
- Model/table definitions must not be dumped into a single generic file.

## Workstreams
### A. Completed prior workstream
- Parent DB foundation spec completed in the previous run sequence.
- Model file separation refactor spec completed.

### B. Active workstream — DB verification and regression hardening
- Immediate next build target: `dbv-999`
- Active spec: `specs/parent_db_verification_and_regression.json`

### C. Later workstreams
After the DB verification workstream is green:
1. parent backend route list and contract buildout
2. Pay integration contract
3. promo-code design in Pay
4. route/service/repository implementation by domain

## Command references
- Planning:
  - `./scripts/ralph-loop.sh plan 1`
- One build iteration:
  - `./scripts/ralph-loop.sh build 1`
- Full tests:
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
