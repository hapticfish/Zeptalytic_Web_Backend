# Spec Authoring and Harness Workflow

## Purpose

This document defines how implementation specs are created for the Zeptalytic Web Backend after the architecture/control docs are in place.

The backend now uses a staged agent workflow:

1. Architecture/control documents define durable system decisions.
2. A spec-authoring pass creates one focused runnable spec.
3. A planning pass reviews the active spec and proposes implementation steps.
4. A build pass implements the active spec.
5. Tests verify the work.
6. The next spec-authoring pass starts from the updated repo state.

This prevents the build agent from inventing architecture, expanding scope, duplicating Pay logic, or generating stale specs that no longer match the repo.

## Agent roles

### Spec Author Agent

The Spec Author Agent creates or updates exactly one implementation spec JSON file.

It must read:

- `AGENTS.md`
- `IMPLEMENTATION_PLAN.md`
- `PROMPT.md` if present
- `specs/next_phase_spec_sequence.json`
- relevant docs under `docs/architecture/`
- `progress/progress.txt`
- current repo structure
- existing tests
- existing models/repositories/services/routers/schemas

It may create or update:

- one spec file under `specs/`
- `progress/progress.txt`

It must not implement runtime application code.

It must not modify database models.

It must not modify Alembic migrations.

It must not modify routers, services, repositories, schemas, workers, integrations, or tests unless the specific task is to create a spec for those future changes.

It must not mark implementation items complete.

It must append a progress entry to the absolute end of `progress/progress.txt`.

It must end with:

```text
SPEC_DONE