"""An emulated Roku that presents itself as a Roku TV.

The core emulated_roku integration presents a "Roku 4" player, so Harmony
picks its Roku 4 profile, which sends only ~12 distinct keys and nothing at
all for the app buttons. A Roku TV profile has volume, channel and input
keys, and Harmony may send app launches when the apps are listed as
installed. This server reuses the emulated_roku library and only changes
what the device says about itself, plus it logs any request it doesn't
know, so new commands can be discovered.
"""

from __future__ import annotations

import logging

from aiohttp import web
from emulated_roku import EmulatedRokuServer

_LOGGER = logging.getLogger(__name__)

INFO_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" ?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <device>
    <deviceType>urn:roku-com:device:player:1-0</deviceType>
    <friendlyName>{usn}</friendlyName>
    <manufacturer>TCL</manufacturer>
    <manufacturerURL>http://www.roku.com/</manufacturerURL>
    <modelDescription>Roku Streaming Player Network Media</modelDescription>
    <modelName>TCL Roku TV</modelName>
    <modelNumber>7105X</modelNumber>
    <modelURL>http://www.roku.com/</modelURL>
    <serialNumber>{usn}</serialNumber>
    <UDN>uuid:{uuid}</UDN>
    </device>
</root>
"""

DEVICE_INFO_TEMPLATE = """<device-info>
    <udn>{uuid}</udn>
    <serial-number>{usn}</serial-number>
    <device-id>{usn}</device-id>
    <vendor-name>TCL</vendor-name>
    <model-number>7105X</model-number>
    <model-name>TCL Roku TV</model-name>
    <model-region>US</model-region>
    <is-tv>true</is-tv>
    <is-stick>false</is-stick>
    <screen-size>55</screen-size>
    <panel-id>1</panel-id>
    <tuner-type>ATSC</tuner-type>
    <supports-ethernet>true</supports-ethernet>
    <wifi-mac>00:00:00:00:00:00</wifi-mac>
    <ethernet-mac>00:00:00:00:00:00</ethernet-mac>
    <network-type>ethernet</network-type>
    <user-device-name>{usn}</user-device-name>
    <friendly-device-name>{usn}</friendly-device-name>
    <friendly-model-name>TCL Roku TV</friendly-model-name>
    <default-device-name>TCL Roku TV - {usn}</default-device-name>
    <software-version>11.5.0</software-version>
    <software-build>4312</software-build>
    <secure-device>true</secure-device>
    <language>en</language>
    <country>US</country>
    <locale>en_US</locale>
    <time-zone>US/Pacific</time-zone>
    <time-zone-offset>-480</time-zone-offset>
    <power-mode>PowerOn</power-mode>
    <supports-suspend>true</supports-suspend>
    <supports-find-remote>false</supports-find-remote>
    <supports-audio-guide>false</supports-audio-guide>
    <supports-ecs-textedit>true</supports-ecs-textedit>
    <supports-ecs-microphone>false</supports-ecs-microphone>
    <supports-wake-on-wlan>false</supports-wake-on-wlan>
    <has-play-on-roku>true</has-play-on-roku>
    <has-mobile-screensaver>false</has-mobile-screensaver>
    <developer-enabled>false</developer-enabled>
    <keyed-developer-id>0000000000000000000000000000000000000000</keyed-developer-id>
    <search-enabled>false</search-enabled>
    <voice-search-enabled>false</voice-search-enabled>
    <notifications-enabled>false</notifications-enabled>
    <notifications-first-use>false</notifications-first-use>
    <supports-private-listening>false</supports-private-listening>
    <headphones-connected>false</headphones-connected>
</device-info>
"""

# Real Roku channel ids, so a remote that only launches installed channels
# finds them, plus the TV inputs a Roku TV reports.
APPS = [
    ("tvinput.dtv", "tvin", "Live TV"),
    ("tvinput.hdmi1", "tvin", "HDMI 1"),
    ("tvinput.hdmi2", "tvin", "HDMI 2"),
    ("tvinput.hdmi3", "tvin", "HDMI 3"),
    ("tvinput.hdmi4", "tvin", "HDMI 4"),
    ("tvinput.cvbs", "tvin", "AV"),
    ("12", "appl", "Netflix"),
    ("13", "appl", "Prime Video"),
    ("28", "appl", "Pandora"),
    ("2285", "appl", "Hulu"),
    ("13842", "appl", "Vudu"),
    ("2016", "appl", "Crackle"),
    ("61322", "appl", "HBO Max"),
    ("8838", "appl", "Showtime"),
    ("46041", "appl", "Sling TV"),
    ("837", "appl", "YouTube"),
    ("291097", "appl", "Disney Plus"),
    ("151908", "appl", "The Roku Channel"),
    ("19977", "appl", "Spotify"),
    ("34376", "appl", "ESPN"),
]

APPS_XML = (
    "<apps>\n"
    + "".join(
        f'    <app id="{app_id}" type="{kind}" version="1.0.0">{name}</app>\n'
        for app_id, kind, name in APPS
    )
    + "</apps>\n"
)

ACTIVE_APP_XML = """<active-app>
    <app>Roku</app>
</active-app>
"""


class EmulatedRokuTVServer(EmulatedRokuServer):
    """EmulatedRokuServer that says it is a TCL Roku TV."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize, then replace the device description."""
        super().__init__(*args, **kwargs)
        self.roku_info = INFO_TEMPLATE.format(uuid=self.roku_uuid, usn=self.roku_usn)
        self.device_info = DEVICE_INFO_TEMPLATE.format(uuid=self.roku_uuid, usn=self.roku_usn)

    async def _roku_apps_handler(self, request):
        return web.Response(body=APPS_XML, headers={"Content-Type": "text/xml"})

    async def _roku_empty_xml_handler(self, request):
        _LOGGER.debug("%s: %s %s", self.roku_usn, request.method, request.path)
        return web.Response(body="<tv-channels/>", headers={"Content-Type": "text/xml"})

    async def _roku_unknown_handler(self, request):
        """Answer anything else with 200 and log it, to see what remotes send."""
        _LOGGER.info(
            "%s: unhandled %s %s %s",
            self.roku_usn,
            request.method,
            request.path_qs,
            (await request.text())[:200],
        )
        return web.Response()

    async def _setup_app(self) -> web.AppRunner:
        app = web.Application(middlewares=[self._check_remote_and_host_ip])
        r = app.router
        r.add_route("GET", "/", self._roku_root_handler)
        r.add_route("POST", "/keydown/{key}", self._roku_keydown_handler)
        r.add_route("POST", "/keyup/{key}", self._roku_keyup_handler)
        r.add_route("POST", "/keypress/{key}", self._roku_keypress_handler)
        r.add_route("POST", "/launch/{id}", self._roku_launch_handler)
        r.add_route("POST", "/input", self._roku_input_handler)
        r.add_route("POST", "/search", self._roku_search_handler)
        r.add_route("GET", "/query/apps", self._roku_apps_handler)
        r.add_route("GET", "/query/icon/{id}", self._roku_app_icon_handler)
        r.add_route("GET", "/query/active-app", self._roku_active_app_handler)
        r.add_route("GET", "/query/device-info", self._roku_info_handler)
        r.add_route("GET", "/query/tv-channels", self._roku_empty_xml_handler)
        r.add_route("GET", "/query/tv-active-channel", self._roku_empty_xml_handler)
        r.add_route("*", "/{tail:.*}", self._roku_unknown_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        return runner
