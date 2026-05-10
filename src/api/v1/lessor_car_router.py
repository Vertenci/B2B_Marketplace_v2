import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.car_schema import (
    CarResponse, CarRequest, CarUpdate, CarStatusRequest,
    CarStatusResponse, DeleteResponse, AttachIotRequest
)
from src.api.schemas.iot_device_schema import IotDeviceResponse, IotDeviceRequest, IotDeviceUpdate
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.lessor_service import LessorService

router = APIRouter(prefix="/lessor/{company_id}", tags=["Lessor - Cars & IoT"])


# ─────────────────────── Cars ───────────────────────────────────────────────

@router.get("/cars", response_model=list[CarResponse])
async def get_cars(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[CarResponse]:
    cars = await LessorService.get_cars(company_id, user, session, skip, limit)
    return [CarResponse.model_validate(c) for c in cars]


@router.get("/cars/{car_id}", response_model=CarResponse)
async def get_car(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await LessorService.get_car(company_id, car_id, user, session)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarResponse.model_validate(car)


@router.post("/cars", response_model=CarResponse, status_code=201)
async def add_car(
        company_id: uuid.UUID,
        data: CarRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await LessorService.add_car(company_id, data, user, session)
    return CarResponse.model_validate(car)


@router.put("/cars/{car_id}", response_model=CarResponse)
async def update_car(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        data: CarUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await LessorService.update_car(company_id, car_id, data, user, session)
    return CarResponse.model_validate(car)


@router.delete("/cars/{car_id}", response_model=DeleteResponse)
async def delete_car(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> DeleteResponse:
    deleted = await LessorService.delete_car(company_id, car_id, user, session)
    if deleted:
        return DeleteResponse(success=True, message="Car deleted successfully", car_id=car_id)
    raise HTTPException(status_code=404, detail="Car not found or cannot be deleted")


@router.patch("/cars/{car_id}/status", response_model=CarStatusResponse)
async def update_car_status(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        data: CarStatusRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarStatusResponse:
    car = await LessorService.update_car_status(company_id, car_id, data, user, session)
    return CarStatusResponse.model_validate(car)


@router.post("/cars/{car_id}/iot", response_model=CarResponse)
async def attach_iot_to_car(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        data: AttachIotRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await LessorService.attach_iot_to_car(company_id, car_id, data.iot_id, user, session)
    return CarResponse.model_validate(car)


@router.get("/cars/{car_id}/iot", response_model=IotDeviceResponse)
async def get_car_iot(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> IotDeviceResponse:
    iot = await LessorService.get_car_iot(company_id, car_id, user, session)
    if not iot:
        raise HTTPException(status_code=404, detail="IoT device not found")
    return IotDeviceResponse.model_validate(iot)


# ─────────────────────── IoT Devices ─────────────────────────────────────────

@router.get("/iots", response_model=list[IotDeviceResponse])
async def get_iots(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[IotDeviceResponse]:
    iots = await LessorService.get_iots(company_id, user, session, skip, limit)
    return [IotDeviceResponse.model_validate(i) for i in iots]


@router.get("/iots/{iot_id}", response_model=IotDeviceResponse)
async def get_iot(
        company_id: uuid.UUID,
        iot_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> IotDeviceResponse:
    iot = await LessorService.get_iot(company_id, iot_id, user, session)
    if not iot:
        raise HTTPException(status_code=404, detail="IoT device not found")
    return IotDeviceResponse.model_validate(iot)


@router.post("/iots", response_model=IotDeviceResponse, status_code=201)
async def add_iot(
        company_id: uuid.UUID,
        data: IotDeviceRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> IotDeviceResponse:
    iot = await LessorService.add_iot(company_id, data, user, session)
    return IotDeviceResponse.model_validate(iot)


@router.put("/iots/{iot_id}", response_model=IotDeviceResponse)
async def update_iot(
        company_id: uuid.UUID,
        iot_id: uuid.UUID,
        data: IotDeviceUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> IotDeviceResponse:
    iot = await LessorService.update_iot(company_id, iot_id, data, user, session)
    return IotDeviceResponse.model_validate(iot)


@router.delete("/iots/{iot_id}", status_code=204)
async def delete_iot(
        company_id: uuid.UUID,
        iot_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    await LessorService.delete_iot(company_id, iot_id, user, session)
