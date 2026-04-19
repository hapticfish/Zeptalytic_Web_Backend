from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import (
    get_auth_service,
    require_authenticated_session_context,
    require_normal_authenticated_session_context,
)
from app.core.config import settings
from app.schemas.auth import (
    AccountClosureRequest,
    AccountClosureResponse,
    AuthAccountSummary,
    AuthSecuritySummary,
    AuthSessionResponse,
    AuthSessionSummary,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    LogoutRequest,
    RevokeOtherSessionsResponse,
    RevokeSessionResponse,
    ResendEmailVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SessionDeviceListResponse,
    SessionDeviceSummary,
    SignupRequest,
    TwoFactorChallengeResponse,
    TwoFactorCodeChallengeRequest,
    TwoFactorEnrollmentResponse,
    TwoFactorProtectedActionRequest,
    TwoFactorRecoveryCodesResponse,
    TwoFactorVerifyRequest,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services import AuthClientInfo, AuthMutationResult, AuthService, AuthenticatedSessionContext

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_client_info(request: Request) -> AuthClientInfo:
    client_host = request.client.host if request.client is not None else None
    return AuthClientInfo(
        ip_address=client_host,
        user_agent=request.headers.get("user-agent"),
    )


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=session_token,
        max_age=settings.auth_session_ttl_hours * 60 * 60,
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
        path=settings.auth_session_cookie_path,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        path=settings.auth_session_cookie_path,
    )


def _build_auth_session_response(result: AuthMutationResult) -> AuthSessionResponse:
    context = result.context
    can_access_support = context.status in {"active", "pending_verification", "suspended"}
    can_access_billing = context.status in {"active", "suspended"}
    can_access_normal_authenticated_routes = (
        context.status == "active" and context.is_email_verified
    )
    return AuthSessionResponse(
        account=AuthAccountSummary(
            account_id=context.account_id,
            username=context.username,
            email=context.email,
            status=context.status,
            role=context.role,
            email_verified_at=context.email_verified_at,
        ),
        session=AuthSessionSummary(
            session_id=context.session_id,
            created_at=context.session_created_at,
            expires_at=context.session_expires_at,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        ),
        security=AuthSecuritySummary(
            email_verification_required=not context.is_email_verified,
            can_access_support=can_access_support,
            can_access_billing=can_access_billing,
            can_access_normal_authenticated_routes=can_access_normal_authenticated_routes,
            can_access_product_launch=can_access_normal_authenticated_routes,
            two_factor_enabled=context.two_factor_enabled,
            two_factor_method=context.two_factor_method,
            recovery_methods_available_count=context.recovery_methods_available_count,
            recovery_codes_generated_at=context.recovery_codes_generated_at,
        ),
    )


def _build_session_device_list_response(
    sessions: list,
) -> SessionDeviceListResponse:
    return SessionDeviceListResponse(
        sessions=[
            SessionDeviceSummary(
                session_id=session.session_id,
                created_at=session.created_at,
                expires_at=session.expires_at,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                is_current=session.is_current,
            )
            for session in sessions
        ]
    )


@router.post("/signup", response_model=AuthSessionResponse, status_code=201)
def signup(
    payload: SignupRequest,
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    result = auth_service.signup(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        client_info=_build_client_info(request),
    )
    _set_session_cookie(response, result.session_token)
    return _build_auth_session_response(result)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    result = auth_service.login(
        email=payload.email,
        password=payload.password,
        client_info=_build_client_info(request),
    )
    _set_session_cookie(response, result.session_token)
    return _build_auth_session_response(result)


@router.post("/verify-email", response_model=VerifyEmailResponse)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> VerifyEmailResponse:
    auth_service.verify_email(
        token=payload.token,
        client_info=_build_client_info(request),
    )
    return VerifyEmailResponse()


@router.post("/resend-verification", response_model=ResendEmailVerificationResponse)
def resend_verification(
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> ResendEmailVerificationResponse:
    auth_service.resend_email_verification(
        context=context,
        client_info=_build_client_info(request),
    )
    return ResendEmailVerificationResponse()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    auth_service.forgot_password(
        email=payload.email,
        client_info=_build_client_info(request),
    )
    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResetPasswordResponse:
    auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
        client_info=_build_client_info(request),
    )
    return ResetPasswordResponse()


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> ChangePasswordResponse:
    result = auth_service.change_password(
        context=context,
        current_password=payload.current_password,
        new_password=payload.new_password,
        client_info=_build_client_info(request),
    )
    _set_session_cookie(response, result.session_token)
    return ChangePasswordResponse()


@router.post("/logout", response_model=LogoutResponse)
def logout(
    payload: LogoutRequest,
    response: Response,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    auth_service.logout(
        context=context,
        client_info=_build_client_info(request),
        revoke_all_sessions=payload.revoke_all_sessions,
    )
    _clear_session_cookie(response)
    return LogoutResponse()


@router.get("/session", response_model=AuthSessionResponse)
def get_current_session(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
) -> AuthSessionResponse:
    return _build_auth_session_response(AuthMutationResult(session_token="", context=context))


@router.post("/2fa/enroll", response_model=TwoFactorEnrollmentResponse)
def enroll_two_factor(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorEnrollmentResponse:
    enrollment = auth_service.begin_two_factor_enrollment(context=context)
    return TwoFactorEnrollmentResponse(secret=enrollment.secret, otpauth_uri=enrollment.otpauth_uri)


@router.post("/2fa/verify", response_model=TwoFactorRecoveryCodesResponse)
def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorRecoveryCodesResponse:
    recovery_codes = auth_service.enable_two_factor(
        context=context,
        code=payload.code,
        client_info=_build_client_info(request),
    )
    return TwoFactorRecoveryCodesResponse(
        message="Two-factor authentication enabled.",
        recovery_codes=recovery_codes,
    )


@router.post("/2fa/challenge", response_model=TwoFactorChallengeResponse)
def challenge_two_factor(
    payload: TwoFactorCodeChallengeRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorChallengeResponse:
    auth_service.challenge_two_factor(
        context=context,
        code=payload.code,
        recovery_code=payload.recovery_code,
        client_info=_build_client_info(request),
    )
    return TwoFactorChallengeResponse()


@router.post("/2fa/recovery-codes/regenerate", response_model=TwoFactorRecoveryCodesResponse)
def regenerate_recovery_codes(
    payload: TwoFactorProtectedActionRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorRecoveryCodesResponse:
    recovery_codes = auth_service.regenerate_recovery_codes(
        context=context,
        current_password=payload.current_password,
        code=payload.code,
        recovery_code=payload.recovery_code,
        client_info=_build_client_info(request),
    )
    return TwoFactorRecoveryCodesResponse(
        message="Recovery codes regenerated successfully.",
        recovery_codes=recovery_codes,
    )


@router.post("/2fa/disable", response_model=LogoutResponse)
def disable_two_factor(
    payload: TwoFactorProtectedActionRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    auth_service.disable_two_factor(
        context=context,
        current_password=payload.current_password,
        code=payload.code,
        recovery_code=payload.recovery_code,
        client_info=_build_client_info(request),
    )
    return LogoutResponse(message="Two-factor authentication disabled.")


@router.get("/sessions", response_model=SessionDeviceListResponse)
def list_sessions(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionDeviceListResponse:
    return _build_session_device_list_response(auth_service.list_active_sessions(context=context))


@router.post("/sessions/{session_id}/revoke", response_model=RevokeSessionResponse)
def revoke_session(
    session_id: UUID,
    response: Response,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> RevokeSessionResponse:
    current_session_revoked = auth_service.revoke_session_by_id(
        context=context,
        session_id=session_id,
        client_info=_build_client_info(request),
    )
    if current_session_revoked:
        _clear_session_cookie(response)
    return RevokeSessionResponse()


@router.post("/sessions/revoke-others", response_model=RevokeOtherSessionsResponse)
def revoke_other_sessions(
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> RevokeOtherSessionsResponse:
    auth_service.revoke_other_sessions(
        context=context,
        client_info=_build_client_info(request),
    )
    return RevokeOtherSessionsResponse()


@router.post("/account-closure", response_model=AccountClosureResponse)
def close_account(
    payload: AccountClosureRequest,
    response: Response,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> AccountClosureResponse:
    auth_service.close_account(
        context=context,
        current_password=payload.current_password,
        code=payload.code,
        recovery_code=payload.recovery_code,
        client_info=_build_client_info(request),
    )
    _clear_session_cookie(response)
    return AccountClosureResponse()
