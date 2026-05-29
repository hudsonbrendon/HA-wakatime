"""Constants for the Wakatime integration."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "wakatime"
NAME = "Wakatime"
ATTRIBUTION = "Data provided by WakaTime"
BASE_URL = "https://wakatime.com/api/v1"

# Config / options keys
CONF_SCAN_INTERVAL = "scan_interval"
CONF_STATS_RANGE = "stats_range"
CONF_ENABLED_SENSORS = "enabled_sensors"
CONF_MONITORED_GOALS = "monitored_goals"
CONF_MONITORED_PROJECTS = "monitored_projects"

# Defaults / bounds
DEFAULT_SCAN_INTERVAL = 30  # minutes
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 1440
DEFAULT_STATS_RANGE = "last_7_days"

STATS_RANGES = [
    "last_7_days",
    "last_30_days",
    "last_6_months",
    "last_year",
    "all_time",
]

# Icons
ICON_CODING = "mdi:code-braces"
ICON_LANGUAGE = "mdi:code-tags"
ICON_PROJECT = "mdi:folder"
ICON_EDITOR = "mdi:laptop"
ICON_OPERATING_SYSTEM = "mdi:monitor"
ICON_CATEGORY = "mdi:shape"
ICON_MACHINE = "mdi:desktop-tower"
ICON_DEPENDENCY = "mdi:package-variant"
ICON_AVERAGE = "mdi:chart-line"
ICON_TOTAL = "mdi:sigma"
ICON_PRODUCTIVITY = "mdi:trending-up"
ICON_BEST_DAY = "mdi:trophy"
ICON_GOAL = "mdi:bullseye-arrow"
ICON_COUNT = "mdi:counter"
