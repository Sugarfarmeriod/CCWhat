## ADDED Requirements

### Requirement: Claude Code shows CCWhat slash commands
系统 SHALL 在 `ccwhat -- claude` 启动前安装或检查 Claude Code 的 CCWhat slash command integration，使 CCWhat 命令出现在 Claude Code 原生 slash 菜单中。

#### Scenario: CCWhat commands are installed before launch
- **WHEN** 用户执行 `ccwhat -- claude`
- **THEN** 系统 SHALL 检查 Claude Code CCWhat integration
- **AND** 如果 integration 缺失，系统 SHALL 安装 CCWhat 管理的 command 或 skill 文件
- **AND** 如果 integration 已过期，系统 SHALL 升级 CCWhat 管理的文件

#### Scenario: Slash menu contains task commands
- **WHEN** Claude Code 启动并显示原生 slash 菜单
- **THEN** 用户 SHALL 能看到 CCWhat Task 命令
- **AND** 菜单 SHALL 至少包含 start 和 finish 命令

### Requirement: Claude Code slash commands call local CCWhat controller
系统 SHALL 将 Claude Code 中触发的 CCWhat slash command 路由到当前 runtime run 的本地 controller。

#### Scenario: Start command calls local controller
- **WHEN** 用户在 Claude Code 中选择 CCWhat start 命令并提供 title
- **THEN** 系统 SHALL 调用当前 run 的 controller start route
- **AND** 系统 SHALL 创建 active task
- **AND** 系统 SHALL 向用户显示 start 成功反馈

#### Scenario: Finish command calls local controller
- **WHEN** 用户在 Claude Code 中选择 CCWhat finish 命令
- **THEN** 系统 SHALL 调用当前 run 的 controller finish route
- **AND** 系统 SHALL finalize active task
- **AND** 系统 SHALL 向用户显示 finish 成功反馈

### Requirement: Claude Code command is not sent to model
系统 SHALL 阻止 CCWhat Task slash command 作为普通 prompt 发送给 Claude 模型。

#### Scenario: Start command is locally intercepted
- **WHEN** 用户在 Claude Code 中触发 CCWhat start 命令
- **THEN** 系统 SHALL 在 prompt 被发送给模型前拦截该命令
- **AND** 系统 SHALL 阻止该命令作为用户 prompt 继续处理
- **AND** runtime evidence SHALL 记录 model_visible 为 false

#### Scenario: Finish command is locally intercepted
- **WHEN** 用户在 Claude Code 中触发 CCWhat finish 命令
- **THEN** 系统 SHALL 在 prompt 被发送给模型前拦截该命令
- **AND** 系统 SHALL 阻止该命令作为用户 prompt 继续处理
- **AND** runtime evidence SHALL 记录 model_visible 为 false

### Requirement: Integration files are managed safely
系统 SHALL 只自动写入或更新由 CCWhat 管理的 Claude Code integration 文件。

#### Scenario: Managed files can be upgraded
- **WHEN** Claude Code integration 文件存在且包含 CCWhat managed marker
- **THEN** 系统 SHALL 可以更新该文件到当前 integration version

#### Scenario: User files are not overwritten
- **WHEN** 目标 command、skill 或 hook 文件已存在但不包含 CCWhat managed marker
- **THEN** 系统 SHALL NOT 覆盖该文件
- **AND** 系统 SHALL 返回明确冲突错误

### Requirement: Command naming can degrade when colon names are unsupported
系统 SHALL 优先使用 `/ccwhat:start` 和 `/ccwhat:finish` 命名；如果 Claude Code 不支持冒号命令名，系统 SHALL 使用等价降级命名。

#### Scenario: Colon names supported
- **WHEN** Claude Code 支持冒号命令名
- **THEN** 菜单命令 SHALL 使用 `/ccwhat:start` 和 `/ccwhat:finish`

#### Scenario: Colon names unsupported
- **WHEN** Claude Code 不支持冒号命令名
- **THEN** 菜单命令 SHALL 使用 `/ccwhat-start` 和 `/ccwhat-finish`
- **AND** 命令描述 SHALL 明确显示 CCWhat Task start/finish 语义

