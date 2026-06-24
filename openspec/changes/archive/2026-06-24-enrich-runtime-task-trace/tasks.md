## 1. session 日志路径定位

- [x] 1.1 确认 proxy output 目录下 session JSONL 的文件命名规则（`<session_id>.jsonl` 或其他约定）
- [x] 1.2 在 `RunRegistry` 或 `staging.py` 中实现 `_resolve_session_log_path(run)` 方法，从 run.json 推导 session 日志路径

## 2. TraceExtractor 模块

- [x] 2.1 新建 `ccwhat/runtime/trace_extractor.py`
- [x] 2.2 实现 `extract_task_trace(session_log_path, started_at, finished_at, agent)` 函数：从 JSONL 按时间窗口（各留 1s buffer）过滤事件
- [x] 2.3 调用 `normalize_session_events` 将过滤后的原始事件转为 `NormalizedEvent` 列表
- [x] 2.4 调用 `extract_evidence(events)` 提取 commands、test_commands、files、errors、final_claim
- [x] 2.5 调用 `extract_change_evidence(events, agent=agent)` 提取 changes 和 patches
- [x] 2.6 组装并返回 `task_trace` 字典（字段与 Dataset v1 trace 对齐）
- [x] 2.7 session 日志不存在时返回 `None`，不抛异常

## 3. task_trace.json 写入

- [x] 3.1 在 `staging.py` 的 `finish_task()` 中调用 `extract_task_trace()`
- [x] 3.2 提取成功时写入 `tasks/<task-id>/task_trace.json`
- [x] 3.3 更新 `task.json` 的 `paths.task_trace` 和 `evidence_availability.task_trace`
- [x] 3.4 提取失败（返回 None）时仅将 `evidence_availability.task_trace` 置为 false，不中断流程

## 4. task.json 语义字段扩展

- [x] 4.1 在 `start_task()` 中为 `task.json` 新增 `instruction`（取自 title）、`success_criteria: null`、`expected_tests: []`
- [x] 4.2 在 `finish_task()` 中，若 `task_trace` 提取成功且含更详细的 user_message，更新 `instruction`
- [x] 4.3 在 `finish_task()` 中，用 `task_trace.test_commands` 更新 `task.json.expected_tests`

## 5. 测试

- [x] 5.1 在 `test_runtime_recording.py` 中新增 `test_task_trace_written_on_finish`：mock session 日志，验证 `task_trace.json` 被写入且包含必要字段
- [x] 5.2 新增 `test_task_trace_missing_log_degrades_gracefully`：session 日志不存在，finish 正常完成，`evidence_availability.task_trace` 为 false
- [x] 5.3 新增 `test_task_json_instruction_and_expected_tests`：验证 start 后 instruction 字段存在，finish 后 expected_tests 被更新
- [x] 5.4 新增 `test_trace_extractor_time_window`：直接测试 `extract_task_trace`，验证时间窗口过滤正确
- [x] 5.5 运行全量测试，确认无回归
