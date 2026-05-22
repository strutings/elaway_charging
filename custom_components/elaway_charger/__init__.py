"""The Elaway Charging integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .api import ElawayAPI

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "button", "binary_sensor", "switch", "number", "text"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elaway from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialiser API-klienten
# Initialiser API-klienten med lagret sikkerhetsnøkkel
    api = ElawayAPI(
        username=entry.data.get("username"),
        password=entry.data.get("password"),
    )
    # Hardkodede referanser for lader og EVSE
    CHARGER_ID = "22408"
    api.evse_id = "21357"

    async def _async_update_data():
        try:
            token = await api.async_get_valid_credentials()
            
            # Bruker den spesifikke ruten for personlige ladere
            url = f"{api.ampeco_base_url}/personal/charge-points/{CHARGER_ID}"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # Bruker Home Assistants felles sesjon (forhindrer minnelekkasje og treghet)
            session = async_get_clientsession(hass)
            
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"API failed with status {resp.status} at {url}")
                return await resp.json()
                
        except Exception as err:
            raise UpdateFailed(f"Failed to communicate with Elaway: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="elaway_charger_coordinator",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=30),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Could not connect to Elaway during first refresh: {ex}") from ex

    # Lagrer både api og coordinator slik at switch.py og number.py finner dem
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Elaway integration config entry platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
