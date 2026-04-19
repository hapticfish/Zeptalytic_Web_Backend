# Zeptalytic Web Backend Build Prompt

You are Codex working in this repository.

Run ONE build iteration only.

End the run with one of:

```text
ITERATION_DONE
ALL_DONE
ITERATION_BLOCKED
```

## 0) Current mission

The active backend workstream is frontend runtime integration readiness.

The intended active spec is:

```text
specs/frontend_runtime_integration_readiness.json
```

This build pass must implement exactly one incomplete item from the active spec.

The work must remain backend-only.

Do not edit the frontend repo.

Do not create frontend API clients.

Do not modify React/Vite files.

## 1) Rehydrate context mandatory

Read:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. Determine the ACTIVE SPEC from the `Active spec:` line in `IMPLEMENTATION_PLAN.md`
6. Read the ACTIVE SPEC file
7. Read `specs/next_phase_spec_sequence.json` if present
8. Read `docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md`
9. Read `docs/architecture/Frontend_Backend_Contract_Map.md` if present
10. Read `docs/architecture/Auth_Session_and_Security_Flows.md` if present
11. Read `docs/architecture/Parent_Backend_Application_Architecture.md` if present
12. Read `docs/architecture/Parent_Backend_API_Contract_Standards.md` if present
13. Read `docs/architecture/Security_Operational_Control_Guide.md` if present
14. Read `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md` if present
15. Read `docs/architecture/Spec_Authoring_and_Harness_Workflow.md` if present
16. Run `git status`
17. Run `git log -5 --oneline`

If the active spec file does not exist, append a blocker entry to `progress/progress.txt`, do not modify implementation files, print exactly `ITERATION_BLOCKED`, and stop.

## 2) Pick ONE item to work on

Choose exactly one item in the ACTIVE SPEC where:

```json
"passes": false
```

Prefer earlier items first unless a later item is clearly blocking.

Do not work on more than one item in a single build iteration unless the active spec item itself explicitly requires a tiny companion change.

Do not mark any item complete unless its acceptance criteria are fully satisfied and required verification passes.

## 3) Search before editing mandatory

Use:

```bash
git ls-files
git grep
rg
find
grep -R
```

Before changing anything, summarize what you found:

- file paths
- key functions/classes/models/schemas/repositories/services involved
- current config/settings structure
- current middleware/app startup structure
- current router registration
- current session cookie behavior
- current OpenAPI behavior
- existing tests that already cover the target area
- gaps the selected spec item should address

Use relevant commands such as:

```bash
git grep -n "CORSMiddleware\|allow_origins\|allow_credentials\|CORS" app tests docs || true
git grep -n "api_v1_prefix\|include_router\|APIRouter" app tests docs || true
git grep -n "zeptalytic_session\|session" app tests docs || true
git grep -n "set_cookie\|delete_cookie\|httponly\|samesite\|secure" app tests docs || true
git grep -n "openapi\|app.openapi\|include_in_schema" app tests docs || true
git grep -n "localhost:5173\|127.0.0.1:5173\|Vite" app tests docs || true
find app -maxdepth 5 -type f | sort
find tests -maxdepth 5 -type f | sort
```

Do not assume something is missing until you search for it.

## 4) Implement the smallest safe change

- Keep changes small and localized.
- Match repository patterns and architecture docs.
- Do not add dependencies unless John explicitly approved them.
- Do not delete files unless the active plan/spec explicitly says to.
- Do not guess unresolved business rules.
- Leave TODO markers only when the decision record has not locked the rule yet.
- Do not modify unrelated files.
- Do not implement future spec work early.
- Do not duplicate existing patterns without searching first.
- Do not edit the frontend repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.

## 5) Backend runtime-readiness guardrails

- Follow the ACTIVE SPEC exactly.
- Preserve `/api/v1` API versioning.
- Preserve HTTP-only cookie auth.
- Frontend browser requests must be able to use `credentials: "include"`.
- Backend must not return raw session tokens to browser-readable payloads.
- Allowed local frontend origins must be explicit:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- Credentialed CORS must not use wildcard origins.
- CORS configuration should live in the backend settings/config layer when practical.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment data in parent.
- Do not implement admin dashboards unless explicitly scoped.
- Do not make Discord linkage affect rewards or product access unless explicitly scoped.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not implement unrelated routers/services/repositories outside the ACTIVE SPEC.
- Do not modify database schema unless the ACTIVE SPEC explicitly scopes it.
- Do not return raw ORM objects from routers.
- Use explicit safe DTOs for API responses.

## 6) Tests required

Add or update tests for the behavior/structure you changed.

For structural refactors, add regression tests that prove the intended layout and registration still work.

Expected test areas by item:

- CORS settings: config/settings tests where present, or app/middleware tests.
- CORSMiddleware wiring: preflight/request tests for allowed origins and credential headers.
- Cookie auth contract: tests proving HTTP-only cookie behavior and session endpoint behavior.
- Route inventory docs: docs consistency checks if repo has docs tests, otherwise clear doc update.
- OpenAPI surface: tests that inspect `app.openapi()` for frontend-critical routes.
- Full verification item: no code behavior change required, but required commands must pass.

If tests fail, fix them in this same iteration; do not move on while tests are failing.

At minimum, run:

```bash
python -m compileall app tests alembic
```

Then run the authoritative Docker test suite:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

## 7) If Docker or verification is blocked

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

## 8) Update durable artifacts only when not blocked

Only when tests are green:

- Update only the ACTIVE SPEC item you fully completed:
  - `passes=true`
  - `completed_at=<ISO 8601 timestamp with timezone>`
  - `completed_by="codex"`
- Update `IMPLEMENTATION_PLAN.md` checkbox/status only if needed.
- Append an iteration entry to `progress/progress.txt`.
- Verify the new entry is appended at EOF.
- Commit only if tests are green and a commit is appropriate.

The progress entry must include:

- date/time with timezone
- active spec
- selected item
- repo search summary
- files changed
- tests run and results
- blockers if any
- next recommended item

## 9) Completion marker

If the active spec is fully complete, end with exactly:

```text
ALL_DONE
```

Otherwise end with exactly:

```text
ITERATION_DONE
```

If blocked, end with exactly:

```text
ITERATION_BLOCKED
```