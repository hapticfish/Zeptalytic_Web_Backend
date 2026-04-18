# Parent Backend Service Layer Design

## Purpose

Define the business/application service conventions for the Zeptalytic Web Backend.

Services own business logic, orchestration, validation, transaction boundaries, and integration coordination.

## Service organization

Organize services by business capability.

Recommended services:

- `AuthService`
- `AccountService`
- `ProfileService`
- `SettingsService`
- `AddressService`
- `CommunicationPreferenceService`
- `SupportService`
- `AnnouncementService`
- `ServiceStatusService`
- `DashboardService`
- `LauncherService`
- `BillingSummaryService`
- `RewardsService`
- `ObjectiveService`
- `BadgeService`
- `DiscordIntegrationService`
- `PayProjectionService`

## Dependency direction

Routers call services.

Services call repositories and integration clients.

Repositories do not call services.

Integration clients do not call services.

Workers may call services or specialized sync/application services.

Avoid services calling many peer services unless orchestration is explicit and controlled. For cross-domain operations, prefer a small application/orchestration service.

## Transaction ownership

Services should own transaction boundaries for multi-step application operations.

Examples:

- signup
- address update and primary address selection
- support ticket creation with attachment metadata
- reward event ingestion
- projection sync/upsert
- objective completion processing

## Policy enforcement

Services should enforce:

- account lifecycle rules
- email verification rules
- role authorization decisions passed from dependencies/context
- parent-owned status transitions
- safe fallback behavior
- product access decisions
- notification viewed/unviewed behavior
- support ticket creation rules
- reward/objective/badge state changes

Services must not enforce commercial payment truth.

## Commercial boundary

The parent service layer may initiate Pay actions but must not duplicate Pay rules.

Allowed:

- request checkout session/initiation from Pay
- request subscription change initiation from Pay
- request cancellation/pause/restart initiation from Pay
- request live payment method/transaction summary from Pay
- upsert Pay-derived projections from Pay responses
- present Pay-derived data safely to frontend

Not allowed:

- decide whether a payment succeeded
- calculate authoritative amount due
- modify subscription truth locally
- store raw card/payment details
- process Stripe/Coinbase webhooks in parent
- infer entitlement truth independently of Pay

## Read model services

Use read-model/aggregation services for page-shaped data:

- `DashboardService`
- `LauncherService`
- `BillingSummaryService`
- `RewardsPresentationService` if needed

These services may compose multiple repositories and integration clients into a normalized frontend payload.

## Dashboard service responsibilities

Dashboard service should assemble:

- product launcher card summaries
- billing snapshot
- milestone/progress summary
- service status summary by product
- notifications/news/version-update feed

## Launcher service responsibilities

Launcher service should determine launch state per product from:

- entitlement summaries
- product access/provisioning state
- account status
- email verification status
- product availability/status
- Pay availability where needed

If entitlement is ON but provisioning is incomplete, return a blocked/pending state with a frontend-safe message.

## Billing summary service responsibilities

Billing summary service should assemble:

- subscription cards per product
- current plan/level
- price/current charge
- billing cycle
- next billing date
- status
- last four/payment method summary
- transaction history
- payment method list
- billing address list from parent

Transaction history and payment method summaries should be fetched live from Pay where available, with mirrored projection support for dashboard and fallback display.

## Rewards service responsibilities

Rewards services should define and process:

- write/event triggers
- progress computation
- milestone detection
- viewed/unviewed notification state
- objective completion ordering
- badge unlock rules
- reward grants
- reward events
- notification presentation state

Frontend reward APIs should be read-only except for presentation actions such as marking notifications viewed.

Reward writes should originate from:

- backend jobs
- product events
- admin/internal operations
- Pay-derived events after criteria are met
- referral qualification events

Do not award reversible points prematurely. Award after criteria are met.

## Background-job readiness

Design services so they can later be called from workers.

Likely worker-driven flows:

- Pay projection sync
- reward event ingestion
- email sending
- attachment processing
- announcement publishing
- Discord sync
- stale session cleanup
- product-originated reward/event ingestion

## Error behavior

Services should raise domain-specific exceptions that routers translate into the standard error shape.

Avoid leaking lower-level database or integration exceptions directly to API clients.

## Testing expectation

Each service slice should have tests around:

- normal behavior
- authorization/account-status behavior
- error handling
- Pay unavailable handling where relevant
- transaction rollback behavior for multi-step writes
- no duplication of Pay commercial truth
