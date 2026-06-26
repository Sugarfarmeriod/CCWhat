## MODIFIED Requirements

### Requirement: Runtime task staging captures task metadata
系统 SHALL 在 Task start/finish 时保存 task 元数据和 git 状态，并在 finish 时提取 Agent 行为轨迹写入 `task_trace.json`。

#### Scenario: Start creates task.json
- **WHEN** controller 成功执行 `start`
- **THEN** 系统 SHALL 创建 `tasks/<task-id>/task.json`
- **AND** `task.json` SHALL 记录 `evidence_availability` 初始状态
- **AND** `task.json` SHALL 包含 `instruction`、`success_criteria`、`expected_tests` 字段（初始为 null 或空列表）

#### Scenario: Finish captures task_trace
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL 尝试提取 Agent 行为轨迹并写入 `tasks/<task-id>/task_trace.json`
- **AND** 系统 SHALL 更新 `task.json` 中的 finished_at、status、paths 和 evidence_availability
- **AND** `evidence_availability.task_trace` SHALL 反映提取是否成功

## REMOVED Requirements

### Requirement: Runtime task staging captures repo snapshots and diff
**Reason**: 仓库快照（tar.gz）对大型仓库不可行，由后续增量 diff 方案替代。
**Migration**: 使用阶段二的增量 diff 追踪功能（GIT_INDEX_FILE 方案）。

#### Scenario: Start no longer creates repo_before.tar.gz
- **WHEN** controller 成功执行 `start`
- **THEN** 系统 SHALL NOT 创建 `tasks/<task-id>/repo_before.tar.gz`
- **AND** `task.json.paths.repo_before` SHALL 为 null
- **AND** `task.json.evidence_availability.repo_before` SHALL 为 false

#### Scenario: Finish no longer creates repo_after.tar.gz or diff.patch
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL NOT 创建 `tasks/<task-id>/repo_after.tar.gz`
- **AND** 系统 SHALL NOT 创建 `tasks/<task-id>/diff.patch`
- **AND** `task.json.paths.repo_after` SHALL 为 null
- **AND** `task.json.paths.diff` SHALL 为 null
- **AND** `task.json.evidence_availability.repo_after` SHALL 为 false
- **AND** `task.json.evidence_availability.diff` SHALL 为 false

### Requirement: Runtime control evidence is recorded
**Reason**: `control_events.jsonl` 对用户透明，诊断引擎不依赖该文件。
**Migration**: Task 边界信息已从 `task.json` 获取，无需额外文件。

#### Scenario: Start no longer creates control_events.jsonl
- **WHEN** controller 成功执行 `start`
- **THEN** 系统 SHALL NOT 创建 `tasks/<task-id>/control_events.jsonl`
- **AND** `task.json.paths.control_events` SHALL 为 null
- **AND** `task.json.evidence_availability.control_events` SHALL 为 false

#### Scenario: Finish no longer appends control events
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL NOT 向任何文件追加 control event

### Requirement: Runtime controller supports note command
**Reason**: `note` 命令未实际使用，增加维护负担。
**Migration**: 如需记录中间状态，直接使用 `/ccwhat:finish` 结束当前 task。

#### Scenario: Note command is rejected
- **WHEN** controller 收到 `note` 命令
- **THEN** 系统 SHALL 返回错误，提示该命令已移除

## ADDED Requirements

### Requirement: Runtime controller rejects unknown commands
系统 SHALL 对未识别的命令返回明确错误。

#### Scenario: Reject invalid command
- **WHEN** controller 收到未识别的命令（如 `note` 或其他无效命令）
- **THEN** 系统 SHALL 返回错误，说明该命令不受支持
