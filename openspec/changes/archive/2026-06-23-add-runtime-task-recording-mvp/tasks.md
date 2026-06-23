## 1. Runtime Run 基础设施

- [x] 1.1 新增 runtime recording 模块结构，定义 `RuntimeRun`、`RunRegistry` 和 runtime 目录约定。
- [x] 1.2 实现 `~/.ccwhat/runtime-runs/<run-id>/run.json` 创建、读取、更新和状态写入。
- [x] 1.3 实现多 run 并发的 registry 测试，确保不同 run 的 `active_task_id` 和目录互不影响。

## 2. 端口自动分配与 Run 启动

- [x] 2.1 实现可用端口自动分配工具，支持 proxy、viewer 和 control 端口。
- [x] 2.2 调整 `ccwhat -- claude` 启动流程：未显式传端口时自动分配端口，显式端口仍保持原行为。
- [x] 2.3 将最终端口、Agent 进程信息和 workspace 写入 `run.json`。
- [x] 2.4 增加端口分配和显式端口保留的单元测试。

## 3. Runtime Controller 与 Task 状态机

- [x] 3.1 实现 localhost HTTP runtime controller，绑定 `127.0.0.1`，支持 `start`、`finish`、`status`、`abort`。
- [x] 3.2 实现 active task 状态机：idle、recording、finalized、aborted。
- [x] 3.3 实现 controller 错误处理：重复 start、无 active task finish、非 git workspace start。
- [x] 3.4 增加 controller start/finish/status/abort 测试。

## 4. Task Staging、Snapshot 和 Diff

- [x] 4.1 实现 `tasks/<task-id>/task.json` 与 `control_events.jsonl` 写入。
- [x] 4.2 实现 start 时保存 `repo_before.tar.gz`，并记录 git commit/status。
- [x] 4.3 实现 finish 时保存 `repo_after.tar.gz` 和 `diff.patch`，并更新 `task.json` evidence 字段。
- [x] 4.4 使用临时 git repo 增加 staging 集成测试，验证 before/after/diff 输出。

## 5. Claude Code Slash Integration

- [x] 5.1 实现 Claude Code CCWhat command/skill 文件生成，包含 managed marker 和版本信息。
- [x] 5.2 实现 Claude Code hook 安装或更新，使用 `UserPromptExpansion` 捕获 CCWhat command 并调用 runtime controller。
- [x] 5.3 实现 integration 冲突检测：遇到非 CCWhat 管理的同名文件不得覆盖。
- [x] 5.4 增加 Claude integration 文件生成、升级和冲突检测测试。

## 6. `ccwhat -- claude` 竖切验收

- [x] 6.1 将 run registry、端口分配、controller、task staging 和 Claude integration 接入 `ccwhat -- claude`。
- [x] 6.2 增加 CLI 层测试，验证 `ccwhat -- claude` 会创建 run、注入 runtime env 并使用自动端口。
- [x] 6.3 增加手工验收脚本或说明：启动 Claude Code 后能在原生 slash 菜单看到 CCWhat start/finish 命令。
- [x] 6.4 完成一次端到端验收：通过 Claude Code slash command 执行 start/finish 后，确认 `~/.ccwhat/runtime-runs/<run-id>/tasks/task-001/` 下存在 `task.json`、`control_events.jsonl`、`repo_before.tar.gz`、`repo_after.tar.gz` 和 `diff.patch`。
