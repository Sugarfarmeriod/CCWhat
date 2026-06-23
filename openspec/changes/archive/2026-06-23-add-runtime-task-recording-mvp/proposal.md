## Why

当前 Task Dataset 主要来自事后 session log 和已切分 task，无法稳定提供自动归因诊断所需的 Task 现场证据。为了让诊断结果可信，需要先跑通 C 场景的最小闭环：用户通过 `ccwhat -- claude` 使用 Claude Code 时，能在原生 slash 菜单中触发 CCWhat Task 边界记录，并在本地生成 runtime Dataset staging。

## What Changes

- 新增 runtime recording run：每次 `ccwhat -- claude` 创建独立 `run_id`，记录 agent、workspace、进程、端口和 active task 状态。
- 将 `ccwhat -- <agent>` 的默认 proxy/viewer 端口从固定端口改为自动分配，显式 `--port` / `--web-port` 仍保留。
- 新增本地 runtime controller，支持 Task `start`、`finish`、`status`、`abort`。
- 新增 runtime task staging：`/ccwhat:start` 保存 `repo_before.tar.gz`，`/ccwhat:finish` 保存 `repo_after.tar.gz`、生成 `diff.patch`，并写入 `task.json` 与 `control_events.jsonl`。
- 为 Claude Code 安装或检查 CCWhat 原生 slash command integration，使用户能在 Claude Code slash 菜单中找到 CCWhat 命令。
- Claude Code slash command 触发后应调用 CCWhat 本地 controller，并阻止命令发送给云端模型；证据中标记 `model_visible=false`、`confidence=high`。
- 本 change 只实现 Claude Code MVP，不做 Codex/OpenCode 正式适配、不做自动归因诊断、不升级最终 Dataset v2 schema。

## Capabilities

### New Capabilities

- `runtime-task-recording`: 定义 CCWhat runtime run、端口自动分配、本地 controller、Task staging、repo before/after snapshot 与 diff 生成的行为。
- `agent-slash-integration`: 定义 Claude Code 原生 slash 菜单中 CCWhat 命令的安装、触发、本地拦截和证据标记行为。

### Modified Capabilities

- 无。

## Impact

- CLI 启动链路：`ccwhat.cli`、`ccwhat.commands.run`。
- 新增 runtime recording 模块，用于 run registry、port allocation、controller 和 task staging。
- Claude Code integration 安装逻辑，涉及用户级或项目级 Claude command/hook 配置写入。
- Dataset staging 输出目录：`~/.ccwhat/runtime-runs/<run-id>/`。
- 测试需要覆盖多 run 端口分配、task start/finish staging、Claude integration 文件生成和控制事件证据。
