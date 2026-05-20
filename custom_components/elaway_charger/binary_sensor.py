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
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )
    
    binary_sensors = [
        # Sensor 1: Cable Connection State (Based on EVSE status)
        ElawayBinarySensor(
            coordinator, entry, "cable_connected", "Cable Connected", BinarySensorDeviceClass.PLUG,
            lambda d: get_first_evse(d).get('status') in ["preparing", "charging", "suspendedEV", "suspendedEVSE", "finishing"], 
            device_info
        ),
        # Sensor 2: Authorization State Requirement
        ElawayBinarySensor(
            coordinator, entry, "auth_required", "Authentication Required", None,
            lambda d: get_root_data(d).get('requires_authorization', False), device_info, icon="mdi:lock"
        ),
        # Sensor 3: Network Connection Status
        ElawayBinarySensor(
            coordinator, entry, "charger_status", "Charger Status", BinarySensorDeviceClass.CONNECTIVITY,
            lambda d: get_root_data(d).get('status') != "unavailable", 
            device_info
        ),
        # Sensor 4: Rebooting status
        ElawayBinarySensor(
            coordinator, entry, "is_rebooting", "Is Rebooting", None,
            lambda d: get_root_data(d).get('is_rebooting', False), device_info, icon="mdi:restart"
        ),
        # Sensor 5: Firmware updating status
        ElawayBinarySensor(
            coordinator, entry, "is_firmware_updating", "Is Firmware Updating", BinarySensorDeviceClass.UPDATE,
            lambda d: get_root_data(d).get('is_firmware_updating', False), device_info
        ),
    ]
    
    async_add_entities(binary_sensors, True)


def get_root_data(coordinator_data):
    """Helper method to safely pull the root data dictionary payload object."""
    if not coordinator_data:
        return {}
    if isinstance(coordinator_data, dict):
        return coordinator_data.get("data", coordinator_data)
    elif isinstance(coordinator_data, list) and len(coordinator_data) > 0:
        return coordinator_data[0]
    return {}


def get_first_evse(coordinator_data):
    """Helper to safely extract the first EVSE object."""
    return get_root_data(coordinator_data).get("evses", [{}])[0]


class ElawayBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Elaway Binary Sensor tied to the core device identifier."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, device_class, value_fn, device_info, icon=None):
        """Initialize the binary sensor."""
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
        """Return True if the binary sensor is active/on."""
        if not self.coordinator or not self.coordinator.data:
            return None
        try:
            return bool(self._value_fn(self.coordinator.data))
        except (KeyError, IndexError, TypeError):
            return False
