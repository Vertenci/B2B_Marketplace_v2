import uuid
from datetime import datetime

from pydantic import BaseModel

from src.models.enums import RentalRequestStatus


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
    message: str | None
    status: RentalRequestStatus
    created_at: datetime

    car: CarShortForRequest
    company: CompanyShortForRequest
    user: UserShortForRequest
