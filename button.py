"""Support for Elaway button entities."""
from __future__ import annotations

import logging
import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

def get_charger_id(coordinator) -> str:
    """Helper to safely pull the charger ID from coordinator telemetry."""
    if not coordinator or not coordinator.data:
        return "22408"
    data = coordinator.data
    root_data = data.get("data", data) if isinstance(data, dict) else {}
    if isinstance(data, list) and len(data) > 0:
        root_data = data[0]
    return str(root_data.get("id", "22408"))

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all Elaway buttons."""
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
        ElawayStartButton(coordinator, api, entry, device_info),
        ElawayStopButton(coordinator, api, entry, device_info),
        ElawayRebootButton(coordinator, api, entry, device_info)
    ], True)


class ElawayStartButton(CoordinatorEntity, ButtonEntity):
    """Button to start a charging session."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Start Charging"
        self._attr_unique_id = f"{entry.entry_id}_start_charging_button"
        self._attr_icon = "mdi:play-circle"

    async def async_press(self) -> None:
        try:
            token = await self.api.async_get_valid_credentials()
            url = f"{self.api.ampeco_base_url}/session/start"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"evseId": int(self.api.evse_id)}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status in [200, 201, 202]:
                        _LOGGER.info("Charging started!")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error starting charge: %s", err)


class ElawayStopButton(CoordinatorEntity, ButtonEntity):
    """Button to stop an active charging session."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Stop Charging"
        self._attr_unique_id = f"{entry.entry_id}_stop_charging_button"
        self._attr_icon = "mdi:stop-circle"

    async def async_press(self) -> None:
        try:
            token = await self.api.async_get_valid_credentials()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            charger_id = get_charger_id(self.coordinator)
            
            # Finn sesjon ID
            data = self.coordinator.data
            root = data.get("data", data) if isinstance(data, dict) else data
            session_id = None
            if isinstance(root, dict) and "evses" in root and root["evses"]:
                session_id = root["evses"][0].get("session", {}).get("id")

            if session_id:
                stop_url = f"{self.api.ampeco_base_url}/session/{session_id}/end"
                async with aiohttp.ClientSession() as session:
                    await session.post(stop_url, headers=headers)
                await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error stopping charge: %s", err)


class ElawayRebootButton(CoordinatorEntity, ButtonEntity):
    """Button to restart the charger."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Restart Charger"
        self._attr_unique_id = f"{entry.entry_id}_reboot_button"
        self._attr_icon = "mdi:restart"
        self._attr_device_class = "restart"

    async def async_press(self) -> None:
        charger_id = get_charger_id(self.coordinator)
        try:
            token = await self.api.async_get_valid_credentials()
            url = f"{self.api.ampeco_base_url}/personal/charge-points/{charger_id}/reboot"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={}) as resp:
                    if resp.status in [200, 201, 202, 204]:
                        _LOGGER.info("Reboot command sent.")
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error during reboot: %s", err)
