"""
Сервис для всех операций Renter компании.
"""
import io
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence, Any

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.clients.minio_client import minio_client
from src.models import (
    CarModel,
    UserModel,
    CompanyModel,
    CompanyUserModel,
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
    PaymentStatus,
    PaymentType,
    RentalDocumentType,
)


class RenterService:

    @staticmethod
    async def _verify_company_access(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CompanyModel:
        stmt = (
            select(CompanyModel)
            .join(CompanyUserModel, CompanyModel.id == CompanyUserModel.company_id)
            .where(
                CompanyModel.id == company_id,
                CompanyModel.type == CompanyType.RENTER,
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

    # ─────────────────────── Drivers ────────────────────────────────────────

    @staticmethod
    async def get_drivers(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(CompanyUserModel)
            .where(
                CompanyUserModel.company_id == company_id,
                CompanyUserModel.position == CompanyRole.DRIVER,
            )
            .options(joinedload(CompanyUserModel.user))
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def add_driver(
            company_id: uuid.UUID,
            driver_email: str,
            user: UserModel,
            session: AsyncSession
    ) -> CompanyUserModel:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(UserModel).where(UserModel.email == driver_email.strip().lower())
        )
        driver_user = result.scalar_one_or_none()
        if not driver_user:
            raise HTTPException(status_code=404, detail="User not found")

        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.user_id == driver_user.id,
                CompanyUserModel.company_id == company_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.is_active:
                raise HTTPException(status_code=400, detail="User is already in this company")
            existing.is_active = True
            existing.position = CompanyRole.DRIVER
            await session.commit()
            await session.refresh(existing)
            return existing

        company_user = CompanyUserModel(
            user_id=driver_user.id,
            company_id=company_id,
            position=CompanyRole.DRIVER,
            is_active=True
        )
        session.add(company_user)
        await session.commit()
        await session.refresh(company_user)
        return company_user

    @staticmethod
    async def remove_driver(
            company_id: uuid.UUID,
            driver_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> None:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.id == driver_id,
                CompanyUserModel.company_id == company_id,
                CompanyUserModel.position == CompanyRole.DRIVER,
            )
        )
        cu = result.scalar_one_or_none()
        if not cu:
            raise HTTPException(status_code=404, detail="Driver not found in this company")

        await session.delete(cu)
        await session.commit()

    @staticmethod
    async def toggle_driver(
            company_id: uuid.UUID,
            driver_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CompanyUserModel:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.id == driver_id,
                CompanyUserModel.company_id == company_id,
                CompanyUserModel.position == CompanyRole.DRIVER,
            )
        )
        cu = result.scalar_one_or_none()
        if not cu:
            raise HTTPException(status_code=404, detail="Driver not found")

        cu.is_active = not cu.is_active
        await session.commit()
        await session.refresh(cu)
        return cu

    # ─────────────────────── Car Search ─────────────────────────────────────

    @staticmethod
    async def search_cars(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            brand: str | None = None,
            model: str | None = None,
            year: str | None = None,
            min_price: Decimal | None = None,
            max_price: Decimal | None = None,
            status: CarStatus | None = None,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(CarModel)
            .where(CarModel.status == CarStatus.AVAILABLE)
            .options(
                joinedload(CarModel.company),
                joinedload(CarModel.iot_device),
                selectinload(CarModel.geofences),
            )
        )

        if brand:
            stmt = stmt.where(CarModel.brand.ilike(f"%{brand}%"))
        if model:
            stmt = stmt.where(CarModel.model.ilike(f"%{model}%"))
        if year:
            stmt = stmt.where(CarModel.year == year)
        if min_price is not None:
            stmt = stmt.where(CarModel.price_per_day >= min_price)
        if max_price is not None:
            stmt = stmt.where(CarModel.price_per_day <= max_price)
        if status:
            stmt = stmt.where(CarModel.status == status)

        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_car_detail(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> CarModel | None:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(CarModel)
            .where(CarModel.id == car_id)
            .options(
                joinedload(CarModel.company),
                joinedload(CarModel.iot_device),
                selectinload(CarModel.geofences),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    # ─────────────────────── Rental Requests ────────────────────────────────

    @staticmethod
    async def get_requests(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .where(RentalRequestModel.renter_company_id == company_id)
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
            .order_by(RentalRequestModel.created_at.desc())
            .offset(skip).limit(limit)
        )
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def create_request(
            company_id: uuid.UUID,
            car_id: uuid.UUID,
            driver_id: uuid.UUID,
            start_date,
            end_date,
            message: str | None,
            user: UserModel,
            session: AsyncSession
    ) -> RentalRequestModel:
        await RenterService._verify_company_access(company_id, user, session)

        # Проверяем что машина доступна
        result = await session.execute(
            select(CarModel).where(CarModel.id == car_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        if car.status != CarStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=f"Car is not available. Status: {car.status.value}")

        # Проверяем что водитель принадлежит renter компании
        result = await session.execute(
            select(CompanyUserModel).where(
                CompanyUserModel.user_id == driver_id,
                CompanyUserModel.company_id == company_id,
                CompanyUserModel.position == CompanyRole.DRIVER,
                CompanyUserModel.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Driver not found in this company")

        request = RentalRequestModel(
            renter_company_id=company_id,
            car_id=car_id,
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date,
            message=message,
            status=RentalRequestStatus.PENDING,
        )
        session.add(request)
        await session.commit()
        await session.refresh(request)

        # Перезагрузить с relations
        stmt = (
            select(RentalRequestModel)
            .where(RentalRequestModel.id == request.id)
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one()

    @staticmethod
    async def get_request(
            company_id: uuid.UUID,
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalRequestModel | None:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .where(
                RentalRequestModel.id == request_id,
                RentalRequestModel.renter_company_id == company_id
            )
            .options(
                joinedload(RentalRequestModel.car),
                joinedload(RentalRequestModel.company),
                joinedload(RentalRequestModel.user),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def cancel_request(
            company_id: uuid.UUID,
            request_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalRequestModel:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalRequestModel)
            .where(
                RentalRequestModel.id == request_id,
                RentalRequestModel.renter_company_id == company_id,
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
            raise HTTPException(status_code=404, detail="Request not found or cannot be cancelled")

        request.status = RentalRequestStatus.CANCELLED
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
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalModel)
            .where(RentalModel.renter_company_id == company_id)
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
        await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(RentalModel)
            .where(RentalModel.id == rental_id, RentalModel.renter_company_id == company_id)
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
    async def get_rental_telemetry(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> TelemetryModel | None:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id
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
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id
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
    async def get_rental_payment(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> PaymentModel | None:
        rental = await RenterService.get_rental(company_id, rental_id, user, session)
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        return rental.payment

    @staticmethod
    async def get_rental_geofence_events(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id
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

    @staticmethod
    async def pay_rental(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> PaymentModel:
        company = await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel)
            .where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id,
                RentalModel.status == RentalStatus.COMPLETED,
                RentalModel.is_paid == False,
            )
            .options(joinedload(RentalModel.car), joinedload(RentalModel.lessor_company))
        )
        rental = result.unique().scalar_one_or_none()
        if not rental:
            raise HTTPException(status_code=404, detail="Completed unpaid rental not found")

        total_amount = rental.base_price_total + rental.extra_days_fee
        commission_rate = Decimal("0.05")  # 5% комиссия платформы
        commission_amount = total_amount * commission_rate

        if company.balance < total_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        now = datetime.now(timezone.utc)
        payment = PaymentModel(
            rental_id=rental_id,
            payer_company_id=company_id,
            receiver_company_id=rental.lessor_company_id,
            amount=total_amount,
            commission_amount=commission_amount,
            status=PaymentStatus.PAID,
            payment_method=PaymentType.BALANCE,
            paid_at=now,
        )
        session.add(payment)

        # Обновляем балансы
        company.balance -= total_amount
        rental.lessor_company.balance += (total_amount - commission_amount)
        rental.is_paid = True

        await session.commit()
        await session.refresh(payment)
        return payment

    @staticmethod
    async def get_rental_documents(
            company_id: uuid.UUID,
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> Sequence[Any]:
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id
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
        await RenterService._verify_company_access(company_id, user, session)

        result = await session.execute(
            select(RentalModel).where(
                RentalModel.id == rental_id,
                RentalModel.renter_company_id == company_id
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

    # ─────────────────────── Finances ───────────────────────────────────────

    @staticmethod
    async def get_finances(
            company_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> dict:
        company = await RenterService._verify_company_access(company_id, user, session)

        stmt = (
            select(PaymentModel)
            .where(PaymentModel.payer_company_id == company_id)
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
