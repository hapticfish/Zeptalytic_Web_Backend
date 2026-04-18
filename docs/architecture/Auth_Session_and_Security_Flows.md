# Auth, Session, and Account Security Flows

## Purpose

Define parent account authentication and account-security behavior.

## Core decision

The parent backend is the sole login authority for Zeptalytic accounts across products.

Product apps should eventually trust parent-issued identity/session state.

## Recommended auth model

Use secure server-managed sessions with HTTP-only secure cookies for browser authentication, unless the implementation plan explicitly chooses JWT access/refresh tokens.

If using cookies:

- use HTTP-only cookies
- use Secure in production
- use SameSite protection
- add CSRF protection for unsafe methods
- rotate session identifiers on login and privilege changes
- support session/device management

If product apps need cross-domain identity handoff, define a separate product-launch token or short-lived signed handoff token rather than exposing browser session internals.

## Required flows

Phase 1 must support:

- signup
- login
- logout
- email verification
- resend verification
- forgot password
- reset password
- authenticated password change
- 2FA enrollment
- 2FA challenge/verify
- 2FA recovery codes
- account closure
- session/device management

## Signup requirements

Registration form captures:

- username
- email
- password
- preferred language
- timezone
- phone number
- investment profile
- risk tolerance
- multi-select preferred assets
- initial notification preferences
- optional Discord OAuth data

At account creation:

- create parent account/profile
- create Pay profile/customer identity using same `account_id`
- create initial communication preferences
- create initial profile preferences
- create verification token
- account may remain `pending_verification` until email verification is complete

## Email verification rule

Email verification is required for all normal authenticated actions except opening a support ticket.

Unverified users may:

- log in if allowed by implementation
- access minimal verification-required screen
- request resend verification
- open support ticket

Unverified users may not:

- launch products
- complete checkout
- access normal dashboard features
- manage subscription actions
- change sensitive settings beyond verification support

## Account statuses

### active

Normal account access.

### pending_verification

Used when account creation or normal access is held up by verification, especially email verification.

Expected behavior:

- allow login/minimal access
- require verification before normal use
- allow support ticket creation
- allow resend verification

### suspended

Used for terms violations or serious account issues. Multiple payment failures may contribute, but terms/security issues are the clearer suspension reason.

Expected behavior:

- allow login
- allow billing access
- allow support access
- block product launch
- block account-expanding actions
- return clear status messages

### closed

Closed by user or by Zeptalytic.

Expected behavior:

- no normal login/product access
- support/admin recovery only if implemented
- do not silently recreate account without explicit flow

## Roles

Implement role-based authorization immediately for:

- user
- admin
- super_admin

Admin/internal routes should be separated from user-facing routes when implemented.

## 2FA

2FA should support:

- enrollment
- verification challenge
- recovery codes
- disable/reset flow with strong verification
- session/device awareness where practical

Do not expose 2FA secrets after enrollment.

## Session/device management

Support:

- current session identification
- list active sessions/devices
- revoke session
- revoke all other sessions
- stale session cleanup worker

## Password reset

Password reset should use:

- time-limited token
- one-time use
- generic success response to prevent account enumeration
- secure password policy
- session invalidation after reset where appropriate

## Account closure

Account closure should:

- mark account closed rather than hard-delete core records
- preserve required billing/support/history records
- block future normal login
- avoid deleting Pay commercial truth

## Audit logging

Audit logging is allowed and desired for security-sensitive actions, but it does not need to be the first implementation blocker.

Security-sensitive actions that should eventually be audited:

- login success/failure
- password change/reset
- email change
- 2FA enable/disable
- session revocation
- account closure
- role changes
- support attachment upload
- Pay action initiation
