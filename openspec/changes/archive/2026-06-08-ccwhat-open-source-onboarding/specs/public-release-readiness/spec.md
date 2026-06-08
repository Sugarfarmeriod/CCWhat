## ADDED Requirements

### Requirement: Public release repository contains only public-safe tracked files
The release commit SHALL NOT contain tracked internal packages, internal diagnostic reports, raw captures, private notebooks, generated exports, real tokens, private paths, or internal service references.

#### Scenario: Legacy package tree is not tracked
- **WHEN** maintainers inspect the release commit with `git ls-files`
- **THEN** no tracked path begins with `deep_ai_analysis/`
- **AND** no tracked path begins with `deep_ai_analysis.egg-info/`

#### Scenario: Internal sample data is not tracked
- **WHEN** maintainers inspect the release commit with `git ls-files`
- **THEN** no tracked path begins with `sample_data/`
- **AND** no tracked raw request/response capture or generated diagnostic export is included

#### Scenario: Internal docs are removed or sanitized
- **WHEN** maintainers scan tracked documentation before release
- **THEN** docs contain no internal object-storage URLs, internal domains, private employee paths, old wheel filenames, or private diagnostic workflow notes
- **AND** any remaining legacy-name references are explicitly for compatibility or migration

#### Scenario: Public-safe scan passes
- **WHEN** maintainers run the documented pre-release scan
- **THEN** it fails on real bearer tokens, API keys, internal domains, private local paths, internal repository names, and generated capture directories
- **AND** it ignores only reviewed compatibility references such as legacy import package support

### Requirement: README is the first public onboarding surface
The README SHALL provide enough public information for a new user to install, configure, run, troubleshoot, and understand privacy boundaries without internal context.

#### Scenario: Repository URL is public and real
- **WHEN** a user reads the README install-from-source section
- **THEN** the GitHub URL points to the real public repository
- **AND** it does not contain placeholder organizations such as `your-org`

#### Scenario: Quick start is command-complete
- **WHEN** a user follows the README quick start
- **THEN** it includes install commands, `ccwhat -- claude`, viewer startup, and where local logs are written

#### Scenario: Gateway users can configure domains
- **WHEN** a user connects Claude Code through a gateway, proxy, OpenAI-compatible router, or Anthropic-compatible base URL
- **THEN** the README explains explicit domain/path configuration and metadata-only discovery
- **AND** it states that payload recording requires user-confirmed allowlists

#### Scenario: Privacy boundaries are visible
- **WHEN** a user reads the README
- **THEN** it explains local-only storage, MITM certificate requirements, header redaction, body truncation, domain/path filtering, and discovery metadata limits

### Requirement: Release checklist is executable from a clean environment
The release checklist SHALL use commands supported by the project's declared dependencies and SHALL verify both source tree and built artifacts before publication.

#### Scenario: Test command matches dependencies
- **WHEN** maintainers follow the release checklist in a clean environment
- **THEN** the documented test command succeeds after installing declared runtime and test dependencies
- **AND** the checklist does not require undeclared tools such as `pytest` unless they are declared as dev/test dependencies

#### Scenario: Build artifacts exclude legacy packages
- **WHEN** maintainers build the source distribution and wheel
- **THEN** the artifacts contain `ccwhat*` and `viewer*` package files
- **AND** they do not contain `deep_ai_analysis*`, `sample_data*`, raw captures, internal notebooks, or private diagnostic docs

#### Scenario: First public release can be tagged
- **WHEN** repository scan, tests, CLI smoke tests, OpenSpec validation, and artifact inspection all pass
- **THEN** maintainers may tag and publish the first public release
- **AND** the release notes mention the `ccwhat` rename and legacy import/config compatibility boundaries
