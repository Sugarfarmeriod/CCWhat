# Codex Runtime Recording MVP 验收说明

## 目标

通过 `ccwhat -- codex` 启动 Codex 后，优先手动输入与 Claude Code 对齐的 CCWhat slash 命令触发 Task 切分；如果当前 Codex CLI 在 TUI 层拒绝未知 slash 命令，则使用完整文本兜底命令触发 start/finish，并生成 runtime Dataset staging。

## 手工验收步骤

1. 在一个 git workspace 中启动：

   ```bash
   ccwhat -- codex
   ```

   如果本次启动前已经打开过 Codex，会话可能没有重新加载本地 source command。退出当前 Codex TUI 后重新执行一次 `ccwhat -- codex`。

2. 如果 Codex 提示项目 hooks 未信任，按 Codex TUI 提示信任当前项目 hook，或在 Codex 内执行 `/hooks` 查看并信任。

3. 在 Codex 中打开 slash 菜单，确认是否能看到 CCWhat 命令。Codex MVP 会尝试使用和 OpenSpec `/opsx:*` 相同的 source-command skill 注册方式，常见显示应为：

   ```text
   /ccwhat:start
   /ccwhat:finish
   ```

   这两个命令都不带参数。后端会按 Task 顺序自动生成 `Task1`、`Task2`。

4. 先直接手动输入 slash 命令测试 Codex 是否会把未知 slash 交给 `UserPromptSubmit` hook：

   ```text
   /ccwhat:start
   ```

   如果看到 `CCWhat start recorded locally`，说明该 prompt 被 `UserPromptSubmit` hook 拦截并 block，不应发送给模型。

5. 如果 Codex TUI 直接提示未知 slash 命令，改用完整文本兜底命令：

   ```text
   ccwhat start
   ```

6. 在 workspace 中做一次可观察的文件修改。

7. 使用 slash finish 命令：

   ```text
   /ccwhat:finish
   ```

   如果 slash 命令被 Codex TUI 拒绝，则使用完整文本兜底命令：

   ```text
   ccwhat finish
   ```

8. 检查本地 staging：

   ```bash
   ls ~/.ccwhat/runtime-runs/codex
   find ~/.ccwhat/runtime-runs/codex -path '*/tasks/task-001/*' -maxdepth 6
   ```

   最新 run 的 `tasks/task-001/` 目录下应存在：

   ```text
   task.json
   control_events.jsonl
   repo_before.tar.gz
   repo_after.tar.gz
   diff.patch
   ```

9. 检查 Codex 控制命令证据：

   ```bash
   tail -n 2 ~/.ccwhat/runtime-runs/codex/<run-id>/tasks/task-001/control_events.jsonl
   ```

   事件中应包含：

   ```json
   {
     "agent": "codex",
     "integration": "codex_user_prompt_submit",
     "model_visible": false,
     "confidence": "high"
   }
   ```

## 当前范围

本验收只覆盖 Codex runtime MVP。OpenCode、正式 Dataset v2 schema 和自动归因诊断不在本 change 范围内。
