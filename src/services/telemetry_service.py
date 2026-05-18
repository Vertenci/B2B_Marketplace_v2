import math
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import (
    TelemetryModel,
    RentalModel,
    IotDeviceModel,
    GeofenceModel,
    GeofenceEventModel,
    ViolationModel,
)
from src.models.enums import (
    RentalStatus,
    GeofenceType,
    ViolationType,
    SeverityType,
)

SPEED_LIMIT_KMH = 120


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Радиус Земли в метрах
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class TelemetryService:
    @staticmethod
    async def process_telemetry(
            device_identifier: str,
            lat: float,
            lng: float,
            speed: int,
            session: AsyncSession,
            recorded_at: datetime | None = None,
            battery_level: int | None = None,
    ) -> TelemetryModel:
        result = await session.execute(
            select(IotDeviceModel)
            .where(IotDeviceModel.device_identifier == device_identifier)
            .options(joinedload(IotDeviceModel.car))
        )
        iot = result.unique().scalar_one_or_none()
        if not iot:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"IoT device '{device_identifier}' not found")

        if not iot.car_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="IoT device is not attached to any car")

        car_id = iot.car_id

        result = await session.execute(
            select(RentalModel)
            .where(
                RentalModel.car_id == car_id,
                RentalModel.status == RentalStatus.ACTIVE,
            )
        )
        rental = result.scalar_one_or_none()
        if not rental:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="No active rental for this car")

        iot.is_online = True
        if battery_level is not None:
            iot.battery_level = max(0, min(100, battery_level))

        now = recorded_at or datetime.now(timezone.utc)
        telemetry = TelemetryModel(
            rental_id=rental.id,
            car_id=car_id,
            driver_id=rental.driver_id,
            lat=Decimal(str(lat)),
            lng=Decimal(str(lng)),
            speed=speed,
            recorded_at=now,
        )
        session.add(telemetry)

        if speed > SPEED_LIMIT_KMH:
            violation = ViolationModel(
                rental_id=rental.id,
                geofence_event_id=None,
                type=ViolationType.SPEEDING,
                severity=SeverityType.WARNING,
            )
            session.add(violation)

        result = await session.execute(
            select(GeofenceModel).where(
                GeofenceModel.car_id == car_id,
                GeofenceModel.is_active == True,
            )
        )
        geofences = result.scalars().all()

        for geofence in geofences:
            distance = _haversine_distance_meters(
                lat, lng,
                float(geofence.center_lat),
                float(geofence.center_lng),
            )
            is_inside = distance <= float(geofence.radius_meters)

            last_event_result = await session.execute(
                select(GeofenceEventModel)
                .where(
                    GeofenceEventModel.rental_id == rental.id,
                    GeofenceEventModel.geofence_id == geofence.id,
                )
                .order_by(GeofenceEventModel.triggered_at.desc())
                .limit(1)
            )
            last_event = last_event_result.scalar_one_or_none()

            was_inside = (last_event is not None and last_event.type == GeofenceType.ENTER)

            event_type = None
            if is_inside and not was_inside:
                event_type = GeofenceType.ENTER
            elif not is_inside and was_inside:
                event_type = GeofenceType.EXIT

            if event_type is not None:
                geo_event = GeofenceEventModel(
                    rental_id=rental.id,
                    geofence_id=geofence.id,
                    type=event_type,
                    lat=Decimal(str(lat)),
                    lng=Decimal(str(lng)),
                    triggered_at=now,
                )
                session.add(geo_event)
                await session.flush()

                if event_type == GeofenceType.EXIT:
                    violation = ViolationModel(
                        rental_id=rental.id,
                        geofence_event_id=geo_event.id,
                        type=ViolationType.GEOFENCE_EXIT,
                        severity=SeverityType.WARNING,
                    )
                    session.add(violation)

        await session.commit()
        await session.refresh(telemetry)
        return telemetry
