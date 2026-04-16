You are Codex working in this repository. Run ONE build iteration only.

Follow this exact routine every run:

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

## 1) Pick ONE item to work on
- Choose exactly one item in the ACTIVE SPEC where `passes=false`
- Prefer earlier items first unless a later item is clearly blocking

## 2) Search before editing (mandatory)
- Use: `git ls-files`, `git grep`, `rg`, `find`, `grep -R`
- Summarize what you found BEFORE changing anything:
  - file paths
  - key functions / classes / models / schemas / repositories involved
  - current wiring / import registration / router registration
  - existing tests that already cover the target area
- Do not assume something is missing until you search for it

## 3) Implement the smallest safe change
- Keep changes small and localized
- Match repository patterns and architecture docs
- Do not add dependencies unless John explicitly approved them
- Do not delete files unless the active plan/spec explicitly says to
- Do not guess unresolved business rules; leave TODO markers only when the decision record has not locked them yet

### Model/layout rules (mandatory)
- Do NOT dump unrelated tables into one file
- Use one table/model per file by default unless the spec explicitly says otherwise
- Create sensible directories when needed instead of collapsing concerns into a generic module
- Update import / metadata / Alembic discovery registration cleanly

### Domain-specific guardrails for this workstream
- For Discord identity correction:
  - do not overbuild OAuth/token features not in scope
  - current active linkage belongs on `profiles`
  - preserve historical state separately
- For rewards work:
  - treat milestone objectives and general objectives consistently with the approved architecture docs
  - keep the data model aligned to the locked vocabulary decision records
  - keep milestone/objective/reward presentation queue behavior consistent with the UI interaction reference

## 4) Tests (required)
- Add or update tests for the behavior / structure you changed
- For structural refactors, add regression tests that prove the intended layout and registration still work
- If tests fail, fix them in this same iteration; do not move on while tests are failing

## 5) Run the authoritative test suite (must be green)
Run:
`docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`

If Docker is unavailable or the command cannot run:
- append a blocker entry to `progress/progress.txt`
- do NOT mark any spec item complete
- print exactly: `ITERATION_BLOCKED`
- stop the iteration

If the topology or command is missing/unusable:
- append the blocker and the repo-reality evidence to `progress/progress.txt`
- do NOT mark any spec item complete
- print exactly: `ITERATION_BLOCKED`
- stop the iteration

## 6) Update durable artifacts (only when NOT blocked)
- Update only the ACTIVE SPEC item you fully completed:
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
