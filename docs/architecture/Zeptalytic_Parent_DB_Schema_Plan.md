# Zeptalytic Parent DB Schema Plan

## Purpose
This document is the build reference for the first Zeptalytic parent-site database workstream. It converts the control docs into a concrete parent DB plan that Ralph/Codex runs can implement safely without duplicating Pay-service billing truth.

This document is intentionally scoped to the **parent site backend + parent DB**. It does **not** redefine the Pay service schema.

## Scope rules
1. Pay remains the source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk flags, and provider webhooks.
2. The parent DB owns identity, auth/security state, profiles/settings, addresses, support, website content/status, and Pay-derived read models.
3. The parent DB may store safe payment-method summaries for display **only if needed**. It must not store raw card data or CVC.
4. Stripe card capture is handled through Stripe.js / Elements + SetupIntents. Coinbase is treated as a checkout/payment rail, not a saved-card subsystem.
5. This first DB workstream should focus on **launch-critical parent-owned tables** first.

## Current repo reality audit (2026-04-13)
- Runtime entrypoint: `app/main.py` creates the FastAPI app directly and exposes only `/health`.
- Config surface: `app/core/config.py` is the active settings module; there is no `app/settings.py` in this repo.
- DB bootstrap: `app/db/base.py` defines `Base`, `app/db/session.py` defines `engine` and `SessionLocal`, and `alembic/env.py` points `target_metadata` at `Base.metadata`.
- Model registration: `app/db/bootstrap.py` is the shared metadata-loading path and calls `app/db/models/__init__.py` so Alembic and future schema work use one model-registration surface.
- Migration path: `alembic/versions/` exists but is empty.
- Container topology: `docker-compose.yml` and `docker-compose.test.yml` now exist and define the documented `api`, `migrate`, and `test` services used by the authoritative docker commands.
- Test harness: concrete tests currently consist of `tests/unit/test_health.py` and `tests/unit/test_config.py`; there are still no DB bootstrap, migration, or repository tests yet.

Planning implication:
- the next implementation slice should add the first concrete parent-owned tables and Alembic revisions on top of the now-aligned bootstrap path.

## Launch-critical table groups for the first workstream

### Group A — Identity and auth
These are required before real authenticated pages can work.

#### `accounts`
Core account table.
- `id` UUID primary key
- `username` unique, immutable after creation
- `email` unique
- `password_hash`
- `status`
- `role`
- `created_at`
- `updated_at`
- `last_login_at`
- `email_verified_at` nullable

Indexes / constraints:
- unique on `username`
- unique on `email`
- index on `status`

#### `auth_sessions`
Session/refresh-token persistence if the site uses session-backed auth.
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `session_token_hash`
- `created_at`
- `expires_at`
- `revoked_at` nullable
- `ip_address` nullable
- `user_agent` nullable

Indexes:
- index on `account_id`
- index on `expires_at`

#### `email_verification_tokens`
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `token_hash`
- `expires_at`
- `used_at` nullable
- `created_at`

#### `password_reset_tokens`
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `token_hash`
- `expires_at`
- `used_at` nullable
- `created_at`

#### `account_security_settings`
Supports settings/security UI.
- `account_id` PK/FK -> `accounts.id`
- `two_factor_enabled` boolean
- `two_factor_method` nullable text
- `recovery_methods_available_count` integer default 0
- `recovery_codes_generated_at` nullable timestamptz
- `updated_at`

#### `mfa_recovery_codes`
Only needed if 2FA launches in this wave. Can be deferred if 2FA UI remains display-only.
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `code_hash`
- `used_at` nullable
- `created_at`

#### `auth_events`
Audit/security events.
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `event_type`
- `ip_address` nullable
- `user_agent` nullable
- `created_at`
- `metadata` JSONB default `{}`

### Group B — Profile and settings

#### `profiles`
- `account_id` PK/FK -> `accounts.id`
- `display_name` nullable
- `phone` nullable
- `timezone` nullable
- `profile_image_url` nullable
- `discord_username` nullable
- `created_at`
- `updated_at`

#### `profile_preferences`
- `account_id` PK/FK -> `accounts.id`
- `preferred_language` nullable
- `created_at`
- `updated_at`

#### `communication_preferences`
- `account_id` PK/FK -> `accounts.id`
- `marketing_emails_enabled` boolean default false
- `product_updates_enabled` boolean default true
- `announcement_emails_enabled` boolean default true
- `created_at`
- `updated_at`

#### `oauth_connections`
For Discord and future integrations.
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `provider`
- `provider_user_id`
- `provider_username` nullable
- `status`
- `connected_at`
- `disconnected_at` nullable
- `metadata` JSONB default `{}`

Constraints / indexes:
- unique on (`provider`, `provider_user_id`)
- index on `account_id`

### Group C — Addresses

#### `addresses`
Parent-owned address table for international support.
- `id` UUID primary key
- `account_id` FK -> `accounts.id`
- `address_type` text (`billing` initially; extensible later)
- `label` nullable
- `full_name`
- `line1`
- `line2` nullable
- `city_or_locality`
- `state_or_region` nullable
- `postal_code` nullable
- `country_code`
- `country_name` nullable
- `formatted_address` nullable
- `is_primary` boolean default false
- `created_at`
- `updated_at`

Indexes:
- index on `account_id`
- index on (`account_id`, `address_type`)

### Group D — Support

#### `support_tickets`
- `id` UUID primary key
- `ticket_code` unique
- `account_id` FK -> `accounts.id`
- `request_type`
- `related_product_code` nullable
- `priority`
- `subject`
- `description`
- `status`
- `estimated_response_sla_label` nullable
- `created_at`
- `updated_at`

#### `support_ticket_messages`
- `id` UUID primary key
- `ticket_id` FK -> `support_tickets.id`
- `account_id` nullable FK -> `accounts.id`
- `author_type`
- `message_body`
- `is_internal_note` boolean default false
- `created_at`

#### `support_ticket_attachments`
- `id` UUID primary key
- `ticket_id` FK -> `support_tickets.id`
- `uploaded_by_account_id` FK -> `accounts.id`
- `storage_key`
- `original_filename`
- `content_type`
- `file_size_bytes`
- `scan_status`
- `created_at`

Notes:
- file contents should live in object storage or an equivalent storage layer, not in Postgres
- this table stores metadata only

### Group E — Website status / announcements

#### `announcements`
- `id` UUID primary key
- `scope` text
- `product_code` nullable
- `title`
- `body`
- `severity`
- `published_at`
- `expires_at` nullable
- `created_at`
- `updated_at`

#### `service_statuses`
- `id` UUID primary key
- `product_code`
- `status`
- `message` nullable
- `updated_at`

### Group F — Pay-derived read models
These are parent-side projections / summaries only. They are not commercial truth.

#### `subscription_summaries`
- `id` UUID primary key
- `account_id`
- `product_code`
- `plan_code`
- `billing_interval`
- `normalized_status`
- `provider_status_raw`
- `current_period_start_at` nullable
- `current_period_end_at` nullable
- `cancel_at_period_end` boolean default false
- `canceled_at` nullable
- `next_billing_at` nullable
- `last_synced_at`

#### `entitlement_summaries`
- `id` UUID primary key
- `account_id`
- `product_code`
- `plan_code`
- `status`
- `starts_at` nullable
- `ends_at` nullable
- `metadata` JSONB default `{}`
- `last_synced_at`

#### `product_access_states`
- `id` UUID primary key
- `account_id`
- `product_code`
- `access_state`
- `launch_url` nullable
- `disabled_reason` nullable
- `external_account_reference` nullable
- `updated_at`

#### `payment_summaries`
- `id` UUID primary key
- `account_id`
- `product_code` nullable
- `payment_rail`
- `normalized_status`
- `provider_status_raw` nullable
- `amount_cents`
- `currency`
- `paid_at` nullable
- `provider_payment_reference` nullable
- `updated_at`

#### `payment_method_summaries` (optional in first DB wave)
Use only if the first backend wave benefits from a cached display table.
- `id` UUID primary key
- `account_id`
- `provider`
- `provider_customer_id`
- `provider_payment_method_id`
- `brand`
- `last4`
- `exp_month`
- `exp_year`
- `billing_name` nullable
- `billing_country` nullable
- `is_default` boolean default false
- `status`
- `last_synced_at`

Notes:
- safe summary cache only
- no raw card number or CVC

## Deferred / later-phase tables
These are parent-owned but can follow after the initial DB foundation if needed:
- testimonial cache
- knowledge-base content/search tables
- newsletter tables
- rewards/objectives/badges tables if not included in the first launch slice
- plan/bundle marketing metadata tables if kept as frontend config initially

## Recommended migration order
1. container topology / authoritative docker path (`docker-compose.yml`, `docker-compose.test.yml`, `api`, `migrate`, `test`)
2. base DB bootstrap / common model registration / Alembic wiring cleanup if needed
3. `accounts`, `auth_sessions`, `email_verification_tokens`, `password_reset_tokens`
4. `account_security_settings`, optional `mfa_recovery_codes`, `auth_events`
5. `profiles`
6. `profile_preferences`, `communication_preferences`, `oauth_connections`
7. `addresses`
8. `support_tickets`, `support_ticket_messages`
9. `support_ticket_attachments`
10. `announcements`, `service_statuses`
11. `subscription_summaries`, `entitlement_summaries`
12. `product_access_states`, `payment_summaries`, optional `payment_method_summaries`
13. later-phase content/rewards tables

## Constraints and implementation notes for the first spec
- Verify exact table/column names before queries are written.
- Use UUID primary keys consistently.
- Prefer append-only event/audit tables where they improve traceability.
- Keep settings/auth/security tables separated rather than overloading `accounts`.
- Keep parent DB abstractions product-agnostic where possible (`product_code`, not hard-coded per-product columns).
- Keep address schema international, not US-only.
- Avoid premature reward/testimonial/newsletter coupling unless the active spec explicitly includes them.
- Every DB slice should come with:
  - SQLAlchemy models
  - Alembic migration
  - model registration/import so Alembic sees metadata
  - focused tests if the repo already has DB/integration test patterns
  - progress log update

## Acceptance rules for the first DB workstream
A DB slice is not complete unless:
1. the spec item is implemented narrowly
2. migrations apply cleanly in docker
3. focused tests pass
4. authoritative docker test suite passes
5. `progress/progress.txt` is updated at EOF
6. the spec item is marked complete with timestamp and `completed_by="codex"`
