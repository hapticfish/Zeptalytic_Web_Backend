# Zeptalytic Web Backend Implementation Plan

Active spec: specs/model_file_separation_refactor.json

## Current workstream
Refactor the parent DB model layout into sensible per-table files and harden the DB verification test layer before moving on to parent backend route work.

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

### B. Active workstream — model file separation refactor
- Immediate next build target: `mdl-040`
- Current repo reality to plan against: the identity/auth/account slice and the profile/settings/address/integration slice now live in per-file model modules, while the remaining support/content/status and billing projection tables still live in `app/db/models/auth.py`; registration continues to flow through `app/db/models/__init__.py` -> `app/db/bootstrap.py` -> `alembic/env.py`.
- [x] `mdl-001` inventory current model layout and confirm exact files/tables to split
- [x] `mdl-010` lock vocabulary decision record into repo docs
- [x] `mdl-020` split identity/auth/account models into sensible per-file modules
- [x] `mdl-030` split profile/settings/address/integration models into sensible per-file modules
- [ ] `mdl-040` split support/content/status models into sensible per-file modules
- [ ] `mdl-050` split billing/read-model projection models into sensible per-file modules
- [ ] `mdl-060` align imports/metadata registration/Alembic discovery after split
- [ ] `mdl-070` add structural regression tests to prevent future model-dump regressions
- [ ] `mdl-999` run the authoritative docker test suite and mark this spec complete only when green

### C. Next queued workstream — DB verification and regression hardening
Queued next spec after B is green:
- `specs/parent_db_verification_and_regression.json`

### D. Later workstreams
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
