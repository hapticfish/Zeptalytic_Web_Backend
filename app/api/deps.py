from collections.abc import Generator

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.services import (
    AuthService,
    AuthenticationRequiredError,
    AuthenticatedSessionContext,
    build_auth_service,
)


def get_settings():
    return settings


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return build_auth_service(db)


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
