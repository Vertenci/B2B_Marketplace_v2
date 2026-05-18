import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.clients.minio_client import minio_client
from src.models import (
    RentalModel,
    UserModel,
    CompanyUserModel,
    CompanyModel,
    GeofenceEventModel,
    PaymentModel, ViolationModel, TelemetryModel, RentalDocumentsModel,
)
from src.models.enums import RentalStatus, CompanyType, CarStatus, RentalDocumentType


class RentalService:
    @staticmethod
    async def get_rentals(
        session: AsyncSession,
        user: UserModel,
        status: RentalStatus | None = None,
        skip: int = 0,
        limit: int = 10
    ) -> Sequence[Any]:
        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view rentals")

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
                selectinload(RentalModel.violations)
                .joinedload(ViolationModel.geofence_event)
                .joinedload(GeofenceEventModel.geofence),
            )
        )

        if status:
            stmt = stmt.where(RentalModel.status == status)

        stmt = stmt.offset(skip).limit(limit).order_by(RentalModel.created_at.desc())

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental_telemetry(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> TelemetryModel | None:
        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view telemetry")

        rental_stmt = select(RentalModel).where(
            RentalModel.id == rental_id,
            RentalModel.lessor_company_id == company_id
        )
        result = await session.execute(rental_stmt)
        rental = result.scalars().first()

        if not rental:
            raise ValueError("Rental not found or access denied")

        stmt = (
            select(TelemetryModel)
            .where(TelemetryModel.rental_id == rental_id)
            .options(
                joinedload(TelemetryModel.car),
                joinedload(TelemetryModel.user),
                joinedload(TelemetryModel.rental),
            )
            .order_by(TelemetryModel.recorded_at.desc())
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_rental_violations(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession,
            skip: int = 0,
            limit: int = 10
    ) -> Sequence[Any]:
        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view violations")

        rental_stmt = select(RentalModel).where(
            RentalModel.id == rental_id,
            RentalModel.lessor_company_id == company_id
        )
        result = await session.execute(rental_stmt)
        rental = result.scalars().first()

        if not rental:
            raise ValueError("Rental not found or access denied")

        stmt = (
            select(ViolationModel)
            .where(ViolationModel.rental_id == rental_id)
            .options(
                joinedload(ViolationModel.geofence_event).joinedload(GeofenceEventModel.geofence),
            )
            .order_by(ViolationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.unique().scalars().all()

    @staticmethod
    async def get_rental_by_id(
        rental_id: uuid.UUID,
        user: UserModel,
        session: AsyncSession
    ) -> RentalModel | None:
        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can view rentals")

        stmt = (
            select(RentalModel)
            .where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id
            )
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
    async def complete_rental(
            rental_id: uuid.UUID,
            user: UserModel,
            session: AsyncSession
    ) -> RentalModel:

        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can complete rentals")

        stmt = (
            select(RentalModel)
            .where(
                RentalModel.id == rental_id,
                RentalModel.lessor_company_id == company_id,
                RentalModel.status == RentalStatus.ACTIVE
            )
            .options(
                joinedload(RentalModel.rental_request),
                joinedload(RentalModel.lessor_company),
                joinedload(RentalModel.renter_company),
                joinedload(RentalModel.car),
                joinedload(RentalModel.user),
            )
        )
        result = await session.execute(stmt)
        rental = result.unique().scalar_one_or_none()

        if not rental:
            raise ValueError("Active rental not found or access denied")

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

        rental_with_relations = await RentalService._get_rental_by_id(rental.id, session)

        from src.services.contract_service import ContractService
        asyncio.create_task(
            ContractService.generate_and_upload_act(str(rental.id), "lessor")
        )
        asyncio.create_task(
            ContractService.generate_and_upload_invoice(str(rental.id))
        )

        return rental_with_relations


    @staticmethod
    async def download_document(
            rental_id: uuid.UUID,
            document_type: RentalDocumentType,
            user: UserModel,
            session: AsyncSession
    ) -> tuple[bytes, str, str]:
        company_id = await RentalService._get_company_id_for_user(user, session)

        company_stmt = select(CompanyModel).where(CompanyModel.id == company_id)
        result = await session.execute(company_stmt)
        company = result.scalars().first()

        if not company or company.type != CompanyType.LESSOR:
            raise ValueError("Only lessor companies can download documents")

        rental_stmt = select(RentalModel).where(
            RentalModel.id == rental_id,
            RentalModel.lessor_company_id == company_id
        )
        result = await session.execute(rental_stmt)
        rental = result.scalars().first()

        if not rental:
            raise ValueError("Rental not found or access denied")

        stmt = (
            select(RentalDocumentsModel)
            .where(
                RentalDocumentsModel.rental_id == rental_id,
                RentalDocumentsModel.type == document_type
            )
            .order_by(RentalDocumentsModel.generated_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        document = result.scalars().first()

        if not document:
            raise ValueError(f"Document type '{document_type.value}' not found for this rental")
        try:
            response = minio_client.client.get_object(
                bucket_name=minio_client.bucket_name,
                object_name=document.file_path
            )
            file_data = response.read()
            response.close()
            response.release_conn()

            filename = f"{document_type.value}_{rental_id}_{document.generated_at.strftime('%Y%m%d')}.pdf"

            return file_data, filename, "application/pdf"

        except Exception as e:
            raise ValueError(f"Error downloading file: {e}")
