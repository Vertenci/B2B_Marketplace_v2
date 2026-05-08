import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, Numeric
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.enums import CarStatus
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.company_model import CompanyModel
    from src.models.iot_device_model import IotDeviceModel
    from src.models.geofence_model import GeofenceModel
    from src.models.rental_request_model import RentalRequestModel
    from src.models.rental_model import RentalModel
    from src.models.telemetry_model import TelemetryModel


class CarModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "cars"

    owner_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    brand: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    year: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    plate_number: Mapped[str] = mapped_column(
        String(7),
        unique=True,
        nullable=False,
    )

    vin: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    price_per_day: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    status: Mapped[CarStatus] = mapped_column(
        SqlEnum(
            CarStatus,
            name="car_status",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=CarStatus.HIDDEN,
        nullable=False,
    )

    company: Mapped["CompanyModel"] = relationship("CompanyModel", back_populates="cars", lazy="raise", uselist=False)

    iot_device: Mapped["IotDeviceModel | None"] = relationship("IotDeviceModel", back_populates="car", lazy="raise", uselist=False)

    geofences: Mapped[list["GeofenceModel"]] = relationship("GeofenceModel", back_populates="car", lazy="raise", uselist=True)

    rental_requests: Mapped[list["RentalRequestModel"]] = relationship("RentalRequestModel", back_populates="car", lazy="raise", uselist=True)

    rentals: Mapped[list["RentalModel"]] = relationship("RentalModel", back_populates="car", lazy="raise", uselist=True)

    telemetries: Mapped[list["TelemetryModel"]] = relationship("TelemetryModel", back_populates="car", lazy="raise", uselist=True)
