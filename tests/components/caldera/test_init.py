"""Test initialization of the Caldera Spas integration."""
from unittest.mock import AsyncMock, patch

from pycaldera import ConnectionError, SpaControlError

from homeassistant.components.caldera.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_setup_and_unload_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test we can setup and unload the integration."""
    with patch(
        "homeassistant.components.caldera.AsyncCalderaClient", return_value=mock_client
    ):
        # Setup the integration
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that the entry is loaded
        assert mock_config_entry.state is ConfigEntryState.LOADED

        # Check that client and coordinator are stored in hass.data
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert "client" in hass.data[DOMAIN][mock_config_entry.entry_id]
        assert "coordinator" in hass.data[DOMAIN][mock_config_entry.entry_id]

        # Unload the integration
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that the entry is unloaded
        assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

        # Check that the data has been removed
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]
        
        # Ensure the context manager was properly closed
        assert mock_client.__aexit__.called


async def test_coordinator_update_failure(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Test coordinator update raising exceptions."""
    # Set up for connection error
    mock_client.get_spa_status.side_effect = ConnectionError("Connection failed")
    
    with patch(
        "homeassistant.components.caldera.AsyncCalderaClient", return_value=mock_client
    ):
        # Setup integration
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Entry should still be set up but with entities unavailable
        assert mock_config_entry.state is ConfigEntryState.LOADED
        
        # Access the coordinator
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
        
        # Check that the coordinator shows an error
        assert coordinator.last_update_success is False
        
        # Now set up for SpaControlError
        mock_client.get_spa_status.side_effect = None
        mock_client.get_live_settings.side_effect = SpaControlError("Control failed")
        
        # Manually update the coordinator
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        
        # Check that the coordinator still shows an error
        assert coordinator.last_update_success is False