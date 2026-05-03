from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length

from src.admin.views.base_admin import BaseAdmin
from src.models.enums import RentalDocumentType
from src.models.rental_document_model import RentalDocumentsModel


class RentalDocumentsAdmin(BaseAdmin, model=RentalDocumentsModel):
    name = "Rental Document"
    name_plural = "Rental Documents"
    icon = "fa-solid fa-file"
    category = "Rentals"
    category_icon = "fa-solid fa-truck-moving"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        RentalDocumentsModel.id,
        RentalDocumentsModel.rental_id,
        RentalDocumentsModel.type,
        RentalDocumentsModel.file_path,
        RentalDocumentsModel.generated_at,
    ]

    column_searchable_list = [
        RentalDocumentsModel.file_path,
    ]

    column_filters = [
        StaticValuesFilter(
            RentalDocumentsModel.type,
            values=[
                (t.value, t.value.upper())
                for t in RentalDocumentType
            ],
            title="Document type",
        ),
        OperationColumnFilter(RentalDocumentsModel.rental_id, title="Rental ID"),
    ]

    column_sortable_list = [
        RentalDocumentsModel.type,
        RentalDocumentsModel.generated_at,
    ]

    column_default_sort = [(RentalDocumentsModel.generated_at, True)]

    form_args = {
        "rental_id": {
            "validators": [DataRequired()]
        },
        "type": {
            "validators": [DataRequired()]
        },
        "file_path": {
            "validators": [
                DataRequired(),
                Length(min=1, max=2048),
            ]
        },
    }

    can_create = False

    @staticmethod
    def _format_type(model, attribute):
        doc_type = model.type

        if doc_type is None:
            return "—"

        type_config = {
            RentalDocumentType.ACT: {
                "icon": "📋",
                "label": "Act",
                "color": "#5C6BC0",
                "bg": "#E8EAF6"
            },
            RentalDocumentType.INVOICE: {
                "icon": "🧾",
                "label": "Invoice",
                "color": "#26A69A",
                "bg": "#E0F2F1"
            },
            RentalDocumentType.CONTRACT: {
                "icon": "📄",
                "label": "Contract",
                "color": "#FF7043",
                "bg": "#FBE9E7"
            },
        }

        config = type_config.get(doc_type, {
            "icon": "📁",
            "label": doc_type.value,
            "color": "#757575",
            "bg": "#F5F5F5"
        })

        return Markup(
            f'<span style="display: inline-block; padding: 4px 10px; '
            f'background-color: {config["bg"]}; color: {config["color"]}; '
            f'border-radius: 12px; font-weight: 500; font-size: 13px;">'
            f'{config["icon"]} {config["label"]}'
            f'</span>'
        )

    @staticmethod
    def _format_file_path(model, attribute):
        file_path = model.file_path or ""

        if not file_path:
            return "—"

        filename = file_path.split("/")[-1] if "/" in file_path else file_path

        file_extension = filename.split(".")[-1].lower() if "." in filename else ""

        extension_icons = {
            "pdf": "📕",
            "doc": "📘",
            "docx": "📘",
            "xls": "📗",
            "xlsx": "📗",
            "jpg": "🖼️",
            "jpeg": "🖼️",
            "png": "🖼️",
        }

        icon = extension_icons.get(file_extension, "📁")

        max_length = 30
        if len(filename) > max_length:
            display_name = filename[:15] + "..." + filename[-12:]
        else:
            display_name = filename

        return Markup(
            f'<div>'
            f'<span style="margin-right: 5px;">{icon}</span>'
            f'<a href="{file_path}" target="_blank" '
            f'style="color: #1976D2; text-decoration: none; border-bottom: 1px dashed #1976D2;" '
            f'title="{file_path}">{display_name}</a>'
            f'</div>'
        )

    @staticmethod
    def _format_generated_at(model, attribute):
        generated_at = model.generated_at

        if generated_at is None:
            return "—"

        formatted_date = generated_at.strftime("%Y-%m-%d %H:%M")

        return Markup(
            f'<span style="font-family: monospace;">{formatted_date}</span>'
        )

    @staticmethod
    def _format_rental_id(model, attribute):
        value = model.rental_id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_id(model, attribute):
        value = model.id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_document_preview(model, attribute):
        doc_type = model.type
        file_path = model.file_path
        generated_at = model.generated_at

        type_config = {
            RentalDocumentType.ACT: {"icon": "📋", "label": "Act"},
            RentalDocumentType.INVOICE: {"icon": "🧾", "label": "Invoice"},
            RentalDocumentType.CONTRACT: {"icon": "📄", "label": "Contract"},
        }

        config = type_config.get(doc_type, {"icon": "📁", "label": doc_type.value if doc_type else "Document"})

        filename = file_path.split("/")[-1] if file_path and "/" in file_path else file_path or "Unknown"

        formatted_date = generated_at.strftime("%Y-%m-%d %H:%M") if generated_at else "N/A"

        return Markup(
            f'<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            f'border-radius: 12px; color: white;">'
            f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">'
            f'<span style="font-size: 48px;">{config["icon"]}</span>'
            f'<div>'
            f'<div style="font-size: 24px; font-weight: 700; margin-bottom: 5px;">{config["label"]}</div>'
            f'<div style="font-size: 14px; opacity: 0.9;">Generated: {formatted_date}</div>'
            f'</div>'
            f'</div>'
            f'<div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;">'
            f'<div style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">File</div>'
            f'<div style="font-family: monospace; word-break: break-all; font-size: 13px; margin-bottom: 15px;">'
            f'{filename}'
            f'</div>'
            f'<a href="{file_path}" target="_blank" '
            f'style="display: inline-block; padding: 8px 16px; background: white; color: #667eea; '
            f'text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">'
            f'📂 Open Document'
            f'</a>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        RentalDocumentsModel.type: _format_type,
        RentalDocumentsModel.file_path: _format_file_path,
        RentalDocumentsModel.generated_at: _format_generated_at,
        RentalDocumentsModel.rental_id: _format_rental_id,
        RentalDocumentsModel.id: _format_id,
    }

    column_formatters_detail = {
        RentalDocumentsModel.id: _format_document_preview,
        RentalDocumentsModel.type: _format_type,
        RentalDocumentsModel.file_path: _format_file_path,
        RentalDocumentsModel.rental_id: _format_rental_id,
    }
