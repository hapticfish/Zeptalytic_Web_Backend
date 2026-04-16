# Codex rules for Zeptalytic Web Backend (read before doing work)

## Purpose of this repo
A FastAPI-based parent-site backend for the Zeptalytic ecosystem. This service owns:
- auth / sessions / account profile / settings / addresses
- support tickets / attachments / announcements / service status
- rewards / objectives / badges / points / progress presentation
- browser-facing aggregation for dashboard / launcher / billing
- parent-side integration contracts to the Zeptalytic Pay service

## Non-negotiable rules (always)
- Do NOT add new dependencies unless John explicitly approves.
- Do NOT delete files unless the active implementation plan explicitly says to.
- Prefer small, safe, reviewable changes.
- Keep parent-site ownership separate from Pay ownership.
- Do not move commercial/billing truth into this repo.
- Do not dump unrelated models into one generic file.
- Default rule: one table/model per file unless a tightly-coupled pair is explicitly justified.
- If sensible directories do not exist, create them rather than collapsing concerns into one file.

## Locked architecture boundaries
- Pay remains source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, and risk.
- Parent backend owns auth/settings/addresses/support/rewards/announcements/testimonials/dashboard aggregation.
- Stripe.js / Elements + SetupIntents is the intended payment-method update path.
- Discord current active linkage is modeled on `profiles`, with preserved historical connection state tracked separately.
- The docs under `docs/architecture/` are durable reference material; do not contradict them without updating the relevant decision record first.

## Required rehydrate behavior (every run)
Read these first:
1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` (if present)
4. `progress/progress.txt` (last 1–3 entries)
5. Determine the active spec from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the active spec file
7. Read these architecture references when relevant:
   - `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
   - `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
   - `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
   - `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`
   - `docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` is the canonical source for parent-site vocabulary, enum values, and status names.
   - `docs/architecture/Discord_Integration_Decision_Record.md`
   - `docs/architecture/Rewards_Objectives_Badges_Domain_Decision_Record.md`
   - `docs/architecture/Rewards_Objectives_Badges_Data_Model_Reference.md`
   - `docs/architecture/Rewards_Objectives_Badges_UI_Interaction_Reference.md`
   - `docs/architecture/Discord_Rewards_Workstream_Sequence.md`
8. Run `git status`
9. Run `git log -5 --oneline`

## Search-before-edit rule
Before changing code, search the repo for:
- existing router/service/model/repository patterns
- existing tests that already cover the same surface
- existing migration/bootstrap conventions
Do not assume something is missing until you search.

## Test requirement
Do not claim done until the authoritative suite passes:
- `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`

If the command cannot run, record the blocker in `progress/progress.txt` and stop the iteration.

## Durable artifact rule
When a run is successful:
- update the active spec only for the completed item
- append a new entry to `progress/progress.txt`
- keep progress append-only
