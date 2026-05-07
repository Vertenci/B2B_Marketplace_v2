import io
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.api.schemas.rental_schema import RentalResponse, TelemetryDetailResponse, ViolationDetailResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import RentalStatus, RentalDocumentType
from src.services.rental_service import RentalService

router = APIRouter(prefix="/lessor/rentals", tags=["Lessor Rentals"])


@router.get("", response_model=list[RentalResponse])
async def get_rentals(
        status: RentalStatus | None = Query(None, description="Фильтр по статусу: ACTIVE, COMPLETED, OVERDUE"),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[RentalResponse]:
    try:
        rentals = await RentalService.get_rentals(session, user, status, skip, limit)
        if not rentals:
            raise HTTPException(status_code=404, detail="Rentals not found")
        return [RentalResponse.model_validate(rental) for rental in rentals]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> RentalResponse:
    try:
        rental = await RentalService.get_rental_by_id(rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return RentalResponse.model_validate(rental)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}/telemetry", response_model=TelemetryDetailResponse)
async def get_rental_telemetry(
    rental_id: uuid.UUID,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session)
) -> TelemetryDetailResponse:
    try:
        telemetry = await RentalService.get_rental_telemetry(rental_id, user, session)
        if not telemetry:
            raise HTTPException(status_code=404, detail="Telemetry not found for this rental")
        return TelemetryDetailResponse.model_validate(telemetry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rental_id}/violations", response_model=list[ViolationDetailResponse])
async def get_rental_violations(
    rental_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session)
) -> list[ViolationDetailResponse]:
    try:
        violations = await RentalService.get_rental_violations(
            rental_id, user, session, skip, limit
        )
        if not violations:
            raise HTTPException(status_code=404, detail="Violations not found for this rental")
        return [ViolationDetailResponse.model_validate(v) for v in violations]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rental_id}/complete", response_model=RentalResponse)
async def complete_rental(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> RentalResponse:
    try:
        rental = await RentalService.complete_rental(rental_id, user, session)
        return RentalResponse.model_validate(rental)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rental_id}/documents/{document_type}")
async def download_document(
        rental_id: uuid.UUID,
        document_type: RentalDocumentType,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
):
    try:
        file_data, filename, content_type = await RentalService.download_document(
            rental_id, document_type, user, session
        )

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
