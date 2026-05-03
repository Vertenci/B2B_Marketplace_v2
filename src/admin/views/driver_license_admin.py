from datetime import date, datetime
from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter, BooleanFilter
from wtforms.validators import DataRequired, Length, ValidationError

from src.admin.views.base_admin import BaseAdmin
from src.models.driver_license_model import DriverLicenseModel
from src.models.enums import CategoriesType


class DriverLicenseAdmin(BaseAdmin, model=DriverLicenseModel):
    name = "Driver License"
    name_plural = "Driver Licenses"
    icon = "fa-solid fa-id-card"
    category = "Accounts"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        DriverLicenseModel.id,
        DriverLicenseModel.user_id,
        DriverLicenseModel.license_number,
        DriverLicenseModel.categories,
        DriverLicenseModel.issue_date,
        DriverLicenseModel.expire_date,
        DriverLicenseModel.verified,
    ]

    column_searchable_list = [
        DriverLicenseModel.license_number,
    ]

    column_filters = [
        StaticValuesFilter(
            DriverLicenseModel.categories,
            values=[
                (c.value, c.value.title())
                for c in CategoriesType
            ],
            title="Categories",
        ),
        BooleanFilter(DriverLicenseModel.verified),
        OperationColumnFilter(DriverLicenseModel.user_id, title="User ID"),
    ]

    column_sortable_list = [
        DriverLicenseModel.license_number,
        DriverLicenseModel.categories,
        DriverLicenseModel.issue_date,
        DriverLicenseModel.expire_date,
        DriverLicenseModel.verified,
    ]

    column_default_sort = [(DriverLicenseModel.expire_date, False)]

    form_args = {
        "license_number": {
            "validators": [
                DataRequired(),
                Length(min=1, max=100),
            ]
        },
        "issue_date": {
            "validators": [DataRequired()]
        },
        "expire_date": {
            "validators": [DataRequired()]
        },
        "categories": {
            "validators": [DataRequired()]
        },
        "user_id": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _validate_dates(form, field):
        if form.issue_date.data and form.expire_date.data:
            if form.expire_date.data <= form.issue_date.data:
                raise ValidationError("Expiration date must be after issue date")

    @staticmethod
    def _format_license_number(model, attribute):
        value = model.license_number or ""

        if len(value) <= 10:
            return value

        short = f"{value[:4]}...{value[-4:]}"

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_expire_date(model, attribute):
        expire_date = model.expire_date

        if expire_date is None:
            return "—"

        today = datetime.now(expire_date.tzinfo) if expire_date.tzinfo else datetime.now()
        days_until_expiry = (expire_date.replace(tzinfo=None) - today.replace(tzinfo=None)).days

        if days_until_expiry < 0:
            color = "red"
            status = "Expired"
        elif days_until_expiry <= 30:
            color = "orange"
            status = f"Expires in {days_until_expiry} days"
        else:
            color = "green"
            status = "Valid"

        formatted_date = expire_date.strftime("%Y-%m-%d")

        return Markup(
            f'<span title="{status}">'
            f'<span style="color: {color};">{formatted_date}</span>'
            f'</span>'
        )

    @staticmethod
    def _format_verified(model, attribute):
        verified = model.verified

        if verified:
            return Markup(
                '<span style="color: green;">✓ Verified</span>'
            )
        else:
            return Markup(
                '<span style="color: gray;">✗ Unverified</span>'
            )

    @staticmethod
    def _format_categories(model, attribute):
        categories = model.categories

        if categories is None:
            return "—"

        category_colors = {
            CategoriesType.B: "#4CAF50",
            CategoriesType.C: "#2196F3",
            CategoriesType.D: "#FF9800",
        }

        color = category_colors.get(categories, "#000000")

        return Markup(
            f'<span style="display: inline-block; padding: 2px 8px; '
            f'background-color: {color}; color: white; border-radius: 4px; '
            f'font-weight: 500;">{categories.value}</span>'
        )

    column_formatters = {
        DriverLicenseModel.license_number: _format_license_number,
        DriverLicenseModel.expire_date: _format_expire_date,
        DriverLicenseModel.verified: _format_verified,
        DriverLicenseModel.categories: _format_categories,
    }
