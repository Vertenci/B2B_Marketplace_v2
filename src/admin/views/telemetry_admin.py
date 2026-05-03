from datetime import datetime
from markupsafe import Markup
from sqladmin.filters import OperationColumnFilter
from wtforms.validators import DataRequired, NumberRange

from src.admin.views.base_admin import BaseAdmin
from src.models.telemetry_model import TelemetryModel


class TelemetryAdmin(BaseAdmin, model=TelemetryModel):
    name = "Telemetry"
    name_plural = "Telemetries"
    icon = "fa-solid fa-satellite-dish"
    category = "IoT"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        TelemetryModel.id,
        TelemetryModel.rental_id,
        TelemetryModel.car_id,
        TelemetryModel.driver_id,
        TelemetryModel.lat,
        TelemetryModel.lng,
        TelemetryModel.speed,
        TelemetryModel.recorded_at,
    ]

    column_searchable_list = []

    column_filters = [
        OperationColumnFilter(TelemetryModel.rental_id, title="Rental ID"),
        OperationColumnFilter(TelemetryModel.car_id, title="Car ID"),
        OperationColumnFilter(TelemetryModel.driver_id, title="Driver ID"),
        OperationColumnFilter(TelemetryModel.speed, title="Speed (km/h)"),
    ]

    column_sortable_list = [
        TelemetryModel.speed,
        TelemetryModel.recorded_at,
    ]

    column_default_sort = [(TelemetryModel.recorded_at, True)]

    form_args = {
        "rental_id": {
            "validators": [DataRequired()]
        },
        "car_id": {
            "validators": [DataRequired()]
        },
        "driver_id": {
            "validators": [DataRequired()]
        },
        "lat": {
            "validators": [
                DataRequired(),
                NumberRange(min=-90, max=90, message="Latitude must be between -90 and 90")
            ]
        },
        "lng": {
            "validators": [
                DataRequired(),
                NumberRange(min=-180, max=180, message="Longitude must be between -180 and 180")
            ]
        },
        "speed": {
            "validators": [
                DataRequired(),
                NumberRange(min=0, max=500, message="Speed must be between 0 and 500 km/h")
            ]
        },
    }

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
            f'<a href="{google_maps_url}" target="_blank" style="font-size: 11px;">🗺️ G</a> '
            f'<a href="{yandex_maps_url}" target="_blank" style="font-size: 11px;">📍 Y</a>'
            f'</div>'
        )

    @staticmethod
    def _format_speed(model, attribute):
        speed = model.speed

        if speed is None:
            return "—"

        if speed == 0:
            color = "#9E9E9E"
            icon = "🅿️"
        elif speed < 30:
            color = "#4CAF50"
            icon = "🐢"
        elif speed < 60:
            color = "#2196F3"
            icon = "🚗"
        elif speed < 90:
            color = "#FF9800"
            icon = "🚗💨"
        elif speed < 120:
            color = "#F44336"
            icon = "🏎️"
        else:
            color = "#D32F2F"
            icon = "⚠️"

        return Markup(
            f'<div style="display: flex; align-items: center; gap: 5px;">'
            f'<span style="color: {color}; font-weight: 600;">{speed}</span>'
            f'<span style="font-size: 11px; color: #757575;">km/h</span>'
            f'<span style="margin-left: 5px;">{icon}</span>'
            f'</div>'
        )

    @staticmethod
    def _format_speed_bar(model, attribute):
        speed = model.speed

        if speed is None:
            return "—"

        max_speed = 200
        percentage = min((speed / max_speed) * 100, 100)

        if speed < 30:
            color = "#4CAF50"
        elif speed < 60:
            color = "#2196F3"
        elif speed < 90:
            color = "#FF9800"
        elif speed < 120:
            color = "#F44336"
        else:
            color = "#D32F2F"

        return Markup(
            f'<div style="margin-top: 5px;">'
            f'<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">'
            f'<span style="font-weight: 600; color: {color};">{speed} km/h</span>'
            f'<span style="font-size: 11px; color: #757575;">max 200 km/h</span>'
            f'</div>'
            f'<div style="width: 100%; height: 8px; background-color: #e0e0e0; border-radius: 4px; overflow: hidden;">'
            f'<div style="width: {percentage}%; height: 100%; background-color: {color};"></div>'
            f'</div>'
            f'</div>'
        )

    @staticmethod
    def _format_recorded_at(model, attribute):
        recorded_at = model.recorded_at

        if recorded_at is None:
            return "—"

        now = datetime.now(recorded_at.tzinfo) if recorded_at.tzinfo else datetime.now()
        time_diff = now.replace(tzinfo=None) - recorded_at.replace(tzinfo=None)

        formatted_time = recorded_at.strftime("%H:%M:%S")
        formatted_date = recorded_at.strftime("%Y-%m-%d")

        if time_diff.days == 0:
            if time_diff.seconds < 60:
                time_ago = "just now"
            elif time_diff.seconds < 3600:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} min ago"
            else:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hours ago"
        elif time_diff.days == 1:
            time_ago = "yesterday"
        else:
            time_ago = f"{time_diff.days} days ago"

        return Markup(
            f'<div>'
            f'<span style="font-family: monospace;">{formatted_date}</span><br>'
            f'<span style="font-family: monospace; font-size: 12px;">{formatted_time}</span><br>'
            f'<span style="font-size: 11px; color: #757575;">{time_ago}</span>'
            f'</div>'
        )

    @staticmethod
    def _format_ids(model, attribute):
        value = getattr(model, attribute, None)

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_telemetry_card(model, attribute):
        lat = model.lat
        lng = model.lng
        speed = model.speed
        recorded_at = model.recorded_at

        google_maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        yandex_maps_url = f"https://yandex.ru/maps/?ll={lng},{lat}&z=15&pt={lng},{lat}"
        openstreetmap_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=15"

        if speed == 0:
            speed_color = "#9E9E9E"
            speed_text = "Stationary"
        elif speed < 30:
            speed_color = "#4CAF50"
            speed_text = "Slow"
        elif speed < 60:
            speed_color = "#2196F3"
            speed_text = "City speed"
        elif speed < 90:
            speed_color = "#FF9800"
            speed_text = "Highway speed"
        elif speed < 120:
            speed_color = "#F44336"
            speed_text = "Fast"
        else:
            speed_color = "#D32F2F"
            speed_text = "Very fast"

        formatted_time = recorded_at.strftime("%Y-%m-%d %H:%M:%S") if recorded_at else "N/A"

        return Markup(
            f'<div style="padding: 20px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); '
            f'border-radius: 12px; color: white;">'
            f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">'
            f'<span style="font-size: 48px;">🛰️</span>'
            f'<div>'
            f'<div style="font-size: 24px; font-weight: 700; margin-bottom: 5px;">Telemetry Data</div>'
            f'<div style="font-size: 14px; opacity: 0.9;">{formatted_time}</div>'
            f'</div>'
            f'</div>'
            f'<div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;">'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">Speed</div>'
            f'<div style="font-size: 36px; font-weight: 700; color: {speed_color};">{speed}</div>'
            f'<div style="font-size: 14px;">km/h · {speed_text}</div>'
            f'</div>'
            f'<div>'
            f'<div style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">Coordinates</div>'
            f'<div style="font-family: monospace; font-size: 14px;">{lat:.6f}</div>'
            f'<div style="font-family: monospace; font-size: 14px;">{lng:.6f}</div>'
            f'</div>'
            f'</div>'
            f'<div style="display: flex; gap: 15px;">'
            f'<a href="{google_maps_url}" target="_blank" '
            f'style="padding: 8px 16px; background: white; color: #1e3c72; '
            f'text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">'
            f'🗺️ Google Maps'
            f'</a>'
            f'<a href="{yandex_maps_url}" target="_blank" '
            f'style="padding: 8px 16px; background: rgba(255,255,255,0.2); color: white; '
            f'text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">'
            f'📍 Yandex Maps'
            f'</a>'
            f'<a href="{openstreetmap_url}" target="_blank" '
            f'style="padding: 8px 16px; background: rgba(255,255,255,0.2); color: white; '
            f'text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">'
            f'🌍 OpenStreetMap'
            f'</a>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        TelemetryModel.lat: _format_coordinates,
        TelemetryModel.speed: _format_speed,
        TelemetryModel.recorded_at: _format_recorded_at,
        TelemetryModel.rental_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
        TelemetryModel.car_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
        TelemetryModel.driver_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
        TelemetryModel.id: lambda m, a: TelemetryAdmin._format_ids(m, a),
    }

    column_formatters_detail = {
        TelemetryModel.id: _format_telemetry_card,
        TelemetryModel.lat: _format_coordinates,
        TelemetryModel.speed: _format_speed_bar,
        TelemetryModel.recorded_at: _format_recorded_at,
        TelemetryModel.rental_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
        TelemetryModel.car_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
        TelemetryModel.driver_id: lambda m, a: TelemetryAdmin._format_ids(m, a),
    }
