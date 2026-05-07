import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.models.enums import (
    RentalStatus,
    CompanyType,
    CarStatus,
    RentalRequestStatus,
    GeofenceType,
    ViolationType,
    SeverityType,
    PaymentStatus,
    PaymentType,
    RentalDocumentType,
)


class CompanyShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    inn: str
    type: CompanyType
    is_verified: bool


class CarShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    brand: str
    model: str
    year: str
    plate_number: str
    vin: str
    price_per_day: Decimal
    status: CarStatus


class UserShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    phone: str
    full_name: str


class RentalRequestShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    message: str | None
    status: RentalRequestStatus


class PaymentShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None
    payer_company: CompanyShort | None = None
    receiver_company: CompanyShort | None = None


class RentalDocumentShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: RentalDocumentType
    file_path: str
    generated_at: datetime


class TelemetryShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    lat: Decimal
    lng: Decimal
    speed: int
    recorded_at: datetime


class GeofenceShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: int


class GeofenceEventShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: GeofenceType
    lat: Decimal
    lng: Decimal
    triggered_at: datetime
    geofence: GeofenceShort | None = None


class ViolationShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: ViolationType | None
    severity: SeverityType | None
    created_at: datetime


class TelemetryDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    lat: Decimal
    lng: Decimal
    speed: int
    recorded_at: datetime

    rental: RentalShort | None = None
    car: CarShort | None = None
    user: UserShort | None = None


class RentalShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    status: RentalStatus


class GeofenceEventDetailShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: GeofenceType
    lat: Decimal
    lng: Decimal
    triggered_at: datetime
    geofence: GeofenceShort | None = None


class ViolationDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: ViolationType | None
    severity: SeverityType | None
    created_at: datetime

    geofence_event: GeofenceEventDetailShort | None = None




class RentalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    request_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    actual_return_date: datetime | None
    base_price_total: Decimal
    extra_days_fee: Decimal
    status: RentalStatus
    is_paid: bool
    created_at: datetime

    rental_request: RentalRequestShort | None = None
    lessor_company: CompanyShort | None = None
    renter_company: CompanyShort | None = None
    car: CarShort | None = None
    user: UserShort | None = None

    payment: PaymentShort | None = None

    rental_documents: list[RentalDocumentShort] = []

    telemetries: list[TelemetryShort] = []
    geofence_events: list[GeofenceEventShort] = []
    violations: list[ViolationShort] = []
