# Agent Non-Goals and Implementation Guardrails

## Purpose

Prevent coding agents from inventing behavior, duplicating Pay logic, or expanding scope beyond the agreed backend phase.

## Non-goals

Agents must not implement the following unless a later spec explicitly authorizes it.

### Do not duplicate Pay commercial logic

Do not implement local parent-side truth for:

- checkout execution
- payment success/failure
- subscription commercial truth
- entitlement truth from provider events
- refunds/disputes/risk
- Stripe webhooks
- Coinbase Commerce webhooks
- payment-provider secret handling

### Do not store sensitive payment details

Do not store:

- full card number
- CVV/CVC
- raw payment credentials
- private wallet keys

### Do not build admin dashboards yet

Admin/support dashboards are not in first-phase scope.

Admin management can be handled through database/terminal/code workflows until later specs.

### Do not redesign stable frontend pages

Frontend pages are mostly stable. Backend contracts should support the current page surfaces while remaining normalized and maintainable.

### Do not make Discord affect rewards/access

Discord integration is profile/settings linkage only for phase 1.

Do not implement Discord-based rewards, access, launcher permissions, or notification delivery.

### Do not award points directly from frontend

Frontend reward APIs should be read-only except for presentation state actions, such as mark viewed/skip.

### Do not create giant layer-only specs after foundation

Avoid building every repository/service/router in isolation across the whole repo.

After foundation conventions are in place, prefer vertical feature specs.

### Do not mark spec items complete without authoritative verification

The Docker test suite must pass before marking spec items complete.

### Do not insert progress entries above older entries

Progress entries must be appended to the absolute end of `progress/progress.txt`.

Newest entry must be the final content in the file.

## Required implementation discipline

Agents must:

- search before editing
- summarize repo findings before changes
- keep changes small and localized
- preserve one-table-per-file model organization
- use existing vocabulary docs
- preserve Pay/source-of-truth boundary
- update tests with implementation
- update docs/spec status honestly
- record blockers instead of marking incomplete work done

## Recommended next-phase spec pattern

Use a small set of foundation specs, then vertical capability specs.

Foundation specs:

1. application conventions
2. repository conventions
3. service conventions
4. API contract/error conventions
5. Pay client/projection skeleton

Vertical specs:

1. auth/session/account foundation
2. profile/settings/addresses/preferences
3. Pay integration and billing projections
4. dashboard/launcher/billing aggregation
5. support/announcements/service status
6. rewards application/read APIs
7. Discord integration application flow
8. background jobs/security hardening
