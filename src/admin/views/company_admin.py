from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter, BooleanFilter
from starlette.requests import Request
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

    column_details_exclude_list = [
        "company_users",
        "cars",
        "rental_requests",
        "lessor_rentals",
        "renter_rentals",
        "payer_companies",
        "receiver_companies",
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

    # При редактировании type НЕ включаем в форму — чтобы не перезаписывалось
    # Баланс, is_verified, name, inn — можно менять
    form_columns = [
        "name",
        "inn",
        "balance",
        "is_verified",
    ]

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

    async def on_model_change(self, data: dict, model: CompanyModel, is_created: bool, request: Request):
        """
        Гарантируем что type не меняется при редактировании.
        При создании — type из формы (если передан), иначе lessor по умолчанию.
        """
        if not is_created:
            # При редактировании — восстанавливаем оригинальный type из модели
            # (data может не содержать type, но на всякий случай принудительно ставим)
            if "type" in data:
                data["type"] = model.type
        else:
            # При создании — если type не указан, ставим lessor
            if not data.get("type"):
                data["type"] = CompanyType.LESSOR

    @staticmethod
    def _format_inn(model, attribute):
        value = model.inn or ""
        max_length = 15
        if len(value) <= max_length:
            return value
        return Markup(f'<span title="{value}">{value[:max_length]}...</span>')

    @staticmethod
    def _format_name(model, attribute):
        value = model.name or ""
        max_length = 20
        if len(value) <= max_length:
            return value
        return Markup(f'<span title="{value}">{value[:max_length]}...</span>')

    @staticmethod
    def _format_type(model, attribute):
        colors = {
            CompanyType.LESSOR: ("#1976D2", "Арендодатель"),
            CompanyType.RENTER: ("#388E3C", "Арендатор"),
        }
        color, label = colors.get(model.type, ("#333", model.type.value))
        return Markup(
            f'<span style="color:{color};font-weight:600;background:{color}22;'
            f'padding:2px 8px;border-radius:4px;">{label}</span>'
        )

    column_formatters = {
        CompanyModel.inn: _format_inn,
        CompanyModel.name: _format_name,
        CompanyModel.type: _format_type,
    }
