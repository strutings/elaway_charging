"""Config flow for Elaway Charger integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .api import ElawayAPI

_LOGGER = logging.getLogger(__name__)

# Definerer skjemaet som vises i Home Assistant sitt brukergrensesnitt
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

class ElawayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elaway Charger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step where user inputs their Elaway credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Sjekk om brukernavnet allerede er lagt til for å unngå duplikater
            await self.async_set_unique_id(user_input["username"].lower())
            self._abort_if_unique_id_configured()

            try:
                # Initialiserer API-klienten med de oppgitte legitimasjonene
                api = ElawayAPI(
                    username=user_input["username"],
                    password=user_input["password"]
                )
                
                # Tester påloggingen og henter det første gyldige Ampeco-tokenet
                token = await api.async_get_valid_credentials()
                
                if not token:
                    raise InvalidAuth

                # Hvis påloggingen gikk bra, lagres oppføringen i Home Assistant
                return self.async_create_entry(
                    title=f"Elaway ({user_input['username']})",
                    data=user_input,
                )

            except InvalidAuth:
                _LOGGER.error("Feil under pålogging: Ugyldig brukernavn eller passord")
                errors["base"] = "invalid_auth"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Uventet feil under Elaway konfigurasjonsflyt: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the Elaway/Auth0 servers."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth (wrong username or password)."""
