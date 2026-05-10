import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_validator

from src.models.enums import CarStatus, CompanyType, RentalRequestStatus, RentalStatus


class CompanyShort(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    type: CompanyType
    is_verified: bool
    created_at: datetime


class IotDeviceShort(BaseModel):
    model_config = {"from_attributes": True}

    device_identifier: str | None = None
    sim_number: str | None = None
    battery_level: int | None = None
    is_online: bool = False


class GeofenceShort(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: int
    is_active: bool
    created_at: datetime


class UserShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str


class RentalRequestShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user: UserShort | None = None
    start_date: datetime
    end_date: datetime
    message: str | None = None
    status: RentalRequestStatus


class RentalShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    actual_return_date: datetime | None = None
    base_price_total: Decimal
    status: RentalStatus
    is_paid: bool

    lessor_company: CompanyShort | None = None
    renter_company: CompanyShort | None = None


class TelemetryShort(BaseModel):
    model_config = {"from_attributes": True}

    lat: Decimal
    lng: Decimal
    speed: int
    recorded_at: datetime


def _safe_list(obj: Any, attr: str) -> list:
    """Безопасно читает lazy-атрибут — возвращает [] если поднимается lazy='raise'."""
    try:
        val = getattr(obj, attr)
        return list(val) if val is not None else []
    except Exception:
        return []


def _safe_get(obj: Any, attr: str) -> Any:
    """Безопасно читает lazy-атрибут — возвращает None если поднимается lazy='raise'."""
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class CarResponse(BaseModel):
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    id: uuid.UUID
    brand: str
    model: str
    year: str
    plate_number: str
    vin: str
    price_per_day: Decimal
    status: CarStatus

    company: CompanyShort | None = None
    iot_device: IotDeviceShort | None = None
    geofences: list[GeofenceShort] = []
    rental_requests: list[RentalRequestShort] = []
    rentals: list[RentalShort] = []
    telemetries: list[TelemetryShort] = []

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
        if not isinstance(obj, dict):
            # Безопасно читаем lazy-поля перед валидацией
            data = {
                "id": obj.id,
                "brand": obj.brand,
                "model": obj.model,
                "year": obj.year,
                "plate_number": obj.plate_number,
                "vin": obj.vin,
                "price_per_day": obj.price_per_day,
                "status": obj.status,
                "company": _safe_get(obj, "company"),
                "iot_device": _safe_get(obj, "iot_device"),
                "geofences": _safe_list(obj, "geofences"),
                "rental_requests": _safe_list(obj, "rental_requests"),
                "rentals": _safe_list(obj, "rentals"),
                "telemetries": _safe_list(obj, "telemetries"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class CarRequest(BaseModel):
    brand: str
    model: str
    year: str
    plate_number: str
    vin: str
    price_per_day: Decimal
    status: CarStatus = CarStatus.HIDDEN


class CarUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: str | None = None
    plate_number: str | None = None
    vin: str | None = None
    price_per_day: Decimal | None = None
    status: CarStatus | None = None


class CarStatusRequest(BaseModel):
    status: CarStatus


class CarStatusResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: CarStatus


class DeleteResponse(BaseModel):
    success: bool
    message: str
    car_id: uuid.UUID


class AttachIotRequest(BaseModel):
    iot_id: uuid.UUID
