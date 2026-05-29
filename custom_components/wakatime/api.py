"""API client for Wakatime."""

from __future__ import annotations

import base64
import logging

import aiohttp
from homeassistant.util import dt as dt_util

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class WakatimeApiError(Exception):
    """Generic Wakatime API error."""


class WakatimeApiAuthError(WakatimeApiError):
    """Authentication error talking to the Wakatime API."""


class WakatimeApiClient:
    """API client for Wakatime."""

    def __init__(self, api_key: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session
        encoded = base64.b64encode(api_key.encode()).decode()
        self._headers = {"Authorization": f"Basic {encoded}"}

    async def _fetch_data(self, endpoint: str) -> dict:
        """Fetch and parse data from the API, raising typed errors."""
        url = f"{BASE_URL}/{endpoint}"
        try:
            async with self._session.get(url, headers=self._headers) as response:
                if response.status in (401, 403):
                    msg = f"Authentication failed ({response.status})"
                    raise WakatimeApiAuthError(msg)
                if response.status != 200:
                    msg = f"Error fetching {endpoint}: HTTP {response.status}"
                    raise WakatimeApiError(msg)
                return await response.json()
        except aiohttp.ClientError as err:
            msg = f"Connection error: {err}"
            raise WakatimeApiError(msg) from err

    async def get_user_info(self) -> dict:
        """Get the current user."""
        return await self._fetch_data("users/current")

    async def get_stats(self, stats_range: str = "last_7_days") -> dict:
        """Get aggregated stats for the given range."""
        return await self._fetch_data(f"users/current/stats/{stats_range}")

    async def get_summary_today(self) -> dict:
        """Get today's summary."""
        today = dt_util.now().strftime("%Y-%m-%d")
        return await self._fetch_data(
            f"users/current/summaries?start={today}&end={today}"
        )

    async def get_all_time_since_today(self) -> dict:
        """Get all-time totals."""
        return await self._fetch_data("users/current/all_time_since_today")

    async def get_goals(self) -> dict:
        """Get the user's goals."""
        return await self._fetch_data("users/current/goals")

    async def get_machine_names(self) -> dict:
        """Get the user's machines."""
        return await self._fetch_data("users/current/machine_names")

    async def get_projects(self) -> dict:
        """Get the user's projects."""
        return await self._fetch_data("users/current/projects")
