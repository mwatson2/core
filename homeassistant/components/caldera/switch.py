"""Switch platform for Caldera Spas integration."""

from __future__ import annotations

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
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

# Define max number of pumps based on API
MAX_PUMPS = 3

# The spa's lock_state fields are strings: "1" = disabled/unlocked,
# "2" = enabled/locked. These values are not exported from pycaldera's
# public API (they live in pycaldera.const), so keep a local copy.
_LOCK_ENABLED = "2"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Caldera Spa switches from config entry."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    client = runtime_data.client

    entities: list[CalderaEntity] = [
        CalderaPumpSwitch(coordinator, client, pump_number)
        for pump_number in range(1, MAX_PUMPS + 1)
    ]
    entities.append(CalderaTempLockSwitch(coordinator, client))
    entities.append(CalderaSpaLockSwitch(coordinator, client))

    async_add_entities(entities)


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
        self._attr_translation_key = f"pump_{pump_number}"
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


class _CalderaLockSwitch(CalderaEntity, SwitchEntity):
    """Base class for Caldera control-lock switches.

    These are not physical door locks — they are preference toggles
    that prevent bathers from changing settings at the spa's topside
    panel. Exposed as switches (not lock entities) so HA groups them
    with the other configuration toggles rather than with door locks.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _lock_state_attr: str
    _lock_slug: str

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
    ) -> None:
        """Initialize the lock switch."""
        super().__init__(coordinator, client)
        self._attr_translation_key = self._lock_slug
        self._attr_unique_id = (
            f"{self.coordinator.data['status'].spaSerialNumber}_{self._lock_slug}"
        )

    @property
    def is_on(self) -> bool:
        """Return True when the lock is engaged."""
        value = getattr(
            self.coordinator.data["settings"], self._lock_state_attr, None
        )
        return value == _LOCK_ENABLED

    async def _async_set(self, locked: bool) -> None:
        """Subclasses implement the pycaldera call."""
        raise NotImplementedError

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Engage the lock."""
        try:
            await self._async_set(True)
            await self.coordinator.async_request_refresh()
        except SpaControlError as err:
            raise HomeAssistantError(
                f"Failed to engage {self._lock_slug}: {err}"
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Release the lock."""
        try:
            await self._async_set(False)
            await self.coordinator.async_request_refresh()
        except SpaControlError as err:
            raise HomeAssistantError(
                f"Failed to release {self._lock_slug}: {err}"
            ) from err


class CalderaTempLockSwitch(_CalderaLockSwitch):
    """Lock the spa's temperature setpoint against panel changes."""

    _lock_slug = "temperature_lock"
    _lock_state_attr = "usr_set_temp_lock_state"

    async def _async_set(self, locked: bool) -> None:
        """Call pycaldera to toggle the temperature lock."""
        await self.client.set_temp_lock(locked)


class CalderaSpaLockSwitch(_CalderaLockSwitch):
    """Lock all spa controls against panel changes."""

    _lock_slug = "spa_lock"
    _lock_state_attr = "usr_set_spa_lock_state"

    async def _async_set(self, locked: bool) -> None:
        """Call pycaldera to toggle the full spa lock."""
        await self.client.set_spa_lock(locked)
