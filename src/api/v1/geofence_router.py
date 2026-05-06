import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.geofence_schema import (
    GeofenceResponse,
    GeofenceRequest,
    GeofenceUpdate,
    GeofenceToggleResponse,
    DeleteGeofenceResponse,
)
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.geofence_service import GeofenceService

router = APIRouter(prefix="/lessor", tags=["Lessor Geofences"])


@router.get("/cars/{car_id}/geofences", response_model=list[GeofenceResponse])
async def get_car_geofences(
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[GeofenceResponse]:
    try:
        geofences = await GeofenceService.get_car_geofences(car_id, user, session)
        if not geofences:
            raise HTTPException(status_code=404, detail="Geofences not found for this car")
        return [GeofenceResponse.model_validate(geofence) for geofence in geofences]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cars/{car_id}/geofences", response_model=GeofenceResponse, status_code=201)
async def create_geofence(
        car_id: uuid.UUID,
        data: GeofenceRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> GeofenceResponse:
    try:
        geofence = await GeofenceService.create_geofence(car_id, data, user, session)
        return GeofenceResponse.model_validate(geofence)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/geofences", response_model=list[GeofenceResponse])
async def get_geofences(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> list[GeofenceResponse]:
    geofences = await GeofenceService.get_geofences(session, user, skip, limit)
    if not geofences:
        raise HTTPException(status_code=404, detail="Geofences not found")
    return [GeofenceResponse.model_validate(geofence) for geofence in geofences]


@router.get("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> GeofenceResponse:
    geofence = await GeofenceService.get_geofence(geofence_id, user, session)
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    return GeofenceResponse.model_validate(geofence)


@router.put("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
        geofence_id: uuid.UUID,
        data: GeofenceUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> GeofenceResponse:
    try:
        geofence = await GeofenceService.update_geofence(geofence_id, data, user, session)
        return GeofenceResponse.model_validate(geofence)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/geofences/{geofence_id}/toggle", response_model=GeofenceToggleResponse)
async def toggle_geofence(
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> GeofenceToggleResponse:
    try:
        geofence = await GeofenceService.toggle_geofence(geofence_id, user, session)
        return GeofenceToggleResponse.model_validate(geofence)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/geofences/{geofence_id}")
async def delete_geofence(
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session)
) -> DeleteGeofenceResponse:
    deleted = await GeofenceService.delete_geofence(geofence_id, user, session)

    if deleted:
        return DeleteGeofenceResponse(
            success=True,
            message="Geofence deleted successfully",
            geofence_id=geofence_id
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Geofence not found or you don't have permission to delete it"
        )
