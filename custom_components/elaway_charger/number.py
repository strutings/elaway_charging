"""Support for Elaway number configuration entities."""
from __future__ import annotations

import logging
import aiohttp
from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up Elaway number entities based on coordinator and api data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    api = entry_data["api"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    root_data = get_root_data(coordinator)
    
    entities: list[NumberEntity] = [
        ElawayMaxCurrentNumber(coordinator, api, entry.entry_id, device_info)
    ]
    
    if root_data.get("is_light_intensity_supported", False):
        entities.append(ElawayLightIntensityNumber(coordinator, api, entry.entry_id, device_info))

    async_add_entities(entities, True)


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


class ElawayMaxCurrentNumber(CoordinatorEntity, NumberEntity):
    """Representation of a number entity to control Elaway charger maximum current limit."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Max Charging Current"
        self._attr_unique_id = f"{entry_id}_max_current"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_unit_of_measurement = "A"
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_step = 1.0

    @property
    def native_value(self) -> float | None:
        try:
            val = get_root_data(self.coordinator).get("max_current_a")
            return float(val) if val is not None else 32.0
        except (TypeError, ValueError):
            return 32.0

    @property
    def native_min_value(self) -> float:
        try:
            return float(get_root_data(self.coordinator).get("min_charging_current", 6.0))
        except (TypeError, ValueError):
            return 6.0

    @property
    def native_max_value(self) -> float:
        try:
            return float(get_root_data(self.coordinator).get("allowed_max_current_a", 32.0))
        except (TypeError, ValueError):
            return 32.0

    async def async_set_native_value(self, value: float) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        if await _send_ampeco_patch(self.api, str(charger_id), {"max_current_a": int(value)}):
            await self.coordinator.async_request_refresh()


class ElawayLightIntensityNumber(CoordinatorEntity, NumberEntity):
    """Representation of a number entity to control Elaway charger status LED brightness."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Status Light Intensity"
        self._attr_unique_id = f"{entry_id}_light_intensity"
        self._attr_icon = "mdi:brightness-6"
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_step = 1.0
        self._attr_native_min_value = 1.0
        self._attr_native_max_value = 5.0

    @property
    def native_value(self) -> float | None:
        try:
            val = get_root_data(self.coordinator).get("light_intensity")
            if val is not None:
                raw_val = int(val)
                return float(raw_val // 20) if raw_val >= 20 else float(raw_val)
            return 5.0
        except (TypeError, ValueError):
            return 5.0

    async def async_set_native_value(self, value: float) -> None:
        charger_id = get_root_data(self.coordinator).get("id")
        if not charger_id:
            return

        # Mapper slider-verdi (1-5) direkte til Ampecos prosent-skala (20-100)
        api_target = int(value) * 20

        if await _send_ampeco_patch(self.api, str(charger_id), {"light_intensity": api_target}):
            await self.coordinator.async_request_refresh()
