import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UUID, DateTime, func, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import AgreementType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.user_model import UserModel


class AgreementModel(Base, IdMixin):
    __tablename__ = "agreements"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[AgreementType] = mapped_column(
        SqlEnum(
            AgreementType,
            name="agreement_type",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=AgreementType.PUBLIC_OFFER,
        nullable=False,
    )

    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="agreements", lazy="joined", uselist=False)
