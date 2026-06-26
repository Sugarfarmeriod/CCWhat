## Why

Change 7 已建立增量 diff 基础设施（CCWhatIndex、StepDiffBuffer、TaskStaging.record_step()），但缺少触发机制。当前代码无法自动记录 Agent 的文件修改。我们需要通过 Claude Code 的 PostToolUse Hook，在每次 Write/Edit 工具调用后自动触发 diff 记录，并建立 tool_call 与 diff 的关联。

## What Changes

- **新增 `ccwhat` 脚手架脚本**: 设置 `CCWHAT_ENABLED=1` 环境变量后启动 Claude Code
- **新增 PostToolUse Hook**: 捕获 Write/Edit 工具调用，提取 tool_name 和 file_path
- **新增 `/step` controller endpoint**: 接收 hook 通知，调用 `staging.record_step()`
- **新增 Hook 条件激活机制**: 只有 `CCWHAT_ENABLED=1` 时 hook 才生效，避免影响正常 session
- **更新 diff.patch 格式**: 关联 step_index 与 tool_call

## Capabilities

### New Capabilities
- `ccwhat-cli-wrapper`: ccwhat 脚手架脚本，设置环境变量并启动 Agent
- `posttooluse-hook-integration`: PostToolUse Hook 捕获文件修改并通知 controller

### Modified Capabilities
- `runtime-controller`: 新增 `/step` endpoint 接收 hook 通知

## Impact

- **新增 `ccwhat` CLI 命令**: 替代 `claude` 启动追踪模式
- **新增 `.claude/hooks/ccwhat-diff-hook.sh`**: PostToolUse Hook 脚本
- **修改 `controller.py`**: 新增 `/step` endpoint
- **修改 `.claude/settings.json`**: 注册 PostToolUse Hook
