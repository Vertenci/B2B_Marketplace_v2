import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.models.enums import CarStatus, CompanyType, RentalRequestStatus, RentalStatus


class CarResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    brand: str
    model: str
    year: str
    plate_number: str
    vin: str
    price_per_day: Decimal
    status: CarStatus

    company: CompanyShort
    iot_device: IotDeviceShort | None = None
    geofences: list[GeofenceShort] = []
    rental_requests: list[RentalRequestShort] = []
    rentals: list[RentalShort] = []
    telemetries: list[TelemetryShort] = []


class CompanyShort(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    type: CompanyType
    is_verified: bool
    created_at: datetime


class IotDeviceShort(BaseModel):
    model_config = {"from_attributes": True}

    device_identifier: str | None
    sim_number: str | None
    battery_level: int | None
    is_online: bool


class GeofenceShort(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: int
    is_active: bool
    created_at: datetime


class RentalRequestShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user: UserShort
    start_date: datetime
    end_date: datetime
    message: str | None
    status: RentalRequestStatus


class RentalShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    actual_return_date: datetime | None
    base_price_total: Decimal
    status: RentalStatus
    is_paid: bool

    lessor_company: CompanyShort
    renter_company: CompanyShort


class UserShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str


class TelemetryShort(BaseModel):
    model_config = {"from_attributes": True}

    lat: Decimal
    lng: Decimal
    speed: int
    recorded_at: datetime


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
