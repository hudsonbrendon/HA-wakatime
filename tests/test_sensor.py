"""Tests for the Wakatime sensors."""

from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.const import (
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_PROJECTS,
    DOMAIN,
)


async def _setup(hass, options=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "waka_key"},
        options=options or {},
        unique_id="user-123",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity_id(hass, entry, unique_id_suffix):
    """Resolve an entity_id from its stable unique_id, or None."""
    registry = er.async_get(hass)
    return registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{unique_id_suffix}"
    )


def _state(hass, entry, unique_id_suffix):
    """Look up an entity by its stable unique_id, return its state."""
    entity_id = _entity_id(hass, entry, unique_id_suffix)
    assert entity_id is not None, f"no entity registered for {unique_id_suffix}"
    return hass.states.get(entity_id)


async def test_daily_total_sensor(hass, mock_api) -> None:
    """Daily total reflects today's summary grand_total."""
    entry = await _setup(hass)
    state = _state(hass, entry, "daily_total")
    assert state is not None
    assert state.state == "3600"


async def test_top_language_sensor(hass, mock_api) -> None:
    """Top language is the first language and lists the rest as attributes."""
    entry = await _setup(hass)
    state = _state(hass, entry, "top_language")
    assert state.state == "Python"
    assert state.attributes["breakdown"][0]["name"] == "Python"


async def test_range_total_and_all_time(hass, mock_api) -> None:
    """Range total and all-time total map to stats/all_time totals."""
    entry = await _setup(hass)
    assert _state(hass, entry, "range_total").state == "36000"
    assert _state(hass, entry, "all_time_total").state == "360000"


async def test_productivity_level(hass, mock_api) -> None:
    """daily_average of 9000s (>7200) maps to Medium."""
    entry = await _setup(hass)
    assert _state(hass, entry, "productivity_level").state == "Medium"


async def test_goal_sensor_created(hass, mock_api) -> None:
    """A sensor is created for each goal (unique_id suffix goal_<id>)."""
    entry = await _setup(hass)
    state = _state(hass, entry, "goal_goal-1")
    assert state is not None
    assert state.state == "success"
    assert state.attributes["title"] == "Code 2 hrs per day"


async def test_project_sensor_created(hass, mock_api) -> None:
    """A monitored project gets its own sensor with range coding seconds."""
    entry = await _setup(hass, {CONF_MONITORED_PROJECTS: ["ha-wakatime"]})
    state = _state(hass, entry, "project_ha-wakatime")
    assert state is not None
    assert state.state == "21600"


async def test_enabled_sensors_filter(hass, mock_api) -> None:
    """Only sensors listed in CONF_ENABLED_SENSORS are created."""
    entry = await _setup(hass, {CONF_ENABLED_SENSORS: ["daily_total"]})
    assert _state(hass, entry, "daily_total") is not None
    assert _entity_id(hass, entry, "range_total") is None
