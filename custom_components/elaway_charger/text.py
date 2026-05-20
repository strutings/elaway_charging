"""Support for Elaway text entities to control smart charging schedules."""
from __future__ import annotations

import logging
from homeassistant.components.text import TextEntity
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
    """Set up Elaway text entities based on coordinator data."""
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
        ElawaySmartChargingTime(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info, "start_time", "Smart Charging Start"),
        ElawaySmartChargingTime(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info, "end_time", "Smart Charging End")
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


class ElawaySmartChargingTime(CoordinatorEntity, TextEntity):
    """Representation of a text entity to control Elaway smart charging schedule times."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info, key, name):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._key = key
        self._attr_device_info = device_info
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_smart_{key}"
        self._attr_icon = "mdi:clock-outline"
        self._attr_pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$" # HH:MM or HH:MM:SS

    @property
    def native_value(self) -> str | None:
        smart_charging = get_root_data(self.coordinator).get("smart_charging", {})
        if isinstance(smart_charging, dict):
            return smart_charging.get(self._key)
        return None

    async def async_set_value(self, value: str) -> None:
        """Update the smart charging time."""
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        payload = {
            "smart_charging": {
                self._key: value
            }
        }
        if await self.api.async_patch_charger(str(charger_id), payload):
            await self.coordinator.async_request_refresh()
