from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas import (
    AddressRouteContractResponse,
    AddressSummary,
    ApiErrorResponse,
    AnnouncementListResponse,
    CommunicationPreferenceRouteContractResponse,
    CommunicationPreferenceSummary,
    CursorPageInfo,
    CursorPageResponse,
    MutationSuccessResponse,
    ProfileRouteContractResponse,
    ProfileSettingsSummary,
    ServiceStatusListResponse,
    SupportTicketCreateRequest,
    SupportTicketListResponse,
)
from app.api.deps import get_pay_client, get_pay_projection_service
from app.integrations import (
    PayClient,
    PayClientConfigurationError,
    PayClientInvalidResponseError,
    PayClientUnavailableError,
    build_pay_client,
)
from app.services import (
    AnnouncementService,
    AddressService,
    AuthService,
    BillingSummaryService,
    CommunicationPreferenceService,
    DashboardService,
    SupportService,
    SupportTicketNotFoundError,
    SupportTicketValidationError,
    PayProjectionEntitlementSummary,
    PayProjectionPaymentMethodSummary,
    PayProjectionPaymentSummary,
    PayProjectionProductAccessState,
    PayProjectionService,
    ProfileSettingsService,
    LauncherService,
    RewardNotificationService,
    RewardObjectiveService,
    RewardSummaryNotFoundError,
    RewardSummaryService,
    ServiceStatusService,
    PayProjectionSubscriptionSummary,
    build_announcement_service,
    build_address_service,
    build_auth_service,
    build_billing_summary_service,
    build_communication_preference_service,
    build_dashboard_service,
    build_launcher_service,
    build_pay_projection_service,
    build_profile_settings_service,
    build_reward_notification_service,
    build_reward_objective_service,
    build_reward_summary_service,
    build_service_status_service,
    build_support_service,
)


class ExampleCursorItem(BaseModel):
    item_id: str
    label: str


def test_mutation_success_response_uses_standard_success_contract() -> None:
    response = MutationSuccessResponse(message="Profile updated.")

    assert response.model_dump(mode="json") == {
        "success": True,
        "message": "Profile updated.",
    }


def test_cursor_page_response_serializes_items_and_cursor_metadata() -> None:
    response = CursorPageResponse[ExampleCursorItem](
        items=[
            ExampleCursorItem(item_id="reward-1", label="Silver Reward"),
            ExampleCursorItem(item_id="reward-2", label="Gold Reward"),
        ],
        page=CursorPageInfo(limit=25, cursor="cursor_001", next_cursor="cursor_002"),
    )

    assert response.model_dump(mode="json") == {
        "items": [
            {"item_id": "reward-1", "label": "Silver Reward"},
            {"item_id": "reward-2", "label": "Gold Reward"},
        ],
        "page": {
            "limit": 25,
            "cursor": "cursor_001",
            "next_cursor": "cursor_002",
        },
    }


def test_cursor_page_info_requires_positive_limit() -> None:
    with pytest.raises(ValidationError):
        CursorPageInfo(limit=0)


def test_api_error_response_serializes_standard_contract() -> None:
    response = ApiErrorResponse.model_validate(
        {
            "error": {
                "code": "reward_summary_not_found",
                "message": "Reward summary not found.",
                "details": {"account_scope": "rewards"},
            }
        }
    )

    assert response.model_dump(exclude_none=True) == {
        "error": {
            "code": "reward_summary_not_found",
            "message": "Reward summary not found.",
            "details": {"account_scope": "rewards"},
        }
    }


def test_service_package_exports_reward_service_builders() -> None:
    assert build_announcement_service is not None
    assert build_address_service is not None
    assert build_auth_service is not None
    assert build_billing_summary_service is not None
    assert build_communication_preference_service is not None
    assert build_dashboard_service is not None
    assert build_launcher_service is not None
    assert build_pay_projection_service is not None
    assert build_profile_settings_service is not None
    assert build_reward_summary_service is not None
    assert build_service_status_service is not None
    assert build_reward_objective_service is not None
    assert build_reward_notification_service is not None
    assert build_support_service is not None
    assert AnnouncementService is not None
    assert AddressService is not None
    assert AuthService is not None
    assert BillingSummaryService is not None
    assert CommunicationPreferenceService is not None
    assert DashboardService is not None
    assert LauncherService is not None
    assert PayProjectionSubscriptionSummary is not None
    assert PayProjectionEntitlementSummary is not None
    assert PayProjectionPaymentSummary is not None
    assert PayProjectionPaymentMethodSummary is not None
    assert PayProjectionProductAccessState is not None
    assert PayProjectionService is not None
    assert ProfileSettingsService is not None
    assert RewardSummaryService is not None
    assert RewardSummaryNotFoundError is not None
    assert RewardObjectiveService is not None
    assert RewardNotificationService is not None
    assert ServiceStatusService is not None
    assert SupportService is not None
    assert SupportTicketNotFoundError is not None
    assert SupportTicketValidationError is not None


def test_pay_integration_package_exports_client_boundary() -> None:
    assert PayClient is not None
    assert build_pay_client is not None
    assert PayClientConfigurationError is not None
    assert PayClientUnavailableError is not None
    assert PayClientInvalidResponseError is not None
    assert get_pay_client is not None
    assert get_pay_projection_service is not None


def test_reward_router_modules_do_not_import_repositories_directly() -> None:
    router_modules = [
        Path("app/api/routers/rewards_summary.py"),
        Path("app/api/routers/reward_objectives.py"),
        Path("app/api/routers/reward_notifications.py"),
    ]

    for module_path in router_modules:
        parsed = ast.parse(module_path.read_text(encoding="utf-8"))
        direct_repository_imports = [
            node.module
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.db.repositories")
        ]
        assert direct_repository_imports == [], module_path.as_posix()


def test_settings_router_modules_do_not_import_repositories_directly() -> None:
    router_modules = {
        Path("app/api/routers/v1/profiles.py"): "require_normal_authenticated_session_context",
        Path("app/api/routers/v1/addresses.py"): "require_normal_authenticated_session_context",
        Path("app/api/routers/v1/communication_preferences.py"): "require_normal_authenticated_session_context",
        Path("app/api/routers/v1/support.py"): "require_authenticated_session_context",
        Path("app/api/routers/v1/announcements.py"): "require_authenticated_session_context",
        Path("app/api/routers/v1/service_status.py"): "require_authenticated_session_context",
        Path("app/api/routers/v1/dashboard.py"): "require_normal_authenticated_session_context",
        Path("app/api/routers/v1/launcher.py"): "require_normal_authenticated_session_context",
        Path("app/api/routers/v1/billing.py"): "require_authenticated_session_context",
    }

    for module_path, expected_dependency in router_modules.items():
        parsed = ast.parse(module_path.read_text(encoding="utf-8"))
        direct_repository_imports = [
            node.module
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.db.repositories")
        ]
        dependency_references = [
            node.id
            for node in ast.walk(parsed)
            if isinstance(node, ast.Name)
            and node.id == expected_dependency
        ]
        assert direct_repository_imports == [], module_path.as_posix()
        assert dependency_references, module_path.as_posix()


def test_reward_service_modules_define_repository_construction_boundary() -> None:
    service_modules = [
        Path("app/services/announcement_service.py"),
        Path("app/services/reward_summary_service.py"),
        Path("app/services/reward_objective_service.py"),
        Path("app/services/reward_notification_service.py"),
        Path("app/services/dashboard_service.py"),
        Path("app/services/billing_summary_service.py"),
        Path("app/services/service_status_service.py"),
    ]

    for module_path in service_modules:
        parsed = ast.parse(module_path.read_text(encoding="utf-8"))
        repository_imports = [
            node.module
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.db.repositories")
        ]
        builder_functions = [
            node.name
            for node in parsed.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("build_")
        ]

        assert repository_imports != [], module_path.as_posix()
        assert builder_functions != [], module_path.as_posix()


def test_settings_service_modules_define_repository_construction_boundary() -> None:
    service_modules = [
        Path("app/services/profile_settings_service.py"),
        Path("app/services/address_service.py"),
        Path("app/services/communication_preference_service.py"),
        Path("app/services/support_service.py"),
    ]

    for module_path in service_modules:
        parsed = ast.parse(module_path.read_text(encoding="utf-8"))
        repository_imports = [
            node.module
            for node in ast.walk(parsed)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("app.db.repositories")
        ]
        builder_functions = [
            node.name
            for node in parsed.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("build_")
        ]

        assert repository_imports != [], module_path.as_posix()
        assert builder_functions != [], module_path.as_posix()


def test_settings_schema_package_exports_contract_safe_dtos() -> None:
    assert ProfileSettingsSummary is not None
    assert AddressSummary is not None
    assert CommunicationPreferenceSummary is not None
    assert ProfileRouteContractResponse is not None
    assert AddressRouteContractResponse is not None
    assert CommunicationPreferenceRouteContractResponse is not None


def test_support_schema_package_exports_contract_safe_dtos() -> None:
    assert SupportTicketCreateRequest is not None
    assert SupportTicketListResponse is not None
    assert AnnouncementListResponse is not None
    assert ServiceStatusListResponse is not None
