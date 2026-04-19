from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import MutationSuccessResponse


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=255)


class LogoutRequest(BaseModel):
    revoke_all_sessions: bool = False


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class OptionalTwoFactorCodeChallengeRequest(BaseModel):
    code: str | None = Field(default=None, min_length=6, max_length=12)
    recovery_code: str | None = Field(default=None, min_length=6, max_length=64)


class TwoFactorCodeChallengeRequest(OptionalTwoFactorCodeChallengeRequest):

    @model_validator(mode="after")
    def validate_factor_choice(self) -> "TwoFactorCodeChallengeRequest":
        if not self.code and not self.recovery_code:
            raise ValueError("Either code or recovery_code is required.")
        return self


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12)


class TwoFactorProtectedActionRequest(TwoFactorCodeChallengeRequest):
    current_password: str = Field(min_length=8, max_length=255)


class AccountClosureRequest(OptionalTwoFactorCodeChallengeRequest):
    current_password: str = Field(min_length=8, max_length=255)


class AuthAccountSummary(BaseModel):
    account_id: UUID
    username: str
    email: str
    status: Literal["active", "pending_verification", "suspended", "closed"]
    role: Literal["user", "admin", "super_admin"]
    email_verified_at: datetime | None = None


class AuthSessionSummary(BaseModel):
    session_id: UUID
    created_at: datetime
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None


class SessionDeviceSummary(BaseModel):
    session_id: UUID
    created_at: datetime
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    is_current: bool


class AuthSecuritySummary(BaseModel):
    email_verification_required: bool
    can_access_support: bool
    can_access_billing: bool
    can_access_normal_authenticated_routes: bool
    can_access_product_launch: bool
    two_factor_enabled: bool = False
    two_factor_method: Literal["totp"] | None = None
    recovery_methods_available_count: int = 0
    recovery_codes_generated_at: datetime | None = None


class AuthSessionResponse(BaseModel):
    authenticated: bool = True
    account: AuthAccountSummary
    session: AuthSessionSummary
    security: AuthSecuritySummary


class VerifyEmailResponse(MutationSuccessResponse):
    message: str = "Email verified successfully."


class TwoFactorEnrollmentResponse(BaseModel):
    secret: str
    otpauth_uri: str


class TwoFactorRecoveryCodesResponse(MutationSuccessResponse):
    message: str
    recovery_codes: list[str]


class TwoFactorChallengeResponse(MutationSuccessResponse):
    message: str = "Two-factor challenge verified."


class SessionDeviceListResponse(BaseModel):
    sessions: list[SessionDeviceSummary]


class ResendEmailVerificationResponse(MutationSuccessResponse):
    message: str = "Verification email sent."


class LogoutResponse(MutationSuccessResponse):
    message: str = "Logged out successfully."


class ForgotPasswordResponse(MutationSuccessResponse):
    message: str = "If the account exists, password reset instructions have been sent."


class ResetPasswordResponse(MutationSuccessResponse):
    message: str = "Password reset successfully."


class ChangePasswordResponse(MutationSuccessResponse):
    message: str = "Password changed successfully."


class RevokeSessionResponse(MutationSuccessResponse):
    message: str = "Session revoked successfully."


class RevokeOtherSessionsResponse(MutationSuccessResponse):
    message: str = "All other sessions revoked successfully."


class AccountClosureResponse(MutationSuccessResponse):
    message: str = "Account closed successfully."
