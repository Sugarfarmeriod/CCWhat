## MODIFIED Requirements

### Requirement: Runtime task staging captures incremental diff
系统 SHALL 在 Task 执行期间记录增量 diff，并在 finish 时保存到 diff.patch。

#### Scenario: Start initializes CCWhatIndex
- **WHEN** controller 成功执行 `start`
- **THEN` 系统 SHALL 初始化 `CCWhatIndex`
- **AND** 备用 index SHALL 为空

#### Scenario: Record step captures diff
- **WHEN** 调用 `staging.record_step(tool_name, file_path)`
- **THEN** 系统 SHALL 将文件添加到备用 index
- **AND** 系统 SHALL 生成该步骤的 diff
- **AND** 系统 SHALL 追加 diff 到内存缓冲区

#### Scenario: Finish writes diff.patch
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL 将累积的 diff 写入 `tasks/<task-id>/diff.patch`
- **AND** `task.json.paths.diff` SHALL 为 `"diff.patch"`
- **AND** `task.json.evidence_availability.diff` SHALL 为 true

## ADDED Requirements

### Requirement: TaskStaging 提供 record_step 方法
系统 SHALL 提供 `record_step()` 方法供外部调用记录文件变更。

#### Scenario: 外部调用 record_step
- **WHEN** 调用 `staging.record_step(tool_name="Write", file_path="src/app.py")`
- **THEN** 系统 SHALL 更新备用 index
- **AND** 系统 SHALL 追加 diff 到缓冲区
- **AND** 系统 SHALL 返回 step_index
