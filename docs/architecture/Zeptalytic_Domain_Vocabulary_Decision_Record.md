# Zeptalytic Domain Vocabulary Decision Record

This file locks the canonical allowed-value vocabularies for the parent-site backend.
Do not invent alternate values during implementation. If a future change is needed, update this file first and then update the relevant spec.

## 1. Account status
- Allowed values:
  - `active`
  - `pending_verification`
  - `suspended`
  - `closed`
- Default:
  - `pending_verification`

## 2. Parent account role
- Allowed values:
  - `user`
  - `admin`
  - `super_admin`
- Default:
  - `user`

## 3. Announcement scope
- Allowed values:
  - `global`
  - `product`
- Default:
  - `global`

## 4. Announcement severity
- Allowed values:
  - `info`
  - `success`
  - `warning`
  - `critical`
- Default:
  - `info`

## 5. Service status
- Allowed values:
  - `online`
  - `degraded`
  - `maintenance`
  - `offline`
- Default:
  - `online`

## 6. Billing interval
Canonical internal vocabulary should align with Pay and remain uppercase.
- Allowed values:
  - `MONTHLY`
  - `ANNUAL`
- Default:
  - `MONTHLY`

## 7. Normalized subscription status
- Allowed values:
  - `active`
  - `trialing`
  - `past_due`
  - `paused`
  - `cancel_at_period_end`
  - `canceled`
  - `incomplete`
  - `incomplete_expired`
  - `unpaid`
  - `suspended`
- Default:
  - `incomplete`

## 8. Normalized entitlement status
Mirror the Pay entitlement vocabulary exactly.
- Allowed values:
  - `OFF`
  - `ON`
  - `PAUSED`
  - `SCHEDULED_OFF`
  - `BLOCKED_COMPLIANCE`
- Default:
  - `OFF`

## 9. Launcher access state
- Allowed values:
  - `none`
  - `provision_pending`
  - `active`
  - `suspended`
- Default:
  - `none`

## 10. Payment rail
Mirror the Pay payment rail vocabulary exactly.
- Allowed values:
  - `STRIPE`
  - `COINBASE_COMMERCE`
- Default:
  - none (must be explicit when present)

## 11. Normalized payment status
Mirror the Pay payment-status vocabulary exactly.
- Allowed values:
  - `INITIATED`
  - `REQUIRES_ACTION`
  - `SUCCEEDED`
  - `FAILED`
  - `REFUNDED`
  - `DISPUTED`
  - `CHARGE_CREATED`
  - `PENDING_ONCHAIN`
  - `CONFIRMED_FINAL`
  - `EXPIRED`
  - `UNDERPAID_REVIEW`
  - `OVERPAID_REVIEW`
- Default:
  - `INITIATED`

## 12. Payment-method summary status
Keep status separate from the default flag.
- Allowed values:
  - `active`
  - `default`
  - `expired`
  - `disabled`
- Default:
  - `active`
- Separate field:
  - `is_default` boolean must also exist for the summary model/API shape

## 13. OAuth / integration status
- Allowed values:
  - `connected`
  - `disconnected`
  - `error`
  - `pending`
- Default:
  - `pending`

## 14. Initial address type
- Allowed values:
  - `billing`
  - `shipping`
- Default:
  - `billing`

## 15. Support request type
- Allowed values:
  - `billing`
  - `sales`
  - `feature_request`
  - `technical_support`
- Default:
  - `technical_support`

## 16. Support priority
- Allowed values:
  - `low`
  - `medium`
  - `high`
  - `urgent`
- Default:
  - `medium`

## 17. Support ticket status
- Allowed values:
  - `open`
  - `in_progress`
  - `waiting_on_customer`
  - `resolved`
  - `closed`
- Default:
  - `open`

## 18. Support message author type
- Allowed values:
  - `customer`
  - `support_agent`
  - `system`
- Default:
  - `customer`

## 19. Attachment scan status
- Allowed values:
  - `pending`
  - `clean`
  - `infected`
  - `failed`
- Default:
  - `pending`

## Implementation note
Where the parent backend mirrors Pay vocabulary exactly, prefer:
- canonical internal values unchanged
- frontend label mapping handled separately in UI or presentation schemas

## Structural rule reminder
Future implementations must place models, schemas, repositories, and services into sensible files/directories if they do not already exist. Dumping unrelated definitions into one generic file is not acceptable.
