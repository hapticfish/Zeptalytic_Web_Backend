# Parent Backend Repository Layer Design

## Purpose

Define data-access conventions for the Zeptalytic Web Backend.

The repository layer must keep persistence concerns separate from service/business logic.

## Repository organization

Prefer one repository per aggregate/domain rather than one repository per table, except when a table is large or important enough to need its own focused repository.

Recommended repositories:

- `AccountsRepository`
- `ProfilesRepository`
- `AddressesRepository`
- `CommunicationPreferencesRepository`
- `SupportRepository`
- `AnnouncementsRepository`
- `ServiceStatusRepository`
- `RewardsRepository`
- `ObjectivesRepository`
- `BadgesRepository`
- `ProductAccessRepository`
- `BillingProjectionsRepository`
- `DiscordIntegrationsRepository`
- `AuthSessionsRepository`
- `SecuritySettingsRepository`

## Persistence-only rule

Repositories should be persistence-oriented.

They may include:

- targeted query methods
- existence checks
- insert/update helpers
- relationship loading strategies
- projection upsert helpers
- pagination helpers

They should not include:

- payment/commercial policy
- UI composition
- cross-domain orchestration
- role/permission decisions
- email sending
- external HTTP calls
- reward business decisions beyond simple state persistence

Those belong in services/integrations/workers.

## Return types

Repositories may return ORM objects internally to services when that is the existing project convention and helps with transactions.

Routers must not return ORM objects directly. Services or schemas must convert to safe response DTOs.

## Transaction boundary

Preferred convention:

- service layer owns transaction boundary for multi-step operations
- repository methods assume an active session
- repository methods should not independently commit unless explicitly documented
- use one transaction per user action where practical

Examples requiring service-owned transactions:

- signup creates account, profile, Pay identity link record, preferences, and maybe verification token
- support ticket creation inserts ticket plus attachments metadata
- address update plus set-primary behavior
- reward event ingestion updates progress and grant records
- projection sync upserts multiple Pay-derived rows

## Naming conventions

Repository methods should be specific and readable.

Examples:

```python
get_by_id(account_id)
get_by_email(email)
get_profile_for_account(account_id)
list_addresses_for_account(account_id)
set_primary_address(account_id, address_id, address_type)
upsert_subscription_summary(...)
list_active_product_access_states(account_id)
```

Avoid vague names such as:

```python
handle_data()
process_user()
do_query()
```

## Timestamp handling

Use timezone-aware UTC timestamps.

Do not mix naive datetimes with aware datetimes.

Created/updated timestamps should be set consistently by models or repository/service helpers.

## Soft delete / lifecycle handling

Prefer lifecycle/status fields over hard delete for important business records.

Examples:

- accounts: active, pending_verification, suspended, closed
- support tickets: open, in_progress, waiting_on_customer, resolved, closed
- product access: none, provision_pending, active, suspended
- integration state: connected, disconnected, pending, error where applicable

Hard delete may be appropriate for non-sensitive temporary data only, such as expired tokens, if project conventions allow it.

## Optimistic locking

Use optimistic locking/version fields only where concurrent edits are likely and meaningful.

Likely candidates:

- support ticket status/assignment
- account settings
- address primary selection
- projection upsert conflict handling
- reward progress updates

Do not add versioning everywhere unless needed.

## Status filtering

Repository list methods should be explicit about default filters.

Examples:

- `list_active_addresses_for_account`
- `list_visible_announcements`
- `list_user_support_tickets`
- `list_current_entitlement_summaries`
- `list_unviewed_reward_notifications`

Avoid methods that hide deleted/inactive records without naming that behavior.

## Projection repositories

Projection tables should have separate repository methods from parent-owned source tables.

Pay-derived projection rows are not commercial truth. They are cached/aggregated copies for frontend and parent-domain decisions.

Projection repositories should support:

- upsert by account/product/provider key
- fetch current summaries for UI
- mark stale/unavailable when sync fails if such field exists
- prevent accidental editing from normal user flows

## Immediate repository domains

Build repositories for these immediately:

- accounts/profiles/settings
- addresses
- communication preferences
- support
- announcements
- service status
- rewards/objectives/badges
- product access
- subscription/payment/entitlement/payment-method summaries
- Discord integration state/history
- auth sessions/security settings

## Attachment metadata

Support attachment metadata should be stored in the DB.

Actual attachment file storage should use a safe external storage strategy, such as object storage or local dev storage abstracted behind a storage service. Do not store raw file blobs directly in ordinary relational rows unless explicitly approved.
