"""Tests for the Wakatime sensors."""

from homeassistant.const import CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wakatime.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_API_KEY: "waka_key"}, unique_id="user-123"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_daily_total_sensor(hass, mock_api):
    """Daily total reflects today's summary grand_total."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_daily_total")
    assert state is not None
    assert state.state == "3600"


async def test_top_language_sensor(hass, mock_api):
    """Top language is the first language and lists the rest as attributes."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_top_language")
    assert state.state == "Python"
    assert state.attributes["breakdown"][0]["name"] == "Python"


async def test_range_total_and_all_time(hass, mock_api):
    """Range total and all-time total map to stats/all_time totals.

    Without translations loaded HA falls back to device_class ("duration") for
    the entity name, so the entity_ids are duration / duration_3 rather than
    range_total / all_time_total.  Ordering matches SENSOR_TYPES: daily_total
    (index 0, gets "daily_total" from translation_key), range_total (index 1,
    first pure-duration fallback → "duration"), daily_average (index 2 →
    "duration_2"), all_time_total (index 3 → "duration_3").
    """
    await _setup(hass)
    assert hass.states.get("sensor.dev_example_duration").state == "36000"
    assert hass.states.get("sensor.dev_example_duration_3").state == "360000"


async def test_goal_sensor_created(hass, mock_api):
    """A sensor is created for each goal."""
    await _setup(hass)
    state = hass.states.get("sensor.dev_example_code_2_hrs_per_day")
    assert state is not None
    assert state.state == "success"
