from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.errors import build_error_response
from app.services.auth_service import (
    AccountAccessRestrictedError,
    AuthenticationRequiredError,
    CurrentPasswordInvalidError,
    DuplicateAccountError,
    EmailVerificationRequiredError,
    EmailVerificationTokenInvalidError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
    SessionNotFoundError,
    TwoFactorAlreadyEnabledError,
    TwoFactorCodeInvalidError,
    TwoFactorNotEnabledError,
)
from app.services.reward_notification_service import (
    RewardNotificationNotFoundError,
    RewardNotificationQueueNotFoundError,
)
from app.services.reward_objective_service import RewardObjectivesNotFoundError
from app.services.reward_summary_service import RewardSummaryNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthenticationRequiredError, authentication_required_handler)
    app.add_exception_handler(
        EmailVerificationRequiredError,
        email_verification_required_handler,
    )
    app.add_exception_handler(
        AccountAccessRestrictedError,
        account_access_restricted_handler,
    )
    app.add_exception_handler(DuplicateAccountError, duplicate_account_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(
        EmailVerificationTokenInvalidError,
        email_verification_token_invalid_handler,
    )
    app.add_exception_handler(
        PasswordResetTokenInvalidError,
        password_reset_token_invalid_handler,
    )
    app.add_exception_handler(
        CurrentPasswordInvalidError,
        current_password_invalid_handler,
    )
    app.add_exception_handler(TwoFactorNotEnabledError, two_factor_not_enabled_handler)
    app.add_exception_handler(
        TwoFactorAlreadyEnabledError,
        two_factor_already_enabled_handler,
    )
    app.add_exception_handler(TwoFactorCodeInvalidError, two_factor_code_invalid_handler)
    app.add_exception_handler(SessionNotFoundError, session_not_found_handler)
    app.add_exception_handler(RewardSummaryNotFoundError, reward_summary_not_found_handler)
    app.add_exception_handler(RewardObjectivesNotFoundError, reward_objectives_not_found_handler)
    app.add_exception_handler(
        RewardNotificationQueueNotFoundError,
        reward_notification_queue_not_found_handler,
    )
    app.add_exception_handler(
        RewardNotificationNotFoundError,
        reward_notification_not_found_handler,
    )
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def reward_summary_not_found_handler(
    request: Request,
    exc: RewardSummaryNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_summary_not_found",
        message="Reward summary not found.",
        request_id=_request_id(request),
    )


async def authentication_required_handler(
    request: Request,
    exc: AuthenticationRequiredError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="authentication_required",
        message="Authentication is required.",
        request_id=_request_id(request),
    )


async def email_verification_required_handler(
    request: Request,
    exc: EmailVerificationRequiredError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        code="email_verification_required",
        message="Email verification is required.",
        request_id=_request_id(request),
    )


async def account_access_restricted_handler(
    request: Request,
    exc: AccountAccessRestrictedError,
) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        code="account_access_restricted",
        message="Account access is restricted.",
        details={"status": exc.status},
        request_id=_request_id(request),
    )


async def duplicate_account_handler(
    request: Request,
    exc: DuplicateAccountError,
) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="account_already_exists",
        message="An account with that username or email already exists.",
        details={"conflicts": exc.conflicts},
        request_id=_request_id(request),
    )


async def invalid_credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="invalid_credentials",
        message="Invalid email or password.",
        request_id=_request_id(request),
    )


async def email_verification_token_invalid_handler(
    request: Request,
    exc: EmailVerificationTokenInvalidError,
) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="email_verification_token_invalid",
        message="The email verification link is invalid or expired.",
        details={"reason": exc.reason},
        request_id=_request_id(request),
    )


async def password_reset_token_invalid_handler(
    request: Request,
    exc: PasswordResetTokenInvalidError,
) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="password_reset_token_invalid",
        message="The password reset link is invalid or expired.",
        details={"reason": exc.reason},
        request_id=_request_id(request),
    )


async def current_password_invalid_handler(
    request: Request,
    exc: CurrentPasswordInvalidError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="current_password_invalid",
        message="The current password is incorrect.",
        request_id=_request_id(request),
    )


async def two_factor_not_enabled_handler(
    request: Request,
    exc: TwoFactorNotEnabledError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="two_factor_not_enabled",
        message="Two-factor authentication is not enabled.",
        request_id=_request_id(request),
    )


async def two_factor_already_enabled_handler(
    request: Request,
    exc: TwoFactorAlreadyEnabledError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="two_factor_already_enabled",
        message="Two-factor authentication is already enabled.",
        request_id=_request_id(request),
    )


async def two_factor_code_invalid_handler(
    request: Request,
    exc: TwoFactorCodeInvalidError,
) -> JSONResponse:
    return build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="two_factor_code_invalid",
        message="The two-factor code is invalid.",
        details={"reason": exc.reason},
        request_id=_request_id(request),
    )


async def session_not_found_handler(
    request: Request,
    exc: SessionNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="session_not_found",
        message="Session not found.",
        request_id=_request_id(request),
    )


async def reward_objectives_not_found_handler(
    request: Request,
    exc: RewardObjectivesNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_objectives_not_found",
        message="Reward objectives not found.",
        request_id=_request_id(request),
    )


async def reward_notification_queue_not_found_handler(
    request: Request,
    exc: RewardNotificationQueueNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_notification_queue_not_found",
        message="Reward notification queue not found.",
        request_id=_request_id(request),
    )


async def reward_notification_not_found_handler(
    request: Request,
    exc: RewardNotificationNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_notification_not_found",
        message="Reward notification not found.",
        request_id=_request_id(request),
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = {
        "errors": [
            {
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
    }
    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="validation_error",
        message="Request validation failed.",
        details=details,
        request_id=_request_id(request),
    )
