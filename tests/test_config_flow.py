"""Tests for the Wakatime config and options flows."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResultType

from custom_components.wakatime.api import WakatimeApiAuthError
from custom_components.wakatime.const import DOMAIN


async def test_user_flow_success(hass) -> None:
    """A valid key creates an entry titled with the user's email."""
    with patch(
        "custom_components.wakatime.config_flow.WakatimeApiClient.get_user_info",
        return_value={"data": {"id": "user-123", "email": "dev@example.com"}},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "waka_key"}
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "dev@example.com"
    assert result2["data"][CONF_API_KEY] == "waka_key"


async def test_user_flow_invalid_auth(hass) -> None:
    """An auth error surfaces the invalid_auth message."""
    with patch(
        "custom_components.wakatime.config_flow.WakatimeApiClient.get_user_info",
        side_effect=WakatimeApiAuthError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "bad"}
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"


async def test_options_flow(hass, mock_api) -> None:
    """The options flow stores the chosen scan interval and range."""
    from homeassistant.const import CONF_API_KEY as _KEY
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.wakatime.const import (
        CONF_SCAN_INTERVAL,
        CONF_STATS_RANGE,
    )

    entry = MockConfigEntry(
        domain=DOMAIN, data={_KEY: "waka_key"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_SCAN_INTERVAL: 15, CONF_STATS_RANGE: "last_30_days"},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 15
    assert entry.options[CONF_STATS_RANGE] == "last_30_days"

    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_reauth_flow(hass, mock_api):
    """Reauth replaces the stored API key when the new key validates."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_API_KEY: "old"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new"}
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data[CONF_API_KEY] == "new"
