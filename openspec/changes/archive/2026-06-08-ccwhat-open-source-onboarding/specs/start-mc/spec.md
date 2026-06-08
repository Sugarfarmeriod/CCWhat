## REMOVED Requirements

### Requirement: Launch mc with proxy environment
**Reason**: The public open-source workflow must not depend on the internal `mc` command or hard-code `mc --code`.
**Migration**: Use `ccwhat -- claude` for Claude Code or `ccwhat -- <command...>` for custom CLIs.

#### Scenario: Generic launcher replaces start-mc
- **WHEN** a user needs to launch an AI coding CLI through ccwhat
- **THEN** documentation and help direct them to `ccwhat -- <command...>`

### Requirement: mc not found error
**Reason**: `ccwhat` no longer treats `mc` as a required or special command.
**Migration**: Missing target command errors are handled by the generic `run` command.

#### Scenario: Missing command handled by run
- **WHEN** the target command passed to `ccwhat -- <command...>` is not found
- **THEN** the generic launcher prints an error naming that target command

### Requirement: CA certificate warning
**Reason**: CA certificate handling moves to the generic `run`, `proxy`, and onboarding flows.
**Migration**: Use `ccwhat -- <command...>` or `ccwhat proxy`; both commands display CA guidance when required.

#### Scenario: CA warning handled by generic commands
- **WHEN** a required CA certificate is missing
- **THEN** `ccwhat run` or `ccwhat proxy` prints the relevant certificate guidance
