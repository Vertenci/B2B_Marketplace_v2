import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.car_schema import CarResponse
from src.api.schemas.company_schema import CompanyResponse
from src.api.schemas.rental_schema import (
    RentalResponse, TelemetryDetailResponse, ViolationDetailResponse, GeofenceEventShort,
)
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import RentalStatus
from src.services.driver_service import DriverService

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get("/my_company", response_model=CompanyResponse)
async def get_my_company(
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CompanyResponse:
    company = await DriverService.get_my_company(user, session)
    if not company:
        raise HTTPException(status_code=404, detail="You are not in any company as a driver")
    return CompanyResponse.model_validate(company)


@router.get("/my_company/rentals", response_model=list[RentalResponse])
async def get_company_rentals(
        status: RentalStatus | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalResponse]:
    rentals = await DriverService.get_my_rentals(user, session, status, skip, limit)
    return [RentalResponse.model_validate(r) for r in rentals]


@router.get("/rentals/{rental_id}", response_model=RentalResponse)
async def get_rental(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalResponse:
    rental = await DriverService.get_rental(rental_id, user, session)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return RentalResponse.model_validate(rental)


@router.get("/rentals/{rental_id}/car", response_model=CarResponse)
async def get_rental_car(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await DriverService.get_rental_car(rental_id, user, session)
    return CarResponse.model_validate(car)


@router.get("/rentals/{rental_id}/telemetry", response_model=TelemetryDetailResponse)
async def get_rental_telemetry(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> TelemetryDetailResponse:
    telemetry = await DriverService.get_rental_telemetry(rental_id, user, session)
    if not telemetry:
        raise HTTPException(status_code=404, detail="Telemetry not found")
    return TelemetryDetailResponse.model_validate(telemetry)


@router.get("/rentals/{rental_id}/violations", response_model=list[ViolationDetailResponse])
async def get_rental_violations(
        rental_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[ViolationDetailResponse]:
    violations = await DriverService.get_rental_violations(rental_id, user, session, skip, limit)
    return [ViolationDetailResponse.model_validate(v) for v in violations]


@router.get("/rentals/{rental_id}/geofence_events", response_model=list[GeofenceEventShort])
async def get_geofence_events(
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[GeofenceEventShort]:
    events = await DriverService.get_rental_geofence_events(rental_id, user, session)
    return [GeofenceEventShort.model_validate(e) for e in events]
