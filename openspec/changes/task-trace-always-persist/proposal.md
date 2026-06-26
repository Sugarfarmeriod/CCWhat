## Why

当前 `trace_extractor.py` 在多种情况下返回 `None`（agent 不支持、时间窗口解析失败、日志不存在、时间窗内无事件），导致 `staging.py` 必须处理复杂的分支逻辑，且部分 task 目录缺少 `task_trace.json`，给下游消费带来不确定性。为了简化代码逻辑并确保 Dataset 结构的一致性，需要让 `task_trace.json` 始终写入，通过 `extraction_status` 字段显式表达提取结果。

## What Changes

- **trace_extractor.py**: 返回类型从 `dict | None` 改为 `dict`，新增 `extraction_status` 字段标识提取状态（`ok`, `unsupported_agent`, `invalid_time_bounds`, `log_not_found`, `no_events`）
- **staging.py**: 删除 `if trace is not None` 分支，始终写入 `task_trace.json`，始终设置 `evidence_availability.task_trace = True`
- **task_trace.json 结构**: 异常情况下返回包含 `extraction_status` 和 `extraction_status_reason` 的完整结构，替代 `None`

## Capabilities

### New Capabilities
- `task-trace-extraction`: 定义 task_trace.json 的提取逻辑和状态码规范

### Modified Capabilities
- `runtime-staging`: 修改 finish_task 流程，task_trace.json 从"条件写入"改为"始终写入"

## Impact

- `ccwhat/runtime/trace_extractor.py`: 修改返回类型和错误处理逻辑
- `ccwhat/runtime/staging.py`: 简化 finish_task 中的 trace 处理分支
- `tests/test_runtime_recording.py`: 更新测试断言，移除 `trace is None` 相关测试
- `tests/test_task_dataset_change_evidence.py`: 更新测试以验证新的 extraction_status 行为
