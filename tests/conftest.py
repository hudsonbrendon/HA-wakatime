"""Shared fixtures for Wakatime tests."""

from unittest.mock import AsyncMock, patch

import pytest

from . import const

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Enable loading the wakatime custom integration in every test."""
    return


@pytest.fixture
def mock_api():
    """Patch WakatimeApiClient everywhere it is imported with canned data."""
    with (
        patch(
            "custom_components.wakatime.WakatimeApiClient", autospec=True
        ) as client_cls,
        patch(
            "custom_components.wakatime.config_flow.WakatimeApiClient", new=client_cls
        ),
    ):
        client = client_cls.return_value
        client.get_user_info = AsyncMock(return_value=const.USER_INFO)
        client.get_stats = AsyncMock(return_value=const.STATS)
        client.get_summary_today = AsyncMock(return_value=const.SUMMARY_TODAY)
        client.get_all_time_since_today = AsyncMock(return_value=const.ALL_TIME)
        client.get_goals = AsyncMock(return_value=const.GOALS)
        client.get_machine_names = AsyncMock(return_value=const.MACHINES)
        client.get_projects = AsyncMock(return_value=const.PROJECTS)
        yield client
