from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.billing import BillingAddressBookSummary, BillingSnapshotResponse
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.launcher import LauncherProductsResponse
from app.schemas.reward_summary import RewardSummaryNextMilestone, RewardSummaryResponse
from app.services.dashboard_service import DashboardService
from app.services.reward_summary_service import RewardSummaryNotFoundError


class StubLauncherService:
    def __init__(self, response: LauncherProductsResponse) -> None:
        self._response = response

    def get_products(self, context):  # noqa: ANN001
        del context
        return self._response


class StubBillingSummaryService:
    def __init__(self, response: BillingSnapshotResponse) -> None:
        self._response = response

    def get_snapshot(self, account_id):  # noqa: ANN001
        del account_id
        return self._response


class StubRewardSummaryService:
    def __init__(self, response: RewardSummaryResponse | None) -> None:
        self._response = response

    def get_summary(self, account_id):  # noqa: ANN001
        del account_id
        if self._response is None:
            raise RewardSummaryNotFoundError("missing")
        return self._response


class StubAnnouncementRecord:
    def __init__(self) -> None:
        self.title = "Planned maintenance"
        self.body = "Maintenance begins tonight."
        self.severity = "announcement"
        self.published_at = datetime(2026, 4, 18, 18, 0, tzinfo=timezone.utc)


class StubAnnouncementRepository:
    def list_active_announcements(self, *, limit: int = 10):  # noqa: ANN001
        assert limit == 10
        return [StubAnnouncementRecord()]


class StubServiceStatusRecord:
    def __init__(self) -> None:
        self.product_code = "zardbot"
        self.status = "online"
        self.message = "All systems nominal."
        self.updated_at = datetime(2026, 4, 18, 18, 5, tzinfo=timezone.utc)


class StubServiceStatusRepository:
    def list_current_statuses(self):
        return [StubServiceStatusRecord()]


class StubContext:
    def __init__(self, account_id) -> None:  # noqa: ANN001
        self.account_id = account_id


def test_dashboard_service_composes_launcher_billing_rewards_status_and_notifications() -> None:
    account_id = uuid4()
    service = DashboardService(
        launcher_service=StubLauncherService(
            LauncherProductsResponse(pay_integration_status="available", products=[])
        ),
        billing_summary_service=StubBillingSummaryService(
            BillingSnapshotResponse(
                pay_integration_status="available",
                pay_projection_billing=None,
                parent_billing_addresses=BillingAddressBookSummary(total_saved_count=0, addresses=[]),
            )
        ),
        reward_summary_service=StubRewardSummaryService(
            RewardSummaryResponse(
                account_id=account_id,
                current_points=1200,
                current_tier="gold",
                current_tier_progress_points=200,
                next_milestone=RewardSummaryNextMilestone(
                    milestone_points=1500,
                    points_remaining=300,
                    tier_code="gold",
                    is_tier_boundary=False,
                ),
                active_perks=[],
                earned_badges=[],
            )
        ),
        announcement_repository=StubAnnouncementRepository(),
        service_status_repository=StubServiceStatusRepository(),
    )

    response = service.get_summary(StubContext(account_id))

    assert isinstance(response, DashboardSummaryResponse)
    assert response.parent_rewards_progress is not None
    assert response.parent_rewards_progress.current_points == 1200
    assert response.parent_system_statuses[0].product_name == "ZardBot"
    assert response.parent_notifications[0].title == "Planned maintenance"


def test_dashboard_service_omits_rewards_progress_when_no_rewards_summary_exists() -> None:
    account_id = uuid4()
    service = DashboardService(
        launcher_service=StubLauncherService(
            LauncherProductsResponse(pay_integration_status="unavailable", products=[])
        ),
        billing_summary_service=StubBillingSummaryService(
            BillingSnapshotResponse(
                pay_integration_status="unavailable",
                pay_projection_billing=None,
                parent_billing_addresses=BillingAddressBookSummary(total_saved_count=0, addresses=[]),
            )
        ),
        reward_summary_service=StubRewardSummaryService(None),
        announcement_repository=StubAnnouncementRepository(),
        service_status_repository=StubServiceStatusRepository(),
    )

    response = service.get_summary(StubContext(account_id))

    assert response.parent_rewards_progress is None
    assert response.parent_system_statuses[0].status == "online"
