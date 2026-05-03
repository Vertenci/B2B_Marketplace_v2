import logging

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserModel
from src.models.agreement_model import AgreementModel
from src.models.document_model import DocumentModel
from src.models.enums import AgreementType

logger = logging.getLogger(__name__)


class DocumentService:
    @staticmethod
    async def get_active_document(
            session: AsyncSession,
            document_type: AgreementType
    ) -> DocumentModel | None:
        stmt = select(DocumentModel).where(
            DocumentModel.document_type == document_type,
            DocumentModel.is_active == True
        ).order_by(desc(DocumentModel.published_at))

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def accept_agreement(
            session: AsyncSession,
            user: UserModel,
            agreement_type: AgreementType,
            ip_address: str | None = None,
            user_agent: str | None = None
    ) -> AgreementModel:
        stmt = select(AgreementModel).where(
            AgreementModel.user_id == user.id,
            AgreementModel.type == agreement_type
        )
        result = await session.execute(stmt)
        existing_agreement = result.scalar_one_or_none()

        if existing_agreement:
            existing_agreement.accepted_at = func.now()
            existing_agreement.ip_address = ip_address
            existing_agreement.user_agent = user_agent
            agreement = existing_agreement
            logger.info(f"Updated {agreement_type.value} agreement for user {user.id}")
        else:
            agreement = AgreementModel(
                user_id=user.id,
                type=agreement_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            session.add(agreement)
            logger.info(f"Created {agreement_type.value} agreement for user {user.id}")

        await session.commit()
        await session.refresh(agreement)
        return agreement

    @staticmethod
    async def get_user_agreements_status(
            session: AsyncSession,
            user: UserModel
    ) -> dict:
        stmt = select(AgreementModel).where(
            AgreementModel.user_id == user.id
        )
        result = await session.execute(stmt)
        agreements = result.scalars().all()

        status = {
            "public_offer_accepted": False,
            "driver_offer_accepted": False,
            "public_offer_agreement": None,
            "driver_offer_agreement": None
        }

        for agreement in agreements:
            if agreement.type == AgreementType.PUBLIC_OFFER:
                status["public_offer_accepted"] = True
                status["public_offer_agreement"] = agreement
            elif agreement.type == AgreementType.DRIVER_OFFER:
                status["driver_offer_accepted"] = True
                status["driver_offer_agreement"] = agreement

        return status
