from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.models import UserModel, CompanyModel, CompanyUserModel
from src.models.enums import CompanyType


class ProfileService:

    @staticmethod
    async def get_my_profile(user: UserModel) -> UserModel:
        return user

    @staticmethod
    async def update_my_profile(
            user: UserModel,
            phone: str | None,
            full_name: str | None,
            session: AsyncSession
    ) -> UserModel:
        if phone is not None:
            result = await session.execute(
                select(UserModel).where(
                    UserModel.phone == phone,
                    UserModel.id != user.id
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Phone already in use")
            user.phone = phone

        if full_name is not None:
            user.full_name = full_name

        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete_my_profile(
            user: UserModel,
            session: AsyncSession
    ) -> None:
        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True
            )
        )
        active_memberships = result.scalars().all()

        if active_memberships:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete account while associated with active companies"
            )

        await session.delete(user)
        await session.commit()

    @staticmethod
    async def get_my_dashboard(user: UserModel, session: AsyncSession) -> dict:
        stmt = (
            select(CompanyModel, CompanyUserModel.position)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True
            )
        )
        result = await session.execute(stmt)
        rows = result.all()

        companies_by_type: dict[CompanyType, int] = {}
        for company, position in rows:
            t = company.type
            companies_by_type[t] = companies_by_type.get(t, 0) + 1

        return {
            "total_companies": len(rows),
            "companies_by_type": [
                {"type": t, "count": c} for t, c in companies_by_type.items()
            ]
        }
