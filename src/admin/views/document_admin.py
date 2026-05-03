import logging
from datetime import datetime
from pathlib import Path
from io import BytesIO

from markupsafe import Markup
from sqladmin import ModelView
from starlette.requests import Request
from wtforms import FileField
from wtforms.validators import DataRequired
import humanize

from src.clients.minio_client import minio_client
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
        "published_at"
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

    @staticmethod
    def _format_file_size(model, attribute):
        if model.file_size:
            return humanize.naturalsize(model.file_size)
        return "—"

    @staticmethod
    def _format_document_type(model, attribute):
        type_colors = {
            AgreementType.PUBLIC_OFFER: "blue",
            AgreementType.DRIVER_OFFER: "green",
        }
        color = type_colors.get(model.document_type, "black")
        return Markup(
            f'<span style="color: {color}; font-weight: 500;">{model.document_type.value}</span>'
        )

    @staticmethod
    def _format_active_status(model, attribute):
        if model.is_active:
            return Markup('<span style="color: green;">✓ Active</span>')
        return Markup('<span style="color: gray;">✗ Inactive</span>')

    column_formatters = {
        DocumentModel.file_size: _format_file_size,
        DocumentModel.document_type: _format_document_type,
        DocumentModel.is_active: _format_active_status,
    }

    async def scaffold_form(self, rules=None):
        form_class = await super().scaffold_form(rules)

        form_class.file = FileField(
            "Document File",
            validators=[
                DataRequired(message="File is required")
            ],
            description="Upload PDF document"
        )

        return form_class

    async def on_model_change(self, data: dict, model, is_created: bool, request: Request):
        file = data.pop("file", None)

        if file and hasattr(file, 'filename') and file.filename:
            file_content = await file.read()
            file_data = BytesIO(file_content)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(file.filename).suffix

            doc_type = AgreementType(data.get("document_type") or model.document_type)
            version = data.get("version") or model.version

            object_name = f"{doc_type.value}/v{version}_{timestamp}{file_extension}"

            file_data.seek(0)
            await minio_client.upload_file(
                file_data=file_data,
                object_name=object_name,
                content_type=file.content_type or "application/pdf"
            )

            data["file_path"] = object_name
            data["file_name"] = file.filename
            data["file_size"] = len(file_content)
            data["mime_type"] = file.content_type or "application/pdf"
            data["published_at"] = datetime.now()

    async def after_model_change(self, data: dict, model, is_created: bool, request: Request):
        action = "Created" if is_created else "Updated"
        logger.info(f"{action} document: {model.title} v{model.version}")

    async def delete_model(self, request: Request, pk):
        model = await self.get_object_for_delete(pk)

        if model.file_path:
            try:
                await minio_client.delete_file(model.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file from MinIO: {e}")

        return await super().delete_model(request, pk)
