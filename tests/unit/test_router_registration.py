from app.api.routers import api_router
from app.api.routers.v1 import api_router as versioned_api_router
from app.api.routers.v1.rewards import router as rewards_router
from app.main import app


def test_top_level_api_router_re_exports_versioned_router() -> None:
    assert api_router is versioned_api_router


def test_versioned_rewards_router_is_canonical_registration_surface() -> None:
    reward_paths = {route.path for route in rewards_router.routes}
    assert "/rewards/{account_id}/summary" in reward_paths
    assert "/rewards/{account_id}/objectives" in reward_paths
    assert "/rewards/{account_id}/notifications" in reward_paths
    assert "/rewards/{account_id}/notifications/{notification_id}/seen" in reward_paths
    assert "/rewards/{account_id}/notifications/skip-all" in reward_paths


def test_main_app_mounts_versioned_rewards_routes_under_api_v1() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/rewards/{account_id}/summary" in routes
    assert "/api/v1/rewards/{account_id}/objectives" in routes
    assert "/api/v1/rewards/{account_id}/notifications" in routes
