from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.profile_schema import ProfileResponse, ProfileUpdateRequest, MyDashboardResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.services.profile_service import ProfileService

router = APIRouter(tags=["My Profile"])


@router.get("/my_profile", response_model=ProfileResponse)
async def get_my_profile(
        user: UserModel = Depends(get_current_user),
) -> ProfileResponse:
    return ProfileResponse.model_validate(user)


@router.put("/my_profile", response_model=ProfileResponse)
async def update_my_profile(
        data: ProfileUpdateRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> ProfileResponse:
    updated = await ProfileService.update_my_profile(
        user=user,
        phone=data.phone,
        full_name=data.full_name,
        session=session,
    )
    return ProfileResponse.model_validate(updated)


@router.delete("/my_profile", status_code=204)
async def delete_my_profile(
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    await ProfileService.delete_my_profile(user=user, session=session)


@router.get("/my_dashboard", response_model=MyDashboardResponse)
async def get_my_dashboard(
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> MyDashboardResponse:
    data = await ProfileService.get_my_dashboard(user=user, session=session)
    return MyDashboardResponse(**data)
