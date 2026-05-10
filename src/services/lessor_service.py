"""
Сервис для всех операций Lessor компании.
Все методы принимают company_id явно и проверяют принадлежность пользователя к компании.
"""
import asyncio
import io
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Sequence, Any

from fastapi import HTTPException
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.api.schemas.car_schema import CarRequest, CarUpdate, CarStatusRequest
from src.api.schemas.geofence_schema import GeofenceRequest, GeofenceUpdate
from src.api.schemas.iot_device_schema import IotDeviceRequest, IotDeviceUpdate
from src.clients.minio_client import minio_client
from src.models import (
    CarModel,
    UserModel,
    CompanyModel,
    CompanyUserModel,
    IotDeviceModel,
    GeofenceModel,
    RentalRequestModel,
    RentalModel,
    PaymentModel,
    GeofenceEventModel,
    ViolationModel,
    TelemetryModel,
    RentalDocumentsModel,
)
from src.models.enums import (
    CompanyType,
    CompanyRole,
    CarStatus,
    RentalStatus,
    RentalRequestStatus,
    RentalDocumentType,
)


class LessorService:

    # ─────────────────────── Helpers ────────────────────────────────────────

    @staticmethod
    async def _verify_company_access(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CompanyModel:
        """Убедиться что пользователь принадлежит этой LESSOR компании."""
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyModel.id == company_id,
                CompanyModel.type == CompanyType.LESSOR,
                CompanyUserModel.user_id == user.id,
                CompanyUserModel.is_active == True,
            )
        )
        result = await session.execute(stmt)
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=403, detail="Access denied to this company")
        return company

    @staticmethod
    async def _start_simulator_for_iot(
            iot: IotDeviceModel,
            session: AsyncSession,
    ) -> None:
        """
        Запустить IoT симулятор для устройства.
        Выбирает первую активную геозону машины как центр орбиты.
        """
        from src.clients.iot_simulator import iot_simulator, DEFAULT_CENTER_LAT, DEFAULT_CENTER_LNG, DEFAULT_ZONE_RADIUS

        if not iot.device_identifier:
            return

        # Загружаем геозоны машины если не подгружены
        center_lat, center_lng, zone_radius = DEFAULT_CENTER_LAT, DEFAULT_CENTER_LNG, DEFAULT_ZONE_RADIUS

        if iot.car_id:
            result = await session.execute(
                select(GeofenceModel)
                .where(GeofenceModel.car_id == iot.car_id, GeofenceModel.is_active == True)
                .limit(1)
            )
            geofence = result.scalar_one_or_none()
            if geofence:
                center_lat = float(geofence.center_lat)
                center_lng = float(geofence.center_lng)
                zone_radius = float(geofence.radius_meters)

        iot_simulator.register(
            iot_id=iot.id,
            device_identifier=iot.device_identifier,
            center_lat=center_lat,
            center_lng=center_lng,
            zone_radius_m=zone_radius,
        )

    @staticmethod
    async def _maybe_start_simulator_for_car(car_id: uuid.UUID, session: AsyncSession) -> None:
        """Найти IoT устройство машины и запустить симулятор."""
        try:
            result = await session.execute(
                select(IotDeviceModel)
                .where(IotDeviceModel.car_id == car_id)
                .options(joinedload(IotDeviceModel.car))
            )
            iot = result.unique().scalar_one_or_none()
            if iot and iot.device_identifier:
                await LessorService._start_simulator_for_iot(iot, session)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"[IoT Sim] Failed to start simulator for car {car_id}: {exc}"
            )

    @staticmethod
    async def _maybe_stop_simulator_for_car(car_id: uuid.UUID, session: AsyncSession) -> None:
        """Найти IoT устройство машины и остановить симулятор."""
        from src.clients.iot_simulator import iot_simulator
        try:
            result = await session.execute(
                select(IotDeviceModel).where(IotDeviceModel.car_id == car_id)
            )
            iot = result.scalar_one_or_none()
            if iot:
                iot_simulator.unregister(iot.id)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"[IoT Sim] Failed to stop simulator for car {car_id}: {exc}"
            )

    @staticmethod
    async def _get_car_with_relations(car_id: uuid.UUID, session: AsyncSession) -> CarModel | None:
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

    @staticmethod
    async def _get_rental_with_relations(rental_id: uuid.UUID, session: AsyncSession) -> RentalModel | None:
        stmt = (
            select(RentalModel)
            .where(RentalModel.id == rental_id)
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
                joinedload(RentalModel.payment).joinedload(PaymentModel.payer_company),
                joinedload(RentalModel.payment).joinedload(PaymentModel.receiver_company),
                selectinload(RentalModel.rental_documents),
                selectinload(RentalModel.telemetries),
                selectinload(RentalModel.geofence_events).joinedload(GeofenceEventModel.geofence),
                selectinload(RentalModel.violations),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    # ─────────────────────── Cars ───────────────────────────────────────────

    @staticmethod
    async def get_cars(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

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
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_car(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(CarModel)
            .where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
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
            company_id: uuid.UUID,
            data: CarRequest,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        await LessorService._verify_company_access(company_id, user, session)

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
        return await LessorService._get_car_with_relations(car.id, session)

    @staticmethod
    async def update_car(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            data: CarUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        # Нельзя редактировать если в аренде
        if car.status == CarStatus.RENTED:
            raise HTTPException(status_code=400, detail="Cannot edit car that is currently rented")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(car, field, value)

        await session.commit()
        await session.refresh(car)
        return await LessorService._get_car_with_relations(car.id, session)

    @staticmethod
    async def delete_car(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> bool:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            return False

        # Нельзя удалить если в аренде
        if car.status == CarStatus.RENTED:
            raise HTTPException(status_code=400, detail="Cannot delete car that is currently rented")

        # Останавливаем симулятор IoT для этой машины перед удалением
        iot_result = await session.execute(
            select(IotDeviceModel).where(IotDeviceModel.car_id == car_id)
        )
        iot = iot_result.scalar_one_or_none()
        if iot:
            from src.clients.iot_simulator import iot_simulator
            iot_simulator.unregister(iot.id)
            # car_id обнулится автоматически через SET NULL (ondelete)

        await session.execute(delete(CarModel).where(CarModel.id == car_id))
        await session.commit()
        return True

    @staticmethod
    async def update_car_status(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            data: CarStatusRequest,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        car.status = data.status
        await session.commit()
        await session.refresh(car)
        return car

    @staticmethod
    async def attach_iot_to_car(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            iot_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

        result = await session.execute(
            select(IotDeviceModel).where(IotDeviceModel.id == iot_id)
        )
        iot = result.scalar_one_or_none()
        if not iot:
            raise HTTPException(status_code=404, detail="IoT device not found")

        if iot.car_id and iot.car_id != car_id:
            raise HTTPException(status_code=400, detail="IoT device already attached to another car")

        iot.car_id = car_id
        await session.commit()

        # Запускаем симулятор после привязки (если есть identifier)
        if iot.device_identifier:
            # Перезагружаем iot чтобы получить car.geofences
            result = await session.execute(
                select(IotDeviceModel)
                .where(IotDeviceModel.id == iot_id)
                .options(joinedload(IotDeviceModel.car))
            )
            iot_fresh = result.unique().scalar_one_or_none()
            if iot_fresh:
                await LessorService._start_simulator_for_iot(iot_fresh, session)

        return await LessorService._get_car_with_relations(car_id, session)

    @staticmethod
    async def get_car_iot(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Car not found")

        result = await session.execute(
            select(IotDeviceModel)
            .where(IotDeviceModel.car_id == car_id)
            .options(joinedload(IotDeviceModel.car))
        )
        return result.unique().scalar_one_or_none()

    # ─────────────────────── IoT Devices ─────────────────────────────────────

    @staticmethod
    async def get_iots(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(IotDeviceModel)
            .join(CarModel, IotDeviceModel.car_id == CarModel.id, isouter=True)
            .where(
                or_(
                    CarModel.owner_company_id == company_id,
                    IotDeviceModel.car_id.is_(None)
                )
            )
            .options(joinedload(IotDeviceModel.car))
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_iot(
            company_id: uuid.UUID,
            iot_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(IotDeviceModel)
            .where(IotDeviceModel.id == iot_id)
            .options(joinedload(IotDeviceModel.car))
        )
        iot = result.unique().scalar_one_or_none()
        if not iot:
            return None
        # Проверяем принадлежность — либо привязан к машине компании, либо без привязки
        if iot.car_id:
            car_res = await session.execute(
                select(CarModel).where(CarModel.id == iot.car_id, CarModel.owner_company_id == company_id)
            )
            if not car_res.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Access denied")
        return iot

    @staticmethod
    async def add_iot(
            company_id: uuid.UUID,
            data: IotDeviceRequest,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel:
        await LessorService._verify_company_access(company_id, user, session)

        iot = IotDeviceModel(
            device_identifier=data.device_identifier,
            sim_number=data.sim_number,
            battery_level=data.battery_level,
            is_online=data.is_online,
            car_id=data.car_id,
        )
        session.add(iot)
        await session.commit()

        # Перезагружаем с joinedload чтобы избежать lazy='raise'
        result = await session.execute(
            select(IotDeviceModel)
            .where(IotDeviceModel.id == iot.id)
            .options(joinedload(IotDeviceModel.car))
        )
        iot = result.unique().scalar_one()

        # Запускаем симулятор только если устройство привязано к машине
        # и device_identifier задан
        if iot.device_identifier and iot.car_id:
            await LessorService._start_simulator_for_iot(iot, session)

        return iot

    @staticmethod
    async def update_iot(
            company_id: uuid.UUID,
            iot_id: uuid.UUID,
            data: IotDeviceUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> IotDeviceModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(IotDeviceModel).where(IotDeviceModel.id == iot_id)
        )
        iot = result.scalar_one_or_none()
        if not iot:
            raise HTTPException(status_code=404, detail="IoT device not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(iot, field, value)

        await session.commit()
        await session.refresh(iot)
        return iot

    @staticmethod
    async def delete_iot(
            company_id: uuid.UUID,
            iot_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(IotDeviceModel)
            .where(IotDeviceModel.id == iot_id)
            .options(joinedload(IotDeviceModel.car))
        )
        iot = result.unique().scalar_one_or_none()
        if not iot:
            raise HTTPException(status_code=404, detail="IoT device not found")

        if iot.car_id:
            car_res = await session.execute(
                select(CarModel).where(CarModel.id == iot.car_id)
            )
            car = car_res.scalar_one_or_none()
            if car and car.status != CarStatus.HIDDEN:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete IoT device: car must be HIDDEN first"
                )

        # Останавливаем симулятор перед удалением
        from src.clients.iot_simulator import iot_simulator
        iot_simulator.unregister(iot.id)

        await session.delete(iot)
        await session.commit()

    # ─────────────────────── Geofences ──────────────────────────────────────

    @staticmethod
    async def get_car_geofences(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Car not found")

        result = await session.execute(
            select(GeofenceModel)
            .where(GeofenceModel.car_id == car_id)
            .options(joinedload(GeofenceModel.car))
        )
        return result.unique().scalars().all()

    @staticmethod
    async def create_geofence(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            data: GeofenceRequest,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id, CarModel.owner_company_id == company_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Car not found")

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

        # Перезагружаем с joinedload чтобы избежать lazy='raise'
        result = await session.execute(
            select(GeofenceModel)
            .where(GeofenceModel.id == geofence.id)
            .options(joinedload(GeofenceModel.car))
        )
        return result.unique().scalar_one()

    @staticmethod
    async def get_all_geofences(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(CarModel.owner_company_id == company_id)
            .options(joinedload(GeofenceModel.car))
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_geofence(
            company_id: uuid.UUID,
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
            .options(joinedload(GeofenceModel.car))
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def update_geofence(
            company_id: uuid.UUID,
            geofence_id: uuid.UUID,
            data: GeofenceUpdate,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        geofence = result.unique().scalar_one_or_none()
        if not geofence:
            raise HTTPException(status_code=404, detail="Geofence not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(geofence, field, value)

        await session.commit()
        await session.refresh(geofence)
        return geofence

    @staticmethod
    async def toggle_geofence(
            company_id: uuid.UUID,
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> GeofenceModel:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        geofence = result.unique().scalar_one_or_none()
        if not geofence:
            raise HTTPException(status_code=404, detail="Geofence not found")

        geofence.is_active = not geofence.is_active
        await session.commit()
        await session.refresh(geofence)
        return geofence

    @staticmethod
    async def delete_geofence(
            company_id: uuid.UUID,
            geofence_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(GeofenceModel)
            .join(CarModel, GeofenceModel.car_id == CarModel.id)
            .where(
                GeofenceModel.id == geofence_id,
                CarModel.owner_company_id == company_id
            )
        )
        geofence = result.unique().scalar_one_or_none()
        if not geofence:
            raise HTTPException(status_code=404, detail="Geofence not found")

        await session.delete(geofence)
        await session.commit()

    # ─────────────────────── Rental Requests ────────────────────────────────

    @staticmethod
    async def get_incoming_requests(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            status: RentalRequestStatus | None = None,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(CarModel.owner_company_id == company_id)
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )
        if status:
            stmt = stmt.where(RentalRequestModel.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(RentalRequestModel.created_at.desc())
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def approve_request(
            company_id: uuid.UUID,
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(
                RentalRequestModel.id == request_id,
                CarModel.owner_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING,
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
            raise HTTPException(status_code=404, detail="Request not found or already processed")

        if request.car.status != CarStatus.AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail=f"Car is not available. Status: {request.car.status.value}"
            )

        days = (request.end_date - request.start_date).days
        if days <= 0:
            days = 1
        base_price_total = request.car.price_per_day * Decimal(days)

        rental = RentalModel(
            request_id=request.id,
            lessor_company_id=company_id,
            renter_company_id=request.renter_company_id,
            car_id=request.car_id,
            driver_id=request.driver_id,
            start_date=request.start_date,
            end_date=request.end_date,
            base_price_total=base_price_total,
            extra_days_fee=Decimal("0.00"),
            status=RentalStatus.ACTIVE,
            is_paid=False,
        )
        session.add(rental)
        request.status = RentalRequestStatus.APPROVED
        request.car.status = CarStatus.RENTED

        await session.commit()
        await session.refresh(rental)

        rental_with_relations = await LessorService._get_rental_with_relations(rental.id, session)

        from src.services.contract_service import ContractService
        asyncio.create_task(
            ContractService.generate_and_upload_contract(str(rental.id))
        )

        # Запускаем симулятор IoT для машины этой аренды
        asyncio.create_task(
            LessorService._maybe_start_simulator_for_car(request.car_id, session)
        )

        return rental_with_relations

    @staticmethod
    async def reject_request(
            company_id: uuid.UUID,
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalRequestModel:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .join(CarModel, RentalRequestModel.car_id == CarModel.id)
            .where(
                RentalRequestModel.id == request_id,
                CarModel.owner_company_id == company_id,
                RentalRequestModel.status == RentalRequestStatus.PENDING,
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
            raise HTTPException(status_code=404, detail="Request not found or already processed")

        request.status = RentalRequestStatus.REJECTED
        await session.commit()
        await session.refresh(request)
        return request

    # ─────────────────────── Rentals ────────────────────────────────────────

    @staticmethod
    async def get_rentals(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            status: RentalStatus | None = None,
            payment_status_pending: bool = False,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalModel)
            .where(RentalModel.lessor_company_id == company_id)
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
                joinedload(RentalModel.payment).joinedload(PaymentModel.payer_company),
                joinedload(RentalModel.payment).joinedload(PaymentModel.receiver_company),
                selectinload(RentalModel.rental_documents),
                selectinload(RentalModel.telemetries),
                selectinload(RentalModel.geofence_events).joinedload(GeofenceEventModel.geofence),
                selectinload(RentalModel.violations),
            )
        )

        if status:
            stmt = stmt.where(RentalModel.status == status)

        if payment_status_pending:
            stmt = stmt.where(
                RentalModel.status == RentalStatus.COMPLETED,
                RentalModel.is_paid == False
            )

        stmt = stmt.offset(skip).limit(limit).order_by(RentalModel.created_at.desc())
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalModel)
            .where(RentalModel.id == rental_id, RentalModel.lessor_company_id == company_id)
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
                joinedload(RentalModel.payment).joinedload(PaymentModel.payer_company),
                joinedload(RentalModel.payment).joinedload(PaymentModel.receiver_company),
                selectinload(RentalModel.rental_documents),
                selectinload(RentalModel.telemetries),
                selectinload(RentalModel.geofence_events).joinedload(GeofenceEventModel.geofence),
                selectinload(RentalModel.violations),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_rental_driver(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> UserModel | None:
        rental = await LessorService.get_rental(company_id, rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental.user

    @staticmethod
    async def get_rental_car(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel | None:
        rental = await LessorService.get_rental(company_id, rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental.car

    @staticmethod
    async def get_rental_payment(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> PaymentModel | None:
        rental = await LessorService.get_rental(company_id, rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental.payment

    @staticmethod
    async def get_rental_telemetry(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> TelemetryModel | None:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id
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
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        stmt = (
            select(ViolationModel)
            .where(ViolationModel.rental_id == rental_id)
            .options(joinedload(ViolationModel.geofence_event).joinedload(GeofenceEventModel.geofence))
            .order_by(ViolationModel.created_at.desc())
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental_documents(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        result = await session.execute(
            select(RentalDocumentsModel)
            .where(RentalDocumentsModel.rental_id == rental_id)
            .order_by(RentalDocumentsModel.generated_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def download_document(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            document_type: RentalDocumentType,
            user: UserModel,
            session: AsyncSession
    ) -> tuple[bytes, str, str]:
        await LessorService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Rental not found")

        result = await session.execute(
            select(RentalDocumentsModel)
            .where(
                RentalDocumentsModel.rental_id == rental_id,
                RentalDocumentsModel.type == document_type
            )
            .order_by(RentalDocumentsModel.generated_at.desc())
            .limit(1)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document '{document_type.value}' not found")

        try:
            response = minio_client.client.get_object(
                bucket_name=minio_client.bucket_name,
                object_name=doc.file_path
            )
            file_data = response.read()
            response.close()
            response.release_conn()
            filename = f"{document_type.value}_{rental_id}_{doc.generated_at.strftime('%Y%m%d')}.pdf"
            return file_data, filename, "application/pdf"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error downloading file: {e}")

    @staticmethod
    async def complete_rental(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalModel)
            .where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
            .options(
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
            )
        )
        result = await session.execute(stmt)
        rental = result.unique().scalar_one_or_none()
        if not rental:
            raise HTTPException(status_code=404, detail="Active rental not found")

        now = datetime.now(timezone.utc)
        rental.actual_return_date = now
        price_per_day = rental.car.price_per_day

        if now < rental.end_date:
            days = (now - rental.start_date).days
            if days <= 0:
                days = 1
            rental.base_price_total = price_per_day * Decimal(str(days))
            rental.extra_days_fee = Decimal("0.00")
        elif now > rental.end_date:
            extra_days = (now - rental.end_date).days
            if extra_days > 0:
                rental.extra_days_fee = price_per_day * Decimal(str(extra_days))
        else:
            rental.extra_days_fee = Decimal("0.00")

        rental.status = RentalStatus.COMPLETED
        rental.car.status = CarStatus.AVAILABLE

        await session.commit()
        await session.refresh(rental)

        rental_with_relations = await LessorService._get_rental_with_relations(rental.id, session)

        from src.services.contract_service import ContractService
        asyncio.create_task(
            ContractService.generate_and_upload_act(str(rental.id), "lessor")
        )
        asyncio.create_task(
            ContractService.generate_and_upload_invoice(str(rental.id))
        )

        # Останавливаем симулятор IoT для машины этой аренды
        asyncio.create_task(
            LessorService._maybe_stop_simulator_for_car(rental.car_id, session)
        )

        return rental_with_relations

    # ─────────────────────── Finances ───────────────────────────────────────

    @staticmethod
    async def get_finances(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> dict:
        company = await LessorService._verify_company_access(company_id, user, session)

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
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        payments = result.unique().scalars().all()

        return {"balance": company.balance, "payments": payments}

    # ─────────────────────── Employers ──────────────────────────────────────

    @staticmethod
    async def get_employers(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await LessorService._verify_company_access(company_id, user, session)

        stmt = (
            select(CompanyUserModel)
            .where(CompanyUserModel.company_id == company_id)
            .options(joinedload(CompanyUserModel.user))
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def add_employer(
            company_id: uuid.UUID,
            user_email: str,
            current_user: UserModel,
            session: AsyncSession
    ) -> CompanyUserModel:
        from src.services.company_service import CompanyService
        return await CompanyService.add_owner_to_company(
            company_id, user_email, current_user, CompanyType.LESSOR, session
        )

    # ─────────────────────── Company Profile ────────────────────────────────

    @staticmethod
    async def get_company_profile(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CompanyModel:
        return await LessorService._verify_company_access(company_id, user, session)
