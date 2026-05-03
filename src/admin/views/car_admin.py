from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length

from src.admin.views.base_admin import BaseAdmin
from src.models.car_model import CarModel
from src.models.enums import CarStatus


class CarAdmin(BaseAdmin, model=CarModel):
    name = "Car"
    name_plural = "Cars"
    icon = "fa-solid fa-car"
    category = "Fleet"
    category_icon = "fa-solid fa-car"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        CarModel.id,
        CarModel.plate_number,
        CarModel.brand,
        CarModel.model,
        CarModel.year,
        CarModel.owner_company_id,
        CarModel.price_per_day,
        CarModel.status,
        CarModel.created_at,
    ]

    column_searchable_list = [
        CarModel.plate_number,
        CarModel.vin,
        CarModel.brand,
        CarModel.model,
    ]

    column_filters = [
        StaticValuesFilter(
            CarModel.status,
            values=[
                (s.value, s.value.title())
                for s in CarStatus
            ],
            title="Car status",
        ),
        OperationColumnFilter(CarModel.owner_company_id, title="Company ID"),
        OperationColumnFilter(CarModel.price_per_day, title="Price per day"),
        OperationColumnFilter(CarModel.year, title="Year"),
    ]

    column_sortable_list = [
        CarModel.plate_number,
        CarModel.brand,
        CarModel.model,
        CarModel.year,
        CarModel.price_per_day,
        CarModel.status,
        CarModel.created_at,
    ]

    column_default_sort = [(CarModel.created_at, True)]

    form_args = {
        "brand": {
            "validators": [
                DataRequired(),
                Length(min=1, max=80),
            ]
        },
        "model": {
            "validators": [
                DataRequired(),
                Length(min=1, max=80),
            ]
        },
        "year": {
            "validators": [
                DataRequired(),
                Length(min=4, max=5),
            ]
        },
        "plate_number": {
            "validators": [
                DataRequired(),
                Length(min=1, max=7),
            ]
        },
        "vin": {
            "validators": [
                DataRequired(),
                Length(min=1, max=80),
            ]
        },
        "owner_company_id": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _format_price(model, attribute):
        value = model.price_per_day

        if value is None:
            return "—"

        return Markup(
            f'<span style="font-weight: 500;">${value:,.2f}</span>'
        )

    @staticmethod
    def _format_status(model, attribute):
        status = model.status

        if status is None:
            return "—"

        status_colors = {
            CarStatus.AVAILABLE: "green",
            CarStatus.RENTED: "blue",
            CarStatus.INACTIVE: "orange",
            CarStatus.HIDDEN: "gray",
        }

        color = status_colors.get(status, "black")

        return Markup(
            f'<span style="color: {color}; font-weight: 500;">{status.value}</span>'
        )

    @staticmethod
    def _format_vin(model, attribute):
        value = model.vin or ""

        if len(value) <= 10:
            return value

        short = f"{value[:4]}...{value[-4:]}"

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    column_formatters = {
        CarModel.price_per_day: _format_price,
        CarModel.status: _format_status,
        CarModel.vin: _format_vin,
    }
