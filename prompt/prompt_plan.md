You are Codex working in this repository. This run is PLANNING ONLY.

Rules:
- Do NOT modify runtime application code in this run.
- Allowed changes: `specs/`, `docs/`, `README.md`, `PROMPT.md`, `prompt/*`, `scripts/*`, `IMPLEMENTATION_PLAN.md`, `progress/*`, and other planning-only files.
- Keep changes small and reviewable.

Follow this exact routine every planning run:

## 0) Rehydrate context (mandatory)
- Read: `AGENTS.md`
- Read: `IMPLEMENTATION_PLAN.md`
- Read: `PROMPT.md` (if present)
- Read: `progress/progress.txt` (last 1–3 entries)
- Determine the ACTIVE SPEC from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
- Read the ACTIVE SPEC file
- Rehydrate the architecture docs named in `AGENTS.md` / `IMPLEMENTATION_PLAN.md`
- Run: `git status`
- Run: `git log -5 --oneline`

## 1) Confirm repo reality before editing
- Search before editing and summarize current related code, file layout, wiring, and tests.
- When model-file structure is in scope, inspect at minimum:
  - `app/db/models/`
  - metadata registration paths
  - Alembic discovery/import paths
- When verification/testing is in scope, inspect at minimum:
  - `tests/`
  - `docker-compose.test.yml`
  - `alembic/`
  - current DB/bootstrap fixtures or setup helpers
- Do not assume the current workstream still matches repo reality until you verify it.

## 2) Planning output
- Refine the ACTIVE SPEC if repo reality or blocker history requires it.
- Keep items small enough for one build iteration each.
- Keep the next queued spec ready, but do NOT make it active unless the current workstream has materially changed or is no longer the correct next target.
- Record blockers, command drift, topology drift, or architecture-doc drift in repo docs when relevant.
- Preserve the split between Discord correction, rewards schema, rewards verification, and rewards API/application unless repo reality forces a different sequence.

## 3) Durable artifacts
- Append a planning entry to `progress/progress.txt`
- If docs/specs are refined, keep changes small and reviewable
- If tests are required for a docs-only planning run, use the authoritative docker command
- If the topology is missing or unusable, record the blocker and stop safely
- Commit only planning/doc files if tests are green

End with:
`PLAN_DONE`
