import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import RentalDocumentType
from src.models.mixin import IdMixin

if TYPE_CHECKING:
    from src.models.rental_model import RentalModel


class RentalDocumentsModel(Base, IdMixin):
    __tablename__ = "rental_documents"

    rental_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[RentalDocumentType] = mapped_column(
        SqlEnum(
            RentalDocumentType,
            name="rental_document_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=RentalDocumentType.ACT,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    rental: Mapped["RentalModel"] = relationship("RentalModel", back_populates="rental_documents", uselist=False, lazy="raise")
