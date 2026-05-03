import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.enums import ViolationType, SeverityType
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.rental_model import RentalModel
    from src.models.geofence_event_model import GeofenceEventModel


class ViolationModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "violations"

    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    )

    geofence_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geofence_events.id", ondelete="CASCADE"),
        nullable=True,
    )

    type: Mapped[ViolationType | None] = mapped_column(
        SqlEnum(
            ViolationType,
            name="violation_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=True,
    )

    severity: Mapped[SeverityType | None] = mapped_column(
        SqlEnum(
            SeverityType,
            name="severity_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=True,
    )

    rental: Mapped["RentalModel"] = relationship("RentalModel", back_populates="violations", lazy="joined", uselist=False)

    geofence_event: Mapped["GeofenceEventModel"] = relationship("GeofenceEventModel", back_populates="violations", lazy="joined", uselist=False)
