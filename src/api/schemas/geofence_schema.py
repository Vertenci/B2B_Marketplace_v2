import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


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


class CarShortForGeofence(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    brand: str
    model: str
    plate_number: str


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
