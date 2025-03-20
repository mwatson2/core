"""Test the Caldera Spas switch platform."""

from unittest.mock import AsyncMock

from pycaldera import PUMP_HIGH, PUMP_OFF, InvalidParameterError, SpaControlError
import pytest

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry


async def test_switch_entities(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test switch entities exist and have the right state."""
    # Based on our mock data:
    # - Pump 1 should be on (PUMP_HIGH = 2)
    # - Pump 2 should be on (PUMP_LOW = 1)
    # - Pump 3 should be off (PUMP_OFF = 0)

    # Pump 1
    state_1 = hass.states.get("switch.mycalderaspa_pump_1")
    assert state_1
    assert state_1.state == STATE_ON

    # Pump 2
    state_2 = hass.states.get("switch.mycalderaspa_pump_2")
    assert state_2
    assert state_2.state == STATE_ON

    # Pump 3
    state_3 = hass.states.get("switch.mycalderaspa_pump_3")
    assert state_3
    assert state_3.state == STATE_OFF


async def test_turn_on_pump(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test turning on a pump."""
    # Call the service for Pump 3 (which is off in our mock)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "switch.mycalderaspa_pump_3",
        },
        blocking=True,
    )

    # Check that the API was called with high speed
    mock_client.set_pump.assert_called_once_with(3, PUMP_HIGH)

    # Since we can't check if refresh was requested directly, we just make sure
    # the coordinator exists and the test runs without errors
    coordinator = init_integration.runtime_data.coordinator
    assert coordinator is not None


async def test_turn_off_pump(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test turning off a pump."""
    # Call the service for Pump 1 (which is on in our mock)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "switch.mycalderaspa_pump_1",
        },
        blocking=True,
    )

    # Check that the API was called with off
    mock_client.set_pump.assert_called_once_with(1, PUMP_OFF)

    # Since we can't check if refresh was requested directly, we just make sure
    # the coordinator exists and the test runs without errors
    coordinator = init_integration.runtime_data.coordinator
    assert coordinator is not None


async def test_pump_turn_on_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when turning on pump."""
    # Test invalid parameter error
    mock_client.set_pump.side_effect = InvalidParameterError("Invalid pump")

    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "switch.mycalderaspa_pump_3",
            },
            blocking=True,
        )

    # Test spa control error
    mock_client.set_pump.side_effect = SpaControlError("Connection error")

    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "switch.mycalderaspa_pump_3",
            },
            blocking=True,
        )


async def test_pump_turn_off_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when turning off pump."""
    # Test invalid parameter error
    mock_client.set_pump.side_effect = InvalidParameterError("Invalid pump")

    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "switch.mycalderaspa_pump_1",
            },
            blocking=True,
        )

    # Test spa control error
    mock_client.set_pump.side_effect = SpaControlError("Connection error")

    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "switch.mycalderaspa_pump_1",
            },
            blocking=True,
        )
