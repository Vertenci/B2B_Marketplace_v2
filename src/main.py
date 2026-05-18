import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.auth_router import router as auth_router
from src.api.v1.profile_router import router as profile_router
from src.api.v1.company_router import router as company_router
from src.api.v1.document_router import router as document_router
from src.api.v1.lessor_car_router import router as lessor_car_router
from src.api.v1.lessor_geofence_router import router as lessor_geofence_router
from src.api.v1.lessor_rental_router import router as lessor_rental_router
from src.api.v1.renter_router import router as renter_router
from src.api.v1.driver_router import router as driver_router
from src.api.v1.telemetry_router import router as telemetry_router
from src.admin.setup import setup_admin
from src.clients.iot_simulator import iot_simulator
from src.core.settings import settings
from src.db.session import db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting app...")

    iot_simulator.set_base_url(settings.APP_BASE_URL)

    await iot_simulator.restore_from_db(db.session_factory)

    yield

    logger.info("Shutting app...")
    iot_simulator.unregister_all()
    await db.dispose()


app = FastAPI(
    title="B2B Fleet Marketplace",
    description="API для платформы аренды транспорта",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

PREFIX = "/api/v1"


app.include_router(auth_router, prefix=PREFIX)

app.include_router(profile_router, prefix=PREFIX)
app.include_router(company_router, prefix=PREFIX)

app.include_router(document_router, prefix=PREFIX)

app.include_router(lessor_car_router, prefix=PREFIX)
app.include_router(lessor_geofence_router, prefix=PREFIX)
app.include_router(lessor_rental_router, prefix=PREFIX)

app.include_router(renter_router, prefix=PREFIX)

app.include_router(driver_router, prefix=PREFIX)

app.include_router(telemetry_router, prefix=PREFIX)

setup_admin(app, db)
