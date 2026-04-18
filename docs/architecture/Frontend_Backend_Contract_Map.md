# Frontend ↔ Backend Contract Map

## Purpose

Map existing Zeptalytic frontend pages to backend data contracts.

The frontend pages are considered mostly stable. Backend payloads may be designed for long-term normalized use, but they must support the existing pages and modals.

## Ownership labels

Use these ownership labels for each field:

- Parent-owned
- Pay-owned live
- Pay-derived projection
- Static/display metadata
- External review source
- Future/not implemented

## Public home page

Mostly static marketing content.

Backend needs:

- none for initial phase

Optional later:

- announcements
- product status
- testimonials

## Product pages

Pages:

- `/products/zardbot`
- `/products/zepta`
- future `/products/altra`

Backend needs:

- product display metadata
- subscription tiers
- pricing values
- monthly/annual toggle support
- feature lists per tier
- testimonial/review section from G2 or equivalent external review source
- status/availability if displayed

Recommended ownership:

- price truth: Pay-owned or Pay-derived catalog projection
- feature list and marketing copy: Parent display metadata
- testimonials: External review source, optionally cached/projected by parent

## Pricing page

Backend needs:

- ZardBot tiers
- Zepta tiers
- bundles
- monthly/annual prices
- feature comparison tables
- bundle comparison details
- CTA/action metadata for checkout initiation

Recommended approach:

- parent returns display-ready plan catalog composed from Pay price truth and parent display metadata
- detailed comparison tables should be database/config-backed, not hardcoded only in frontend
- frontend toggle should select monthly/annual variants from backend-provided data

## About/company page

Mostly static copy.

Backend needs:

- testimonial/review section from G2 or equivalent if enabled

## Support page

Backend needs:

- product status by product
- support modal submission
- request type options
- product options
- priority options
- estimated response time display
- attachment upload support
- Discord community invite/link

Support modal fields:

- request type: technical support, billing, sales, feature request
- product
- priority: low, normal/medium, high, urgent
- subject
- description
- document uploads
- estimated response time
- product status display

First phase does not require full admin support dashboard.

## Registration/signup page

Backend must support:

- username
- confirm username if frontend requires it
- email
- confirm email
- password
- confirm password
- preferred language
- timezone
- phone number
- investment profile
- risk tolerance
- multi-select preferred assets
- initial notification preferences
- optional Discord OAuth link/capture
- Discord username capture
- internal Discord user ID capture

Email verification is required before normal account use except opening support tickets.

Pay profile/customer identity must be created at parent account creation.

## Login page

Backend must support:

- login
- 2FA challenge if enabled
- session creation
- account status handling
- suspended-user billing/support access
- closed-account blocking

## Reset password page

Backend must support:

- forgot password request
- reset token validation
- reset password
- password change while authenticated

## Dashboard home

Backend should expose a dashboard summary endpoint.

Required dashboard sections:

### Product launcher card

- products the user has access to
- product name/code
- access state
- launch URL or launch action metadata
- blocked/pending message if not launchable

### Billing snapshot card

- subscription status
- subscription level by subscribed product
- current charge amount
- billing frequency
- next payment date
- last four of current payment method

### Milestone/progress card

- current points
- reward tier
- subscription level where needed
- current milestone
- next milestone
- points to next milestone

### System status card

Product-level status for:

- ZardBot
- Zepta
- ɅLTRA

### Notification feed

Scrolling notifications such as:

- newsletters
- version updates
- announcements
- product notices

## Launcher page

Same access behavior as dashboard launcher card, expanded for all products.

Launch state should be based on entitlement summaries and product access/provisioning state.

If entitlement is ON but provisioning is incomplete, return a pending/blocked state and message.

## Rewards page

Backend needs:

- total points
- reward tier
- current milestone
- points to next milestone
- current active perks
- next milestone action/description
- objective progress list
- reward/badge gallery
- collected/earned rewards
- milestone notification presentation state

Active perks may come from reward grants/objective achievements.

## Objectives page

Backend needs:

- total points
- reward tier
- all available objectives
- objective completion status
- objective descriptions
- staged progress, if applicable
- current progress percentage
- recent objective activity
- tier status
- completion notification queue

## Billing page

Backend needs:

### Subscription cards

For each subscribed/enrolled product:

- product
- subscription level
- price/current charge
- billing cycle
- next billing date
- status: active/canceled/suspended/etc.

### Promo code card

- submit promo code
- validate/apply through Pay where commercial
- return success/failure result

### Explore upgrades/promotions card

Mostly link/CTA to checkout/upgrade flow.

### Payment methods

- card/wallet icon based on type
- payment brand/type
- last four
- wallet first four and last four where applicable
- expiration details where applicable
- primary/default flag
- last-used timestamp
- PayPal-like email where applicable
- cardholder name if available

Payment method truth should come from Pay live reads or Pay-derived safe summaries.

### Billing address mini cards

- saved billing/mailing addresses
- primary address
- structured display

Addresses are parent-owned.

### Transaction history

- date
- detail line/description
- amount

Transaction history should be read live from Pay where practical.

## Manage payment methods modal

Backend needs:

- list payment methods
- show expiration
- show primary/default flag
- show last used
- show PayPal email if applicable
- show cardholder name
- show last four
- initiate set-primary/default action through Pay where commercial
- initiate save/update through Pay-managed flow where payment details are involved

Parent must not store sensitive payment data.

## Manage billing address modal

Backend needs:

- list multiple saved addresses
- total saved count
- create/edit/delete address
- set primary address
- support billing and mailing address types
- country-specific validation
- lat/lng and normalized structured Google address components
- formatted display address

## Settings page

### Profile card

Backend needs:

- static username
- email editable
- phone editable
- timezone editable
- profile picture/display avatar
- Discord username display
- profile update flow

### Notification preferences card

Backend needs:

- marketing emails
- product updates
- billing notifications
- email announcements
- newsletter subscription state separately tracked

No SMS or Discord notification channel for now.

### Security/authentication card

Backend needs:

- password reset/change
- 2FA enablement
- recovery codes
- session/device management if displayed

### Integrations card

Backend needs:

- Discord integration status
- connected/not connected
- Discord username
- connect flow support
- future additional integrations placeholder

## Manage subscription flows

Parent may initiate but Pay executes.

Backend should support:

- view current subscription state
- preview/prepare upgrade/downgrade if Pay supports it
- apply promo code via Pay
- request checkout/session creation via Pay
- pause/cancel request via Pay
- restart paused subscription via Pay

Do not implement subscription truth locally.

## Contract documentation requirement

For each page/surface, specs should define:

- endpoint
- method
- request shape
- response shape
- ownership source
- fallback behavior
- auth requirement
- email verification requirement
- Pay dependency
