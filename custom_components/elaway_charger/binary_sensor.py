"""Support for Elaway binary sensors (On/Off) linked to a single device context."""
from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors based on the shared data update coordinator."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    
    # We construct the identical device wrapper object used in sensor.py and button.py
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )
    
    binary_sensors = [
        # Sensor 1: Cable Connection State
        ElawayBinarySensor(
            coordinator, entry, "cable_connected", "Cable Connected", BinarySensorDeviceClass.PLUG,
            lambda d: d['data']['evses'][0]['session']['isCableConnected'], device_info
        ),
        # Sensor 2: Authorization State Requirement
        ElawayBinarySensor(
            coordinator, entry, "auth_required", "Authentication Required", None,
            lambda d: d['data']['evses'][0]['auth_required'], device_info, icon="mdi:lock"
        ),
        # Sensor 3: Network Connection Status (Online / Offline)
        ElawayBinarySensor(
            coordinator, entry, "charger_status", "Charger Status", BinarySensorDeviceClass.CONNECTIVITY,
            lambda d: d['data']['status'].lower() == "online", device_info
        ),
    ]
    
    async_add_entities(binary_sensors, True)


class ElawayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Elaway Binary Sensor tied to the core device identifier."""

    # Tells Home Assistant to automatically prepend the Device name cleanly in the UI registry layout loop
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, device_class, value_fn, device_info, icon=None):
        """Initialize the binary sensor integration block structure."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._value_fn = value_fn
        self._attr_device_info = device_info
        
        if icon:
            self._attr_icon = icon
            
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is active/on contextually based on lambda data parsers."""
        if not self.coordinator or not self.coordinator.data:
            return None
        try:
            return bool(self._value_fn(self.coordinator.data))
        except (KeyError, IndexError, TypeError):
            return False
