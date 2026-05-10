import uuid
from decimal import Decimal
import asyncio
from typing import Sequence, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import (
    RentalRequestModel,
    CarModel,
    UserModel,
    CompanyUserModel,
    CompanyModel, RentalModel,
)
from src.models.enums import RentalRequestStatus, CompanyType, CarStatus, RentalStatus
from src.services.contract_service import ContractService


class RentalRequestService:
    @staticmethod
    async def get_incoming_requests(
            session: AsyncSession,
            user: UserModel,
            status: RentalRequestStatus | None = None,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        company_id = await RentalRequestService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view incoming requests")

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .join(CompanyModel, RentalRequestModel.renter_company_id == CompanyModel.id)
            .where(
                CarModel.owner_company_id == company_id,
                CompanyModel.type == CompanyType.RENTER
            )
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )

        if status:
            stmt = stmt.where(RentalRequestModel.status == status)

        stmt = stmt.offset(skip).limit(limit)

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def approve_request(
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel:
        lessor_company_id = await RentalRequestService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == lessor_company_id)
        result = await session.execute(company_stmt)
        lessor_company = result.scalars().first()

        if not lessor_company or lessor_company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can approve requests")

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .join(CompanyModel, RentalRequestModel.renter_company_id == CompanyModel.id)
            .where(
                RentalRequestModel.id == request_id,
                CarModel.owner_company_id == lessor_company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING,
                CompanyModel.type == CompanyType.RENTER
            )
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )
        result = await session.execute(stmt)
        request = result.unique().scalar_one_or_none()

        if not request:
            raise ValueError("Request not found, already processed, or access denied")

        if request.car.status != CarStatus.AVAILABLE:
            raise ValueError(f"Car is not available. Current status: {request.car.status.value}")

        days = (request.end_date - request.start_date).days
        if days <= 0:
            days = 1
        base_price_total = request.car.price_per_day * Decimal(days)

        rental = RentalModel(
            request_id=request.id,
            lessor_company_id=lessor_company_id,
            renter_company_id=request.renter_company_id,
            car_id=request.car_id,
            driver_id=request.driver_id,
            start_date=request.start_date,
            end_date=request.end_date,
            base_price_total=base_price_total,
            status=RentalStatus.ACTIVE,
            is_paid=False,
        )
        session.add(rental)

        request.status = RentalRequestStatus.APPROVED

        request.car.status = CarStatus.RENTED

        await session.commit()
        await session.refresh(rental)

        rental_with_relations = await RentalRequestService._get_rental_by_id(rental.id, session)

        asyncio.create_task(
            ContractService.generate_and_upload_contract(str(rental.id))
        )

        return await RentalRequestService._get_rental_by_id(rental.id, session)

    @staticmethod
    async def reject_request(
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalRequestModel:
        lessor_company_id = await RentalRequestService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == lessor_company_id)
        result = await session.execute(company_stmt)
        lessor_company = result.scalars().first()

        if not lessor_company or lessor_company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can reject requests")

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .join(CompanyModel, RentalRequestModel.renter_company_id == CompanyModel.id)
            .where(
                RentalRequestModel.id == request_id,
                CarModel.owner_company_id == lessor_company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING,
                CompanyModel.type == CompanyType.RENTER
            )
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )
        result = await session.execute(stmt)
        request = result.unique().scalar_one_or_none()

        if not request:
            raise ValueError("Request not found, already processed, or access denied")

        request.status = RentalRequestStatus.REJECTED

        await session.commit()
        await session.refresh(request)

        return request

    @staticmethod
    async def _get_rental_by_id(
            rental_id: uuid.UUID,
            session: AsyncSession
    ) -> RentalModel | None:
        stmt = (
            select(RentalModel)
            .where(RentalModel.id == rental_id)
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

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
