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
        status = self.coordinator.data["status"]

        # Identify the device by its spa serial number — it is stable
        # across user renames in the Caldera app. The display name
        # still comes from the user-facing spa name.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, status.spaSerialNumber)},
            name=status.spaName,
            manufacturer="Caldera Spas",
            model=status.spaModel,
            serial_number=status.spaSerialNumber,
        )
