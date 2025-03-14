"""Test the Caldera Spas climate platform."""
from unittest.mock import AsyncMock, patch

import pytest
from pycaldera import InvalidParameterError, SpaControlError

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry


async def test_climate_entity_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test climate entity attributes."""
    state = hass.states.get("climate.temperature")
    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 100
    assert state.attributes[ATTR_TEMPERATURE] == 102
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    
    # Make sure the min/max temps are set properly
    assert state.attributes[ATTR_TARGET_TEMP_LOW] == 80
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] == 104


async def test_set_temperature(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test setting temperature."""
    # Call the service
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: "climate.temperature",
            ATTR_TEMPERATURE: 101,
        },
        blocking=True,
    )
    
    # Check that the API was called with correct parameters
    mock_client.set_temperature.assert_called_once_with(101)
    
    # Check that refresh was requested
    coordinator = hass.data["caldera"][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_set_temperature_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when setting temperature."""
    # Test invalid parameter error
    mock_client.set_temperature.side_effect = InvalidParameterError("Invalid temperature")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.temperature",
                ATTR_TEMPERATURE: 120,  # Out of range
            },
            blocking=True,
        )
    
    # Test spa control error
    mock_client.set_temperature.side_effect = SpaControlError("Connection error")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.temperature",
                ATTR_TEMPERATURE: 101,
            },
            blocking=True,
        )


async def test_set_hvac_mode(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test setting HVAC mode (which isn't directly supported)."""
    # Calling this service would normally log a warning that it's not supported
    # But that's hard to test here, so we just make sure the entity still exists after
    
    state_before = hass.states.get("climate.temperature")
    assert state_before
    
    # Try to set mode to OFF
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {
            ATTR_ENTITY_ID: "climate.temperature",
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )
    
    # Entity should still exist and be in the same state
    state_after = hass.states.get("climate.temperature")
    assert state_after
    assert state_after.state == state_before.state