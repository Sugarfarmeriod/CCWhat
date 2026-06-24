## MODIFIED Requirements

### Requirement: Runtime task staging captures repo snapshots and diff
系统 SHALL 在 Task start/finish 时保存 git workspace 的 before/after 快照和真实 diff，并在 finish 时额外提取 Agent 行为轨迹写入 `task_trace.json`。

#### Scenario: Start captures repo_before
- **WHEN** controller 成功执行 `start`
- **THEN** 系统 SHALL 创建 `tasks/<task-id>/task.json`
- **AND** 系统 SHALL 创建 `tasks/<task-id>/control_events.jsonl`
- **AND** 系统 SHALL 保存 `tasks/<task-id>/repo_before.tar.gz`
- **AND** `task.json` SHALL 记录 `evidence_availability.repo_before` 为 true
- **AND** `task.json` SHALL 包含 `instruction`、`success_criteria`、`expected_tests` 字段（初始为 null 或空列表）

#### Scenario: Finish captures repo_after、diff 和 task_trace
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL 保存 `tasks/<task-id>/repo_after.tar.gz`
- **AND** 系统 SHALL 生成 `tasks/<task-id>/diff.patch`
- **AND** 系统 SHALL 尝试提取 Agent 行为轨迹并写入 `tasks/<task-id>/task_trace.json`
- **AND** 系统 SHALL 更新 `task.json` 中的 finished_at、status、paths 和 evidence_availability
- **AND** `evidence_availability.task_trace` SHALL 反映提取是否成功

#### Scenario: Non-git workspace is rejected
- **WHEN** 用户在非 git workspace 中通过 controller 执行 `start`
- **THEN** 系统 SHALL 返回明确错误
- **AND** 系统 SHALL NOT 创建 finalized task

## ADDED Requirements

### Requirement: task.json 记录任务语义字段
`task.json` SHALL 在创建时写入任务语义字段，供诊断引擎理解任务意图。

#### Scenario: instruction 字段从 control event 提取
- **WHEN** `start` 命令包含非空 title
- **THEN** `task.json.instruction` SHALL 记录该 title 作为任务描述
- **AND** `task.json.expected_tests` SHALL 初始化为空列表
- **AND** `task.json.success_criteria` SHALL 初始化为 null

#### Scenario: instruction 字段在 finish 时可从 trace 补充
- **WHEN** `task_trace.json` 提取成功且 session 首条 user_message 不为空
- **THEN** 系统 SHALL 用 session 首条 user_message 更新 `task.json.instruction`（若比 title 更详细）
- **AND** 系统 SHALL 用 `task_trace.test_commands` 更新 `task.json.expected_tests`
