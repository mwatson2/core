"""The Caldera Spas integration."""

from __future__ import annotations

from dataclasses import dataclass

from pycaldera import AsyncCalderaClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .coordinator import CalderaDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.SWITCH,
]


@dataclass
class CalderaRuntimeData:
    """Class to store the runtime data."""

    client: AsyncCalderaClient
    coordinator: CalderaDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Caldera Spas from a config entry."""
    # Create client
    client = AsyncCalderaClient(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    # Enter the context manager
    # This is needed because pycaldera requires a context manager
    # but Home Assistant integration design doesn't support this pattern directly
    await client.__aenter__()  # pylint: disable=unnecessary-dunder-call

    # Create coordinator for data updates
    coordinator = CalderaDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    # Store runtime data in config entry
    entry.runtime_data = CalderaRuntimeData(
        client=client,
        coordinator=coordinator,
    )

    # Set up platforms with the entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Get runtime data from config entry
        runtime_data: CalderaRuntimeData = entry.runtime_data
        # Properly exit the context manager
        await runtime_data.client.__aexit__(None, None, None)

    return unload_ok
