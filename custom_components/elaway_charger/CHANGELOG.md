### CHANGELOG.md

```markdown
# Changelog

A comprehensive collection of all notable structural modifications and technical fixes implemented in the Elaway Charger custom integration codebase.

### Changed
- **Technical Language Standardization**: Refactored all log outputs, system messages, and code commentary into formal technical English to maintain an industry-standard implementation.
- **Payload Protocol Refactoring**: Transitioned the outbound third-party backend payload structure from legacy form URL-encoded blocks into a native JSON request format to achieve precise string typing enforcement.

### Added
- **PKCE Cryptographic Layer**: Implemented automated client challenge routines (`code_verifier` and `code_challenge` under `S256`) to conform securely with modern OAuth2 mobile endpoint requirements.
- **Application Identity Headers**: Integrated native mobile identification properties (`x-platform`, `x-mobile-app-bundle-id`, and `x-internal-app-version`) directly into outbound platform request blocks based on live application telemetry analysis.
- **Geographical Routing Boundaries**: Added fixed localization environment tracking via the `"operatorCountry": "NO"` parameter string to ensure proper regional data routing.

### Fixed
- **PHP Data Types Schema Alignment**: Resolved a deep backend gateway error (`Argument #2 ($token) must be of type string, array given`) originated within the core Ampeco validation layers (`ThirdPartyGrant.php`).
- **Data Serialization Handling**: Enforced strict inline payload wrapping rules by passing the internal authentication dictionary through an explicit `json.dumps()` serialization block before transmission.
- **Secret Matrix Resolution**: Swapped out experimental development authorization hashes with the authentic production application secret key verified from active network traces.
- **Authentication Bypass Constraints**: Mitigated authentication handshaking failures by stripping incorrect `audience` string variables from initial Auth0 transaction parameters.
- **Asynchronous Redirect Interception**: Fixed flow execution issues by implementing robust query string extraction (`parse_qs`) to dynamically capture returned authorization state keys.
