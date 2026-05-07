import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.rental_request_schema import RentalRequestResponse
from src.api.schemas.rental_schema import RentalResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import RentalRequestStatus
from src.services.rental_request_service import RentalRequestService

router = APIRouter(prefix="/lessor/requests", tags=["Lessor Rental Requests"])


@router.get("", response_model=list[RentalRequestResponse])
async def get_incoming_requests(
        status: RentalRequestStatus | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[RentalRequestResponse]:
    try:
        requests = await RentalRequestService.get_incoming_requests(
            session, user, status, skip, limit
        )
        if not requests:
            raise HTTPException(status_code=404, detail="Rental requests not found")
        return [RentalRequestResponse.model_validate(req) for req in requests]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/approve", response_model=RentalResponse)
async def approve_request(
    request_id: uuid.UUID,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session)
) -> RentalResponse:
    try:
        rental = await RentalRequestService.approve_request(request_id, user, session)
        return RentalResponse.model_validate(rental)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reject", response_model=RentalRequestResponse)
async def reject_request(
    request_id: uuid.UUID,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session)
) -> RentalRequestResponse:
    try:
        request = await RentalRequestService.reject_request(request_id, user, session)
        return RentalRequestResponse.model_validate(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
