import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import PaymentStatus, PaymentType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.rental_model import RentalModel
    from src.models.company_model import CompanyModel


class PaymentModel(Base, IdMixin):
    __tablename__ = "payments"

    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    )

    payer_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    receiver_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
    )

    commission_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now()
    )

    payment_method: Mapped[PaymentType] = mapped_column(
        SqlEnum(
            PaymentType,
            name="payment_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=PaymentType.BALANCE,
        nullable=False,
    )

    rental: Mapped["RentalModel"] = relationship("RentalModel", back_populates="payment", lazy="raise", uselist=False)

    payer_company: Mapped["CompanyModel"] = relationship("CompanyModel", foreign_keys=[payer_company_id], back_populates="payer_companies", lazy="raise", uselist=False)

    receiver_company: Mapped["CompanyModel"] = relationship("CompanyModel", foreign_keys=[receiver_company_id], back_populates="receiver_companies", lazy="raise", uselist=False)
