from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter, BooleanFilter
from wtforms.validators import DataRequired, NumberRange

from src.admin.views.base_admin import BaseAdmin
from src.models.rental_model import RentalModel
from src.models.enums import RentalStatus


class RentalAdmin(BaseAdmin, model=RentalModel):
    name = "Rental"
    name_plural = "Rentals"
    icon = "fa-solid fa-file-contract"
    category = "Rentals"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        RentalModel.id,
        RentalModel.start_date,
        RentalModel.end_date,
        RentalModel.base_price_total,
        RentalModel.status,
        RentalModel.is_paid,
        RentalModel.created_at,
    ]

    column_searchable_list = []

    column_filters = [
        StaticValuesFilter(
            RentalModel.status,
            values=[
                (s.value, s.value.title())
                for s in RentalStatus
            ],
            title="Rental status",
        ),
        BooleanFilter(RentalModel.is_paid),
        OperationColumnFilter(RentalModel.car_id, title="Car ID"),
        OperationColumnFilter(RentalModel.driver_id, title="Driver ID"),
        OperationColumnFilter(RentalModel.lessor_company_id, title="Lessor Company ID"),
        OperationColumnFilter(RentalModel.renter_company_id, title="Renter Company ID"),
        OperationColumnFilter(RentalModel.base_price_total, title="Base price"),
        OperationColumnFilter(RentalModel.extra_days_fee, title="Extra days fee"),
    ]

    column_sortable_list = [
        RentalModel.start_date,
        RentalModel.end_date,
        RentalModel.base_price_total,
        RentalModel.status,
        RentalModel.is_paid,
        RentalModel.created_at,
    ]

    column_default_sort = [(RentalModel.created_at, True)]

    form_args = {
        "request_id": {
            "validators": [DataRequired()]
        },
        "lessor_company_id": {
            "validators": [DataRequired()]
        },
        "renter_company_id": {
            "validators": [DataRequired()]
        },
        "car_id": {
            "validators": [DataRequired()]
        },
        "driver_id": {
            "validators": [DataRequired()]
        },
        "base_price_total": {
            "validators": [
                DataRequired(),
                NumberRange(min=0, message="Price must be positive")
            ]
        },
        "extra_days_fee": {
            "validators": [
                NumberRange(min=0, message="Fee must be positive")
            ]
        },
    }

    @staticmethod
    def _format_status(model, attribute):
        status = model.status

        if status is None:
            return "—"

        status_config = {
            RentalStatus.ACTIVE: {
                "color": "#4CAF50",
                "bg": "#E8F5E9",
                "icon": "🟢",
                "text": "Active"
            },
            RentalStatus.COMPLETED: {
                "color": "#2196F3",
                "bg": "#E3F2FD",
                "icon": "✅",
                "text": "Completed"
            },
            RentalStatus.OVERDUE: {
                "color": "#F44336",
                "bg": "#FFEBEE",
                "icon": "⚠️",
                "text": "Overdue"
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
    def _format_price(model, attribute):
        price = model.base_price_total

        if price is None:
            return "—"

        return Markup(
            f'<span style="font-weight: 600; color: #2E7D32;">P{price:,.2f}</span>'
        )

    @staticmethod
    def _format_extra_fee(model, attribute):
        fee = model.extra_days_fee

        if fee is None:
            return "—"

        if fee > 0:
            return Markup(
                f'<span style="color: #F44336; font-weight: 500;">+P{fee:,.2f}</span>'
            )
        else:
            return Markup(
                f'<span style="color: #757575;">P{fee:,.2f}</span>'
            )

    @staticmethod
    def _format_total_price(model, attribute):
        base = model.base_price_total or 0
        extra = model.extra_days_fee or 0
        total = base + extra

        return Markup(
            f'<span style="font-weight: 700; color: #1565C0;">P{total:,.2f}</span>'
        )

    @staticmethod
    def _format_is_paid(model, attribute):
        is_paid = model.is_paid

        if is_paid:
            return Markup(
                '<span style="color: #4CAF50; font-weight: 500;">✓ Paid</span>'
            )
        else:
            return Markup(
                '<span style="color: #FF9800; font-weight: 500;">⏳ Unpaid</span>'
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
    def _format_actual_return(model, attribute):
        actual_return = model.actual_return_date

        if actual_return is None:
            return Markup('<span style="color: #999;">Not returned</span>')

        formatted = actual_return.strftime("%Y-%m-%d %H:%M")

        return Markup(
            f'<span style="font-family: monospace;">{formatted}</span>'
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
    def _format_rental_summary(model, attribute):
        status = model.status
        is_paid = model.is_paid
        base_price = model.base_price_total or 0
        extra_fee = model.extra_days_fee or 0
        total = base_price + extra_fee

        status_config = {
            RentalStatus.ACTIVE: {"color": "#4CAF50", "bg": "#E8F5E9"},
            RentalStatus.COMPLETED: {"color": "#2196F3", "bg": "#E3F2FD"},
            RentalStatus.OVERDUE: {"color": "#F44336", "bg": "#FFEBEE"},
        }

        config = status_config.get(status, {"color": "#757575", "bg": "#F5F5F5"})

        return Markup(
            f'<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            f'border-radius: 12px; color: white;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">'
            f'<div>'
            f'<div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Total Amount</div>'
            f'<div style="font-size: 36px; font-weight: 700;">${total:,.2f}</div>'
            f'</div>'
            f'<div style="text-align: right;">'
            f'<div style="display: inline-block; padding: 6px 16px; '
            f'background-color: {config["bg"]}; color: {config["color"]}; '
            f'border-radius: 20px; font-weight: 600;">'
            f'{status.value if status else "N/A"}'
            f'</div>'
            f'</div>'
            f'</div>'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; '
            f'background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;">'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8;">Base Price</div>'
            f'<div style="font-size: 18px; font-weight: 600;">${base_price:,.2f}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8;">Extra Fees</div>'
            f'<div style="font-size: 18px; font-weight: 600;">${extra_fee:,.2f}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8;">Payment Status</div>'
            f'<div style="font-size: 16px; font-weight: 500;">{"✓ Paid" if is_paid else "⏳ Unpaid"}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        RentalModel.status: _format_status,
        RentalModel.base_price_total: _format_price,
        RentalModel.extra_days_fee: _format_extra_fee,
        RentalModel.is_paid: _format_is_paid,
        RentalModel.actual_return_date: _format_actual_return,
        RentalModel.car_id: lambda m, a: RentalAdmin._format_ids(m, a),
        RentalModel.driver_id: lambda m, a: RentalAdmin._format_ids(m, a),
        RentalModel.lessor_company_id: lambda m, a: RentalAdmin._format_ids(m, a),
        RentalModel.renter_company_id: lambda m, a: RentalAdmin._format_ids(m, a),
        RentalModel.request_id: lambda m, a: RentalAdmin._format_ids(m, a),
        RentalModel.id: lambda m, a: RentalAdmin._format_ids(m, a),
    }

    column_formatters_detail = {
        RentalModel.id: _format_rental_summary,
        RentalModel.status: _format_status,
        RentalModel.base_price_total: _format_price,
        RentalModel.extra_days_fee: _format_extra_fee,
        RentalModel.is_paid: _format_is_paid,
        RentalModel.actual_return_date: _format_actual_return,
        RentalModel.start_date: lambda m, a: RentalAdmin._format_date_range(m, a),
    }
