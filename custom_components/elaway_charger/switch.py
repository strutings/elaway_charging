"""Support for Elaway switch configuration entities."""
from __future__ import annotations

import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity
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
    """Set up Elaway switches based on coordinator data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    switches = [
        ElawayCableLockSwitch(coordinator, entry, device_info),
        ElawayFreeChargingSwitch(coordinator, entry, device_info),
    ]

    async_add_entities(switches, True)


def get_root_data(coordinator) -> dict:
    """Helper method to safely pull and unpack root payload contexts while auto-extracting EVSE ID strings."""
    if not coordinator or not coordinator.data:
        return {}
    
    data = coordinator.data
    root_data = data.get("data", data) if isinstance(data, dict) else {}
    
    if isinstance(data, list) and len(data) > 0:
        root_data = data[0]

    # Dynamically bind the target infrastructure ID to the API class instances if vacant
    if root_data and hasattr(coordinator, "api") and coordinator.api.get("evse_id") is None:
        evse_uid = root_data.get("id") or root_data.get("evses", [{}])[0].get("id")
        if evse_uid:
            coordinator.api.evse_id = str(evse_uid)

    return root_data


class ElawayCableLockSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to permanently lock or unlock the charging cable to the station."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_info):
        """Initialize the cable lock switch."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Permanent Cable Lock"
        self._attr_unique_id = f"{entry.entry_id}_cable_lock"
        self._attr_icon = "mdi:lock"

    @property
    def is_on(self) -> bool:
        """Return True if the cable is configured to stay permanently locked."""
        return bool(get_root_data(self.coordinator).get("cable_lock_mode", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable permanent cable locking mode via API."""
        _LOGGER.debug("Sending command to lock charging cable frame permanently")
        try:
            await self.coordinator.api.async_patch_settings({"cable_lock_mode": True})
            root_data = get_root_data(self.coordinator)
            if root_data:
                root_data["cable_lock_mode"] = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to commit permanent cable lock profile parameters: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable permanent cable locking mode via API."""
        _LOGGER.debug("Sending command to unlock charging cable clamp bindings")
        try:
            await self.coordinator.api.async_patch_settings({"cable_lock_mode": False})
            root_data = get_root_data(self.coordinator)
            if root_data:
                root_data["cable_lock_mode"] = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to release permanent cable lock profile parameters: %s", err)


class ElawayFreeChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable free access mode (charging without requiring an RFID token)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_info):
        """Initialize the free charging access switch."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Authentication Required"
        self._attr_unique_id = f"{entry.entry_id}_free_charging"
        self._attr_icon = "mdi:rfid"

    @property
    def is_on(self) -> bool:
        """Return True if authentication is currently required."""
        return bool(get_root_data(self.coordinator).get("requires_authorization", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Require RFID/App authorization to initiate charges."""
        _LOGGER.debug("Sending command to enforce access token challenge locks")
        try:
            await self.coordinator.api.async_patch_settings({"requires_authorization": True})
            root_data = get_root_data(self.coordinator)
            if root_data:
                root_data["requires_authorization"] = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to restrict authentication access boundaries: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable authorization requirement, enabling direct plug-and-charge free access."""
        _LOGGER.debug("Sending command to open free charging authorization loops (Plug & Charge)")
        try:
            await self.coordinator.api.async_patch_settings({"requires_authorization": False})
            root_data = get_root_data(self.coordinator)
            if root_data:
                root_data["requires_authorization"] = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to deploy free open-access plug configuration: %s", err)
