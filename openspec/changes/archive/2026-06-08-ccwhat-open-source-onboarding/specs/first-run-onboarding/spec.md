## ADDED Requirements

### Requirement: First-run onboarding starts when recording config is missing
The system SHALL guide interactive users through setup before any payload recording command runs without a valid recording config.

#### Scenario: run triggers setup
- **WHEN** an interactive user runs `ccwhat -- claude` or `ccwhat -- <custom-cli>` and no valid recording config exists
- **THEN** the first-run onboarding wizard starts before launching the target command

#### Scenario: proxy triggers setup
- **WHEN** an interactive user runs `ccwhat proxy` and no valid recording config exists
- **THEN** the first-run onboarding wizard starts before payload recording starts

#### Scenario: non-interactive command fails safely
- **WHEN** a non-interactive process runs a payload-recording command without config or explicit domains
- **THEN** the command exits non-zero
- **AND** prints an actionable message that includes `ccwhat setup`, `ccwhat discover`, and `--domain`

### Requirement: Onboarding offers three setup modes
The wizard SHALL offer official Claude API, gateway/base URL, and discovery modes.

#### Scenario: Official Claude mode
- **WHEN** the user selects official Claude API mode
- **THEN** the wizard proposes the `claude` preset
- **AND** shows `api.anthropic.com` and the model API paths that will be recorded before saving

#### Scenario: Gateway mode with detected base URL
- **WHEN** environment variables include a supported base URL such as `ANTHROPIC_BASE_URL`
- **THEN** the wizard presents the detected host as a candidate gateway domain
- **AND** asks the user to confirm before saving it

#### Scenario: Gateway mode without detected base URL
- **WHEN** the user selects gateway mode and no supported base URL environment variable is set
- **THEN** the wizard prompts the user to enter a gateway URL or domain
- **AND** validates the entered value before saving

#### Scenario: Unsure mode starts discovery
- **WHEN** the user selects the "not sure" mode
- **THEN** the wizard starts metadata-only discovery
- **AND** asks the user to launch or exercise their AI coding CLI so candidate endpoints can be observed

### Requirement: Onboarding copy makes privacy boundaries explicit
The wizard SHALL clearly state what will and will not be recorded.

#### Scenario: Recording scope is shown before save
- **WHEN** the wizard is ready to save config
- **THEN** it displays the exact domains and paths selected for payload recording
- **AND** states that login, updater, GitHub, telemetry, and unrelated traffic are not recorded unless explicitly allowlisted

#### Scenario: Redaction summary is shown
- **WHEN** the wizard displays the confirmation screen
- **THEN** it summarizes default header redaction and body size limits

### Requirement: Onboarding can be rerun
The system SHALL allow users to rerun setup and replace or extend saved recording config.

#### Scenario: Manual setup command
- **WHEN** the user runs `ccwhat setup`
- **THEN** the wizard starts even if onboarding was previously completed

#### Scenario: Existing config is shown
- **WHEN** setup starts and a config already exists
- **THEN** the wizard displays the current domains, paths, preset, and config file location

#### Scenario: User can keep existing config
- **WHEN** setup starts with existing config and the user chooses not to change it
- **THEN** no config file changes are written

### Requirement: Onboarding supports non-interactive setup flags
The setup command SHALL support non-interactive configuration for scripts and CI.

#### Scenario: Save Claude preset non-interactively
- **WHEN** the user runs `ccwhat setup --preset claude --yes`
- **THEN** the system writes config for the Claude preset without prompting

#### Scenario: Save manual domain non-interactively
- **WHEN** the user runs `ccwhat setup --domain gateway.example.com --path /v1/messages --yes`
- **THEN** the system writes config for that domain/path without prompting

#### Scenario: Non-interactive setup validates input
- **WHEN** the user runs setup with invalid non-interactive options
- **THEN** the command exits non-zero
- **AND** prints validation errors without writing partial config
