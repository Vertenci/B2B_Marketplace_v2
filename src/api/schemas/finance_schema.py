import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import PaymentStatus, PaymentType, RentalStatus, BalanceEventType


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class CompanyRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    inn: str


class RentalRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start_date: datetime
    end_date: datetime
    base_price_total: Decimal
    status: RentalStatus


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None = None

    rental: RentalRef | None = None
    payer_company: CompanyRef | None = None
    receiver_company: CompanyRef | None = None

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
                "rental": _safe_get(obj, "rental"),
                "payer_company": _safe_get(obj, "payer_company"),
                "receiver_company": _safe_get(obj, "receiver_company"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class BalanceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    event_type: BalanceEventType
    balance_before: Decimal
    balance_after: Decimal
    operation_amount: Decimal
    created_at: datetime

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "company_id": obj.company_id,
                "event_type": obj.event_type,
                "balance_before": obj.balance_before,
                "balance_after": obj.balance_after,
                "operation_amount": obj.operation_amount,
                "created_at": obj.created_at,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class FinanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance: Decimal
    payments: list[PaymentResponse] = []
    balance_events: list[BalanceEventResponse] = []


class BalanceAmountRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount must be greater than zero")

    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    model_config = {"from_attributes": True}
