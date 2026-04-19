from pathlib import Path

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DOC = REPO_ROOT / "docs" / "architecture" / "Frontend_Backend_Contract_Inventory.md"


def test_frontend_contract_inventory_doc_exists_with_required_sections() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")

    required_phrases = (
        "Current repo reality on 2026-04-19",
        "Canonical route registration",
        "Implemented `/api/v1` route inventory from runtime registration",
        "Shared DTO and contract conventions already implemented",
        "Auth and session surfaces",
        "Settings, profile, address, and communication preference surfaces",
        "Dashboard and launcher surfaces",
        "Billing surfaces",
        "Support, announcements, and service status surfaces",
        "Rewards surfaces",
        "Discord integration surfaces",
        "Explicitly unimplemented public or future surfaces",
        "Future/not implemented",
    )

    for phrase in required_phrases:
        assert phrase in contents


def test_frontend_contract_inventory_doc_references_existing_runtime_and_test_files() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")

    required_paths = (
        "app/main.py",
        "app/api/routers/v1/__init__.py",
        "app/api/routers/v1/auth.py",
        "app/api/routers/v1/profiles.py",
        "app/api/routers/v1/addresses.py",
        "app/api/routers/v1/communication_preferences.py",
        "app/api/routers/v1/dashboard.py",
        "app/api/routers/v1/launcher.py",
        "app/api/routers/v1/billing.py",
        "app/api/routers/v1/support.py",
        "app/api/routers/v1/announcements.py",
        "app/api/routers/v1/service_status.py",
        "app/api/routers/v1/integrations.py",
        "app/api/routers/rewards_summary.py",
        "app/api/routers/reward_objectives.py",
        "app/api/routers/reward_notifications.py",
        "app/api/routers/reward_badges.py",
        "app/schemas/common.py",
        "app/schemas/auth.py",
        "app/schemas/profiles.py",
        "app/schemas/addresses.py",
        "app/schemas/communication_preferences.py",
        "app/schemas/dashboard.py",
        "app/schemas/launcher.py",
        "app/schemas/billing.py",
        "app/schemas/support.py",
        "app/schemas/announcements.py",
        "app/schemas/service_status.py",
        "app/schemas/integrations.py",
        "app/schemas/reward_summary.py",
        "app/schemas/reward_objectives.py",
        "app/schemas/reward_notifications.py",
        "app/schemas/reward_badges.py",
        "tests/unit/test_router_registration.py",
        "tests/unit/test_auth_api.py",
        "tests/unit/test_profiles_api.py",
        "tests/unit/test_addresses_api.py",
        "tests/unit/test_communication_preferences_api.py",
        "tests/unit/test_dashboard_api.py",
        "tests/unit/test_launcher_api.py",
        "tests/unit/test_billing_api.py",
        "tests/unit/test_support_api.py",
        "tests/unit/test_announcement_api.py",
        "tests/unit/test_service_status_api.py",
        "tests/unit/test_discord_integration_api.py",
        "tests/unit/test_rewards_summary_api.py",
        "tests/unit/test_reward_objectives_api.py",
        "tests/unit/test_reward_notifications_api.py",
        "tests/unit/test_reward_badges_api.py",
    )

    for relative_path in required_paths:
        assert relative_path in contents
        assert (REPO_ROOT / relative_path).exists()


def test_frontend_contract_inventory_doc_lists_runtime_registered_frontend_routes() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")
    runtime_routes = {route.path for route in app.routes}

    required_routes = (
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
        "/api/v1/auth/session",
        "/api/v1/auth/sessions",
        "/api/v1/profiles/me",
        "/api/v1/addresses/me",
        "/api/v1/communication-preferences/me",
        "/api/v1/dashboard/summary",
        "/api/v1/launcher/products",
        "/api/v1/billing/snapshot",
        "/api/v1/billing/payment-methods",
        "/api/v1/billing/transactions",
        "/api/v1/support/tickets",
        "/api/v1/announcements",
        "/api/v1/service-status",
        "/api/v1/rewards/me/summary",
        "/api/v1/rewards/me/objectives",
        "/api/v1/rewards/me/notifications",
        "/api/v1/rewards/me/badges",
        "/api/v1/integrations/discord",
    )

    for route_path in required_routes:
        assert route_path in contents
        assert route_path in runtime_routes


def test_frontend_contract_inventory_doc_calls_out_unimplemented_public_contracts() -> None:
    contents = INVENTORY_DOC.read_text(encoding="utf-8")

    required_phrases = (
        "Public home page backend APIs: Future/not implemented",
        "Product page catalog and feature APIs: Future/not implemented",
        "Pricing page plan catalog APIs: Future/not implemented",
        "About-page testimonial/review APIs: Future/not implemented",
        "docs/architecture/Frontend_Backend_Contract_Map.md",
        "specs/frontend_backend_contract_alignment.json",
    )

    for phrase in required_phrases:
        assert phrase in contents
