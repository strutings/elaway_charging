# ⚡ Elaway Charger integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/Version-4.0.0-emerald.svg?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained%3F-Yes-emerald.svg?style=for-the-badge)

An unofficial Home Assistant integration for **Elaway** charging stations running on the Ampeco platform. This integration can be utilized by any user provisioned with Elaway as their charging operator through housing cooperatives, condominiums, or apartment co-ownerships (borettslag og sameier). It provides full control over charging, real-time data, and a suite of diagnostic sensors by securely replicating the official mobile application authentication flows.
---

## ✨ Features

The integration creates a unified device in Home Assistant (**Ampeco Powered Elaway Charger**) containing the following entities:

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

## 🔑 Authentication Architecture

Unlike previous versions, this integration does not require complex browser developer tools interception or manual token extraction. The component fully automates the native mobile client authentication sequence natively:

1. **Auth0 Handshake**: Initiates an authorization block simulating an iOS device agent, leveraging a dynamically generated Proof Key for Code Exchange (PKCE) challenge layer (`S256`).
2. **Token Grant**: Programmatically exchanges validation strings against the Auth0 API to retrieve standard `access_token` and `id_token` bundles.
3. **Ampeco Platform Exchange**: Packages identity keys as a string-serialized payload model alongside mandatory system tracking headers (`x-platform`, `x-mobile-app-bundle-id`, `x-internal-app-version`) to seamlessly generate valid application bearer tokens.

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

1. Download the repository and extract the archive folder.
2. Upload the `elaway_charger` folder to your Home Assistant installation components directory:
   `└── /config/custom_components/elaway_charger/`
3. **Restart Home Assistant.**

---

## ⚙️ Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for `Elaway Charger`.
4. Enter the account registered email address (username) and password.
5. Click **Submit** to finalize device setup and initialize sensor assets.

---

## 🛠️ Troubleshooting

To enable debug logging for runtime connection testing or protocol formatting analysis, add the following configuration block onto your primary `configuration.yaml` file:

```yaml
logger:
  default: warning
  logs:
    custom_components.elaway_charger: debug
