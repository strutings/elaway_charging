import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .api import ElawayAPI

_LOGGER = logging.getLogger(__name__)

# ONLY the shared Ampeco values are kept hardcoded here now
HARDCODED_AMPECO_CLIENT_ID = "1"
HARDCODED_AMPECO_URL = "https://no.eu-elaway.charge.ampeco.tech/api/v1/app"

# The schema now requires username, password, your unique Auth0 string, and secret
DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
        vol.Required("client_id"): str,  # Back in the schema since it is unique to you
        vol.Required("elaway_client_secret"): str,
    }
)

class ElawayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles setup where a unique client_id is entered, while the Ampeco ID is static."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Runs when the user adds the integration."""
        errors = {}

        if user_input is not None:
            try:
                # Combines the user's unique data with the hardcoded shared values
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
                    # We store everything together so __init__.py and api.py can retrieve it later
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
                _LOGGER.error("Detailed error during Elaway validation: %s", err)
                
                if "auth0 login failed" in err_msg or "unauthorized_client" in err_msg:
                    errors["base"] = "Incorrect username, password, or Client ID (Auth0 rejected)."
                elif "ampeco rejected the token" in err_msg:
                    errors["base"] = "Auth0 OK, but Ampeco rejected the Elaway Client Secret."
                elif "failed to extract 'code'" in err_msg:
                    errors["base"] = "Could not retrieve session code. Likely blocked by Auth0 bot protection."
                elif "cannot connect" in err_msg or "404" in err_msg:
                    errors["base"] = "Could not contact the Elaway server."
                else:
                    errors["base"] = f"Error: {str(err)}"

        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA, 
            errors=errors
        )
