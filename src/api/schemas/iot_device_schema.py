import uuid
from pydantic import BaseModel


class CarShortForIot(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID


class IotDeviceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    device_identifier: str | None
    sim_number: str | None
    battery_level: int | None
    is_online: bool
    car: CarShortForIot | None = None


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
