"""Fan platform for Caldera Spas integration (jet pumps)."""

from __future__ import annotations

from typing import Any

from pycaldera import (
    PUMP_HIGH,
    PUMP_LOW,
    PUMP_OFF,
    AsyncCalderaClient,
    InvalidParameterError,
    PumpInfo,
    SpaControlError,
)

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

PRESET_LOW = "low"
PRESET_HIGH = "high"

_PRESET_TO_SPEED = {PRESET_LOW: PUMP_LOW, PRESET_HIGH: PUMP_HIGH}
_SPEED_TO_PRESET = {v: k for k, v in _PRESET_TO_SPEED.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa pump fans from config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    pumps = coordinator.data["status"].pumps
    async_add_entities(
        CalderaPumpFan(coordinator, client, pump) for pump in pumps
    )


class CalderaPumpFan(CalderaEntity, FanEntity):
    """Caldera Spa jet pump as a fan entity with speed presets."""

    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.PRESET_MODE
    )

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
        pump: PumpInfo,
    ) -> None:
        """Initialize the pump fan entity."""
        super().__init__(coordinator, client)
        self._pump = pump
        self._attr_translation_key = f"pump_{pump.number}"
        self._attr_unique_id = (
            f"{self.coordinator.data['status'].spaSerialNumber}_pump_{pump.number}"
        )
        self._attr_preset_modes = [
            _SPEED_TO_PRESET[s] for s in pump.available_speeds if s != PUMP_OFF
        ]

    @property
    def is_on(self) -> bool:
        """Return True if the pump is on."""
        return (
            self.coordinator.data["settings"].get_pump_speed(self._pump.number)
            != PUMP_OFF
        )

    @property
    def preset_mode(self) -> str | None:
        """Return current preset (low/high) or None when off."""
        speed = self.coordinator.data["settings"].get_pump_speed(self._pump.number)
        return _SPEED_TO_PRESET.get(speed)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the pump on, defaulting to the highest available speed."""
        if preset_mode is not None:
            speed = _PRESET_TO_SPEED[preset_mode]
        else:
            speed = PUMP_HIGH if PUMP_HIGH in self._pump.available_speeds else PUMP_LOW
        await self._set_speed(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the pump off."""
        await self._set_speed(PUMP_OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the pump to the requested preset speed."""
        await self._set_speed(_PRESET_TO_SPEED[preset_mode])

    async def _set_speed(self, speed: int) -> None:
        try:
            await self.client.set_pump(self._pump.number, speed)
            await self.coordinator.async_request_refresh()
        except InvalidParameterError as err:
            raise HomeAssistantError(
                f"Invalid speed {speed} for pump {self._pump.number}"
            ) from err
        except SpaControlError as err:
            raise HomeAssistantError(
                f"Failed to set pump {self._pump.number}: {err}"
            ) from err
