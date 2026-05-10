import logging
from datetime import datetime
from pathlib import Path
from io import BytesIO

from markupsafe import Markup
from sqladmin import ModelView
from sqlalchemy import select, update
from starlette.requests import Request
from wtforms import FileField
from wtforms.validators import DataRequired
import humanize

from src.clients.minio_client import minio_client
from src.db.session import db
from src.models.document_model import DocumentModel
from src.models.enums import AgreementType

logger = logging.getLogger(__name__)


class DocumentAdmin(ModelView, model=DocumentModel):
    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-file-contract"
    category = "Documents"

    page_size = 25

    column_list = [
        DocumentModel.title,
        DocumentModel.document_type,
        DocumentModel.version,
        DocumentModel.file_name,
        DocumentModel.file_size,
        DocumentModel.is_active,
        DocumentModel.published_at,
        DocumentModel.created_at,
    ]

    column_searchable_list = [
        DocumentModel.title,
        DocumentModel.file_name,
        DocumentModel.description,
    ]

    column_sortable_list = [
        DocumentModel.title,
        DocumentModel.document_type,
        DocumentModel.version,
        DocumentModel.is_active,
        DocumentModel.published_at,
        DocumentModel.created_at,
    ]

    column_default_sort = [(DocumentModel.created_at, True)]

    form_excluded_columns = [
        "file_path",
        "file_name",
        "file_size",
        "mime_type",
        "published_at",
        "created_at",
    ]

    form_args = {
        "title": {
            "validators": [DataRequired()]
        },
        "document_type": {
            "validators": [DataRequired()]
        },
        "version": {
            "validators": [DataRequired()]
        },
    }

    # ── Formatters ────────────────────────────────────────────────────────────

    @staticmethod
    def _format_file_size(model, attribute):
        if model.file_size:
            return humanize.naturalsize(model.file_size)
        return "—"

    @staticmethod
    def _format_document_type(model, attribute):
        type_colors = {
            AgreementType.PUBLIC_OFFER: "#1976D2",
            AgreementType.DRIVER_OFFER: "#388E3C",
        }
        color = type_colors.get(model.document_type, "#333")
        label = model.document_type.value.replace("_", " ").title()
        return Markup(
            f'<span style="color: {color}; font-weight: 600; '
            f'background: {color}22; padding: 2px 8px; border-radius: 4px;">'
            f'{label}</span>'
        )

    @staticmethod
    def _format_active_status(model, attribute):
        if model.is_active:
            return Markup(
                '<span style="display:inline-flex;align-items:center;gap:5px;">'
                '<span style="width:8px;height:8px;background:#4CAF50;border-radius:50%;'
                'display:inline-block;animation:pulse 1.5s infinite;"></span>'
                '<span style="color:#4CAF50;font-weight:600;">Active</span>'
                '</span>'
                '<style>@keyframes pulse{0%{opacity:1}50%{opacity:.4}100%{opacity:1}}</style>'
            )
        return Markup('<span style="color:#9E9E9E;">Inactive</span>')

    @staticmethod
    def _format_version(model, attribute):
        return Markup(
            f'<code style="background:#F5F5F5;padding:2px 6px;border-radius:3px;">'
            f'v{model.version}</code>'
        )

    column_formatters = {
        DocumentModel.file_size: _format_file_size,
        DocumentModel.document_type: _format_document_type,
        DocumentModel.is_active: _format_active_status,
        DocumentModel.version: _format_version,
    }

    # ── Form customization ────────────────────────────────────────────────────

    async def scaffold_form(self, rules=None):
        form_class = await super().scaffold_form(rules)
        form_class.file = FileField(
            "Document PDF File",
            description="Upload a new PDF file. Leave empty to keep existing file."
        )
        return form_class

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    async def on_model_change(self, data: dict, model, is_created: bool, request: Request):
        file = data.pop("file", None)

        # Загружаем файл если предоставлен
        if file and hasattr(file, "filename") and file.filename:
            file_content = await file.read()
            if file_content:
                file_data = BytesIO(file_content)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = Path(file.filename).suffix or ".pdf"

                doc_type_val = data.get("document_type") or getattr(model, "document_type", None)
                if doc_type_val:
                    doc_type = AgreementType(doc_type_val) if isinstance(doc_type_val, str) else doc_type_val
                else:
                    doc_type = AgreementType.PUBLIC_OFFER

                version = data.get("version") or getattr(model, "version", "1.0")
                object_name = f"{doc_type.value}/v{version}_{timestamp}{file_extension}"

                file_data.seek(0)
                await minio_client.upload_file(
                    file_data=file_data,
                    object_name=object_name,
                    content_type=file.content_type or "application/pdf",
                )

                data["file_path"] = object_name
                data["file_name"] = file.filename
                data["file_size"] = len(file_content)
                data["mime_type"] = file.content_type or "application/pdf"
                data["published_at"] = datetime.now()

        # Если документ помечается как активный — деактивируем все остальные
        # того же типа (только одна версия может быть активной)
        is_active = data.get("is_active")
        if is_active:
            doc_type_val = data.get("document_type") or getattr(model, "document_type", None)
            if doc_type_val:
                doc_type = AgreementType(doc_type_val) if isinstance(doc_type_val, str) else doc_type_val
                await self._deactivate_other_documents(doc_type, model.id if not is_created else None)

    async def _deactivate_other_documents(self, doc_type: AgreementType, exclude_id=None):
        """Деактивировать все остальные документы этого типа."""
        try:
            async with db.session_factory() as session:
                stmt = (
                    update(DocumentModel)
                    .where(
                        DocumentModel.document_type == doc_type,
                        DocumentModel.is_active == True,
                    )
                    .values(is_active=False)
                )
                if exclude_id:
                    from sqlalchemy import and_
                    stmt = (
                        update(DocumentModel)
                        .where(
                            DocumentModel.document_type == doc_type,
                            DocumentModel.is_active == True,
                            DocumentModel.id != exclude_id,
                        )
                        .values(is_active=False)
                    )
                await session.execute(stmt)
                await session.commit()
        except Exception as exc:
            logger.error(f"Failed to deactivate other documents: {exc}")

    async def after_model_change(self, data: dict, model, is_created: bool, request: Request):
        action = "Created" if is_created else "Updated"
        logger.info(f"[DocumentAdmin] {action}: '{model.title}' v{model.version} active={model.is_active}")

    async def delete_model(self, request: Request, pk):
        model = await self.get_object_for_delete(pk)

        if model and model.file_path:
            try:
                await minio_client.delete_file(model.file_path)
                logger.info(f"[DocumentAdmin] Deleted file from MinIO: {model.file_path}")
            except Exception as exc:
                logger.warning(f"[DocumentAdmin] Failed to delete MinIO file: {exc}")

        return await super().delete_model(request, pk)
