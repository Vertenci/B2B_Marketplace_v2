from typing import Any
from wtforms.validators import Optional

from markupsafe import Markup
from sqladmin.filters import BooleanFilter, StaticValuesFilter, OperationColumnFilter
from starlette.requests import Request
from wtforms import PasswordField
from wtforms.validators import DataRequired, Email, Length

from src.admin.validators import strong_password
from src.admin.views.base_admin import BaseAdmin
from src.models.enums import UserRole
from src.models.user_model import UserModel


class UserAdmin(BaseAdmin, model=UserModel):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category = "Accounts"
    category_icon = "fa-solid fa-user"

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    page_size = 25
    column_auto_select_related = False

    column_list = [
        UserModel.id,
        UserModel.email,
        UserModel.phone,
        UserModel.full_name,
        UserModel.role,
        UserModel.created_at,
    ]

    column_searchable_list = [
        UserModel.email,
    ]

    column_filters = [
        BooleanFilter(UserModel.is_active),
        StaticValuesFilter(
            UserModel.role,
            values=[
                (status.value, status.name.title())
                for status in UserRole
            ],
            title="Role",
        ),
        OperationColumnFilter(UserModel.email),
        OperationColumnFilter(UserModel.id, title="User ID")
    ]

    column_sortable_list = [
        UserModel.email,
        UserModel.role,
        UserModel.created_at,
        UserModel.is_active,
    ]

    form_excluded_columns = ["password_hash"]

    column_details_exclude_list = ["password_hash"]

    column_default_sort = [(UserModel.created_at, True)]

    form_args = {
        "email": {
            "label": "Email address",
            "validators": [
                DataRequired(),
                Email(message="Invalid email format"),
                Length(max=120)
            ]
        },
        "is_active": {"label": "Active"},
    }

    @staticmethod
    def _format_email(model, attribute):
        value = model.email or ""

        max_length = 15

        if len(value) <= max_length:
            return value

        short = value[:max_length] + "..."

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    column_formatters = {
        UserModel.email: _format_email,
    }

    async def scaffold_form(self, rules=None):
        form_class = await super().scaffold_form(rules)

        form_class.password = PasswordField(
            "Password",
            validators=[
                Optional(),
                strong_password
            ],
        )

        return form_class

    async def on_model_change(
            self,
            data: dict,
            model: Any,
            is_created: bool,
            request: Request,
    ):
        if is_created:
            model.role = UserRole.USER

        password = data.pop("password", None)
        data.pop("password_hash", None)

        data["is_active"] = bool(data.get("is_active"))

        if password:
            model.password = password
        elif is_created:
            raise ValueError("Password is required")

        return await super().on_model_change(data, model, is_created, request)

    async def on_model_delete(self, model: Any, request: Request) -> None:
        if model.role == UserRole.ADMIN:
            raise ValueError("Cannot delete admin user")
