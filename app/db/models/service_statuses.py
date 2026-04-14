from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServiceStatus(Base):
    __tablename__ = "service_statuses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # TODO(john): Lock the service-status vocabulary in the dashboard/status spec.
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
