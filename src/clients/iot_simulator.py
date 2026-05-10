"""
IoT Device Simulator

Каждое устройство (IotDeviceModel) получает свой asyncio-таск, который:
- Отправляет POST /api/v1/telemetry/ingest каждые 3 секунды
- Имитирует GPS-движение по кругу вблизи геозоны устройства
- С вероятностью 10% выходит за пределы геозоны (нарушение)
- Имитирует разряд battery_level от 100% до 5% за 60 сек, затем сбрасывается

Жизненный цикл:
- Устройство добавлено в БД → simulator.register(iot_id, device_identifier, geofence)
- Устройство удалено → simulator.unregister(iot_id)
- При старте приложения → simulator.restore_from_db(session)
"""
import asyncio
import logging
import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


# ─── Константы ────────────────────────────────────────────────────────────────

SEND_INTERVAL_SECONDS = 3          # Интервал отправки данных
BATTERY_DRAIN_SECONDS = 60         # Полный цикл батареи (100→5 за 60 сек)
BATTERY_MIN = 5
BATTERY_MAX = 100
EXIT_ZONE_PROBABILITY = 0.10       # 10% шанс выйти за зону
ORBIT_RADIUS_METERS = 30           # Радиус орбиты внутри зоны (по умолчанию)
BASE_SPEED_KMH = 30                # Базовая скорость имитации
EARTH_RADIUS_M = 6_371_000         # Радиус Земли в метрах

# Fallback-центр если у устройства нет геозоны (Москва)
DEFAULT_CENTER_LAT = 55.7558
DEFAULT_CENTER_LNG = 37.6173
DEFAULT_ZONE_RADIUS = 200          # метров


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _offset_latlon(lat: float, lng: float, dx_m: float, dy_m: float):
    """Смещение точки на dx_m метров по долготе и dy_m по широте."""
    new_lat = lat + (dy_m / EARTH_RADIUS_M) * (180.0 / math.pi)
    new_lng = lng + (dx_m / EARTH_RADIUS_M) * (180.0 / math.pi) / math.cos(math.radians(lat))
    return new_lat, new_lng


def _point_on_circle(center_lat: float, center_lng: float,
                     radius_m: float, angle_deg: float):
    """Точка на окружности заданного радиуса вокруг центра."""
    rad = math.radians(angle_deg)
    dx = radius_m * math.cos(rad)
    dy = radius_m * math.sin(rad)
    return _offset_latlon(center_lat, center_lng, dx, dy)


# ─── Состояние одного устройства ──────────────────────────────────────────────

@dataclass
class DeviceState:
    iot_id: uuid.UUID
    device_identifier: str
    center_lat: float
    center_lng: float
    zone_radius_m: float             # радиус геозоны в метрах

    angle: float = 0.0               # текущий угол на орбите (градусы)
    battery_level: int = BATTERY_MAX
    _battery_step: int = field(default=0, init=False)  # сколько тиков прошло

    @property
    def orbit_radius(self) -> float:
        """Орбита — 70% от радиуса зоны, но не больше 150м и не меньше 10м."""
        return max(10.0, min(150.0, self.zone_radius_m * 0.70))

    def next_position(self) -> tuple[float, float, int]:
        """
        Рассчитать следующую позицию и скорость.
        Возвращает (lat, lng, speed_kmh).
        """
        self.angle = (self.angle + 12.0) % 360.0  # 12° за тик → полный круг за 30 тиков

        use_orbit = self.orbit_radius
        outside = random.random() < EXIT_ZONE_PROBABILITY

        if outside:
            # Выход за зону: добавляем случайное смещение за пределами
            extra = self.zone_radius_m * random.uniform(1.3, 2.0)
            use_orbit = extra

        lat, lng = _point_on_circle(
            self.center_lat, self.center_lng,
            use_orbit, self.angle
        )

        # Скорость: обычно 20-50 км/ч, при выходе — 60-130 (нарушение скорости тоже может быть)
        if outside:
            speed = random.randint(80, 130)
        else:
            speed = random.randint(20, 55)

        return round(lat, 7), round(lng, 7), speed

    def next_battery(self) -> int:
        """
        Батарея убывает линейно от 100 до 5 за BATTERY_DRAIN_SECONDS секунд,
        затем сбрасывается на 100 (новый цикл).
        """
        ticks_per_cycle = BATTERY_DRAIN_SECONDS // SEND_INTERVAL_SECONDS  # 20 тиков
        drain_per_tick = (BATTERY_MAX - BATTERY_MIN) / ticks_per_cycle    # ~4.75%/тик

        self._battery_step += 1
        level = BATTERY_MAX - int(self._battery_step * drain_per_tick)

        if level <= BATTERY_MIN:
            self._battery_step = 0
            level = BATTERY_MAX

        self.battery_level = level
        return level


# ─── Менеджер симуляторов ─────────────────────────────────────────────────────

class IotSimulatorManager:
    """
    Синглтон, управляющий asyncio-тасками симуляции IoT устройств.
    Каждый зарегистрированный девайс получает свой бесконечный таск.
    """

    def __init__(self):
        self._tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._base_url: str = "http://localhost:8000"  # будет переопределено при старте

    def set_base_url(self, url: str):
        self._base_url = url.rstrip("/")

    # ── Регистрация / удаление ─────────────────────────────────────────────

    def register(
        self,
        iot_id: uuid.UUID,
        device_identifier: str,
        center_lat: float,
        center_lng: float,
        zone_radius_m: float,
    ):
        """Запустить таск симуляции для устройства."""
        if iot_id in self._tasks:
            logger.debug(f"[IoT Sim] Device {device_identifier} already running, skip")
            return

        state = DeviceState(
            iot_id=iot_id,
            device_identifier=device_identifier,
            center_lat=center_lat,
            center_lng=center_lng,
            zone_radius_m=zone_radius_m,
            angle=random.uniform(0, 360),  # случайная начальная точка на орбите
        )

        task = asyncio.create_task(
            self._run_device(state),
            name=f"iot-sim-{device_identifier}",
        )
        self._tasks[iot_id] = task
        logger.info(f"[IoT Sim] Started device {device_identifier} "
                    f"center=({center_lat:.5f}, {center_lng:.5f}) r={zone_radius_m}m")

    def unregister(self, iot_id: uuid.UUID):
        """Остановить таск симуляции для устройства."""
        task = self._tasks.pop(iot_id, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"[IoT Sim] Stopped device iot_id={iot_id}")

    def unregister_all(self):
        """Остановить все симуляторы (при shutdown)."""
        for iot_id in list(self._tasks):
            self.unregister(iot_id)

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    # ── Восстановление из БД при старте ───────────────────────────────────

    async def restore_from_db(self, session_factory):
        """
        При старте приложения — подгрузить все IoT устройства с активными
        арендами и запустить для них симуляторы.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        from src.models import IotDeviceModel, CarModel, RentalModel
        from src.models.enums import RentalStatus

        try:
            async with session_factory() as session:
                # Берём устройства, у которых есть машина с активной арендой
                stmt = (
                    select(IotDeviceModel)
                    .join(CarModel, IotDeviceModel.car_id == CarModel.id)
                    .join(RentalModel, RentalModel.car_id == CarModel.id)
                    .where(
                        IotDeviceModel.device_identifier.isnot(None),
                        RentalModel.status == RentalStatus.ACTIVE,
                    )
                    .options(
                        joinedload(IotDeviceModel.car).selectinload(CarModel.geofences)
                    )
                )
                result = await session.execute(stmt)
                devices = result.unique().scalars().all()

                for iot in devices:
                    geo = self._pick_geofence(iot.car.geofences if iot.car else [])
                    self.register(
                        iot_id=iot.id,
                        device_identifier=iot.device_identifier,
                        center_lat=geo[0],
                        center_lng=geo[1],
                        zone_radius_m=geo[2],
                    )

                logger.info(f"[IoT Sim] Restored {len(devices)} device(s) from DB")

        except Exception as exc:
            logger.error(f"[IoT Sim] Failed to restore devices from DB: {exc}")

    # ── Внутренняя логика таска ────────────────────────────────────────────

    async def _run_device(self, state: DeviceState):
        """Бесконечный цикл отправки данных для одного устройства."""
        endpoint = f"{self._base_url}/api/v1/telemetry/ingest"

        async with httpx.AsyncClient(timeout=5.0) as client:
            while True:
                try:
                    lat, lng, speed = state.next_position()
                    battery = state.next_battery()

                    payload = {
                        "device_identifier": state.device_identifier,
                        "lat": lat,
                        "lng": lng,
                        "speed": speed,
                        "battery_level": battery,
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    }

                    resp = await client.post(endpoint, json=payload)

                    if resp.status_code == 200:
                        logger.debug(
                            f"[IoT Sim] {state.device_identifier} → "
                            f"({lat}, {lng}) speed={speed} bat={battery}%"
                        )
                    else:
                        # 404 = аренда завершена или устройство не найдено — прекращаем
                        if resp.status_code in (404, 400):
                            logger.info(
                                f"[IoT Sim] Device {state.device_identifier} "
                                f"got {resp.status_code}, stopping simulation"
                            )
                            break
                        else:
                            logger.warning(
                                f"[IoT Sim] {state.device_identifier} → "
                                f"HTTP {resp.status_code}: {resp.text[:120]}"
                            )

                except asyncio.CancelledError:
                    logger.info(f"[IoT Sim] Device {state.device_identifier} cancelled")
                    raise

                except httpx.ConnectError:
                    # Сервер ещё не поднялся — ждём
                    logger.debug(f"[IoT Sim] {state.device_identifier}: connect error, retrying...")

                except Exception as exc:
                    logger.error(f"[IoT Sim] {state.device_identifier}: unexpected error: {exc}")

                await asyncio.sleep(SEND_INTERVAL_SECONDS)

        # Таск завершился сам по себе (404) — удаляем из реестра
        self._tasks.pop(state.iot_id, None)

    # ── Утилиты ───────────────────────────────────────────────────────────

    @staticmethod
    def _pick_geofence(geofences) -> tuple[float, float, float]:
        """
        Выбрать первую активную геозону.
        Возвращает (center_lat, center_lng, radius_m).
        """
        for g in geofences:
            if g.is_active:
                return float(g.center_lat), float(g.center_lng), float(g.radius_meters)

        # Нет геозон — используем Москву по умолчанию
        return DEFAULT_CENTER_LAT, DEFAULT_CENTER_LNG, DEFAULT_ZONE_RADIUS


# Глобальный синглтон
iot_simulator = IotSimulatorManager()
