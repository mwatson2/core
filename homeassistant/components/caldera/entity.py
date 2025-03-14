"""Entity for Caldera Spas integration."""

from __future__ import annotations

from pycaldera import AsyncCalderaClient

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CalderaDataUpdateCoordinator


class CalderaEntity(CoordinatorEntity[CalderaDataUpdateCoordinator]):
    """Base entity for Caldera Spas."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CalderaDataUpdateCoordinator,
        client: AsyncCalderaClient,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.client = client
        # Use spa name from status for device info
        spa_name = self.coordinator.data["status"].spaName

        # Set up device info for all entities
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, spa_name)},
            name=spa_name,
            manufacturer="Caldera Spas",
            model=self.coordinator.data["status"].spaModel,
        )
