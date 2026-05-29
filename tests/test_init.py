"""Tests for setup and unload of the Wakatime integration."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.const import DOMAIN


async def _add_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "waka_key"},
        unique_id="user-123",
        title="dev@example.com",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_and_unload(hass, mock_api):
    """Entry loads, exposes the coordinator, then unloads cleanly."""
    entry = await _add_entry(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None
    assert entry.runtime_data.data["user"]["id"] == "user-123"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
