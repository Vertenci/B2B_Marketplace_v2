import io
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.api.schemas.rental_request_schema import RentalRequestResponse
from src.api.schemas.rental_schema import (
    RentalResponse, TelemetryDetailResponse, ViolationDetailResponse,
    RentalDocumentShort, PaymentShort, CarShort, UserShort,
)
from src.api.schemas.company_schema import LessorDashboardResponse
from src.api.schemas.company_schema import CompanyUserResponse, AddOwnerRequest
from src.api.schemas.company_schema import CompanyResponse
from src.api.schemas.finance_schema import FinanceResponse, PaymentResponse, BalanceEventResponse, BalanceAmountRequest
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import RentalStatus, RentalRequestStatus, RentalDocumentType
from src.services.lessor_service import LessorService
from src.services.company_service import CompanyService


router = APIRouter(prefix="/lessor/{company_id}", tags=["Lessor - Rentals & Requests"])


@router.post("/finances/top-up")
async def top_up_balance(
    company_id: uuid.UUID,
    data: BalanceAmountRequest,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    company = await LessorService.top_up_company_balance(
        company_id=company_id,
        user=user,
        session=session,
        amount=data.amount,
    )

    return {
        "company_id": company.id,
        "balance": company.balance,
    }


@router.post("/finances/withdraw")
async def withdraw_balance(
    company_id: uuid.UUID,
    data: BalanceAmountRequest,
    user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    company = await LessorService.withdraw_company_balance(
        company_id=company_id,
        user=user,
        session=session,
        amount=data.amount,
    )

    return {
        "company_id": company.id,
        "balance": company.balance,
    }


@router.get("/requests", response_model=list[RentalRequestResponse])
async def get_incoming_requests(
        company_id: uuid.UUID,
        status: RentalRequestStatus | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalRequestResponse]:
    requests = await LessorService.get_incoming_requests(
        company_id, user, session, status, skip, limit
    )
    return [RentalRequestResponse.model_validate(r) for r in requests]

@router.post("/requests/{request_id}/approve", response_model=RentalResponse)
async def approve_request(
        company_id: uuid.UUID,
        request_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalResponse:
    rental = await LessorService.approve_request(company_id, request_id, user, session)
    return RentalResponse.model_validate(rental)

@router.post("/requests/{request_id}/reject", response_model=RentalRequestResponse)
async def reject_request(
        company_id: uuid.UUID,
        request_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalRequestResponse:
    request = await LessorService.reject_request(company_id, request_id, user, session)
    return RentalRequestResponse.model_validate(request)

@router.get("/rentals", response_model=list[RentalResponse])
async def get_rentals(
        company_id: uuid.UUID,
        status: RentalStatus | None = Query(None),
        payment_pending: bool = Query(False, description="Только завершённые неоплаченные"),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalResponse]:
    rentals = await LessorService.get_rentals(
        company_id, user, session, status, payment_pending, skip, limit
    )
    return [RentalResponse.model_validate(r) for r in rentals]

@router.get("/rentals/{rental_id}", response_model=RentalResponse)
async def get_rental(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalResponse:
    rental = await LessorService.get_rental(company_id, rental_id, user, session)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return RentalResponse.model_validate(rental)

@router.get("/rentals/{rental_id}/driver")
async def get_rental_driver(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    driver = await LessorService.get_rental_driver(company_id, rental_id, user, session)
    return UserShort.model_validate(driver)

@router.get("/rentals/{rental_id}/car")
async def get_rental_car(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    car = await LessorService.get_rental_car(company_id, rental_id, user, session)
    return CarShort.model_validate(car)

@router.get("/rentals/{rental_id}/payment")
async def get_rental_payment(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    payment = await LessorService.get_rental_payment(company_id, rental_id, user, session)
    if not payment:
        return {"detail": "No payment yet — rental not completed"}
    return PaymentShort.model_validate(payment)

@router.get("/rentals/{rental_id}/telemetry", response_model=TelemetryDetailResponse)
async def get_rental_telemetry(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> TelemetryDetailResponse:
    telemetry = await LessorService.get_rental_telemetry(company_id, rental_id, user, session)
    if not telemetry:
        raise HTTPException(status_code=404, detail="Telemetry not found")
    return TelemetryDetailResponse.model_validate(telemetry)

@router.get("/rentals/{rental_id}/violations", response_model=list[ViolationDetailResponse])
async def get_rental_violations(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[ViolationDetailResponse]:
    violations = await LessorService.get_rental_violations(
        company_id, rental_id, user, session, skip, limit
    )
    return [ViolationDetailResponse.model_validate(v) for v in violations]

@router.get("/rentals/{rental_id}/documents", response_model=list[RentalDocumentShort])
async def get_rental_documents(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalDocumentShort]:
    docs = await LessorService.get_rental_documents(company_id, rental_id, user, session)
    return [RentalDocumentShort.model_validate(d) for d in docs]

@router.post("/rentals/{rental_id}/complete", response_model=RentalResponse)
async def complete_rental(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalResponse:
    rental = await LessorService.complete_rental(company_id, rental_id, user, session)
    return RentalResponse.model_validate(rental)

@router.post("/rentals/{rental_id}/documents/{document_type}")
async def download_document(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        document_type: RentalDocumentType,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    file_data, filename, content_type = await LessorService.download_document(
        company_id, rental_id, document_type, user, session
    )
    from urllib.parse import quote
    encoded_name = quote(filename, safe='')
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )

@router.get("/finances", response_model=FinanceResponse)
async def get_finances(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        events_skip: int = Query(0, ge=0, alias="eventsSkip"),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> FinanceResponse:
    data = await LessorService.get_finances(company_id, user, session, skip, limit, events_skip,)
    return FinanceResponse(
        balance=data["balance"],
        payments=[PaymentResponse.model_validate(p) for p in data["payments"]],
        balance_events=[BalanceEventResponse.model_validate(e) for e in data["balance_events"]],
    )

@router.get("/employers")
async def get_employers(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    employers = await LessorService.get_employers(company_id, user, session)
    return [CompanyUserResponse.model_validate(e) for e in employers]

@router.post("/employers", status_code=201)
async def add_employer(
        company_id: uuid.UUID,
        data: AddOwnerRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    employer = await LessorService.add_employer(company_id, data.user_email, user, session)
    return CompanyUserResponse.model_validate(employer)

@router.get("/profile", response_model=CompanyResponse)
async def get_company_profile(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CompanyResponse:
    company = await LessorService.get_company_profile(company_id, user, session)
    return CompanyResponse.model_validate(company)

@router.get("/dashboard", response_model=LessorDashboardResponse)
async def get_lessor_dashboard(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> LessorDashboardResponse:
    data = await CompanyService.get_lessor_dashboard(company_id, user, session)
    return LessorDashboardResponse(**data)

@router.delete("/delete", status_code=204)
async def delete_company(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    await CompanyService.delete_lessor_company(company_id, user, session)
