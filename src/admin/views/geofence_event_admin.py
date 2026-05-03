from markupsafe import Markup
from sqladmin.filters import StaticValuesFilter, OperationColumnFilter
from wtforms.validators import DataRequired

from src.admin.views.base_admin import BaseAdmin
from src.models.geofence_event_model import GeofenceEventModel
from src.models.enums import GeofenceType


class GeofenceEventAdmin(BaseAdmin, model=GeofenceEventModel):
    name = "Geofence Event"
    name_plural = "Geofence Events"
    icon = "fa-solid fa-location-crosshairs"
    category = "Fleet"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        GeofenceEventModel.id,
        GeofenceEventModel.rental_id,
        GeofenceEventModel.geofence_id,
        GeofenceEventModel.type,
        GeofenceEventModel.lat,
        GeofenceEventModel.lng,
        GeofenceEventModel.triggered_at,
    ]

    column_searchable_list = []

    column_filters = [
        StaticValuesFilter(
            GeofenceEventModel.type,
            values=[
                (t.value, t.value.title())
                for t in GeofenceType
            ],
            title="Event type",
        ),
        OperationColumnFilter(GeofenceEventModel.rental_id, title="Rental ID"),
        OperationColumnFilter(GeofenceEventModel.geofence_id, title="Geofence ID"),
        OperationColumnFilter(GeofenceEventModel.lat, title="Latitude"),
        OperationColumnFilter(GeofenceEventModel.lng, title="Longitude"),
    ]

    column_sortable_list = [
        GeofenceEventModel.type,
        GeofenceEventModel.triggered_at,
    ]

    column_default_sort = [(GeofenceEventModel.triggered_at, True)]

    form_args = {
        "rental_id": {
            "validators": [DataRequired()]
        },
        "geofence_id": {
            "validators": [DataRequired()]
        },
        "type": {
            "validators": [DataRequired()]
        },
        "lat": {
            "validators": [DataRequired()]
        },
        "lng": {
            "validators": [DataRequired()]
        },
    }

    @staticmethod
    def _format_type(model, attribute):
        event_type = model.type

        if event_type is None:
            return "—"

        type_colors = {
            GeofenceType.ENTER: "#4CAF50",
            GeofenceType.EXIT: "#F44336",
        }

        type_icons = {
            GeofenceType.ENTER: "↘️",
            GeofenceType.EXIT: "↗️",
        }

        color = type_colors.get(event_type, "#000000")
        icon = type_icons.get(event_type, "")

        return Markup(
            f'<span style="display: inline-block; padding: 2px 8px; '
            f'background-color: {color}; color: white; border-radius: 4px; '
            f'font-weight: 500;">{icon} {event_type.value}</span>'
        )

    @staticmethod
    def _format_coordinates(model, attribute):
        lat = model.lat
        lng = model.lng

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
    def _format_triggered_at(model, attribute):
        triggered_at = model.triggered_at

        if triggered_at is None:
            return "—"

        formatted_date = triggered_at.strftime("%Y-%m-%d %H:%M:%S")

        return Markup(
            f'<span style="font-family: monospace;">{formatted_date}</span>'
        )

    @staticmethod
    def _format_geofence_id(model, attribute):
        value = model.geofence_id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_rental_id(model, attribute):
        value = model.rental_id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    column_formatters = {
        GeofenceEventModel.type: _format_type,
        GeofenceEventModel.lat: _format_coordinates,
        GeofenceEventModel.triggered_at: _format_triggered_at,
        GeofenceEventModel.geofence_id: _format_geofence_id,
        GeofenceEventModel.rental_id: _format_rental_id,
    }

    column_formatters_detail = {
        GeofenceEventModel.lat: _format_coordinates,
        GeofenceEventModel.lng: _format_coordinates,
    }
