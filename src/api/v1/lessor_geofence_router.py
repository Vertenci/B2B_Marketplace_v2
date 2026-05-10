import io
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.api.schemas.geofence_schema import (
    GeofenceResponse, GeofenceRequest, GeofenceUpdate,
    GeofenceToggleResponse, DeleteGeofenceResponse
)
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.lessor_service import LessorService

router = APIRouter(prefix="/lessor/{company_id}", tags=["Lessor - Geofences"])


@router.get("/cars/{car_id}/geofences", response_model=list[GeofenceResponse])
async def get_car_geofences(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[GeofenceResponse]:
    geofences = await LessorService.get_car_geofences(company_id, car_id, user, session)
    return [GeofenceResponse.model_validate(g) for g in geofences]


@router.post("/cars/{car_id}/geofences", response_model=GeofenceResponse, status_code=201)
async def create_geofence(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        data: GeofenceRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> GeofenceResponse:
    geofence = await LessorService.create_geofence(company_id, car_id, data, user, session)
    return GeofenceResponse.model_validate(geofence)


@router.get("/geofences", response_model=list[GeofenceResponse])
async def get_all_geofences(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[GeofenceResponse]:
    geofences = await LessorService.get_all_geofences(company_id, user, session, skip, limit)
    return [GeofenceResponse.model_validate(g) for g in geofences]


@router.get("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
        company_id: uuid.UUID,
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> GeofenceResponse:
    geofence = await LessorService.get_geofence(company_id, geofence_id, user, session)
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    return GeofenceResponse.model_validate(geofence)


@router.put("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
        company_id: uuid.UUID,
        geofence_id: uuid.UUID,
        data: GeofenceUpdate,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> GeofenceResponse:
    geofence = await LessorService.update_geofence(company_id, geofence_id, data, user, session)
    return GeofenceResponse.model_validate(geofence)


@router.patch("/geofences/{geofence_id}/toggle", response_model=GeofenceToggleResponse)
async def toggle_geofence(
        company_id: uuid.UUID,
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> GeofenceToggleResponse:
    geofence = await LessorService.toggle_geofence(company_id, geofence_id, user, session)
    return GeofenceToggleResponse.model_validate(geofence)


@router.delete("/geofences/{geofence_id}", response_model=DeleteGeofenceResponse)
async def delete_geofence(
        company_id: uuid.UUID,
        geofence_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> DeleteGeofenceResponse:
    await LessorService.delete_geofence(company_id, geofence_id, user, session)
    return DeleteGeofenceResponse(
        success=True,
        message="Geofence deleted successfully",
        geofence_id=geofence_id
    )
