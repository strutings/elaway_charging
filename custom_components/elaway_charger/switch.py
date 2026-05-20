"""Support for Elaway switch configuration entities."""
from __future__ import annotations

import logging
import aiohttp
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
    """Set up Elaway switches based on coordinator and api data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    api = entry_data["api"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    # Fallback charger ID if not found in data
    FALLBACK_CHARGER_ID = "22408"

    async_add_entities([
        ElawayCableLockSwitch(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
        ElawayFreeChargingSwitch(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
        ElawayPlugAndChargeSwitch(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
        ElawaySmartChargingSwitch(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
    ], True)


def get_root_data(coordinator) -> dict:
    """Helper method to safely pull and unpack root payload contexts."""
    if not coordinator or not coordinator.data:
        return {}
    data = coordinator.data
    root_data = data.get("data", data) if isinstance(data, dict) else {}
    if isinstance(data, list) and len(data) > 0:
        root_data = data[0]
    return root_data


class ElawayCableLockSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to permanently lock or unlock the charging cable to the station."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Permanent Cable Lock"
        self._attr_unique_id = f"{entry_id}_cable_lock"
        self._attr_icon = "mdi:lock"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("connector_lock", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"connector_lock": True}):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"connector_lock": False}):
            await self.coordinator.async_request_refresh()


class ElawayFreeChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable free access mode."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Authentication Required"
        self._attr_unique_id = f"{entry_id}_free_charging"
        self._attr_icon = "mdi:rfid"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("requires_authorization", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"requires_authorization": True}):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"requires_authorization": False}):
            await self.coordinator.async_request_refresh()


class ElawayPlugAndChargeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Plug & Charge."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Plug & Charge"
        self._attr_unique_id = f"{entry_id}_plug_and_charge"
        self._attr_icon = "mdi:ev-plug-type2"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("plug_and_charge", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"plug_and_charge": True}):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"plug_and_charge": False}):
            await self.coordinator.async_request_refresh()


class ElawaySmartChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Smart Charging."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Smart Charging"
        self._attr_unique_id = f"{entry_id}_smart_charging"
        self._attr_icon = "mdi:auto-fix"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("smart_charging_enabled", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        payload = {
            "smart_charging_enabled": True,
            "smart_charging": {"enabled": True}
        }
        if await self.api.async_patch_charger(str(charger_id), payload):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        payload = {
            "smart_charging_enabled": False,
            "smart_charging": {"enabled": False}
        }
        if await self.api.async_patch_charger(str(charger_id), payload):
            await self.coordinator.async_request_refresh()
