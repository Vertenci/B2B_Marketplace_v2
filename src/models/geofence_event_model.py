import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import GeofenceType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.rental_model import RentalModel
    from src.models.geofence_model import GeofenceModel
    from src.models.violation_model import ViolationModel


class GeofenceEventModel(Base, IdMixin):
    __tablename__ = "geofence_events"

    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    )

    geofence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geofences.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[GeofenceType] = mapped_column(
        SqlEnum(
            GeofenceType,
            name="geofence_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
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

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    rental: Mapped["RentalModel"] = relationship("RentalModel", back_populates="geofence_events", lazy="raise", uselist=False)

    geofence: Mapped["GeofenceModel"] = relationship("GeofenceModel", back_populates="geofence_events", lazy="raise", uselist=False)

    violations: Mapped[list["ViolationModel"] | None] = relationship("ViolationModel", back_populates="geofence_event", lazy="raise", uselist=True)
