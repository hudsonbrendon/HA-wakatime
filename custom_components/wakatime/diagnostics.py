"""Diagnostics support for the Wakatime integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import WakatimeConfigEntry

TO_REDACT = {CONF_API_KEY, "email", "ip", "id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: WakatimeConfigEntry,
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
