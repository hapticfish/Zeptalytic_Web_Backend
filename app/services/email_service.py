from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.db.repositories.email_send_attempt_repository import (
    EmailSendAttemptRecord,
    EmailSendAttemptRepository,
)
from app.integrations import BrevoClient, BrevoTemplateEmailRequest
from app.schemas.email import EmailTemplateKey, build_email_template_catalog, resolve_email_sender_profile


@dataclass(frozen=True, slots=True)
class EmailSendResult:
    attempt_id: UUID
    template_key: EmailTemplateKey
    status: str
    provider: str
    provider_template_id: int | None
    provider_message_id: str | None
    failure_code: str | None
    failure_message: str | None

    @property
    def success(self) -> bool:
        return self.status == "sent"


class EmailService:
    def __init__(
        self,
        repository: EmailSendAttemptRepository,
        *,
        brevo_client: BrevoClient | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._brevo_client = brevo_client
        self._settings = app_settings or settings

    def send_signup_verification(
        self,
        *,
        account_id: UUID,
        to_email: str,
        verification_url: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        return self._send_template(
            template_key=EmailTemplateKey.EMAIL_VERIFICATION,
            account_id=account_id,
            to_email=to_email,
            to_name=display_name,
            params=self._build_template_params(
                displayName=display_name,
                verificationUrl=verification_url,
                expiresIn="24 hours",
            ),
            metadata={
                "flow": "signup",
                "token_type": "email_verification",
                "has_verification_url": True,
            },
        )

    def send_resend_verification(
        self,
        *,
        account_id: UUID,
        to_email: str,
        verification_url: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        return self._send_template(
            template_key=EmailTemplateKey.EMAIL_VERIFICATION,
            account_id=account_id,
            to_email=to_email,
            to_name=display_name,
            params=self._build_template_params(
                displayName=display_name,
                verificationUrl=verification_url,
                expiresIn="24 hours",
            ),
            metadata={
                "flow": "resend_verification",
                "token_type": "email_verification",
                "has_verification_url": True,
            },
        )

    def send_password_reset(
        self,
        *,
        account_id: UUID | None,
        to_email: str,
        reset_url: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        return self._send_template(
            template_key=EmailTemplateKey.PASSWORD_RESET,
            account_id=account_id,
            to_email=to_email,
            to_name=display_name,
            params=self._build_template_params(
                displayName=display_name,
                resetUrl=reset_url,
                expiresIn="2 hours",
            ),
            metadata={
                "flow": "forgot_password",
                "token_type": "password_reset",
                "has_reset_url": True,
            },
        )

    def send_welcome(
        self,
        *,
        account_id: UUID,
        to_email: str,
        display_name: str | None = None,
    ) -> EmailSendResult:
        return self._send_template(
            template_key=EmailTemplateKey.WELCOME,
            account_id=account_id,
            to_email=to_email,
            to_name=display_name,
            params=self._build_template_params(
                displayName=display_name,
                loginUrl=f"{self._settings.frontend_base_url}/login",
                dashboardUrl=f"{self._settings.frontend_base_url}/dashboard",
                supportEmail=self._settings.email_reply_to_address,
            ),
            metadata={"flow": "welcome"},
        )

    def send_account_details_changed(
        self,
        *,
        account_id: UUID,
        to_email: str,
        display_name: str | None = None,
        change_summary: str | None = None,
        changed_at: datetime | None = None,
    ) -> EmailSendResult:
        return self._send_template(
            template_key=EmailTemplateKey.ACCOUNT_DETAILS_CHANGED,
            account_id=account_id,
            to_email=to_email,
            to_name=display_name,
            params=self._build_template_params(
                displayName=display_name,
                changeSummary=change_summary,
                changedAt=changed_at.isoformat() if changed_at is not None else None,
                supportEmail=self._settings.email_support_from_address,
            ),
            metadata={
                "flow": "account_details_changed",
                "change_summary_present": change_summary is not None,
            },
        )

    def _send_template(
        self,
        *,
        template_key: EmailTemplateKey,
        account_id: UUID | None,
        to_email: str,
        to_name: str | None,
        params: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> EmailSendResult:
        catalog_entry = build_email_template_catalog(self._settings)[template_key]
        sender = resolve_email_sender_profile(template_key, self._settings)

        attempt = self._repository.create_send_attempt(
            account_id=account_id,
            to_email=to_email,
            from_email=sender.from_email,
            from_name=sender.from_name,
            reply_to_email=sender.reply_to_email,
            template_key=template_key.value,
            provider_template_id=catalog_entry.provider_template_id,
            status="pending",
            provider=self._settings.email_provider,
            metadata=metadata,
        )

        try:
            if self._settings.email_provider != "brevo":
                finalized_attempt = self._repository.mark_skipped(
                    attempt.attempt_id,
                    failure_code="provider_disabled",
                    failure_message="Transactional email provider is not enabled.",
                )
            elif self._brevo_client is None:
                finalized_attempt = self._repository.mark_failed(
                    attempt.attempt_id,
                    failure_code="provider_invalid_config",
                    failure_message="Brevo client is not configured.",
                )
            else:
                provider_result = self._brevo_client.send_template_email(
                    BrevoTemplateEmailRequest(
                        sender_name=sender.from_name,
                        sender_email=sender.from_email,
                        reply_to_name=sender.reply_to_name,
                        reply_to_email=sender.reply_to_email,
                        to_email=to_email,
                        to_name=to_name,
                        template_id=catalog_entry.provider_template_id,
                        params=params,
                    )
                )
                if provider_result.success:
                    finalized_attempt = self._repository.mark_sent(
                        attempt.attempt_id,
                        provider_message_id=provider_result.provider_message_id,
                    )
                else:
                    finalized_attempt = self._repository.mark_failed(
                        attempt.attempt_id,
                        failure_code=provider_result.failure_code or "provider_unexpected_response",
                        failure_message=provider_result.failure_message,
                    )

            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise

        if finalized_attempt is None:
            raise RuntimeError("Email send attempt could not be finalized.")
        return self._to_result(finalized_attempt, template_key=template_key)

    @staticmethod
    def _to_result(
        attempt: EmailSendAttemptRecord,
        *,
        template_key: EmailTemplateKey,
    ) -> EmailSendResult:
        return EmailSendResult(
            attempt_id=attempt.attempt_id,
            template_key=template_key,
            status=attempt.status,
            provider=attempt.provider,
            provider_template_id=attempt.provider_template_id,
            provider_message_id=attempt.provider_message_id,
            failure_code=attempt.failure_code,
            failure_message=attempt.failure_message,
        )

    @staticmethod
    def _build_template_params(**values: Any) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value is not None}


def build_email_service(
    db: Session,
    brevo_client: BrevoClient | None = None,
    *,
    app_settings: Settings | None = None,
) -> EmailService:
    return EmailService(
        EmailSendAttemptRepository(db),
        brevo_client=brevo_client,
        app_settings=app_settings,
    )
