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
- DB bootstrap: `app/db/base.py` defines `Base`, `app/db/session.py` defines `engine` and `SessionLocal`, `app/db/bootstrap.py` is the shared metadata-loading surface, and `alembic/env.py` imports `target_metadata` from that bootstrap path.
- Model registration: `app/db/bootstrap.py` is the shared metadata-loading path and calls `app/db/models/__init__.py`, which now imports the split per-table model modules directly for Alembic/metadata discovery.
- Current registered ORM surface: `app/db/models/` now contains one concrete table model per file for the 22 parent tables plus a backward-compatible `app/db/models/auth.py` re-export shim that is no longer part of the registry path.
- Migration path: `alembic/versions/` now contains the parent DB foundation revision chain through `20260413_2128_pdb075_access_payment_summary_tables.py`.
- Container topology: `docker-compose.yml` and `docker-compose.test.yml` now exist and define the documented `api`, `migrate`, and `test` services used by the authoritative docker commands.
- Test harness: concrete tests include `tests/unit/test_db_bootstrap.py`, `tests/unit/test_auth_models.py`, `tests/unit/test_model_module_layout.py`, `tests/unit/test_model_metadata_registration.py`, and `tests/unit/test_domain_vocabulary_decision_record.py`; DB coverage is still mostly unit-level and SQLite-backed, and `tests/integration/` has no concrete DB tests yet.

Planning implication:
- the parent DB foundation and model-file-separation workstreams are complete; the active workstream is now `specs/parent_db_verification_and_regression.json`.
- the next implementation slice should be `dbv-001`, starting with a durable gap inventory for metadata, migration, vocabulary, Postgres-backed CRUD/constraint coverage, and compose-topology verification.

## DB verification surface audit for `dbv-001` (2026-04-13)
- Existing DB verification is concentrated in unit tests:
  - `tests/unit/test_auth_models.py` performs broad schema, relationship, default, and constraint checks plus SQLite-backed round trips across all 22 parent tables.
  - `tests/unit/test_db_bootstrap.py` and `tests/unit/test_model_metadata_registration.py` verify bootstrap/model registration and the expected table inventory.
  - `tests/unit/test_domain_vocabulary_decision_record.py` guards that the decision record remains explicitly wired into repo control docs, but it does not yet verify model defaults/value vocabularies against the record.
- Current gaps relative to the active verification spec:
  - no concrete `tests/integration/` coverage against the migrated Postgres schema
  - no explicit migration smoke/regression test beyond the compose `migrate` service succeeding during full-suite runs
  - no dedicated model-vocabulary regression tests comparing implemented defaults/value fields against `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md`
  - no explicit topology contract test covering `docker-compose.test.yml` service names, dependency ordering, and `pytest -q` execution

Historical note:
- The `mdl-001` model split inventory below remains as a reference artifact from the completed prior workstream.

## Model split inventory for `mdl-001` (2026-04-13)

### Current overloaded module state
- `app/db/models/auth.py` is the only concrete ORM module and currently defines all 22 table models:
  - `Account` -> `accounts`
  - `Announcement` -> `announcements`
  - `ServiceStatus` -> `service_statuses`
  - `SubscriptionSummary` -> `subscription_summaries`
  - `EntitlementSummary` -> `entitlement_summaries`
  - `ProductAccessState` -> `product_access_states`
  - `PaymentSummary` -> `payment_summaries`
  - `PaymentMethodSummary` -> `payment_method_summaries`
  - `AuthSession` -> `auth_sessions`
  - `EmailVerificationToken` -> `email_verification_tokens`
  - `PasswordResetToken` -> `password_reset_tokens`
  - `AccountSecuritySettings` -> `account_security_settings`
  - `MfaRecoveryCode` -> `mfa_recovery_codes`
  - `AuthEvent` -> `auth_events`
  - `Profile` -> `profiles`
  - `ProfilePreference` -> `profile_preferences`
  - `CommunicationPreference` -> `communication_preferences`
  - `OAuthConnection` -> `oauth_connections`
  - `Address` -> `addresses`
  - `SupportTicket` -> `support_tickets`
  - `SupportTicketMessage` -> `support_ticket_messages`
  - `SupportTicketAttachment` -> `support_ticket_attachments`

### Current registration and discovery wiring
- `app/db/models/__init__.py` exposes `import_models()` and currently imports only `app.db.models.auth`.
- `app/db/bootstrap.py` calls `import_models()` inside `get_target_metadata()` and exports `target_metadata = get_target_metadata()`.
- `alembic/env.py` imports `target_metadata` from `app.db.bootstrap`, so Alembic discovery depends on `app/db/models/__init__.py` remaining the central import-registration surface.
- `tests/unit/test_auth_models.py` currently imports every concrete model from `app.db.models.auth`, so the later split will need import/test realignment.
- `tests/unit/test_db_bootstrap.py` currently guards the shared bootstrap path and should remain valid after the split.

### Exact target file map for the split
| Current source | Model | Table | Target file |
| --- | --- | --- | --- |
| `app/db/models/auth.py` | `Account` | `accounts` | `app/db/models/accounts.py` |
| `app/db/models/auth.py` | `AuthSession` | `auth_sessions` | `app/db/models/auth_sessions.py` |
| `app/db/models/auth.py` | `EmailVerificationToken` | `email_verification_tokens` | `app/db/models/email_verification_tokens.py` |
| `app/db/models/auth.py` | `PasswordResetToken` | `password_reset_tokens` | `app/db/models/password_reset_tokens.py` |
| `app/db/models/auth.py` | `AccountSecuritySettings` | `account_security_settings` | `app/db/models/account_security_settings.py` |
| `app/db/models/auth.py` | `MfaRecoveryCode` | `mfa_recovery_codes` | `app/db/models/mfa_recovery_codes.py` |
| `app/db/models/auth.py` | `AuthEvent` | `auth_events` | `app/db/models/auth_events.py` |
| `app/db/models/auth.py` | `Profile` | `profiles` | `app/db/models/profiles.py` |
| `app/db/models/auth.py` | `ProfilePreference` | `profile_preferences` | `app/db/models/profile_preferences.py` |
| `app/db/models/auth.py` | `CommunicationPreference` | `communication_preferences` | `app/db/models/communication_preferences.py` |
| `app/db/models/auth.py` | `OAuthConnection` | `oauth_connections` | `app/db/models/oauth_connections.py` |
| `app/db/models/auth.py` | `Address` | `addresses` | `app/db/models/addresses.py` |
| `app/db/models/auth.py` | `SupportTicket` | `support_tickets` | `app/db/models/support_tickets.py` |
| `app/db/models/auth.py` | `SupportTicketMessage` | `support_ticket_messages` | `app/db/models/support_ticket_messages.py` |
| `app/db/models/auth.py` | `SupportTicketAttachment` | `support_ticket_attachments` | `app/db/models/support_ticket_attachments.py` |
| `app/db/models/auth.py` | `Announcement` | `announcements` | `app/db/models/announcements.py` |
| `app/db/models/auth.py` | `ServiceStatus` | `service_statuses` | `app/db/models/service_statuses.py` |
| `app/db/models/auth.py` | `SubscriptionSummary` | `subscription_summaries` | `app/db/models/subscription_summaries.py` |
| `app/db/models/auth.py` | `EntitlementSummary` | `entitlement_summaries` | `app/db/models/entitlement_summaries.py` |
| `app/db/models/auth.py` | `ProductAccessState` | `product_access_states` | `app/db/models/product_access_states.py` |
| `app/db/models/auth.py` | `PaymentSummary` | `payment_summaries` | `app/db/models/payment_summaries.py` |
| `app/db/models/auth.py` | `PaymentMethodSummary` | `payment_method_summaries` | `app/db/models/payment_method_summaries.py` |

### Known split risks to address in later items
- `Account` is the relationship anchor for most other tables, so later per-file moves will need careful import ordering or string-based relationships to avoid circular imports.
- `tests/unit/test_auth_models.py` is intentionally broad and will need staged updates as models move out of `app.db.models.auth`.
- `app/db/models/__init__.py` must remain the single registration hub while files are split so `app/db/bootstrap.py` and `alembic/env.py` do not change behavior mid-refactor.

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
