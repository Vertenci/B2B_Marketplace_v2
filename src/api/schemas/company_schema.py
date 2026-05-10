import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models.enums import CompanyType, CompanyRole


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    inn: str = Field(min_length=10, max_length=255)


class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    inn: str
    type: CompanyType
    balance: Decimal
    is_verified: bool
    created_at: datetime


class CompanyTypeItem(BaseModel):
    type: CompanyType
    label: str


class CompanyUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID
    position: CompanyRole
    is_active: bool
    created_at: datetime


class AddOwnerRequest(BaseModel):
    user_email: str = Field(min_length=5, max_length=255)


class LessorDashboardResponse(BaseModel):
    total_cars: int
    total_rentals: int
    active_rentals: int
    total_requests: int
    pending_requests: int
    balance: Decimal


class RenterDashboardResponse(BaseModel):
    total_drivers: int
    total_rentals: int
    active_rentals: int
    total_requests: int
    pending_requests: int
    balance: Decimal


class MainDashboardResponse(BaseModel):
    total_companies: int
    total_users: int
    total_lessor_companies: int
    total_renter_companies: int
