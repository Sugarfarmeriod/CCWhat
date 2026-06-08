## ADDED Requirements

### Requirement: Viewer displays recording configuration
The viewer SHALL display the active recording configuration used by the running server.

#### Scenario: Recording config panel visible
- **WHEN** the viewer loads successfully
- **THEN** the page displays the active recording domains, path filters, raw log directory, and config file path

#### Scenario: No config state visible
- **WHEN** the server reports that no valid recording config exists
- **THEN** the viewer displays a setup-required state
- **AND** includes commands for `ccwhat setup` and `ccwhat discover`

#### Scenario: Config redaction summary visible
- **WHEN** the viewer displays recording configuration
- **THEN** it summarizes that sensitive headers are redacted and body size limits may truncate logs

### Requirement: Viewer provides actionable empty states
The viewer SHALL explain likely causes when no model request logs are available.

#### Scenario: No raw logs found
- **WHEN** the viewer has session logs but no matching raw request/response logs
- **THEN** it displays an empty state explaining that no model API requests were recorded
- **AND** suggests checking configured domains, CA trust, and whether the AI coding CLI was launched via `ccwhat run`

#### Scenario: Gateway setup hint
- **WHEN** active config uses no gateway domain and no logs are found
- **THEN** the viewer suggests `ccwhat discover -- <command...>` for users with gateways or unknown providers

#### Scenario: Recorded domain mismatch hint
- **WHEN** discovery metadata or server status indicates observed hosts that are not in the recording allowlist
- **THEN** the viewer shows those hosts as possible configuration candidates without exposing payload data

### Requirement: Viewer exposes recording health API
The server SHALL expose a local API endpoint that returns recording configuration and health status for the static viewer.

#### Scenario: Get recording status
- **WHEN** the frontend calls `GET /api/recording/status`
- **THEN** the server returns JSON containing configured domains, path filters, raw log directory, config path, latest raw log timestamp if available, and whether config is valid

#### Scenario: Status endpoint avoids secrets
- **WHEN** `GET /api/recording/status` returns config data
- **THEN** the response does not include API keys, authorization values, cookies, or unredacted sensitive header values

### Requirement: Viewer copy uses ccwhat
The viewer SHALL use `ccwhat` in visible commands and product copy.

#### Scenario: Import command copy
- **WHEN** the viewer displays an import command
- **THEN** the command uses `ccwhat import`

#### Scenario: Setup guidance copy
- **WHEN** the viewer displays setup or troubleshooting guidance
- **THEN** the guidance uses `ccwhat setup`, `ccwhat discover`, `ccwhat run`, and `ccwhat proxy`

### Requirement: Report analysis uses launched CLI command
When the viewer is started by `ccwhat -- <cli> [args...]`, report generation SHALL use that same target CLI command for analysis.

#### Scenario: Managed viewer report uses launch command
- **WHEN** the user starts ccwhat with `ccwhat -- mc --code`
- **AND** clicks report generation in the viewer started by that command
- **THEN** the analysis subprocess is launched with `mc --code`
- **AND** the generated prompt is sent to that subprocess through stdin

#### Scenario: Standalone viewer keeps analyzer fallback
- **WHEN** the user starts the viewer with `ccwhat web`
- **THEN** report generation uses the configured analyzer fallback behavior
- **AND** `CCWHAT_ANALYZE_CMD` can still override the default analyzer command
