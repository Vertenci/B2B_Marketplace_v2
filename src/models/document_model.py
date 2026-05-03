from datetime import datetime

from sqlalchemy import DateTime, Boolean, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SqlEnum

from src.db.base import Base
from src.models.enums import AgreementType
from src.models.mixin import IdMixin, CreatedAtMixin


class DocumentModel(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    document_type: Mapped[AgreementType] = mapped_column(
        SqlEnum(
            AgreementType,
            name="document_type_enum",
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0"
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Путь к файлу в MinIO (bucket/path/file.pdf)"
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Размер файла в байтах"
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="application/pdf"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Актуальная версия документа"
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата публикации документа"
    )

    def __repr__(self):
        return f"<Document {self.title} v{self.version}>"
