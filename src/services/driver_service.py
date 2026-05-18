import uuid
from typing import Sequence, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models import (
    UserModel,
    CompanyModel,
    CompanyUserModel,
    RentalModel,
    CarModel,
    TelemetryModel,
    GeofenceEventModel,
    ViolationModel,
)
from src.models.enums import CompanyRole, RentalStatus


class DriverService:

    @staticmethod
    async def get_my_company(
            user: UserModel,
            session: AsyncSession
    ) -> CompanyModel | None:
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.position == CompanyRole.DRIVER,
                CompanyUserModel.is_active == True,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _require_driver_company(user: UserModel, session: AsyncSession) -> CompanyModel:
        company = await DriverService.get_my_company(user, session)
        if not company:
            raise HTTPException(status_code=403, detail="You are not a driver in any company")
        return company

    @staticmethod
    async def get_my_rentals(
            user: UserModel,
            session: AsyncSession,
            status: RentalStatus | None = None,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await DriverService._require_driver_company(user, session)

        stmt = (
            select(RentalModel)
            .where(RentalModel.driver_id == user.id)
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
                joinedload(RentalModel.payment),
                selectinload(RentalModel.rental_documents),
                selectinload(RentalModel.telemetries),
                selectinload(RentalModel.geofence_events).joinedload(GeofenceEventModel.geofence),
                selectinload(RentalModel.violations),
            )
        )

        if status:
            stmt = stmt.where(RentalModel.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(RentalModel.created_at.desc())
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel | None:
        await DriverService._require_driver_company(user, session)

        stmt = (
            select(RentalModel)
            .where(
                RentalModel.id == rental_id,
                RentalModel.driver_id == user.id,
            )
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
                joinedload(RentalModel.payment),
                selectinload(RentalModel.rental_documents),
                selectinload(RentalModel.telemetries),
                selectinload(RentalModel.geofence_events).joinedload(GeofenceEventModel.geofence),
                selectinload(RentalModel.violations),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_rental_car(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel | None:
        rental = await DriverService.get_rental(rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental.car

    @staticmethod
    async def get_rental_telemetry(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> TelemetryModel | None:
        await DriverService._require_driver_company(user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.driver_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        result = await session.execute(
            select(TelemetryModel)
            .where(TelemetryModel.rental_id == rental_id)
            .options(joinedload(TelemetryModel.car), joinedload(TelemetryModel.user), joinedload(TelemetryModel.rental))
            .order_by(TelemetryModel.recorded_at.desc())
            .limit(1)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_rental_violations(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await DriverService._require_driver_company(user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.driver_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        result = await session.execute(
            select(ViolationModel)
            .where(ViolationModel.rental_id == rental_id)
            .options(joinedload(ViolationModel.geofence_event).joinedload(GeofenceEventModel.geofence))
            .order_by(ViolationModel.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental_geofence_events(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await DriverService._require_driver_company(user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.driver_id == user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        result = await session.execute(
            select(GeofenceEventModel)
            .where(GeofenceEventModel.rental_id == rental_id)
            .options(joinedload(GeofenceEventModel.geofence))
            .order_by(GeofenceEventModel.triggered_at.desc())
        )
        return result.unique().scalars().all()
