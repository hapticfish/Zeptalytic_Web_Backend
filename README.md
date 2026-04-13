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
