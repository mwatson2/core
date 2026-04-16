"""Switch platform for Caldera Spas integration."""

from __future__ import annotations

from typing import Any

from pycaldera import AsyncCalderaClient, SpaControlError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CalderaDataUpdateCoordinator
from .entity import CalderaEntity

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

    async_add_entities(
        [
            CalderaTempLockSwitch(coordinator, client),
            CalderaSpaLockSwitch(coordinator, client),
        ]
    )


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
