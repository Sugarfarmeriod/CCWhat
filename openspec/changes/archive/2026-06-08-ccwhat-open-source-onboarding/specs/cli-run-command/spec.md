## ADDED Requirements

### Requirement: run launches arbitrary commands through ccwhat proxy
The top-level passthrough command `ccwhat -- <command...>` SHALL launch a user-provided command with local proxy and certificate environment variables injected. The hidden `run` command MAY remain as a compatibility alias for the same behavior.

#### Scenario: Launch Claude Code
- **WHEN** the user runs `ccwhat -- claude`
- **THEN** the system starts or reuses a local ccwhat proxy
- **AND** launches `claude` with proxy and CA environment variables injected
- **AND** returns the target command exit code

#### Scenario: Launch custom command with arguments
- **WHEN** the user runs `ccwhat -- my-ai-cli --model sonnet --resume`
- **THEN** the system launches `my-ai-cli --model sonnet --resume`
- **AND** preserves argument order exactly after `--`

#### Scenario: Missing target command
- **WHEN** the user runs `ccwhat run` without a target command
- **THEN** the command exits non-zero
- **AND** prints usage examples including `ccwhat -- <command>`

### Requirement: run manages proxy lifecycle
The `run` command SHALL start a managed proxy when needed and stop it when the target command exits.

#### Scenario: Managed proxy starts when port is free
- **WHEN** the configured proxy port is not in use
- **THEN** `ccwhat run` starts a managed local proxy bound to `127.0.0.1`
- **AND** prints the recording domains, paths, log directory, and viewer hint

#### Scenario: Existing proxy is reused
- **WHEN** a compatible ccwhat proxy is already listening on the configured port
- **THEN** `ccwhat run` reuses it
- **AND** does not start a duplicate proxy

#### Scenario: Occupied non-ccwhat port is rejected
- **WHEN** the configured proxy port is already occupied by a process that cannot be identified as a compatible ccwhat proxy
- **THEN** `ccwhat run` exits non-zero before launching the target command
- **AND** prints a port conflict message that tells the user to choose another port or stop the existing process

#### Scenario: Stale proxy marker is ignored
- **WHEN** a proxy marker exists but its process is no longer alive
- **THEN** `ccwhat run` treats the marker as stale
- **AND** removes or replaces the stale marker before deciding whether to start a managed proxy

#### Scenario: Managed proxy startup failure is explicit
- **WHEN** `ccwhat run` starts a managed proxy but the process exits or fails to bind the configured port
- **THEN** `ccwhat run` removes any marker it created
- **AND** exits non-zero before launching the target command
- **AND** prints the proxy startup failure reason when available

#### Scenario: Managed proxy stops after command exits
- **WHEN** the target command exits
- **THEN** any proxy process started by `ccwhat run` is stopped
- **AND** the target command exit code is propagated

#### Scenario: Ctrl+C cleanup
- **WHEN** the user presses Ctrl+C while the target command is running
- **THEN** the signal is forwarded or the target command is terminated according to platform behavior
- **AND** any managed proxy is stopped before `ccwhat run` exits

### Requirement: run opens the viewer by default
The `run` command SHALL make the local viewer available by default without requiring a second terminal.

#### Scenario: Managed viewer starts when port is free
- **WHEN** the user runs `ccwhat -- claude` or the hidden compatibility command `ccwhat run -- claude` and the viewer port is free
- **THEN** `ccwhat run` starts a managed local viewer bound to `127.0.0.1`
- **AND** opens the browser to `http://127.0.0.1:<viewer-port>/claude-log.html`
- **AND** prints the viewer URL so the user can reopen it after closing the browser tab

#### Scenario: Existing viewer is reused
- **WHEN** the viewer port is already occupied
- **THEN** `ccwhat run` does not fail because of the viewer port
- **AND** prints and opens `http://127.0.0.1:<viewer-port>/claude-log.html`

#### Scenario: Managed viewer stops after command exits
- **WHEN** the target command exits
- **THEN** any viewer server started by `ccwhat run` is stopped
- **AND** proxy cleanup and target exit-code propagation still occur

#### Scenario: User disables viewer launch with top-level passthrough
- **WHEN** the user runs `ccwhat --no-web -- claude`
- **THEN** ccwhat does not start or open the viewer
- **AND** still launches the target command through the proxy

### Requirement: run injects proxy environment safely
The `run` command SHALL inject proxy variables without discarding unrelated user environment variables.

#### Scenario: Proxy environment variables injected
- **WHEN** `ccwhat run` launches a target command
- **THEN** the child environment includes `HTTPS_PROXY=http://127.0.0.1:<port>`
- **AND** includes `HTTP_PROXY=http://127.0.0.1:<port>`
- **AND** includes `NODE_EXTRA_CA_CERTS=<mitmproxy-ca-cert.pem>`

#### Scenario: Existing environment preserved
- **WHEN** the parent process has unrelated environment variables
- **THEN** the target command receives those variables unless `ccwhat run` explicitly overrides proxy or certificate variables

#### Scenario: NO_PROXY is preserved unless configured
- **WHEN** the parent process has `NO_PROXY`
- **THEN** `ccwhat run` preserves it unless the user explicitly requests a different value

### Requirement: run integrates with onboarding
The `run` command SHALL use onboarding before payload recording when no valid config exists.

#### Scenario: First run prompts setup
- **WHEN** an interactive user runs `ccwhat -- claude` or `ccwhat -- mc --code` with no valid config
- **THEN** the onboarding wizard runs before the target command starts

#### Scenario: Skip setup disables payload recording
- **WHEN** the user runs `ccwhat --no-setup -- claude` with no valid config
- **THEN** the command may launch the target through proxy for discovery or troubleshooting
- **AND** payload recording remains disabled
- **AND** the terminal clearly states that no request/response bodies will be recorded
