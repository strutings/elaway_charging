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

    async_add_entities([
        ElawayCableLockSwitch(coordinator, api, entry.entry_id, device_info),
        ElawayFreeChargingSwitch(coordinator, api, entry.entry_id, device_info),
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


async def _send_ampeco_patch(api, charger_id: str, payload_dict: dict) -> bool:
    """Helper to send PATCH directly to the charge point."""
    try:
        token = await api.async_get_valid_credentials()
        url = f"{api.ampeco_base_url}/personal/charge-points/{charger_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        _LOGGER.debug("Sender PATCH: URL=%s | Payload=%s", url, payload_dict)
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload_dict) as resp:
                if resp.status not in [200, 204]:
                    error_msg = await resp.text()
                    _LOGGER.error("Ampeco PATCH feilet med status (%s): %s", resp.status, error_msg)
                    return False
                
                _LOGGER.debug("Ampeco PATCH suksess (Status %s)", resp.status)
                return True
    except Exception as e:
        _LOGGER.error("Krasj under sending av PATCH: %s", e)
        return False


class ElawayCableLockSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to permanently lock or unlock the charging cable to the station."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Permanent Cable Lock"
        self._attr_unique_id = f"{entry_id}_cable_lock"
        self._attr_icon = "mdi:lock"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("connector_lock", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        if await _send_ampeco_patch(self.api, str(charger_id), {"connector_lock": True}):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        if await _send_ampeco_patch(self.api, str(charger_id), {"connector_lock": False}):
            await self.coordinator.async_request_refresh()


class ElawayFreeChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable free access mode."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Authentication Required"
        self._attr_unique_id = f"{entry_id}_free_charging"
        self._attr_icon = "mdi:rfid"

    @property
    def is_on(self) -> bool:
        return bool(get_root_data(self.coordinator).get("requires_authorization", True))

    async def async_turn_on(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        if await _send_ampeco_patch(self.api, str(charger_id), {"requires_authorization": True}):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        if await _send_ampeco_patch(self.api, str(charger_id), {"requires_authorization": False}):
            await self.coordinator.async_request_refresh()
