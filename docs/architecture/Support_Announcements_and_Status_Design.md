# Support, Announcements, and Service Status Design

## Purpose

Define first-phase backend behavior for support tickets, announcements, and product status.

## Support scope

First phase supports customer-side ticket creation and basic ticket metadata handling.

Admin/support dashboards are not in scope for the first phase. Administrative handling may be done through database/terminal/code workflows until a later admin UI exists.

## Support ticket creation

Support modal must capture:

- request type
- product
- priority
- subject
- description
- document uploads
- estimated response time
- product status context

Supported request types:

- technical support
- billing
- sales
- feature request

Supported priority values:

- low
- medium/normal
- high
- urgent

Product selection should include current Zeptalytic products:

- ZardBot
- Zepta
- ɅLTRA
- general/account if needed

## Ticket behavior

Phase 1 should support:

- create ticket
- upload attachment metadata
- store attachment association
- ticket status changes
- ticket assignment
- category/request type updates
- priority updates

Full customer-visible ticket conversation history is not required for the first pass unless already easy to include.

## Ticket statuses

Use the locked parent support ticket status vocabulary:

- open
- in_progress
- waiting_on_customer
- resolved
- closed

## Support attachments

Do not store large raw file blobs directly in normal database rows.

Recommended approach:

- DB stores attachment metadata
- file storage uses a storage service abstraction
- local filesystem may be used in development only behind the same abstraction
- production should use object storage or equivalent safe storage

Attachment controls:

- size limit
- extension allowlist
- MIME validation
- malware scanning hook or future placeholder
- account/ticket authorization on retrieval
- no public unauthenticated file URLs unless signed and time-limited

Suggested first-phase limits:

- max 10 MB per file
- max 5 files per ticket
- allow common support-safe types: PDF, PNG, JPG/JPEG, TXT, LOG, CSV, DOCX
- reject executable/script/archive types by default

## Estimated response time

Support modal may display an estimated response time.

Initial implementation options:

- static per-priority estimate
- computed from recent support-ticket response data if available
- fallback to default estimate when not enough data exists

Do not block ticket creation if estimate cannot be computed.

## Announcements

Announcements can appear in:

- dashboard notification feed
- support page
- possibly public pages later

Phase 1 may use read-only site consumption with admin management through DB/terminal/code.

Announcements should support:

- global/product scope
- severity
- type/category
- publish/active window if already modeled
- display title/body
- product association if product-scoped

## Service status

Service status is per product.

Products:

- ZardBot
- Zepta
- ɅLTRA

Statuses should align with locked vocabulary:

- online
- degraded
- maintenance
- offline

Service status should appear in:

- dashboard system status card
- support page product status
- possibly public product pages later

## Read model

Create a common read model for announcements/status so dashboard/support/public pages do not duplicate logic.

Recommended service:

- `ServiceStatusService`
- `AnnouncementService`
- optional `SiteNoticeService` for composed notification feed
