"""The Wakatime integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WakatimeApiClient
from .coordinator import WakatimeDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]

type WakatimeConfigEntry = ConfigEntry[WakatimeDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> bool:
    """Set up Wakatime from a config entry."""
    client = WakatimeApiClient(entry.data[CONF_API_KEY], async_get_clientsession(hass))
    coordinator = WakatimeDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: WakatimeConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
