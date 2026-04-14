You are Codex working in this repository. Run ONE iteration only.

Follow this exact routine every run:

## 0) Rehydrate context (mandatory)
- Read: `AGENTS.md`
- Read: `IMPLEMENTATION_PLAN.md`
- Read: `PROMPT.md` (if present)
- Read: `progress/progress.txt` (last 1–3 entries)
- Determine the ACTIVE SPEC FILE from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
- Read the ACTIVE SPEC file
- Run: `git status`
- Run: `git log -5 --oneline`

## 1) Pick ONE item to work on
- Choose exactly one item in the ACTIVE_SPEC where `passes=false`
- Prefer earlier items first unless a later item is blocking

## 2) Search before editing (mandatory)
- Use `git ls-files`, `git grep`, `rg`, `find`, `grep -R`
- Summarize what you found BEFORE changing anything:
  - file paths
  - key functions/classes/models
  - current wiring/import registration
  - existing tests

## 3) Implement the smallest safe change
- Keep changes localized
- Match repository patterns
- Do not add dependencies unless John approved them
- Do not delete files unless the plan/spec explicitly says to
- When touching model files:
  - do NOT dump unrelated tables into one file
  - place one table/model per file by default
  - create sensible directories if they do not exist
  - update import registration cleanly

## 4) Tests (required)
- Add or update tests for the behavior/structure you changed
- For structural refactors, add regression tests that prove the intended layout/registration still works

## 5) Run the authoritative test suite (must be green)
Run:
`docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`

If docker is unavailable or the command cannot run:
- record the blocker in `progress/progress.txt`
- do NOT mark the spec item complete
- stop the iteration with exactly:
`ITERATION_BLOCKED`

If tests fail:
- fix them in this same iteration
- do not move on while tests are failing

## 6) Update durable artifacts (only when NOT blocked)
- Update the ACTIVE_SPEC item you completed:
  - `passes=true`
  - `completed_at=<ISO 8601 timestamp with timezone>`
  - `completed_by="codex"`
- Update `IMPLEMENTATION_PLAN.md` checkbox if needed
- Append an iteration entry to `progress/progress.txt`
- Verify the new entry is appended at EOF
- Commit only if tests are green

If the active spec is fully complete, end with:
`ALL_DONE`
Otherwise end with:
`ITERATION_DONE`
