## ADDED Requirements

### Requirement: Discovery records metadata only
The discovery mode SHALL observe proxied traffic metadata without persisting request bodies, response bodies, full headers, cookies, or authorization values.

#### Scenario: Metadata fields captured
- **WHEN** discovery observes an HTTP request and response
- **THEN** it may store timestamp, host, method, path, status code, response content type, request content type, and whether the response appears to be streaming
- **AND** it does not store request body, response body, or sensitive header values

#### Scenario: Authorization is never stored in discovery
- **WHEN** a discovered request contains authorization-like headers
- **THEN** discovery output does not include the header value
- **AND** it may only indicate that a redacted sensitive header was present

### Requirement: Discovery scores likely model API candidates
Discovery SHALL identify likely model API endpoints and explain why each candidate is recommended.

#### Scenario: Anthropic messages endpoint candidate
- **WHEN** discovery observes a POST request to `/v1/messages`
- **THEN** the host/path is marked as a likely model API candidate
- **AND** the reason mentions the Anthropic Messages endpoint shape

#### Scenario: Streaming response candidate
- **WHEN** discovery observes a POST response with `text/event-stream`
- **THEN** the host/path is marked as a likely model API candidate
- **AND** the reason mentions streaming model response content type

#### Scenario: Non-model host is not preselected
- **WHEN** discovery observes hosts used for downloads, source control, auth, telemetry, or unrelated GET requests
- **THEN** those hosts are listed as observed but are not preselected for payload recording

### Requirement: Discovery confirmation saves recording config
Discovery SHALL ask the user to confirm candidate endpoints before saving them as payload recording rules.

#### Scenario: Candidate confirmation
- **WHEN** discovery has at least one likely candidate
- **THEN** it displays candidates with host, path, method, content type, and reason
- **AND** prompts the user to choose which candidates to save

#### Scenario: Save selected candidates
- **WHEN** the user confirms selected candidates
- **THEN** the system writes or updates `~/.ccwhat/config.toml`
- **AND** future proxy recording uses the selected domains and paths

#### Scenario: No candidates found
- **WHEN** discovery ends without likely model API candidates
- **THEN** it prints observed hosts and troubleshooting guidance
- **AND** it does not write an unsafe wildcard recording config

### Requirement: Discovery can wrap a target command
The system SHALL support running discovery around a target AI coding CLI command.

#### Scenario: Discover with target command
- **WHEN** the user runs `ccwhat discover -- claude`
- **THEN** the target command runs with proxy and CA environment variables injected
- **AND** discovery observes traffic until the target command exits or the user stops discovery

#### Scenario: Discover without target command
- **WHEN** the user runs `ccwhat discover`
- **THEN** the system starts a local proxy and prints instructions for configuring or launching an AI coding CLI through it

#### Scenario: Discovery exits cleanly
- **WHEN** the user presses Ctrl+C during discovery
- **THEN** discovery stops the managed proxy
- **AND** prints any candidates observed before shutdown
