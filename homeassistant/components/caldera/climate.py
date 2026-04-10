"""Climate platform for Caldera Spas integration."""

from __future__ import annotations

from typing import Any

from pycaldera import AsyncCalderaClient, InvalidParameterError, SpaControlError

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

# Temperature limits as per API documentation
MIN_TEMP_F = 80
MAX_TEMP_F = 104


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa climate entity from config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    async_add_entities([CalderaClimate(coordinator, client)])


class CalderaClimate(CalderaEntity, ClimateEntity):
    """Caldera Spa climate entity.

    Caldera spas are always in "heat to setpoint" mode; there is no
    user-controllable heater on/off. HVAC mode is therefore fixed to
    HEAT, and the HEATING vs IDLE distinction is exposed through
    hvac_action instead.
    """

    _attr_name = "Temperature"
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_min_temp = MIN_TEMP_F
    _attr_max_temp = MAX_TEMP_F
    _attr_target_temperature_step = 1.0

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, client)
        self._attr_unique_id = (
            f"{self.coordinator.data['status'].spaSerialNumber}_temperature"
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data["status"].ctrl_head_water_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data["settings"].ctrl_head_set_temperature

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return HEATING if the element is firing, IDLE otherwise."""
        if self.coordinator.data["status"].is_heating:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            await self.client.set_temperature(temperature)
            await self.coordinator.async_request_refresh()
        except InvalidParameterError as err:
            raise HomeAssistantError(
                f"Invalid temperature: {temperature}. "
                f"Must be between {MIN_TEMP_F} and {MAX_TEMP_F}"
            ) from err
        except SpaControlError as err:
            raise HomeAssistantError(f"Failed to set temperature: {err}") from err
