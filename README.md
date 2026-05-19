# ⚡ Elaway Charger integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/Version-3.4.5-emerald.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-Yes-emerald.svg?style=for-the-badge)

An unofficial Home Assistant integration for **Elaway** charging stations running on the Ampeco platform. This integration provides full control over charging, real-time data, and a suite of diagnostic sensors.

Distributed and maintained by **Eirik Skorstad**.

---

## ✨ Features

The integration creates a unified device in Home Assistant (**Ampeco Powered Charger by Eirik Skorstad**) containing the following entities:

* **Controls:**
    * `Start Charging` / `Stop Charging` buttons tailored for Ampeco sessions.
* **Binary Sensors:**
    * `Charger Status` (Connectivity/Online status)
    * `Cable Connected` (Detection of EV plug)
    * `Authentication Required` (Lock status)
* **Telemetry Sensors:**
    * `Charging Status` (Preparing, charging, available, etc.)
    * `Max Charging Power` (kW) & `Max Current` (A)
    * `Charging Price` (Real-time kWh price set by property manager)
    * `Connection Fixed Fee` (Session start fee with tariff markup attributes)
    * `Energy Last Month` (kWh)
    * `Firmware Version` & `Registered Owner`

---

## 🔑 How to retrieve API Credentials

To set up the integration, you need credentials from the Elaway web portal. 

1.  Log in to the Elaway charging portal in **Chrome** or **Edge**.
2.  Press `F12` to open Developer Tools and go to the **Network** tab.
3.  Refresh the page (`F5`).
4.  Search for `/user` or `login` in the filter box.
5.  Check the **Headers** or **Response** for:
    * `client_id` (Your unique Auth0 string)
    * `elaway_client_secret`
    * `ampeco_api_url` *(Usually `https://no.eu-elaway.charge.ampeco.tech/api/v1/app`)*

---

## 🚀 Installation

### Method 1: Automatic via HACS (Recommended)

Click the button below to add this repository to your HACS instance:

[![Open your Home Assistant instance and open a repository maintainer's website.](https://my.home-assistant.io/badge/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=strutings&repository=elaway_charging&category=integration)

**Or add manually in HACS:**
1. Open **HACS** -> Three dots (top right) -> **Custom repositories**.
2. Paste the URL of this GitHub repository.
3. Select **Integration** as category and click **Add**.

---

### Method 2: Manual Installation

1. Download the repository and extract the `.zip`.
2. Upload the `elaway_charger` folder to your Home Assistant installation:
   `└── /config/custom_components/elaway_charger/`
3. **Restart Home Assistant.**

---

## ⚙️ Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for `Elaway Charger`.
4. Enter your username, password, and the API credentials retrieved in the previous steps.
5. Click **Submit**.

---

## 🛠️ Troubleshooting

To enable debug logging, add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.elaway_charger: debug
