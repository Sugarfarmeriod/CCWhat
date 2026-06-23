# runtime-task-recording Specification

## Purpose
TBD - created by archiving change add-runtime-task-recording-mvp. Update Purpose after archive.
## Requirements
### Requirement: Runtime run registry
系统 SHALL 在每次 `ccwhat -- claude` 启动时创建独立 runtime run，并将 run metadata 写入 `~/.ccwhat/runtime-runs/<run-id>/run.json`。

#### Scenario: 创建独立 run
- **WHEN** 用户执行 `ccwhat -- claude`
- **THEN** 系统 SHALL 创建唯一 `run_id`
- **AND** 系统 SHALL 写入 `run.json`
- **AND** `run.json` SHALL 记录 agent、workspace、started_at、status、agent_process、proxy、viewer、control 和 active_task_id

#### Scenario: 多个 run 并发
- **WHEN** 用户在两个终端分别执行 `ccwhat -- claude`
- **THEN** 系统 SHALL 为两个进程创建不同 `run_id`
- **AND** 两个 run SHALL 写入不同 runtime run 目录
- **AND** 两个 run SHALL 不共享 active_task_id

### Requirement: Runtime ports are allocated per run
系统 SHALL 在未显式指定端口时为每个 runtime run 自动分配可用 proxy、viewer 和 control 端口。

#### Scenario: 自动分配端口
- **WHEN** 用户执行 `ccwhat -- claude` 且未传入 `--port` 或 `--web-port`
- **THEN** 系统 SHALL 自动选择可用 proxy 端口
- **AND** 系统 SHALL 自动选择可用 viewer 端口
- **AND** 系统 SHALL 自动选择可用 control 端口
- **AND** 最终端口 SHALL 写入 `run.json`

#### Scenario: 保留显式端口
- **WHEN** 用户执行 `ccwhat --port 7790 --web-port 7791 -- claude`
- **THEN** 系统 SHALL 使用用户指定的 proxy 和 viewer 端口
- **AND** 系统 SHALL 在端口不可用时报错

### Requirement: Runtime controller supports task commands
系统 SHALL 为每个 runtime run 启动本地 controller，支持 Task start、finish、status 和 abort。

#### Scenario: Start task through controller
- **WHEN** controller 收到 `start` 命令和 task title
- **THEN** 系统 SHALL 创建新的 task_id
- **AND** 系统 SHALL 将 `run.json.active_task_id` 更新为该 task_id
- **AND** 系统 SHALL 在该 run 的 `tasks/<task-id>/` 下创建 task staging

#### Scenario: Finish task through controller
- **WHEN** controller 收到 `finish` 命令且存在 active task
- **THEN** 系统 SHALL finalize active task
- **AND** 系统 SHALL 将 `run.json.active_task_id` 置为 null

#### Scenario: Reject finish without active task
- **WHEN** controller 收到 `finish` 命令但不存在 active task
- **THEN** 系统 SHALL 返回明确错误
- **AND** 系统 SHALL NOT 创建新的 task staging

### Requirement: Runtime task staging captures repo snapshots and diff
系统 SHALL 在 Task start/finish 时保存 git workspace 的 before/after 快照和真实 diff。

#### Scenario: Start captures repo_before
- **WHEN** controller 成功执行 `start`
- **THEN** 系统 SHALL 创建 `tasks/<task-id>/task.json`
- **AND** 系统 SHALL 创建 `tasks/<task-id>/control_events.jsonl`
- **AND** 系统 SHALL 保存 `tasks/<task-id>/repo_before.tar.gz`
- **AND** `task.json` SHALL 记录 evidence_availability.repo_before 为 true

#### Scenario: Finish captures repo_after and diff
- **WHEN** controller 成功执行 `finish`
- **THEN** 系统 SHALL 保存 `tasks/<task-id>/repo_after.tar.gz`
- **AND** 系统 SHALL 生成 `tasks/<task-id>/diff.patch`
- **AND** 系统 SHALL 更新 `task.json` 中的 finished_at、status、paths 和 evidence_availability

#### Scenario: Non-git workspace is rejected
- **WHEN** 用户在非 git workspace 中通过 controller 执行 `start`
- **THEN** 系统 SHALL 返回明确错误
- **AND** 系统 SHALL NOT 创建 finalized task

### Requirement: Runtime control evidence is recorded
系统 SHALL 为每次 CCWhat Task 控制命令写入 control event，并记录该命令是否对模型可见。

#### Scenario: Local command records high confidence evidence
- **WHEN** Claude Code slash command 被本地拦截并成功调用 controller
- **THEN** 系统 SHALL 在 `control_events.jsonl` 写入 command、raw_args、agent、integration、model_visible、agent_log_visible 和 confidence
- **AND** model_visible SHALL 为 false
- **AND** confidence SHALL 为 high

