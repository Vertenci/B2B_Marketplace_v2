import uuid
from typing import Any

from pydantic import BaseModel


class CarShortForIot(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID


def _safe_get(obj: Any, attr: str) -> Any:
    try:
        return getattr(obj, attr)
    except Exception:
        return None


class IotDeviceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    device_identifier: str | None = None
    sim_number: str | None = None
    battery_level: int | None = None
    is_online: bool = False
    car: CarShortForIot | None = None

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):  # type: ignore[override]
        if not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "device_identifier": obj.device_identifier,
                "sim_number": obj.sim_number,
                "battery_level": obj.battery_level,
                "is_online": obj.is_online,
                "car": _safe_get(obj, "car"),
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class IotDeviceRequest(BaseModel):
    car_id: uuid.UUID | None = None
    device_identifier: str | None = None
    sim_number: str | None = None
    battery_level: int | None = None
    is_online: bool = False


class IotDeviceUpdate(BaseModel):
    device_identifier: str | None = None
    sim_number: str | None = None
    battery_level: int | None = None
    is_online: bool | None = None
    car_id: uuid.UUID | None = None


class DeleteIotResponse(BaseModel):
    success: bool
    message: str
    iot_id: uuid.UUID
