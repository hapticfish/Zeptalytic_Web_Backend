# Parent ↔ Pay Integration and Projection Strategy

## Purpose

Define how the Zeptalytic parent backend integrates with the Zeptalytic Pay service.

## Core decision

The parent backend may initiate payment-related workflows but Pay owns execution and commercial truth.

Parent calls Pay for payment/subscription/entitlement operations and presents the returned result.

## Linking key

The linking key between parent and Pay is `account_id`.

A Pay-side account/customer identity must exist for every parent account. The Pay profile/customer record should be created during account creation. Checkout later adds commercial details.

Account linking failures are internal operational issues, not normal user-facing flows.

## Parent-owned vs Pay-owned

### Parent-owned

- billing/mailing addresses
- frontend-safe billing aggregation
- dashboard billing snapshot presentation
- product launcher presentation
- Pay-derived projection rows
- support tickets about billing issues
- parent account identity and settings

### Pay-owned

- checkout
- pricing truth
- orders
- payments
- refunds
- subscriptions
- entitlements
- disputes
- risk
- payment provider interaction
- Stripe/Coinbase webhooks
- actual payment method truth

## Parent-initiated Pay actions

The parent backend may expose endpoints that initiate:

- checkout
- plan change
- subscription cancel/pause
- subscription restart
- promo/discount application or validation
- payment method management session/setup flow

However, the endpoint must delegate the commercial operation to Pay.

The parent should return Pay-generated redirect URLs, client secrets, session IDs, or safe result summaries as appropriate.

## Pay authentication

Use the most secure conventional internal service authentication available for the current architecture.

Recommended path:

1. short-lived service JWT between parent and Pay, with issuer/audience validation
2. strict internal network/configuration controls
3. rotateable keys/secrets
4. mTLS later if the deployment environment supports it cleanly

Avoid hardcoding secrets.

## Live reads vs projections

Use a hybrid model.

### Live Pay reads

Use live Pay reads for:

- transaction history on billing page
- current payment method summaries
- manage subscription actions
- checkout/session creation
- plan change/cancel/pause/restart initiation
- current pricing truth when needed for checkout-critical flows

### Parent-side projections

Mirror Pay facts into parent DB projection tables for:

- subscription summaries
- payment summaries
- entitlement summaries
- payment method summaries
- product access states

These projections support:

- dashboard display
- launcher display
- rewards eligibility hints
- faster page loads
- fallback display when appropriate
- frontend aggregation

Projection tables are not editable commercial truth.

## Projection update strategy

Use both event-driven and scheduled sync where practical.

Initial acceptable implementation:

- request-triggered sync where needed
- scheduled worker sync for stale records
- explicit upsert methods
- safe stale/unavailable handling

Future enhancement:

- Pay outbox/event feed to parent
- signed internal events
- retry/dead-letter handling

## Pay unavailable behavior

When Pay is unavailable:

### Dashboard

Return dashboard payload with null/empty Pay-derived billing fields and an integration unavailable marker.

### Billing

Return null/empty transaction and payment method summaries. Do not allow critical mutation actions.

### Launcher

Do not launch products if entitlement/projection state cannot be trusted.

### Manage subscription

Block checkout/change/cancel/restart actions and return a clear standard error.

### Rewards

Rewards remain viewable. Pay-dependent reward eligibility or updates should not be processed.

## Required Pay endpoint inventory

The parent integration docs/specs should identify Pay endpoints for:

- pricing catalog/read
- checkout/session initiation
- subscription summary
- subscription change initiation
- subscription cancellation/pause/restart initiation
- payment history
- payment method summary
- payment method management/setup flow
- entitlement summary
- promo/discount validation/application
- refund/dispute visibility if exposed

For each endpoint, document whether parent:

- consumes it live
- mirrors it into projection tables
- transforms it into a UI aggregation response
- only initiates and redirects/hands off

## Data safety

Parent must never store:

- full card numbers
- CVV/CVC
- raw provider payment secrets
- private wallet keys
- Stripe/Coinbase webhook secrets outside secure config
- sensitive provider payloads in normal UI tables

Parent may store/display safe summaries:

- payment brand/type
- last four
- wallet first four/last four when safe
- expiration month/year where allowed
- primary/default flag
- last-used timestamp
- provider display label
- masked email for PayPal-like methods if supported by Pay

## Pricing/public page strategy

Public pricing and product pages should use a composed display model:

- Pay owns commercial price truth.
- Parent owns display metadata and marketing feature descriptions.
- Product feature comparison tables should be database/config-backed rather than hardcoded in frontend where practical.
- The frontend should not contain authoritative pricing.

Use parent-side display metadata tables for feature lists and marketing presentation, with price values sourced from Pay or Pay-derived catalog projections.

## No duplicate commercial logic

Agents must not implement Pay-equivalent subscription/payment logic inside parent. If a frontend flow needs commercial state, add/consume a Pay integration contract rather than duplicating the rule locally.
