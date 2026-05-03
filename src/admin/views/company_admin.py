from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter, BooleanFilter
from wtforms.validators import DataRequired, Length

from src.admin.views.base_admin import BaseAdmin
from src.models.company_model import CompanyModel
from src.models.enums import CompanyType


class CompanyAdmin(BaseAdmin, model=CompanyModel):
    name = "Company"
    name_plural = "Companies"
    icon = "fa-solid fa-building"
    category = "Companies"
    category_icon = "fa-solid fa-building"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        CompanyModel.id,
        CompanyModel.name,
        CompanyModel.inn,
        CompanyModel.type,
        CompanyModel.balance,
        CompanyModel.is_verified,
        CompanyModel.created_at,
    ]

    column_searchable_list = [CompanyModel.name, CompanyModel.inn]

    column_filters = [
        StaticValuesFilter(
            CompanyModel.type,
            values=[
                (t.value, t.name.title())
                for t in CompanyType
            ],
            title="Company type",
        ),
        BooleanFilter(CompanyModel.is_verified),
        OperationColumnFilter(CompanyModel.id, title="Company ID"),
        OperationColumnFilter(CompanyModel.balance, title="Company balance"),
    ]

    column_sortable_list = [
        CompanyModel.name,
        CompanyModel.type,
        CompanyModel.balance,
        CompanyModel.is_verified,
        CompanyModel.created_at,
    ]

    column_default_sort = [(CompanyModel.created_at, True)]


    form_args = {
        "name": {
            "validators": [
                DataRequired(),
                Length(min=3, max=120),
            ]
        },
        "inn": {
            "validators": [
                DataRequired(),
                Length(min=3, max=120),
            ]
        },
    }

    @staticmethod
    def _format_inn(model, attribute):
        value = model.inn or ""

        max_length = 15

        if len(value) <= max_length:
            return value

        short = value[:max_length] + "..."

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    @staticmethod
    def _format_name(model, attribute):
        value = model.name or ""

        max_length = 15

        if len(value) <= max_length:
            return value

        short = value[:max_length] + "..."

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    column_formatters = {
        CompanyModel.inn: _format_inn,
        CompanyModel.name: _format_name,
    }
