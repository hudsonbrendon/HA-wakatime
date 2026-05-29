"""Tests for the Wakatime coordinator error mapping."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.api import WakatimeApiAuthError, WakatimeApiError
from custom_components.wakatime.const import DOMAIN


async def _add(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_API_KEY: "k"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_auth_error_maps_to_setup_error(hass, mock_api):
    """An auth error on first refresh marks the entry as auth-failed."""
    mock_api.get_user_info.side_effect = WakatimeApiAuthError("bad key")
    entry = await _add(hass)
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_api_error_maps_to_setup_retry(hass, mock_api):
    """A generic API error on first refresh schedules a setup retry."""
    mock_api.get_stats.side_effect = WakatimeApiError("boom")
    entry = await _add(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
