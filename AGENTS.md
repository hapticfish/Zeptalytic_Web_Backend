# Codex rules for Zeptalytic Website Backend / Parent Site repo (read before doing work)

## Purpose of this repo
A FastAPI parent-site backend for Zeptalytic using PostgreSQL + Alembic migrations, container-first workflow,
and integration with the existing Zeptalytic Pay Service.

This repo owns browser-facing account/site functionality such as:
- auth and account security
- profile/settings/integrations
- addresses
- support tickets and attachments
- announcements/status/testimonials
- rewards/objectives (when in scope)
- parent-side read models / projections derived from Pay

It does **not** replace the Pay service.

## Non-negotiable rules (always)
- Do NOT add new dependencies (production or dev) unless John explicitly approves.
- Do NOT delete files unless the current IMPLEMENTATION_PLAN.md explicitly says to.
- Prefer small, safe changes. Avoid big rewrites unless the plan requires it.
- Follow the existing project structure and patterns (routers / services / repositories / models / schemas / workers / clients).
- Do not break existing behavior unless the spec requires it.
- Treat the docs under `docs/architecture/` as controlling references for ownership and implementation boundaries.

## Architecture rules (always)
- The parent backend is the only browser-facing API.
- The Pay service remains the source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, and provider webhook finality.
- Do NOT duplicate Pay billing truth in the parent DB.
- Parent-side projection/read-model tables are allowed for UX and aggregation, but they are not authoritative commercial truth.
- Stripe card handling uses Stripe.js / Elements + SetupIntents so raw card data does not pass through parent servers.
- Coinbase is treated as a checkout/payment rail, not a Stripe-like saved-card subsystem.
- Promo code logic belongs in Pay unless John explicitly changes that decision.

## Security expectations (always)
- Do not hardcode secrets or credentials. Do not commit secrets.
- Treat all external input as untrusted (request bodies, headers, attachment uploads, OAuth payloads, callback params).
- Validate and normalize inputs where appropriate and fail safely with clear errors.
- Do not log raw secrets, tokens, password-reset links, verification tokens, or unsafe attachment details.
- Avoid common vulnerabilities when relevant:
  - insecure auth/session handling
  - CSRF/session misuse if cookie auth is introduced
  - file upload abuse
  - injection (SQL/header/path)
  - authorization bugs / cross-account access
  - insecure object reference patterns
- Add security-relevant tests when it makes sense.

## Code quality expectations (always)
- Production-grade code is the goal.
- Keep code split into clear parts (routers / services / repositories / models / schemas / workers / clients).
- Keep changes consistent with container deployment:
  - no machine-specific paths
  - use env vars and existing settings patterns
  - do not assume local-only resources
- Search before editing; do not assume something is missing because you have not found it yet.

## Required rehydrate behavior (every run)
1) Read these files first:
   - `AGENTS.md`
   - `IMPLEMENTATION_PLAN.md`
   - `PROMPT.md` (if present)
   - `progress/progress.txt` (last 1–3 entries)
2) Resolve the ACTIVE SPEC from `IMPLEMENTATION_PLAN.md` (fallback to `PROMPT.md` if needed).
3) Read the ACTIVE SPEC file.
4) Read the relevant architecture docs for the active workstream, especially:
   - `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
   - `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
   - `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
   - any more specific architecture doc named by the active spec
5) Before editing, search the repo for existing related code.
   - Summarize what you found (file paths + key functions/classes) before changing anything.
   - Use tools that always exist: `git grep`, `find`, `python -c`, `grep -R`, `git ls-files`.

## Test requirements (must be followed)
- Do not claim “done” until tests pass.
- The authoritative full test run for this repo should be treated as:
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
- If the current repo reality uses a different authoritative command, update docs/plan/prompt files first in a planning run.
- If docker is not available in the current environment, stop and record the blocker in `progress/progress.txt`.
- Do NOT commit changes that you cannot test unless the blocker rule in the build prompt explicitly allows it.

## Internet usage (only when needed)
- If online info is needed, prefer official documentation.
- Record sources used in `progress/progress.txt` under `Sources used`.

## Git/branch rules
- Work on a feature branch, not `main` / `master`.
- Commit only when tests are green.
- One commit per meaningful step (small and reviewable).
- Commit message format:
  - `<spec-id>: <short description>`

## Parent-site implementation reminders
- Pricing page display must not become authoritative pricing truth in frontend or parent DB.
- Dashboard billing snapshot and launcher access must derive from Pay truth or Pay-derived parent projections.
- Support, settings, addresses, rewards, announcements, and testimonials belong to the parent site, not Pay.
- If a UI feature already exists visually, do not assume the backend already exists; consult the ownership docs and current repo search results.
