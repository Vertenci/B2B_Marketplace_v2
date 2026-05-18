from datetime import datetime

from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter

from src.admin.views.base_admin import BaseAdmin
from src.models.balance_event_model import BalanceEventModel
from src.models.enums import BalanceEventType


class BalanceEventAdmin(BaseAdmin, model=BalanceEventModel):
    name = "Balance Event"
    name_plural = "Balance Events"
    icon = "fa-solid fa-scale-balanced"
    category = "Finance"
    category_icon = "fa-solid fa-coins"

    page_size = 25
    column_auto_select_related = False

    can_create = False
    can_edit = False
    can_delete = False

    column_list = [
        BalanceEventModel.id,
        BalanceEventModel.company_id,
        BalanceEventModel.event_type,
        BalanceEventModel.operation_amount,
        BalanceEventModel.balance_before,
        BalanceEventModel.balance_after,
        BalanceEventModel.created_at,
    ]

    column_searchable_list = [
        BalanceEventModel.company_id,
    ]

    column_filters = [
        StaticValuesFilter(
            BalanceEventModel.event_type,
            values=[
                (e.value, e.value.title())
                for e in BalanceEventType
            ],
            title="Event type",
        ),
        OperationColumnFilter(
            BalanceEventModel.operation_amount,
            title="Operation amount",
        ),
        OperationColumnFilter(
            BalanceEventModel.balance_before,
            title="Balance before",
        ),
        OperationColumnFilter(
            BalanceEventModel.balance_after,
            title="Balance after",
        ),
        OperationColumnFilter(
            BalanceEventModel.company_id,
            title="Company ID",
        ),
    ]

    column_sortable_list = [
        BalanceEventModel.created_at,
        BalanceEventModel.event_type,
        BalanceEventModel.operation_amount,
        BalanceEventModel.balance_before,
        BalanceEventModel.balance_after,
    ]

    column_default_sort = [(BalanceEventModel.created_at, True)]

    @staticmethod
    def _format_amount(model, attribute):
        value = getattr(model, attribute)

        if value is None:
            return "—"

        return Markup(
            f'<span style="font-weight: 500;">₽{value:,.2f}</span>'
        )

    @staticmethod
    def _format_operation_amount(model, attribute):
        value = model.operation_amount

        if value is None:
            return "—"

        event_type = model.event_type
        if event_type == BalanceEventType.TOP_UP:
            color = "#16a34a"
            prefix = "+"
        elif event_type == BalanceEventType.WITHDRAW:
            color = "#dc2626"
            prefix = "-"
        else:
            color = "#6b7280"
            prefix = ""

        return Markup(
            f'<span style="color: {color}; font-weight: 500;">{prefix}₽{value:,.2f}</span>'
        )

    @staticmethod
    def _format_event_type(model, attribute):
        event_type = model.event_type

        if event_type is None:
            return "—"

        type_config = {
            BalanceEventType.TOP_UP: {
                "color": "#16a34a",
                "icon": "fa-arrow-down",
                "label": "Top Up",
            },
            BalanceEventType.WITHDRAW: {
                "color": "#dc2626",
                "icon": "fa-arrow-up",
                "label": "Withdraw",
            },
        }

        config = type_config.get(event_type, {
            "color": "#6b7280",
            "icon": "fa-circle",
            "label": event_type.value,
        })

        return Markup(
            f'<span style="color: {config["color"]}; font-weight: 500;">'
            f'<i class="fa-solid {config["icon"]}"></i> '
            f'{config["label"]}'
            f'</span>'
        )

    @staticmethod
    def _format_date(model, attribute):
        value = model.created_at

        if value is None:
            return "—"

        if isinstance(value, datetime):
            return Markup(
                f'<span title="{value.isoformat()}">'
                f'{value.strftime("%Y-%m-%d %H:%M")}'
                f'</span>'
            )
        return str(value)

    @staticmethod
    def _format_balance_change(model, attribute):
        balance_before = model.balance_before
        balance_after = model.balance_after

        if balance_before is None or balance_after is None:
            return "—"

        change = balance_after - balance_before

        if change > 0:
            color = "#16a34a"
            prefix = "+"
        elif change < 0:
            color = "#dc2626"
            prefix = ""
        else:
            color = "#6b7280"
            prefix = ""

        return Markup(
            f'<span style="color: {color}; font-weight: 500;">'
            f'{prefix}₽{change:,.2f}'
            f'</span>'
        )

    column_formatters = {
        BalanceEventModel.operation_amount: _format_operation_amount,
        BalanceEventModel.balance_before: _format_amount,
        BalanceEventModel.balance_after: _format_amount,
        BalanceEventModel.event_type: _format_event_type,
        BalanceEventModel.created_at: _format_date,
    }

    column_formatters_detail = {
        BalanceEventModel.operation_amount: _format_operation_amount,
        BalanceEventModel.balance_before: _format_amount,
        BalanceEventModel.balance_after: _format_amount,
        BalanceEventModel.event_type: _format_event_type,
        BalanceEventModel.created_at: _format_date,
    }
