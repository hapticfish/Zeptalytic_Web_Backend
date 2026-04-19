from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4

from app.api.routers.v1.announcements import router as announcements_router
from app.api.routers.v1.auth import router as auth_router
from app.api.routers.v1.addresses import router as addresses_router
from app.api.routers.v1.billing import router as billing_router
from app.api.routers.v1.communication_preferences import (
    router as communication_preferences_router,
)
from app.api.routers.v1.dashboard import router as dashboard_router
from app.api.routers.v1.integrations import router as integrations_router
from app.api.routers.v1.launcher import router as launcher_router
from app.api.routers.v1.profiles import router as profiles_router
from app.api.routers.v1.rewards import router as rewards_router
from app.api.routers.v1.service_status import router as service_status_router
from app.api.routers.v1.support import router as support_router
from app.schemas.addresses import (
    AddressDeleteResponse,
    AddressListResponse,
    AddressReadResponse,
    AddressRouteContractResponse,
    AddressSummary,
)
from app.schemas.announcements import AnnouncementListItem, AnnouncementListResponse
from app.schemas.auth import (
    AccountClosureResponse,
    AuthSessionResponse,
    ChangePasswordResponse,
    ForgotPasswordResponse,
    LogoutResponse,
    ResendEmailVerificationResponse,
    ResetPasswordResponse,
    RevokeOtherSessionsResponse,
    RevokeSessionResponse,
    SessionDeviceListResponse,
    TwoFactorEnrollmentResponse,
    TwoFactorChallengeResponse,
    TwoFactorRecoveryCodesResponse,
    VerifyEmailResponse,
)
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingAddressBookSummary,
    BillingAddressSummary,
    BillingPaymentMethodsResponse,
    BillingPaymentMethodSummary,
    BillingSnapshotPayProjectionSummary,
    BillingSnapshotResponse,
    BillingSubscriptionsResponse,
    BillingSubscriptionSummary,
    BillingTransactionsPage,
    BillingTransactionsResponse,
)
from app.schemas.common import CursorPageInfo, CursorPageResponse, MutationSuccessResponse
from app.schemas.communication_preferences import (
    CommunicationPreferenceReadResponse,
    CommunicationPreferenceRouteContractResponse,
)
from app.schemas.dashboard import (
    DashboardNotificationSummary,
    DashboardProgressSummary,
    DashboardSummaryResponse,
    DashboardSystemStatusSummary,
)
from app.schemas.integrations import DiscordConnectInitiationResponse, DiscordIntegrationReadResponse
from app.schemas.launcher import (
    LauncherPayProjectionSummary,
    LauncherProductSummary,
    LauncherProductsResponse,
)
from app.schemas.profiles import ProfileRouteContractResponse, ProfileSettingsReadResponse
from app.schemas.reward_badges import RewardBadgeGalleryResponse
from app.schemas.reward_notifications import (
    RewardNotificationQueueResponse,
    RewardNotificationSkipAllResponse,
    RewardNotificationStateChangeResponse,
)
from app.schemas.reward_objectives import RewardObjectivesResponse
from app.schemas.reward_summary import RewardSummaryResponse
from app.schemas.service_status import ServiceStatusListResponse
from app.schemas.support import (
    SupportRouteContractResponse,
    SupportTicketCreateResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
)


def _route_response_models(router) -> dict[tuple[str, tuple[str, ...]], object]:
    return {
        (route.path, tuple(sorted(route.methods or []))): route.response_model
        for route in router.routes
    }


def test_frontend_contract_regression_routes_lock_canonical_response_models() -> None:
    assert _route_response_models(auth_router) == {
        ("/auth/signup", ("POST",)): AuthSessionResponse,
        ("/auth/login", ("POST",)): AuthSessionResponse,
        ("/auth/verify-email", ("POST",)): VerifyEmailResponse,
        ("/auth/resend-verification", ("POST",)): ResendEmailVerificationResponse,
        ("/auth/forgot-password", ("POST",)): ForgotPasswordResponse,
        ("/auth/reset-password", ("POST",)): ResetPasswordResponse,
        ("/auth/change-password", ("POST",)): ChangePasswordResponse,
        ("/auth/logout", ("POST",)): LogoutResponse,
        ("/auth/session", ("GET",)): AuthSessionResponse,
        ("/auth/2fa/enroll", ("POST",)): TwoFactorEnrollmentResponse,
        ("/auth/2fa/verify", ("POST",)): TwoFactorRecoveryCodesResponse,
        ("/auth/2fa/challenge", ("POST",)): TwoFactorChallengeResponse,
        ("/auth/2fa/recovery-codes/regenerate", ("POST",)): TwoFactorRecoveryCodesResponse,
        ("/auth/2fa/disable", ("POST",)): LogoutResponse,
        ("/auth/sessions", ("GET",)): SessionDeviceListResponse,
        ("/auth/sessions/{session_id}/revoke", ("POST",)): RevokeSessionResponse,
        ("/auth/sessions/revoke-others", ("POST",)): RevokeOtherSessionsResponse,
        ("/auth/account-closure", ("POST",)): AccountClosureResponse,
    }
    assert _route_response_models(profiles_router) == {
        ("/profiles/_contract", ("GET",)): ProfileRouteContractResponse,
        ("/profiles/me", ("GET",)): ProfileSettingsReadResponse,
        ("/profiles/me", ("PATCH",)): ProfileSettingsReadResponse,
    }
    assert _route_response_models(addresses_router) == {
        ("/addresses/_contract", ("GET",)): AddressRouteContractResponse,
        ("/addresses/me", ("GET",)): AddressListResponse,
        ("/addresses/me", ("POST",)): AddressReadResponse,
        ("/addresses/me/{address_id}", ("PATCH",)): AddressReadResponse,
        ("/addresses/me/{address_id}", ("DELETE",)): AddressDeleteResponse,
        ("/addresses/me/{address_id}/primary", ("POST",)): AddressReadResponse,
    }
    assert _route_response_models(communication_preferences_router) == {
        ("/communication-preferences/_contract", ("GET",)): CommunicationPreferenceRouteContractResponse,
        ("/communication-preferences/me", ("GET",)): CommunicationPreferenceReadResponse,
        ("/communication-preferences/me", ("PATCH",)): CommunicationPreferenceReadResponse,
    }
    assert _route_response_models(dashboard_router) == {
        ("/dashboard/summary", ("GET",)): DashboardSummaryResponse,
    }
    assert _route_response_models(launcher_router) == {
        ("/launcher/products", ("GET",)): LauncherProductsResponse,
    }
    assert _route_response_models(billing_router) == {
        ("/billing/snapshot", ("GET",)): BillingSnapshotResponse,
        ("/billing/subscriptions", ("GET",)): BillingSubscriptionsResponse,
        ("/billing/payment-methods", ("GET",)): BillingPaymentMethodsResponse,
        ("/billing/transactions", ("GET",)): BillingTransactionsResponse,
        ("/billing/checkout", ("POST",)): BillingActionInitiationResponse,
        ("/billing/subscription-change", ("POST",)): BillingActionInitiationResponse,
        ("/billing/subscription-cancel", ("POST",)): BillingActionInitiationResponse,
        ("/billing/subscription-restart", ("POST",)): BillingActionInitiationResponse,
        ("/billing/promo-code/validate", ("POST",)): BillingActionInitiationResponse,
        ("/billing/promo-code/apply", ("POST",)): BillingActionInitiationResponse,
    }
    assert _route_response_models(support_router) == {
        ("/support/_contract", ("GET",)): SupportRouteContractResponse,
        ("/support/tickets", ("GET",)): SupportTicketListResponse,
        ("/support/tickets/{ticket_id}", ("GET",)): SupportTicketDetailResponse,
        ("/support/tickets", ("POST",)): SupportTicketCreateResponse,
    }
    assert _route_response_models(announcements_router) == {
        ("/announcements", ("GET",)): AnnouncementListResponse,
    }
    assert _route_response_models(service_status_router) == {
        ("/service-status", ("GET",)): ServiceStatusListResponse,
    }
    assert _route_response_models(integrations_router) == {
        ("/integrations/discord", ("GET",)): DiscordIntegrationReadResponse,
        ("/integrations/discord/connect", ("POST",)): DiscordConnectInitiationResponse,
        ("/integrations/discord/callback", ("GET",)): DiscordIntegrationReadResponse,
        ("/integrations/discord/disconnect", ("POST",)): DiscordIntegrationReadResponse,
    }
    assert _route_response_models(rewards_router) == {
        ("/rewards/me/badges", ("GET",)): RewardBadgeGalleryResponse,
        ("/rewards/me/notifications", ("GET",)): RewardNotificationQueueResponse,
        ("/rewards/me/notifications/{notification_id}/seen", ("POST",)): RewardNotificationStateChangeResponse,
        ("/rewards/me/notifications/skip-all", ("POST",)): RewardNotificationSkipAllResponse,
        ("/rewards/me/objectives", ("GET",)): RewardObjectivesResponse,
        ("/rewards/me/summary", ("GET",)): RewardSummaryResponse,
    }


def test_frontend_contract_regression_reuses_shared_mutation_and_pagination_contracts() -> None:
    mutation_models = [
        VerifyEmailResponse,
        ResendEmailVerificationResponse,
        ForgotPasswordResponse,
        ResetPasswordResponse,
        ChangePasswordResponse,
        LogoutResponse,
        TwoFactorChallengeResponse,
        TwoFactorRecoveryCodesResponse,
        RevokeSessionResponse,
        RevokeOtherSessionsResponse,
        AccountClosureResponse,
        ProfileRouteContractResponse,
        AddressDeleteResponse,
        AddressRouteContractResponse,
        CommunicationPreferenceRouteContractResponse,
        BillingActionInitiationResponse,
        SupportTicketCreateResponse,
        SupportRouteContractResponse,
    ]

    for response_model in mutation_models:
        assert issubclass(response_model, MutationSuccessResponse)

    for paged_model in [SupportTicketListResponse, AnnouncementListResponse, BillingTransactionsPage]:
        assert issubclass(paged_model, CursorPageResponse)


def test_frontend_contract_regression_preserves_pay_and_parent_ownership_nesting() -> None:
    now = datetime.now(UTC)
    response = DashboardSummaryResponse(
        launcher=LauncherProductsResponse(
            pay_integration_status="projection_only",
            products=[
                LauncherProductSummary(
                    product_code="zardbot",
                    product_name="ZardBot",
                    pay_projection=LauncherPayProjectionSummary(
                        entitlement_status="active",
                        subscription_status="active",
                        product_access_state="ready",
                        provisioning_state="complete",
                        last_synced_at=now,
                    ),
                    access_state="launchable",
                    can_launch=True,
                    launch_url="https://launch.example.com/zardbot",
                )
            ],
        ),
        billing=BillingSnapshotResponse(
            pay_integration_status="projection_only",
            pay_projection_billing=BillingSnapshotPayProjectionSummary(
                subscribed_products=[
                    BillingSubscriptionSummary(
                        source="pay_projection",
                        product_code="zardbot",
                        product_name="ZardBot",
                        plan_code="pro",
                        subscription_status="active",
                        billing_interval="monthly",
                        current_charge_amount_cents=4900,
                        currency="USD",
                        next_payment_at=now,
                    )
                ],
                current_payment_method=BillingPaymentMethodSummary(
                    source="pay_projection",
                    provider="stripe",
                    method_type="card",
                    display_label="Visa ending in 4242",
                    brand="visa",
                    last4="4242",
                    exp_month=12,
                    exp_year=2030,
                    is_default=True,
                    status="active",
                ),
            ),
            parent_billing_addresses=BillingAddressBookSummary(
                total_saved_count=1,
                addresses=[
                    BillingAddressSummary(
                        address_id=uuid4(),
                        address_type="billing",
                        full_name="Alex Zepta",
                        formatted_address="100 Main Street, Chicago, IL 60601, US",
                        country_code="US",
                        is_primary=True,
                    )
                ],
            ),
        ),
        parent_rewards_progress=DashboardProgressSummary(
            current_points=1250,
            current_tier="gold",
            current_milestone="milestone_1000",
            next_milestone="milestone_1500",
            points_to_next_milestone=250,
        ),
        parent_system_statuses=[
            DashboardSystemStatusSummary(
                product_code="zardbot",
                product_name="ZardBot",
                status="online",
                updated_at=now,
            )
        ],
        parent_notifications=[
            DashboardNotificationSummary(
                notification_type="announcement",
                title="Launcher update",
                body="Provisioning delays are resolved.",
                published_at=now,
            )
        ],
    )

    assert response.model_dump() == {
        "launcher": {
            "pay_integration_status": "projection_only",
            "products": [
                {
                    "product_code": "zardbot",
                    "product_name": "ZardBot",
                    "display_tag": None,
                    "pay_projection": {
                        "source": "pay_projection",
                        "entitlement_status": "active",
                        "subscription_status": "active",
                        "product_access_state": "ready",
                        "provisioning_state": "complete",
                        "last_synced_at": now,
                    },
                    "access_state": "launchable",
                    "can_launch": True,
                    "launch_url": "https://launch.example.com/zardbot",
                    "blocked_reason": None,
                    "status_message": None,
                }
            ],
        },
        "billing": {
            "pay_integration_status": "projection_only",
            "pay_projection_billing": {
                "source": "pay_projection",
                "subscribed_products": [
                    {
                        "source": "pay_projection",
                        "product_code": "zardbot",
                        "product_name": "ZardBot",
                        "plan_code": "pro",
                        "subscription_status": "active",
                        "billing_interval": "monthly",
                        "current_charge_amount_cents": 4900,
                        "currency": "USD",
                        "next_payment_at": now,
                        "cancel_at_period_end": False,
                    }
                ],
                "current_payment_method": {
                    "source": "pay_projection",
                    "provider": "stripe",
                    "method_type": "card",
                    "display_label": "Visa ending in 4242",
                    "brand": "visa",
                    "last4": "4242",
                    "wallet_first4": None,
                    "wallet_last4": None,
                    "exp_month": 12,
                    "exp_year": 2030,
                    "cardholder_name": None,
                    "billing_country": None,
                    "paypal_email_masked": None,
                    "is_default": True,
                    "last_used_at": None,
                    "status": "active",
                },
            },
            "parent_billing_addresses": {
                "source": "parent_owned",
                "total_saved_count": 1,
                "addresses": [
                    {
                        "address_id": response.billing.parent_billing_addresses.addresses[0].address_id,
                        "address_type": "billing",
                        "label": None,
                        "full_name": "Alex Zepta",
                        "formatted_address": "100 Main Street, Chicago, IL 60601, US",
                        "country_code": "US",
                        "is_primary": True,
                    }
                ],
            },
        },
        "parent_rewards_progress": {
            "source": "parent_owned",
            "current_points": 1250,
            "current_tier": "gold",
            "current_milestone": "milestone_1000",
            "next_milestone": "milestone_1500",
            "points_to_next_milestone": 250,
            "subscription_level_hint": None,
        },
        "parent_system_statuses": [
            {
                "source": "parent_owned",
                "product_code": "zardbot",
                "product_name": "ZardBot",
                "status": "online",
                "headline": None,
                "detail": None,
                "updated_at": now,
            }
        ],
        "parent_notifications": [
            {
                "source": "parent_owned",
                "notification_type": "announcement",
                "title": "Launcher update",
                "body": "Provisioning delays are resolved.",
                "published_at": now,
                "cta_label": None,
                "cta_url": None,
            }
        ],
    }


def test_frontend_contract_regression_safe_dtos_exclude_sensitive_fields() -> None:
    auth_session_fields = set(AuthSessionResponse.model_fields)
    profile_fields = set(ProfileSettingsReadResponse.model_fields)
    address_fields = set(AddressSummary.model_fields)
    billing_payment_method_fields = set(BillingPaymentMethodSummary.model_fields)
    rewards_fields = set(RewardSummaryResponse.model_fields)
    discord_summary_schema = DiscordIntegrationReadResponse.model_json_schema()
    profile_schema = ProfileSettingsReadResponse.model_json_schema()

    assert auth_session_fields == {"authenticated", "account", "session", "security"}
    assert profile_fields == {"profile"}
    assert "account_id" not in address_fields
    assert (
        "discord_user_id"
        not in profile_schema["$defs"]["DiscordProfileDisplaySummary"]["properties"]
    )
    assert {"card_number", "cvc", "provider_token", "provider_secret"}.isdisjoint(
        billing_payment_method_fields
    )
    assert (
        "discord_user_id"
        not in discord_summary_schema["$defs"]["DiscordIntegrationSummary"]["properties"]
    )
    assert {"password_hash", "recovery_codes", "two_factor_secret"}.isdisjoint(rewards_fields)


def test_frontend_contract_regression_representative_list_and_status_payloads_are_stable() -> None:
    now = datetime.now(UTC)

    announcement_response = AnnouncementListResponse(
        items=[
            AnnouncementListItem(
                announcement_id=uuid4(),
                scope="product",
                product_code="zardbot",
                title="Latency notice",
                body="Response times may be slower during maintenance.",
                severity="warning",
                published_at=now,
            )
        ],
        page=CursorPageInfo(limit=10, cursor=None, next_cursor="announcement_002"),
    )

    assert announcement_response.model_dump()["page"] == {
        "limit": 10,
        "cursor": None,
        "next_cursor": "announcement_002",
    }
