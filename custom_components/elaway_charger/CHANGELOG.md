# Changelog

All notable changes to the Elaway Charger integration will be documented in this file.

## [3.5.0] - 2026-05-20

### Added
- **New API Migration**: Migrated core API endpoint to `no.eu-elaway.charge.ampeco.tech` to fix `DNSError` and connectivity issues.
- **Backward Compatibility**: Added automatic sanitization of old configuration URLs to ensure seamless migration for existing users.
- **Plug & Charge Control**: Added a new switch to enable/disable Plug & Charge functionality.
- **Smart Charging Control**: Added a new switch and diagnostic sensors for Elaway's Smart Charging system.
- **Enhanced Power Allocation Sensors**:
    - `Offered Charging Power` (kW): Real-time power offered to the vehicle.
    - `Infrastructure Available Power` (kW): Shows the hard limit set by the housing association/infrastructure.
- **Advanced Diagnostics**:
    - `Smart Charging Target` (kWh) and `Smart Charging Mode`.
    - `Subscription Active` status for the account owner.
    - `Cost Last Month` (NOK) and `Electricity Tax` (%) sensors.
    - `Min Solar Power` (kW) for solar-optimized charging.
- **New Binary Sensors**: `Is Rebooting` and `Is Firmware Updating` states.
- **Advanced Configuration**:
    - Added `Smart Charging Target` number entity for kWh adjustment.
    - Added `Min Solar Power` number entity for solar threshold adjustment.
    - Added `Smart Charging Start/End` text entities for schedule management.

### Fixed
- **Cable Connection Logic**: Fixed an issue where the cable appeared disconnected while plugged in. Now uses EVSE status for reliable connection detection.
- **Unit Conversion**: Fixed "Session Power" and "Offered Power" units; they are now correctly converted from Watts to Kilowatts (kW).
- **Session Reliability**: Improved data parsing to handle edge cases where session objects might be missing from the API response.
- **Enhanced Logging**: Added detailed API response logging for PATCH requests to assist with troubleshooting control failures.
