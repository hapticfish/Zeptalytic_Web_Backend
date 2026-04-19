# Zeptalytic Frontend ↔ Backend Runtime Integration Guide

## Purpose

This document controls the integration phase between the Zeptalytic Web Backend and the Zeptalytic React/Vite frontend.

- Backend repo: `Dev/Zeptalytic_Web_Backend`
- Frontend repo: `Dev/zeptalytic_web`

The backend is the FastAPI parent-site domain backend. The frontend is the React/Vite Zeptalytic website and authenticated app UI.

The goal is to preserve the existing frontend visual work while replacing static/mock data with backend API calls in controlled phases.

This guide should be referenced by backend and frontend spec-authoring, planning, and build runs during the frontend/backend integration phase.

---

## Repository Boundary

Backend specs are run from:

```bash
cd ~/Desktop/Dev/Zeptalytic_Web_Backend
```

Frontend specs are run from:

```bash
cd ~/Desktop/Dev/zeptalytic_web
```

Do not let one build run freely edit both repos.

Cross-repo behavior should be coordinated through:

- this runtime integration guide
- backend OpenAPI output
- backend route inventory documentation
- frontend API client contracts
- explicit repo-specific specs

Backend specs may update backend files only unless explicitly scoped otherwise.

Frontend specs may update frontend files only unless explicitly scoped otherwise.

Prefer separate backend and frontend specs over cross-repo specs.

---

## Local Development Origins

Backend local origins:

```text
http://localhost:8000
http://127.0.0.1:8000
```

Frontend local origins:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Frontend API base URL:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

The frontend should read this with:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
```

---

## Backend Runtime Requirement

The backend must run locally with:

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

The following URLs should open successfully:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

The backend app currently mounts API routes under:

```text
/api/v1
```

Do not add duplicate `/v1` prefixes inside individual frontend API calls.

---

## Auth Model

The backend currently uses HTTP-only cookie sessions.

Login and signup set the backend session cookie:

```text
zeptalytic_session
```

The frontend must not store the session token in:

```text
localStorage
sessionStorage
normal React state
visible JavaScript variables
```

Frontend API calls must use:

```ts
credentials: "include"
```

The expected browser auth flow is:

```text
1. User submits login form.
2. Frontend calls POST /api/v1/auth/login.
3. Backend validates credentials.
4. Backend sets the HTTP-only zeptalytic_session cookie.
5. Frontend calls GET /api/v1/auth/session.
6. Frontend stores only the safe returned account/session/security summary.
7. Protected frontend routes use that safe session summary.
8. Protected backend routes rely on the HTTP-only cookie.
```

---

## Required Backend CORS Behavior

The backend must allow local Vite frontend origins during development:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Credentialed CORS must be enabled for these explicit origins.

The backend should not use wildcard credentialed CORS in production.

Acceptable development behavior:

```python
allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

allow_credentials = True
```

The backend should expose this through settings rather than hard-coding all CORS behavior directly in `app/main.py`.

Suggested backend config fields:

```python
cors_allowed_origins: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
cors_allow_credentials: bool = True
```

---

## Frontend API Client Convention

Create a shared API client under:

```text
src/api/client.ts
```

The client should:

- use `import.meta.env.VITE_API_BASE_URL`
- set `credentials: "include"` by default
- send JSON request bodies where appropriate
- parse JSON responses
- handle empty responses safely
- parse the backend standard error response shape
- throw typed/safe frontend errors
- avoid leaking raw backend stack traces or sensitive fields
- avoid storing session tokens directly

Recommended frontend API folder structure:

```text
src/api/
  client.ts
  errors.ts
  authApi.ts
  dashboardApi.ts
  launcherApi.ts
  billingApi.ts
  settingsApi.ts
  rewardsApi.ts
  supportApi.ts
  integrationsApi.ts
```

---

## Frontend Migration Strategy

Do not remove static data files immediately.

Use static data files as reference/fallback while each page is migrated.

Current static frontend data lives under:

```text
src/data/
```

Preferred migration pattern:

```text
1. Add an API module for the backend capability.
2. Add TypeScript DTO types matching backend responses.
3. Add mapper functions from backend DTOs to current component prop shapes.
4. Update the page/container component to fetch backend data.
5. Preserve existing section/presentation components where possible.
6. Add loading, empty, and error states.
7. Confirm the API call in the browser Network tab.
8. Remove or reduce static-data dependency only after the page works with backend data.
```

Avoid rewriting stable visual components just to match backend DTO names. Prefer adapter/mapper functions.

Example:

```text
Backend DTO
→ frontend API response type
→ mapper function
→ existing component prop shape
→ existing UI component
```

---

## First Integration Milestone

The first full-stack proof should be:

```text
1. User submits login form.
2. Frontend calls POST /api/v1/auth/login.
3. Backend sets zeptalytic_session cookie.
4. Frontend calls GET /api/v1/auth/session.
5. Protected /app route allows access.
6. Dashboard calls GET /api/v1/dashboard/summary.
7. Dashboard renders backend-backed data.
```

This proves:

```text
browser
→ React form
→ frontend API client
→ FastAPI backend
→ cookie auth
→ protected backend route
→ frontend render
```

Do not start with billing write actions or subscription modification flows. Start with login/session and dashboard read behavior.

---

## Initial Backend Endpoints

Known first-slice endpoints include:

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/session

GET /api/v1/dashboard/summary
GET /api/v1/launcher/products

GET /api/v1/billing/snapshot
GET /api/v1/billing/subscriptions
GET /api/v1/billing/payment-methods
GET /api/v1/billing/transactions

POST /api/v1/billing/checkout
POST /api/v1/billing/subscription-change
POST /api/v1/billing/subscription-cancel
POST /api/v1/billing/subscription-restart
POST /api/v1/billing/promo-code/validate
POST /api/v1/billing/promo-code/apply
```

Keep this list synchronized with backend OpenAPI output.

To export the current backend route list:

```bash
poetry run python - <<'PY'
from app.main import app

for route in app.routes:
    path = getattr(route, "path", "")
    if not path.startswith("/api"):
        continue

    methods = ",".join(sorted(route.methods or []))
    name = getattr(route, "name", "")
    print(f"{methods:25} {path:80} {name}")
PY
```

To export OpenAPI:

```bash
poetry run python - <<'PY'
import json
from app.main import app

schema = app.openapi()

with open("backend_openapi.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2, default=str)

print("Wrote backend_openapi.json")
print(f"Route count: {len(schema.get('paths', {}))}")
for path in sorted(schema.get("paths", {}).keys()):
    print(path)
PY
```

---

## Frontend Static-Data Replacement Order

Recommended order:

```text
1. Auth/session foundation
2. Dashboard
3. Launcher
4. Billing read views
5. Billing actions
6. Settings/profile/address/preferences
7. Rewards/objectives
8. Support/status/announcements
9. Discord integration
10. Full-stack regression/smoke pass
```

This order matters because later authenticated pages depend on the auth/session foundation.

---

## Frontend Auth Integration Rules

The login page should call:

```text
POST /api/v1/auth/login
```

The signup page should call:

```text
POST /api/v1/auth/signup
```

The app shell/session provider should call:

```text
GET /api/v1/auth/session
```

Logout should call:

```text
POST /api/v1/auth/logout
```

Frontend protected routes should use safe auth state returned from the backend, not raw cookies or tokens.

The frontend should support at least these auth UI states:

```text
idle
submitting
loading session
authenticated
unauthenticated
email verification required
error
```

---

## Dashboard Integration Rules

The dashboard page should call:

```text
GET /api/v1/dashboard/summary
```

The backend response should be mapped into the current dashboard UI sections:

```text
launcher cards
billing snapshot
rewards progress
system statuses
notification/feed items
```

Preserve the current dashboard layout where possible.

Do not let the dashboard directly calculate commercial truth. It should render what the backend returns.

---

## Launcher Integration Rules

The launcher page should call:

```text
GET /api/v1/launcher/products
```

The launcher should respect backend-provided access state:

```text
can_launch
launch_url
access_state
blocked_reason
status_message
pay_projection
```

If `can_launch` is false, the frontend should not navigate to the product launch URL. It should display the backend-provided blocked reason or status message.

Discord linkage must not affect launcher eligibility.

---

## Billing Integration Rules

Billing read views should call:

```text
GET /api/v1/billing/snapshot
GET /api/v1/billing/subscriptions
GET /api/v1/billing/payment-methods
GET /api/v1/billing/transactions
```

Billing action initiators should call:

```text
POST /api/v1/billing/checkout
POST /api/v1/billing/subscription-change
POST /api/v1/billing/subscription-cancel
POST /api/v1/billing/subscription-restart
POST /api/v1/billing/promo-code/validate
POST /api/v1/billing/promo-code/apply
```

Do not collect raw card details directly in this frontend integration phase.

Do not store full card numbers, CVV/CVC, raw wallet keys, or raw provider credentials.

Payment method management should be handled through backend/Pay-supported flows.

---

## Settings/Profile/Address Integration Rules

Settings integration should preserve current UI expectations:

```text
username is static
email can be edited
phone can be edited
timezone can be edited
profile image/avatar can be displayed
Discord username/status can be displayed
notification preferences can be edited
mailing/billing addresses can be managed
security/session state can be displayed
```

Address forms should respect backend-supported fields and should not invent column names or payload fields without checking backend schemas/OpenAPI.

---

## Rewards/Objectives Integration Rules

Rewards and objectives frontend APIs should remain read-oriented.

The frontend must not directly award:

```text
points
rewards
badges
entitlements
milestones
objective completions
```

Reward writes should come from:

```text
backend jobs
admin/internal operations
product-originated events
Pay-derived events
referral qualification events
```

Frontend may call backend endpoints for safe presentation actions such as:

```text
mark notification viewed
skip/dismiss notification
```

only where supported by backend APIs.

---

## Support/Status/Announcements Integration Rules

Support frontend integration should cover:

```text
support ticket creation
support modal submission
support categories/request types
priority selection
service status display
announcement/news feed display
safe attachment metadata where supported
```

Do not build an admin support dashboard unless explicitly scoped.

File uploads should follow backend limits and validation rules.

---

## Discord Integration Rules

Discord integration should be limited to:

```text
display current Discord linkage state
initiate Discord OAuth/link flow
show linked Discord username/status
unlink where supported
```

Discord linkage must not affect:

```text
rewards
points
badges
entitlements
launcher eligibility
product access
```

Do not expose Discord internal user IDs in normal frontend display unless explicitly required and safe.

---

## Spec Generation Rules

Spec generation must not arbitrarily limit specs to 3–4 implementation items.

Each spec should include the number of items required by the workstream, provided each item is:

- focused
- buildable
- testable
- reviewable
- scoped to the current repo
- clear about acceptance criteria

A spec may have 3 items, 6 items, 10 items, or more if the scope requires it.

The constraint is not item count. The constraint is item quality.

Avoid artificially merging unrelated work just to keep the item count small. Also avoid splitting trivial changes into unnecessary micro-items.

Do not mark an item complete unless the acceptance criteria are satisfied and verification commands pass.

---

## Backend Verification

Backend implementation items should normally run:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

If a backend test failure is unrelated or pre-existing, document it clearly and do not mark the item complete unless the spec explicitly allows blocked completion.

---

## Frontend Verification

Frontend implementation items should normally run:

```bash
npm run build
```

If lint is clean and configured, also run:

```bash
npm run lint
```

If lint is blocked by pre-existing issues, document the blocker instead of silently skipping it.

For browser verification, run:

```bash
npm run dev
```

and confirm calls in the browser Network tab.

---

## Full-Stack Local Smoke Path

Use this as the first serious full-stack check:

```text
1. Start backend:
   poetry run uvicorn app.main:app --reload --port 8000

2. Start frontend:
   npm run dev

3. Open frontend:
   http://localhost:5173

4. Submit login or signup.

5. Confirm backend sets the zeptalytic_session cookie.

6. Confirm frontend calls:
   GET /api/v1/auth/session

7. Navigate to:
   /app/dashboard

8. Confirm frontend calls:
   GET /api/v1/dashboard/summary

9. Confirm dashboard renders backend-backed data.

10. Confirm there are no browser CORS errors.
```

---

## Guardrails

- Do not redesign stable frontend pages during integration unless required.
- Do not duplicate Pay commercial rules in the frontend or parent backend.
- Do not collect raw card details directly in the frontend during this pass.
- Do not expose raw session tokens, password hashes, 2FA secrets, Discord internal IDs, raw payment credentials, or backend stack traces.
- Do not allow frontend calls to directly award rewards, points, badges, or entitlements.
- Keep backend and frontend work in separate repo-specific specs.
- Use backend schemas/OpenAPI as the source of truth for frontend DTOs.
- Prefer DTO mappers instead of rewriting existing visual components.
- Preserve static data files until each page has a confirmed backend-backed replacement.