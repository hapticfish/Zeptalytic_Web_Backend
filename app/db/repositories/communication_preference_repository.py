from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.communication_preferences import CommunicationPreference


@dataclass(slots=True)
class CommunicationPreferenceRecord:
    account_id: UUID
    marketing_emails_enabled: bool
    product_updates_enabled: bool
    announcement_emails_enabled: bool
    created_at: datetime
    updated_at: datetime


class CommunicationPreferenceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_account(self, account_id: UUID) -> CommunicationPreferenceRecord | None:
        preference = self._db.scalar(
            select(CommunicationPreference).where(CommunicationPreference.account_id == account_id)
        )
        if preference is None:
            return None

        return CommunicationPreferenceRecord(
            account_id=preference.account_id,
            marketing_emails_enabled=preference.marketing_emails_enabled,
            product_updates_enabled=preference.product_updates_enabled,
            announcement_emails_enabled=preference.announcement_emails_enabled,
            created_at=preference.created_at,
            updated_at=preference.updated_at,
        )
