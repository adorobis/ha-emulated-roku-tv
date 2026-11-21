"""Constants for Emulated Roku TV."""

DOMAIN = "emulated_roku_tv"

CONF_LISTEN_PORT = "listen_port"

DEFAULT_NAME = "Roku TV"
# The core emulated_roku integration defaults to 8060 and counts up from there.
DEFAULT_PORT = 8070

# Same event as the core emulated_roku integration, so automations look alike.
EVENT_ROKU_COMMAND = "roku_command"
