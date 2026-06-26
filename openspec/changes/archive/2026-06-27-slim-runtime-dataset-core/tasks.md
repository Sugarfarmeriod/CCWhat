## 1. Staging 层清理

- [x] 1.1 删除 `ControlEvidence` dataclass 及其所有字段
- [x] 1.2 删除 `_append_control_event()` 方法
- [x] 1.3 删除 `note()` 方法
- [x] 1.4 修改 `start_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [x] 1.5 修改 `start_task()`：删除 `repo_before.tar.gz` 写入逻辑
- [x] 1.6 修改 `start_task()`：`task["paths"]` 移除 `"repo_before"`、`"control_events"` 键
- [x] 1.7 修改 `start_task()`：`task["evidence_availability"]` 移除 `"repo_before"`、`"control_events"` 键，设置为 false
- [x] 1.8 修改 `finish_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [x] 1.9 修改 `finish_task()`：删除 `repo_after.tar.gz` 写入逻辑
- [x] 1.10 修改 `finish_task()`：删除 `diff.patch` 生成逻辑
- [x] 1.11 修改 `finish_task()`：`task["paths"]` 移除 `"repo_after"`、`"diff"` 键（设为 null）
- [x] 1.12 修改 `finish_task()`：`task["evidence_availability"]` 移除 `"repo_after"`、`"diff"` 键，设置为 false
- [x] 1.13 修改 `abort_task()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用
- [x] 1.14 修改 `status()`：移除 `evidence` 参数，删除 `_append_control_event()` 调用

## 2. Controller 层清理

- [x] 2.1 删除 `ControlEvidence` 的 import
- [x] 2.2 删除 `"note"` 从 `VALID_ACTIONS` 列表
- [x] 2.3 删除 `note` 处理分支（或改为返回错误）
- [x] 2.4 修改 `start` 处理：调用 `staging.start_task()` 时去掉 `evidence=` 参数
- [x] 2.5 修改 `finish` 处理：调用 `staging.finish_task()` 时去掉 `evidence=` 参数
- [x] 2.6 修改 `abort` 处理：调用 `staging.abort_task()` 时去掉 `evidence=` 参数
- [x] 2.7 修改 `status` 处理：调用 `staging.status()` 时去掉 `evidence=` 参数

## 3. Claude Integration 清理

- [x] 3.1 删除 `"note"` 从 `COMMANDS` 字典

## 4. Claude Hook 清理

- [x] 4.1 简化 payload：删除 `integration` 字段
- [x] 4.2 简化 payload：删除 `model_visible` 字段
- [x] 4.3 简化 payload：删除 `agent_log_visible` 字段
- [x] 4.4 简化 payload：删除 `confidence` 字段
- [x] 4.5 更新正则表达式：从 `_SLASH_RE` 移除 `note` 命令

## 5. 测试更新

- [x] 5.1 更新 `test_runtime_recording.py`：移除对废弃文件的断言
- [x] 5.2 更新 `test_runtime_recording.py`：验证废弃文件不存在
- [x] 5.3 更新 `test_runtime_recording.py`：验证 `note` 命令返回错误
- [x] 5.4 运行全部测试：`pytest tests/test_runtime_recording.py tests/test_task_dataset_core.py tests/test_task_dataset_change_evidence.py -x -q`（50 passed）

## 6. 验证与收尾

- [x] 6.1 代码审查：确保无遗留的 `ControlEvidence` 引用
- [x] 6.2 代码审查：确保 `note` 命令已完全移除
- [x] 6.3 运行测试验证：50 个测试全部通过
