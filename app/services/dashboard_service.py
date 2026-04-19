from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.announcement_repository import AnnouncementRepository
from app.db.repositories.service_status_repository import ServiceStatusRepository
from app.schemas.dashboard import (
    DashboardNotificationSummary,
    DashboardProgressSummary,
    DashboardSummaryResponse,
    DashboardSystemStatusSummary,
)
from app.services.auth_service import AuthenticatedSessionContext
from app.services.billing_summary_service import BillingSummaryService
from app.services.launcher_service import LauncherService
from app.services.reward_summary_service import RewardSummaryNotFoundError, RewardSummaryService

PRODUCT_NAMES = {
    "altra": "ALTRA",
    "zardbot": "ZardBot",
    "zepta": "Zepta",
}


class DashboardService:
    def __init__(
        self,
        launcher_service: LauncherService,
        billing_summary_service: BillingSummaryService,
        reward_summary_service: RewardSummaryService,
        announcement_repository: AnnouncementRepository,
        service_status_repository: ServiceStatusRepository,
    ) -> None:
        self._launcher_service = launcher_service
        self._billing_summary_service = billing_summary_service
        self._reward_summary_service = reward_summary_service
        self._announcement_repository = announcement_repository
        self._service_status_repository = service_status_repository

    def get_summary(self, context: AuthenticatedSessionContext) -> DashboardSummaryResponse:
        launcher = self._launcher_service.get_products(context)
        billing = self._billing_summary_service.get_snapshot(context.account_id)

        return DashboardSummaryResponse(
            launcher=launcher,
            billing=billing,
            parent_rewards_progress=self._build_rewards_progress(context.account_id, billing),
            parent_system_statuses=self._build_system_statuses(),
            parent_notifications=self._build_notifications(),
        )

    def _build_rewards_progress(self, account_id, billing):  # noqa: ANN001
        try:
            reward_summary = self._reward_summary_service.get_summary(account_id)
        except RewardSummaryNotFoundError:
            return None

        subscription_level_hint = None
        if (
            billing.pay_projection_billing is not None
            and billing.pay_projection_billing.subscribed_products
        ):
            subscription_level_hint = billing.pay_projection_billing.subscribed_products[0].plan_code

        next_milestone = reward_summary.next_milestone
        current_milestone = None
        if next_milestone is not None:
            current_milestone = str(
                max(next_milestone.milestone_points - next_milestone.points_remaining, 0)
            )

        return DashboardProgressSummary(
            current_points=reward_summary.current_points,
            current_tier=reward_summary.current_tier,
            current_milestone=current_milestone,
            next_milestone=None if next_milestone is None else str(next_milestone.milestone_points),
            points_to_next_milestone=None if next_milestone is None else next_milestone.points_remaining,
            subscription_level_hint=subscription_level_hint,
        )

    def _build_system_statuses(self) -> list[DashboardSystemStatusSummary]:
        return [
            DashboardSystemStatusSummary(
                product_code=record.product_code,
                product_name=PRODUCT_NAMES.get(
                    record.product_code,
                    record.product_code.replace("-", " ").title(),
                ),
                status=record.status,
                headline=record.message,
                detail=record.message,
                updated_at=record.updated_at,
            )
            for record in self._service_status_repository.list_current_statuses()
        ]

    def _build_notifications(self) -> list[DashboardNotificationSummary]:
        return [
            DashboardNotificationSummary(
                notification_type=record.severity,
                title=record.title,
                body=record.body,
                published_at=record.published_at,
            )
            for record in self._announcement_repository.list_active_announcements(limit=10)
        ]


def build_dashboard_service(
    db: Session,
    launcher_service: LauncherService,
    billing_summary_service: BillingSummaryService,
    reward_summary_service: RewardSummaryService,
) -> DashboardService:
    return DashboardService(
        launcher_service=launcher_service,
        billing_summary_service=billing_summary_service,
        reward_summary_service=reward_summary_service,
        announcement_repository=AnnouncementRepository(db),
        service_status_repository=ServiceStatusRepository(db),
    )
