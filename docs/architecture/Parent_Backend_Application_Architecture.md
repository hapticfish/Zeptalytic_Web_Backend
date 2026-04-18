# Zeptalytic Parent Backend Application Architecture

## Status

Decision/control document for the post-database implementation phase.

## Purpose

The Zeptalytic Web Backend is the parent-site domain backend for the Zeptalytic ecosystem. It owns browser-facing account and product-experience behavior while integrating with the existing Zeptalytic Pay service for payment/commercial truth.

This backend is not a thin proxy only. It is a domain backend with its own state, business logic, read models, validation, authorization, and parent-owned workflows.

## Core architecture decision

The parent backend shall act as a domain backend with its own business logic and persistent state.

It shall own:

- parent account identity
- profile and settings
- addresses
- communication preferences
- support tickets and support attachment metadata
- announcements
- per-product service status
- rewards, objectives, badges, points, and progress presentation state
- product launcher aggregation
- frontend-facing billing/dashboard aggregation
- parent-side projections of Pay-owned facts
- Discord integration state/history
- parent-to-product identity handoff contracts
- parent-to-Pay integration contracts

The Pay service shall remain the source of truth for:

- pricing truth
- checkout execution
- orders
- payments
- refunds
- subscriptions
- entitlements
- disputes
- risk
- Stripe interaction
- Coinbase Commerce interaction
- payment method truth

The parent backend may initiate payment-related actions, but execution must be delegated to Pay.

## Non-negotiable boundary

The parent backend must not duplicate commercial business rules from Pay.

Examples of logic that belongs in Pay:

- calculating final payable amount
- validating payment provider state
- deciding final payment state
- deciding commercial subscription truth
- processing Stripe webhooks
- processing Coinbase Commerce webhooks
- issuing/refusing refunds as commercial truth
- determining entitlement truth from payment/subscription events
- storing or processing sensitive card/payment data

Examples of logic that belongs in parent:

- deciding how to present account state to the user
- deciding whether a launcher button should be enabled based on entitlement/provisioning summaries
- displaying a billing snapshot
- displaying masked payment method information received from Pay
- storing and managing billing/mailing addresses
- creating a support ticket
- displaying service status by product
- computing parent-owned rewards page presentation
- recording notification viewed/unviewed state
- handling parent account settings and security preferences

## High-level module boundaries

Recommended application packages:

```text
app/
  api/
    routers/
      v1/
        auth.py
        accounts.py
        profiles.py
        addresses.py
        communication_preferences.py
        support.py
        announcements.py
        service_status.py
        rewards.py
        objectives.py
        badges.py
        launcher.py
        dashboard.py
        billing.py
        integrations.py
  db/
    repositories/
      accounts.py
      profiles.py
      addresses.py
      communication_preferences.py
      support.py
      announcements.py
      service_status.py
      rewards.py
      objectives.py
      badges.py
      product_access.py
      billing_projections.py
      discord_integrations.py
  schemas/
    common.py
    auth.py
    accounts.py
    profiles.py
    addresses.py
    support.py
    announcements.py
    rewards.py
    dashboard.py
    launcher.py
    billing.py
    integrations.py
  services/
    auth_service.py
    account_service.py
    profile_service.py
    settings_service.py
    support_service.py
    announcement_service.py
    service_status_service.py
    rewards_service.py
    objective_service.py
    badge_service.py
    dashboard_service.py
    launcher_service.py
    billing_summary_service.py
    discord_integration_service.py
  integrations/
    pay_client.py
    discord_oauth_client.py
  workers/
    pay_projection_worker.py
    email_worker.py
    attachment_processing_worker.py
    session_cleanup_worker.py
    reward_event_worker.py
```

The exact filenames may vary, but agents must preserve separation of concerns.

## API shape principle

Use domain routers for most resources, plus a few UI aggregation routers where one endpoint naturally powers a major page.

Domain routers:

- `/api/v1/profiles`
- `/api/v1/addresses`
- `/api/v1/support`
- `/api/v1/rewards`
- `/api/v1/objectives`
- `/api/v1/badges`
- `/api/v1/announcements`
- `/api/v1/service-status`
- `/api/v1/integrations`

Aggregation routers:

- `/api/v1/dashboard`
- `/api/v1/launcher`
- `/api/v1/billing`

## Frontend contract principle

Frontend pages are stable enough that backend work should support the existing page structure, but payloads should be normalized enough for long-term reuse.

The backend should avoid one-off fields that only match a single temporary component name. However, it may expose page-level aggregation endpoints where it reduces frontend complexity.

## Failure behavior

Parent-to-Pay failure behavior:

- Dashboard: return empty/null billing-related fields where safe, with an integration-unavailable status.
- Billing: return empty/null Pay-derived fields and block critical payment actions.
- Launcher: do not launch products if Pay entitlement/projection status cannot be trusted.
- Manage subscription: do not trigger checkout/change/cancel/restart actions while Pay is unavailable.
- Rewards: remain viewable, except Pay-dependent reward updates or Pay-derived eligibility must not proceed.

## Product access rule

Product launch eligibility must consider entitlement summaries and product access/provisioning state.

If entitlement is ON but provisioning is incomplete, the launcher must not silently proceed. It should return a status that lets the frontend show a message such as:

> Complete account setup or wait for provisioning to finish before launching this product.

## Account identity rule

The parent backend is the sole login authority for Zeptalytic accounts. Product apps should trust parent-issued identity/session state according to the eventual product integration contract.

## Implementation strategy

Do not build the entire repository layer first across all domains. After a small foundation pass, implement vertical feature slices that include:

- repository methods
- service logic
- schemas
- router endpoints
- tests
- docs/spec updates

Preferred initial vertical slices:

1. application foundation and API conventions
2. auth/session/account foundation
3. profile/settings/addresses/communication preferences
4. parent-to-Pay client and projection foundation
5. dashboard/launcher/billing aggregation
6. support/announcements/service status
7. rewards/objectives/badges application layer
8. Discord integration flow
9. background jobs and operational hardening
