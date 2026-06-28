## ADDED Requirements

### Requirement: extraction_status 字段标识提取结果状态

`task_trace.json` SHALL 包含 `extraction_status` 字段，显式标识 trace 提取的结果状态。

#### Scenario: 正常提取返回 ok 状态
- **WHEN** trace 提取成功
- **THEN** `extraction_status` SHALL 为 `"ok"`
- **AND** `extraction_status_reason` SHALL 为 `null`

#### Scenario: 不支持的 agent 返回 unsupported_agent
- **WHEN** agent 不是 claude
- **THEN** `extraction_status` SHALL 为 `"unsupported_agent"`
- **AND** `extraction_status_reason` SHALL 包含 agent 名称说明

#### Scenario: 时间窗口解析失败返回 invalid_time_bounds
- **WHEN** started_at 或 finished_at 无法解析为有效时间戳
- **THEN** `extraction_status` SHALL 为 `"invalid_time_bounds"`
- **AND** `extraction_status_reason` SHALL 说明失败原因

#### Scenario: 日志文件不存在返回 log_not_found
- **WHEN** 项目目录或 session JSONL 日志文件不存在
- **THEN** `extraction_status` SHALL 为 `"log_not_found"`
- **AND** `extraction_status_reason` SHALL 说明缺失的资源

#### Scenario: 时间窗内无事件返回 no_events
- **WHEN** 时间窗口过滤后事件列表为空
- **THEN** `extraction_status` SHALL 为 `"no_events"`
- **AND** `extraction_status_reason` SHALL 为 `null`

### Requirement: task_trace.json 始终包含完整字段结构

无论提取状态如何，`task_trace.json` SHALL 始终包含所有顶层字段，异常情况下使用空值或 null 填充。

#### Scenario: 异常状态包含完整结构
- **WHEN** `extraction_status` 不为 `"ok"`
- **THEN** `task_trace.json` SHALL 包含所有标准字段
- **AND** `events`, `commands`, `test_commands`, `changes`, `patches`, `errors` SHALL 为空列表
- **AND** `final_claim`, `repo_state.cwd`, `repo_state.base_commit`, `repo_state.head_commit` SHALL 为 `null`
- **AND** `files.read`, `files.changed` SHALL 为空列表
- **AND** `time_window.started_at`, `time_window.finished_at` SHALL 为 `null`（如时间解析失败）或原值

### Requirement: trace_extractor 返回类型始终为 dict

`trace_extractor.extract_task_trace()` 的返回类型 SHALL 为 `dict`，禁止返回 `None`。

#### Scenario: 提取函数永不返回 None
- **WHEN** 调用 `extract_task_trace()` 传入任何参数
- **THEN** 返回值 SHALL 始终为非空的 dict
- **AND** 调用方无需检查 `if trace is not None`
