import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.car_model import CarModel


class IotDeviceModel(Base, IdMixin):
    __tablename__ = "iot_devices"

    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cars.id", ondelete="CASCADE"),
        nullable=False,
    )

    device_identifier: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    sim_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    battery_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __str__(self):
        return f"{self.device_identifier}"

    car: Mapped["CarModel"] = relationship("CarModel", back_populates="iot_device", lazy="raise", uselist=False)
