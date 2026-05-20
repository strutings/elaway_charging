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
    
    # Fallback charger ID if not found in data
    FALLBACK_CHARGER_ID = "22408"

    entities: list[NumberEntity] = [
        ElawayMaxCurrentNumber(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
        ElawaySmartChargingTargetNumber(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info),
        ElawaySolarMinPowerNumber(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info)
    ]
    
    if root_data.get("is_light_intensity_supported", False):
        entities.append(ElawayLightIntensityNumber(coordinator, api, entry.entry_id, FALLBACK_CHARGER_ID, device_info))

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


class ElawayMaxCurrentNumber(CoordinatorEntity, NumberEntity):
    """Representation of a number entity to control Elaway charger maximum current limit."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
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
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"max_current_a": int(value)}):
            await self.coordinator.async_request_refresh()


class ElawayLightIntensityNumber(CoordinatorEntity, NumberEntity):
    """Representation of a number entity to control Elaway charger status LED brightness."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
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
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        # Mapper slider-verdi (1-5) direkte til Ampecos prosent-skala (20-100)
        api_target = int(value) * 20
        if await self.api.async_patch_charger(str(charger_id), {"light_intensity": api_target}):
            await self.coordinator.async_request_refresh()


class ElawaySmartChargingTargetNumber(CoordinatorEntity, NumberEntity):
    """Control the minimum energy target for smart charging sessions (kWh)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Smart Charging Target"
        self._attr_unique_id = f"{entry_id}_smart_target_kwh"
        self._attr_icon = "mdi:battery-charging-100"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_native_step = 1.0
        self._attr_native_min_value = 1.0
        self._attr_native_max_value = 100.0

    @property
    def native_value(self) -> float | None:
        smart_charging = get_root_data(self.coordinator).get("smart_charging", {})
        if isinstance(smart_charging, dict):
            target = smart_charging.get("target_charge", {})
            if isinstance(target, dict):
                val = target.get("min_kwh")
                return float(val) if val is not None else 5.0
        return 5.0

    async def async_set_native_value(self, value: float) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        payload = {
            "smart_charging": {
                "target_charge": {"min_kwh": str(int(value))}
            }
        }
        if await self.api.async_patch_charger(str(charger_id), payload):
            await self.coordinator.async_request_refresh()


class ElawaySolarMinPowerNumber(CoordinatorEntity, NumberEntity):
    """Control the minimum solar power required for solar-based charging (kW)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, entry_id, fallback_charger_id, device_info):
        super().__init__(coordinator)
        self.api = api
        self.fallback_charger_id = fallback_charger_id
        self._attr_device_info = device_info
        self._attr_name = "Min Solar Power"
        self._attr_unique_id = f"{entry_id}_min_solar_kw"
        self._attr_icon = "mdi:solar-power"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_native_step = 0.1
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 22.0

    @property
    def native_value(self) -> float | None:
        try:
            val = get_root_data(self.coordinator).get("allowed_solar_min_power_kw")
            return float(val) if val is not None else 2.0
        except (TypeError, ValueError):
            return 2.0

    async def async_set_native_value(self, value: float) -> None:
        charger_id = get_root_data(self.coordinator).get("id") or self.fallback_charger_id
        if await self.api.async_patch_charger(str(charger_id), {"allowed_solar_min_power_kw": value}):
            await self.coordinator.async_request_refresh()
