from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DOC = REPO_ROOT / "docs" / "architecture" / "Rewards_API_Application_Inventory.md"


def test_rewards_api_inventory_doc_exists_with_required_sections() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")

    required_phrases = (
        "Current repo reality on 2026-04-16",
        "GET /health",
        "app/api/routers/",
        "app/services/",
        "app/db/repositories/",
        "app/schemas/",
        "Rewards summary surface",
        "Objectives detail surface",
        "Reward notification queue surface",
        "Internal progression surface",
        "app/api/routers/rewards_summary.py",
        "app/services/reward_summary_service.py",
        "app/db/repositories/reward_summary_repository.py",
        "app/schemas/reward_summary.py",
    )

    for phrase in required_phrases:
        assert phrase in contents


def test_rewards_api_inventory_doc_references_existing_baseline_files() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")

    baseline_files = (
        "app/main.py",
        "app/api/deps.py",
        "app/db/models/rewards/__init__.py",
        "app/db/models/__init__.py",
        "tests/unit/test_health.py",
        "tests/unit/test_rewards_verification_inventory.py",
        "tests/integration/test_parent_db_round_trips.py",
    )

    for relative_path in baseline_files:
        assert relative_path in contents
        assert (REPO_ROOT / relative_path).exists()
