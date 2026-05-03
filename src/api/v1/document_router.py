from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.api.schemas.document_schema import (
    AgreementResponse,
    UserAgreementsStatusResponse,
)
from src.clients.minio_client import minio_client
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import AgreementType
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{agreement_type}/download")
async def download_document(
        agreement_type: AgreementType,
        session: AsyncSession = Depends(db.get_session),
):
    document = await DocumentService.get_active_document(session, agreement_type)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active document found for {agreement_type.value}"
        )

    try:
        file_data = minio_client.client.get_object(
            bucket_name=minio_client.bucket_name,
            object_name=document.file_path
        )

        return StreamingResponse(
            file_data.stream(8192),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{document.file_name}"',
                "Content-Length": str(document.file_size)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.post("/{agreement_type}/accept", response_model=AgreementResponse)
async def accept_agreement(
        agreement_type: AgreementType,
        request: Request,
        session: AsyncSession = Depends(db.get_session),
        current_user: UserModel = Depends(get_current_user)
):
    document = await DocumentService.get_active_document(session, agreement_type)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active document for {agreement_type.value}. Contact administrator."
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    agreement = await DocumentService.accept_agreement(
        session=session,
        user=current_user,
        agreement_type=agreement_type,
        ip_address=ip_address,
        user_agent=user_agent
    )

    return AgreementResponse.model_validate(agreement)


@router.get("/status", response_model=UserAgreementsStatusResponse)
async def get_agreements_status(
        session: AsyncSession = Depends(db.get_session),
        current_user: UserModel = Depends(get_current_user)
):
    status_data = await DocumentService.get_user_agreements_status(
        session=session,
        user=current_user
    )

    return UserAgreementsStatusResponse(
        public_offer_accepted=status_data["public_offer_accepted"],
        driver_offer_accepted=status_data["driver_offer_accepted"],
        public_offer_agreement=AgreementResponse.model_validate(status_data["public_offer_agreement"])
        if status_data["public_offer_agreement"] else None,
        driver_offer_agreement=AgreementResponse.model_validate(status_data["driver_offer_agreement"])
        if status_data["driver_offer_agreement"] else None
    )
