"""Constants for the Wakatime integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "wakatime"
NAME = "Wakatime"
SCAN_INTERVAL = 30  # Minutes

# Icons
ICON_CODING = "mdi:code-braces"
ICON_LANGUAGE = "mdi:code-tags"
ICON_PROJECT = "mdi:folder"
ICON_EDITOR = "mdi:laptop"
ICON_OPERATING_SYSTEM = "mdi:laptop"
ICON_CATEGORY = "mdi:shape"
ICON_MACHINE = "mdi:desktop-tower"
ICON_BRANCH = "mdi:source-branch"
ICON_TIME = "mdi:clock-outline"
ICON_WEEKLY = "mdi:calendar-week"
ICON_PRODUCTIVITY = "mdi:trending-up"
ICON_ACTIVE_TIME = "mdi:clock-time-eight"
ICON_STREAK = "mdi:fire"

CONF_BASE_URL = "base_url"
