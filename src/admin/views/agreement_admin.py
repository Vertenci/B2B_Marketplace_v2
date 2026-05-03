from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired

from src.admin.views.base_admin import BaseAdmin
from src.models.agreement_model import AgreementModel
from src.models.enums import AgreementType


class AgreementAdmin(BaseAdmin, model=AgreementModel):
    name = "Agreement"
    name_plural = "Agreements"
    icon = "fa-solid fa-file-signature"
    category = "Documents"
    category_icon = "fa-file-signature"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        AgreementModel.id,
        AgreementModel.user_id,
        AgreementModel.type,
        AgreementModel.accepted_at,
        AgreementModel.ip_address,
    ]

    column_searchable_list = [AgreementModel.ip_address]

    column_filters = [
        StaticValuesFilter(
            AgreementModel.type,
            values=[
                (t.value, t.name.title())
                for t in AgreementType
            ],
            title="Agreement type",
        ),
        OperationColumnFilter(AgreementModel.user_id, title="User ID"),
    ]

    column_sortable_list = [
        AgreementModel.type,
        AgreementModel.accepted_at,
    ]

    column_default_sort = [(AgreementModel.accepted_at, True)]

    form_args = {
        "user_id": {
            "validators": [DataRequired()]
        },
        "type": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _format_user_agent(model, attribute):
        value = model.user_agent or ""

        max_length = 50

        if len(value) <= max_length:
            return value

        short = value[:max_length] + "..."

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    @staticmethod
    def _format_ip_address(model, attribute):
        value = model.ip_address or "—"

        return Markup(
            f'<code>{value}</code>'
        )

    column_formatters = {
        AgreementModel.user_agent: _format_user_agent,
        AgreementModel.ip_address: _format_ip_address,
    }
