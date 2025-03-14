"""The Caldera Spas integration."""

from __future__ import annotations

from typing import cast

from pycaldera import (  # pylint: disable=no-name-in-module
    PUMP_HIGH,
    PUMP_LOW,
    PUMP_OFF,
    AsyncCalderaClient,
    InvalidParameterError,
    SpaControlError,
)
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.light import LightEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_EMAIL,
    CONF_PASSWORD,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent

from .const import (
    ATTR_PUMP_NUMBER,
    ATTR_PUMP_SPEED,
    DOMAIN,
    SERVICE_SET_LIGHTS,
    SERVICE_SET_PUMP,
    SERVICE_SET_TEMPERATURE,
)
from .coordinator import CalderaDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.SWITCH,
]

# Service schemas
SET_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required(ATTR_TEMPERATURE): vol.All(
            vol.Coerce(int), vol.Range(min=80, max=104)
        ),
    }
)

SET_PUMP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required(ATTR_PUMP_NUMBER): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=3)
        ),
        vol.Required(ATTR_PUMP_SPEED): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=2)
        ),
    }
)

SET_LIGHTS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required("state"): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Caldera Spas from a config entry."""
    # Create client
    client = AsyncCalderaClient(
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    # Enter the context manager
    # This is needed because pycaldera requires a context manager
    # but Home Assistant integration design doesn't support this pattern directly
    await client.__aenter__()  # pylint: disable=unnecessary-dunder-call

    # Create coordinator for data updates
    coordinator = CalderaDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def set_temperature_service(call: ServiceCall) -> None:
        """Handle set temperature service."""
        entity_ids = call.data[ATTR_ENTITY_ID]
        temperature = call.data[ATTR_TEMPERATURE]

        # Get climate component and entities
        component = cast(EntityComponent[ClimateEntity], hass.data.get("climate"))
        if not component:
            raise HomeAssistantError("Climate component not found")

        # Find matching entities and call the service
        target_entities = [
            entity
            for entity in component.entities
            if entity.entity_id in entity_ids
            and entity.platform.platform_name == DOMAIN
        ]

        if not target_entities:
            raise HomeAssistantError(
                f"No Caldera spa entities found with ids: {entity_ids}"
            )

        for entity in target_entities:
            await entity.async_set_temperature(**{ATTR_TEMPERATURE: temperature})

    async def set_pump_service(call: ServiceCall) -> None:
        """Handle set pump service."""
        entity_ids = call.data[ATTR_ENTITY_ID]
        pump_number = call.data[ATTR_PUMP_NUMBER]
        pump_speed = call.data[ATTR_PUMP_SPEED]

        speed_map = {0: PUMP_OFF, 1: PUMP_LOW, 2: PUMP_HIGH}

        # Find the first entity from the list to get access to the client
        client = None
        target_entity = None

        # Get switch component and entities
        component = cast(EntityComponent[SwitchEntity], hass.data.get("switch"))
        if not component:
            raise HomeAssistantError("Switch component not found")

        for entity in component.entities:
            if (
                entity.entity_id in entity_ids
                and entity.platform.platform_name == DOMAIN
            ):
                target_entity = entity
                break

        if target_entity and hasattr(target_entity, "client"):
            client = target_entity.client
        else:
            # Try to find client in the integration data
            for entry_data in hass.data[DOMAIN].values():
                if "client" in entry_data:
                    client = entry_data["client"]
                    break

        if not client:
            raise HomeAssistantError("Could not find Caldera spa client")

        try:
            await client.set_pump(pump_number, speed_map[pump_speed])

            # Refresh all coordinators
            for entry_data in hass.data[DOMAIN].values():
                if "coordinator" in entry_data:
                    await entry_data["coordinator"].async_request_refresh()

        except InvalidParameterError as err:
            raise HomeAssistantError(f"Invalid pump parameters: {err}") from err
        except SpaControlError as err:
            raise HomeAssistantError(f"Error controlling pump: {err}") from err

    async def set_lights_service(call: ServiceCall) -> None:
        """Handle set lights service."""
        entity_ids = call.data[ATTR_ENTITY_ID]
        state = call.data["state"]

        # Get light component and entities
        component = cast(EntityComponent[LightEntity], hass.data.get("light"))
        if not component:
            raise HomeAssistantError("Light component not found")

        # Find matching entities and call the service
        target_entities = [
            entity
            for entity in component.entities
            if entity.entity_id in entity_ids
            and entity.platform.platform_name == DOMAIN
        ]

        if not target_entities:
            raise HomeAssistantError(
                f"No Caldera spa light entities found with ids: {entity_ids}"
            )

        for entity in target_entities:
            if state:
                await entity.async_turn_on()
            else:
                await entity.async_turn_off()

    # Register the services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        set_temperature_service,
        schema=SET_TEMPERATURE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_PUMP, set_pump_service, schema=SET_PUMP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_LIGHTS, set_lights_service, schema=SET_LIGHTS_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = hass.data[DOMAIN].pop(entry.entry_id)
        client = data["client"]
        # Properly exit the context manager
        await client.__aexit__(None, None, None)

        # If this is the last config entry, remove the services
        if not hass.data[DOMAIN]:
            for service in (
                SERVICE_SET_TEMPERATURE,
                SERVICE_SET_PUMP,
                SERVICE_SET_LIGHTS,
            ):
                hass.services.async_remove(DOMAIN, service)

    return unload_ok
