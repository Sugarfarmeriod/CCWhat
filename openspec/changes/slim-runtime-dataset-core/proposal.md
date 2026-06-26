## Why

当前 Runtime Dataset 存在数据结构冗余问题：`control_events.jsonl` 对用户透明且诊断价值有限，`repo_before.tar.gz` / `repo_after.tar.gz` 在真实场景下无法对大型仓库使用。同时，单次 `diff.patch` 无法追踪"哪一步引入了什么变更"，而增量 diff 需要不污染主 git 工作区的方案。本 change 先清理废弃文件，为后续增量 diff 追踪奠定精简的数据基础。

## What Changes

- **删除 `control_events.jsonl`**：移除该文件及其相关生成逻辑
- **删除 `repo_before.tar.gz` 和 `repo_after.tar.gz`**：移除仓库快照打包逻辑
- **简化 `ControlEvidence` 机制**：删除该 dataclass 及相关参数传递
- **删除 `note` 命令**：从 slash commands 和 controller 中移除
- **清理 hook payload**：移除 `integration`、`model_visible`、`agent_log_visible`、`confidence` 字段
- **更新测试**：调整现有测试以适配新的数据结构
- **BREAKING**: Task 目录结构变化，不再包含上述三个文件

## Capabilities

### New Capabilities
- *(无新能力，本 change 为清理和简化)*

### Modified Capabilities
- `runtime-task-staging`: 移除 `control_events` 和仓库快照相关功能，简化 task 数据结构
- `runtime-controller`: 移除 `note` action 和 `ControlEvidence` 处理
- `claude-slash-integration`: 移除 `note` 命令，简化 hook payload

## Impact

- **ccwhat/runtime/staging.py**: 删除 `ControlEvidence`、`_append_control_event`、`note` 方法，移除 tar.gz 打包逻辑
- **ccwhat/runtime/controller.py**: 删除 `ControlEvidence` import 和 `note` 处理分支
- **ccwhat/runtime/claude_integration.py**: 删除 `note` 命令
- **ccwhat/runtime/claude_hook.py**: 简化 payload 字段
- **tests/**: 更新测试用例，移除对废弃文件的断言
- **Task 目录结构**: `control_events.jsonl`、`repo_before.tar.gz`、`repo_after.tar.gz` 不再生成
