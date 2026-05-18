import logging
import time
import json
import aiohttp
import traceback
import secrets
from urllib.parse import urlparse, parse_qs, urljoin

_LOGGER = logging.getLogger(__name__)

# Verdier hentet direkte fra din config.js og auth.ts
REDIRECT_URI = "io.elaway.no.app://auth.elaway.io/ios/io.elaway.no.app/callback"
ELAWAY_AUTH_URL = "https://auth.elaway.io/authorize"
ELAWAY_TOKEN_URL = "https://auth.elaway.io/oauth/token"
# Dette var den manglende brikken:
AMPECO_BASE_URL = "https://no.eu-elaway.charge.ampeco.tech/api/v1/app"

class ElawayAPI:
    def __init__(self, username, password, client_id, elaway_client_id, elaway_client_secret, ampeco_api_url=None):
        self.username = username
        self.password = password
        self.client_id = client_id  # Auth0 Client ID
        self.elaway_client_id = elaway_client_id # Ampeco Client ID
        self.elaway_client_secret = elaway_client_secret # Ampeco Secret
        
        self.ampeco_base_url = AMPECO_BASE_URL
        self.ampeco_token_url = f"{self.ampeco_base_url}/oauth/token"
        
        self.ampeco_token = None
        self.expires_at = 0
        self.evse_id = None # Bør fylles ut av sensor.py ved første henting

    async def async_get_valid_credentials(self) -> str:
        """Hovedmetode for å hente gyldig token."""
        if self.ampeco_token and self.expires_at > time.time():
            return self.ampeco_token

        try:
            return await self._perform_login()
        except Exception as e:
            _LOGGER.error("KRITISK FEIL I API.PY: %s", traceback.format_exc())
            raise Exception(str(e))

    async def _perform_login(self):
        """
        Gjenskaper flyten fra auth.ts.
        Merk: Uten Puppeteer kan Auth0 blokkere forespørselen.
        """
        _LOGGER.info("Starter pålogging mot Elaway/Ampeco...")
        
        headers = {
            "User-Agent": "insomnia/10.0.0", # Fra din auth.ts
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        local_state = "randomstate" # Fra din auth.ts
        
        async with aiohttp.ClientSession(headers=headers, cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
            
            # 1. Start Auth0 sesjon
            auth_url = (
                f"{ELAWAY_AUTH_URL}?response_type=code"
                f"&client_id={self.client_id}"
                f"&redirect_uri={REDIRECT_URI}"
                f"&scope=openid%20profile%20email"
                f"&state={local_state}"
            )
            
            async with session.get(auth_url, allow_redirects=True) as resp:
                if resp.status != 200:
                    raise Exception(f"Auth0 init feilet: {resp.status}")
                
                # Finn den ekte staten som Auth0 krever i POST
                final_url = str(resp.url)
                actual_state = parse_qs(urlparse(final_url).query).get("state", [local_state])[0]

            # 2. Post login-info
            login_url = f"https://auth.elaway.io/u/login?state={actual_state}"
            payload = {
                "state": actual_state,
                "username": self.username,
                "password": self.password,
                "action": "default"
            }

            async with session.post(login_url, data=payload, allow_redirects=False) as resp:
                if resp.status not in (301, 302):
                    raise Exception("Auth0 nektet pålogging. Sjekk brukernavn/passord.")
                
                location = resp.headers.get("Location")

            # 3. Hent autorisasjonskode fra redirect
            if "code=" not in location:
                async with session.get(urljoin("https://auth.elaway.io", location), allow_redirects=False) as resp:
                    location = resp.headers.get("Location", "")

            code = parse_qs(urlparse(location).query).get("code", [None])[0]
            if not code:
                raise Exception("Fant ikke autorisasjonskode.")

            # 4. Bytt kode mot Auth0 tokens
            async with session.post(ELAWAY_TOKEN_URL, json={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "redirect_uri": REDIRECT_URI,
                "code": code
            }) as resp:
                auth0_data = await resp.json()
                access_token = auth0_data.get("access_token")
                id_token = auth0_data.get("id_token")

            # 5. Bytt Auth0 tokens mot Ampeco Bearer Token (Selve Elaway-nøkkelen)
            ampeco_payload = {
                "token": json.dumps({
                    "accessToken": access_token,
                    "idToken": id_token,
                    "scope": "openid profile email",
                    "expiresIn": 100,
                    "tokenType": "Bearer"
                }),
                "type": "auth0",
                "grant_type": "third-party",
                "client_id": self.elaway_client_id,
                "client_secret": self.elaway_client_secret
            }
            
            async with session.post(self.ampeco_token_url, json=ampeco_payload) as resp:
                if resp.status != 200:
                    raise Exception(f"Ampeco nektet token: {await resp.text()}")
                
                data = await resp.json()
                self.ampeco_token = data.get("access_token")
                self.expires_at = time.time() + data.get("expires_in", 3600)
                
                return self.ampeco_token
