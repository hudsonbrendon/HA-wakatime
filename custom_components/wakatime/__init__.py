"""The Wakatime integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WakatimeApiClient
from .const import DOMAIN, SCAN_INTERVAL, CONF_BASE_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wakatime from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    base_url = entry.data.get(CONF_BASE_URL, "https://wakatime.com/api/v1")
    session = async_get_clientsession(hass)
    client = WakatimeApiClient(api_key, session, base_url=base_url)

    coordinator = WakatimeDataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class WakatimeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Wakatime data."""

    def __init__(self, hass: HomeAssistant, client: WakatimeApiClient) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                summary = await self.client.get_summary()
                stats = await self.client.get_stats()
                user_info = await self.client.get_user_info()
                last_7_days = await self.client.get_last_7_days()
                all_time = await self.client.get_all_time_since_today()

                return {
                    "summary": summary,
                    "stats": stats,
                    "user_info": user_info,
                    "last_7_days": last_7_days,
                    "all_time": all_time,
                }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
