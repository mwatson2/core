"""Test the Caldera Spas services."""
from unittest.mock import AsyncMock, patch

import pytest
from pycaldera import InvalidParameterError, SpaControlError

from homeassistant.components.caldera.const import (
    ATTR_PUMP_NUMBER,
    ATTR_PUMP_SPEED,
    DOMAIN,
    SERVICE_SET_LIGHTS,
    SERVICE_SET_PUMP,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from tests.common import MockConfigEntry


async def test_set_temperature_service(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test the set_temperature service."""
    # Call the service
    await hass.services.async_call(
        DOMAIN,
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
    coordinator = hass.data[DOMAIN][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_set_pump_service(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test the set_pump service."""
    # Call the service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_PUMP,
        {
            ATTR_ENTITY_ID: "switch.pump_1",
            ATTR_PUMP_NUMBER: 1,
            ATTR_PUMP_SPEED: 1,  # PUMP_LOW
        },
        blocking=True,
    )
    
    # Check that the API was called with correct parameters
    mock_client.set_pump.assert_called_once_with(1, 1)  # pump 1, PUMP_LOW
    
    # Check that refresh was requested
    coordinator = hass.data[DOMAIN][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_set_lights_service(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test the set_lights service."""
    # Call the service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_LIGHTS,
        {
            ATTR_ENTITY_ID: "light.light",
            "state": False,
        },
        blocking=True,
    )
    
    # Check that the API was called with correct parameters
    mock_client.set_lights.assert_called_once_with(False)
    
    # Check that refresh was requested
    coordinator = hass.data[DOMAIN][init_integration.entry_id]["coordinator"]
    assert coordinator.async_request_refresh.called


async def test_set_temperature_service_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when using set_temperature service."""
    # Test with invalid parameter error
    mock_client.set_temperature.side_effect = InvalidParameterError("Invalid temperature")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.temperature",
                ATTR_TEMPERATURE: 120,  # Out of range
            },
            blocking=True,
        )
    
    # Test with spa control error
    mock_client.set_temperature.side_effect = SpaControlError("Connection error")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.temperature",
                ATTR_TEMPERATURE: 101,
            },
            blocking=True,
        )


async def test_set_pump_service_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when using set_pump service."""
    # Test with invalid parameter error
    mock_client.set_pump.side_effect = InvalidParameterError("Invalid pump")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_PUMP,
            {
                ATTR_ENTITY_ID: "switch.pump_1",
                ATTR_PUMP_NUMBER: 4,  # Invalid pump number
                ATTR_PUMP_SPEED: 1,
            },
            blocking=True,
        )
    
    # Test with spa control error
    mock_client.set_pump.side_effect = SpaControlError("Connection error")
    
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_PUMP,
            {
                ATTR_ENTITY_ID: "switch.pump_1",
                ATTR_PUMP_NUMBER: 1,
                ATTR_PUMP_SPEED: 1,
            },
            blocking=True,
        )


async def test_set_lights_service_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test error handling when using set_lights service."""
    # Set up error
    mock_client.set_lights.side_effect = SpaControlError("Connection error")
    
    # Test error handling
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_LIGHTS,
            {
                ATTR_ENTITY_ID: "light.light",
                "state": True,
            },
            blocking=True,
        )