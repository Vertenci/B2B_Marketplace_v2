import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import CompanyRole
from src.models.mixin import IdMixin, CreatedAtMixin

if TYPE_CHECKING:
    from src.models.user_model import UserModel
    from src.models.company_model import CompanyModel


class CompanyUserModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "company_users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    position: Mapped[CompanyRole] = mapped_column(
        SqlEnum(
            CompanyRole,
            name="company_role",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=CompanyRole.DRIVER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="company_users", lazy="raise", uselist=False)

    company: Mapped["CompanyModel"] = relationship("CompanyModel", back_populates="company_users", lazy="raise", uselist=False)
