from markupsafe import Markup
from sqladmin.filters import BooleanFilter, StaticValuesFilter

from src.admin.views.base_admin import BaseAdmin
from src.models.company_users_model import CompanyUserModel
from src.models.enums import CompanyRole


class CompanyUserAdmin(BaseAdmin, model=CompanyUserModel):
    name = "Company User"
    name_display = "Company Users"
    icon = "fa-solid fa-users"
    category = "Accounts"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        CompanyUserModel.id,
        CompanyUserModel.user,
        CompanyUserModel.company,
        CompanyUserModel.position,
        CompanyUserModel.is_active,
        CompanyUserModel.created_at,
    ]

    column_labels = {
        CompanyUserModel.user: "User Email",
    }

    column_searchable_list = [
        CompanyUserModel.user_id,
        CompanyUserModel.company,
        CompanyUserModel.position,
    ]

    column_sortable_list = [
        CompanyUserModel.position,
        CompanyUserModel.is_active,
        CompanyUserModel.created_at,
    ]

    column_default_sort = [(CompanyUserModel.created_at, True)]

    column_filters = [
        BooleanFilter(CompanyUserModel.is_active),
        StaticValuesFilter(
            CompanyUserModel.position,
            values=[
                (p.value, p.name.title())
                for p in CompanyRole
            ],
            title="Position",
        ),
    ]

    @staticmethod
    def _format_position(model, attribute):
        colors = {
            CompanyRole.OWNER: "danger",
            CompanyRole.DRIVER: "info",
        }

        color = colors.get(model.position, "secondary")

        return Markup(
            f'<span class="badge bg-{color}">'
            f'{model.position.name.title()}'
            f'</span>'
        )

    column_formatters = {
        CompanyUserModel.position: _format_position,
    }

    column_formatters_detail = {
        CompanyUserModel.position: _format_position,
    }
