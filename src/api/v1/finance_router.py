from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.finance_schema import FinanceResponse, PaymentResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.finance_service import FinanceService

router = APIRouter(prefix="/lessor/finances", tags=["Lessor Finances"])


@router.get("", response_model=FinanceResponse)
async def get_finances(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session)
) -> FinanceResponse:
    try:
        finances = await FinanceService.get_finances(session, user, skip, limit)
        return FinanceResponse(
            balance=finances["balance"],
            payments=[PaymentResponse.model_validate(p) for p in finances["payments"]]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
