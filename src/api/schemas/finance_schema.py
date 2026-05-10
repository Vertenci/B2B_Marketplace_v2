import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.models.enums import PaymentStatus, PaymentType, RentalStatus


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class PaymentShort(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    amount: Decimal
    commission_amount: Decimal
    status: PaymentStatus
    payment_method: PaymentType
    paid_at: datetime | None = None


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
    paid_at: datetime | None = None

    rental: RentalRef | None = None
    payer_company: CompanyRef | None = None
    receiver_company: CompanyRef | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
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


class FinanceResponse(BaseModel):
    balance: Decimal
    payments: list[PaymentResponse] = []
