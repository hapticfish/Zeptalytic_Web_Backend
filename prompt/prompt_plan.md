# Zeptalytic Web Backend Planning Prompt

You are Codex working in this repository.

This run is PLANNING ONLY.

End the run with exactly:

```text
PLAN_DONE
```

## Rules

- Do NOT modify runtime application code in this run.
- Allowed changes: `specs/`, `docs/`, `README.md`, `PROMPT.md`, `prompt/*`, `scripts/*`, `IMPLEMENTATION_PLAN.md`, `progress/*`, and other planning-only files.
- Keep changes small and reviewable.
- Do not implement application behavior in planning mode.
- Do not add dependencies unless John explicitly approved them.
- Do not edit the frontend repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.

## 0) Current mission

The active backend workstream is frontend runtime integration readiness.

The intended active spec is:

```text
specs/frontend_runtime_integration_readiness.json
```

This backend planning pass should confirm that the active spec is ready for build iterations that prepare the FastAPI backend for browser-based calls from the React/Vite frontend.

The planning pass may refine the spec, docs, prompts, or implementation plan if repo reality requires it.

The planning pass must not implement CORS/runtime code directly.

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

If the active spec file does not exist, append a blocker/planning entry explaining that spec-authoring must be run first, then end with `PLAN_DONE`.

## 2) Confirm repo reality before editing

Search before editing and summarize current related code, file layout, wiring, and tests.

Use relevant commands such as:

```bash
git ls-files
git grep -n "CORSMiddleware\|allow_origins\|allow_credentials\|CORS" app tests docs || true
git grep -n "api_v1_prefix\|include_router\|APIRouter" app tests docs || true
git grep -n "zeptalytic_session\|session" app tests docs || true
git grep -n "set_cookie\|delete_cookie\|httponly\|samesite\|secure" app tests docs || true
git grep -n "openapi\|app.openapi\|include_in_schema" app tests docs || true
git grep -n "localhost:5173\|127.0.0.1:5173\|Vite" app tests docs || true
git grep -n "/api/v1/auth\|/api/v1/dashboard\|/api/v1/launcher\|/api/v1/billing" app tests docs || true
find app -maxdepth 5 -type f | sort
find tests -maxdepth 5 -type f | sort
find docs -maxdepth 3 -type f | sort
```

When config/middleware is in scope, inspect at minimum:

- the backend settings/config module
- the FastAPI app factory or `app/main.py`
- router include/mounting paths
- current tests for app startup, OpenAPI, auth/session, and middleware

When browser auth is in scope, inspect at minimum:

- signup/login/logout/session routes
- session cookie creation/deletion
- tests that assert cookie behavior
- docs that describe frontend auth behavior

Do not assume the current workstream still matches repo reality until you verify it.

## 3) Planning output

Refine the ACTIVE SPEC only if repo reality or blocker history requires it.

Keep items focused enough for one build iteration each.

Expected spec sequence remains:

1. CORS runtime settings
2. FastAPI CORSMiddleware wiring
3. browser cookie auth contract verification/documentation
4. frontend-facing backend API route inventory
5. OpenAPI runtime surface regression coverage
6. full backend verification

Do not expand the spec into frontend implementation.

Do not add a broad UI integration spec in the backend repo.

Do not collapse unrelated future work into this backend-readiness spec.

Record blockers, command drift, topology drift, or architecture-doc drift in repo docs when relevant.

## 4) Scope guardrails

- Do not edit the frontend repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment details in parent.
- Do not implement admin dashboards unless the ACTIVE SPEC explicitly scopes them.
- Do not make Discord linkage affect rewards or product access unless the ACTIVE SPEC explicitly scopes it.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not create broad unused repositories/services detached from the active spec.
- Do not implement runtime code in planning mode.
- Do not add dependencies unless John explicitly approved them.
- Do not modify database schema unless the ACTIVE SPEC explicitly scopes schema work.
- Do not use wildcard credentialed CORS.
- Preserve HTTP-only cookie auth.
- Do not expose raw session tokens in browser-readable payloads.

## 5) Durable artifacts

- Append a planning entry to `progress/progress.txt`.
- Verify the progress entry is appended at EOF.
- If docs/specs are refined, keep changes small and reviewable.
- If tests are required for a docs-only planning run, use the authoritative Docker command only if appropriate.
- If the topology is missing or unusable, record the blocker and stop safely.
- Commit only planning/doc files if tests are green and a commit is appropriate.

## 6) Final response requirements

In the final response, summarize:

- active spec
- repo search summary
- planning changes made
- files changed
- non-goals preserved
- blockers or assumptions
- exact next command

End the final response with exactly:

```text
PLAN_DONE
```