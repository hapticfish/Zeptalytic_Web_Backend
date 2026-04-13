# Zeptalytic Feature Ownership Register

## Purpose
This register maps each currently known frontend route/feature to:
- frontend ownership
- parent backend ownership
- Pay dependency
- data source expectations
- launch priority
- implementation notes

This document should be updated as features move from static to live.

---

## Public routes

### `/`
**Current frontend behavior**
- hero CTAs route to signup/login/product pages
- sticky launch goes to signup
- product cards route to product pages
- newsletter button exists but is not live

**Ownership**
- frontend: layout, routing, animations, CTA shell
- parent backend: signup/login behavior when live
- Pay: none
- parent DB: none for launch; newsletter later

**Notes**
- newsletter stays deferred until backend/provider flow exists
- CTA routing may remain frontend-only until live auth routes are wired

**Launch priority**
- launch-critical for routing only
- newsletter is post-launch

---

### `/products/zardbot`
**Current frontend behavior**
- launch/get started buttons lead to signup/sign-in
- testimonials currently static
- pricing area currently static

**Ownership**
- frontend: layout, product visuals, section composition
- parent backend: live pricing response, testimonial response later
- Pay: pricing truth
- parent DB: testimonials cache later, optional product display metadata

**Notes**
- pricing cards must stop acting as production truth once pricing API exists
- testimonials should move from static content to parent-managed source later

**Launch priority**
- launch-critical for pricing CTA correctness
- G2-backed testimonials can be post-launch

---

### product detail page 2 (same pattern as second product page)
**Ownership**
- same as `/products/zardbot`

---

### `/pricing`
**Current frontend behavior**
- monthly/yearly toggle
- static plan prices and bundles
- checkout / upgrade buttons route to signup
- feature comparison matrix currently static

**Ownership**
- frontend: toggle interaction, presentation
- parent backend: plan/bundle display API
- Pay: pricing truth via plan catalog
- parent DB: optional marketing/display metadata for comparison matrix and bundles

**Notes**
- toggle remains frontend state
- actual prices and available plan intervals come from backend
- feature comparison matrix is parent-owned metadata, not Pay truth

**Launch priority**
- launch-critical

---

### `/company`
**Ownership**
- frontend only

**Notes**
- no launch backend dependency

---

### `/support`
**Current frontend behavior**
- support modal launch
- billing/support/sales cards
- FAQ accordion
- Discord link
- knowledge-base search planned later

**Ownership**
- frontend: modal shell, FAQ, Discord link, future search UI
- parent backend: support ticket endpoints, attachment handling, response-time info, product status data
- Pay: none
- parent DB: support tickets, messages, attachment metadata

**Notes**
- attachment handling must be hardened
- KB search is post-launch

**Launch priority**
- launch-critical for support modal
- KB search post-launch

---

## Authenticated routes

### `/app/dashboard`
**Current frontend behavior**
- logout button
- billing snapshot
- milestone progress card
- system status card
- updates area
- launcher cards

**Ownership**
- frontend: dashboard layout and composition
- parent backend: aggregated dashboard response, logout
- Pay: billing snapshot truth and entitlement/access truth
- parent DB: rewards, announcements, service statuses, access state projection cache

**Notes**
- do not let frontend reconstruct business state from scattered calls
- billing snapshot must be parent-served using Pay truth

**Launch priority**
- launch-critical

---

### `/app/launcher`
**Current frontend behavior**
- product cards and launch buttons

**Ownership**
- frontend: launcher page UI
- parent backend: launch availability, access state, launch URL, disabled reason
- Pay: entitlement truth
- parent DB: product access state projection

**Notes**
- frontend must not guess access state

**Launch priority**
- launch-critical

---

### `/app/rewards`
**Current frontend behavior**
- points/tier progress
- perks
- milestones
- objectives
- reward gallery

**Ownership**
- frontend: visuals and interactions
- parent backend: rewards/objectives APIs
- Pay: optional event input only
- parent DB: rewards tables

**Notes**
- this domain is parent-owned

**Launch priority**
- can be launch-critical if included in launch scope; otherwise phase 2 launch

---

### `/app/billing`
**Current frontend behavior**
- subscription cards
- manage-subscription
- promo code entry
- plan changes
- payment-method cards/modal
- billing address modal
- transaction history and downloads

**Ownership**
- frontend: page UI, modal shells
- parent backend: billing page API, address CRUD, safe payment-method summary display, transaction history API, document/download endpoints
- Pay: subscriptions, pricing, checkout, promo logic, payment truth, invoices/receipts, entitlement-linked billing changes
- parent DB: addresses, optional payment-method safe summary cache, billing read-models

**Notes**
- Stripe.js / Elements + SetupIntents is the intended add/update card model
- no raw card data through parent servers
- Coinbase should be modeled as a crypto payment rail, not saved-card management
- promo logic belongs in Pay

**Launch priority**
- launch-critical

---

### `/app/settings`
**Current frontend behavior**
- profile image
- immutable username
- email
- phone
- timezone
- notifications
- integrations (Discord)
- security/auth card
- 2FA toggle
- password change fields

**Ownership**
- frontend: settings page UI
- parent backend: profile/settings/auth/integrations endpoints
- Pay: none
- parent DB: accounts, profiles, communication preferences, integrations/oauth connections, security state tables

**Notes**
- add fields/support for:
  - last login
  - email verification state
  - recovery-method visibility if 2FA is live
  - Discord username display

**Launch priority**
- launch-critical

---

## Cross-feature ownership reminders

### Pricing
- pricing truth is Pay-owned
- plan comparison copy is parent-owned

### Payment methods
- provider-managed instrument handling
- parent shows safe summaries only
- Stripe Elements / SetupIntents is the intended card-capture pattern

### Launcher access
- parent-served, Pay-derived

### Support
- parent-owned, never in Pay

### Rewards
- parent-owned, may receive billing-related event input later

### Testimonials
- parent-owned cache/normalization, G2-backed later

### Newsletter
- parent-owned, later phase

### KB search
- parent-owned, later phase
