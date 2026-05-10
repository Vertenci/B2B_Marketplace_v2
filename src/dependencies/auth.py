from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import settings
from src.db.session import db
from src.models.user_model import UserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(db.get_session)
) -> UserModel:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await session.execute(select(UserModel).where(UserModel.id == user_id))

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


async def get_current_user_with_offer(
        user: UserModel = Depends(get_current_user)
) -> UserModel:
    """Требует принятия публичной оферты."""
    if not user.public_offer_accepted:
        raise HTTPException(
            status_code=403,
            detail="You must accept the public offer before using this service"
        )
    return user


def require_role(role: str):
    async def checker(user: UserModel = Depends(get_current_user)):
        if user.role.value != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker
