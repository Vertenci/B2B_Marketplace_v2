import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from src.core.settings import settings
from src.models.refresh_token_model import RefreshTokenModel
from src.models.user_model import UserModel


class AuthService:
    @staticmethod
    async def register(
            email: str,
            password: str,
            session: AsyncSession,
    ) -> UserModel:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )

        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

        user = UserModel(email=email,)
        user.password = password

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def login(email: str, password: str, session: AsyncSession):
        result = await session.execute(select(UserModel).where(UserModel.email == email))

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is not active")

        access_token = create_access_token(str(user.id), user.system_role.value)
        token_id, refresh_token, token_hash = create_refresh_token()

        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        token = RefreshTokenModel(id=uuid.UUID(token_id), user_id=user.id, token_hash=token_hash, expires_at=expire)

        session.add(token)
        await session.commit()

        return access_token, refresh_token

    @staticmethod
    async def refresh(refresh_token: str, session: AsyncSession):
        try:
            token_id, secret = refresh_token.split('.')
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = await session.execute(select(RefreshTokenModel).where(RefreshTokenModel.id == uuid.UUID(token_id)))

        token = result.scalar_one_or_none()

        if not token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if token.revoked:
            raise HTTPException(status_code=401, detail="Token revoked")

        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")

        if not verify_token(secret, token.token_hash):
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = token.user

        access_token = create_access_token(str(user.id), user.system_role.value)

        token.revoked = True

        new_token_id, new_refresh_token, new_hash = create_refresh_token()

        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        new_token = RefreshTokenModel(
            id=uuid.UUID(new_token_id),
            user_id=user.id,
            token_hash=new_hash,
            expires_at=expire,
        )

        session.add(new_token)
        await session.commit()

        return access_token, new_refresh_token

    @staticmethod
    async def logout(refresh_token: str, session: AsyncSession):
        try:
            token_id, secret = refresh_token.split(".")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = await session.execute(
            select(RefreshTokenModel)
            .where(RefreshTokenModel.id == uuid.UUID(token_id))
        )

        token = result.scalar_one_or_none()

        if not token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if not verify_token(secret, token.token_hash):
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        token.revoked = True

        await session.commit()
