import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class CarShortForGeofence(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    brand: str
    model: str
    plate_number: str


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class GeofenceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    car_id: uuid.UUID
    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: int
    is_active: bool
    created_at: datetime
    car: CarShortForGeofence | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "car_id": obj.car_id,
                "name": obj.name,
                "center_lat": obj.center_lat,
                "center_lng": obj.center_lng,
                "radius_meters": obj.radius_meters,
                "is_active": obj.is_active,
                "created_at": obj.created_at,
                "car": _safe_get(obj, "car"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class GeofenceRequest(BaseModel):
    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: int
    is_active: bool = True


class GeofenceUpdate(BaseModel):
    name: str | None = None
    center_lat: Decimal | None = None
    center_lng: Decimal | None = None
    radius_meters: int | None = None
    is_active: bool | None = None


class GeofenceToggleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    is_active: bool


class DeleteGeofenceResponse(BaseModel):
    success: bool
    message: str
    geofence_id: uuid.UUID
