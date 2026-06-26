## ADDED Requirements

### Requirement: ccwhat CLI 提供 start 子命令
系统 SHALL 提供 `ccwhat start` 命令，设置环境变量后启动 Claude Code。

#### Scenario: ccwhat start 设置环境变量
- **WHEN** 用户执行 `ccwhat start`
- **THEN** 系统 SHALL 设置 `CCWHAT_ENABLED=1`
- **AND** 系统 SHALL 设置 `CCWHAT_RUNTIME_CONTROL_PORT`
- **AND** 系统 SHALL 设置 `CCWHAT_RUNTIME_TOKEN`
- **AND** 系统 SHALL 启动 runtime controller
- **AND** 系统 SHALL 启动 Claude Code

#### Scenario: ccwhat start 继承现有 runtime 功能
- **WHEN** 用户执行 `ccwhat start`
- **THEN** 系统 SHALL 复用 `ccwhat -- claude` 的 runtime 初始化逻辑
- **AND** 系统 SHALL 创建独立的 run 目录
- **AND** 系统 SHALL 分配独立的 controller 端口
