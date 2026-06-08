## MODIFIED Requirements

### Requirement: Run 模式 Agent 推断
系统 MUST 在 `ccwhat -- <target>` 启动模式下根据目标命令推断 observed agent 类型，并把该类型传给 viewer 后端用于选择 Log Adapter；系统 MUST NOT 将目标命令参数 `target_args` 直接作为报告生成 analyzer command。

#### Scenario: 推断 Claude
- **WHEN** 用户运行 `ccwhat -- claude` 或 `ccwhat -- claude-code`
- **THEN** 系统必须推断 observed agent 为 `claude`

#### Scenario: 推断 Codex
- **WHEN** 用户运行 `ccwhat -- codex`
- **THEN** 系统必须推断 observed agent 为 `codex`

#### Scenario: 推断 OpenCode
- **WHEN** 用户运行 `ccwhat -- opencode`、`ccwhat -- open-code` 或 `ccwhat -- open_code`
- **THEN** 系统必须推断 observed agent 为 `opencode`

#### Scenario: 未实现 agent 不阻塞目标命令
- **WHEN** 用户通过 run 模式启动尚未实现日志 adapter 的 agent
- **THEN** 系统必须避免因 viewer adapter 未实现而使目标命令崩溃，并必须输出清晰 warning 或 fallback 提示

#### Scenario: target args 不传给 analyzer
- **WHEN** 用户运行 `ccwhat -- codex` 或 `ccwhat -- opencode`
- **THEN** 系统不得把 `target_args` 直接传给 Viewer Server 的 `analyzer_cmd`，报告生成必须通过 Analyzer Adapter 或显式 analyzer 配置选择命令
