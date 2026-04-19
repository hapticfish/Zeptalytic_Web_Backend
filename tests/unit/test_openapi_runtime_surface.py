from app.main import app


def test_openapi_runtime_surface_exposes_frontend_critical_api_v1_paths() -> None:
    paths = app.openapi()["paths"]

    expected_paths = {
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/session",
        "/api/v1/profiles/me",
        "/api/v1/addresses/me",
        "/api/v1/communication-preferences/me",
        "/api/v1/dashboard/summary",
        "/api/v1/launcher/products",
        "/api/v1/billing/snapshot",
        "/api/v1/billing/subscriptions",
        "/api/v1/billing/payment-methods",
        "/api/v1/billing/transactions",
        "/api/v1/billing/checkout",
        "/api/v1/billing/subscription-change",
        "/api/v1/billing/subscription-cancel",
        "/api/v1/billing/subscription-restart",
        "/api/v1/billing/promo-code/validate",
        "/api/v1/billing/promo-code/apply",
        "/api/v1/support/tickets",
        "/api/v1/support/tickets/{ticket_id}",
        "/api/v1/announcements",
        "/api/v1/service-status",
        "/api/v1/rewards/me/summary",
        "/api/v1/rewards/me/objectives",
        "/api/v1/rewards/me/notifications",
        "/api/v1/rewards/me/notifications/{notification_id}/seen",
        "/api/v1/rewards/me/notifications/skip-all",
        "/api/v1/rewards/me/badges",
        "/api/v1/integrations/discord",
        "/api/v1/integrations/discord/connect",
        "/api/v1/integrations/discord/callback",
        "/api/v1/integrations/discord/disconnect",
    }

    assert expected_paths.issubset(paths)


def test_openapi_runtime_surface_excludes_hidden_contract_helper_paths() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/profiles/_contract" not in paths
    assert "/api/v1/addresses/_contract" not in paths
    assert "/api/v1/communication-preferences/_contract" not in paths
    assert "/api/v1/support/_contract" not in paths
