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

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up start and stop buttons for Elaway."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    api = entry_data["api"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Elaway Charger ({entry.title})",
        manufacturer="Eirik Skorstad",
        model="Ampeco Powered Charger",
    )

    CHARGER_ID = "22408"

    async_add_entities([
        ElawayStartButton(coordinator, api, entry, device_info),
        ElawayStopButton(coordinator, api, CHARGER_ID, entry, device_info)
    ], True)


class ElawayStartButton(CoordinatorEntity, ButtonEntity):
    """Button to start a charging session."""

    def __init__(self, coordinator, api, entry, device_info):
        super().__init__(coordinator)
        self.api = api
        self._attr_device_info = device_info
        self._attr_name = "Elaway Start Charging"
        self._attr_unique_id = f"{entry.entry_id}_start_charging_button"
        self._attr_icon = "mdi:play-circle"

    async def async_press(self) -> None:
        """Send START command based on chargerrouter.ts."""
        try:
            token = await self.api.async_get_valid_credentials()
            url = f"{self.api.ampeco_base_url}/session/start"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            payload = {"evseId": int(self.api.evse_id)}

            _LOGGER.info("Sending start command to Elaway via %s with evseId %s", url, self.api.evse_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    # CHANGED HERE: Now also accepts 202 (Accepted) from Ampeco
                    if resp.status not in [200, 201, 202]:
                        error_text = await resp.text()
                        _LOGGER.error("Failed to start charging. Status: %s, Response: %s", resp.status, error_text)
                        return
                    
                    _LOGGER.info("Charging started successfully (Status %s)!", resp.status)
                    
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Error occurred while sending start command: %s", err)


class ElawayStopButton(CoordinatorEntity, ButtonEntity):
    """Button to stop an active charging session."""

    def __init__(self, coordinator, api, charger_id, entry, device_info):
        super().__init__(coordinator)
        self.api = api
        self.charger_id = charger_id
        self._attr_device_info = device_info
        self._attr_name = "Elaway Stop Charging"
        self._attr_unique_id = f"{entry.entry_id}_stop_charging_button"
        self._attr_icon = "mdi:stop-circle"

    async def async_press(self) -> None:
        """Send STOP command based on active session ID from chargerrouter.ts."""
        try:
            token = await self.api.api_get_valid_credentials() if hasattr(self.api, 'api_get_valid_credentials') else await self.api.async_get_valid_credentials()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            current_session_id = None
            
            data = self.coordinator.data
            root_obj = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(root_obj, dict) and "evses" in root_obj:
                evses = root_obj.get("evses", [])
                if evses and "session" in evses[0] and evses[0]["session"]:
                    current_session_id = evses[0]["session"].get("id")

            if not current_session_id:
                _LOGGER.debug("No active session found in memory, performing live status check against charger...")
                check_url = f"{self.api.ampeco_base_url}/personal/charge-points/{self.charger_id}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(check_url, headers=headers) as resp:
                        if resp.status == 200:
                            live_data = await resp.json()
                            live_root = live_data.get("data", live_data)
                            if isinstance(live_root, dict) and "evses" in live_root:
                                evses = live_root.get("evses", [])
                                if evses and "session" in evses[0] and evses[0]["session"]:
                                    current_session_id = evses[0]["session"].get("id")

            if not current_session_id:
                _LOGGER.warning("Could not stop charging: No active charging session found.")
                return

            stop_url = f"{self.api.ampeco_base_url}/session/{current_session_id}/end"
            _LOGGER.info("Ending charging session via %s", stop_url)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(stop_url, headers=headers) as resp:
                    # ALSO CHANGED HERE: Accepts 200, 202, and 204 upon stopping
                    if resp.status not in [200, 202, 204]:
                        error_text = await resp.text()
                        _LOGGER.error("Failed to stop charging. Status: %s, Response: %s", resp.status, error_text)
                        return
                    
                    _LOGGER.info("Charging stopped successfully!")

            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Error occurred while sending stop command: %s", err)
