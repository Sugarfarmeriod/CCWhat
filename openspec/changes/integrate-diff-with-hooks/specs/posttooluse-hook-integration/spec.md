## ADDED Requirements

### Requirement: PostToolUse Hook 捕获文件修改
系统 SHALL 在 PostToolUse 事件时，提取工具信息并通知 controller。

#### Scenario: Hook 条件激活
- **WHEN** `CCWHAT_ENABLED=1` 时 PostToolUse 事件触发
- **THEN** Hook SHALL 解析 payload 并通知 controller
- **WHEN** `CCWHAT_ENABLED` 未设置时
- **THEN** Hook SHALL 立即 exit 0，不执行任何操作

#### Scenario: Hook 提取 Write 工具信息
- **WHEN** Agent 执行 Write 工具
- **THEN** Hook SHALL 提取 `tool_name="Write"`
- **AND** Hook SHALL 提取 `tool_input.file_path`
- **AND** Hook SHALL POST 到 controller `/step` endpoint

#### Scenario: Hook 提取 Edit 工具信息
- **WHEN** Agent 执行 Edit 工具
- **THEN** Hook SHALL 提取 `tool_name="Edit"`
- **AND** Hook SHALL 提取 `tool_input.file_path`
- **AND** Hook SHALL POST 到 controller `/step` endpoint

#### Scenario: Hook 忽略非文件工具
- **WHEN** Agent 执行 Bash、Read 等非文件修改工具
- **THEN** Hook SHALL 不发送请求到 controller

### Requirement: Hook 脚本可独立执行
系统 SHALL 提供可执行的 hook 脚本，处理 payload 并调用 controller。

#### Scenario: Hook 脚本处理 JSON payload
- **WHEN** Hook 脚本从 stdin 接收 JSON payload
- **THEN** Hook SHALL 正确解析 `tool_name` 和 `tool_input.file_path`
- **AND** Hook SHALL 发送 HTTP POST 请求
