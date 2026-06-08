## ADDED Requirements

### Requirement: Public package identity uses ccwhat
The project SHALL expose `ccwhat` as the public package name, Python import package, console command, help program name, and user-facing product name.

#### Scenario: Installed command is ccwhat
- **WHEN** a user installs the package with `pip install .` or `pip install -e .`
- **THEN** the `ccwhat` command is available on PATH
- **AND** the `deep-ai-analysis` command is not documented as the primary command

#### Scenario: Python package is ccwhat
- **WHEN** code imports the project package
- **THEN** the import path is `ccwhat`
- **AND** public package metadata names the distribution `ccwhat`

#### Scenario: cc command is not registered
- **WHEN** the package is installed
- **THEN** it SHALL NOT register a top-level `cc` console command
- **AND** documentation SHALL NOT instruct users to invoke `cc`

### Requirement: Local application data uses ~/.ccwhat
The application SHALL store new configuration and logs under `~/.ccwhat` by default.

#### Scenario: Default config path
- **WHEN** the application reads or writes user configuration without an explicit config path
- **THEN** it uses `~/.ccwhat/config.toml`

#### Scenario: Default raw log path
- **WHEN** the proxy writes raw request/response logs without an explicit output path
- **THEN** it writes under `~/.ccwhat/raw-req-resp/`

#### Scenario: Legacy path remains readable
- **WHEN** legacy data exists under `~/.deep-ai-analysis`
- **THEN** migration-aware commands can read it when needed
- **AND** new writes still use `~/.ccwhat` unless the user explicitly chooses a legacy path

### Requirement: Public documentation contains no internal distribution links
Public-facing documentation and install scripts SHALL describe open-source installation paths and SHALL NOT reference internal package hosting, internal Git remotes, or internal object storage.

#### Scenario: README install commands are public
- **WHEN** a user opens the README
- **THEN** installation examples use public mechanisms such as PyPI, pipx, GitHub source install, or local editable install
- **AND** no install command references `example.com` hosts

#### Scenario: Release docs are public
- **WHEN** release documentation is included in the public repository
- **THEN** it describes public release targets such as PyPI or GitHub Releases
- **AND** it does not instruct maintainers to upload artifacts to internal S3 or internal package stores

### Requirement: Public repository excludes internal diagnostic data
The public repository SHALL exclude internal Claude logs, private notebooks, internal sample payloads, local build artifacts, and generated diagnostic captures.

#### Scenario: Internal data directories are ignored
- **WHEN** a developer runs `git status` after local captures are generated
- **THEN** `.ccwhat/`, `.deep-ai-analysis/`, raw request/response logs, build outputs, wheel artifacts, notebook scratch data, and local diagnostic exports are ignored

#### Scenario: Public samples are sanitized
- **WHEN** sample data is included in the repository
- **THEN** it contains no real API tokens, internal domains, private user paths, internal service names, internal IP addresses, or proprietary business code
