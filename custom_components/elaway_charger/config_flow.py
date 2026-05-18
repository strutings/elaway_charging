import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .api import ElawayAPI

_LOGGER = logging.getLogger(__name__)

# KUN de felles Ampeco-verdiene holdes hardkodet her nå
HARDCODED_AMPECO_CLIENT_ID = "1"
HARDCODED_AMPECO_URL = "https://api.elaway.io/api/v1/app"

# Skjemaet krever nå brukernavn, passord, din unike Auth0-streng og secret
DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("client_id"): str,  # Tilbake i skjemaet siden den er unik for deg
        vol.Required("elaway_client_secret"): str,
    }
)

class ElawayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer oppsett der unik client_id tastes inn, mens Ampeco-ID er fast."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Kjøres når brukeren legger til integrasjonen."""
        errors = {}

        if user_input is not None:
            try:
                # Kombinerer brukerens unike data med de hardkodede fellesverdiene
                api = ElawayAPI(
                    username=user_input["username"],
                    password=user_input["password"],
                    client_id=user_input["client_id"],
                    elaway_client_id=HARDCODED_AMPECO_CLIENT_ID,
                    elaway_client_secret=user_input["elaway_client_secret"],
                    ampeco_api_url=HARDCODED_AMPECO_URL
                )

                token = await api.async_get_valid_credentials()
                
                if token:
                    # Vi lagrer alt samlet så __init__.py og api.py får tak i det senere
                    full_data = {
                        **user_input,
                        "elaway_client_id": HARDCODED_AMPECO_CLIENT_ID,
                        "ampeco_api_url": HARDCODED_AMPECO_URL
                    }
                    
                    return self.async_create_entry(
                        title=f"Elaway ({user_input['username']})", 
                        data=full_data
                    )
                else:
                    errors["base"] = "invalid_auth"

            except Exception as err:
                err_msg = str(err).lower()
                _LOGGER.error("Detaljert feil under Elaway-validering: %s", err)
                
                if "auth0 pålogging feilet" in err_msg or "unauthorized_client" in err_msg:
                    errors["base"] = "Feil brukernavn, passord eller Client ID (Auth0 avviste)."
                elif "ampeco avviste tokenet" in err_msg:
                    errors["base"] = "Auth0 OK, men Ampeco avviste Elaway Client Secret."
                elif "klarte ikke å hente ut 'code'" in err_msg:
                    errors["base"] = "Kunne ikke hente sesjonskode. Sannsynligvis blokkert av Auth0 bot-skjold."
                elif "cannot connect" in err_msg or "404" in err_msg:
                    errors["base"] = "Kunne ikke kontakte Elaway-serveren."
                else:
                    errors["base"] = f"Feil: {str(err)}"

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )
