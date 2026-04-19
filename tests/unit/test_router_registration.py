from app.api.routers import api_router
from app.api.routers.v1 import api_router as versioned_api_router
from app.api.routers.v1.auth import router as auth_router
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


def test_versioned_auth_router_is_canonical_registration_surface() -> None:
    auth_paths = {route.path for route in auth_router.routes}
    assert "/auth/signup" in auth_paths
    assert "/auth/login" in auth_paths
    assert "/auth/verify-email" in auth_paths
    assert "/auth/resend-verification" in auth_paths
    assert "/auth/forgot-password" in auth_paths
    assert "/auth/reset-password" in auth_paths
    assert "/auth/change-password" in auth_paths
    assert "/auth/logout" in auth_paths
    assert "/auth/session" in auth_paths
    assert "/auth/2fa/enroll" in auth_paths
    assert "/auth/2fa/verify" in auth_paths
    assert "/auth/2fa/challenge" in auth_paths
    assert "/auth/2fa/recovery-codes/regenerate" in auth_paths
    assert "/auth/2fa/disable" in auth_paths
    assert "/auth/sessions" in auth_paths
    assert "/auth/sessions/{session_id}/revoke" in auth_paths
    assert "/auth/sessions/revoke-others" in auth_paths
    assert "/auth/account-closure" in auth_paths


def test_main_app_mounts_versioned_rewards_routes_under_api_v1() -> None:
    routes = {route.path for route in app.routes}
    assert "/api/v1/auth/signup" in routes
    assert "/api/v1/auth/login" in routes
    assert "/api/v1/auth/verify-email" in routes
    assert "/api/v1/auth/resend-verification" in routes
    assert "/api/v1/auth/forgot-password" in routes
    assert "/api/v1/auth/reset-password" in routes
    assert "/api/v1/auth/change-password" in routes
    assert "/api/v1/auth/logout" in routes
    assert "/api/v1/auth/session" in routes
    assert "/api/v1/auth/2fa/enroll" in routes
    assert "/api/v1/auth/2fa/verify" in routes
    assert "/api/v1/auth/2fa/challenge" in routes
    assert "/api/v1/auth/2fa/recovery-codes/regenerate" in routes
    assert "/api/v1/auth/2fa/disable" in routes
    assert "/api/v1/auth/sessions" in routes
    assert "/api/v1/auth/sessions/{session_id}/revoke" in routes
    assert "/api/v1/auth/sessions/revoke-others" in routes
    assert "/api/v1/auth/account-closure" in routes
    assert "/api/v1/rewards/{account_id}/summary" in routes
    assert "/api/v1/rewards/{account_id}/objectives" in routes
    assert "/api/v1/rewards/{account_id}/notifications" in routes
