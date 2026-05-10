"""
Роутер для приёма телеметрии от IoT устройств.
IoT устройства отправляют POST запрос с координатами и скоростью.
Авторизация через device_identifier (не требует JWT — IoT использует device_identifier как ключ).
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import db
from src.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["Telemetry (IoT)"])


class TelemetryInput(BaseModel):
    device_identifier: str
    lat: float
    lng: float
    speed: int
    recorded_at: datetime | None = None
    battery_level: int | None = None


class TelemetryOutput(BaseModel):
    id: str
    rental_id: str
    car_id: str
    driver_id: str
    lat: float
    lng: float
    speed: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


@router.post("/ingest", response_model=TelemetryOutput)
async def ingest_telemetry(
        data: TelemetryInput,
        session: AsyncSession = Depends(db.get_session),
) -> TelemetryOutput:
    """
    Принять данные телеметрии от IoT устройства.
    IoT устройство идентифицируется по device_identifier.
    Автоматически проверяются геозоны и скоростной режим.
    """
    telemetry = await TelemetryService.process_telemetry(
        device_identifier=data.device_identifier,
        lat=data.lat,
        lng=data.lng,
        speed=data.speed,
        session=session,
        recorded_at=data.recorded_at,
        battery_level=data.battery_level,
    )
    return TelemetryOutput(
        id=str(telemetry.id),
        rental_id=str(telemetry.rental_id),
        car_id=str(telemetry.car_id),
        driver_id=str(telemetry.driver_id),
        lat=float(telemetry.lat),
        lng=float(telemetry.lng),
        speed=telemetry.speed,
        recorded_at=telemetry.recorded_at,
    )
