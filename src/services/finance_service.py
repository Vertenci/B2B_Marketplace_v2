import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import (
    PaymentModel,
    UserModel,
    CompanyUserModel,
    CompanyModel,
)
from src.models.enums import CompanyType


class FinanceService:
    @staticmethod
    async def get_finances(
        session: AsyncSession,
        user: UserModel,
        skip: int = 0,
        limit: int = 10
    ) -> dict:
        company_id = await FinanceService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view finances")

        stmt = (
            select(PaymentModel)
            .where(
                or_(
                    PaymentModel.receiver_company_id == company_id,
                    PaymentModel.payer_company_id == company_id
                )
            )
            .options(
                joinedload(PaymentModel.rental),
                joinedload(PaymentModel.payer_company),
                joinedload(PaymentModel.receiver_company),
            )
            .order_by(PaymentModel.paid_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        payments = result.unique().scalars().all()

        return {
            "balance": company.balance,
            "payments": payments
        }

    @staticmethod
    async def _get_company_id_for_user(
        user: UserModel,
        session: AsyncSession
    ) -> uuid.UUID:
        stmt = select(CompanyUserModel).where(
            CompanyUserModel.user_id == user.id,
            CompanyUserModel.is_active == True
        )
        result = await session.execute(stmt)
        company_user = result.scalars().first()

        if not company_user:
            raise ValueError("User is not associated with any company")

        return company_user.company_id
