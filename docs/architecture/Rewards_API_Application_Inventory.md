# Rewards API Application Inventory

## Purpose
Capture the current repo reality for the rewards API/application workstream before browser-facing rewards endpoints are added, and map the frontend-owned rewards/objectives expectations to the parent backend surfaces that need to be built next.

## Current repo reality on 2026-04-16

### FastAPI and router baseline
- `app/main.py` creates the FastAPI app directly.
- The only registered route is `GET /health`.
- `app/api/routers/` currently contains only `__init__.py`.
- `app/api/deps.py` currently exposes only `get_settings()`.

### Service, repository, and schema baseline
- `app/services/` currently contains only `__init__.py`.
- `app/db/repositories/` currently contains only `__init__.py`.
- `app/schemas/` currently contains only `__init__.py`.
- There are no committed rewards/objectives API schemas, services, repositories, or router modules yet.

### Rewards data layer already implemented
- Rewards tables/models already exist under `app/db/models/rewards/`.
- Model discovery flows through `app/db/models/rewards/__init__.py` to `app/db/models/__init__.py`, then `app/db/bootstrap.py`, then `alembic/env.py`.
- `app/db/models/accounts.py` already exposes account relationships to:
  - `RewardAccount`
  - `RewardEvent`
  - `RewardGrant`
  - `RewardNotification`
  - `AccountBadge`
  - `AccountObjectiveProgress`
- The rewards migration chain is:
  - `20260415_2355_rdb010_reward_foundation_tables.py`
  - `20260416_0010_rdb020_reward_tiers_and_milestones.py`
  - `20260416_0105_rdb030_objective_definition_and_progress_tables.py`
  - `20260416_0215_rdb040_reward_badge_and_grant_tables.py`
  - `20260416_0245_rdb050_reward_notifications.py`

### Existing tests already covering the rewards foundation
- Route baseline:
  - `tests/unit/test_health.py`
- Rewards inventory/layout/bootstrap coverage:
  - `tests/unit/test_rewards_verification_inventory.py`
  - `tests/unit/test_db_bootstrap.py`
  - `tests/unit/test_model_metadata_registration.py`
  - `tests/unit/test_model_module_layout.py`
  - `tests/unit/test_parent_db_metadata_tables.py`
- Migrated Postgres rewards behavior:
  - `tests/integration/test_parent_db_bootstrap.py`
  - `tests/integration/test_parent_db_constraints.py`
  - `tests/integration/test_parent_db_round_trips.py`

## Frontend expectation sources
- `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
- `docs/architecture/Rewards_Objectives_Badges_Domain_Decision_Record.md`
- `docs/architecture/Rewards_Objectives_Badges_UI_Interaction_Reference.md`
- `docs/architecture/Rewards_Objectives_Badges_Data_Model_Reference.md`

## Parent-owned browser API surfaces implied by the frontend

### Rewards summary surface
Frontend pages:
- `/app/dashboard`
- `/app/rewards`

Parent backend responsibilities:
- current points
- current tier
- current progress within the current 1000-point tier band
- next milestone summary
- active perks summary
- achieved rewards or badges gallery summary

### Objectives detail surface
Frontend page:
- `/app/rewards` objectives view

Parent backend responsibilities:
- grouped and ordered objective listings
- milestone objectives linked to progress-bar milestones
- per-objective progress counts/state
- reward details for each objective
- repeatable objective indicators
- scope/gating metadata needed for organized presentation

### Reward notification queue surface
Frontend page:
- objectives completion flow on `/app/rewards`

Parent backend responsibilities:
- ordered queue retrieval for newly completed items
- seen or consumed transitions
- skip-all dismissal of remaining queued items
- milestone vs non-milestone presentation distinctions

### Internal progression surface
Not browser-owned yet, but required by later rewards application items:
- award points
- reverse points/rewards
- complete objective progress
- queue reward presentation records

## Planned module split for the next rewards API items

### Routers
- `app/api/routers/rewards_summary.py`
- `app/api/routers/reward_objectives.py`
- `app/api/routers/reward_notifications.py`

### Services
- `app/services/reward_summary_service.py`
- `app/services/reward_objective_service.py`
- `app/services/reward_notification_service.py`
- `app/services/reward_progression_service.py`

### Repositories
- `app/db/repositories/reward_summary_repository.py`
- `app/db/repositories/reward_objective_repository.py`
- `app/db/repositories/reward_notification_repository.py`

### Schemas
- `app/schemas/reward_summary.py`
- `app/schemas/reward_objectives.py`
- `app/schemas/reward_notifications.py`

## Guardrails for the next implementation items
- Keep rewards browser APIs parent-owned and separate from Pay-owned billing truth.
- Keep rewards page behavior summary-oriented and objectives page behavior structured/detailed.
- Preserve milestone/objective linkage instead of splitting them into unrelated API concepts.
- Only milestone rewards should follow the automatic progress-bar presentation path.
- Non-milestone objective completions should use the ordered objectives-page queue flow.
