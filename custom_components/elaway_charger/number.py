"""Support for Elaway number configuration entities."""
from __future__ import annotations

import logging
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elaway number entities based on coordinator data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    data = coordinator.data if isinstance(coordinator.data, dict) else {}
    root_data = data.get("data", data) if "data" in data else data
    
    if root_data.get("is_light_intensity_supported", False):
        async_add_entities([
            ElawayLightIntensityNumber(coordinator, entry, device_info)
        ], True)


def get_root_data(coordinator) -> dict:
    """Helper method to safely pull and unpack root payload contexts while auto-extracting EVSE ID strings."""
    if not coordinator or not coordinator.data:
        return {}
    
    data = coordinator.data
    root_data = data.get("data", data) if isinstance(data, dict) else {}
    
    if isinstance(data, list) and len(data) > 0:
        root_data = data[0]

    if root_data and hasattr(coordinator, "api") and coordinator.api.get("evse_id") is None:
        evse_uid = root_data.get("id") or root_data.get("evses", [{}])[0].get("id")
        if evse_uid:
            coordinator.api.evse_id = str(evse_uid)

    return root_data


class ElawayLightIntensityNumber(CoordinatorEntity, NumberEntity):
    """Representation of a number entity to control Elaway charger status LED brightness."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_info):
        """Initialize the light intensity config selector."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Status Light Intensity"
        self._attr_unique_id = f"{entry.entry_id}_light_intensity"
        self._attr_icon = "mdi:brightness-6"
        
        self._attr_native_min_value = 1.0
        self._attr_native_max_value = 5.0
        self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        """Return the current light intensity step state from the coordinator."""
        try:
            val = get_root_data(self.coordinator).get("light_intensity")
            return float(val) if val is not None else 5.0
        except (TypeError, ValueError):
            return 5.0

    async def async_set_native_value(self, value: float) -> None:
        """Transmit the requested dimming tier parameter changes over back to the API."""
        intensity_target = int(value)
        _LOGGER.debug("Sending command to shift status illumination tier target to: %s", intensity_target)
        
        try:
            await self.coordinator.api.async_patch_settings({"light_intensity": intensity_target})
            root_data = get_root_data(self.coordinator)
            if root_data:
                root_data["light_intensity"] = intensity_target
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("Failed to commit dimming frame parameters to backend database API: %s", err)
