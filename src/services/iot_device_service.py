import uuid
from typing import Sequence, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.api.schemas.iot_device_schema import IotDeviceRequest, IotDeviceUpdate
from src.models import IotDeviceModel, CarModel, UserModel, CompanyUserModel


class IotDeviceService:
    @staticmethod
    async def get_iots(
            session: AsyncSession,
            user: UserModel,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        company_id = await IotDeviceService.get_company_id_for_user(user, session)

        stmt = (
            select(IotDeviceModel)
            .join(CarModel, IotDeviceModel.car_id == CarModel.id)
            .where(CarModel.owner_company_id == company_id)
            .options(
                joinedload(IotDeviceModel.car)
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_iot(
            iot_id: uuid.UUID,
            session: AsyncSession,
            user: UserModel
    ) -> IotDeviceModel | None:
        company_id = await IotDeviceService.get_company_id_for_user(user, session)

        stmt = (
            select(IotDeviceModel)
            .join(CarModel, IotDeviceModel.car_id == CarModel.id)
            .where(
                IotDeviceModel.id == iot_id,
                CarModel.owner_company_id == company_id
            )
            .options(
                joinedload(IotDeviceModel.car)
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def add_iot(
            data: IotDeviceRequest,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel:
        if data.car_id:
            await IotDeviceService._check_car_ownership(data.car_id, user, session)

        iot = IotDeviceModel(
            car_id=data.car_id,
            device_identifier=data.device_identifier,
            sim_number=data.sim_number,
            battery_level=data.battery_level,
            is_online=data.is_online,
        )

        session.add(iot)
        await session.commit()
        await session.refresh(iot)

        return await IotDeviceService.get_iot(iot.id, session, user)

    @staticmethod
    async def update_iot(
            iot_id: uuid.UUID,
            data: IotDeviceUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel:
        company_id = await IotDeviceService.get_company_id_for_user(user, session)

        stmt = (
            select(IotDeviceModel)
            .join(CarModel, IotDeviceModel.car_id == CarModel.id)
            .where(
                IotDeviceModel.id == iot_id,
                CarModel.owner_company_id == company_id
            )
        )
        result = await session.execute(stmt)
        iot = result.scalars().first()

        if not iot:
            raise ValueError(f"IoT device with id {iot_id} not found")

        if data.car_id is not None and data.car_id != iot.car_id:
            await IotDeviceService._check_car_ownership(data.car_id, user, session)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(iot, field, value)

        await session.commit()
        await session.refresh(iot)

        return await IotDeviceService.get_iot(iot.id, session, user)

    @staticmethod
    async def delete_iot(
            iot_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> bool:
        company_id = await IotDeviceService.get_company_id_for_user(user, session)

        check_stmt = (
            select(IotDeviceModel)
            .join(CarModel, IotDeviceModel.car_id == CarModel.id)
            .where(
                IotDeviceModel.id == iot_id,
                CarModel.owner_company_id == company_id
            )
        )
        result = await session.execute(check_stmt)
        iot = result.scalars().first()

        if not iot:
            return False

        delete_stmt = delete(IotDeviceModel).where(IotDeviceModel.id == iot_id)
        await session.execute(delete_stmt)
        await session.commit()

        return True

    @staticmethod
    async def get_company_id_for_user(
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
    async def _check_car_ownership(
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        company_id = await IotDeviceService.get_company_id_for_user(user, session)

        stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(stmt)
        car = result.scalars().first()

        if not car:
            raise ValueError(
                "Car not found or you don't have permission to attach device to this car"
            )
