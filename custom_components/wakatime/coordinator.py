"""DataUpdateCoordinator for the Wakatime integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WakatimeApiAuthError, WakatimeApiClient, WakatimeApiError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_STATS_RANGE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_RANGE,
    DOMAIN,
    LOGGER,
)


class WakatimeDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage fetching Wakatime data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WakatimeApiClient,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.entry = entry
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    @property
    def stats_range(self) -> str:
        """Return the configured stats range."""
        return self.entry.options.get(CONF_STATS_RANGE, DEFAULT_STATS_RANGE)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all endpoints in parallel and normalize the result."""
        try:
            async with async_timeout.timeout(30):
                (
                    user_info,
                    stats,
                    summary_today,
                    all_time,
                    goals,
                    machines,
                    projects,
                ) = await asyncio.gather(
                    self.client.get_user_info(),
                    self.client.get_stats(self.stats_range),
                    self.client.get_summary_today(),
                    self.client.get_all_time_since_today(),
                    self.client.get_goals(),
                    self.client.get_machine_names(),
                    self.client.get_projects(),
                )
        except WakatimeApiAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except WakatimeApiError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "user": user_info.get("data", {}),
            "stats": stats.get("data", {}),
            "summaries": summary_today.get("data", []),
            "all_time": all_time.get("data", {}),
            "goals": goals.get("data", []),
            "machines": machines.get("data", []),
            "projects": projects.get("data", []),
        }
