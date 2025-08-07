"""Config flow for Wakatime integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WakatimeApiClient
from .const import DOMAIN, NAME, CONF_BASE_URL

_LOGGER = logging.getLogger(__name__)


class WakatimeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wakatime."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            base_url = user_input.get(CONF_BASE_URL, "https://wakatime.com/api/v1")
            api_key = user_input[CONF_API_KEY]
            session = async_get_clientsession(self.hass)
            client = WakatimeApiClient(api_key, session, base_url=base_url)

            try:
                user_info = await client.get_user_info()
                if "data" in user_info and "email" in user_info["data"]:
                    # Successfully authenticated
                    await self.async_set_unique_id(user_info["data"]["id"])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=user_info["data"]["email"],
                        data=user_input,
                    )
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_BASE_URL, default="https://wakatime.com/api/v1"): str,
                }
            ),
            errors=errors,
        )
