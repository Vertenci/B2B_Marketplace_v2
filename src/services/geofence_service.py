import uuid
from typing import Sequence, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.api.schemas.geofence_schema import GeofenceRequest, GeofenceUpdate
from src.models import GeofenceModel, CarModel, UserModel, CompanyUserModel


class GeofenceService:
    @staticmethod
    async def get_geofences(
            session: AsyncSession,
            user: UserModel,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(CarModel.owner_company_id == company_id)
            .options(
                joinedload(GeofenceModel.car)
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_geofence(
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel | None:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
            .options(
                joinedload(GeofenceModel.car)
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_car_geofences(
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        car_stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(car_stmt)
        car = result.scalars().first()

        if not car:
            raise ValueError("Car not found or access denied")

        stmt = (
            select(GeofenceModel)
            .where(GeofenceModel.car_id == car_id)
            .options(
                joinedload(GeofenceModel.car)
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def create_geofence(
            car_id: uuid.UUID,
            data: GeofenceRequest,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(stmt)
        car = result.scalars().first()

        if not car:
            raise ValueError("Car not found or access denied")

        geofence = GeofenceModel(
            car_id=car_id,
            name=data.name,
            center_lat=data.center_lat,
            center_lng=data.center_lng,
            radius_meters=data.radius_meters,
            is_active=data.is_active,
        )

        session.add(geofence)
        await session.commit()
        await session.refresh(geofence)

        return await GeofenceService._get_geofence_by_id(geofence.id, session)

    @staticmethod
    async def update_geofence(
            geofence_id: uuid.UUID,
            data: GeofenceUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        result = await session.execute(stmt)
        geofence = result.scalars().first()

        if not geofence:
            raise ValueError("Geofence not found or access denied")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(geofence, field, value)

        await session.commit()
        await session.refresh(geofence)

        return await GeofenceService._get_geofence_by_id(geofence.id, session)

    @staticmethod
    async def toggle_geofence(
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        result = await session.execute(stmt)
        geofence = result.scalars().first()

        if not geofence:
            raise ValueError("Geofence not found or access denied")

        geofence.is_active = not geofence.is_active

        await session.commit()
        await session.refresh(geofence)

        return geofence

    @staticmethod
    async def delete_geofence(
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> bool:
        company_id = await GeofenceService._get_company_id_for_user(user, session)

        check_stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        result = await session.execute(check_stmt)
        geofence = result.scalars().first()

        if not geofence:
            return False

        delete_stmt = delete(GeofenceModel).where(GeofenceModel.id == geofence_id)
        await session.execute(delete_stmt)
        await session.commit()

        return True

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

    @staticmethod
    async def _get_geofence_by_id(
            geofence_id: uuid.UUID,
            session: AsyncSession
    ) -> GeofenceModel | None:
        stmt = (
            select(GeofenceModel)
            .where(GeofenceModel.id == geofence_id)
            .options(
                joinedload(GeofenceModel.car)
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()
