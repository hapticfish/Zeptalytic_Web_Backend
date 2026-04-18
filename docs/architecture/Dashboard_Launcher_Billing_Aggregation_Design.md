# Dashboard, Launcher, and Billing Aggregation Design

## Purpose

Define backend behavior for dashboard, launcher, billing, and manage-subscription surfaces.

## Design principle

Use aggregation services/endpoints to reduce frontend complexity while keeping payloads normalized enough for long-term reuse.

Recommended endpoints:

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/launcher/products`
- `GET /api/v1/billing/snapshot`
- `GET /api/v1/billing/subscriptions`
- `GET /api/v1/billing/payment-methods`
- `GET /api/v1/billing/transactions`
- `POST /api/v1/billing/checkout`
- `POST /api/v1/billing/subscription-change`
- `POST /api/v1/billing/subscription-cancel`
- `POST /api/v1/billing/subscription-restart`
- `POST /api/v1/billing/promo-code`

Exact endpoint names may be refined by specs.

## Dashboard summary

Dashboard summary should include these sections.

### Product launcher cards

For each product:

- product code
- product name
- display metadata
- access state
- entitlement state
- provisioning state
- launch URL/action metadata if allowed
- disabled reason if blocked
- status message

Products include:

- ZardBot
- Zepta
- ɅLTRA

### Billing snapshot

Required fields:

- subscribed products
- subscription level per subscribed product
- subscription status
- current charge amount
- billing frequency
- next payment date
- current payment method summary
- last four where applicable

### Milestone/progress summary

Required fields:

- current points
- current reward tier
- current milestone
- next milestone
- points to next milestone
- subscription level where needed by UI

### System status

Product-level statuses for:

- ZardBot
- Zepta
- ɅLTRA

### Notifications feed

Scrolling notification items may include:

- newsletters
- version updates
- announcements
- product notices
- support-relevant notices

## Launcher behavior

Launcher access should be based on entitlement summaries and product access/provisioning states.

Additional blockers may include:

- account is not active
- email is not verified
- account is suspended
- product is offline/maintenance
- Pay-derived entitlement/projection state is unavailable
- provisioning is incomplete

If entitlement is ON but provisioning is incomplete, return a blocked/pending state with a message suitable for a popup.

Example state:

```json
{
  "product_code": "zardbot",
  "access_state": "provision_pending",
  "can_launch": false,
  "message": "Your subscription is active, but product setup is still being completed."
}
```

## Billing page behavior

Billing page needs:

### Subscription cards

For each enrolled/subscribed product:

- product
- subscription level
- price/current charge
- billing cycle
- next billing date
- status

### Promo code

Parent may accept promo code input but Pay must validate/apply commercial effects.

### Payment methods

Payment method summaries come from Pay live reads or Pay-derived safe summaries.

Display fields:

- type/brand
- icon type
- last four
- wallet first four/last four when applicable
- expiration date where applicable
- primary/default flag
- last-used timestamp
- PayPal-like email if applicable
- cardholder name if available

### Billing addresses

Billing and mailing addresses are parent-owned.

Display:

- multiple saved addresses
- primary flag
- total saved count
- structured and formatted address

### Transaction history

Transaction history should come from Pay live reads where practical.

Fields:

- date
- description/detail line
- amount
- status if needed
- product/subscription association if available

## Manage subscription

Parent exposes initiation endpoints, but Pay executes.

Supported flows:

- current subscription view
- upgrade/downgrade initiation
- checkout/session creation
- promo code validation/application
- pause/cancel initiation
- restart paused subscription initiation

Parent must not independently mutate commercial subscription truth.

## Pay unavailable behavior

When Pay is unavailable:

- dashboard returns null/empty Pay fields where safe
- billing returns empty/null Pay-derived details
- launcher blocks product launch if entitlement cannot be trusted
- manage subscription mutation actions fail with standard error
- rewards remain viewable except Pay-dependent eligibility/update behavior

## Projection behavior

Parent may mirror these Pay facts into projections:

- subscription summaries
- payment summaries
- entitlement summaries
- payment method summaries
- product access states

Projection tables support UI and launcher decisions, but are not commercial truth.
