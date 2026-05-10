import logging
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import select, desc
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
    async def accept_public_offer(
            session: AsyncSession,
            user: UserModel,
            ip_address: str | None = None,
            user_agent: str | None = None
    ) -> AgreementModel:
        """Принять публичную оферту и обновить флаг в профиле пользователя."""
        stmt = select(AgreementModel).where(
            AgreementModel.user_id == user.id,
            AgreementModel.type == AgreementType.PUBLIC_OFFER
        )
        result = await session.execute(stmt)
        existing_agreement = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if existing_agreement:
            existing_agreement.accepted_at = now
            existing_agreement.ip_address = ip_address
            existing_agreement.user_agent = user_agent
            agreement = existing_agreement
        else:
            agreement = AgreementModel(
                user_id=user.id,
                type=AgreementType.PUBLIC_OFFER,
                accepted_at=now,
                ip_address=ip_address,
                user_agent=user_agent
            )
            session.add(agreement)

        # Обновляем флаг в модели пользователя
        user.public_offer_accepted = True

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
            "public_offer_accepted": user.public_offer_accepted,
            "public_offer_agreement": None,
        }

        for agreement in agreements:
            if agreement.type == AgreementType.PUBLIC_OFFER:
                status["public_offer_agreement"] = agreement

        return status
