"""Emulated Roku TV: a Roku TV emulation that turns remote commands into events.

Runs next to the core emulated_roku integration and fires the same
``roku_command`` events (``source_name`` = this entry's name), so existing
emulated Roku instances are not touched.
"""

from __future__ import annotations

import logging

from emulated_roku import EmulatedRokuCommandHandler
from homeassistant.components.network import async_get_source_ip
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_START
from homeassistant.core import CoreState, Event, EventOrigin, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_LISTEN_PORT, EVENT_ROKU_COMMAND
from .server import EmulatedRokuTVServer

_LOGGER = logging.getLogger(__name__)

type EmulatedRokuTVConfigEntry = ConfigEntry[EmulatedRokuTVServer]


class EventCommandHandler(EmulatedRokuCommandHandler):
    """Turn remote commands into roku_command events."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Keep a reference to hass for firing events."""
        self.hass = hass

    def _fire(self, roku_usn: str, kind: str, **data: str) -> None:
        self.hass.bus.async_fire(
            EVENT_ROKU_COMMAND,
            {"source_name": roku_usn, "type": kind, **data},
            EventOrigin.local,
        )

    def on_keydown(self, roku_usn: str, key: str) -> None:
        """Fire a keydown event."""
        self._fire(roku_usn, "keydown", key=key)

    def on_keyup(self, roku_usn: str, key: str) -> None:
        """Fire a keyup event."""
        self._fire(roku_usn, "keyup", key=key)

    def on_keypress(self, roku_usn: str, key: str) -> None:
        """Fire a keypress event."""
        self._fire(roku_usn, "keypress", key=key)

    def launch(self, roku_usn: str, app_id: str) -> None:
        """Fire a launch event."""
        self._fire(roku_usn, "launch", app_id=app_id)


async def async_setup_entry(hass: HomeAssistant, entry: EmulatedRokuTVConfigEntry) -> bool:
    """Start an emulated Roku TV server."""
    name: str = entry.data[CONF_NAME]
    port: int = entry.data[CONF_LISTEN_PORT]
    host_ip = await async_get_source_ip(hass)

    server = EmulatedRokuTVServer(hass.loop, EventCommandHandler(hass), name, host_ip, port)
    entry.runtime_data = server

    async def start() -> None:
        try:
            await server.start()
        except OSError:
            await server.close()
            raise
        _LOGGER.info("Emulated Roku TV %s listening on %s:%s", name, host_ip, port)

    if hass.state is CoreState.running:
        try:
            await start()
        except OSError as err:
            raise ConfigEntryNotReady(f"Port {port} is not available: {err}") from err
        return True

    async def start_on_ha_start(_event: Event) -> None:
        try:
            await start()
        except OSError as err:
            _LOGGER.error("Emulated Roku TV %s could not start on port %s: %s", name, port, err)

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_on_ha_start))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EmulatedRokuTVConfigEntry) -> bool:
    """Stop the server."""
    await entry.runtime_data.close()
    return True
