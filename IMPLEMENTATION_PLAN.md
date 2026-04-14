# Zeptalytic Website Backend / Parent Site Implementation Plan

Active spec: specs/parent_db_foundation.json

## Purpose
This plan controls the first parent-site backend workstream using the same Ralph/Codex spec-driven pattern used in the Pay service.

This first workstream starts with the **parent DB foundation** because the parent backend, auth flows, settings flows, support flows, and Pay-derived read models all depend on stable schema ownership boundaries.

## Required reference docs for this workstream
Read before planning or building:
- `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
- `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
- `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
- `docs/architecture/Zeptalytic_Agent_Harness_Development_Strategy.md`
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`

## Locked architecture decisions for this repo
- Parent backend is the browser-facing API boundary.
- Pay is the source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, and webhook finality.
- Parent DB owns identity, auth/security state, profiles/settings, addresses, support, announcements/status, rewards/content when in scope, and Pay-derived read models.
- Stripe card handling uses Stripe.js / Elements + SetupIntents; raw card data must not pass through parent servers.
- Coinbase is a checkout/payment rail, not a Stripe-like saved-card subsystem.
- Promo code logic belongs in Pay.

## Authoritative commands (target baseline)
- Full tests:
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
- API:
  - `docker compose up --build api`
- Migrations:
  - `docker compose run --rm migrate`

Current repo reality audit on 2026-04-13:
- `docker-compose.yml` and `docker-compose.test.yml` now exist and expose the documented `api`, `migrate`, and `test` services.
- The next build slice should align shared DB bootstrap/model-registration/Alembic wiring before table-by-table schema work expands.
- Later schema items still may not claim completion unless the authoritative docker command passes for their slice.

If these differ from repo reality, a planning run must update the docs/prompt/plan files before implementation continues.

## Work order for the active spec

- [x] `pdb-001` — Discovery + repo reality audit for the parent DB workstream; confirm current DB/bootstrap/model/alembic surfaces and create/validate the parent DB schema plan doc.
- [x] `pdb-005` — Add or align container topology (`docker-compose.yml`, `docker-compose.test.yml`, `api`, `migrate`, `test`) so the repo has a real authoritative docker path.
- [x] `pdb-010` — Add or align shared DB bootstrap/model-registration/Alembic wiring for the parent site repo without implementing endpoint logic yet.
- [x] `pdb-020` — Implement `accounts`, `auth_sessions`, `email_verification_tokens`, and `password_reset_tokens` with focused tests.
- [x] `pdb-025` — Implement `account_security_settings`, optional `mfa_recovery_codes`, and `auth_events` with focused tests.
- [x] `pdb-030` — Implement `profiles` with focused tests.
- [x] `pdb-035` — Implement `profile_preferences`, `communication_preferences`, and `oauth_connections` with focused tests.
- [x] `pdb-040` — Implement international-ready parent-owned `addresses` table and migration with focused tests.
- [x] `pdb-050` — Implement `support_tickets` and `support_ticket_messages` with focused tests.
- [x] `pdb-055` — Implement `support_ticket_attachments` metadata storage with focused tests.
- [x] `pdb-060` — Implement `announcements` and `service_statuses` tables and migrations with focused tests.
- [x] `pdb-070` — Implement `subscription_summaries` and `entitlement_summaries` with focused tests.
- [x] `pdb-075` — Implement `product_access_states`, `payment_summaries`, and optional `payment_method_summaries` with focused tests.
- [x] `pdb-080` — Align README/docs with actual DB topology, migration commands, and model-registration behavior if needed.
- [ ] `pdb-999` — Final authoritative docker test suite green for the parent DB foundation workstream.

## Out-of-scope for this first spec
These are intentionally deferred to later specs unless the active spec is explicitly expanded:
- parent backend route implementation
- auth/session endpoint implementation
- settings/profile API implementation
- support API implementation
- pricing/checkout API implementation
- promo code design in Pay
- rewards/content/testimonials/newsletter implementation
- audits

## Completion rule
Do not mark an item complete unless:
1. the item was the one chosen for the iteration
2. the change is narrow and matches the controlling docs
3. migrations and focused tests for the touched slice pass
4. the authoritative docker suite passes
5. the active spec item is updated with `passes=true`, timestamp, and `completed_by="codex"`
6. `progress/progress.txt` is updated at EOF

