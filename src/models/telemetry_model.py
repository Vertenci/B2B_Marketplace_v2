import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Numeric, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.rental_model import RentalModel
    from src.models.car_model import CarModel
    from src.models.user_model import UserModel


class TelemetryModel(Base, IdMixin):
    __tablename__ = "telemetries"

    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
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

    lat: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    lng: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    speed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    def __str__(self):
        return f"{self.id}"

    rental: Mapped["RentalModel"] = relationship("RentalModel", back_populates="telemetries", lazy="raise", uselist=False)

    car: Mapped["CarModel"] = relationship("CarModel", back_populates="telemetries", lazy="raise", uselist=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="telemetries", lazy="raise", uselist=False)
