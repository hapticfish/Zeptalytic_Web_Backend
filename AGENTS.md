# Codex rules for Zeptalytic Web Backend (read before doing work)

## Purpose of this repo
A FastAPI-based parent-site backend for Zeptalytic. This service is the browser-facing API for:
- auth and account management
- profile/settings/integrations
- addresses
- support tickets and attachments
- rewards/objectives
- announcements/status/testimonials
- dashboard/launcher aggregation
- Pay-derived read models for billing/access display

It is NOT the source of truth for commercial billing lifecycle logic. The Zeptalytic Pay Service remains authoritative for:
- pricing truth
- checkout/payment initiation
- orders/payments/refunds
- subscriptions/entitlements
- disputes/risk
- provider-facing webhook/finality logic

## Non-negotiable rules (always)
- Do NOT add new dependencies (production or dev) unless John explicitly approves.
- Do NOT delete files unless the current IMPLEMENTATION_PLAN.md explicitly says to.
- Prefer small, safe, reviewable changes.
- Follow the existing project structure and separation-of-concerns conventions.
- Do not break existing behavior unless the active spec requires it.

## Architecture boundary rules (always)
- Parent backend is the only browser-facing API boundary.
- Pay remains the commercial source of truth.
- Parent-owned domains must stay in this repo: auth, settings, addresses, support, rewards, announcements, testimonials, dashboard aggregation.
- Pricing comparison matrices and marketing copy are parent metadata, not Pay truth.
- Card data must never pass through this service; Stripe.js / Elements + SetupIntents is the intended card-update path.

## File organization rules (always)
- Do NOT dump unrelated models into one file.
- One SQLAlchemy model/table per file by default.
- Group files into sensible directories when the project needs it; create missing directories rather than collapsing concerns into a generic file.
- Acceptable model layout examples:
  - `app/db/models/accounts.py`
  - `app/db/models/profiles.py`
  - `app/db/models/support_tickets.py`
  - `app/db/models/billing/payment_summaries.py`
- Shared mixins, enums, or helpers may live in separate support files, but table models should remain individually readable.
- The same principle applies to schemas, services, repositories, and routers: split by responsibility.

## Vocabulary decisions (locked)
Use the canonical vocabularies from:
- `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md`

Do not invent alternate status values during implementation.

## Required “rehydrate context” behavior (every run)
1) Read these files first:
   - `AGENTS.md`
   - `IMPLEMENTATION_PLAN.md`
   - `PROMPT.md` (if present)
   - `progress/progress.txt` (last 1–3 entries)
2) Determine the ACTIVE SPEC FILE from `IMPLEMENTATION_PLAN.md` (or `PROMPT.md` fallback).
3) Read the ACTIVE SPEC file.
4) Before editing, search the repo for existing related code.
   - Do not assume something is missing.
   - Summarize what you found before changing anything.
   - Use commands that exist in the repo environment: `git grep`, `find`, `rg`, `grep -R`, `python -c`.

## Test requirements (must be followed)
- Do not claim “done” until tests pass.
- The authoritative full test run for this repo is:
  - `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
- If docker is unavailable or the command cannot run because required topology files are missing:
  - record the blocker in `progress/progress.txt`
  - do NOT mark the spec item complete
  - stop the iteration with `ITERATION_BLOCKED`

## Git/branch rules
- Work on a feature branch, not main/master.
- Commit only when tests are green.
- One commit per meaningful step.
- Use short commit messages:
  - `pdb-020: add account/auth tables`
  - `mdl-030: split support models into per-file modules`
  - `dbv-040: add metadata and migration verification tests`
