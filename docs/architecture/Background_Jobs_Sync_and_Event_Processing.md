# Background Jobs, Sync, and Event Processing

## Purpose

Define background processing expectations for the parent backend.

## Scope

Background jobs are in scope for the next backend phase, but an outbox/event bus architecture does not need to be fully implemented immediately unless a spec requires it.

## Likely background jobs

### Pay projection sync

Keeps parent-side projection tables aligned with Pay for:

- subscription summaries
- payment summaries
- entitlement summaries
- payment method summaries
- product access states

### Email sending

Handles:

- email verification
- password reset
- support ticket confirmation
- security notifications
- product/account notifications
- newsletter integration later if applicable

### Support attachment processing

Handles:

- file validation
- storage processing
- malware-scan hook/future placeholder
- metadata finalization

### Announcement publishing

Handles:

- scheduled publish/unpublish
- notification-feed availability
- product-scoped announcements

### Discord sync

Handles:

- optional refresh/check of Discord integration state
- cleanup/repair if OAuth linkage changes

### Stale session cleanup

Handles:

- expired session removal
- revoked session cleanup
- stale device/session metadata

### Reward event processing

Handles:

- product-originated events
- objective progress updates
- milestone detection
- badge/reward grants
- notification presentation records

## Design principles

- Services should be callable by both routers and workers where safe.
- Jobs should be idempotent.
- Jobs should record enough status for retry/debugging.
- Jobs should not silently duplicate reward grants or projection rows.
- Workers should not own commercial truth; Pay still owns payment/subscription/entitlement truth.

## Deferred event/outbox pattern

A formal outbox/event processing architecture may be deferred, but docs/specs should avoid choices that make it hard to add later.

Future-ready design:

- internal event table or queue
- event type
- source system
- idempotency key
- payload
- status
- attempts
- last error
- processed_at

## Product event ingestion

Future product apps should be able to emit events to parent for:

- reward progress
- objective completion
- product usage milestones
- onboarding completion
- activity summaries

These events must be authenticated and validated.

Do not let product apps directly mutate points/badges/rewards tables without parent validation.
