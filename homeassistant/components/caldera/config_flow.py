"""Config flow for Caldera Spas integration."""

from __future__ import annotations

from typing import Any

from pycaldera import (
    AsyncCalderaClient,
    AuthenticationError,
    ConnectionError,
    InvalidParameterError,
    SpaControlError,
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Caldera Spas."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Use the async context manager as required by the API
                async with AsyncCalderaClient(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                ) as client:
                    # Get basic spa status for verification
                    status = await client.get_spa_status()

                    # Use spa name as the unique ID
                    await self.async_set_unique_id(status.spaName)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=status.spaName,
                        data=user_input,
                    )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except SpaControlError:
                errors["base"] = "cannot_connect"
            except InvalidParameterError:
                errors["base"] = "invalid_parameters"
            except:  # noqa: E722
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
