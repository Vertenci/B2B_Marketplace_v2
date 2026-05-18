import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import BalanceEventType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.company_model import CompanyModel


class BalanceEventModel(Base, IdMixin):
    __tablename__ = "balance_events"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_type: Mapped[BalanceEventType] = mapped_column(
        SqlEnum(
            BalanceEventType,
            name="balance_event_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    operation_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["CompanyModel"] = relationship("CompanyModel", back_populates="balance_events", lazy="raise", uselist=False)
