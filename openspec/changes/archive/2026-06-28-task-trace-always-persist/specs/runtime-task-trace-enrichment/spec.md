## MODIFIED Requirements

### Requirement: finish 时从 session 日志提取 Agent 行为轨迹

系统 SHALL 在 `finish_task()` 执行时，从 proxy session JSONL 日志中按任务时间窗口提取 Agent 行为字段，写入 `task_trace.json`。

#### Scenario: 正常提取并写入 task_trace.json
- **WHEN** controller 成功执行 `finish` 且 session JSONL 日志存在
- **THEN** 系统 SHALL 按 start/finish 时间戳切出任务时间窗口内的事件
- **AND** 系统 SHALL 从切出的事件中提取 commands、test_commands、files.read、files.changed、changes、patches、errors、final_claim
- **AND** 系统 SHALL 将提取结果写入 `tasks/<task-id>/task_trace.json`
- **AND** `task.json` 中 `evidence_availability.task_trace` SHALL 为 true
- **AND** `task_trace.json` 中 `extraction_status` SHALL 为 `"ok"`

#### Scenario: session 日志不存在时仍写入 task_trace.json
- **WHEN** controller 成功执行 `finish` 但 session JSONL 日志不存在
- **THEN** 系统 SHALL NOT 中断 finish 流程
- **AND** 系统 SHALL 写入包含 `extraction_status` 为 `"log_not_found"` 的 `task_trace.json`
- **AND** `task.json` 中 `evidence_availability.task_trace` SHALL 为 true

#### Scenario: 不支持的 agent 仍写入 task_trace.json
- **WHEN** agent 不是 claude
- **THEN** 系统 SHALL 写入包含 `extraction_status` 为 `"unsupported_agent"` 的 `task_trace.json`
- **AND** `task.json` 中 `evidence_availability.task_trace` SHALL 为 true

#### Scenario: 提取结果为空时仍写入
- **WHEN** 时间窗口内的事件不含任何 commands 或 changes
- **THEN** 系统 SHALL 仍然写入 `task_trace.json`
- **AND** `extraction_status` SHALL 为 `"ok"`（提取成功，只是无数据）或 `"no_events"`（无时间窗事件）
- **AND** `evidence_availability.task_trace` SHALL 为 true

### Requirement: task_trace.json 结构与 Dataset v1 trace 对齐

`task_trace.json` 的字段结构 SHALL 与 Dataset v1 的 `traces/<trace_id>.json` 保持一致，使诊断引擎可以统一消费两种数据来源。

#### Scenario: task_trace.json 包含必要字段
- **WHEN** `task_trace.json` 被写入
- **THEN** 文件 SHALL 包含以下顶层字段：task_id、run_id、agent、extraction_status、extraction_status_reason、time_window、events、commands、test_commands、files、changes、patches、errors、final_claim、repo_state
- **AND** `files` SHALL 包含 `read` 和 `changed` 两个子字段
- **AND** `time_window` SHALL 包含 `started_at` 和 `finished_at`

#### Scenario: repo_state 与 task.json git 字段一致
- **WHEN** `task_trace.json` 被写入
- **THEN** `repo_state.base_commit` SHALL 等于 `task.json` 中的 `git.before_commit`
- **AND** `repo_state.head_commit` SHALL 等于 `task.json` 中的 `git.after_commit`
- **AND** 当提取失败时，`repo_state.base_commit` 和 `repo_state.head_commit` SHALL 为 `null`
