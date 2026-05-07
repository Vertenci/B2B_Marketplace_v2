import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.models.enums import RentalStatus, CompanyType, CarStatus, RentalRequestStatus


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
