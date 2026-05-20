"""Set up Elaway sensors based on active API data."""
from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up Elaway telemetry and text sensors based on coordinator data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    sensors = [
        ElawayEvseStatusSensor(coordinator, entry, device_info),
        ElawayMaxPowerSensor(coordinator, entry, device_info),
        ElawayMaxCurrentSensor(coordinator, entry, device_info),
        ElawayTariffPriceSensor(coordinator, entry, device_info),
        ElawayTariffNameSensor(coordinator, entry, device_info),
        ElawayLastMonthEnergySensor(coordinator, entry, device_info),
        ElawayFirmwareSensor(coordinator, entry, device_info),
        ElawaySmartChargingSensor(coordinator, entry, device_info),
        ElawayPlugAndChargeSensor(coordinator, entry, device_info),
        ElawaySolarMinPowerSensor(coordinator, entry, device_info),
        ElawaySmartChargingModeSensor(coordinator, entry, device_info),
        ElawayOfferedPowerSensor(coordinator, entry, device_info),
        ElawayAvailablePowerSensor(coordinator, entry, device_info),
        ElawaySubscriptionActiveSensor(coordinator, entry, device_info),
        ElawayLastMonthCostSensor(coordinator, entry, device_info),
        ElawayElectricityTaxSensor(coordinator, entry, device_info),
        ElawayOwnerSensor(coordinator, entry, device_info),
        ElawayFixedFeeSensor(coordinator, entry, device_info),
        # Session Sensors
        ElawaySessionEnergySensor(coordinator, entry, device_info),
        ElawaySessionPowerSensor(coordinator, entry, device_info),
        ElawaySessionDurationSensor(coordinator, entry, device_info),
        ElawaySessionStateSensor(coordinator, entry, device_info),
        ElawaySessionCostSensor(coordinator, entry, device_info),
        ElawaySessionOfferedPowerSensor(coordinator, entry, device_info),
    ]
    
    async_add_entities(sensors, True)


def get_root_data(coordinator_data):
    """Helper method to safely pull the root data dictionary payload object."""
    if not coordinator_data:
        return {}
    if isinstance(coordinator_data, dict):
        return coordinator_data.get("data", coordinator_data)
    elif isinstance(coordinator_data, list) and len(coordinator_data) > 0:
        return coordinator_data[0]
    return {}

def get_session_data(coordinator_data):
    """Helper to safely extract the active session object from the first EVSE."""
    data = get_root_data(coordinator_data)
    evses = data.get("evses", [])
    if evses and isinstance(evses, list):
        return evses[0].get("session", {})
    return {}


class ElawayEvseStatusSensor(CoordinatorEntity, SensorEntity):
    """Specific state for the charging socket outlet itself (e.g., preparing, charging)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Charging Status"
        self._attr_unique_id = f"{entry.entry_id}_evse_status_sensor"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            return evses[0].get("status", "Unknown")
        return "Unknown"


class ElawayMaxPowerSensor(CoordinatorEntity, SensorEntity):
    """Maximum allowable charging effect/limit set by the infrastructure management loop (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Max Charging Power"
        self._attr_unique_id = f"{entry.entry_id}_max_power_sensor"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = "power"

    @property
    def native_value(self):
        try:
            val = get_root_data(self.coordinator.data).get("allowed_max_power_kw")
            return float(val) if val is not None else 22.2
        except Exception:
            return 22.2


class ElawayMaxCurrentSensor(CoordinatorEntity, SensorEntity):
    """Maximum current constraints configuration allowance value (A)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Max Current"
        self._attr_unique_id = f"{entry.entry_id}_max_current_sensor"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_unit_of_measurement = "A"

    @property
    def native_value(self):
        try:
            val = get_root_data(self.coordinator.data).get("allowed_max_current_a")
            return int(val) if val is not None else 32
        except Exception:
            return 32


class ElawayTariffPriceSensor(CoordinatorEntity, SensorEntity):
    """Current electricity cost rate tracking per kWh applied by housing association property parameters."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Charging Price"
        self._attr_unique_id = f"{entry.entry_id}_tariff_price_sensor"
        self._attr_icon = "mdi:cash-100"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            pricing = tariff.get("pricing", {}) if isinstance(tariff, dict) else {}
            price = pricing.get("pricePerKwh") if isinstance(pricing, dict) else None
            currency = tariff.get("currency", "NOK") if isinstance(tariff, dict) else "NOK"
            if price is not None:
                return f"{price} {currency}/kWh"
        return "Unknown"


class ElawayTariffNameSensor(CoordinatorEntity, SensorEntity):
    """The title/identifier of the active rate contract plan loaded into the station."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Tariff Name"
        self._attr_unique_id = f"{entry.entry_id}_tariff_name_sensor"
        self._attr_icon = "mdi:file-sign"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                return tariff.get("name", "Unknown")
        return "Unknown"


class ElawayLastMonthEnergySensor(CoordinatorEntity, SensorEntity):
    """Total cumulative electricity consumption consumed during previous calendar month cycle interval (kWh)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Energy Last Month"
        self._attr_unique_id = f"{entry.entry_id}_last_month_energy_sensor"
        self._attr_icon = "mdi:calendar-month"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"

    @property
    def native_value(self):
        try:
            val = get_root_data(self.coordinator.data).get("last_month_energy_kwh")
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0


class ElawayFirmwareSensor(CoordinatorEntity, SensorEntity):
    """Active software/firmware build reference version string currently active within device system hardware."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Firmware Version"
        self._attr_unique_id = f"{entry.entry_id}_firmware_sensor"
        self._attr_icon = "mdi:update"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("firmware_version", "Unknown")


class ElawaySmartChargingSensor(CoordinatorEntity, SensorEntity):
    """Evaluates whether charging automation calendar profiles are handled actively inside the user software account app."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Smart Charging Active"
        self._attr_unique_id = f"{entry.entry_id}_smart_charging_sensor"
        self._attr_icon = "mdi:brain"

    @property
    def native_value(self):
        is_enabled = get_root_data(self.coordinator.data).get("smart_charging_enabled", False)
        return "Yes" if is_enabled else "No"


class ElawayPlugAndChargeSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor for Plug & Charge status."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Plug & Charge Active"
        self._attr_unique_id = f"{entry.entry_id}_plug_and_charge_sensor"
        self._attr_icon = "mdi:ev-plug-type2"

    @property
    def native_value(self):
        is_enabled = get_root_data(self.coordinator.data).get("plug_and_charge", False)
        return "Yes" if is_enabled else "No"


class ElawaySolarMinPowerSensor(CoordinatorEntity, SensorEntity):
    """Minimum solar power required for solar-based charging (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Min Solar Power"
        self._attr_unique_id = f"{entry.entry_id}_solar_min_power"
        self._attr_icon = "mdi:solar-power"
        self._attr_native_unit_of_measurement = "kW"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("allowed_solar_min_power_kw")


class ElawaySmartChargingTargetKwhSensor(CoordinatorEntity, SensorEntity):
    """The minimum energy target for smart charging sessions (kWh)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Smart Charging Target"
        self._attr_unique_id = f"{entry.entry_id}_smart_charging_target"
        self._attr_icon = "mdi:battery-charging-100"
        self._attr_native_unit_of_measurement = "kWh"

    @property
    def native_value(self):
        smart_charging = get_root_data(self.coordinator.data).get("smart_charging", {})
        if isinstance(smart_charging, dict):
            target = smart_charging.get("target_charge", {})
            if isinstance(target, dict):
                return target.get("min_kwh")
        return None


class ElawaySubscriptionActiveSensor(CoordinatorEntity, SensorEntity):
    """Indicates if the account owner has an active charging subscription."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Subscription Active"
        self._attr_unique_id = f"{entry.entry_id}_subscription_active"
        self._attr_icon = "mdi:card-account-details-outline"

    @property
    def native_value(self):
        is_active = get_root_data(self.coordinator.data).get("ownerHasActiveSubscription", False)
        return "Yes" if is_active else "No"


class ElawaySmartChargingModeSensor(CoordinatorEntity, SensorEntity):
    """Indicates the current mode of the smart charging system (e.g., schedule)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Smart Charging Mode"
        self._attr_unique_id = f"{entry.entry_id}_smart_charging_mode"
        self._attr_icon = "mdi:cog-sync"

    @property
    def native_value(self):
        smart_charging = get_root_data(self.coordinator.data).get("smart_charging", {})
        if isinstance(smart_charging, dict):
            return smart_charging.get("mode", "Unknown")
        return "Unknown"


class ElawayOfferedPowerSensor(CoordinatorEntity, SensorEntity):
    """Real-time charging effect currently offered to the vehicle by the infrastructure (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Offered Charging Power"
        self._attr_unique_id = f"{entry.entry_id}_offered_power_sensor"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = "power"

    @property
    def native_value(self):
        try:
            # Henter offeredPower fra session i første EVSE og konverterer fra W til kW
            data = get_root_data(self.coordinator.data)
            evses = data.get("evses", [])
            if evses and isinstance(evses, list):
                val = evses[0].get("session", {}).get("offeredPower")
                return round(float(val) / 1000, 2) if val is not None else 0.0
        except Exception:
            return 0.0
        return 0.0


class ElawayAvailablePowerSensor(CoordinatorEntity, SensorEntity):
    """The absolute maximum power limit currently permitted by the housing association infrastructure (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Infrastructure Available Power"
        self._attr_unique_id = f"{entry.entry_id}_available_power_sensor"
        self._attr_icon = "mdi:transmission-tower"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = "power"

    @property
    def native_value(self):
        try:
            val = get_root_data(self.coordinator.data).get("allowed_max_power_kw")
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0


class ElawayLastMonthCostSensor(CoordinatorEntity, SensorEntity):
    """Total electricity cost for the previous calendar month cycle."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Cost Last Month"
        self._attr_unique_id = f"{entry.entry_id}_last_month_cost"
        self._attr_icon = "mdi:cash-clock"

    @property
    def native_value(self):
        try:
            val = get_root_data(self.coordinator.data).get("last_month_electricity_cost")
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0

    @property
    def native_unit_of_measurement(self):
        return "NOK"


class ElawayElectricityTaxSensor(CoordinatorEntity, SensorEntity):
    """The electricity tax percentage applied to the charging costs."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Electricity Tax"
        self._attr_unique_id = f"{entry.entry_id}_electricity_tax"
        self._attr_icon = "mdi:percent"
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("electricity_cost_tax_percent")


class ElawayOwnerSensor(CoordinatorEntity, SensorEntity):
    """Profile display information tracking account owner values associated with this hardware asset node entry."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Registered Owner"
        self._attr_unique_id = f"{entry.entry_id}_owner_sensor"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("ownerName", "Unknown")


class ElawayFixedFeeSensor(CoordinatorEntity, SensorEntity):
    """Tracks initial access connection fixed fees required per session instantiation cycle."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Connection Fixed Fee"
        self._attr_unique_id = f"{entry.entry_id}_fixed_fee_sensor"
        self._attr_icon = "mdi:cash-marker"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                pricing = tariff.get("pricing", {})
                if isinstance(pricing, dict):
                    return pricing.get("connectionFee", 0)
        return 0

    @property
    def native_unit_of_measurement(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                return tariff.get("currency", "NOK")
        return "NOK"

    @property
    def extra_state_attributes(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        markup_fee = 0
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                pricing = tariff.get("pricing", {})
                if isinstance(pricing, dict):
                    markup_fee = pricing.get("markupFixedFeePerKwh", 0)
        return {"markup_fixed_fee_per_kwh": markup_fee}


class ElawaySessionEnergySensor(CoordinatorEntity, SensorEntity):
    """Real-time energy consumption for the current active charging session (converted to kWh)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session Energy"
        self._attr_unique_id = f"{entry.entry_id}_session_energy"
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        """Return energy in kWh (API provides Wh)."""
        try:
            # Henter Wh fra API og deler på 1000 for å få kWh
            wh_value = float(get_session_data(self.coordinator.data).get("energy", 0))
            return round(wh_value / 1000, 3)
        except (TypeError, ValueError):
            return 0

class ElawaySessionPowerSensor(CoordinatorEntity, SensorEntity):
    """Real-time charging effect for the current active charging session (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session Power"
        self._attr_unique_id = f"{entry.entry_id}_session_power"
        self._attr_icon = "mdi:flash"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = "power"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return power in kW (API provides W)."""
        try:
            val = get_session_data(self.coordinator.data).get("power", 0)
            return round(float(val) / 1000, 2) if val is not None else 0.0
        except (TypeError, ValueError):
            return 0.0


class ElawaySessionDurationSensor(CoordinatorEntity, SensorEntity):
    """Current active charging session duration in minutes."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session Duration"
        self._attr_unique_id = f"{entry.entry_id}_session_duration"
        self._attr_icon = "mdi:timer-outline"
        self._attr_native_unit_of_measurement = "min"

    @property
    def native_value(self):
        return get_session_data(self.coordinator.data).get("duration", 0)


class ElawaySessionStateSensor(CoordinatorEntity, SensorEntity):
    """Granular charging state from the session object (e.g., suspendedEVSE)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session State"
        self._attr_unique_id = f"{entry.entry_id}_session_state"
        self._attr_icon = "mdi:information-outline"

    @property
    def native_value(self):
        return get_session_data(self.coordinator.data).get("chargingState", "Idle")


class ElawaySessionCostSensor(CoordinatorEntity, SensorEntity):
    """The current accumulated cost of the active charging session."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session Cost"
        self._attr_unique_id = f"{entry.entry_id}_session_cost"
        self._attr_icon = "mdi:cash"
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self):
        return get_session_data(self.coordinator.data).get("amount", 0)

    @property
    def native_unit_of_measurement(self):
        session = get_session_data(self.coordinator.data)
        return session.get("currency", {}).get("code", "NOK")


class ElawaySessionOfferedPowerSensor(CoordinatorEntity, SensorEntity):
    """The maximum power offered to the vehicle by the infrastructure charger (W)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Session Offered Power"
        self._attr_unique_id = f"{entry.entry_id}_session_offered_power"
        self._attr_icon = "mdi:shield-flash-outline"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = "power"

    @property
    def native_value(self):
        """Return offered power in kW (API provides W)."""
        try:
            val = get_session_data(self.coordinator.data).get("offeredPower", 0)
            return round(float(val) / 1000, 2) if val is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
