"""Config flow for Caldera Spas integration."""

from __future__ import annotations

from collections.abc import Mapping
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


async def _async_validate_credentials(
    email: str, password: str
) -> tuple[str, str]:
    """Authenticate against the Caldera API and return (serial, name).

    Raises:
        AuthenticationError, ConnectionError, SpaControlError,
        InvalidParameterError on the corresponding failure modes.
    """
    async with AsyncCalderaClient(email, password) as client:
        status = await client.get_spa_status()
        return status.spaSerialNumber, status.spaName


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
                serial, name = await _async_validate_credentials(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except SpaControlError:
                errors["base"] = "cannot_connect"
            except InvalidParameterError:
                errors["base"] = "invalid_parameters"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                # Use the spa serial number as the unique ID — it is
                # stable across spa renames in the Caldera app, whereas
                # the user-facing spa name can change.
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-auth when stored credentials stop working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt the user for new Caldera credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                serial, _ = await _async_validate_credentials(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except SpaControlError:
                errors["base"] = "cannot_connect"
            except InvalidParameterError:
                errors["base"] = "invalid_parameters"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                # Make sure the user signed back in to the same spa.
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
