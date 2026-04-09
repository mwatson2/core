"""Light platform for Caldera Spas integration."""

from __future__ import annotations

import logging
from typing import Any

from pycaldera import AsyncCalderaClient, SpaControlError

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa light from config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    async_add_entities([CalderaLight(coordinator, client)])


class CalderaLight(CalderaEntity, LightEntity):
    """Caldera Spa light entity."""

    _attr_name = "Light"

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator, client)
        self._attr_unique_id = (
            f"{self.coordinator.data['status'].spaSerialNumber}_light"
        )

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self.coordinator.data["settings"].light_status

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        try:
            await self.client.set_lights(True)
            await self.coordinator.async_request_refresh()
        except SpaControlError as err:
            raise HomeAssistantError(f"Failed to turn on the light: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        try:
            await self.client.set_lights(False)
            await self.coordinator.async_request_refresh()
        except SpaControlError as err:
            raise HomeAssistantError(f"Failed to turn off the light: {err}") from err
