import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateRentalRequestSchema(BaseModel):
    car_id: uuid.UUID
    driver_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    message: str | None = Field(None, max_length=500)


class AddDriverRequest(BaseModel):
    driver_email: str = Field(min_length=5, max_length=255)


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class DriverCompanyUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID
    is_active: bool
    created_at: datetime

    class UserInfo(BaseModel):
        model_config = {"from_attributes": True}
        id: uuid.UUID
        email: str
        full_name: str
        phone: str

    user: "DriverCompanyUserResponse.UserInfo | None" = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
        if not isinstance(obj, dict):
            raw_user = _safe_get(obj, "user")
            data = {
                "id": obj.id,
                "user_id": obj.user_id,
                "company_id": obj.company_id,
                "is_active": obj.is_active,
                "created_at": obj.created_at,
                "user": raw_user,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
