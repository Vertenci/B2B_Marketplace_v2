import io
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.api.schemas.car_schema import CarResponse
from src.api.schemas.company_schema import (
    CompanyResponse, CompanyUserResponse, AddOwnerRequest,
    RenterDashboardResponse,
)
from src.api.schemas.finance_schema import FinanceResponse, PaymentResponse
from src.api.schemas.rental_request_schema import RentalRequestResponse
from src.api.schemas.rental_schema import (
    RentalResponse, TelemetryDetailResponse, ViolationDetailResponse,
    RentalDocumentShort, GeofenceEventShort, PaymentShort,
)
from src.api.schemas.renter_schema import CreateRentalRequestSchema, AddDriverRequest, DriverCompanyUserResponse
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import RentalStatus, RentalDocumentType, CarStatus, CompanyType
from src.services.renter_service import RenterService
from src.services.company_service import CompanyService

router = APIRouter(prefix="/renter/{company_id}", tags=["Renter"])


# ─────────────────────── Drivers ─────────────────────────────────────────────

@router.get("/drivers", response_model=list[DriverCompanyUserResponse])
async def get_drivers(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[DriverCompanyUserResponse]:
    drivers = await RenterService.get_drivers(company_id, user, session)
    return [DriverCompanyUserResponse.model_validate(d) for d in drivers]


@router.post("/drivers", response_model=DriverCompanyUserResponse, status_code=201)
async def add_driver(
        company_id: uuid.UUID,
        data: AddDriverRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> DriverCompanyUserResponse:
    driver = await RenterService.add_driver(company_id, data.driver_email, user, session)
    return DriverCompanyUserResponse.model_validate(driver)


@router.delete("/drivers/{driver_id}", status_code=204)
async def remove_driver(
        company_id: uuid.UUID,
        driver_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    await RenterService.remove_driver(company_id, driver_id, user, session)


@router.patch("/drivers/{driver_id}/toggle", response_model=DriverCompanyUserResponse)
async def toggle_driver(
        company_id: uuid.UUID,
        driver_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> DriverCompanyUserResponse:
    driver = await RenterService.toggle_driver(company_id, driver_id, user, session)
    return DriverCompanyUserResponse.model_validate(driver)


# ─────────────────────── Car Search ──────────────────────────────────────────

@router.get("/cars", response_model=list[CarResponse])
async def search_cars(
        company_id: uuid.UUID,
        brand: str | None = Query(None),
        model: str | None = Query(None),
        year: str | None = Query(None),
        min_price: Decimal | None = Query(None),
        max_price: Decimal | None = Query(None),
        status: CarStatus | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[CarResponse]:
    cars = await RenterService.search_cars(
        company_id, user, session,
        brand=brand, model=model, year=year,
        min_price=min_price, max_price=max_price, status=status,
        skip=skip, limit=limit
    )
    return [CarResponse.model_validate(c) for c in cars]


@router.get("/cars/{car_id}", response_model=CarResponse)
async def get_car(
        company_id: uuid.UUID,
        car_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CarResponse:
    car = await RenterService.get_car_detail(company_id, car_id, user, session)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarResponse.model_validate(car)


# ─────────────────────── Rental Requests ─────────────────────────────────────

@router.get("/requests", response_model=list[RentalRequestResponse])
async def get_requests(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalRequestResponse]:
    requests = await RenterService.get_requests(company_id, user, session, skip, limit)
    return [RentalRequestResponse.model_validate(r) for r in requests]


@router.post("/requests", response_model=RentalRequestResponse, status_code=201)
async def create_request(
        company_id: uuid.UUID,
        data: CreateRentalRequestSchema,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalRequestResponse:
    request = await RenterService.create_request(
        company_id=company_id,
        car_id=data.car_id,
        driver_id=data.driver_id,
        start_date=data.start_date,
        end_date=data.end_date,
        message=data.message,
        user=user,
        session=session,
    )
    return RentalRequestResponse.model_validate(request)


@router.get("/requests/{request_id}", response_model=RentalRequestResponse)
async def get_request(
        company_id: uuid.UUID,
        request_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalRequestResponse:
    request = await RenterService.get_request(company_id, request_id, user, session)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return RentalRequestResponse.model_validate(request)


@router.post("/requests/{request_id}/cancel", response_model=RentalRequestResponse)
async def cancel_request(
        company_id: uuid.UUID,
        request_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalRequestResponse:
    request = await RenterService.cancel_request(company_id, request_id, user, session)
    return RentalRequestResponse.model_validate(request)


# ─────────────────────── Rentals ─────────────────────────────────────────────

@router.get("/rentals", response_model=list[RentalResponse])
async def get_rentals(
        company_id: uuid.UUID,
        status: RentalStatus | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalResponse]:
    rentals = await RenterService.get_rentals(company_id, user, session, status, skip, limit)
    return [RentalResponse.model_validate(r) for r in rentals]


@router.get("/rentals/{rental_id}", response_model=RentalResponse)
async def get_rental(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RentalResponse:
    rental = await RenterService.get_rental(company_id, rental_id, user, session)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return RentalResponse.model_validate(rental)


@router.get("/rentals/{rental_id}/telemetry", response_model=TelemetryDetailResponse)
async def get_rental_telemetry(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> TelemetryDetailResponse:
    telemetry = await RenterService.get_rental_telemetry(company_id, rental_id, user, session)
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
    violations = await RenterService.get_rental_violations(
        company_id, rental_id, user, session, skip, limit
    )
    return [ViolationDetailResponse.model_validate(v) for v in violations]


@router.get("/rentals/{rental_id}/payment")
async def get_rental_payment(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    payment = await RenterService.get_rental_payment(company_id, rental_id, user, session)
    if not payment:
        return {"detail": "No payment yet — rental not completed"}
    return PaymentShort.model_validate(payment)


@router.get("/rentals/{rental_id}/geofence_events", response_model=list[GeofenceEventShort])
async def get_geofence_events(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[GeofenceEventShort]:
    events = await RenterService.get_rental_geofence_events(company_id, rental_id, user, session)
    return [GeofenceEventShort.model_validate(e) for e in events]


@router.post("/rentals/{rental_id}/pay")
async def pay_rental(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    payment = await RenterService.pay_rental(company_id, rental_id, user, session)
    return PaymentShort.model_validate(payment)


@router.get("/rentals/{rental_id}/documents", response_model=list[RentalDocumentShort])
async def get_rental_documents(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[RentalDocumentShort]:
    docs = await RenterService.get_rental_documents(company_id, rental_id, user, session)
    return [RentalDocumentShort.model_validate(d) for d in docs]


@router.post("/rentals/{rental_id}/documents/{document_type}")
async def download_document(
        company_id: uuid.UUID,
        rental_id: uuid.UUID,
        document_type: RentalDocumentType,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    file_data, filename, content_type = await RenterService.download_document(
        company_id, rental_id, document_type, user, session
    )
    from urllib.parse import quote
    encoded_name = quote(filename, safe='')
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
    )


# ─────────────────────── Finances ─────────────────────────────────────────────

@router.get("/finances", response_model=FinanceResponse)
async def get_finances(
        company_id: uuid.UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> FinanceResponse:
    data = await RenterService.get_finances(company_id, user, session, skip, limit)
    return FinanceResponse(
        balance=data["balance"],
        payments=[PaymentResponse.model_validate(p) for p in data["payments"]]
    )


# ─────────────────────── Company Profile ─────────────────────────────────────

@router.get("/profile", response_model=CompanyResponse)
async def get_company_profile(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CompanyResponse:
    company = await CompanyService.get_company_for_user(
        company_id, user, CompanyType.RENTER, session
    )
    return CompanyResponse.model_validate(company)


@router.get("/dashboard", response_model=RenterDashboardResponse)
async def get_renter_dashboard(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> RenterDashboardResponse:
    data = await CompanyService.get_renter_dashboard(company_id, user, session)
    return RenterDashboardResponse(**data)


@router.delete("/delete", status_code=204)
async def delete_company(
        company_id: uuid.UUID,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
):
    await CompanyService.delete_renter_company(company_id, user, session)
