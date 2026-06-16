## Why

Codex 和 OpenCode adapter 已能读取本地会话元数据，但 Viewer 仍主要以 session id 展示会话，用户无法在 CCWhat 中直接维护可读名称。需要让 Viewer 支持显示和修改 session 名称，并把 Codex/OpenCode 的修改同步回对应 native 存储，避免 CCWhat 展示名与原工具标题分裂。

## What Changes

- Viewer 在 session 列表、当前 session 标题区和必要的状态反馈中显示 session 名称；无名称时回退到非 id 文案或现有可读摘要，默认可见 UI 不显示 raw/short session id。
- Viewer 提供修改 session 名称的入口，支持保存中、成功、失败和取消状态。
- 后端提供 session rename API，按当前 agent 路由到对应 adapter，并返回更新后的 session metadata。
- Codex rename 成功后必须同步写回 `~/.codex/state_5.sqlite` 的 `threads.title`。
- OpenCode rename 成功后必须同步写回 `~/.local/share/opencode/opencode.db` 的 `session.title`。
- rename 操作必须有清晰校验和错误处理：空名称、未知 agent、session 不存在、SQLite 不可用、schema 缺失、写入失败等情况不得静默成功。
- Claude Code 本阶段不做 native title 同步；Viewer 可以显示已有名称或 fallback，但修改 Claude native title 明确排除，并作为后续 spike。
- 补充后端 adapter/API 测试和前端展示/交互测试，覆盖成功、失败、回退和 unsupported agent。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `session-viewer`: 增加 session 名称展示、编辑入口、rename API 行为和前端状态反馈要求。
- `multi-agent-log-adapters`: 增加 adapter 暴露 session title、支持 Codex/OpenCode native title 写回、以及 Claude Code native 同步排除要求。

## Impact

- 预计影响 `viewer/server.py` 的项目/session API 返回字段和新增 rename handler。
- 预计影响 Viewer 前端 session 选择器、session 标题区和编辑交互。
- 预计影响 Codex/OpenCode adapter 的 session metadata 读取、title 更新和 SQLite 错误处理。
- 预计影响 adapter registry 或 adapter interface，用于声明 rename 能力和 unsupported 状态。
- 不新增第三方依赖；SQLite 写回优先使用 Python 标准库 `sqlite3`。
- 不实现 Claude Code native title 写回，不修改 `~/.claude/projects` 下的会话日志。
