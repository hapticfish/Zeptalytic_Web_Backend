from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_REWARD_MODEL_FILES = {
    "__init__.py",
    "account_badges.py",
    "account_objective_progress.py",
    "badge_definitions.py",
    "objective_definitions.py",
    "objective_reward_links.py",
    "reward_accounts.py",
    "reward_definitions.py",
    "reward_events.py",
    "reward_grants.py",
    "reward_milestones.py",
    "reward_notifications.py",
    "reward_tier_definitions.py",
}

EXPECTED_REWARD_MIGRATION_FILES = (
    "20260415_2355_rdb010_reward_foundation_tables.py",
    "20260416_0010_rdb020_reward_tiers_and_milestones.py",
    "20260416_0105_rdb030_objective_definition_and_progress_tables.py",
    "20260416_0215_rdb040_reward_badge_and_grant_tables.py",
    "20260416_0245_rdb050_reward_notifications.py",
)

EXPECTED_REWARD_VERIFICATION_TEST_FILES = {
    "tests/unit/test_db_bootstrap.py",
    "tests/unit/test_model_metadata_registration.py",
    "tests/unit/test_model_module_layout.py",
    "tests/unit/test_parent_db_metadata_tables.py",
    "tests/integration/test_parent_db_bootstrap.py",
    "tests/integration/test_parent_db_constraints.py",
    "tests/integration/test_parent_db_round_trips.py",
}


def test_rewards_verification_inventory_matches_current_repo_surface() -> None:
    reward_models_dir = REPO_ROOT / "app" / "db" / "models" / "rewards"
    migration_dir = REPO_ROOT / "alembic" / "versions"

    reward_model_files = {path.name for path in reward_models_dir.glob("*.py")}
    migration_files = {path.name for path in migration_dir.glob("*rdb*.py")}

    assert reward_model_files == EXPECTED_REWARD_MODEL_FILES
    assert tuple(
        migration_name for migration_name in EXPECTED_REWARD_MIGRATION_FILES
    ) == EXPECTED_REWARD_MIGRATION_FILES
    assert set(EXPECTED_REWARD_MIGRATION_FILES).issubset(migration_files)


def test_rewards_verification_inventory_tracks_existing_reward_regression_files() -> None:
    repo_files = {
        path.relative_to(REPO_ROOT).as_posix() for path in REPO_ROOT.glob("tests/**/*.py")
    }

    assert EXPECTED_REWARD_VERIFICATION_TEST_FILES.issubset(repo_files)
