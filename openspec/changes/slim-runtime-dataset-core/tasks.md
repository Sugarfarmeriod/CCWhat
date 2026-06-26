## 1. Staging 层清理

- [ ] 1.1 删除 `ControlEvidence` dataclass 及其所有字段
- [ ] 1.2 删除 `_append_control_event()` 方法
- [ ] 1.3 删除 `note()` 方法
- [ ] 1.4 修改 `start_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [ ] 1.5 修改 `start_task()`：删除 `repo_before.tar.gz` 写入逻辑
- [ ] 1.6 修改 `start_task()`：`task["paths"]` 移除 `"repo_before"`、`"control_events"` 键
- [ ] 1.7 修改 `start_task()`：`task["evidence_availability"]` 移除 `"repo_before"`、`"control_events"` 键，设置为 false
- [ ] 1.8 修改 `finish_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [ ] 1.9 修改 `finish_task()`：删除 `repo_after.tar.gz` 写入逻辑
- [ ] 1.10 修改 `finish_task()`：删除 `diff.patch` 生成逻辑
- [ ] 1.11 修改 `finish_task()`：`task["paths"]` 移除 `"repo_after"`、`"diff"` 键（设为 null）
- [ ] 1.12 修改 `finish_task()`：`task["evidence_availability"]` 移除 `"repo_after"`、`"diff"` 键，设置为 false
- [ ] 1.13 修改 `abort_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [ ] 1.14 修改 `status()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用

## 2. Controller 层清理

- [ ] 2.1 删除 `ControlEvidence` 的 import
- [ ] 2.2 删除 `"note"` 从 `VALID_ACTIONS` 列表
- [ ] 2.3 删除 `note` 处理分支（或改为返回错误）
- [ ] 2.4 修改 `start` 处理：调用 `staging.start_task()` 时去掉 `evidence=` 参数
- [ ] 2.5 修改 `finish` 处理：调用 `staging.finish_task()` 时去掉 `evidence=` 参数
- [ ] 2.6 修改 `abort` 处理：调用 `staging.abort_task()` 时去掉 `evidence=` 参数
- [ ] 2.7 修改 `status` 处理：调用 `staging.status()` 时去掉 `evidence=` 参数

## 3. Claude Integration 清理

- [ ] 3.1 删除 `"note"` 从 `COMMANDS` 字典

## 4. Claude Hook 清理

- [ ] 4.1 简化 payload：删除 `integration` 字段
- [ ] 4.2 简化 payload：删除 `model_visible` 字段
- [ ] 4.3 简化 payload：删除 `agent_log_visible` 字段
- [ ] 4.4 简化 payload：删除 `confidence` 字段

## 5. 测试更新

- [ ] 5.1 更新 `test_task_dataset_core.py`：移除对 `control_events.jsonl` 的断言
- [ ] 5.2 更新 `test_task_dataset_core.py`：移除对 `repo_before.tar.gz` 的断言
- [ ] 5.3 更新 `test_task_dataset_core.py`：移除对 `repo_after.tar.gz` 的断言
- [ ] 5.4 更新 `test_task_dataset_core.py`：验证 `evidence_availability` 中对应键为 false
- [ ] 5.5 更新 `test_task_dataset_change_evidence.py`：同上调整断言
- [ ] 5.6 运行全部测试：`pytest tests/test_task_dataset_core.py tests/test_task_dataset_change_evidence.py -x -q`
- [ ] 5.7 修复任何失败的测试

## 6. 验证与收尾

- [ ] 6.1 手动测试：`ccwhat -- claude` 启动正常
- [ ] 6.2 手动测试：`/ccwhat:start` 创建 task 成功
- [ ] 6.3 手动测试：`/ccwhat:finish` 完成 task 成功
- [ ] 6.4 手动验证：task 目录不包含废弃文件
- [ ] 6.5 代码审查：确保无遗留的 `ControlEvidence` 引用
- [ ] 6.6 代码审查：确保 `note` 命令已完全移除
