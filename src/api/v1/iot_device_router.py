import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.iot_device_schema import (
    IotDeviceResponse,
    IotDeviceRequest,
    IotDeviceUpdate,
    DeleteIotResponse,
)
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.iot_device_service import IotDeviceService

router = APIRouter(prefix="/lessor/iots", tags=["Lessor IoT Devices"])


@router.get("", response_model=list[IotDeviceResponse])
async def get_iots(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[IotDeviceResponse]:
    iots = await IotDeviceService.get_iots(session, user, skip, limit)
    if not iots:
        raise HTTPException(status_code=404, detail="IoT devices not found")
    return [IotDeviceResponse.model_validate(iot) for iot in iots]


@router.get("/{iot_id}", response_model=IotDeviceResponse)
async def get_iot(
        iot_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> IotDeviceResponse:
    iot = await IotDeviceService.get_iot(iot_id, session, user)
    if not iot:
        raise HTTPException(status_code=404, detail="IoT device not found")
    return IotDeviceResponse.model_validate(iot)


@router.post("", response_model=IotDeviceResponse, status_code=201)
async def add_iot(
        data: IotDeviceRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> IotDeviceResponse:
    try:
        iot = await IotDeviceService.add_iot(data, user, session)
        return IotDeviceResponse.model_validate(iot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{iot_id}", response_model=IotDeviceResponse)
async def update_iot(
        iot_id: uuid.UUID,
        data: IotDeviceUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> IotDeviceResponse:
    try:
        iot = await IotDeviceService.update_iot(iot_id, data, user, session)
        return IotDeviceResponse.model_validate(iot)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{iot_id}")
async def delete_iot(
        iot_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> DeleteIotResponse:
    deleted = await IotDeviceService.delete_iot(iot_id, user, session)

    if deleted:
        return DeleteIotResponse(
            success=True,
            message="IoT device deleted successfully",
            iot_id=iot_id
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="IoT device not found or you don't have permission to delete it"
        )
