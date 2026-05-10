import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.models.enums import RentalRequestStatus


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class CompanyShortForRequest(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    inn: str
    type: str


class CarShortForRequest(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    brand: str
    model: str
    year: str
    plate_number: str
    price_per_day: float


class UserShortForRequest(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    phone: str
    full_name: str
    role: str


class RentalRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    message: str | None = None
    status: RentalRequestStatus
    created_at: datetime

    car: CarShortForRequest | None = None
    company: CompanyShortForRequest | None = None
    user: UserShortForRequest | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "start_date": obj.start_date,
                "end_date": obj.end_date,
                "message": obj.message,
                "status": obj.status,
                "created_at": obj.created_at,
                "car": _safe_get(obj, "car"),
                "company": _safe_get(obj, "company"),
                "user": _safe_get(obj, "user"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
