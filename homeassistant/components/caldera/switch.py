"""Switch platform for Caldera Spas integration."""

from __future__ import annotations

import logging
from typing import Any

from pycaldera import (  # pylint: disable=no-name-in-module
    PUMP_HIGH,
    PUMP_OFF,
    AsyncCalderaClient,
    InvalidParameterError,
    SpaControlError,
)

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

_LOGGER = logging.getLogger(__name__)

# Define max number of pumps based on API
MAX_PUMPS = 3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa pump switches from config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    # Create a switch for each pump (1-based indexing)
    switches = [
        CalderaPumpSwitch(coordinator, client, pump_number)
        for pump_number in range(1, MAX_PUMPS + 1)
    ]

    async_add_entities(switches)


class CalderaPumpSwitch(CalderaEntity, SwitchEntity):
    """Caldera Spa pump switch entity."""

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
        pump_number: int,
    ) -> None:
        """Initialize the pump switch entity."""
        super().__init__(coordinator, client)
        self.pump_number = pump_number
        self._attr_name = f"Pump {pump_number}"
        self._attr_unique_id = (
            f"{self.coordinator.data['status'].spaSerialNumber}_pump_{pump_number}"
        )

    @property
    def is_on(self) -> bool:
        """Return True if the pump is on."""
        # Check settings to determine if pump is active (not OFF)
        pump_status = getattr(
            self.coordinator.data["settings"], f"pump{self.pump_number}_status", 0
        )
        return pump_status != PUMP_OFF

    @property
    def available(self) -> bool:
        """Return if the switch is available."""
        # Check if this pump exists on this spa model
        return hasattr(
            self.coordinator.data["settings"], f"pump{self.pump_number}_status"
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the pump (set to high speed)."""
        try:
            await self.client.set_pump(self.pump_number, PUMP_HIGH)
            await self.coordinator.async_request_refresh()
        except InvalidParameterError as err:
            raise HomeAssistantError(
                f"Invalid pump number: {self.pump_number}"
            ) from err
        except SpaControlError as err:
            raise HomeAssistantError(
                f"Failed to turn on pump {self.pump_number}: {err}"
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the pump."""
        try:
            await self.client.set_pump(self.pump_number, PUMP_OFF)
            await self.coordinator.async_request_refresh()
        except InvalidParameterError as err:
            raise HomeAssistantError(
                f"Invalid pump number: {self.pump_number}"
            ) from err
        except SpaControlError as err:
            raise HomeAssistantError(
                f"Failed to turn off pump {self.pump_number}: {err}"
            ) from err
