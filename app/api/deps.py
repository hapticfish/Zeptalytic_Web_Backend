from collections.abc import Generator

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations import PayClient, build_pay_client
from app.services import (
    AnnouncementService,
    AddressService,
    AuthService,
    AuthenticationRequiredError,
    AuthenticatedSessionContext,
    BillingSummaryService,
    CommunicationPreferenceService,
    DashboardService,
    LauncherService,
    PayProjectionService,
    ProfileSettingsService,
    RewardBadgeService,
    RewardNotificationService,
    RewardObjectiveService,
    RewardSummaryService,
    ServiceStatusService,
    SupportService,
    build_announcement_service,
    build_address_service,
    build_auth_service,
    build_billing_summary_service,
    build_communication_preference_service,
    build_dashboard_service,
    build_launcher_service,
    build_pay_projection_service,
    build_profile_settings_service,
    build_reward_badge_service,
    build_reward_notification_service,
    build_reward_objective_service,
    build_reward_summary_service,
    build_service_status_service,
    build_support_service,
)


def get_settings():
    return settings


def get_pay_client(active_settings=Depends(get_settings)) -> PayClient:
    return build_pay_client(active_settings)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return build_auth_service(db)


def get_profile_settings_service(
    db: Session = Depends(get_db),
) -> ProfileSettingsService:
    return build_profile_settings_service(db)


def get_support_service(db: Session = Depends(get_db)) -> SupportService:
    return build_support_service(db)


def get_announcement_service(db: Session = Depends(get_db)) -> AnnouncementService:
    return build_announcement_service(db)


def get_service_status_service(db: Session = Depends(get_db)) -> ServiceStatusService:
    return build_service_status_service(db)


def get_address_service(db: Session = Depends(get_db)) -> AddressService:
    return build_address_service(db)


def get_communication_preference_service(
    db: Session = Depends(get_db),
) -> CommunicationPreferenceService:
    return build_communication_preference_service(db)


def get_reward_summary_service(db: Session = Depends(get_db)) -> RewardSummaryService:
    return build_reward_summary_service(db)


def get_reward_badge_service(db: Session = Depends(get_db)) -> RewardBadgeService:
    return build_reward_badge_service(db)


def get_reward_objective_service(db: Session = Depends(get_db)) -> RewardObjectiveService:
    return build_reward_objective_service(db)


def get_reward_notification_service(
    db: Session = Depends(get_db),
) -> RewardNotificationService:
    return build_reward_notification_service(db)


def get_pay_projection_service(
    db: Session = Depends(get_db),
    pay_client: PayClient = Depends(get_pay_client),
) -> PayProjectionService:
    return build_pay_projection_service(db, pay_client)


def get_launcher_service(
    pay_projection_service: PayProjectionService = Depends(get_pay_projection_service),
) -> LauncherService:
    return build_launcher_service(pay_projection_service)


def get_billing_summary_service(
    db: Session = Depends(get_db),
    pay_projection_service: PayProjectionService = Depends(get_pay_projection_service),
    pay_client: PayClient = Depends(get_pay_client),
) -> BillingSummaryService:
    return build_billing_summary_service(db, pay_projection_service, pay_client)


def get_dashboard_service(
    db: Session = Depends(get_db),
    launcher_service: LauncherService = Depends(get_launcher_service),
    billing_summary_service: BillingSummaryService = Depends(get_billing_summary_service),
) -> DashboardService:
    return build_dashboard_service(
        db,
        launcher_service,
        billing_summary_service,
        build_reward_summary_service(db),
    )


def get_optional_authenticated_session_context(
    session_token: str | None = Cookie(default=None, alias=settings.auth_session_cookie_name),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedSessionContext | None:
    return auth_service.get_authenticated_session_context(session_token)


def require_authenticated_session_context(
    context: AuthenticatedSessionContext | None = Depends(get_optional_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedSessionContext:
    if context is None:
        raise AuthenticationRequiredError("Authentication is required.")
    return auth_service.ensure_account_status_allows_authenticated_access(context)


def require_verified_session_context(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedSessionContext:
    return auth_service.ensure_email_verified(context)


def require_normal_authenticated_session_context(
    context: AuthenticatedSessionContext = Depends(require_verified_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedSessionContext:
    return auth_service.ensure_account_status_allows_normal_authenticated_actions(context)
