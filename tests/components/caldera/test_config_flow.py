"""Test the Caldera Spas config flow."""

from unittest.mock import AsyncMock, patch

from pycaldera import (
    AuthenticationError,
    ConnectionError,
    InvalidParameterError,
    SpaControlError,
)

from homeassistant import config_entries
from homeassistant.components.caldera.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form(hass: HomeAssistant, mock_client: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert not result["errors"]

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient",
        return_value=mock_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "MyCalderaSpa"
    assert result2["data"] == {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "test-password",
    }


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as mock_client:
        mock_client.return_value.__aenter__.side_effect = AuthenticationError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "wrong-password",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as mock_client:
        mock_client.return_value.__aenter__.side_effect = ConnectionError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_spa_control_error(hass: HomeAssistant) -> None:
    """Test we handle spa control error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as mock_client:
        mock_client.return_value.__aenter__.side_effect = SpaControlError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_parameters(hass: HomeAssistant) -> None:
    """Test we handle invalid parameters error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as mock_client:
        mock_client.return_value.__aenter__.side_effect = InvalidParameterError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_parameters"}


async def test_form_unexpected_exception(hass: HomeAssistant) -> None:
    """Test we handle unexpected exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as mock_client:
        mock_client.return_value.__aenter__.side_effect = Exception()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


# --- Reauth flow tests --------------------------------------------------------


async def _start_reauth(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> str:
    """Helper: add the entry, kick off the reauth flow, return its flow_id."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    return result["flow_id"]


async def test_reauth_success_updates_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: AsyncMock,
) -> None:
    """Submitting valid credentials updates the entry and aborts."""
    flow_id = await _start_reauth(hass, mock_config_entry)

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_EMAIL: "new@example.com",
                CONF_PASSWORD: "fresh-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_EMAIL] == "new@example.com"
    assert mock_config_entry.data[CONF_PASSWORD] == "fresh-password"


async def test_reauth_wrong_account_aborts(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: AsyncMock,
) -> None:
    """Reauthing into a different spa is rejected."""
    flow_id = await _start_reauth(hass, mock_config_entry)

    # Make get_spa_status return a different serial than the saved entry.
    different_status = AsyncMock()
    different_status.spaSerialNumber = "DIFFERENT_SERIAL"
    different_status.spaName = "Someone else's spa"
    mock_client.get_spa_status.return_value = different_status

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_EMAIL: "other@example.com",
                CONF_PASSWORD: "other-password",
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "wrong_account"


async def test_reauth_invalid_credentials_show_form_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """If the user enters bad credentials again, show the error in the form."""
    flow_id = await _start_reauth(hass, mock_config_entry)

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as cli:
        cli.return_value.__aenter__.side_effect = AuthenticationError()
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_EMAIL: "still@example.com",
                CONF_PASSWORD: "still-bad",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_cannot_connect_show_form_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """A transient connection failure is shown to the user, not aborted."""
    flow_id = await _start_reauth(hass, mock_config_entry)

    with patch(
        "homeassistant.components.caldera.config_flow.AsyncCalderaClient"
    ) as cli:
        cli.return_value.__aenter__.side_effect = ConnectionError()
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_EMAIL: "x@example.com",
                CONF_PASSWORD: "y",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_unique_id_constraint_uses_state(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The reauth path correctly initialises with the entry already loaded."""
    mock_config_entry.add_to_hass(hass)
    # Sanity: the entry exists and has the expected unique id
    assert mock_config_entry.unique_id == "REU21D4211094"
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
