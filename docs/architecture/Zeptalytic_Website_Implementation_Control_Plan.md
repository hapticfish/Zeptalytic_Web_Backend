# Zeptalytic Website Implementation Control Plan

## Purpose
This document is the controlling implementation plan for the Zeptalytic parent site build. It defines:
- authoritative system ownership boundaries
- execution order
- non-negotiable implementation rules
- validation gates between phases
- the core assumptions Ralph/Codex agent runs must follow

This document should be treated as the top-level reference for all agent-guided implementation work related to the parent site, parent DB, and parent backend integration with the existing Pay service.

## Current baseline assumptions
These assumptions are locked unless explicitly revised in a later architecture decision:
1. The **parent frontend** is the presentation layer only.
2. The **parent backend** is the only browser-facing API.
3. The **Pay service** remains the source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, and provider-webhook finality.
4. The **parent DB** owns identity, settings, addresses, support, rewards, content feeds, testimonial cache, announcements, and Pay-derived read models.
5. `account_id` is the cross-system identity bridge between parent site and Pay.
6. Stripe card handling uses **Stripe.js / Elements + SetupIntents** so card data goes from browser to Stripe, not through parent servers.
7. Coinbase Commerce is treated as a checkout/payment rail, not a saved-card manager in the same sense as Stripe.
8. Promo-code logic belongs in Pay because it changes commercial truth.
9. Newsletter signup and knowledge-base search are post-launch unless reprioritized.
10. Testimonials are currently static and should later move to a parent-managed G2-backed normalized source.

## Non-negotiable architecture rules

### Rule 1 — Frontend never owns commercial truth
Do not keep production pricing, subscription state, entitlement state, order state, or payment state as authoritative frontend constants.

### Rule 2 — Parent backend is the browser boundary
The browser talks only to the parent backend. The parent backend talks to Pay and other integrations.

### Rule 3 — Pay remains commercial truth
Orders, payments, refunds, subscriptions, entitlements, risk, disputes, checkout, provider references, and pricing truth belong to Pay.

### Rule 4 — Parent site owns website/account functionality
Auth, profile, settings, addresses, support, rewards, announcements, testimonials, and dashboard composition belong to the parent site.

### Rule 5 — No raw payment instrument handling in parent systems
Parent frontend and backend must not handle or persist raw PAN/CVC. Stripe.js / Elements + SetupIntents is the intended model. Any locally stored payment-method data must be safe summary data only.

### Rule 6 — Launcher and billing access come from Pay-derived truth
Frontend must not infer entitlement state locally. Launcher access and billing snapshots must be based on parent-served data derived from Pay truth.

### Rule 7 — No duplicated billing engine in parent DB
Parent DB may hold projection/read-model tables for display performance and coherent UX, but not a second authoritative billing engine.

### Rule 8 — Every user-visible feature needs a full implementation chain
A feature is not complete unless the following exist:
1. UI surface
2. API contract
3. backend implementation
4. persistence/integration path
5. error and loading states
6. tests
7. authoritative source validation for Pay-coupled features

## Phase plan

### Phase 0 — Freeze identifiers and vocabulary
Lock the following before implementation starts:
- product codes
- plan codes
- bundle codes
- billing interval vocabulary
- parent API route naming
- account lifecycle/status vocabulary
- immutable username rule
- required signup fields
- initial launch scope vs post-launch scope

**Exit gate**
- one written decision record exists for each of the above

### Phase 1 — Build control artifacts
Create and maintain:
- Feature Ownership Register
- Parent vs Pay Data Ownership Matrix
- UI-to-API Matrix
- Migration Ledger
- Projection / Read-Model Ledger

**Exit gate**
- every current page, card, modal, and button is mapped to an owner

### Phase 2 — Finalize parent DB schema
Build or confirm parent DB domains:
- identity and auth
- profile and settings
- addresses
- integrations
- support
- announcements/status
- rewards
- testimonial cache
- Pay-derived read models

**Exit gate**
- parent schema is migration-backed
- no duplicated billing truth with Pay
- table and column names verified

### Phase 3 — Parent backend foundation
Implement:
- FastAPI app shell
- configuration and environment loading
- DB session handling
- security dependencies
- error handling
- structured logging
- rate limiting for public/sensitive routes
- object storage / attachment handling framework
- service clients for Pay and other integrations

**Exit gate**
- health/readiness works
- DB connectivity works
- core dependency injection and auth scaffolding exist
- Pay client skeleton exists

### Phase 4 — Auth and core account flows
Implement:
- signup
- login
- logout
- current user
- password change
- forgot/reset password
- email verification
- last login tracking
- 2FA state support
- profile/settings CRUD
- Discord connection state display

**Exit gate**
- protected routes can be wired to live auth
- settings page can stop using placeholders

### Phase 5 — Support and attachment handling
Implement:
- support ticket create/list/read
- secure attachments
- response-time policy display
- product association
- priority/request type handling

**Exit gate**
- support modal is fully functional
- attachments are stored and validated safely

### Phase 6 — Parent ↔ Pay integration contracts
Define and implement parent-facing service contracts for:
- pricing catalog reads
- checkout/session creation
- billing snapshot
- subscriptions summary
- entitlement summary
- payment-method safe summaries
- transaction history
- pause/cancel/change-plan actions
- invoice/receipt fetch or links

**Exit gate**
- parent backend has a stable internal contract with Pay
- frontend does not consume raw Pay schema directly

### Phase 7 — Pricing and checkout implementation
Implement:
- live pricing fetch
- monthly/yearly display toggle using backend-sourced values
- bundle pricing display
- CTA flows for signup, checkout, and upgrades
- comparison matrix data strategy

**Exit gate**
- no production pricing truth remains hardcoded in frontend
- checkout flow is real

### Phase 8 — Billing implementation
Implement:
- subscription cards
- payment-method summary display
- payment-method add/update/remove flow initiation
- billing addresses
- transaction history
- receipt/download flow
- promo-code application UI backed by Pay

**Exit gate**
- billing page is live without unsafe payment handling
- promo flow is designed and wired against Pay

### Phase 9 — Dashboard and launcher aggregation
Implement parent aggregation endpoints for:
- billing snapshot
- rewards snapshot
- system status
- announcements
- launcher access states
- product launch URLs and disabled reasons

**Exit gate**
- dashboard and launcher use coherent parent-served aggregation

### Phase 10 — Rewards and objectives
Implement:
- tier definitions
- point balances
- milestones
- objectives
- active perks
- reward galleries / badges
- reward events and progress

**Exit gate**
- rewards page is fully live on parent systems

### Phase 11 — Testimonials and additional content feeds
Implement:
- testimonial normalization and cache
- G2 integration later
- dashboard/product updates feed
- newsletter later
- KB search later

**Exit gate**
- any enabled dynamic content is parent-managed and not hardcoded

### Phase 12 — Hardening and release gates
Before release verify:
- auth and route authorization
- support attachment security
- pricing source verification
- billing source verification
- subscription and entitlement consistency
- launcher gating
- address CRUD
- settings/profile correctness
- promo behavior
- transaction history correctness
- error-state UI coverage
- secrets not leaked to frontend
- parent-to-Pay authentication works

## Stop signs / things not to do
- Do not put pricing truth in frontend.
- Do not duplicate Pay lifecycle logic in parent DB.
- Do not collect raw card data outside Stripe Elements / SetupIntents.
- Do not model Coinbase like a saved-card system.
- Do not make launcher access a frontend-only decision.
- Do not push support/newsletter/testimonials/settings into Pay.
- Do not wire the billing page before the Pay contract is defined.
- Do not mark a UI feature complete when it only has visuals.

## Recommended agent-run breakdown
The work should be split into separate specs / runs rather than one giant implementation pass.

Recommended branch/spec split:
1. parent DB foundation
2. parent auth/profile/settings
3. parent support + attachments
4. parent Pay read-models + integration client
5. pricing + checkout wiring
6. billing page implementation
7. dashboard + launcher aggregation
8. rewards implementation
9. testimonials / announcements / later content flows
10. hardening + test coverage

## How agent specs should reference this document
Every spec touching the parent site should instruct the agent to consult:
- this control plan
- the feature ownership register
- the parent vs Pay data ownership matrix
- any active schema/migration plan
- any relevant frontend inventory references

## Suggested spec naming
- `specs/parent_db_foundation.json`
- `specs/parent_auth_profile_settings.json`
- `specs/parent_support_and_attachments.json`
- `specs/parent_pay_integration_read_models.json`
- `specs/parent_pricing_checkout.json`
- `specs/parent_billing_page.json`
- `specs/parent_dashboard_launcher.json`
- `specs/parent_rewards.json`
- `specs/parent_content_and_testimonials.json`
- `specs/parent_hardening_and_tests.json`
