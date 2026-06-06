## Why

多 Agent Log Adapter v0.1 已经把 CCWhat 从 Claude-only viewer 抽象为 adapter 架构，但 Codex 和 OpenCode 仍然只是预留入口。现在需要让 CCWhat 真实读取 Codex 和 OpenCode 的本地会话记录，使 `ccwhat -- codex` 和 `ccwhat -- opencode` 能进入对应 agent 的历史会话视图，而不是 fallback 到 Claude。

## What Changes

- 新增 `CodexAdapter`，读取 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，并可使用 `~/.codex/state_5.sqlite` 作为 thread metadata 索引。
- 新增 `OpenCodeAdapter`，读取 `~/.local/share/opencode/opencode.db`，通过 `session`、`message`、`part` 等表还原会话、事件、turn 和 usage。
- 更新 registry，使 `codex` 和 `opencode` 从未实现状态变为已支持 adapter。
- 更新 `ccwhat web --agent codex` 和 `ccwhat web --agent opencode`，使用各自默认数据源启动 viewer。
- 更新 `ccwhat -- codex` 和 `ccwhat -- opencode`，不再因 adapter 未实现 fallback 到 Claude。
- 为 Codex/OpenCode 输出 normalized `events`、`turns` 和 `usage`，但不伪装成 Claude 的 `main/subagents` 原始结构。
- 前端只做必要适配：当非 Claude session 没有 `main/subagents` 时，使用 `events/turns` 做基础展示。
- 保持 `req-resp.html` 独立；网络抓包仍只作为可关联时的补充来源。

## Capabilities

### New Capabilities

无。

### Modified Capabilities
- `multi-agent-log-adapters`: 将 Codex 和 OpenCode 从预留 agent 升级为真实 adapter，并要求 viewer 能展示其 normalized events/turns/usage。

## Impact

- 影响 `ccwhat/adapters/registry.py`、新增 `ccwhat/adapters/codex.py` 和 `ccwhat/adapters/opencode.py`。
- 影响 `viewer/server.py` 和 `viewer/claude-log.html` 的非 Claude 数据展示路径。
- 影响 CLI 行为：`ccwhat web --agent codex/opencode` 和 `ccwhat -- codex/opencode` 应使用对应 adapter。
- 需要新增 SQLite 读取逻辑，但不新增第三方依赖，优先使用 Python 标准库 `sqlite3`。
- 需要新增测试 fixture 覆盖 Codex JSONL 和 OpenCode SQLite。
