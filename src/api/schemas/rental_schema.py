import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

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


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


def _safe_list(obj: Any, attr: str) -> list:
    try:
        val = getattr(obj, attr)
        return list(val) if val is not None else []
    except Exception:
        return []


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
    message: str | None = None
    status: RentalRequestStatus


class PaymentShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None = None
    payer_company: CompanyShort | None = None
    receiver_company: CompanyShort | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "amount": obj.amount,
                "commission_amount": obj.commission_amount,
                "status": obj.status,
                "payment_method": obj.payment_method,
                "paid_at": obj.paid_at,
                "payer_company": _safe_get(obj, "payer_company"),
                "receiver_company": _safe_get(obj, "receiver_company"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


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
    is_active: bool


class GeofenceEventShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    type: GeofenceType
    lat: Decimal
    lng: Decimal
    triggered_at: datetime
    geofence: GeofenceShort | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "type": obj.type,
                "lat": obj.lat,
                "lng": obj.lng,
                "triggered_at": obj.triggered_at,
                "geofence": _safe_get(obj, "geofence"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class ViolationShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    type: ViolationType | None = None
    severity: SeverityType | None = None
    created_at: datetime
    geofence_event: GeofenceEventShort | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "type": obj.type,
                "severity": obj.severity,
                "created_at": obj.created_at,
                "geofence_event": _safe_get(obj, "geofence_event"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class GeofenceEventDetailShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    type: GeofenceType
    lat: Decimal
    lng: Decimal
    triggered_at: datetime
    geofence: GeofenceShort | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id, "type": obj.type,
                "lat": obj.lat, "lng": obj.lng,
                "triggered_at": obj.triggered_at,
                "geofence": _safe_get(obj, "geofence"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class ViolationDetailResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    type: ViolationType | None = None
    severity: SeverityType | None = None
    created_at: datetime
    geofence_event: GeofenceEventDetailShort | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id, "type": obj.type,
                "severity": obj.severity, "created_at": obj.created_at,
                "geofence_event": _safe_get(obj, "geofence_event"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class RentalShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    status: RentalStatus


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

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id, "lat": obj.lat, "lng": obj.lng,
                "speed": obj.speed, "recorded_at": obj.recorded_at,
                "rental": _safe_get(obj, "rental"),
                "car": _safe_get(obj, "car"),
                "user": _safe_get(obj, "user"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class RentalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    request_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    actual_return_date: datetime | None = None
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

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "request_id": obj.request_id,
                "start_date": obj.start_date,
                "end_date": obj.end_date,
                "actual_return_date": obj.actual_return_date,
                "base_price_total": obj.base_price_total,
                "extra_days_fee": obj.extra_days_fee,
                "status": obj.status,
                "is_paid": obj.is_paid,
                "created_at": obj.created_at,
                "rental_request": _safe_get(obj, "rental_request"),
                "lessor_company": _safe_get(obj, "lessor_company"),
                "renter_company": _safe_get(obj, "renter_company"),
                "car": _safe_get(obj, "car"),
                "user": _safe_get(obj, "user"),
                "payment": _safe_get(obj, "payment"),
                "rental_documents": [
                    RentalDocumentShort.model_validate(x)
                    for x in _safe_list(obj, "rental_documents")
                ],

                "telemetries": [
                    TelemetryShort.model_validate(x)
                    for x in _safe_list(obj, "telemetries")
                ],

                "geofence_events": [
                    GeofenceEventShort.model_validate(x)
                    for x in _safe_list(obj, "geofence_events")
                ],

                "violations": [
                    ViolationShort.model_validate(x)
                    for x in _safe_list(obj, "violations")
                ],
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
