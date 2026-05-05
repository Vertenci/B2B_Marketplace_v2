import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.car_schema import CarResponse, CarRequest, CarUpdate, CarStatusRequest, CarStatusResponse, \
    DeleteResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.car_service import CarService

router = APIRouter(prefix="/lessor/cars", tags=["Lessor Cars"])

@router.get("", response_model=list[CarResponse])
async def get_cars(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[CarResponse]:
    cars = await CarService.get_cars(session, user, skip, limit)
    if not cars:
        raise HTTPException(status_code=404, detail="Cars not found")
    return [CarResponse.model_validate(car) for car in cars]


@router.get("{car_id}", response_model=CarResponse)
async def get_car(
        car_id: uuid.UUID,
        session: AsyncSession = Depends(db.get_session),
        user: UserModel = Depends(get_current_user),
) -> CarResponse:
    car = await CarService.get_car(car_id, user, session)
    if not car:
        raise HTTPException(status_code=404, detail="Cars not found")
    return CarResponse.model_validate(car)


@router.post("", response_model=CarResponse)
async def add_car(
        data: CarRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> CarResponse:
    car = await CarService.add_car(data, user, session)
    if not car:
        raise HTTPException(status_code=404, detail="Car not created")
    return CarResponse.model_validate(car)


@router.put("/{car_id}", response_model=CarResponse)
async def update_car(
        car_id: uuid.UUID,
        data: CarUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> CarResponse:
        car = await CarService.update_car(car_id, data, user, session)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return CarResponse.model_validate(car)

@router.patch("/{car_id}/status", response_model=CarStatusResponse)
async def update_car_status(
        car_id: uuid.UUID,
        data: CarStatusRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarStatusResponse:
    car_status = CarService.update_car_status(car_id, data, user, session)
    if not car_status:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarStatusResponse.model_validate(car_status)


@router.delete("/{car_id}")
async def delete_car(
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> DeleteResponse:
    deleted = await CarService.delete_car(car_id, user, session)

    if deleted:
        return DeleteResponse(
            success=True,
            message="Car deleted successfully",
            car_id=car_id
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Car not found or you don't have permission to delete it"
        )
