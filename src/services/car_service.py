import uuid
from typing import Sequence, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.api.schemas.car_schema import CarRequest, CarUpdate, CarStatusRequest
from src.models import CarModel, UserModel, CompanyUserModel, RentalRequestModel, RentalModel


class CarService:
    @staticmethod
    async def get_cars(
            session: AsyncSession,
            user: UserModel,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        company_id = await CarService._get_company_id_for_user(user, session)

        stmt = (
            select(CarModel)
            .where(CarModel.owner_company_id == company_id)
            .options(
                joinedload(CarModel.company),
                joinedload(CarModel.iot_device),
                selectinload(CarModel.geofences),
                selectinload(CarModel.rental_requests).joinedload(RentalRequestModel.user),
                selectinload(CarModel.rentals).joinedload(RentalModel.lessor_company),
                selectinload(CarModel.rentals).joinedload(RentalModel.renter_company),
                selectinload(CarModel.telemetries),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_car(
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel | None:
        company_id = await CarService._get_company_id_for_user(user, session)

        stmt = (
            select(CarModel)
            .where(
                CarModel.id == car_id,
                CarModel.owner_company_id == company_id
            )
            .options(
                joinedload(CarModel.company),
                joinedload(CarModel.iot_device),
                selectinload(CarModel.geofences),
                selectinload(CarModel.rental_requests).joinedload(RentalRequestModel.user),
                selectinload(CarModel.rentals).joinedload(RentalModel.lessor_company),
                selectinload(CarModel.rentals).joinedload(RentalModel.renter_company),
                selectinload(CarModel.telemetries),
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def add_car(
            data: CarRequest,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        company_id = await CarService._get_company_id_for_user(user, session)

        car = CarModel(
            owner_company_id=company_id,
            brand=data.brand,
            model=data.model,
            year=data.year,
            plate_number=data.plate_number,
            vin=data.vin,
            price_per_day=data.price_per_day,
            status=data.status,
        )

        session.add(car)
        await session.commit()
        await session.refresh(car)
        return await CarService._get_car_by_id(car.id, session)

    @staticmethod
    async def update_car(
            car_id: uuid.UUID,
            data: CarUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        company_id = await CarService._get_company_id_for_user(user, session)

        stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(stmt)
        car = result.scalars().first()

        if not car:
            raise ValueError(f"Car with id {car_id} not found or access denied")

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(car, field, value)

        await session.commit()
        await session.refresh(car)

        return await CarService._get_car_by_id(car.id, session)

    @staticmethod
    async def update_car_status(
            car_id: uuid.UUID,
            data: CarStatusRequest,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        company_id = await CarService._get_company_id_for_user(user, session)

        stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(stmt)
        car = result.scalars().first()

        if not car:
            raise ValueError(f"Car with id {car_id} not found or access denied")

        car.status = data.status

        await session.commit()
        await session.refresh(car)

        return car

    @staticmethod
    async def delete_car(
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> bool:
        company_id = await CarService._get_company_id_for_user(user, session)

        check_stmt = select(CarModel).where(
            CarModel.id == car_id,
            CarModel.owner_company_id == company_id
        )
        result = await session.execute(check_stmt)
        car = result.unique().scalar_one_or_none()

        if not car:
            return False

        delete_stmt = delete(CarModel).where(CarModel.id == car_id)
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
    async def _get_car_by_id(
            car_id: uuid.UUID,
            session: AsyncSession
    ) -> CarModel:
        stmt = (
            select(CarModel)
            .where(CarModel.id == car_id)
            .options(
                joinedload(CarModel.company),
                joinedload(CarModel.iot_device),
                selectinload(CarModel.geofences),
                selectinload(CarModel.rental_requests).joinedload(RentalRequestModel.user),
                selectinload(CarModel.rentals).joinedload(RentalModel.lessor_company),
                selectinload(CarModel.rentals).joinedload(RentalModel.renter_company),
                selectinload(CarModel.telemetries),
            )
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()
