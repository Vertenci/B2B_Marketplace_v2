import uuid
from decimal import Decimal
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import (
    UserModel,
    CompanyModel,
    CompanyUserModel,
    RentalModel,
    RentalRequestModel,
)
from src.models.enums import (
    CompanyType,
    CompanyRole,
    RentalStatus,
    RentalRequestStatus,
    CarStatus,
)


class CompanyService:

    @staticmethod
    async def create_company(
            user: UserModel,
            company_type: CompanyType,
            name: str,
            inn: str,
            session: AsyncSession
    ) -> CompanyModel:
        # Проверим уникальность имени
        result = await session.execute(
            select(CompanyModel).where(CompanyModel.name == name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Company name already exists")

        result = await session.execute(
            select(CompanyModel).where(CompanyModel.inn == inn)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Company INN already exists")

        company = CompanyModel(name=name, inn=inn, type=company_type)
        session.add(company)
        await session.flush()

        # Добавляем создателя как владельца
        company_user = CompanyUserModel(
            user_id=user.id,
            company_id=company.id,
            position=CompanyRole.OWNER,
            is_active=True
        )
        session.add(company_user)

        await session.commit()
        await session.refresh(company)
        return company

    @staticmethod
    async def get_company_types() -> list[dict]:
        return [
            {"type": CompanyType.LESSOR, "label": "Арендодатель (Lessor)"},
            {"type": CompanyType.RENTER, "label": "Арендатор (Renter)"},
        ]

    @staticmethod
    async def get_my_lessor_companies(
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[CompanyModel]:
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True,
                CompanyModel.type == CompanyType.LESSOR,
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_my_renter_companies(
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[CompanyModel]:
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True,
                CompanyModel.type == CompanyType.RENTER,
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_company_for_user(
            company_id: uuid.UUID,
            user: UserModel,
            company_type: CompanyType,
            session: AsyncSession
    ) -> CompanyModel:
        """Получить компанию и убедиться что пользователь к ней принадлежит."""
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyModel.id == company_id,
                CompanyModel.type == company_type,
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True,
            )
        )
        result = await session.execute(stmt)
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found or access denied")
        return company

    @staticmethod
    async def get_lessor_dashboard(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> dict:
        company = await CompanyService.get_company_for_user(
            company_id, user, CompanyType.LESSOR, session
        )

        from src.models import CarModel
        # Кол-во машин
        total_cars_res = await session.execute(
            select(func.count()).select_from(CarModel).where(CarModel.owner_company_id == company_id)
        )
        total_cars = total_cars_res.scalar() or 0

        # Аренды
        total_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(RentalModel.lessor_company_id == company_id)
        )
        total_rentals = total_rentals_res.scalar() or 0

        active_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(
                RentalModel.lessor_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
        )
        active_rentals = active_rentals_res.scalar() or 0

        # Заявки
        total_req_res = await session.execute(
            select(func.count()).select_from(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(CarModel.owner_company_id == company_id)
        )
        total_requests = total_req_res.scalar() or 0

        pending_req_res = await session.execute(
            select(func.count()).select_from(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(
                CarModel.owner_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING
            )
        )
        pending_requests = pending_req_res.scalar() or 0

        return {
            "total_cars": total_cars,
            "total_rentals": total_rentals,
            "active_rentals": active_rentals,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "balance": company.balance,
        }

    @staticmethod
    async def get_renter_dashboard(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> dict:
        company = await CompanyService.get_company_for_user(
            company_id, user, CompanyType.RENTER, session
        )

        # Кол-во водителей
        drivers_res = await session.execute(
            select(func.count()).select_from(CompanyUserModel).where(
                CompanyUserModel.company_id == company_id,
                CompanyUserModel.position == CompanyRole.DRIVER,
                CompanyUserModel.is_active == True
            )
        )
        total_drivers = drivers_res.scalar() or 0

        total_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(RentalModel.renter_company_id == company_id)
        )
        total_rentals = total_rentals_res.scalar() or 0

        active_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(
                RentalModel.renter_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
        )
        active_rentals = active_rentals_res.scalar() or 0

        total_req_res = await session.execute(
            select(func.count()).select_from(RentalRequestModel).where(
                RentalRequestModel.renter_company_id == company_id
            )
        )
        total_requests = total_req_res.scalar() or 0

        pending_req_res = await session.execute(
            select(func.count()).select_from(RentalRequestModel).where(
                RentalRequestModel.renter_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING
            )
        )
        pending_requests = pending_req_res.scalar() or 0

        return {
            "total_drivers": total_drivers,
            "total_rentals": total_rentals,
            "active_rentals": active_rentals,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "balance": company.balance,
        }

    @staticmethod
    async def delete_lessor_company(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        company = await CompanyService.get_company_for_user(
            company_id, user, CompanyType.LESSOR, session
        )

        # Проверяем: нет активных аренд
        active_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(
                RentalModel.lessor_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
        )
        if (active_rentals_res.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Cannot delete company with active rentals")

        # Нет активных заявок
        from src.models import CarModel
        pending_req_res2 = await session.execute(
            select(func.count()).select_from(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(
                CarModel.owner_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING
            )
        )
        if (pending_req_res2.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Cannot delete company with pending requests")

        # Все машины должны быть HIDDEN
        from src.models import CarModel
        non_hidden_res = await session.execute(
            select(func.count()).select_from(CarModel).where(
                CarModel.owner_company_id == company_id,
                CarModel.status != CarStatus.HIDDEN
            )
        )
        if (non_hidden_res.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="All cars must be HIDDEN before deleting company")

        await session.delete(company)
        await session.commit()

    @staticmethod
    async def delete_renter_company(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        company = await CompanyService.get_company_for_user(
            company_id, user, CompanyType.RENTER, session
        )

        # Нет активных аренд
        active_rentals_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(
                RentalModel.renter_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
        )
        if (active_rentals_res.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Cannot delete company with active rentals")

        # Нет неоплаченных завершённых аренд
        unpaid_res = await session.execute(
            select(func.count()).select_from(RentalModel).where(
                RentalModel.renter_company_id == company_id,
                RentalModel.status == RentalStatus.COMPLETED,
                RentalModel.is_paid == False
            )
        )
        if (unpaid_res.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Cannot delete company with unpaid rentals")

        # Нет активных заявок
        pending_req_res = await session.execute(
            select(func.count()).select_from(RentalRequestModel).where(
                RentalRequestModel.renter_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING
            )
        )
        if (pending_req_res.scalar() or 0) > 0:
            raise HTTPException(status_code=400, detail="Cannot delete company with active requests")

        await session.delete(company)
        await session.commit()

    @staticmethod
    async def add_owner_to_company(
            company_id: uuid.UUID,
            user_email: str,
            current_user: UserModel,
            company_type: CompanyType,
            session: AsyncSession
    ) -> CompanyUserModel:
        """Добавить ещё одного владельца к компании."""
        await CompanyService.get_company_for_user(
            company_id, current_user, company_type, session
        )

        # Находим пользователя по email
        result = await session.execute(
            select(UserModel).where(UserModel.email == user_email.strip().lower())
        )
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверяем, не добавлен ли уже
        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.user_id == target_user.id,
                CompanyUserModel.company_id == company_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.is_active:
                raise HTTPException(status_code=400, detail="User is already in this company")
            # Реактивируем
            existing.is_active = True
            existing.position = CompanyRole.OWNER
            await session.commit()
            await session.refresh(existing)
            return existing

        company_user = CompanyUserModel(
            user_id=target_user.id,
            company_id=company_id,
            position=CompanyRole.OWNER,
            is_active=True
        )
        session.add(company_user)
        await session.commit()
        await session.refresh(company_user)
        return company_user

    @staticmethod
    async def get_main_dashboard(session: AsyncSession) -> dict:
        """Публичная статистика для главной страницы."""
        total_companies_res = await session.execute(
            select(func.count()).select_from(CompanyModel)
        )
        total_companies = total_companies_res.scalar() or 0

        total_users_res = await session.execute(
            select(func.count()).select_from(UserModel)
        )
        total_users = total_users_res.scalar() or 0

        lessor_res = await session.execute(
            select(func.count()).select_from(CompanyModel).where(CompanyModel.type == CompanyType.LESSOR)
        )
        total_lessor = lessor_res.scalar() or 0

        renter_res = await session.execute(
            select(func.count()).select_from(CompanyModel).where(CompanyModel.type == CompanyType.RENTER)
        )
        total_renter = renter_res.scalar() or 0

        return {
            "total_companies": total_companies,
            "total_users": total_users,
            "total_lessor_companies": total_lessor,
            "total_renter_companies": total_renter,
        }
