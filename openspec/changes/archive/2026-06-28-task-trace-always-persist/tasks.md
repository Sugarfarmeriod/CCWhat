## 1. trace_extractor.py 修改

- [x] 1.1 修改 `extract_task_trace()` 返回类型：移除 `| None`，改为始终返回 `dict`
- [x] 1.2 修改异常处理：不再返回 `None`，改为返回带 `extraction_status` 的完整结构
- [x] 1.3 添加 `extraction_status` 字段：支持 `ok`, `unsupported_agent`, `invalid_time_bounds`, `log_not_found`, `no_events`
- [x] 1.4 添加 `extraction_status_reason` 字段：为人类可读的错误说明
- [x] 1.5 异常情况下填充空值：`events`, `commands`, `files` 等字段使用空列表，`final_claim` 等使用 `null`

## 2. staging.py 修改

- [x] 2.1 简化 `finish_task()` 中的 trace 处理：删除 `if trace is not None` 分支
- [x] 2.2 始终写入 `task_trace.json`：移除条件判断，无条件写入
- [x] 2.3 始终设置 `evidence_availability.task_trace = True`：移除条件赋值
- [x] 2.4 清理相关导入：移除不再需要的类型检查

## 3. 测试更新

- [x] 3.1 更新 `test_runtime_recording.py`：修改测试断言，使用 `extraction_status` 替代 `trace is None` 检查
- [x] 3.2 更新 `test_task_dataset_change_evidence.py`：验证新的 extraction_status 行为
- [x] 3.3 添加新的测试场景：`unsupported_agent` 状态处理
- [x] 3.4 添加新的测试场景：`log_not_found` 状态处理
- [x] 3.5 验证异常状态的字段完整性：确保所有字段都存在

## 4. 集成与验证

- [x] 4.1 运行全部测试：确保无回归
- [x] 4.2 手动测试完整流程：`/ccwhat:start` -> `/ccwhat:finish`，验证 task_trace.json 始终生成
- [x] 4.3 检查 task.json 结构：确认 `evidence_availability.task_trace` 始终为 true
- [x] 4.4 代码审查：检查错误处理边界
