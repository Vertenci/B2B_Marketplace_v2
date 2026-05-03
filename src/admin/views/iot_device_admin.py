from markupsafe import Markup
from sqladmin.filters import BooleanFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from src.admin.views.base_admin import BaseAdmin
from src.models.iot_device_model import IotDeviceModel


class IotDeviceAdmin(BaseAdmin, model=IotDeviceModel):
    name = "IoT Device"
    name_plural = "IoT Devices"
    icon = "fa-solid fa-microchip"
    category = "IoT"
    category_icon = "fa-solid fa-microchip"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        IotDeviceModel.id,
        IotDeviceModel.car_id,
        IotDeviceModel.device_identifier,
        IotDeviceModel.sim_number,
        IotDeviceModel.battery_level,
        IotDeviceModel.is_online,
    ]

    column_searchable_list = [
        IotDeviceModel.device_identifier,
        IotDeviceModel.sim_number,
    ]

    column_filters = [
        BooleanFilter(IotDeviceModel.is_online),
        OperationColumnFilter(IotDeviceModel.car_id, title="Car ID"),
        OperationColumnFilter(IotDeviceModel.battery_level, title="Battery level"),
    ]

    column_sortable_list = [
        IotDeviceModel.device_identifier,
        IotDeviceModel.sim_number,
        IotDeviceModel.battery_level,
        IotDeviceModel.is_online,
    ]

    column_default_sort = [(IotDeviceModel.is_online, True), (IotDeviceModel.battery_level, False)]

    form_args = {
        "car_id": {
            "validators": [DataRequired()]
        },
        "device_identifier": {
            "validators": [
                Optional(),
                Length(min=1, max=255),
            ]
        },
        "sim_number": {
            "validators": [
                Optional(),
                Length(min=1, max=100),
            ]
        },
        "battery_level": {
            "validators": [
                Optional(),
                NumberRange(min=0, max=100, message="Battery level must be between 0 and 100")
            ]
        },
    }

    @staticmethod
    def _format_device_identifier(model, attribute):
        value = model.device_identifier or "—"

        if value == "—":
            return Markup(f'<span style="color: #999;">{value}</span>')

        if len(value) <= 20:
            return Markup(f'<span style="font-family: monospace;">{value}</span>')

        short = value[:10] + "..." + value[-7:]

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_sim_number(model, attribute):
        value = model.sim_number

        if not value:
            return Markup('<span style="color: #999;">—</span>')

        formatted = f"{value[:4]} {value[4:7]} {value[7:10]} {value[10:]}" if len(value) >= 10 else value

        return Markup(
            f'<span style="font-family: monospace;">{formatted}</span>'
        )

    @staticmethod
    def _format_battery_level(model, attribute):
        level = model.battery_level

        if level is None:
            return Markup('<span style="color: #999;">—</span>')

        if level >= 75:
            color = "#4CAF50"
            icon = "🔋"
        elif level >= 40:
            color = "#FFC107"
            icon = "⚠️"
        elif level >= 15:
            color = "#FF9800"
            icon = "❗"
        else:
            color = "#F44336"
            icon = "🚨"

        progress_bar = f"""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="min-width: 35px;">{icon} {level}%</span>
            <div style="width: 60px; height: 8px; background-color: #e0e0e0; border-radius: 4px; overflow: hidden;">
                <div style="width: {level}%; height: 100%; background-color: {color};"></div>
            </div>
        </div>
        """

        return Markup(progress_bar)

    @staticmethod
    def _format_is_online(model, attribute):
        is_online = model.is_online

        if is_online:
            return Markup(
                '<span style="display: inline-flex; align-items: center; gap: 4px;">'
                '<span style="width: 10px; height: 10px; background-color: #4CAF50; '
                'border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite;"></span>'
                '<span style="color: #4CAF50; font-weight: 500;">Online</span>'
                '</span>'
                '<style>'
                '@keyframes pulse {'
                '0% { opacity: 1; }'
                '50% { opacity: 0.5; }'
                '100% { opacity: 1; }'
                '}'
                '</style>'
            )
        else:
            return Markup(
                '<span style="display: inline-flex; align-items: center; gap: 4px;">'
                '<span style="width: 10px; height: 10px; background-color: #999; '
                'border-radius: 50%; display: inline-block;"></span>'
                '<span style="color: #999; font-weight: 500;">Offline</span>'
                '</span>'
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
    def _format_status_summary(model, attribute):
        is_online = model.is_online
        battery = model.battery_level
        device_id = model.device_identifier

        if is_online:
            status_text = "Online"
            status_color = "#4CAF50"
        else:
            status_text = "Offline"
            status_color = "#999"

        battery_text = f"{battery}%" if battery is not None else "N/A"
        battery_color = "#4CAF50" if battery and battery >= 50 else "#FF9800" if battery and battery >= 20 else "#F44336"

        return Markup(
            f'<div style="padding: 15px; background-color: #f5f5f5; border-radius: 8px;">'
            f'<div style="margin-bottom: 10px;"><strong>Device ID:</strong> <code>{device_id or "—"}</code></div>'
            f'<div style="display: flex; gap: 20px;">'
            f'<div><strong>Status:</strong> <span style="color: {status_color};">{status_text}</span></div>'
            f'<div><strong>Battery:</strong> <span style="color: {battery_color};">{battery_text}</span></div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        IotDeviceModel.device_identifier: _format_device_identifier,
        IotDeviceModel.sim_number: _format_sim_number,
        IotDeviceModel.battery_level: _format_battery_level,
        IotDeviceModel.is_online: _format_is_online,
        IotDeviceModel.car_id: _format_car_id,
    }

    column_formatters_detail = {
        IotDeviceModel.car_id: _format_car_id,
        IotDeviceModel.id: _format_status_summary,
    }
