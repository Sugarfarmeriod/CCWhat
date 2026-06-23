# OpenCode Runtime Recording MVP 验收说明

## 目标

通过 `ccwhat -- opencode` 启动 OpenCode 后，OpenCode 项目级命令中出现 CCWhat Task start/finish，并能通过命令生成 runtime Dataset staging。

## 手工验收步骤

1. 在一个 git workspace 中启动：

   ```bash
   ccwhat -- opencode
   ```

   OpenCode 配置、命令和插件在启动时加载；如果本次启动前已经打开过 OpenCode，需要退出当前 OpenCode TUI 后重新执行一次。

2. 打开 OpenCode slash 命令菜单，确认能看到：

   ```text
   /ccwhat:start
   /ccwhat:finish
   ```

   安装器会清理 CCWhat 早期生成的 `/ccwhat-start` 和 `/ccwhat-finish` managed 文件，避免菜单里同时出现两套命令。

3. 执行 start 命令：

   ```text
   /ccwhat:start
   ```

   该命令不带参数。后端会按顺序自动生成 `Task1`、`Task2`。当前 OpenCode command 会进入模型请求；命令内容带有安全提示，要求模型只回复“收到”，不要探索项目文件。

4. 在 workspace 中做一次可观察的文件修改。

5. 执行 finish 命令：

   ```text
   /ccwhat:finish
   ```

6. 检查本地 staging：

   ```bash
   ls ~/.ccwhat/runtime-runs/opencode
   find ~/.ccwhat/runtime-runs/opencode -path '*/tasks/task-001/*' -maxdepth 6
   ```

   最新 run 的 `tasks/task-001/` 目录下应存在：

   ```text
   task.json
   control_events.jsonl
   repo_before.tar.gz
   repo_after.tar.gz
   diff.patch
   ```

7. 检查 OpenCode 控制命令证据：

   ```bash
   tail -n 2 ~/.ccwhat/runtime-runs/opencode/<run-id>/tasks/task-001/control_events.jsonl
   ```

   事件中应包含：

   ```json
   {
     "agent": "opencode",
     "integration": "opencode_command_execute_before",
     "model_visible": true,
     "agent_log_visible": true,
     "confidence": "medium"
   }
   ```

## 当前范围

本验收只覆盖 OpenCode runtime MVP。实测 OpenCode 的 `command.execute.before` 可以触发本地 controller 记录 task 边界，但不能可靠阻止 command prompt 进入模型请求。因此 OpenCode evidence 标记为 `model_visible=true`、`agent_log_visible=true`、`confidence=medium`；命令 prompt 本身负责约束模型只回复“收到”。
