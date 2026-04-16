from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ObjectiveRewardLink(Base):
    __tablename__ = "objective_reward_links"
    __table_args__ = (
        Index("ix_objective_reward_links_objective_definition_id", "objective_definition_id"),
        Index("ix_objective_reward_links_reward_definition_id", "reward_definition_id"),
        Index(
            "uq_objective_reward_links_objective_reward",
            "objective_definition_id",
            "reward_definition_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    objective_definition_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("objective_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    reward_definition_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("reward_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    grant_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    objective_definition: Mapped["ObjectiveDefinition"] = relationship(
        back_populates="objective_reward_links"
    )
    reward_definition: Mapped["RewardDefinition"] = relationship(
        back_populates="objective_reward_links"
    )

