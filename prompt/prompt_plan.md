You are Codex working in this repository. This run is PLANNING ONLY.

Rules:
- Do NOT modify runtime application code in this run.
- Allowed changes: `specs/`, `docs/`, `README.md`, `PROMPT.md`, `prompt/*`, `scripts/*`, `IMPLEMENTATION_PLAN.md`, `progress/*`, and other planning-only files.
- Keep changes small and reviewable.

Routine:
1) Rehydrate context:
   - Read `AGENTS.md`
   - Read `IMPLEMENTATION_PLAN.md`
   - Read `PROMPT.md` if present
   - Read the last 1–3 entries of `progress/progress.txt`
   - Determine the ACTIVE SPEC from `IMPLEMENTATION_PLAN.md` (`Active spec:`)
   - Read the ACTIVE SPEC
   - Run `git status`
   - Run `git log -5 --oneline`

2) Confirm repo reality:
   - Search before editing and summarize current related code, file layout, and tests.
   - When model-file structure is in scope, inspect `app/db/models/`, `app/db/base.py`, `alembic/env.py`, and model import registration.
   - When verification/testing is in scope, inspect `tests/`, `docker-compose.test.yml`, `alembic/`, and any current DB bootstrap fixtures.

3) Planning output:
   - Refine the active spec if needed.
   - Keep items small enough for one build iteration each.
   - Keep the next queued spec ready but do not make it active unless the current workstream has materially changed.
   - Record blockers and command/topology drift in repo docs.

4) Durable artifacts:
   - Append an entry to `progress/progress.txt`
   - If tests are required for a docs-only planning run, use the authoritative docker command; if the topology is missing or unusable, record the blocker and stop safely.
   - Commit only planning/doc files if tests are green.

End with `PLAN_DONE` if the planning iteration is complete.
