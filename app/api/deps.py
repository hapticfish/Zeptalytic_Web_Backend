from collections.abc import Generator

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations import PayClient, build_pay_client
from app.services import (
    AddressService,
    AuthService,
    AuthenticationRequiredError,
    AuthenticatedSessionContext,
    CommunicationPreferenceService,
    PayProjectionService,
    ProfileSettingsService,
    build_address_service,
    build_auth_service,
    build_communication_preference_service,
    build_pay_projection_service,
    build_profile_settings_service,
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


def get_address_service(db: Session = Depends(get_db)) -> AddressService:
    return build_address_service(db)


def get_communication_preference_service(
    db: Session = Depends(get_db),
) -> CommunicationPreferenceService:
    return build_communication_preference_service(db)


def get_pay_projection_service(
    db: Session = Depends(get_db),
    pay_client: PayClient = Depends(get_pay_client),
) -> PayProjectionService:
    return build_pay_projection_service(db, pay_client)


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
