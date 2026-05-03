from datetime import datetime
from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length, Optional

from src.admin.views.base_admin import BaseAdmin
from src.models.rental_request_model import RentalRequestModel
from src.models.enums import RentalRequestStatus


class RentalRequestAdmin(BaseAdmin, model=RentalRequestModel):
    name = "Rental Request"
    name_plural = "Rental Requests"
    icon = "fa-solid fa-paper-plane"
    category = "Rentals"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        RentalRequestModel.id,
        RentalRequestModel.renter_company_id,
        RentalRequestModel.car_id,
        RentalRequestModel.driver_id,
        RentalRequestModel.start_date,
        RentalRequestModel.end_date,
        RentalRequestModel.status,
        RentalRequestModel.created_at,
    ]

    column_searchable_list = [
        RentalRequestModel.message,
    ]

    column_filters = [
        StaticValuesFilter(
            RentalRequestModel.status,
            values=[
                (s.value, s.value.title())
                for s in RentalRequestStatus
            ],
            title="Request status",
        ),
        OperationColumnFilter(RentalRequestModel.renter_company_id, title="Renter Company ID"),
        OperationColumnFilter(RentalRequestModel.car_id, title="Car ID"),
        OperationColumnFilter(RentalRequestModel.driver_id, title="Driver ID"),
    ]

    column_sortable_list = [
        RentalRequestModel.start_date,
        RentalRequestModel.end_date,
        RentalRequestModel.status,
        RentalRequestModel.created_at,
    ]

    column_default_sort = [(RentalRequestModel.created_at, True)]

    form_args = {
        "renter_company_id": {
            "validators": [DataRequired()]
        },
        "car_id": {
            "validators": [DataRequired()]
        },
        "driver_id": {
            "validators": [DataRequired()]
        },
        "start_date": {
            "validators": [DataRequired()]
        },
        "end_date": {
            "validators": [DataRequired()]
        },
        "message": {
            "validators": [
                Optional(),
                Length(max=5000),
            ]
        },
        "status": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _format_status(model, attribute):
        status = model.status

        if status is None:
            return "—"

        status_config = {
            RentalRequestStatus.PENDING: {
                "color": "#FF9800",
                "bg": "#FFF3E0",
                "icon": "⏳",
                "text": "Pending"
            },
            RentalRequestStatus.APPROVED: {
                "color": "#4CAF50",
                "bg": "#E8F5E9",
                "icon": "✓",
                "text": "Approved"
            },
            RentalRequestStatus.REJECTED: {
                "color": "#F44336",
                "bg": "#FFEBEE",
                "icon": "✗",
                "text": "Rejected"
            },
            RentalRequestStatus.CANCELLED: {
                "color": "#9E9E9E",
                "bg": "#F5F5F5",
                "icon": "🚫",
                "text": "Cancelled"
            },
        }

        config = status_config.get(status, {
            "color": "#757575",
            "bg": "#F5F5F5",
            "icon": "",
            "text": status.value
        })

        return Markup(
            f'<span style="display: inline-block; padding: 4px 10px; '
            f'background-color: {config["bg"]}; color: {config["color"]}; '
            f'border-radius: 12px; font-weight: 500; font-size: 13px;">'
            f'{config["icon"]} {config["text"]}'
            f'</span>'
        )

    @staticmethod
    def _format_date_range(model, attribute):
        start = model.start_date
        end = model.end_date

        if start is None or end is None:
            return "—"

        duration_days = (end - start).days

        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        return Markup(
            f'<div>'
            f'<span style="font-family: monospace;">{start_str} — {end_str}</span><br>'
            f'<span style="font-size: 11px; color: #757575;">{duration_days} days</span>'
            f'</div>'
        )

    @staticmethod
    def _format_message_preview(model, attribute):
        message = model.message

        if not message:
            return Markup('<span style="color: #999; font-style: italic;">No message</span>')

        max_length = 50

        if len(message) <= max_length:
            return message

        short = message[:max_length] + "..."

        return Markup(
            f'<span title="{message}">{short}</span>'
        )

    @staticmethod
    def _format_created_at(model, attribute):
        created_at = model.created_at

        if created_at is None:
            return "—"

        now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
        time_diff = now.replace(tzinfo=None) - created_at.replace(tzinfo=None)

        formatted_date = created_at.strftime("%Y-%m-%d %H:%M")

        if time_diff.days == 0:
            if time_diff.seconds < 3600:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} min ago"
            else:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hours ago"
        elif time_diff.days == 1:
            time_ago = "Yesterday"
        elif time_diff.days < 7:
            time_ago = f"{time_diff.days} days ago"
        else:
            time_ago = formatted_date

        return Markup(
            f'<div>'
            f'<span style="font-family: monospace;">{formatted_date}</span><br>'
            f'<span style="font-size: 11px; color: #757575;">{time_ago}</span>'
            f'</div>'
        )

    @staticmethod
    def _format_ids(model, attr_name):
        value = getattr(model, attr_name, None)

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_request_summary(model, attribute):
        status = model.status
        start = model.start_date
        end = model.end_date
        message = model.message

        status_config = {
            RentalRequestStatus.PENDING: {"color": "#FF9800", "bg": "#FFF3E0", "icon": "⏳"},
            RentalRequestStatus.APPROVED: {"color": "#4CAF50", "bg": "#E8F5E9", "icon": "✓"},
            RentalRequestStatus.REJECTED: {"color": "#F44336", "bg": "#FFEBEE", "icon": "✗"},
            RentalRequestStatus.CANCELLED: {"color": "#9E9E9E", "bg": "#F5F5F5", "icon": "🚫"},
        }

        config = status_config.get(status, {"color": "#757575", "bg": "#F5F5F5", "icon": "📋"})

        if start and end:
            duration_days = (end - start).days
            date_range = f"{start.strftime('%Y-%m-%d')} — {end.strftime('%Y-%m-%d')}"
        else:
            duration_days = 0
            date_range = "N/A"

        return Markup(
            f'<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            f'border-radius: 12px; color: white;">'
            f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">'
            f'<span style="font-size: 48px;">{config["icon"]}</span>'
            f'<div>'
            f'<div style="display: inline-block; padding: 4px 12px; '
            f'background-color: {config["bg"]}; color: {config["color"]}; '
            f'border-radius: 20px; font-weight: 600; margin-bottom: 8px;">'
            f'{status.value if status else "N/A"}'
            f'</div>'
            f'<div style="font-size: 18px; font-weight: 600;">Rental Request</div>'
            f'</div>'
            f'</div>'
            f'<div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;">'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8;">Rental Period</div>'
            f'<div style="font-size: 14px; font-weight: 500;">{date_range}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8;">Duration</div>'
            f'<div style="font-size: 14px; font-weight: 500;">{duration_days} days</div>'
            f'</div>'
            f'</div>'
            f'{"<hr style=\"border: none; border-top: 1px solid rgba(255,255,255,0.2); margin: 15px 0;\">" if message else ""}'
            f'{"<div style=\"font-size: 12px; opacity: 0.8; margin-bottom: 5px;\">Message</div>" if message else ""}'
            f'{"<div style=\"font-size: 14px; line-height: 1.5;\">" + message + "</div>" if message else ""}'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        RentalRequestModel.status: _format_status,
        RentalRequestModel.message: _format_message_preview,
        RentalRequestModel.created_at: _format_created_at,
        RentalRequestModel.renter_company_id: lambda m, a: RentalRequestAdmin._format_ids(m, a),
        RentalRequestModel.car_id: lambda m, a: RentalRequestAdmin._format_ids(m, a),
        RentalRequestModel.driver_id: lambda m, a: RentalRequestAdmin._format_ids(m, a),
        RentalRequestModel.id: lambda m, a: RentalRequestAdmin._format_ids(m, a),
    }

    column_formatters_detail = {
        RentalRequestModel.id: _format_request_summary,
        RentalRequestModel.status: _format_status,
        RentalRequestModel.start_date: lambda m, a: RentalRequestAdmin._format_date_range(m, a),
        RentalRequestModel.message: lambda m, a: m.message or Markup('<span style="color: #999; font-style: italic;">No message</span>'),
    }
