## Why

CCWhat 当前的 Web Viewer 后端直接绑定 Claude Code 的本地日志目录和 JSONL 结构，导致 `ccwhat -- codex`、`ccwhat -- opencode` 等启动模式下，历史会话展示仍然只能读取 `~/.claude/projects`。为了把 CCWhat 从“Claude Code 专用日志查看器”升级为“多 Coding Agent 会话查看器”，需要先抽出统一的日志适配层，并保证现有 Claude Code 展示能力不回退。

## What Changes

- 新增多 Agent Log Adapter 架构，提供统一的后端接口用于列出项目、列出会话、读取会话和保留原始事件。
- 实现 `ClaudeAdapter`，把现有 `viewer/server.py` 中读取 `~/.claude/projects`、扫描 UUID JSONL、读取 main entries 和 subagents 的逻辑迁移到 adapter 中。
- 新增 agent registry，用于根据 `claude`、`claude-code`、`codex`、`opencode` 等名称选择对应 adapter。
- 为 Codex 和 OpenCode 建立 v0.1 预留入口，但不假设它们的日志格式与 Claude 相同；未实现时返回清晰错误或在 run 模式中明确 fallback。
- 修改 `ccwhat web`，新增 `--agent` 参数，同时保留 `--projects-dir`，且显式 `--projects-dir` 优先于 agent 默认路径。
- 修改 `ccwhat -- <target>` 启动模式，根据 target 推断 agent 类型，并把 agent 类型传给 viewer 后端。
- 改造 `viewer/server.py`，让项目和 session API 通过 adapter 获取数据，同时继续返回前端兼容结构并增加 `agent` 字段。
- 前端只做必要小改动：显示当前 agent 类型，并在 adapter 不支持时展示明确错误。
- 补充 adapter、registry、web 命令和 run 模式相关测试，保证既有 export/import 测试不被破坏。

## Capabilities

### New Capabilities
- `multi-agent-log-adapters`: 定义多 Coding Agent 会话日志适配能力，包括 agent 选择、默认日志目录、Claude Code 兼容读取、未实现 agent 的清晰错误和前端兼容 API 返回。

### Modified Capabilities

无。

## Impact

- 影响后端数据加载路径：`viewer/server.py`、`ccwhat/commands/web_server.py`、`ccwhat/commands/run.py`。
- 新增 `ccwhat/adapters/` 模块，作为未来 CodexAdapter 和 OpenCodeAdapter 的扩展点。
- Web API `/api/projects`、`/api/session/<id>` 等返回会新增 `agent` 字段，但保留当前前端依赖的 `projectDir`、`sessions`、`main`、`subagents` 字段。
- `ccwhat web --projects-dir <path>` 继续可用；`ccwhat web --agent claude` 成为默认推荐入口之一。
- Codex/OpenCode 在本变更中只建立可扩展入口，不承诺完整解析其会话格式。
