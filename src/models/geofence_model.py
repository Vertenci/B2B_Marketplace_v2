import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.car_model import CarModel
    from src.models.geofence_event_model import GeofenceEventModel


class GeofenceModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "geofences"

    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    center_lat: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    center_lng: Mapped[Decimal] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    radius_meters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    def __str__(self):
        return f"{self.name}"

    car: Mapped["CarModel"] = relationship("CarModel", back_populates="geofences", lazy="raise", uselist=False)

    geofence_events: Mapped[list["GeofenceEventModel"]] = relationship("GeofenceEventModel", back_populates="geofence", lazy="raise", uselist=True)
