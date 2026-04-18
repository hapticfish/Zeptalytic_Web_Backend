You are Codex working in this repository. This run is PLANNING ONLY.

Rules:
- Do NOT modify runtime application code in this run.
- Allowed changes: `specs/`, `docs/`, `README.md`, `PROMPT.md`, `prompt/*`, `scripts/*`, `IMPLEMENTATION_PLAN.md`, `progress/*`, and other planning-only files.
- Keep changes small and reviewable.
- Do not implement application behavior in planning mode.
- Do not add dependencies unless John explicitly approved them.

Follow this exact routine every planning run:

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
9. Read architecture docs relevant to the ACTIVE SPEC, especially:
   - `docs/architecture/Spec_Authoring_and_Harness_Workflow.md`
   - `docs/architecture/Parent_Backend_Application_Architecture.md`
   - `docs/architecture/Parent_Backend_API_Contract_Standards.md`
   - `docs/architecture/Parent_Backend_Repository_Layer_Design.md`
   - `docs/architecture/Parent_Backend_Service_Layer_Design.md`
   - `docs/architecture/Parent_Pay_Integration_and_Projection_Strategy.md`
   - `docs/architecture/Frontend_Backend_Contract_Map.md`
   - `docs/architecture/Auth_Session_and_Security_Flows.md`
   - `docs/architecture/Dashboard_Launcher_Billing_Aggregation_Design.md`
   - `docs/architecture/Support_Announcements_and_Status_Design.md`
   - `docs/architecture/Rewards_Application_and_Notification_Flows.md`
   - `docs/architecture/Discord_Integration_Application_Flow.md`
   - `docs/architecture/Background_Jobs_Sync_and_Event_Processing.md`
   - `docs/architecture/Security_Operational_Control_Guide.md`
   - `docs/architecture/Agent_Non_Goals_and_Implementation_Guardrails.md`
10. Run `git status`
11. Run `git log -5 --oneline`

## 1) Confirm repo reality before editing

Search before editing and summarize current related code, file layout, wiring, and tests.

Use relevant commands such as:

```bash
git ls-files
git grep -n "APIRouter" app tests || true
git grep -n "include_router" app tests || true
git grep -n "HTTPException\\|exception_handler\\|RequestValidationError" app tests || true
git grep -n "BaseModel\\|ConfigDict" app tests || true
git grep -n "repository\\|Repository" app tests || true
git grep -n "service\\|Service" app tests || true
find app -maxdepth 4 -type f | sort
find tests -maxdepth 4 -type f | sort
```

When model-file structure is in scope, inspect at minimum:

- `app/db/models/`
- metadata registration paths
- Alembic discovery/import paths

When verification/testing is in scope, inspect at minimum:

- `tests/`
- `docker-compose.test.yml`
- `alembic/`
- current DB/bootstrap fixtures or setup helpers

Adjust searches to the active spec.

Do not assume the current workstream still matches repo reality until you verify it.

## 2) Planning output

Refine the ACTIVE SPEC if repo reality or blocker history requires it.

Keep items small enough for one build iteration each.

Use `specs/next_phase_spec_sequence.json` and the active spec to preserve the next-phase sequence.

Do not collapse unrelated next-phase workstreams into one oversized spec.

Prefer this sequence:

1. application foundation
2. auth/session/account
3. profile/settings/addresses/preferences
4. Pay integration/projections
5. dashboard/launcher/billing
6. support/announcements/status
7. rewards/objectives/badges APIs
8. Discord integration
9. background jobs/security
10. frontend contract alignment

Keep the next queued spec ready, but do not make it active unless the current workstream has materially changed, is complete, or is no longer the correct next target.

Record blockers, command drift, topology drift, or architecture-doc drift in repo docs when relevant.

## 3) Scope guardrails

- Do not duplicate Pay commercial business rules in parent.
- Do not store sensitive payment details in parent.
- Do not implement admin dashboards unless the ACTIVE SPEC explicitly scopes them.
- Do not redesign stable frontend pages.
- Do not make Discord linkage affect rewards or product access unless the ACTIVE SPEC explicitly scopes it.
- Do not allow frontend APIs to directly award points/rewards/badges.
- Do not create broad unused repositories/services detached from the active spec.
- Do not implement runtime code in planning mode.
- Do not add dependencies unless John explicitly approved them.
- Do not modify database schema unless the ACTIVE SPEC explicitly scopes schema work.

## 4) Durable artifacts

- Append a planning entry to `progress/progress.txt`.
- Verify the progress entry is appended at EOF.
- If docs/specs are refined, keep changes small and reviewable.
- If tests are required for a docs-only planning run, use the authoritative Docker command.
- If the topology is missing or unusable, record the blocker and stop safely.
- Commit only planning/doc files if tests are green and a commit is appropriate.

End with:

```text
PLAN_DONE
```