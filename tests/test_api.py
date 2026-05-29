"""Tests for the WakaTime API client."""

import base64

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.wakatime.api import (
    WakatimeApiAuthError,
    WakatimeApiClient,
    WakatimeApiError,
)
from custom_components.wakatime.const import BASE_URL


async def test_auth_header_is_base64(hass) -> None:
    """The Authorization header must contain the base64-encoded key."""
    session = async_get_clientsession(hass)
    client = WakatimeApiClient("waka_key", session)
    expected = base64.b64encode(b"waka_key").decode()
    assert client._headers["Authorization"] == f"Basic {expected}"


async def test_get_stats_success(hass, aioclient_mock) -> None:
    """A 200 response returns the parsed JSON body."""
    aioclient_mock.get(
        f"{BASE_URL}/users/current/stats/last_7_days",
        json={"data": {"total_seconds": 100}},
    )
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    data = await client.get_stats("last_7_days")
    assert data["data"]["total_seconds"] == 100


async def test_auth_error_raised_on_401(hass, aioclient_mock) -> None:
    """A 401 raises WakatimeApiAuthError."""
    aioclient_mock.get(f"{BASE_URL}/users/current", status=401)
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    with pytest.raises(WakatimeApiAuthError):
        await client.get_user_info()


async def test_generic_error_raised_on_500(hass, aioclient_mock) -> None:
    """A 500 raises WakatimeApiError (not auth)."""
    aioclient_mock.get(f"{BASE_URL}/users/current", status=500)
    client = WakatimeApiClient("k", async_get_clientsession(hass))
    with pytest.raises(WakatimeApiError):
        await client.get_user_info()
