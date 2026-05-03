from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import AgreementType


class AcceptAgreementRequest(BaseModel):
    pass


class AgreementResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    type: AgreementType
    accepted_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None


class UserAgreementsStatusResponse(BaseModel):
    public_offer_accepted: bool
    driver_offer_accepted: bool
    public_offer_agreement: AgreementResponse | None = None
    driver_offer_agreement: AgreementResponse | None = None