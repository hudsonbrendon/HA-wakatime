"""Config and options flow for the Wakatime integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import WakatimeApiAuthError, WakatimeApiClient, WakatimeApiError
from .const import (
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_GOALS,
    CONF_MONITORED_PROJECTS,
    CONF_SCAN_INTERVAL,
    CONF_STATS_RANGE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STATS_RANGE,
    DOMAIN,
    LOGGER,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    STATS_RANGES,
)


class WakatimeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial Wakatime config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the API-key step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = WakatimeApiClient(user_input[CONF_API_KEY], session)
            try:
                info = await client.get_user_info()
            except WakatimeApiAuthError:
                errors["base"] = "invalid_auth"
            except WakatimeApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception during Wakatime setup")
                errors["base"] = "unknown"
            else:
                data = info.get("data", {})
                if not data.get("id"):
                    errors["base"] = "invalid_auth"
                else:
                    await self.async_set_unique_id(str(data["id"]))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=data.get("email")
                        or data.get("username")
                        or "WakaTime",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return WakatimeOptionsFlow()


class WakatimeOptionsFlow(OptionsFlow):
    """Handle Wakatime options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Local import avoids a circular import at module load time.
        from .sensor import SENSOR_TYPES

        coordinator = self.config_entry.runtime_data
        data = coordinator.data if coordinator else {}
        options = self.config_entry.options

        sensor_keys = [d.key for d in SENSOR_TYPES]
        goal_titles = [
            g.get("title") or str(g.get("id")) for g in data.get("goals", [])
        ]
        project_names = [
            p["name"] for p in data.get("projects", []) if p.get("name")
        ]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
                vol.Optional(
                    CONF_STATS_RANGE,
                    default=options.get(CONF_STATS_RANGE, DEFAULT_STATS_RANGE),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=STATS_RANGES,
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="stats_range",
                    )
                ),
                vol.Optional(
                    CONF_ENABLED_SENSORS,
                    default=options.get(CONF_ENABLED_SENSORS, sensor_keys),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=sensor_keys,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_MONITORED_GOALS,
                    default=options.get(CONF_MONITORED_GOALS, goal_titles),
                ): SelectSelector(
                    SelectSelectorConfig(options=goal_titles, multiple=True)
                ),
                vol.Optional(
                    CONF_MONITORED_PROJECTS,
                    default=options.get(CONF_MONITORED_PROJECTS, []),
                ): SelectSelector(
                    SelectSelectorConfig(options=project_names, multiple=True)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
