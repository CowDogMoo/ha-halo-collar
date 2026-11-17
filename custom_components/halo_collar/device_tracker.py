from __future__ import annotations

try:
    from homeassistant.components.device_tracker import TrackerEntity
except ImportError:  # Home Assistant 2024.12 compatibility
    from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType

from .const import DOMAIN
from .entity import HaloEntity
from .helpers import TrackerLocation, indoors_on_wifi, tracker_location


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        HaloPetTracker(coordinator, entry, collar) for collar in coordinator.data.collars
    )


if hasattr(TrackerEntity, "in_zones"):
    from homeassistant.components.zone import ENTITY_ID_HOME

    class _IndoorHomeTrackerMixin:
        @property
        def in_zones(self) -> list[str] | None:
            """Assume Home on indoor Wi-Fi only when Halo reports no position."""
            collar = self.collar
            if collar is not None and indoors_on_wifi(collar) and self._location is None:
                return [ENTITY_ID_HOME]
            return None

else:
    from homeassistant.const import STATE_HOME

    class _IndoorHomeTrackerMixin:
        @property
        def location_name(self) -> str | None:
            """Use the legacy location API on older supported HA releases."""
            collar = self.collar
            if collar is not None and indoors_on_wifi(collar) and self._location is None:
                return STATE_HOME
            return None


class HaloPetTracker(_IndoorHomeTrackerMixin, HaloEntity, TrackerEntity):
    _attr_name = None
    _attr_icon = "mdi:dog"

    def __init__(self, coordinator, entry, collar) -> None:
        super().__init__(coordinator, entry, collar)
        self._attr_unique_id = f"{self._collar_id}_pet_tracker"

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def _location(self) -> TrackerLocation | None:
        return tracker_location(self.collar, self.pet)

    @property
    def latitude(self) -> float | None:
        location = self._location
        return None if location is None else location["latitude"]

    @property
    def longitude(self) -> float | None:
        location = self._location
        return None if location is None else location["longitude"]

    @property
    def location_accuracy(self) -> float:
        location = self._location
        if location is None or location["accuracy"] is None:
            return 0
        return location["accuracy"]

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        location = self._location
        if location is None or location["reported_at"] is None:
            return None
        return {"location_reported_at": location["reported_at"].isoformat()}
