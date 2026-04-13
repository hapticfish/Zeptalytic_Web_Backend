# Zeptalytic Parent vs Pay Data Ownership Matrix

## Purpose
This document defines which system is authoritative for each domain and how the parent site should consume or project that data.

---

## Identity and authentication
**Authoritative owner:** Parent  
**Examples**
- signup/login/logout
- password changes
- email verification
- session or refresh state
- 2FA configuration
- last login tracking

**Parent DB role**
- authoritative persistence

**Pay role**
- no ownership, may reference shared `account_id`

---

## Profile and account settings
**Authoritative owner:** Parent  
**Examples**
- username
- profile image
- email display/state
- phone
- timezone
- notification preferences
- Discord username / integration status
- security/recovery display state

**Parent DB role**
- authoritative persistence

**Pay role**
- none

---

## Addresses
**Authoritative owner:** Parent  
**Examples**
- billing addresses
- future shipping/mailing addresses

**Parent DB role**
- authoritative persistence

**Pay role**
- may consume address context when needed, not authoritative owner

---

## Product display metadata
**Authoritative owner:** Parent  
**Examples**
- product copy
- bundle descriptions
- plan marketing labels
- comparison matrix text
- product launch labels
- button copy

**Parent DB role**
- authoritative if stored as site metadata
- can remain frontend config for early phases

**Pay role**
- none

---

## Pricing truth
**Authoritative owner:** Pay  
**Examples**
- actual plan amount
- currency
- billing interval
- provider price IDs

**Pay anchor**
- `plan_catalog`

**Parent role**
- read and display
- may cache or project for UX but not override Pay truth

---

## Checkout orchestration
**Authoritative owner:** Pay  
**Examples**
- order creation
- provider checkout creation
- payment intent / setup intent support if surfaced through Pay orchestration
- subscription creation
- payment finality

**Parent role**
- authenticated browser-facing orchestration layer
- calls Pay internally

---

## Orders
**Authoritative owner:** Pay  
**Pay anchor**
- `orders`

**Parent role**
- summaries / history / display

---

## Payments
**Authoritative owner:** Pay  
**Pay anchor**
- `payments`

**Parent role**
- safe summaries for billing UI and dashboard
- transaction history display
- optional safe summary cache

---

## Refunds
**Authoritative owner:** Pay  
**Pay anchor**
- `refunds`

**Parent role**
- display status/history

---

## Subscriptions
**Authoritative owner:** Pay  
**Pay anchor**
- `subscriptions`

**Parent role**
- display summaries
- manage flows through parent-served actions that delegate to Pay

---

## Entitlements
**Authoritative owner:** Pay  
**Pay anchor**
- `entitlements`

**Parent role**
- launcher and dashboard access gating via projections/read models

---

## Risk / disputes / audit / webhooks / outbox
**Authoritative owner:** Pay  
**Pay anchors**
- `risk_flags`
- `disputes`
- `audit_events`
- `webhook_events`
- `outbox`

**Parent role**
- none for authoritative ownership
- may consume selected summarized operational state if needed for admin tools later

---

## Promo codes and discounts
**Authoritative owner:** Pay  
**Reason**
- modifies billing truth and order totals

**Parent role**
- accept promo code input from UI
- send to Pay for evaluation/application
- display result

**Current note**
- promo structures are not yet present in current Pay schema and need to be added there

---

## Payment methods
**Authoritative owner:** Provider side / Pay-mediated integration  
**Stripe model**
- Stripe.js / Elements + SetupIntents for card capture
- parent servers do not receive raw PAN/CVC

**Coinbase model**
- checkout/payment rail, not a Stripe-like saved-card manager

**Parent role**
- show safe summaries
- initiate add/update/remove/default flows
- optionally cache safe summary data

**Parent DB role**
- optional `payment_method_summaries` safe cache only

---

## Billing addresses
**Authoritative owner:** Parent  
**Reason**
- website/account-side user data
- not provider-billing truth

**Parent role**
- CRUD
- primary selection
- international address support

**Pay role**
- may consume selected address context where needed

---

## Transaction history / receipt views
**Authoritative owner:** Pay for transaction truth, Parent for browser-facing composition  
**Parent role**
- serve billing history endpoints using Pay truth
- provide receipt/download access or links

---

## Dashboard billing snapshot
**Authoritative owner:** Parent-composed, Pay-derived  
**Parent role**
- aggregate a coherent response for the browser
- join Pay-derived billing data with parent-owned rewards/status/updates data

---

## Launcher access
**Authoritative owner:** Parent-composed, Pay-derived  
**Parent role**
- translate Pay entitlement state plus product provisioning state into launchability

---

## Support tickets and attachments
**Authoritative owner:** Parent  
**Parent DB role**
- authoritative persistence

**Pay role**
- none

---

## Rewards, objectives, points, badges
**Authoritative owner:** Parent  
**Parent DB role**
- authoritative persistence

**Pay role**
- optional source of reward-triggering events later

---

## Announcements and system status
**Authoritative owner:** Parent  
**Parent DB role**
- authoritative persistence

**Pay role**
- only indirect if some operational status is later surfaced from billing systems

---

## Testimonials
**Authoritative owner:** Parent  
**Upstream source**
- G2 or another review source later

**Parent role**
- normalize, moderate, cache, serve

**Pay role**
- none

---

## Newsletter
**Authoritative owner:** Parent  
**Pay role**
- none

---

## KB search
**Authoritative owner:** Parent  
**Pay role**
- none
