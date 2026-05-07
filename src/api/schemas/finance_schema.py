import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.models.enums import PaymentStatus, PaymentType, RentalStatus


class PaymentShort(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None


class RentalRef(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    base_price_total: Decimal
    status: RentalStatus


class CompanyRef(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    inn: str


class PaymentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None

    rental: RentalRef | None = None
    payer_company: CompanyRef | None = None
    receiver_company: CompanyRef | None = None


class FinanceResponse(BaseModel):
    model_config = {"from_attributes": True}

    balance: Decimal
    payments: list[PaymentResponse] = []
