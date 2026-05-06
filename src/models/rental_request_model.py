import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, ForeignKey, DateTime, func, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.db.base import Base
from src.models.enums import RentalRequestStatus
from src.models.mixin import CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from src.models.car_model import CarModel
    from src.models.user_model import UserModel
    from src.models.company_model import CompanyModel
    from src.models.rental_model import RentalModel


class RentalRequestModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "rental_requests"

    renter_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
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

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[RentalRequestStatus] = mapped_column(
        SqlEnum(
            RentalRequestStatus,
            name="rental_request_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=RentalRequestStatus.PENDING,
        nullable=False,
    )

    def __str__(self):
        return f"{self.id}"

    company: Mapped["CompanyModel"] = relationship("CompanyModel", back_populates="rental_requests", lazy="raise", uselist=False)

    car: Mapped["CarModel"] = relationship("CarModel", back_populates="rental_requests", lazy="raise", uselist=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="rental_requests", lazy="raise", uselist=False)

    rental: Mapped[Optional["RentalModel"]] = relationship("RentalModel", back_populates="rental_request", lazy="raise", uselist=False)
