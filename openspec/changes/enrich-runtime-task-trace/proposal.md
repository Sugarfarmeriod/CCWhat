## Why

Runtime Staging（V2）已具备真实 git 快照和可靠任务边界，但缺少 Agent 行为轨迹——commands、errors、final_claim、changes 等字段完全没有记录。没有这些字段，V2 无法支撑任何有意义的归因诊断，因为我们只知道代码改了什么，却不知道 Agent 是怎么改的、跑了什么测试、报了什么错。proxy 在 `ccwhat -- claude` 运行期间已经在捕获这些数据，只是没有按任务边界切进 task 目录。

## What Changes

- 新增 `task_trace.json`，随 `/ccwhat:finish` 写入 `tasks/task-001/` 目录
  - 从 proxy session 日志中按任务时间边界切出对应片段
  - 提取并写入：events、commands、test_commands、files.read、files.changed、changes、patches、errors、final_claim
- 扩展 `task.json`，补充任务语义字段：
  - `instruction`：用户完整任务描述（从 session 首条 user_message 提取）
  - `success_criteria`：预期完成标准（如可提取）
  - `expected_tests`：预期测试命令列表
- `evidence_availability` 新增 `task_trace` 字段，标记提取是否成功
- `task_trace.json` 的 `repo_state` 与 task.json 的 git 字段对齐

## Capabilities

### New Capabilities

- `runtime-task-trace-enrichment`：在 `/ccwhat:finish` 时，从 proxy session 日志按任务时间边界提取 Agent 行为轨迹，写成 `task_trace.json` 放入 task 目录。

### Modified Capabilities

- `runtime-task-recording`：task 目录结构新增 `task_trace.json`；task.json 新增 `instruction`、`success_criteria`、`expected_tests` 字段；`evidence_availability` 新增 `task_trace` 标志位。

## Impact

- `ccwhat/runtime/staging.py`：`finish_task()` 新增 trace 提取和写入逻辑
- `ccwhat/runtime/` 新增 `trace_extractor.py`：从 session 日志按时间窗口提取 trace 字段
- `ccwhat/task_segments/` 及 `ccwhat/task_dataset/`：复用已有的 `extract_evidence`、`extract_change_evidence` 逻辑，不重复实现
- `tests/test_runtime_recording.py`：新增 task_trace 写入和字段校验测试
- 不影响 Dataset v1 的导出路径和格式
