# Zeptalytic Web Backend

Parent-site backend for the Zeptalytic ecosystem.

This service is the browser-facing API and parent-domain backend. It owns:
- authentication and account security
- profiles, settings, integrations, and addresses
- support tickets and attachments
- rewards, announcements, and testimonial delivery
- dashboard, launcher, and billing aggregation APIs
- Pay-derived read models for website display

It does **not** own authoritative billing truth. The separate Pay service remains the source of truth for:
- pricing
- checkout / provider payment orchestration
- orders, payments, refunds
- subscriptions and entitlements
- disputes, risk, webhooks, and commercial finality

## Repository layout

- `app/` runtime application package
- `docs/architecture/` durable architecture and ownership references
- `prompt/` harness prompt files for Ralph/Codex runs
- `progress/` append-only iteration log and harness outputs
- `scripts/` developer and harness scripts
- `specs/` active and future implementation specs
- `tests/` unit and integration tests
- `alembic/` migration environment and versions

## Initial run order

1. Review `docs/architecture/` documents.
2. Review `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, and `PROMPT.md`.
3. Run a planning iteration first:
   - `bash scripts/ralph-loop.sh plan 1`
4. Then run a single build iteration:
   - `bash scripts/ralph-loop.sh build 1`

## Current active workstream

The first workstream is parent DB foundation. See:
- `specs/parent_db_foundation.json`
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`

## Current repo reality

- Runtime entrypoint is `app/main.py` with a single `/health` route.
- Config currently lives in `app/core/config.py`; there is no `app/settings.py`.
- DB bootstrap currently consists of `app/db/base.py`, `app/db/session.py`, and `alembic/env.py`.
- `alembic/env.py` targets `Base.metadata`, but `app/db/models/__init__.py` does not import any models yet and `alembic/versions/` is empty.
- Test coverage currently consists of `tests/unit/test_health.py`; there are no DB or migration tests yet.
- Compose topology now exists for the documented baseline commands:
  - `docker compose up --build api`
  - `docker compose run --rm migrate`
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`

## Docker workflow

- `docker compose up --build api` starts Postgres and the FastAPI app on port `8000`.
- `docker compose run --rm migrate` runs Alembic against the compose Postgres service.
- `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test` runs the authoritative test suite path for this repo.
