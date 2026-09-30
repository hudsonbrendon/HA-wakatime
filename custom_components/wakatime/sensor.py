"""Sensor platform for the Wakatime integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime

from .const import (
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_GOALS,
    CONF_MONITORED_PROJECTS,
    ICON_AVERAGE,
    ICON_BEST_DAY,
    ICON_CATEGORY,
    ICON_CODING,
    ICON_COUNT,
    ICON_DEPENDENCY,
    ICON_EDITOR,
    ICON_GOAL,
    ICON_LANGUAGE,
    ICON_MACHINE,
    ICON_OPERATING_SYSTEM,
    ICON_PRODUCTIVITY,
    ICON_PROJECT,
    ICON_TOTAL,
)
from .entity import WakatimeEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import WakatimeConfigEntry
    from .coordinator import WakatimeDataUpdateCoordinator


def _today_seconds(data: dict) -> int:
    """Return today's coding seconds from the summaries list."""
    for day in data.get("summaries", []):
        grand_total = day.get("grand_total")
        if grand_total:
            return int(grand_total.get("total_seconds", 0))
    return 0


def _today_text(data: dict) -> str | None:
    """Return today's human-readable total."""
    for day in data.get("summaries", []):
        grand_total = day.get("grand_total")
        if grand_total:
            return grand_total.get("text")
    return None


def _top_name(data: dict, key: str) -> str:
    """Return the name of the top stats item for the given key."""
    items = data.get("stats", {}).get(key, [])
    return items[0].get("name", "Unknown") if items else "Unknown"


def _breakdown(data: dict, key: str) -> dict | None:
    """Return up to 10 items as a breakdown attribute."""
    items = data.get("stats", {}).get(key, [])
    if not items:
        return None
    return {
        "breakdown": [
            {
                "name": item.get("name"),
                "percent": item.get("percent"),
                "text": item.get("text"),
            }
            for item in items[:10]
        ]
    }


def _productivity(data: dict) -> str:
    """Map daily average seconds to a coarse productivity level."""
    avg = data.get("stats", {}).get("daily_average", 0)
    if avg > 14400:
        return "High"
    if avg > 7200:
        return "Medium"
    if avg > 0:
        return "Low"
    return "Unknown"


@dataclass(frozen=True, kw_only=True)
class WakatimeSensorEntityDescription(SensorEntityDescription):
    """Describes a Wakatime sensor with value/attribute extractors."""

    value_fn: Callable[[dict], StateType]
    attr_fn: Callable[[dict], dict | None] = lambda _data: None


SENSOR_TYPES: tuple[WakatimeSensorEntityDescription, ...] = (
    WakatimeSensorEntityDescription(
        key="daily_total",
        translation_key="daily_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL,
        icon=ICON_CODING,
        value_fn=_today_seconds,
        attr_fn=lambda d: {"human_readable": _today_text(d)},
    ),
    WakatimeSensorEntityDescription(
        key="range_total",
        translation_key="range_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_TOTAL,
        value_fn=lambda d: int(d.get("stats", {}).get("total_seconds", 0)),
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get("human_readable_total"),
            "range": d.get("stats", {}).get("range"),
        },
    ),
    WakatimeSensorEntityDescription(
        key="daily_average",
        translation_key="daily_average",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_AVERAGE,
        value_fn=lambda d: int(d.get("stats", {}).get("daily_average", 0)),
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get("human_readable_daily_average")
        },
    ),
    WakatimeSensorEntityDescription(
        key="all_time_total",
        translation_key="all_time_total",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon=ICON_TOTAL,
        value_fn=lambda d: int(d.get("all_time", {}).get("total_seconds", 0)),
        attr_fn=lambda d: {"human_readable": d.get("all_time", {}).get("text")},
    ),
    WakatimeSensorEntityDescription(
        key="best_day",
        translation_key="best_day",
        icon=ICON_BEST_DAY,
        value_fn=lambda d: d.get("stats", {}).get("best_day", {}).get("date")
        or "Unknown",
        attr_fn=lambda d: {
            "human_readable": d.get("stats", {}).get("best_day", {}).get("text"),
            "total_seconds": d.get("stats", {})
            .get("best_day", {})
            .get("total_seconds"),
        },
    ),
    WakatimeSensorEntityDescription(
        key="top_language",
        translation_key="top_language",
        icon=ICON_LANGUAGE,
        value_fn=lambda d: _top_name(d, "languages"),
        attr_fn=lambda d: _breakdown(d, "languages"),
    ),
    WakatimeSensorEntityDescription(
        key="top_project",
        translation_key="top_project",
        icon=ICON_PROJECT,
        value_fn=lambda d: _top_name(d, "projects"),
        attr_fn=lambda d: _breakdown(d, "projects"),
    ),
    WakatimeSensorEntityDescription(
        key="top_editor",
        translation_key="top_editor",
        icon=ICON_EDITOR,
        value_fn=lambda d: _top_name(d, "editors"),
        attr_fn=lambda d: _breakdown(d, "editors"),
    ),
    WakatimeSensorEntityDescription(
        key="top_os",
        translation_key="top_operating_system",
        icon=ICON_OPERATING_SYSTEM,
        value_fn=lambda d: _top_name(d, "operating_systems"),
        attr_fn=lambda d: _breakdown(d, "operating_systems"),
    ),
    WakatimeSensorEntityDescription(
        key="top_category",
        translation_key="top_category",
        icon=ICON_CATEGORY,
        value_fn=lambda d: _top_name(d, "categories"),
        attr_fn=lambda d: _breakdown(d, "categories"),
    ),
    WakatimeSensorEntityDescription(
        key="top_machine",
        translation_key="top_machine",
        icon=ICON_MACHINE,
        value_fn=lambda d: _top_name(d, "machines"),
        attr_fn=lambda d: _breakdown(d, "machines"),
    ),
    WakatimeSensorEntityDescription(
        key="top_dependency",
        translation_key="top_dependency",
        icon=ICON_DEPENDENCY,
        value_fn=lambda d: _top_name(d, "dependencies"),
        attr_fn=lambda d: _breakdown(d, "dependencies"),
    ),
    WakatimeSensorEntityDescription(
        key="languages_count",
        translation_key="languages_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_COUNT,
        value_fn=lambda d: len(d.get("stats", {}).get("languages", [])),
    ),
    WakatimeSensorEntityDescription(
        key="projects_count",
        translation_key="projects_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_COUNT,
        value_fn=lambda d: len(d.get("projects", [])),
    ),
    WakatimeSensorEntityDescription(
        key="active_machines",
        translation_key="active_machines",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MACHINE,
        value_fn=lambda d: len(d.get("machines", [])),
        attr_fn=lambda d: {
            "machines": [
                {"name": m.get("name"), "last_seen": m.get("last_seen_at")}
                for m in d.get("machines", [])
            ]
        },
    ),
    WakatimeSensorEntityDescription(
        key="productivity_level",
        translation_key="productivity_level",
        icon=ICON_PRODUCTIVITY,
        value_fn=_productivity,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: WakatimeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wakatime sensors from a config entry."""
    coordinator = entry.runtime_data
    options = entry.options
    enabled = options.get(CONF_ENABLED_SENSORS)

    entities: list[SensorEntity] = [
        WakatimeSensor(coordinator, description)
        for description in SENSOR_TYPES
        if enabled is None or description.key in enabled
    ]

    monitored_goals = options.get(CONF_MONITORED_GOALS)
    entities.extend(
        WakatimeGoalSensor(coordinator, goal_id, goal.get("title") or str(goal_id))
        for goal in coordinator.data.get("goals", [])
        if (goal_id := goal.get("id"))
        and (
            monitored_goals is None
            or (goal.get("title") or str(goal_id)) in monitored_goals
        )
    )

    entities.extend(
        WakatimeProjectSensor(coordinator, name)
        for name in options.get(CONF_MONITORED_PROJECTS) or []
    )

    async_add_entities(entities)


class WakatimeSensor(WakatimeEntity, SensorEntity):
    """A declarative Wakatime sensor."""

    entity_description: WakatimeSensorEntityDescription

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        description: WakatimeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the sensor state."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes, dropping None values."""
        if not self.coordinator.data:
            return None
        attrs = self.entity_description.attr_fn(self.coordinator.data)
        if not attrs:
            return None
        return {k: v for k, v in attrs.items() if v is not None}


class WakatimeGoalSensor(WakatimeEntity, SensorEntity):
    """A sensor representing a single WakaTime goal."""

    _attr_icon = ICON_GOAL

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        goal_id: str,
        title: str,
    ) -> None:
        """Initialize the goal sensor."""
        super().__init__(coordinator)
        self._goal_id = goal_id
        self._attr_name = title
        self._attr_unique_id = f"{coordinator.entry.entry_id}_goal_{goal_id}"

    def _goal(self) -> dict:
        if not self.coordinator.data:
            return {}
        for goal in self.coordinator.data.get("goals", []):
            if goal.get("id") == self._goal_id:
                return goal
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the goal's status."""
        goal = self._goal()
        return goal.get("average_status") or goal.get("status") or "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return goal metadata."""
        goal = self._goal()
        if not goal:
            return None
        attrs = {
            "title": goal.get("title"),
            "type": goal.get("type"),
            "is_enabled": goal.get("is_enabled"),
            "target_seconds": goal.get("seconds"),
            "delta": goal.get("delta"),
            "range": goal.get("range"),
        }
        return {k: v for k, v in attrs.items() if v is not None}


class WakatimeProjectSensor(WakatimeEntity, SensorEntity):
    """A sensor tracking coding time for one project over the configured range."""

    _attr_icon = ICON_PROJECT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: WakatimeDataUpdateCoordinator,
        project_name: str,
    ) -> None:
        """Initialize the project sensor."""
        super().__init__(coordinator)
        self._project_name = project_name
        self._attr_name = project_name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_project_{project_name}"

    def _project(self) -> dict:
        if not self.coordinator.data:
            return {}
        for project in self.coordinator.data.get("stats", {}).get("projects", []):
            if project.get("name") == self._project_name:
                return project
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the project's coding seconds for the range."""
        return int(self._project().get("total_seconds", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return project metadata."""
        project = self._project()
        if not project:
            return None
        return {
            "human_readable": project.get("text"),
            "percent": project.get("percent"),
        }
