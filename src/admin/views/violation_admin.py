from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Optional

from src.admin.views.base_admin import BaseAdmin
from src.models.violation_model import ViolationModel
from src.models.enums import ViolationType, SeverityType


class ViolationAdmin(BaseAdmin, model=ViolationModel):
    name = "Violation"
    name_plural = "Violations"
    icon = "fa-solid fa-triangle-exclamation"
    category = "Rentals"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        ViolationModel.id,
        ViolationModel.rental_id,
        ViolationModel.geofence_event_id,
        ViolationModel.type,
        ViolationModel.severity,
        ViolationModel.created_at,
    ]

    column_searchable_list = []

    column_filters = [
        StaticValuesFilter(
            ViolationModel.type,
            values=[
                (t.value, t.value.replace("_", " ").title())
                for t in ViolationType
            ],
            title="Violation type",
        ),
        StaticValuesFilter(
            ViolationModel.severity,
            values=[
                (s.value, s.value.title())
                for s in SeverityType
            ],
            title="Severity",
        ),
        OperationColumnFilter(ViolationModel.rental_id, title="Rental ID"),
        OperationColumnFilter(ViolationModel.geofence_event_id, title="Geofence Event ID"),
    ]

    column_sortable_list = [
        ViolationModel.type,
        ViolationModel.severity,
        ViolationModel.created_at,
    ]

    column_default_sort = [(ViolationModel.created_at, True)]

    form_args = {
        "rental_id": {
            "validators": [DataRequired()]
        },
        "geofence_event_id": {
            "validators": [Optional()]
        },
        "type": {
            "validators": [Optional()]
        },
        "severity": {
            "validators": [Optional()]
        },
    }

    can_create = False
    can_edit = True
    can_delete = True

    @staticmethod
    def _format_type(model, attribute):
        violation_type = model.type

        if violation_type is None:
            return Markup('<span style="color: #999;">—</span>')

        type_config = {
            ViolationType.GEOFENCE_EXIT: {
                "icon": "🚫",
                "label": "Geofence Exit",
                "color": "#FF7043",
                "bg": "#FBE9E7"
            },
            ViolationType.SPEEDING: {
                "icon": "⚡",
                "label": "Speeding",
                "color": "#EF5350",
                "bg": "#FFEBEE"
            },
        }

        config = type_config.get(violation_type, {
            "icon": "⚠️",
            "label": violation_type.value.replace("_", " ").title(),
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
    def _format_severity(model, attribute):
        severity = model.severity

        if severity is None:
            return Markup('<span style="color: #999;">—</span>')

        severity_config = {
            SeverityType.WARNING: {
                "icon": "⚠️",
                "label": "Warning",
                "color": "#FF9800",
                "bg": "#FFF3E0"
            },
        }

        config = severity_config.get(severity, {
            "icon": "📋",
            "label": severity.value.title(),
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
    def _format_created_at(model, attribute):
        created_at = model.created_at

        if created_at is None:
            return "—"

        formatted_date = created_at.strftime("%Y-%m-%d %H:%M")

        return Markup(
            f'<span style="font-family: monospace;">{formatted_date}</span>'
        )

    @staticmethod
    def _format_ids(model, attribute):
        value = getattr(model, attribute, None)

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_violation_card(model, attribute):
        violation_type = model.type
        severity = model.severity
        created_at = model.created_at

        type_config = {
            ViolationType.GEOFENCE_EXIT: {
                "icon": "🚫",
                "label": "Geofence Exit",
                "color": "#FF7043",
                "bg": "#FBE9E7",
                "description": "Vehicle exited the designated geofence area"
            },
            ViolationType.SPEEDING: {
                "icon": "⚡",
                "label": "Speeding",
                "color": "#EF5350",
                "bg": "#FFEBEE",
                "description": "Vehicle exceeded the speed limit"
            },
        }

        severity_config = {
            SeverityType.WARNING: {
                "icon": "⚠️",
                "label": "Warning",
                "color": "#FF9800"
            },
        }

        type_info = type_config.get(violation_type, {
            "icon": "⚠️",
            "label": violation_type.value if violation_type else "Unknown",
            "color": "#757575",
            "bg": "#F5F5F5",
            "description": "Violation detected"
        })

        severity_info = severity_config.get(severity, {
            "icon": "📋",
            "label": severity.value if severity else "Unknown",
            "color": "#757575"
        })

        formatted_date = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "N/A"

        if severity == SeverityType.WARNING:
            gradient = "linear-gradient(135deg, #FF9800 0%, #F57C00 100%)"
        else:
            gradient = "linear-gradient(135deg, #F44336 0%, #D32F2F 100%)"

        return Markup(
            f'<div style="padding: 20px; background: {gradient}; '
            f'border-radius: 12px; color: white;">'
            f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">'
            f'<span style="font-size: 48px;">{type_info["icon"]}</span>'
            f'<div>'
            f'<div style="font-size: 24px; font-weight: 700; margin-bottom: 5px;">'
            f'{type_info["label"]}'
            f'</div>'
            f'<div style="font-size: 14px; opacity: 0.9;">{type_info["description"]}</div>'
            f'</div>'
            f'</div>'
            f'<div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;">'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">Severity</div>'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="font-size: 20px;">{severity_info["icon"]}</span>'
            f'<span style="font-size: 18px; font-weight: 600; color: {severity_info["color"]};">'
            f'{severity_info["label"]}'
            f'</span>'
            f'</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">Detected At</div>'
            f'<div style="font-family: monospace; font-size: 14px;">{formatted_date}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        ViolationModel.type: _format_type,
        ViolationModel.severity: _format_severity,
        ViolationModel.created_at: _format_created_at,
        ViolationModel.rental_id: lambda m, a: ViolationAdmin._format_ids(m, a),
        ViolationModel.geofence_event_id: lambda m, a: ViolationAdmin._format_ids(m, a),
        ViolationModel.id: lambda m, a: ViolationAdmin._format_ids(m, a),
    }

    column_formatters_detail = {
        ViolationModel.id: _format_violation_card,
        ViolationModel.type: _format_type,
        ViolationModel.severity: _format_severity,
        ViolationModel.rental_id: lambda m, a: ViolationAdmin._format_ids(m, a),
        ViolationModel.geofence_event_id: lambda m, a: ViolationAdmin._format_ids(m, a) if m.geofence_event_id else Markup('<span style="color: #999;">—</span>'),
    }
