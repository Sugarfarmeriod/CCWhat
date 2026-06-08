## ADDED Requirements

### Requirement: Recording configuration is persisted
The system SHALL persist user recording settings in a readable config file and load them before starting proxy, run, discovery confirmation, or viewer status operations.

#### Scenario: Config file is created after setup
- **WHEN** onboarding completes successfully
- **THEN** the system writes `~/.ccwhat/config.toml`
- **AND** the file contains recording domains, path filters, redaction settings, body size limit, and onboarding completion state

#### Scenario: Config file is loaded on startup
- **WHEN** the user runs `ccwhat proxy`, `ccwhat run`, `ccwhat discover`, or `ccwhat web`
- **THEN** the command loads `~/.ccwhat/config.toml` unless a different config path is provided

#### Scenario: Missing config is explicit
- **WHEN** a command that records payloads starts without config or CLI-provided domains
- **THEN** the command SHALL NOT silently record all traffic
- **AND** it prompts for setup in interactive mode or fails with an actionable error in non-interactive mode

### Requirement: Recording config supports presets and manual allowlists
The config SHALL support both named presets and explicit allowlisted domains/paths.

#### Scenario: Claude preset expands to model API rules
- **WHEN** the config uses preset `claude`
- **THEN** the active recording rules include domain `api.anthropic.com`
- **AND** the active path filters include `/v1/messages` and `/v1/messages/count_tokens`

#### Scenario: Manual gateway domain is saved
- **WHEN** the user configures a gateway URL such as `https://gateway.example.com/anthropic`
- **THEN** the config stores the host `gateway.example.com`
- **AND** it stores path filters derived from the selected mode or entered by the user

#### Scenario: CLI options override config for one run
- **WHEN** the user runs `ccwhat proxy --domain example.com --path /v1/messages`
- **THEN** that process records according to the CLI-provided domain/path
- **AND** it does not permanently modify the saved config unless the user also requests saving

### Requirement: Config validation prevents unsafe recording
The system SHALL validate config before payload recording starts.

#### Scenario: Empty allowlist is invalid for proxy recording
- **WHEN** active config has no domains and no preset-derived domains
- **THEN** payload recording does not start
- **AND** the terminal explains how to run `ccwhat setup` or `ccwhat discover`

#### Scenario: Invalid domain is rejected
- **WHEN** a configured domain contains a URL scheme, path traversal, whitespace, or an empty value
- **THEN** config validation fails with a user-facing error

#### Scenario: Path filters are normalized
- **WHEN** the user enters path filters without a leading slash
- **THEN** the system stores and applies them with a leading slash

### Requirement: Redaction defaults are configurable and safe
The config SHALL include default redaction rules for sensitive headers and header name patterns.

#### Scenario: Default sensitive headers are configured
- **WHEN** config is initialized
- **THEN** redaction includes `authorization`, `cookie`, `set-cookie`, `x-api-key`, and `proxy-authorization`

#### Scenario: Header name patterns are configured
- **WHEN** config is initialized
- **THEN** header names containing `token`, `secret`, or `key` are marked for redaction unless explicitly allowed by future configuration

### Requirement: Body size limits are configurable
The config SHALL define a maximum request/response body size to persist per record.

#### Scenario: Default body size limit
- **WHEN** config is initialized
- **THEN** `max_body_bytes` is set to a finite default value

#### Scenario: Body exceeding limit is truncated
- **WHEN** a matching request or response body exceeds `max_body_bytes`
- **THEN** the persisted record contains truncated body content
- **AND** includes metadata indicating truncation and original observed size when available
