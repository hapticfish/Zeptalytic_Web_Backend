from app.api.routers import api_router
from app.api.routers.v1 import api_router as versioned_api_router
from app.api.routers.v1.addresses import router as addresses_router
from app.api.routers.v1.billing import router as billing_router
from app.api.routers.v1.auth import router as auth_router
from app.api.routers.v1.communication_preferences import (
    router as communication_preferences_router,
)
from app.api.routers.v1.dashboard import router as dashboard_router
from app.api.routers.v1.launcher import router as launcher_router
from app.api.routers.v1.profiles import router as profiles_router
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


def test_versioned_settings_routers_are_canonical_registration_surfaces() -> None:
    profile_routes = {
        (route.path, tuple(sorted(route.methods or []))) for route in profiles_router.routes
    }
    address_paths = {route.path for route in addresses_router.routes}
    communication_preference_routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in communication_preferences_router.routes
    }

    assert ("/profiles/_contract", ("GET",)) in profile_routes
    assert ("/profiles/me", ("GET",)) in profile_routes
    assert ("/profiles/me", ("PATCH",)) in profile_routes
    assert "/addresses/_contract" in address_paths
    assert "/addresses/me" in address_paths
    assert "/addresses/me/{address_id}" in address_paths
    assert "/addresses/me/{address_id}/primary" in address_paths
    assert ("/communication-preferences/_contract", ("GET",)) in communication_preference_routes
    assert ("/communication-preferences/me", ("GET",)) in communication_preference_routes
    assert ("/communication-preferences/me", ("PATCH",)) in communication_preference_routes


def test_versioned_dashboard_launcher_billing_routers_are_canonical_registration_surfaces() -> None:
    dashboard_routes = {
        (route.path, tuple(sorted(route.methods or []))) for route in dashboard_router.routes
    }
    launcher_routes = {
        (route.path, tuple(sorted(route.methods or []))) for route in launcher_router.routes
    }
    billing_routes = {
        (route.path, tuple(sorted(route.methods or []))) for route in billing_router.routes
    }

    assert ("/dashboard/summary", ("GET",)) in dashboard_routes
    assert ("/launcher/products", ("GET",)) in launcher_routes
    assert ("/billing/snapshot", ("GET",)) in billing_routes
    assert ("/billing/subscriptions", ("GET",)) in billing_routes
    assert ("/billing/payment-methods", ("GET",)) in billing_routes
    assert ("/billing/transactions", ("GET",)) in billing_routes
    assert ("/billing/checkout", ("POST",)) in billing_routes
    assert ("/billing/subscription-change", ("POST",)) in billing_routes
    assert ("/billing/subscription-cancel", ("POST",)) in billing_routes
    assert ("/billing/subscription-restart", ("POST",)) in billing_routes
    assert ("/billing/promo-code/validate", ("POST",)) in billing_routes
    assert ("/billing/promo-code/apply", ("POST",)) in billing_routes


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
    assert "/api/v1/profiles/_contract" in routes
    assert "/api/v1/profiles/me" in routes
    assert "/api/v1/addresses/_contract" in routes
    assert "/api/v1/addresses/me" in routes
    assert "/api/v1/addresses/me/{address_id}" in routes
    assert "/api/v1/addresses/me/{address_id}/primary" in routes
    assert "/api/v1/communication-preferences/_contract" in routes
    assert "/api/v1/communication-preferences/me" in routes
    assert "/api/v1/rewards/{account_id}/summary" in routes
    assert "/api/v1/rewards/{account_id}/objectives" in routes
    assert "/api/v1/rewards/{account_id}/notifications" in routes
    assert "/api/v1/dashboard/summary" in routes
    assert "/api/v1/launcher/products" in routes
    assert "/api/v1/billing/snapshot" in routes
    assert "/api/v1/billing/subscriptions" in routes
    assert "/api/v1/billing/payment-methods" in routes
    assert "/api/v1/billing/transactions" in routes
    assert "/api/v1/billing/checkout" in routes
    assert "/api/v1/billing/subscription-change" in routes
    assert "/api/v1/billing/subscription-cancel" in routes
    assert "/api/v1/billing/subscription-restart" in routes
    assert "/api/v1/billing/promo-code/validate" in routes
    assert "/api/v1/billing/promo-code/apply" in routes
