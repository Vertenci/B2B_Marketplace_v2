from markupsafe import Markup
from sqladmin.filters import BooleanFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length, NumberRange

from src.admin.views.base_admin import BaseAdmin
from src.models.geofence_model import GeofenceModel


class GeofenceAdmin(BaseAdmin, model=GeofenceModel):
    name = "Geofence"
    name_plural = "Geofences"
    icon = "fa-solid fa-draw-polygon"
    category = "Fleet"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        GeofenceModel.id,
        GeofenceModel.name,
        GeofenceModel.car_id,
        GeofenceModel.center_lat,
        GeofenceModel.center_lng,
        GeofenceModel.radius_meters,
        GeofenceModel.is_active,
        GeofenceModel.created_at,
    ]

    column_searchable_list = [
        GeofenceModel.name,
    ]

    column_filters = [
        BooleanFilter(GeofenceModel.is_active),
        OperationColumnFilter(GeofenceModel.car_id, title="Car ID"),
        OperationColumnFilter(GeofenceModel.radius_meters, title="Radius (meters)"),
    ]

    column_sortable_list = [
        GeofenceModel.name,
        GeofenceModel.radius_meters,
        GeofenceModel.is_active,
        GeofenceModel.created_at,
    ]

    column_default_sort = [(GeofenceModel.created_at, True)]

    form_args = {
        "name": {
            "validators": [
                DataRequired(),
                Length(min=1, max=100),
            ]
        },
        "car_id": {
            "validators": [DataRequired()]
        },
        "center_lat": {
            "validators": [
                DataRequired(),
                NumberRange(min=-90, max=90, message="Latitude must be between -90 and 90")
            ]
        },
        "center_lng": {
            "validators": [
                DataRequired(),
                NumberRange(min=-180, max=180, message="Longitude must be between -180 and 180")
            ]
        },
        "radius_meters": {
            "validators": [
                DataRequired(),
                NumberRange(min=1, max=100000, message="Radius must be between 1 and 100,000 meters")
            ]
        },
    }

    @staticmethod
    def _format_name(model, attribute):
        value = model.name or ""

        max_length = 20

        if len(value) <= max_length:
            return value

        short = value[:max_length] + "..."

        return Markup(
            f'<span title="{value}">{short}</span>'
        )

    @staticmethod
    def _format_coordinates(model, attribute):
        lat = model.center_lat
        lng = model.center_lng

        if lat is None or lng is None:
            return "—"

        google_maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        yandex_maps_url = f"https://yandex.ru/maps/?ll={lng},{lat}&z=15&pt={lng},{lat}"

        return Markup(
            f'<div>'
            f'<span style="font-family: monospace;">{lat:.6f}, {lng:.6f}</span><br>'
            f'<a href="{google_maps_url}" target="_blank" style="font-size: 12px;">🗺️ Google</a> '
            f'<a href="{yandex_maps_url}" target="_blank" style="font-size: 12px;">📍 Yandex</a>'
            f'</div>'
        )

    @staticmethod
    def _format_radius(model, attribute):
        radius = model.radius_meters

        if radius is None:
            return "—"

        if radius >= 1000:
            km = radius / 1000
            return Markup(
                f'<span style="font-weight: 500;">{radius} m</span> '
                f'<span style="color: #666; font-size: 12px;">({km:.2f} km)</span>'
            )
        else:
            return Markup(
                f'<span style="font-weight: 500;">{radius} m</span>'
            )

    @staticmethod
    def _format_is_active(model, attribute):
        is_active = model.is_active

        if is_active:
            return Markup(
                '<span style="color: green;">✓ Active</span>'
            )
        else:
            return Markup(
                '<span style="color: gray;">✗ Inactive</span>'
            )

    @staticmethod
    def _format_car_id(model, attribute):
        value = model.car_id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_geofence_preview(model, attribute):
        lat = model.center_lat
        lng = model.center_lng
        radius = model.radius_meters
        name = model.name

        if lat is None or lng is None or radius is None:
            return "—"

        static_map_url = (
            f"https://staticmap.openstreetmap.de/staticmap.php?"
            f"center={lat},{lng}&zoom=14&size=400x300&markers={lat},{lng},lightblue1"
            f"&circle={lat},{lng},{radius}|lightblue|black|3"
        )

        return Markup(
            f'<div style="margin: 10px 0;">'
            f'<strong>{name or "Geofence"}</strong><br>'
            f'<img src="{static_map_url}" alt="Geofence Map" '
            f'style="max-width: 100%; border-radius: 8px; margin-top: 8px; border: 1px solid #ddd;">'
            f'</div>'
        )

    column_formatters = {
        GeofenceModel.name: _format_name,
        GeofenceModel.center_lat: _format_coordinates,
        GeofenceModel.radius_meters: _format_radius,
        GeofenceModel.is_active: _format_is_active,
        GeofenceModel.car_id: _format_car_id,
    }

    column_formatters_detail = {
        GeofenceModel.center_lat: _format_coordinates,
        GeofenceModel.center_lng: _format_coordinates,
        GeofenceModel.radius_meters: _format_radius,
        GeofenceModel.car_id: _format_car_id,
        GeofenceModel.id: _format_geofence_preview,
    }
