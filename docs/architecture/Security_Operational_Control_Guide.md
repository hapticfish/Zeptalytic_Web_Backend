# Security and Operational Control Guide

## Purpose

Define security and operational expectations for the next backend implementation phase.

## Required controls

The backend should incorporate:

- auth guards
- role checks
- CSRF protection if cookie sessions are used
- rate limiting
- file upload validation
- PII handling rules
- secrets/config loading discipline
- request IDs/tracing
- safe response DTOs
- standard error responses
- admin/internal route separation
- audit logging for sensitive actions where practical

## Authentication

All authenticated routes require a valid parent session/token.

Email verification is required for normal use except support ticket creation.

Suspended users may access billing/support but not product launch.

Closed users may not access normal authenticated functionality.

## Authorization

Support role-based authorization immediately:

- user
- admin
- super_admin

Admin/internal routes should be separated physically from user-facing routers.

## CSRF

If cookie-based browser sessions are used, unsafe methods must be protected against CSRF.

Unsafe methods include:

- POST
- PATCH
- PUT
- DELETE

## Rate limiting

Apply rate limits to:

- login
- signup
- forgot password
- resend verification
- support ticket creation
- attachment upload
- Discord OAuth callback abuse patterns
- payment action initiation

## PII handling

Treat these as sensitive:

- email
- phone
- address
- investment profile
- risk tolerance
- preferred assets
- Discord user ID
- support ticket contents
- attachment metadata
- session/device information

Do not log sensitive values unnecessarily.

## Payment safety

Parent must not store or process:

- full card number
- CVV/CVC
- raw payment credentials
- private wallet keys
- provider secrets in database rows
- raw sensitive provider payloads in frontend-facing stores

Use Pay/Stripe/Coinbase for sensitive payment details.

## File upload restrictions

Suggested first-phase limits:

- max 10 MB per file
- max 5 files per ticket
- allow PDF, PNG, JPG/JPEG, TXT, LOG, CSV, DOCX
- reject executables, scripts, binaries, archives by default
- validate extension and MIME type
- store metadata in DB
- store file content behind storage abstraction

## Request IDs and tracing

Every request should eventually have a request ID.

Error responses should include request ID when available.

Logs should include request ID for debugging.

## Audit logging

Audit logging can be phased in but should be planned for:

- login failure/success
- password reset/change
- 2FA enable/disable
- email change
- account closure
- role changes
- Pay action initiation
- support attachment upload
- admin/internal changes

## Secrets/config

Secrets must come from environment/config management.

Do not hardcode:

- Pay service auth secrets
- Discord OAuth secrets
- email provider secrets
- signing keys
- Stripe/Coinbase secrets
- database credentials

## Safe DTO rules

Routers should return safe response schemas, not raw ORM objects.

Do not expose:

- internal database IDs unless intended
- Discord user ID in normal user APIs
- raw Pay/provider identifiers unless safe
- stack traces
- sensitive config
- raw tokens
- password hashes
- 2FA secrets
