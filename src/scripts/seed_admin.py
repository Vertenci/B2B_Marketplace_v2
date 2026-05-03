import asyncio
import logging

from passlib.context import CryptContext
from sqlalchemy import select

from src.core.settings import settings
from src.db.session import db
from src.models.enums import UserRole
from src.models.user_model import UserModel

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def seed():
    async with db.session_factory() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.role == UserRole.ADMIN)
        )
        admin_exists = result.scalar_one_or_none()

        if admin_exists:
            logger.info("Admin already exists")
            return

        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            raise ValueError("ADMIN_EMAIL and ADMIN_PASSWORD must be set")

        user = UserModel(
            email=settings.ADMIN_EMAIL,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            phone="+70000000000",
            full_name="Admin",
            role=UserRole.ADMIN,
        )

        session.add(user)
        await session.commit()

        logger.info("Admin created successfully")


if __name__ == "__main__":
    asyncio.run(seed())
