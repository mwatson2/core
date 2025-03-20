"""Diagnostics support for Caldera Spas."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import CalderaRuntimeData

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data: CalderaRuntimeData = entry.runtime_data

    # Get current data from coordinator
    coordinator_data = runtime_data.coordinator.data

    # Convert to serializable format
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": {
            "status": {
                "spa_name": coordinator_data["status"].spaName,
                "spa_model": coordinator_data["status"].spaModel,
                "water_temperature": coordinator_data[
                    "status"
                ].ctrl_head_water_temperature,
                "is_heating": coordinator_data["status"].is_heating,
                "status": coordinator_data["status"].status,
            },
            "settings": {
                "set_temperature": coordinator_data[
                    "settings"
                ].ctrl_head_set_temperature,
                "light_status": coordinator_data["settings"].light_status,
                "pump1_status": coordinator_data["settings"].pump1_status,
                "pump2_status": coordinator_data["settings"].pump2_status,
                "pump3_status": coordinator_data["settings"].pump3_status,
            },
        },
    }
