"""Test initialization of the Caldera Spas integration."""

from unittest.mock import AsyncMock, patch

from pycaldera import ConnectionError

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

        # Check that runtime_data is stored in the config entry
        assert mock_config_entry.runtime_data is not None
        assert hasattr(mock_config_entry.runtime_data, "client")
        assert hasattr(mock_config_entry.runtime_data, "coordinator")

        # Unload the integration
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check that the entry is unloaded
        assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

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

        # Entry should be in retry state when the connection fails
        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY

        # Since this is a failure test with a connection error,
        # the entry will be in SETUP_RETRY state and the coordinator will not be
        # set up in hass.data yet

        # Instead, let's verify that the entry ID exists in the config_entries
        assert (
            hass.config_entries.async_get_entry(mock_config_entry.entry_id) is not None
        )

        # Ensure the entry is in retry state
        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
