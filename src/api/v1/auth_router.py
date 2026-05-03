from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.auth_schema import RegisterRequest, LoginRequest, RefreshRequest
from src.db.session import db
from src.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register")
async def register(data: RegisterRequest, session: AsyncSession = Depends(db.get_session)):
    user = await AuthService.register(email=data.email, password=data.password, session=session)
    return {
        "id": str(user.id),
        "email": user.email,
    }


@router.post("/login")
async def login(data: LoginRequest, session: AsyncSession = Depends(db.get_session)):
    access, refresh = await AuthService.login(
        email=data.email,
        password=data.password,
        session=session,
    )

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(data: RefreshRequest, session: AsyncSession = Depends(db.get_session)):
    access, refresh = await AuthService.refresh(refresh_token=data.refresh_token, session=session)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(data: RefreshRequest, session: AsyncSession = Depends(db.get_session)):
    await AuthService.logout(refresh_token=data.refresh_token, session=session)
    return {"status": "ok"}
