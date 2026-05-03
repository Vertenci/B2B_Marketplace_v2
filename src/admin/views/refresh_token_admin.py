from datetime import datetime
from markupsafe import Markup
from sqladmin.filters import BooleanFilter, OperationColumnFilter
from wtforms.validators import DataRequired, Length

from src.admin.views.base_admin import BaseAdmin
from src.models.refresh_token_model import RefreshTokenModel


class RefreshTokenAdmin(BaseAdmin, model=RefreshTokenModel):
    name = "Refresh Token"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"
    category = "Security"
    category_icon = "fa-solid fa-key"

    page_size = 25
    column_auto_select_related = False

    column_list = [
        RefreshTokenModel.id,
        RefreshTokenModel.user_id,
        RefreshTokenModel.token_hash,
        RefreshTokenModel.expires_at,
        RefreshTokenModel.revoked,
    ]

    column_searchable_list = []

    column_filters = [
        BooleanFilter(RefreshTokenModel.revoked),
        OperationColumnFilter(RefreshTokenModel.user_id, title="User ID"),
    ]

    column_sortable_list = [
        RefreshTokenModel.expires_at,
        RefreshTokenModel.revoked,
    ]

    column_default_sort = [(RefreshTokenModel.expires_at, True)]

    form_args = {
        "user_id": {
            "validators": [DataRequired()]
        },
        "token_hash": {
            "validators": [
                DataRequired(),
                Length(min=1, max=255),
            ]
        },
        "expires_at": {
            "validators": [DataRequired()]
        },
    }

    can_create = False
    can_edit = False
    can_delete = True

    @staticmethod
    def _format_token_hash(model, attribute):
        value = model.token_hash or ""

        if len(value) <= 16:
            return Markup(f'<code style="font-size: 11px;">{value}</code>')

        short = f"{value[:8]}...{value[-8:]}"

        return Markup(
            f'<code style="font-size: 11px;" title="{value}">{short}</code>'
        )

    @staticmethod
    def _format_expires_at(model, attribute):
        expires_at = model.expires_at

        if expires_at is None:
            return "—"

        now = datetime.now(expires_at.tzinfo) if expires_at.tzinfo else datetime.now()
        time_diff = expires_at.replace(tzinfo=None) - now.replace(tzinfo=None)
        days_remaining = time_diff.days
        hours_remaining = time_diff.seconds // 3600

        formatted_date = expires_at.strftime("%Y-%m-%d %H:%M:%S")

        if time_diff.total_seconds() < 0:
            status_color = "#F44336"
            status_text = "Expired"
            bg_color = "#FFEBEE"
        elif days_remaining < 1:
            status_color = "#FF9800"
            status_text = f"Expires in {hours_remaining}h"
            bg_color = "#FFF3E0"
        elif days_remaining < 7:
            status_color = "#FFC107"
            status_text = f"Expires in {days_remaining}d"
            bg_color = "#FFF8E1"
        else:
            status_color = "#4CAF50"
            status_text = f"Valid for {days_remaining}d"
            bg_color = "#E8F5E9"

        return Markup(
            f'<div>'
            f'<span style="font-family: monospace;">{formatted_date}</span><br>'
            f'<span style="display: inline-block; padding: 2px 8px; margin-top: 4px; '
            f'background-color: {bg_color}; color: {status_color}; '
            f'border-radius: 4px; font-size: 11px; font-weight: 500;">'
            f'{status_text}'
            f'</span>'
            f'</div>'
        )

    @staticmethod
    def _format_revoked(model, attribute):
        revoked = model.revoked

        if revoked:
            return Markup(
                '<span style="display: inline-flex; align-items: center; gap: 4px;">'
                '<span style="color: #F44336; font-weight: 500;">✗ Revoked</span>'
                '</span>'
            )
        else:
            return Markup(
                '<span style="display: inline-flex; align-items: center; gap: 4px;">'
                '<span style="color: #4CAF50; font-weight: 500;">✓ Active</span>'
                '</span>'
            )

    @staticmethod
    def _format_user_id(model, attribute):
        value = model.user_id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_id(model, attribute):
        value = model.id

        if value is None:
            return "—"

        short = str(value)[:8] + "..."

        return Markup(
            f'<span title="{value}" style="font-family: monospace;">{short}</span>'
        )

    @staticmethod
    def _format_token_status(model, attribute):
        revoked = model.revoked
        expires_at = model.expires_at

        if expires_at:
            now = datetime.now(expires_at.tzinfo) if expires_at.tzinfo else datetime.now()
            is_expired = expires_at.replace(tzinfo=None) < now.replace(tzinfo=None)
        else:
            is_expired = False

        if revoked:
            status = "Revoked"
            color = "#F44336"
            icon = "🔴"
        elif is_expired:
            status = "Expired"
            color = "#FF9800"
            icon = "🟡"
        else:
            status = "Active"
            color = "#4CAF50"
            icon = "🟢"

        return Markup(
            f'<div style="padding: 15px; background-color: #f5f5f5; border-radius: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">'
            f'<span style="font-size: 24px;">{icon}</span>'
            f'<span style="font-size: 18px; font-weight: 600; color: {color};">{status}</span>'
            f'</div>'
            f'<div style="display: grid; gap: 8px;">'
            f'<div><strong>Revoked:</strong> {"Yes" if revoked else "No"}</div>'
            f'<div><strong>Expired:</strong> {"Yes" if is_expired else "No"}</div>'
            f'</div>'
            f'</div>'
        )

    column_formatters = {
        RefreshTokenModel.token_hash: _format_token_hash,
        RefreshTokenModel.expires_at: _format_expires_at,
        RefreshTokenModel.revoked: _format_revoked,
        RefreshTokenModel.user_id: _format_user_id,
        RefreshTokenModel.id: _format_id,
    }

    column_formatters_detail = {
        RefreshTokenModel.token_hash: _format_token_hash,
        RefreshTokenModel.user_id: _format_user_id,
        RefreshTokenModel.id: _format_token_status,
    }
