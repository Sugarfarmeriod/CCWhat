# Claude Runtime Recording MVP 验收说明

## 目标

通过 `ccwhat -- claude` 启动 Claude Code 后，Claude Code 原生 slash 菜单中可以看到 CCWhat Task 命令，并能通过 start/finish 生成 runtime Dataset staging。

## 手工验收步骤

1. 在一个 git workspace 中启动：

   ```bash
   ccwhat -- claude
   ```

2. 在 Claude Code 中打开 slash 菜单，确认至少能看到：

   ```text
   /ccwhat:start
   /ccwhat:finish
   ```

   如果 Claude Code 对命名空间显示做了降级，等价命令应显示为 CCWhat Task start/finish。

3. 选择 `/ccwhat:start`，输入本次任务标题。

4. 在 workspace 中做一次可观察的文件修改。

5. 选择 `/ccwhat:finish`。

6. 检查本地 staging：

   ```bash
   ls ~/.ccwhat/runtime-runs
   find ~/.ccwhat/runtime-runs -path '*/tasks/task-001/*' -maxdepth 6
   ```

   最新 run 的 `tasks/task-001/` 目录下应存在：

   ```text
   task.json
   control_events.jsonl
   repo_before.tar.gz
   repo_after.tar.gz
   diff.patch
   ```

7. 检查控制命令证据：

   ```bash
   tail -n 2 ~/.ccwhat/runtime-runs/<run-id>/tasks/task-001/control_events.jsonl
   ```

   `model_visible` 应为 `false`，`confidence` 应为 `high`。

## 当前范围

本验收只覆盖 Claude Code MVP。Codex/OpenCode、自然语言 Skill 触发、正式 Dataset v2 schema 和自动归因诊断不在本 change 范围内。
