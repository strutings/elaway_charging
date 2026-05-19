"""Support for Elaway switch configuration entities."""
from __future__ import annotations

import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
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
        # Switch 1: Permanent Cable Lock Mode
        ElawayCableLockSwitch(coordinator, entry, device_info),
        # Switch 2: Free Charging / Plug & Charge (No RFID token required)
        ElawayFreeChargingSwitch(coordinator, entry, device_info),
    ]

    async_add_entities(switches, True)


def get_root_data(coordinator_data):
    """Helper method to safely pull the root data dictionary payload object."""
    if not coordinator_data:
        return {}
    if isinstance(coordinator_data, dict):
        return coordinator_data.get("data", coordinator_data)
    elif isinstance(coordinator_data, list) and len(coordinator_data) > 0:
        return coordinator_data[0]
    return {}


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
        # Ofte returnert som "always_locked" eller lignende flagg i Ampeco-API-et
        return bool(get_root_data(self.coordinator.data).get("cable_lock_mode", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable permanent cable locking mode via API."""
        _LOGGER.debug("Enabling permanent cable lock for Elaway Charger")
        try:
            # TODO: Koble mot API-klienten din, f.eks:
            # await self.coordinator.api.set_charger_settings({"cable_lock_mode": True})
            
            root_data = get_root_data(self.coordinator.data)
            if root_data:
                root_data["cable_lock_mode"] = True
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to lock cable via API: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable permanent cable locking mode via API."""
        _LOGGER.debug("Disabling permanent cable lock for Elaway Charger")
        try:
            root_data = get_root_data(self.coordinator.data)
            if root_data:
                root_data["cable_lock_mode"] = False
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to unlock cable via API: %s", err)


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
        # Vi inverterer logikken her for brukervennlighet:
        # PÅ = Autentisering kreves. AV = Fri lading (Plug & Charge).
        return bool(get_root_data(self.coordinator.data).get("requires_authorization", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Require RFID/App authorization to initiate charges."""
        _LOGGER.debug("Enabling authorization requirement for Elaway Charger")
        try:
            root_data = get_root_data(self.coordinator.data)
            if root_data:
                root_data["requires_authorization"] = True
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to enable authorization requirement: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable authorization requirement, enabling direct plug-and-charge free access."""
        _LOGGER.debug("Disabling authorization requirement (Free Charging Mode)")
        try:
            root_data = get_root_data(self.coordinator.data)
            if root_data:
                root_data["requires_authorization"] = False
                self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to enable free charging mode: %s", err)
