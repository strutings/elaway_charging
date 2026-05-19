"""Support for Elaway number configuration entities."""
from __future__ import annotations

import logging
from homeassistant.components.number import NumberEntity, NumberDeviceClass
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

    # Only add the sensor if the API explicitly reports hardware support
    data = coordinator.data if isinstance(coordinator.data, dict) else {}
    root_data = data.get("data", data) if "data" in data else data
    
    if root_data.get("is_light_intensity_supported", False):
        async_add_entities([
            ElawayLightIntensityNumber(coordinator, entry, device_info)
        ], True)


def get_root_data(coordinator_data):
    """Helper method to safely pull the root data dictionary payload object."""
    if not coordinator_data:
        return {}
    if isinstance(coordinator_data, dict):
        return coordinator_data.get("data", coordinator_data)
    elif isinstance(coordinator_data, list) and len(coordinator_data) > 0:
        return coordinator_data[0]
    return {}


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
        
        # Configuration properties for the slider interface
        self._attr_native_min_value = 1.0
        self._attr_native_max_value = 5.0
        self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        """Return the current light intensity step state from the coordinator."""
        try:
            val = get_root_data(self.coordinator.data).get("light_intensity")
            return float(val) if val is not None else 5.0
        except (TypeError, ValueError):
            return 5.0

    async def async_set_native_value(self, value: float) -> None:
        """Transmit the requested dimming tier parameter changes over back to the API."""
        intensity_target = int(value)
        _LOGGER.debug("Setting Elaway LED light intensity to: %s", intensity_target)
        
        try:
            # TODO: Integrate this hook with your actual API backend client module logic.
            # Example implementation assumption pattern:
            # await self.coordinator.api.set_light_intensity(self._attr_unique_id, intensity_target)
            
            # Optimistically trigger local data state update loops 
            root_data = get_root_data(self.coordinator.data)
            if root_data:
                root_data["light_intensity"] = intensity_target
                self.async_write_ha_state()
                
            # Request coordinator to refresh remote payload buffers
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("Failed to push light intensity adjustments to Elaway API: %s", err)
