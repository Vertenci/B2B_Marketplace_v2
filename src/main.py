import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.auth_router import router as auth_router
from src.api.v1.car_router import router as car_router
from src.api.v1.iot_device_router import router as iot_device_router
from src.api.v1.geofence_router import router as geofence_router
from src.api.v1.rental_request_router import router as rental_requests_router
from src.api.v1.rental_router import router as rental_router
from src.admin.setup import setup_admin
from src.core.settings import settings
from src.db.session import db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting app...")
    yield
    logger.info("Shutting app...")
    await db.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization"]
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(car_router, prefix="/api/v1")
app.include_router(iot_device_router, prefix="/api/v1")
app.include_router(geofence_router, prefix="/api/v1")
app.include_router(rental_requests_router, prefix="/api/v1")
app.include_router(rental_router, prefix="/api/v1")

setup_admin(app, db)
