# Zeptalytic Website Backend / Parent Site Harness Prompt

Active spec: specs/parent_db_foundation.json

Before every build run, rehydrate context from:
- `AGENTS.md`
- `IMPLEMENTATION_PLAN.md`
- `progress/progress.txt`
- the active spec
- the architecture docs referenced in `IMPLEMENTATION_PLAN.md`

For build iterations, follow:
- `prompt/prompt_build.md`

For planning-only iterations, follow:
- `prompt/prompt_plan.md`

Current first workstream:
- Parent DB foundation for the Zeptalytic website backend / parent site repo.

Current implementation objective:
- establish the parent-owned database foundation in a way that preserves the locked ownership split between parent site and Pay
- avoid duplicating Pay billing truth
- prepare the repo for later backend route/API workstreams

Current repo reality note:
- the repo does not yet contain `docker-compose.yml` or `docker-compose.test.yml`
- the next build slice must establish the `api` / `migrate` / `test` compose topology before later DB schema items can satisfy the authoritative docker command
