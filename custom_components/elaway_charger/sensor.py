import logging
from homeassistant.components.sensor import SensorEntity
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
    """Setter opp Elaway-sensorer basert på faktiske API-data."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Lader ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    # Her oppretter vi alle sensorene dine uten duplikater i koden
    sensors = [
        ElawayStatusSensor(coordinator, entry, device_info),
        ElawayEvseStatusSensor(coordinator, entry, device_info),
        ElawayMaxPowerSensor(coordinator, entry, device_info),
        ElawayMaxCurrentSensor(coordinator, entry, device_info),
        ElawayTariffPriceSensor(coordinator, entry, device_info),
        ElawayTariffNameSensor(coordinator, entry, device_info),
        ElawayLastMonthEnergySensor(coordinator, entry, device_info),
        ElawayFirmwareSensor(coordinator, entry, device_info),
        ElawaySmartChargingSensor(coordinator, entry, device_info),
        ElawayOwnerSensor(coordinator, entry, device_info),
    ]
    
    async_add_entities(sensors, True)


def get_root_data(coordinator_data):
    """Hjelper for å hente ut rot-data-objektet trygt."""
    if not coordinator_data:
        return {}
    if isinstance(coordinator_data, dict):
        # Sjekker om dataene ligger inni en "data"-nøkkel eller i roten direkte
        return coordinator_data.get("data", coordinator_data)
    elif isinstance(coordinator_data, list) and len(coordinator_data) > 0:
        return coordinator_data[0]
    return {}


class ElawayStatusSensor(CoordinatorEntity, SensorEntity):
    """Hovedstatus for ladeboksen (f.eks. available)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Boks Status"
        self._attr_unique_id = f"{entry.entry_id}_box_status_sensor"
        self._attr_icon = "mdi:cloud-check"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("status", "Ukjent")


class ElawayEvseStatusSensor(CoordinatorEntity, SensorEntity):
    """Spesifikk status for selve ladeuttaket (f.eks. preparing, charging)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Ladestatus"
        self._attr_unique_id = f"{entry.entry_id}_evse_status_sensor"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            return evses[0].get("status", "Ukjent")
        return "Ukjent"


class ElawayMaxPowerSensor(CoordinatorEntity, SensorEntity):
    """Maksimal tillatt ladeeffekt satt av systemet (kW)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Maks Ladeeffekt"
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
    """Maksimal tillatt strømstyrke (A)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Maks Strømstyrke"
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
    """Gjeldende strømpris per kWh satt av borettslaget (inkl. valuta)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Ladepris"
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
        return "Ukjent"


class ElawayTariffNameSensor(CoordinatorEntity, SensorEntity):
    """Navnet på tariffen/avtalen som er aktiv på laderen."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Tariffnavn"
        self._attr_unique_id = f"{entry.entry_id}_tariff_name_sensor"
        self._attr_icon = "mdi:file-sign"

    @property
    def native_value(self):
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                return tariff.get("name", "Ukjent")
        return "Ukjent"


class ElawayLastMonthEnergySensor(CoordinatorEntity, SensorEntity):
    """Strømforbruk forrige måned (kWh)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Forbruk Forrige Måned"
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
    """Firmware-versjon installert på ladeboksen."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Firmware Versjon"
        self._attr_unique_id = f"{entry.entry_id}_firmware_sensor"
        self._attr_icon = "mdi:update"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("firmware_version", "Ukjent")


class ElawaySmartChargingSensor(CoordinatorEntity, SensorEntity):
    """Viser om smartlading (tidsplan) er aktivert i appen."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Smartlading Aktiv"
        self._attr_unique_id = f"{entry.entry_id}_smart_charging_sensor"
        self._attr_icon = "mdi:brain"

    @property
    def native_value(self):
        is_enabled = get_root_data(self.coordinator.data).get("smart_charging_enabled", False)
        return "Ja" if is_enabled else "Nei"


class ElawayOwnerSensor(CoordinatorEntity, SensorEntity):
    """Registrert eier av ladeboksen."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Registrert Eier"
        self._attr_unique_id = f"{entry.entry_id}_owner_sensor"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        return get_root_data(self.coordinator.data).get("ownerName", "Ukjent")
class ElawayFixedFeeSensor(CoordinatorEntity, SensorEntity):
    """Viser fast oppstartsavgift for ladesesjonen (Connection Fee)."""
    def __init__(self, coordinator, entry, device_info):
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_name = "Elaway Fast Oppstartsavgift"
        self._attr_unique_id = f"{entry.entry_id}_fixed_fee_sensor"
        self._attr_icon = "mdi:cash-marker"

    @property
    def native_value(self):
        """Henter ut connectionFee (f.eks. 0)."""
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
        """Henter valutaen dynamisk (f.eks. NOK)."""
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                return tariff.get("currency", "NOK")
        return "NOK"

    @property
    def extra_state_attributes(self):
        """Legger til det faste kWh-påslaget som et ekstra attributt."""
        data = get_root_data(self.coordinator.data)
        evses = data.get("evses", [])
        markup_fee = 0
        
        if evses and isinstance(evses, list):
            tariff = evses[0].get("tariff", {})
            if isinstance(tariff, dict):
                pricing = tariff.get("pricing", {})
                if isinstance(pricing, dict):
                    markup_fee = pricing.get("markupFixedFeePerKwh", 0)
                    
        return {
            "markup_fixed_fee_per_kwh": markup_fee
        }
