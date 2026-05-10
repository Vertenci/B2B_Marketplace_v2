import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.company_schema import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyTypeItem,
    MainDashboardResponse,
)
from src.db.session import db
from src.dependencies.auth import get_current_user
from src.models import UserModel
from src.models.enums import CompanyType
from src.services.company_service import CompanyService

router = APIRouter(tags=["Companies"])


@router.get("/main_dashboard", response_model=MainDashboardResponse)
async def main_dashboard(
        session: AsyncSession = Depends(db.get_session),
):
    """Публичная статистика для главной страницы (гость)."""
    data = await CompanyService.get_main_dashboard(session)
    return MainDashboardResponse(**data)


@router.get("/companies_types", response_model=list[CompanyTypeItem])
async def get_company_types():
    """Список типов компаний."""
    types = await CompanyService.get_company_types()
    return [CompanyTypeItem(**t) for t in types]


@router.post("/create_company/{company_type}", response_model=CompanyResponse, status_code=201)
async def create_company(
        company_type: CompanyType,
        data: CompanyCreateRequest,
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> CompanyResponse:
    """Создать компанию указанного типа."""
    company = await CompanyService.create_company(
        user=user,
        company_type=company_type,
        name=data.name,
        inn=data.inn,
        session=session,
    )
    return CompanyResponse.model_validate(company)


@router.get("/lessor/my_companies", response_model=list[CompanyResponse])
async def get_my_lessor_companies(
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[CompanyResponse]:
    """Список LESSOR компаний текущего пользователя."""
    companies = await CompanyService.get_my_lessor_companies(user, session)
    return [CompanyResponse.model_validate(c) for c in companies]


@router.get("/renter/my_companies", response_model=list[CompanyResponse])
async def get_my_renter_companies(
        user: UserModel = Depends(get_current_user),
        session: AsyncSession = Depends(db.get_session),
) -> list[CompanyResponse]:
    """Список RENTER компаний текущего пользователя."""
    companies = await CompanyService.get_my_renter_companies(user, session)
    return [CompanyResponse.model_validate(c) for c in companies]
