## REMOVED Requirements

### Requirement: start-mc 透传额外参数给 mc
**Reason**: `start-mc` is removed from the public workflow because it hard-codes the internal `mc --code` command.
**Migration**: Use `ccwhat -- <command...>`; arguments after `--` are passed to the target command in order.

#### Scenario: run preserves passthrough arguments
- **WHEN** 用户执行 `ccwhat -- claude --resume /some/path --flag`
- **THEN** 系统运行 `claude --resume /some/path --flag`，参数顺序与输入一致
