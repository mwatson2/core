"""DataUpdateCoordinator for the Caldera Spas integration."""

import logging
from typing import Any

from pycaldera import AsyncCalderaClient, ConnectionError, SpaControlError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CalderaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Caldera data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AsyncCalderaClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Caldera.

        The client is already initialized as a context manager in __init__.py,
        so we can use it directly here.
        """
        try:
            # Get current spa status
            status = await self.client.get_spa_status()

            # Get detailed live settings
            settings = await self.client.get_live_settings()
        except ConnectionError as error:
            raise UpdateFailed(
                f"Error communicating with Caldera API: {error}"
            ) from error
        except SpaControlError as error:
            raise UpdateFailed(f"Error controlling Caldera spa: {error}") from error

        return {"status": status, "settings": settings}
