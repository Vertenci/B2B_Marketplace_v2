from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from src.core.security import verify_password
from src.db.session import db
from src.models.enums import UserRole
from src.models.user_model import UserModel


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()

        email = form.get("username")
        password = form.get("password")

        async with db.session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                return False

            if not user.is_active:
                return False

            if not verify_password(password, user.password_hash):
                return False

            if user.role != UserRole.ADMIN:
                return False

            request.session.update({"admin": str(user.id)})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_id = request.session.get("admin")

        if not admin_id:
            return False

        return True
