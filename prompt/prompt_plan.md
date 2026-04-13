You are Codex working in this Zeptalytic Website Backend / Parent Site repository.

Your job in this run is PLANNING ONLY.

## Scope guardrails (mandatory)
- Do NOT add new dependencies (production or dev) unless John explicitly approves.
- Do NOT delete files unless the current IMPLEMENTATION_PLAN.md explicitly says to.
- Do NOT modify application/runtime code in this run (routers/services/models/workers/clients).
  - Allowed changes: `specs/`, `docs/`, `README.md`, `PROMPT.md`, `prompt/*`, `scripts/*`, `IMPLEMENTATION_PLAN.md`, `progress/*`.
- Keep changes small and reviewable.

## 0) Rehydrate context (mandatory)
1) Read `AGENTS.md` and obey it.
2) Read `IMPLEMENTATION_PLAN.md`.
3) Read `PROMPT.md` (if present).
4) Read `progress/progress.txt` (last 1–3 entries).
5) Determine the ACTIVE SPEC FILE:
   - In `IMPLEMENTATION_PLAN.md`, find the line that starts with: `Active spec:`
   - The file path on that line is the ACTIVE_SPEC
   - If not found, check `PROMPT.md` for an `Active spec:` line
   - If still not found, STOP and report that Active spec is missing
6) Read the ACTIVE_SPEC file.
7) Read the architecture docs referenced in `IMPLEMENTATION_PLAN.md`.
8) Run: `git status`
9) Run: `git log -5 --oneline`

## 1) Confirm authoritative commands (from repo docs)
- Full tests:
  `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`
- API:
  `docker compose up --build api`
- Migrations:
  `docker compose run --rm migrate`

If these differ from repo reality, update repo docs accordingly (planning/doc files only).
If the compose files or named services do not exist yet, record that drift explicitly and refine the active spec so the next build slice creates or aligns the container topology before later schema work.

## 2) Durable artifacts check
Ensure these exist (create if missing) and are internally consistent:
- `IMPLEMENTATION_PLAN.md` (must include Active spec)
- `progress/progress.txt`
- `prompt/prompt_build.md`
- `prompt/prompt_plan.md`
- `PROMPT.md` (if used)
- `scripts/ralph-loop.sh`
- `specs/` (directory exists, and ACTIVE_SPEC exists)
- `docs/architecture/` controlling docs for the active workstream

## 3) Planning output for the active spec
- Summarize current scope and what the next spec/workstream needs to cover.
- Identify gaps/risks and required doc/spec changes.
- Propose the next spec items (ids, descriptions, expected_paths, steps, pass criteria).
- If a new spec file is needed:
  - create it under `specs/`
  - update `IMPLEMENTATION_PLAN.md` `Active spec:` to point to it
  - ensure the plan has a small-step checklist that maps to the spec items

Planning expectations:
- Search before editing and summarize actual current repo wiring, DB/bootstrap surfaces, auth/config surfaces, and existing tests.
- Treat runtime entrypoints and registered modules as the source of truth; do not infer active code paths from file names alone.
- When DB/bootstrap work is in scope, inspect the current app package layout, model registration path, Alembic env wiring, metadata imports, and docker migration path before proposing spec or plan changes.
- When auth/config work is in scope later, inspect `app/api/deps.py` and `app/settings.py` before proposing spec changes.
- Check example env files and compose files if config or migration topology is in scope so drift is captured early.
- Prefer refining the current active spec unless the workstream has materially changed.
- Keep proposed items small enough that a later build run can complete one item per iteration.
- Record any command or topology drift in `README.md` and/or `IMPLEMENTATION_PLAN.md`.
- Do not modify runtime application code in a planning-only run.

## 4) Progress + commit (required)
At the end:
- Append a short entry to `progress/progress.txt` describing what was created/updated.
- For the progress entry, set `Date/time` to a full ISO 8601 timestamp with timezone.
  - Generate it from the system clock (do not type it manually).
- Updated/New/Removed files:
  - Generate from: `git diff --name-status HEAD`
  - List `M/A/D` entries with full repo-relative paths.
- Make a git commit that only changes planning/spec/prompt/script/doc files.
- If unrelated non-planning files are already dirty, do not revert them; record the current diff accurately in progress and stage only the allowed planning/doc files you changed for the commit.
- After committing, add: `Commit: <short hash>` where `<short hash>` is from `git rev-parse --short HEAD`.

Print exactly:
PLAN_DONE
