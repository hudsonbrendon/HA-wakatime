"""Base entity for the Wakatime integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME
from .coordinator import WakatimeDataUpdateCoordinator


class WakatimeEntity(CoordinatorEntity[WakatimeDataUpdateCoordinator]):
    """Base class for all Wakatime entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: WakatimeDataUpdateCoordinator) -> None:
        """Initialize the entity and its device."""
        super().__init__(coordinator)
        user = coordinator.data.get("user", {}) if coordinator.data else {}
        user_id = user.get("id") or coordinator.entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(user_id))},
            name=user.get("display_name") or user.get("username") or NAME,
            manufacturer="WakaTime",
            model="API",
            configuration_url="https://wakatime.com/dashboard",
        )
