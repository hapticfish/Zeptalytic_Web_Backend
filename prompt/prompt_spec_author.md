# Zeptalytic Web Backend Spec Author Prompt

You are Codex working in this repository as the Spec Author Agent.

Run ONE spec-authoring iteration only.

Your job is to create exactly one focused implementation spec JSON for the next backend workstream.

You are not implementing runtime application code.

End the run with exactly:

```text
SPEC_DONE
```

## 0) Current mission

The completed broad backend buildout phase is now followed by a narrow backend runtime-readiness pass for frontend integration.

Create or refine this spec:

```text
specs/frontend_runtime_integration_readiness.json
```

This spec prepares the FastAPI parent backend to be safely called by the React/Vite frontend during local browser-based integration.

The spec should focus on:

- explicit credentialed CORS support for local Vite origins
- HTTP-only cookie auth browser contract verification/documentation
- frontend-facing backend route inventory documentation
- runtime OpenAPI surface regression coverage
- compile/test verification

This spec must stay backend-only.

Do not edit the frontend repo.

Do not create frontend API clients.

Do not modify React/Vite files.

Do not redesign frontend pages.

## 1) Rehydrate context mandatory

Read these first:

1. `AGENTS.md`
2. `IMPLEMENTATION_PLAN.md`
3. `PROMPT.md` if present
4. `progress/progress.txt` last 1–3 entries
5. `specs/next_phase_spec_sequence.json` if present
6. `specs/_template_next_phase_spec.json` if present
7. `docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md`
8. `docs/architecture/Frontend_Backend_Contract_Map.md` if present
9. `docs/architecture/Auth_Session_and_Security_Flows.md` if present
10. `docs/architecture/Parent_Backend_Application_Architecture.md` if present
11. `docs/architecture/Parent_Backend_API_Contract_Standards.md` if present
12. `docs/architecture/Security_Operational_Control_Guide.md` if present
13. `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md` if present
14. `docs/architecture/Spec_Authoring_and_Harness_Workflow.md` if present

Also inspect current repo structure before drafting:

```bash
git status
git log -5 --oneline
git ls-files
find app -maxdepth 5 -type f | sort
find tests -maxdepth 5 -type f | sort
find specs -maxdepth 1 -type f | sort
find docs -maxdepth 3 -type f | sort
```

## 2) Determine the spec to author

Create exactly this spec unless it already exists and is materially complete:

```text
specs/frontend_runtime_integration_readiness.json
```

If it already exists but is incomplete, do not create a second spec. Instead, refine only that spec if needed.

If it already exists and all items have `passes=true`, append a progress entry explaining that no new backend readiness spec was needed and stop with `SPEC_DONE`.

Do not create multiple implementation specs in one run.

Do not update frontend files.

Do not update `IMPLEMENTATION_PLAN.md` unless John explicitly asks you to activate the generated spec in the same run.

## 3) Search before writing the spec mandatory

Before writing or refining the spec, search for current repo reality related to frontend runtime integration.

Use commands such as:

```bash
git grep -n "CORSMiddleware\|allow_origins\|allow_credentials\|CORS" app tests docs || true
git grep -n "api_v1_prefix\|include_router\|APIRouter" app tests docs || true
git grep -n "zeptalytic_session\|session" app tests docs || true
git grep -n "set_cookie\|delete_cookie\|httponly\|samesite\|secure" app tests docs || true
git grep -n "openapi\|app.openapi\|include_in_schema" app tests docs || true
git grep -n "localhost:5173\|127.0.0.1:5173\|Vite" app tests docs || true
git grep -n "/api/v1/auth\|/api/v1/dashboard\|/api/v1/launcher\|/api/v1/billing" app tests docs || true
find app/api -maxdepth 5 -type f | sort || true
find tests -maxdepth 5 -type f | sort || true
```

Adjust searches if the repo uses different naming.

Summarize findings in the generated spec under `context.repo_reality_summary`.

Do not assume something is missing until you search for it.

## 4) Create exactly one spec JSON

Create or refine exactly one spec file:

```text
specs/frontend_runtime_integration_readiness.json
```

Use `specs/_template_next_phase_spec.json` as the structure guide if it exists.

Do not create multiple specs in one run.

## 5) Required spec structure

The spec JSON must include:

```json
{
  "id": "frontend_runtime_integration_readiness",
  "title": "Frontend Runtime Integration Readiness",
  "status": "active",
  "owner": "Zeptalytic Web Backend",
  "purpose": "<purpose>",
  "context": {
    "summary": "<summary>",
    "source_docs": [],
    "previous_specs_or_dependencies": [],
    "repo_reality_summary": []
  },
  "global_guardrails": [],
  "expected_paths": {
    "may_create_or_update": [],
    "must_not_modify_without_strong_reason": []
  },
  "items": [],
  "completion_definition": []
}
```

Each item must include:

```json
{
  "id": "<item_id>",
  "title": "<item title>",
  "description": "<description>",
  "acceptance_criteria": [],
  "passes": false,
  "completed_at": null,
  "completed_by": null
}
```

Use `passes=false` for all new items.

Do not use only `status=pending` because the build prompt selects items by `passes=false`.

## 6) Recommended spec items

Use the repo search results to adjust exact paths, but the spec should normally contain these focused items.

### `fri-010` Add CORS runtime settings

Purpose:

- Add explicit backend settings for allowed browser origins.
- Support local Vite dev origins.
- Keep credentialed CORS explicit and non-wildcard.

Expected behavior:

- `http://localhost:5173` allowed.
- `http://127.0.0.1:5173` allowed.
- `allow_credentials=true`.
- No wildcard credentialed CORS.
- Settings live in the backend config/settings layer, not hard-coded only in `main.py`.

### `fri-020` Wire FastAPI CORSMiddleware

Purpose:

- Register FastAPI `CORSMiddleware` using configured origins.
- Preserve existing router mounting and middleware behavior.
- Add tests proving CORS preflight/credential headers for allowed origins.

### `fri-030` Verify and document browser cookie auth contract

Purpose:

- Verify login/signup/session/logout browser behavior.
- Confirm frontend must use `credentials: "include"`.
- Confirm frontend must not store tokens in localStorage/sessionStorage.
- Confirm `zeptalytic_session` remains HTTP-only.
- Add or update docs/tests as appropriate.

### `fri-040` Document frontend-facing backend API route inventory

Purpose:

- Produce a backend-owned route inventory for frontend integration.
- Include known `/api/v1` routes for auth, dashboard, launcher, billing, settings/profile/preferences/addresses, rewards/objectives/badges, support/status/announcements, and integrations/Discord where present.
- Mark routes as runtime available, backend-owned, or future/blocked based on repo reality.
- Do not invent routes that do not exist.

### `fri-050` Add OpenAPI runtime surface regression coverage

Purpose:

- Add tests that inspect `app.openapi()` and assert the frontend-critical route surface exists.
- Confirm runtime OpenAPI behavior aligns with documented browser contract.
- Do not hide frontend-critical routes from OpenAPI unless there is a documented security reason.

### `fri-999` Run full backend verification

Purpose:

- Run compile and Docker test verification.
- Do not mark complete unless required checks pass.

Required commands:

```bash
python -m compileall app tests alembic
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

## 7) Required guardrails for generated spec

Include these guardrails unless a stronger workstream-specific version is needed:

- Search before editing.
- Do not expand scope beyond this spec.
- Do not add dependencies unless John explicitly approves them.
- Do not edit the frontend repo.
- Do not create frontend API clients.
- Do not modify React/Vite files.
- Do not redesign stable frontend pages.
- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment details in parent.
- Do not build admin dashboards unless explicitly scoped.
- Do not make Discord linkage affect rewards or product access unless the spec explicitly says so.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not return raw ORM objects from routers.
- Use explicit safe DTOs for API responses.
- Use explicit allowed origins for credentialed CORS; do not use wildcard credentialed CORS.
- Preserve HTTP-only cookie auth.
- Do not store raw session tokens in browser-visible responses.
- Do not mark incomplete items complete.
- Append progress entries to the absolute end of `progress/progress.txt`.
- Run `python -m compileall app tests alembic` before marking implementation items complete.
- Run `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test` before marking implementation items complete.

## 8) Expected paths

The generated spec should normally allow updates to paths like:

```text
app/core/config.py
app/main.py
app/api/routers/v1/*
app/schemas/*
tests/*
docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md
docs/architecture/Frontend_Backend_Contract_Map.md
docs/openapi/*
specs/frontend_runtime_integration_readiness.json
progress/progress.txt
IMPLEMENTATION_PLAN.md
```

Only include paths that make sense after repo inspection.

The generated spec should normally forbid or strongly discourage changes to:

```text
../zeptalytic_web/*
frontend repo files
node_modules/
venv/
.venv/
database migrations unless explicitly required
payment provider secret handling
unrelated routers/services/repositories
```

## 9) Progress entry mandatory

Append a progress entry to the absolute end of:

```text
progress/progress.txt
```

The entry must include:

- date/time with timezone
- mode: spec_author
- selected workstream
- spec file created or refined
- architecture docs used
- repo search summary
- files changed
- non-goals
- risks/assumptions
- next command to run

The newest progress entry must be the final content in the file.

Do not insert the progress entry above older entries.

Do not keep a footer after it.

## 10) Final response requirements

In the final response, summarize:

- which workstream was selected
- which spec file was created or refined
- which docs were used
- which repo reality was found
- which files were changed
- major non-goals
- risks/assumptions
- exact next command

End the final response with exactly:

```text
SPEC_DONE
```