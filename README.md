<p align="center">
  <img src="custom_components/wakatime/brand/logo@2x.png" alt="Wakatime" height="128">
</p>

# Wakatime Integration for Home Assistant

[![Tests](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/tests.yml)
[![Hassfest](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/hassfest.yml/badge.svg)](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/hassfest.yml)
[![HACS](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/HA-wakatime/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/HA-wakatime?sort=semver)](https://github.com/hudsonbrendon/HA-wakatime/releases)
[![Downloads](https://img.shields.io/github/downloads/hudsonbrendon/HA-wakatime/total)](https://github.com/hudsonbrendon/HA-wakatime/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.2.4%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/hudsonbrendon/HA-wakatime)](LICENSE)

This Home Assistant integration allows you to monitor your coding activity through the Wakatime API.

## Features

- Daily coding time sensor
- Top language information
- Project tracking
- Editor usage statistics
- Operating system details
- Multi-language support (English, Brazilian Portuguese)

## Installation

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hudsonbrendon&repository=HA-wakatime&category=integration)
[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wakatime)

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations
3. Click on the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Search for "Wakatime" and install it

### Manual Installation

1. Download the latest release from the releases page
2. Extract the `custom_components/wakatime` folder into your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. In Home Assistant, go to Configuration > Integrations
2. Click "Add Integration" and search for "Wakatime"
3. Follow the configuration steps:
   - Enter your Wakatime API key (You can find this in your Wakatime account settings)

## API Key

To obtain your Wakatime API key:

1. Log in to your Wakatime account
2. Go to [Account Settings](https://wakatime.com/settings/account)
3. Find your API Key in the "API Key" section

## Sensors

Static sensors (each can be toggled on/off in the integration **Options**):

- **Daily Total** — coding time today (seconds, attr: human-readable)
- **Range Total** — total coding time over the selected range
- **Daily Average** — average coding time per day over the range
- **All-Time Total** — total coding time ever recorded
- **Best Day** — date of your most productive day (attrs: total seconds, text)
- **Top Language / Project / Editor / Operating System / Category / Machine / Dependency** — each with a `breakdown` attribute listing the top 10
- **Languages Count / Projects Count / Active Machines** — counters
- **Productivity Level** — High / Medium / Low derived from your daily average

Dynamic sensors:

- **Goal sensors** — one per WakaTime goal you choose to monitor, state = goal status
- **Project sensors** — one per project you choose to monitor, state = coding time over the range

## Options

After adding the integration, open its **Configure** dialog to set:

- **Update interval** (5–1440 minutes, default 30)
- **Stats range** (last 7 days / 30 days / 6 months / year / all time)
- **Enabled sensors** (pick which static sensors to create)
- **Monitored goals** and **Monitored projects**

Changing options reloads the integration automatically.

## Automations

Example automation to notify you when you've been coding for too long:

```yaml
automation:
  - alias: "Coding Break Reminder"
    trigger:
      platform: numeric_state
      entity_id: sensor.<your_wakatime_user>_daily_total
      above: 14400  # 4 hours in seconds
    action:
      service: notify.mobile_app
      data:
        message: "You've been coding for over 4 hours today! Time for a break."
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
