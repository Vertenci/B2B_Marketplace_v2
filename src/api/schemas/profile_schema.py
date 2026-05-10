import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.models.enums import UserRole, CompanyType


class ProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    phone: str
    full_name: str
    role: UserRole
    is_active: bool
    public_offer_accepted: bool
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    phone: str | None = Field(None, min_length=7, max_length=50)
    full_name: str | None = Field(None, min_length=2, max_length=150)


class CompanyCountByType(BaseModel):
    type: CompanyType
    count: int


class MyDashboardResponse(BaseModel):
    total_companies: int
    companies_by_type: list[CompanyCountByType]
