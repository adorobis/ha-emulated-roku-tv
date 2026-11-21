# Emulated Roku TV for Home Assistant

[![Validate][validate-badge]][validate-url]

Turns the buttons of a Logitech Harmony remote (or any remote/app that controls a Roku over
the network) into Home Assistant events. It does the same job as the core
[Emulated Roku](https://www.home-assistant.io/integrations/emulated_roku/) integration, but
the emulated device presents itself as a **Roku TV**, not a Roku 4 player. That gives you
about 40 usable buttons instead of about 12.

## Why

Harmony picks a device profile based on what the Roku reports about itself. The core
integration reports a *Roku 4*, and Harmony's Roku 4 profile:

- sends only about 12 distinct keys: Stop and Pause arrive as `Play`, Exit as `Home`,
  Options as `Info`, and Sleep as `PowerOff`
- sends **nothing at all** for the app buttons (Netflix, Hulu, Amazon …) or PageUp/PageDown

With a Roku TV profile, Harmony also sends the digit keys, volume, channel, power and input
keys, which makes it practical to map, for example, radio presets or scenes to buttons.

## Keys

Tested with a Harmony Hub and the Roku TV profile Harmony picked from a Wi-Fi scan. All of
these arrive as `type: keypress`:

| Group | `key` |
|---|---|
| Digits | `Lit_0` … `Lit_9`, `Lit_-` |
| Navigation | `Up` `Down` `Left` `Right` `Select` `Back` `Home` `BackSpace` |
| Playback | `Play` (Play and Pause), `Rev` `Fwd` `InstantReplay` |
| TV | `VolumeUp` `VolumeDown` `VolumeMute` `ChannelUp` `ChannelDown` `PowerOn` `PowerOff` |
| Inputs | `InputTuner` `InputHDMI1` … `InputHDMI4` `InputAV1` `InputUSB` |
| Other | `Search` `Info` |

Held buttons may also send `keydown` / `keyup`. The device lists a set of real Roku channel
ids (Netflix 12, Prime Video 13, Hulu 2285 …) and the TV inputs as installed. A remote that
launches channels then sends `type: launch` with `app_id`. Harmony read the list in testing
but did not send launches, so don't rely on app buttons.

## Installation

1. In HACS, add `https://github.com/adorobis/ha-emulated-roku-tv` as a custom repository
   (category: Integration), install **Emulated Roku TV** and restart Home Assistant.
   Or copy `custom_components/emulated_roku_tv` into your `config/custom_components`.
2. Go to **Settings → Devices & services → Add integration → Emulated Roku TV**.
3. Enter a **name**, which the remote shows and events carry as `source_name`, and a
   **port**. The default is 8070; use a port that no other emulated Roku uses. Add one entry
   per emulated TV you need.

Home Assistant must be able to receive SSDP (UDP 1900) and the chosen TCP port from the
remote, so with Docker use host networking.

### Harmony

In the Harmony app: **Harmony Setup → Add & Edit Devices & Activities → Devices → Add Device
→ Scan Wi-Fi**. The emulated device appears as a TCL Roku TV with your name. Add it to an
activity and assign its commands to buttons or to screen (soft) buttons.

A Roku TV that you add by manufacturer/model instead of the Wi-Fi scan usually gets an IR
profile, and IR commands never reach Home Assistant.

## Events

```yaml
event_type: roku_command
data:
  source_name: Roku TV Presets   # the name of the entry
  type: keypress                 # keydown, keyup, keypress or launch
  key: Lit_3                     # for launch: app_id
```

This is the same event as the core integration's, so existing blueprints and automations
work. Filter on `source_name` to tell the emulated devices apart.

### Example: digit keys recall a preset

```yaml
triggers:
  - trigger: event
    event_type: roku_command
    event_data: {source_name: Roku TV Presets, type: keypress, key: Lit_1}
  - trigger: event
    event_type: roku_command
    event_data: {source_name: Roku TV Presets, type: keypress, key: Lit_2}
  # … up to Lit_9
actions:
  - action: number.set_value
    target: {entity_id: number.living_room_preset}
    data:
      value: "{{ trigger.event.data.key | replace('Lit_', '') | int }}"
```

## Running next to the core integration

This integration has its own domain and its own servers, so it doesn't change existing
core Emulated Roku instances or the devices Harmony already knows. Both can run at the same
time as long as each instance has its own port.

## Finding out what a remote sends

Requests that the emulated device doesn't handle are answered with `200 OK` and logged at
INFO level (`… unhandled POST /something`). To see them, enable:

```yaml
logger:
  logs:
    custom_components.emulated_roku_tv: info
```

## Credits

The icon is original artwork made for this project. Roku is a trademark of Roku, Inc.; this
project is not affiliated with or endorsed by Roku.


Built on the [emulated_roku](https://github.com/mindigmarton/emulated_roku) library by
@mindigmarton, which the core integration also uses.

[validate-badge]: https://github.com/adorobis/ha-emulated-roku-tv/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/adorobis/ha-emulated-roku-tv/actions/workflows/validate.yml
