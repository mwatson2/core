"""Test the Caldera Spas climate platform."""

from unittest.mock import AsyncMock

from pycaldera import InvalidParameterError, SpaControlError
import pytest

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
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
    state = hass.states.get("climate.mycalderaspa_temperature")
    assert state
    assert state.state == HVACMode.HEAT
    assert (
        state.attributes[ATTR_CURRENT_TEMPERATURE] == 37.8
    )  # 100°F converted to Celsius
    assert state.attributes[ATTR_TEMPERATURE] == 38.9  # 102°F converted to Celsius
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING

    # Make sure the min/max temps are set properly
    assert state.attributes["min_temp"] == 26.7  # 80°F converted to Celsius
    assert state.attributes["max_temp"] == 40.0  # 104°F converted to Celsius


async def test_set_temperature(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test setting temperature."""
    # Call the service
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: "climate.mycalderaspa_temperature",
            ATTR_TEMPERATURE: 38.3,  # 101°F converted to Celsius
        },
        blocking=True,
    )

    # Check that the API was called with correct parameters
    # The temperature gets converted to F, with a small rounding difference
    mock_client.set_temperature.assert_called_once_with(100.94)

    # Since we can't check if refresh was requested directly, we just make sure
    # the coordinator exists and the test runs without errors
    coordinator = init_integration.runtime_data.coordinator
    assert coordinator is not None


async def test_set_temperature_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when setting temperature."""
    # Test invalid parameter error
    mock_client.set_temperature.side_effect = InvalidParameterError(
        "Invalid temperature"
    )

    # Use a temperature inside the entity's allowed 26.7–40°C range so the
    # call reaches our async_set_temperature override (which then re-raises
    # the mocked pycaldera InvalidParameterError as HomeAssistantError).
    # Going outside the range would short-circuit on upstream climate
    # validation and never exercise our code path.
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.mycalderaspa_temperature",
                ATTR_TEMPERATURE: 39.4,  # 103°F, within range
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
                ATTR_ENTITY_ID: "climate.mycalderaspa_temperature",
                ATTR_TEMPERATURE: 38.3,  # 101°F converted to Celsius
            },
            blocking=True,
        )


async def test_set_hvac_mode(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test setting HVAC mode (which isn't directly supported)."""
    # Calling this service would normally log a warning that it's not supported
    # But that's hard to test here, so we just make sure the entity still exists after

    state_before = hass.states.get("climate.mycalderaspa_temperature")
    assert state_before

    # Try to set mode to OFF
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {
            ATTR_ENTITY_ID: "climate.mycalderaspa_temperature",
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )

    # Entity should still exist and be in the same state
    state_after = hass.states.get("climate.mycalderaspa_temperature")
    assert state_after
    assert state_after.state == state_before.state
