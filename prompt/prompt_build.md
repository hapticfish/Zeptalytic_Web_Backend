You are Codex working in this repository. Run ONE build iteration only.

Follow this exact routine every run:

## 0) Rehydrate context mandatory

Read:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. Determine the ACTIVE SPEC from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the ACTIVE SPEC file
7. Read `specs/next_phase_spec_sequence.json`
8. Rehydrate the architecture docs named in `AGENTS.md` / `IMPLEMENTATION_PLAN.md`
9. Read architecture docs relevant to the ACTIVE SPEC.
10. Run `git status`
11. Run `git log -5 --oneline`

## 1) Pick ONE item to work on

Choose exactly one item in the ACTIVE SPEC where:

```json
"passes": false
```

Prefer earlier items first unless a later item is clearly blocking.

Do not work on more than one item in a single build iteration unless the active spec item itself explicitly requires a tiny companion change.

## 2) Search before editing mandatory

Use:

```bash
git ls-files
git grep
rg
find
grep -R
```

Summarize what you found BEFORE changing anything:

- file paths
- key functions/classes/models/schemas/repositories/services involved
- current wiring/import registration/router registration
- existing tests that already cover the target area
- gaps the current spec item should address

Do not assume something is missing until you search for it.

## 3) Implement the smallest safe change

- Keep changes small and localized.
- Match repository patterns and architecture docs.
- Do not add dependencies unless John explicitly approved them.
- Do not delete files unless the active plan/spec explicitly says to.
- Do not guess unresolved business rules.
- Leave TODO markers only when the decision record has not locked the rule yet.
- Do not modify unrelated files.
- Do not implement future spec work early.
- Do not duplicate existing patterns without searching first.

### Model/layout rules mandatory

- Do not dump unrelated tables/models into one file.
- Use one table/model per file by default unless the spec explicitly says otherwise.
- Create sensible directories when needed instead of collapsing concerns into a generic module.
- Update import/metadata/Alembic discovery registration cleanly when model work is in scope.
- Do not return raw ORM objects from routers.
- Use explicit safe DTOs for API responses.

### Domain-specific guardrails for the next-phase backend workstream

- Follow the ACTIVE SPEC exactly.
- Rehydrate the architecture docs listed in `IMPLEMENTATION_PLAN.md`.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment data in parent.
- Do not implement admin dashboards unless the ACTIVE SPEC explicitly scopes them.
- Do not redesign stable frontend pages.
- Do not make Discord linkage affect rewards or product access unless the ACTIVE SPEC explicitly scopes it.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not implement unrelated routers/services/repositories outside the ACTIVE SPEC.
- Keep foundation specs small.
- After the foundation pass, prefer vertical feature slices.
- If the ACTIVE SPEC concerns Pay integration, parent may initiate Pay actions, but Pay must execute commercial behavior.
- If the ACTIVE SPEC concerns rewards, frontend APIs must not directly award points/rewards/badges.
- If the ACTIVE SPEC concerns Discord, Discord linkage must not affect rewards or product access unless explicitly scoped.
- If the ACTIVE SPEC concerns support, do not build a full admin dashboard unless explicitly scoped.

## 4) Tests required

Add or update tests for the behavior/structure you changed.

For structural refactors, add regression tests that prove the intended layout and registration still work.

If tests fail, fix them in this same iteration; do not move on while tests are failing.

At minimum, run:

```bash
python -m compileall app tests alembic
```

Then run the authoritative Docker test suite:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

## 5) If Docker or verification is blocked

If Docker is unavailable or the authoritative command cannot run:

- append a blocker entry to `progress/progress.txt`
- verify the blocker entry is appended at EOF
- do not mark any spec item complete
- do not update `IMPLEMENTATION_PLAN.md` as complete
- print exactly:

```text
ITERATION_BLOCKED
```

- stop the iteration

If the topology or command is missing/unusable:

- append the blocker and repo-reality evidence to `progress/progress.txt`
- do not mark any spec item complete
- print exactly:

```text
ITERATION_BLOCKED
```

- stop the iteration

## 6) Update durable artifacts only when not blocked

Only when tests are green:

- Update only the ACTIVE SPEC item you fully completed:
  - `passes=true`
  - `completed_at=<ISO 8601 timestamp with timezone>`
  - `completed_by="codex"`
- Update `IMPLEMENTATION_PLAN.md` checkbox/status only if needed.
- Append an iteration entry to `progress/progress.txt`.
- Verify the new entry is appended at EOF.
- Commit only if tests are green.

The progress entry must include:

- date/time with timezone
- active spec
- selected item
- repo search summary
- files changed
- tests run and results
- blockers if any
- next recommended item

## 7) Completion marker

If the active spec is fully complete, end with:

```text
ALL_DONE
```

Otherwise end with:

```text
ITERATION_DONE
```