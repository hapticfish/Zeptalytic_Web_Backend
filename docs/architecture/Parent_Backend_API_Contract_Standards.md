# Parent Backend API Contract Standards

## Purpose

Define API conventions for the Zeptalytic Web Backend so coding agents implement routers, schemas, errors, and frontend contracts consistently.

## Versioning

All new browser-facing APIs should use versioned routes:

```text
/api/v1/...
```

Avoid unversioned application routes except for health/readiness endpoints.

## Router organization

Use domain routers for canonical resources and aggregation routers for UI-composed read models.

Domain routers:

- `/api/v1/auth`
- `/api/v1/accounts`
- `/api/v1/profiles`
- `/api/v1/addresses`
- `/api/v1/communication-preferences`
- `/api/v1/support`
- `/api/v1/announcements`
- `/api/v1/service-status`
- `/api/v1/rewards`
- `/api/v1/objectives`
- `/api/v1/badges`
- `/api/v1/integrations`

Aggregation routers:

- `/api/v1/dashboard`
- `/api/v1/launcher`
- `/api/v1/billing`

## Response style

Use plain JSON resource responses for reads.

For mutations, return simple status/success responses unless returning the updated resource materially improves frontend behavior.

Recommended mutation response:

```json
{
  "success": true,
  "message": "Profile updated."
}
```

When the frontend needs to refresh displayed data after a mutation, prefer a separate read endpoint or return a small updated summary.

## Standard error shape

Use one standard error response shape across the backend.

Recommended structure:

```json
{
  "error": {
    "code": "profile_email_already_exists",
    "message": "That email address is already in use.",
    "details": {},
    "request_id": "req_..."
  }
}
```

Rules:

- `code` must be stable and machine-readable.
- `message` must be safe for user display when appropriate.
- `details` must not leak sensitive internals.
- `request_id` should be included when request IDs/tracing are implemented.
- Do not expose stack traces to clients.

## Pagination

For phase 1, use simple capped list endpoints where data volume is naturally small.

Use cursor pagination for potentially growing user-facing lists:

- support tickets
- support messages
- transaction history
- reward activity
- objective activity
- announcements
- session/device list

Recommended query parameters:

```text
?limit=25&cursor=...
```

Avoid page-number pagination for data that can change while the user browses.

## Authentication and authorization

Logged-in dashboard/authenticated routes require an authenticated parent account session.

Email verification is required for all authenticated actions except opening a support ticket.

Suspended users may log in and access billing/support, but should be blocked from product launch and most account-expanding actions.

Closed accounts should not be allowed normal login or product access.

Role-based authorization is required immediately for:

- user
- admin
- super_admin

Admin/internal endpoints should be physically separated from user-facing routers when implemented.

## DTO safety

API schemas must be explicit safe DTOs. Do not return raw ORM objects directly from routers.

Do not expose:

- Discord user ID unless an internal/admin endpoint requires it
- payment provider sensitive IDs unless explicitly safe
- internal database implementation details
- secrets/tokens
- password hashes
- 2FA secret material
- raw webhook payloads
- internal stack errors

## Ownership metadata in contract docs

Frontend/backend contract docs should identify each field as one of:

- parent-owned
- Pay-owned live
- Pay-derived projection
- static/configured display metadata
- external review source
- not implemented yet

## Fallback behavior

Contracts must explicitly define fallback behavior.

Examples:

- Pay unavailable: Pay-derived fields may be null/empty and critical actions blocked.
- Service status unavailable: return degraded/unknown style status rather than inventing online.
- G2/testimonial unavailable: return empty review list or cached static fallback.
- User has no products: return empty launcher cards and appropriate CTA hints.

## HTTP method conventions

Recommended:

- `GET` for reads
- `POST` for actions and creation
- `PATCH` for partial updates
- `DELETE` for user-requested deletion/removal where appropriate

Avoid overusing `PUT` unless replacing an entire resource.

## Important endpoint categories

### Auth

- signup
- login
- logout
- email verification
- resend verification
- forgot password
- reset password
- change password
- 2FA enrollment
- 2FA challenge/verify
- recovery codes
- account closure
- session/device management

### Settings

- profile display
- profile update
- address list
- address create/update/delete
- set primary address
- communication preferences
- notification settings
- integrations status

### Support

- create support ticket
- upload attachment metadata/submit attachment
- list user tickets
- view ticket details
- add ticket message if implemented
- product status summary for support page

### Dashboard/launcher/billing

- dashboard summary
- launcher products
- billing snapshot
- transaction history
- payment method summaries
- subscription cards
- manage subscription action initiation

### Rewards

- rewards summary
- objective list
- objective progress
- milestone state
- badge gallery
- reward activity
- mark notification viewed
