import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import CategoriesType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.user_model import UserModel


class DriverLicenseModel(Base, IdMixin):
    __tablename__ = "driver_licenses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    license_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    issue_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expire_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    categories: Mapped[CategoriesType] = mapped_column(
        SqlEnum(
            CategoriesType,
            name="categories_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="driver_license", uselist=False, lazy="raise")
