# ⚡ Elaway Charger integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/Version-2.0.0-emerald.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-Yes-emerald.svg?style=for-the-badge)

En uoffisiell Home Assistant-integrasjon for **Elaway** ladebokser som kjører på Ampeco-plattformen (for eksempel i Risvollan Borettslag). Integrasjonen gir deg full kontroll over ladingen, sanntidsdata, priser, samt start- og stoppknapper direkte i ditt smarthus.

Distribuert og vedlikeholdt av **Eirik Skorstad**.

---

## ✨ Funksjoner

Integrasjonen oppretter en enhet i Home Assistant (**Ampeco Powered Charger av Eirik Skorstad**) med følgende enheter:

*   **Styring:** Start- og Stopp-knapper skreddersydd for Ampeco-sesjoner.
*   **Sensorer:**
    *   `Elaway Ladestatus` (preparing, charging, available, etc.)
    *   `Elaway Boks Status` (tilkobling til skyen)
    *   `Elaway Maks Ladeeffekt` (kW) & `Maks Strømstyrke` (A)
    *   `Elaway Ladepris` (Henter gjeldende kWh-pris satt av borettslaget, f.eks. NOK/kWh)
    *   `Elaway Fast Oppstartsavgift` (Viser eventuell startavgift/connection fee, samt tariffpåslag som attributt)
    *   `Elaway Forbruk Forrige Måned` (kWt)
    *   `Elaway Firmware Versjon` & `Registrert Eier`

---

## 🔑 Slik henter du ut API-legitimasjon (Client Secret osv.)

For å sette opp integrasjonen trenger du tilgangstegn (credentials) fra Elaway-appen. Siden Elaway bruker Ampeco i bakgrunnen, kan du fange opp disse ved å logge inn på Elaway sin webportal eller bruke utviklerverktøyet i nettleseren din:

1. Åpne **Google Chrome** eller **Edge** og logg inn på Elaway sin ladeportal (eller borettslagets ladeside).
2. Trykk på `F12` på tastaturet ditt (eller høyreklikk og velg **Inspiser**) for å åpne Utviklerverktøy.
3. Gå til fanen **Network** (Nettverk).
4. Forfrisk siden (`F5`).
5. I søkefeltet under Network-fanen, søk etter `/user` eller `login`.
6. Klikk på en av forespørslene (requests) som dukker opp, og se under **Headers** eller **Response**.
7. Let etter følgende verdier som du må lime inn under oppsettet i Home Assistant:
    *   `client_id` / `elaway_client_id`
    *   `elaway_client_secret`
    *   `ampeco_api_url` *(Standard er satt til `https://no.eu-elaway.charge.ampeco.tech/api/v1/app`)*

---

## 🚀 Installasjon

Velg enten automatisk installasjon via HACS (anbefalt) eller manuell installasjon.

### Metode 1: Automatisk via HACS (Anbefalt)

Du kan legge til dette repositoriet direkte i HACS ved å klikke på knappen under:

[![Åpne ditt Home Assistant-forekomst og vis dialogboksen for å legge til et repositorium i HACS.](https://my.home-assistant.io/badge/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=https://github.com/strutings/elaway_charging.git)

**Eller gjør det manuelt i HACS:**
1. Åpne **HACS** i Home Assistant.
2. Klikk på de tre prikkene øverst i høyre hjørne og velg **Custom repositories** (Egendefinerte repositorier).
3. Lim inn URL-en til dette GitHub-repositoriet.
4. Velg **Integration** som kategori, og klikk **Add**.
5. Finn integrasjonen i HACS-listen, klikk **Download**, og start Home Assistant på nytt.

---

### Metode 2: Manuell installasjon

Hvis du ikke bruker HACS, kan du installere filene manuelt:

1. Last ned dette repositoriet som en `.zip`-fil fra GitHub.
2. Pakk ut filen og finn mappen `custom_components/elaway_charger`.
3. Bruk Samba, SSH eller File Editor til å laste opp mappen `elaway_charger` til din Home Assistant-installasjon under:
   `└── /config/custom_components/elaway_charger/`
4. Sjekk at mappen inneholder alle nødvendige filer (`__init__.py`, `sensor.py`, `button.py`, `manifest.json`, osv.).
5. **Start Home Assistant på nytt.**

---

## ⚙️ Konfigurering

Etter installasjon og omstart, aktiverer du integrasjonen i brukergrensesnittet:

1. Gå til **Innstillinger** -> **Enheter og tjenester**.
2. Klikk på **+ Legg til integrasjon** nederst til høyre.
3. Søk etter `Elaway Charger` og velg den.
4. Skriv inn ditt brukernavn, passord og API-detaljene du fant i steget [🔑 Slik henter du ut API-legitimasjon](#-slik-henter-du-ut-api-legitimasjon-client-secret-osv).
5. Klikk **Send inn**. Enheten din vil nå dukke opp under enheter med navnet `Ampeco Powered Charger av Eirik Skorstad`.

---

## 🛠️ Feilsøking og Loggføring

Hvis start/stopp-knappene eller sensorene ikke oppdaterer seg, kan du aktivere utvidet feilsøking i din `configuration.yaml` for å se nøyaktig hva Ampeco-API-et svarer:

```yaml
logger:
  default: warning
  logs:
    custom_components.elaway_charger: debug
