"""Climate platform for Caldera Spas integration."""

from __future__ import annotations

import logging
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

from .const import DOMAIN
from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

_LOGGER = logging.getLogger(__name__)

# Temperature limits as per API documentation
MIN_TEMP_F = 80
MAX_TEMP_F = 104


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa climate entity from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    async_add_entities([CalderaClimate(coordinator, client)])


class CalderaClimate(CalderaEntity, ClimateEntity):
    """Caldera Spa climate entity."""

    _attr_name = "Temperature"
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
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
        # Use unique_id from spa name
        self._attr_unique_id = f"{self.coordinator.data['status'].spaName}_temperature"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data["status"].ctrl_head_water_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data["settings"].ctrl_head_set_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        # Return HEAT if the heating element is on, otherwise OFF
        # This needs to be adapted based on actual API response
        if self.coordinator.data["status"].is_heating:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action."""
        # Return HEATING if the spa is actively heating
        if self.coordinator.data["status"].is_heating:
            return HVACAction.HEATING
        # Return IDLE if the spa is on but not actively heating
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
                f"Invalid temperature: {temperature}. Must be between {MIN_TEMP_F} and {MAX_TEMP_F}"
            ) from err
        except SpaControlError as err:
            raise HomeAssistantError(f"Failed to set temperature: {err}") from err

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode. This is a placeholder as we can't directly control the heater."""
        # This is mostly a placeholder since we typically can't control the heater directly
        # Could be adapted if the API supports turning the heater on/off
        _LOGGER.warning(
            "Setting HVAC mode is not supported. The spa heater is controlled automatically based on temperature"
        )
