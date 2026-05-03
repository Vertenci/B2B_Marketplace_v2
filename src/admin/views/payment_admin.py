from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired, NumberRange

from src.admin.views.base_admin import BaseAdmin
from src.models.payment_model import PaymentModel
from src.models.enums import PaymentStatus, PaymentType


class PaymentAdmin(BaseAdmin, model=PaymentModel):
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"
    category = "Finance"
    category_icon = "fa-solid fa-credit-card"

    column_list = [
        PaymentModel.id,
        PaymentModel.rental_id,
        PaymentModel.payer_company_id,
        PaymentModel.receiver_company_id,
        PaymentModel.amount,
        PaymentModel.commission_amount,
        PaymentModel.payment_method,
        PaymentModel.status,
        PaymentModel.paid_at,
    ]

    column_searchable_list = []

    column_filters = [
        StaticValuesFilter(
            PaymentModel.status,
            values=[
                (s.value, s.value.title())
                for s in PaymentStatus
            ],
            title="Payment status",
        ),
        StaticValuesFilter(
            PaymentModel.payment_method,
            values=[
                (p.value, p.value.title())
                for p in PaymentType
            ],
            title="Payment method",
        ),
        OperationColumnFilter(PaymentModel.rental_id, title="Rental ID"),
        OperationColumnFilter(PaymentModel.payer_company_id, title="Payer Company ID"),
        OperationColumnFilter(PaymentModel.receiver_company_id, title="Receiver Company ID"),
        OperationColumnFilter(PaymentModel.amount, title="Amount"),
        OperationColumnFilter(PaymentModel.commission_amount, title="Commission"),
    ]

    column_sortable_list = [
        PaymentModel.amount,
        PaymentModel.commission_amount,
        PaymentModel.payment_method,
        PaymentModel.status,
        PaymentModel.paid_at,
    ]

    column_default_sort = [(PaymentModel.paid_at, True), (PaymentModel.status, False)]

    form_args = {
        "rental_id": {
            "validators": [DataRequired()]
        },
        "payer_company_id": {
            "validators": [DataRequired()]
        },
        "receiver_company_id": {
            "validators": [DataRequired()]
        },
        "amount": {
            "validators": [
                DataRequired(),
                NumberRange(min=0, message="Amount must be positive")
            ]
        },
        "commission_amount": {
            "validators": [
                DataRequired(),
                NumberRange(min=0, message="Commission must be positive")
            ]
        },
        "status": {
            "validators": [DataRequired()]
        },
        "payment_method": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _format_amount(model, attribute):
        amount = model.amount

        if amount is None:
            return "—"

        return Markup(
            f'<span style="font-weight: 600; color: #2E7D32;">${amount:,.2f}</span>'
        )

    @staticmethod
    def _format_commission(model, attribute):
        commission = model.commission_amount

        if commission is None:
            return "—"

        return Markup(
            f'<span style="color: #757575;">${commission:,.2f}</span>'
        )

    @staticmethod
    def _format_net_amount(model, attribute):
        amount = model.amount
        commission = model.commission_amount

        if amount is None or commission is None:
            return "—"

        net = amount - commission

        return Markup(
            f'<span style="font-weight: 500; color: #1565C0;">${net:,.2f}</span>'
        )

    @staticmethod
    def _format_status(model, attribute):
        status = model.status

        if status is None:
            return "—"

        status_config = {
            PaymentStatus.PENDING: {
                "color": "#FF9800",
                "bg": "#FFF3E0",
                "icon": "⏳",
                "text": "Pending"
            },
            PaymentStatus.PAID: {
                "color": "#4CAF50",
                "bg": "#E8F5E9",
                "icon": "✓",
                "text": "Paid"
            },
            PaymentStatus.FAILED: {
                "color": "#F44336",
                "bg": "#FFEBEE",
                "icon": "✗",
                "text": "Failed"
            },
        }

        config = status_config.get(status, {"color": "#000", "bg": "#F5F5F5", "icon": "", "text": status.value})

        return Markup(
            f'<span style="display: inline-block; padding: 4px 10px; '
            f'background-color: {config["bg"]}; color: {config["color"]}; '
            f'border-radius: 12px; font-weight: 500; font-size: 13px;">'
            f'{config["icon"]} {config["text"]}'
            f'</span>'
        )

    @staticmethod
    def _format_payment_method(model, attribute):
        method = model.payment_method

        if method is None:
            return "—"

        method_config = {
            PaymentType.BALANCE: {
                "icon": "💰",
                "text": "Balance",
                "color": "#5C6BC0"
            },
            PaymentType.CARD: {
                "icon": "💳",
                "text": "Card",
                "color": "#26A69A"
            },
        }

        config = method_config.get(method, {"icon": "", "text": method.value, "color": "#757575"})

        return Markup(
            f'<span style="color: {config["color"]};">'
            f'{config["icon"]} {config["text"]}'
            f'</span>'
        )

    @staticmethod
    def _format_paid_at(model, attribute):
        paid_at = model.paid_at

        if paid_at is None:
            return Markup('<span style="color: #999;">—</span>')

        formatted_date = paid_at.strftime("%Y-%m-%d %H:%M")

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
    def _format_payment_summary(model, attribute):
        amount = model.amount
        commission = model.commission_amount
        net = amount - commission if amount and commission else None
        status = model.status
        method = model.payment_method

        status_colors = {
            PaymentStatus.PENDING: "#FF9800",
            PaymentStatus.PAID: "#4CAF50",
            PaymentStatus.FAILED: "#F44336",
        }
        status_color = status_colors.get(status, "#000")

        return Markup(
            f'<div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            f'border-radius: 8px; color: white;">'
            f'<div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Total Amount</div>'
            f'<div style="font-size: 32px; font-weight: 700; margin-bottom: 15px;">${amount:,.2f}</div>'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">'
            f'<div>Commission: <strong>${commission:,.2f}</strong></div>'
            f'<div>Net: <strong>${net:,.2f}</strong></div>'
            f'<div>Status: <span style="color: {status_color};">●</span> {status.value if status else "N/A"}</div>'
            f'<div>Method: {method.value if method else "N/A"}</div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        PaymentModel.amount: _format_amount,
        PaymentModel.commission_amount: _format_commission,
        PaymentModel.status: _format_status,
        PaymentModel.payment_method: _format_payment_method,
        PaymentModel.paid_at: _format_paid_at,
        PaymentModel.rental_id: lambda m, a: PaymentAdmin._format_ids(m, a),
        PaymentModel.payer_company_id: lambda m, a: PaymentAdmin._format_ids(m, a),
        PaymentModel.receiver_company_id: lambda m, a: PaymentAdmin._format_ids(m, a),
    }

    column_formatters_detail = {
        PaymentModel.id: _format_payment_summary,
        PaymentModel.amount: _format_amount,
        PaymentModel.commission_amount: _format_commission,
        PaymentModel.rental_id: lambda m, a: PaymentAdmin._format_ids(m, a),
        PaymentModel.payer_company_id: lambda m, a: PaymentAdmin._format_ids(m, a),
        PaymentModel.receiver_company_id: lambda m, a: PaymentAdmin._format_ids(m, a),
    }
