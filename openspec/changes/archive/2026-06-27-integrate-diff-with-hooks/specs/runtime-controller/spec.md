## MODIFIED Requirements

### Requirement: Runtime controller 支持 step endpoint
系统 SHALL 提供 POST `/step` endpoint，接收工具调用信息并记录 diff。

#### Scenario: step endpoint 接收 Write 操作
- **WHEN** controller 收到 POST `/step`
- **AND** body 包含 `tool_name="Write"` 和 `file_path`
- **THEN** 系统 SHALL 调用 `staging.record_step("Write", file_path)`
- **AND** 系统 SHALL 返回 `{"ok": true}`

#### Scenario: step endpoint 接收 Edit 操作
- **WHEN** controller 收到 POST `/step`
- **AND** body 包含 `tool_name="Edit"` 和 `file_path`
- **THEN** 系统 SHALL 调用 `staging.record_step("Edit", file_path)`
- **AND** 系统 SHALL 返回 `{"ok": true}`

#### Scenario: step endpoint 拒绝无效请求
- **WHEN** controller 收到 POST `/step` 但缺少 `tool_name` 或 `file_path`
- **THEN** 系统 SHALL 返回 `{"ok": false, "error": "..."}`

#### Scenario: step endpoint 检查 active task
- **WHEN** controller 收到 POST `/step` 但没有 active task
- **THEN** 系统 SHALL 返回 `{"ok": false, "error": "no active task"}`
