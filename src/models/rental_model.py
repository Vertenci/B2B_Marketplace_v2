import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, DateTime, func, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import RentalStatus
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.rental_request_model import RentalRequestModel
    from src.models.company_model import CompanyModel
    from src.models.car_model import CarModel
    from src.models.user_model import UserModel
    from src.models.payment_model import PaymentModel
    from src.models.rental_document_model import RentalDocumentsModel
    from src.models.telemetry_model import TelemetryModel
    from src.models.geofence_event_model import GeofenceEventModel
    from src.models.violation_model import ViolationModel


class RentalModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "rentals"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rental_requests.id"),
        nullable=False,
    )

    lessor_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    renter_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    actual_return_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now()
    )

    base_price_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    extra_days_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    status: Mapped[RentalStatus] = mapped_column(
        SqlEnum(
            RentalStatus,
            name="rental_status",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=RentalStatus.ACTIVE,
        nullable=False,
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __str__(self):
        return f"{self.id}"

    rental_request: Mapped["RentalRequestModel"] = relationship("RentalRequestModel", back_populates="rental", lazy="raise", uselist=False)

    lessor_company: Mapped["CompanyModel"] = relationship("CompanyModel", foreign_keys=[lessor_company_id], back_populates="lessor_rentals", lazy="raise", uselist=False)

    renter_company: Mapped["CompanyModel"] = relationship("CompanyModel", foreign_keys=[renter_company_id], back_populates="renter_rentals", lazy="raise", uselist=False)

    car: Mapped["CarModel"] = relationship("CarModel", back_populates="rentals", lazy="raise", uselist=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="rentals", lazy="raise", foreign_keys=[driver_id], uselist=False)

    payment: Mapped["PaymentModel"] = relationship("PaymentModel", back_populates="rental", lazy="raise", uselist=False)

    rental_documents: Mapped[list["RentalDocumentsModel"]] = relationship("RentalDocumentsModel", back_populates="rental", lazy="raise", uselist=True)

    telemetries: Mapped[list["TelemetryModel"]] = relationship("TelemetryModel", back_populates="rental", lazy="raise", uselist=True)

    geofence_events: Mapped[list["GeofenceEventModel"]] = relationship("GeofenceEventModel", back_populates="rental", lazy="raise", uselist=True)

    violations: Mapped[list["ViolationModel"]] = relationship("ViolationModel", back_populates="rental", lazy="raise", uselist=True)
