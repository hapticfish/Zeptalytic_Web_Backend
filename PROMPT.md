Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, the active spec file when present, and `progress/progress.txt`.

The active backend workstream is frontend runtime integration readiness.

The target active spec is:

```text
specs/frontend_runtime_integration_readiness.json
```

`docs/architecture/Frontend_Backend_Runtime_Integration_Guide.md` is the primary source for the browser/runtime integration contract between the FastAPI backend and React/Vite frontend.

`docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md` remains the canonical source for parent-site vocabulary, enum values, and status names where domain terminology is involved.

Then:

- for spec-authoring runs, follow `prompt/prompt_spec_author.md`
- for planning runs, follow `prompt/prompt_plan.md`
- for build runs, follow `prompt/prompt_build.md`

The active backend workstream sequence is:

1. frontend runtime integration readiness spec authoring
2. planning review/refinement
3. CORS runtime settings
4. FastAPI CORSMiddleware wiring
5. browser cookie auth contract verification/documentation
6. frontend-facing backend API route inventory
7. OpenAPI runtime surface regression coverage
8. full backend compile and Docker test verification

This backend harness run must not edit the frontend repo.

Do not create frontend API clients here.

Do not modify React/Vite files here.

Do not redesign frontend pages here.