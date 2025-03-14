"""Test the Caldera Spas light platform."""
from unittest.mock import AsyncMock, patch

import pytest
from pycaldera import SpaControlError

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry


async def test_light_entity_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test light entity attributes."""
    state = hass.states.get("light.light")
    assert state
    assert state.state == STATE_ON  # Should be on based on mock data


async def test_turn_on_light(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test turning on the light."""
    # Call the service
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.light",
        },
        blocking=True,
    )
    
    # Check that the API was called
    mock_client.set_lights.assert_called_once_with(True)
    
    # Check that refresh was requested
    coordinator = hass.data["caldera"][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_turn_off_light(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test turning off the light."""
    # Call the service
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "light.light",
        },
        blocking=True,
    )
    
    # Check that the API was called
    mock_client.set_lights.assert_called_once_with(False)
    
    # Check that refresh was requested
    coordinator = hass.data["caldera"][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_light_turn_on_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when turning on light."""
    # Set up error
    mock_client.set_lights.side_effect = SpaControlError("Connection error")
    
    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "light.light",
            },
            blocking=True,
        )


async def test_light_turn_off_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when turning off light."""
    # Set up error
    mock_client.set_lights.side_effect = SpaControlError("Connection error")
    
    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "light.light",
            },
            blocking=True,
        )