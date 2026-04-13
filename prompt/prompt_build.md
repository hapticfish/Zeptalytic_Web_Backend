You are Codex working in this repository. Run ONE iteration only.

Follow this exact routine every run:

## 0) Rehydrate context (mandatory)
- Read: `AGENTS.md`
- Read: `IMPLEMENTATION_PLAN.md`
- Read: `PROMPT.md` (if present)
- Read: `progress/progress.txt` (last 1–3 entries)
- Determine the ACTIVE SPEC FILE:
  - In `IMPLEMENTATION_PLAN.md`, find the line that starts with: `Active spec:`
  - The file path on that line is the ACTIVE_SPEC
  - If not found, check `PROMPT.md` for an `Active spec:` line
  - If still not found, STOP and report that Active spec is missing
- Read: the ACTIVE_SPEC file
- Read the architecture docs referenced by `IMPLEMENTATION_PLAN.md` and the ACTIVE_SPEC
- Run: `git status`
- Run: `git log -5 --oneline`

## 1) Pick ONE item to work on
- Choose exactly one item in the ACTIVE_SPEC where `passes=false`.
- Prefer earlier items first unless a later item is blocking.

## 2) Search before editing (mandatory)
- Use: `git ls-files`, `git grep`, `rg`, `find`, `grep -R` to locate existing related code.
- Summarize what you found BEFORE changing anything:
  - file paths
  - key functions/classes
  - current wiring (what is imported/registered vs just “present”)
  - test coverage that already exists
- Do not assume something is missing until you search.

## 3) Implement the smallest safe change
- Keep changes small and localized.
- Match existing architecture and repository patterns (routers/services/integrations/repos/models/schemas/clients/workers).
- Do not add new dependencies unless John approved.
- Do not delete files unless `IMPLEMENTATION_PLAN.md` explicitly says to.
- Keep container deployment in mind (env vars, settings, no machine paths).
- Respect the ownership docs:
  - do not duplicate Pay commercial truth in parent DB
  - do not introduce raw payment instrument storage
  - keep parent-owned domains in parent systems
- If the spec requires product/business decisions you cannot infer:
  - write TODO markers
  - point to where John can fill the decision (spec, PRD, docs, or constants/config)
  - implement the scaffolding so the decision can be plugged in cleanly.

## 4) Tests (required)
- Add or update tests for the behavior you changed.
- For security-related changes:
  - add tests for invalid inputs (at least 2 realistic bad cases when applicable)
  - ensure auth, ownership boundaries, and unsafe-input denial paths have direct tests when relevant
- Avoid tests that require external network calls (mock provider/integration clients).

## 5) Run the authoritative test suite (must be green)
Run:
`docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test`

If docker is unavailable or the command cannot run:
- record the blocker in `progress/progress.txt`
- do NOT commit changes you cannot test
- stop the iteration (print `ITERATION_BLOCKED`)

If tests fail:
- fix them in this iteration
- do not move on while tests are failing

## 6) BLOCKER RULE (mandatory)
A run is "blocked" if you cannot safely complete the chosen spec item (examples: missing unapproved dependency, missing required runtime capability, docker cannot run, etc.).

If blocked:
- Append a `progress/progress.txt` entry describing the blocker and what decision/action is needed next.
- DO NOT set `passes=true` for any spec item.
- DO NOT set `completed_at/completed_by` for any spec item.
- DO NOT check off items in `IMPLEMENTATION_PLAN.md`.
- You may commit ONLY the `progress/progress.txt` entry (and other small doc-only changes if strictly necessary), but only if tests are green or the blocker is exactly `docker unavailable`.
- Print exactly: `ITERATION_BLOCKED`

## 7) Update durable artifacts (only when NOT blocked)
- Update the ACTIVE_SPEC:
  - set `passes=true` ONLY for the item you fully completed and verified
  - set `completed_at` to an ISO 8601 timestamp with timezone, generated from system clock
  - set `completed_by="codex"`
- Update `IMPLEMENTATION_PLAN.md` checkboxes if needed
- Append an entry to `progress/progress.txt` including:
  - Date/time:
    - MUST be a full ISO 8601 timestamp with timezone
    - Generate it from the system clock (do not type it manually)
  - Updated Files:
    - Generate from: `git diff --name-status HEAD`
    - Include all `M` entries as full repo-relative paths
  - New Files:
    - Include all `A` entries as full repo-relative paths
  - Removed Files:
    - Include all `D` entries as full repo-relative paths
  - what you found (search summary)
  - what changed (files)
  - tests run + results
  - next step
  - Commit:
    - If a commit was created, set to `git rev-parse --short HEAD`
    - If no commit, write: `none (no commit created)`

### Append-to-end rule for progress/progress.txt (MANDATORY)
- The new `## Iteration entry` MUST be appended at the very end of `progress/progress.txt` (EOF).
- Do NOT insert it earlier in the file.
- After writing, verify it is at EOF by running:
  - `tail -n 60 progress/progress.txt`
  and confirm the new entry is visible in that tail output.

## 8) Commit (only if tests are green and NOT blocked)
- Commit only after the docker test suite passes.
- If tests are green and there are any file changes, you must commit.
- Commit message:
  - `<spec-id>: <short description>` (use the spec item id, e.g. `pdb-020`)

### Windows PowerShell note (MANDATORY)
- Do NOT chain commands with `&&` in PowerShell.
- Run `git add ...` and `git commit ...` as separate commands.

## 9) Stop condition
- If blocked, print exactly:
ITERATION_BLOCKED
- If every item in the ACTIVE_SPEC has `passes=true`, print exactly:
ALL_DONE
- Otherwise print exactly:
ITERATION_DONE
