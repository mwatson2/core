"""Common fixtures for the Caldera Spas tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.caldera.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

# @pytest.fixture(autouse=True)
# def skip_translations_check() -> Generator[None, None, None]:
#     """Skip translation checks for Caldera tests."""
#     # The translations are properly set up in strings.json, but
#     # there appears to be an issue with the test framework's validation
#     # of these translations. For now, we'll skip the check.
#     with patch("tests.components.conftest._validate_translation") as mock:
#         mock.return_value = None
#         mock.side_effect = None
#         yield


# Mock data for the integration
@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "password",
        },
        title="Caldera Spa",
        unique_id="REU21D4211094",
    )


# Mock for LiveSettings
class MockLiveSettings:
    """Mock for LiveSettings."""

    def __init__(self) -> None:
        """Initialize mock settings."""
        self.ctrl_head_set_temperature = 102
        self.light_status = True
        self.pump1_status = 2  # PUMP_HIGH
        self.pump2_status = 1  # PUMP_LOW
        self.pump3_status = 0  # PUMP_OFF


# Mock for SpaStatus
class MockSpaStatus:
    """Mock for SpaStatus."""

    def __init__(self) -> None:
        """Initialize mock status."""
        self.spaName = "MyCalderaSpa"
        self.spaSerialNumber = "REU21D4211094"
        self.spaModel = "Caldera Utopia"
        self.ctrl_head_water_temperature = 100
        self.is_heating = True
        self.status = "ONLINE"


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    """Return a mocked Caldera client."""
    with patch("pycaldera.AsyncCalderaClient", autospec=True) as client_mock:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None

        # Set up mock responses
        client.get_spa_status.return_value = MockSpaStatus()
        client.get_live_settings.return_value = MockLiveSettings()

        client_mock.return_value = client
        yield client


@pytest.fixture(autouse=True)
def mock_caldera_client() -> Generator[AsyncMock]:
    """Mock AsyncCalderaClient globally for all tests."""
    with patch("homeassistant.components.caldera.AsyncCalderaClient") as client_mock:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None

        # Set up mock responses
        client.get_spa_status.return_value = MockSpaStatus()
        client.get_live_settings.return_value = MockLiveSettings()

        client_mock.return_value = client
        yield client_mock


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> MockConfigEntry:
    """Set up the Caldera Spas integration for testing."""
    with patch(
        "homeassistant.components.caldera.AsyncCalderaClient",
        return_value=mock_client,
    ):
        mock_config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        return mock_config_entry
