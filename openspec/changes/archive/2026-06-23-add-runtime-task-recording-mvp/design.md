## Context

CCWhat 现有 `ccwhat -- <agent>` 会启动目标 Coding Agent，并通过本地 proxy 记录模型请求/响应；Task Dataset v1 则主要从已有 session log 和 task segmentation 中构建 trace。这个模式适合事后分析，但不足以支撑自动归因诊断，因为缺少运行时 Task 边界、仓库前后快照和真实 diff。

本 change 是 runtime Dataset 的第一条竖切链路：先支持 `ccwhat -- claude`，让用户在 Claude Code 原生 slash 菜单中触发 CCWhat Task start/finish，并在本地生成可检查的 runtime Dataset staging。

## Goals / Non-Goals

**Goals:**

- `ccwhat -- claude` 创建独立 runtime run，并记录到 `~/.ccwhat/runtime-runs/<run-id>/run.json`。
- 默认自动分配 proxy、viewer 和 runtime control 端口，支持多个 CCWhat run 并发。
- Claude Code 原生 slash 菜单中出现 CCWhat 命令。
- `/ccwhat:start` 和 `/ccwhat:finish` 调用本地 CCWhat controller，不发送给云端模型。
- start/finish 后生成 Task staging，包括 `task.json`、`control_events.jsonl`、`repo_before.tar.gz`、`repo_after.tar.gz` 和 `diff.patch`。

**Non-Goals:**

- 不实现 Codex/OpenCode 正式适配。
- 不实现自动归因诊断。
- 不升级最终 Dataset v2 schema 和 validator。
- 不实现 Viewer 控制按钮。
- 不实现自然语言 skill 触发。
- 不支持非 git workspace 的 snapshot/diff。

## Decisions

### Decision: 每次 `ccwhat -- claude` 创建独立 runtime run

每个 run 都有自己的 `run_id`、端口、Agent 进程、active task 状态和 staging 目录。这样可以支持多终端并发，并避免不同 Agent run 的证据混在一起。

备选方案是复用全局 proxy/viewer 和全局 active task 状态。该方案实现更少，但请求、Task 边界和 Dataset staging 难以可靠归属，不适合作为自动归因诊断的证据基础。

### Decision: 默认自动分配端口

未显式传入 `--port` / `--web-port` 时，`ccwhat -- claude` SHALL 自动选择可用端口。显式端口仍保留，方便调试和兼容现有行为。

控制端口也自动分配，并只绑定 `127.0.0.1`。端口写入 `run.json`，不要求普通用户理解或选择。

### Decision: 第一版使用 localhost HTTP control port

Claude Code hook 需要跨进程调用 CCWhat runtime controller。localhost HTTP 比 Unix socket 更容易被 shell/node/python hook 脚本调用，也方便后续 Codex/OpenCode adapter 复用。

控制端口只绑定 `127.0.0.1`，并可以通过 run token 或 run id 校验降低误调用风险。后续如果需要更强隔离，可以把 controller 抽象层切换到 Unix socket。

### Decision: Claude Code 采用原生 command/skill + hook 拦截

本 change 优先实现 Claude Code，因为 Claude hooks 提供 `UserPromptExpansion`，适合在 slash command 展开前拦截。CCWhat 安装受管理的 Claude command/skill，使命令出现在原生 slash 菜单；hook 捕获 CCWhat 命令后调用本地 controller，并阻止原 prompt 继续发送。

如果 Claude Code 不支持 `/ccwhat:start` 这种冒号命名，允许降级为 `/ccwhat-start`，但菜单描述必须保持 CCWhat 命名空间。

### Decision: 第一版只支持 git workspace

repo snapshot 和 diff 是自动归因诊断的关键证据。第一版要求当前 workspace 是 git repo；非 git repo SHALL 返回明确错误，不生成伪造 diff。

snapshot 由 CCWhat 打 tar 包生成，diff 由 git 生成。CCWhat 不强制用户 commit，也不修改用户 git history。

### Decision: Runtime staging 先独立于 Dataset v1

本 change 只生成 runtime staging，不修改现有 Dataset v1 builder/validator。后续 `promote-runtime-dataset-v2` 再把 staging 固化为正式 diagnosis-ready Dataset schema。

## Risks / Trade-offs

- Claude Code hook 行为与文档存在差异 → 先做最小 integration 测试；如果无法确保不发送模型，必须在 `control_events.jsonl` 标记 `model_visible` 和 `confidence`。
- 自动端口分配存在竞态 → 分配后立即绑定服务，并将实际端口写入 `run.json`。
- 修改 Claude 用户配置可能冲突 → 所有文件使用 CCWhat managed marker；遇到非 CCWhat 同名文件不覆盖并报错。
- start/finish 期间 workspace 已 dirty → 允许记录，但在 `task.json` 中保存 git status 和 evidence metadata。
- 运行中断导致 partial task → 保留 staging 文件并标记 incomplete，不静默删除证据。

## Migration Plan

本 change 不迁移现有 Dataset v1 数据，也不破坏当前 `ccwhat web`、`ccwhat proxy`、`ccwhat export` 行为。`ccwhat -- claude` 未显式指定端口时启用自动端口；显式端口仍按用户指定执行。

如需回滚，可删除 `~/.ccwhat/runtime-runs/<run-id>/` 和 CCWhat 管理的 Claude integration 文件。卸载逻辑应只删除带 CCWhat managed marker 的文件。

## Open Questions

- Claude Code 是否允许命令名包含冒号；如果不允许，按本设计降级为 `/ccwhat-start`。
- Claude `UserPromptExpansion` block 后是否完全不写入 Claude transcript；实现阶段需要手工或自动验证。
