"""Config flow for Emulated Roku TV."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
import voluptuous as vol

from .const import CONF_LISTEN_PORT, DEFAULT_NAME, DEFAULT_PORT, DOMAIN


class EmulatedRokuTVFlowHandler(ConfigFlow, domain=DOMAIN):
    """Add an emulated Roku TV."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the name the remote will see and the port."""
        if user_input is not None:
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            self._async_abort_entries_match({CONF_LISTEN_PORT: user_input[CONF_LISTEN_PORT]})
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        count = len(self._async_current_entries())
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=DEFAULT_NAME if not count else f"{DEFAULT_NAME} {count + 1}",
                    ): str,
                    vol.Required(CONF_LISTEN_PORT, default=DEFAULT_PORT + count): vol.Coerce(int),
                }
            ),
        )
