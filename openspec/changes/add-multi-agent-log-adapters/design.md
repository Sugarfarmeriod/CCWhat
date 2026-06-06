## Context

CCWhat 当前的 Web Viewer 后端把 Claude Code 的日志目录和字段结构直接写在 `viewer/server.py` 中：项目来自 `~/.claude/projects`，session 文件按 UUID 命名，subagents 位于 `<project>/<sessionId>/subagents/`。同时 `ccwhat web` 和 `ccwhat -- <target>` 启动 viewer 时也默认指向 Claude Code 项目目录。

这让 CCWhat 在代理记录层面可以启动 Codex 或 OpenCode，但历史会话查看层仍然是 Claude Code 专用。当前目标不是一次性解析所有 agent 的日志格式，而是先建立可扩展后端架构，并保证 Claude Code 现有展示、导出、分析入口不回退。

## Goals / Non-Goals

**Goals:**

- 建立 `ccwhat.adapters` 模块，统一封装不同 Coding Agent 的日志读取行为。
- 将 Claude Code 的项目扫描、session 读取、subagent 读取逻辑迁移到 `ClaudeAdapter`。
- 通过 registry 根据 agent 名称选择 adapter，并支持常见别名。
- 让 `viewer/server.py` 通过 adapter 获取项目和 session 数据，同时保留前端兼容返回结构。
- 为 `ccwhat web --agent claude`、显式 `--projects-dir`、`ccwhat -- claude`、`ccwhat -- codex`、`ccwhat -- opencode` 建立清晰行为。
- Codex/OpenCode 未实现时必须有清晰错误或 fallback 提示，不能让用户误以为已完整支持。
- 为本地 Agent Log 定义轻量 normalized event/turn 和 usage 字段，使 Claude、Codex、OpenCode 后续可以映射到同一展示模型。
- 明确本地日志是 Agent Log 页面的主数据源，网络抓包记录只作为可关联时的补充数据源。
- 补充测试覆盖 adapter、registry、CLI 参数优先级和现有导出导入兼容性。

**Non-Goals:**

- 本变更不实现 Codex 和 OpenCode 的真实日志格式解析。
- 本变更不重写 `viewer/claude-log.html`，也不重命名页面文件。
- 本变更不改变现有 export/import 包格式中的 `claude-logs` 命名。
- 本变更不把 `claude-log.html` 和 `req-resp.html` 合并为一个页面。
- 本变更不要求所有 usage 字段都必须从本地日志拿到；缺失字段必须保留为空或 unknown。
- 本变更不默认展示 cache 命中率，除非 CCWhat 明确定义派生公式。
- 本变更不改变 HTTP req/resp recorder 的 session id 提取策略。

## Decisions

### 1. 新增 adapter 接口，但保留旧 viewer helper 包装

新增 `ccwhat/adapters/base.py` 定义统一接口，建议包括：

- `name`
- `default_projects_dir()`
- `list_projects()`
- `list_sessions()`
- `load_session(session_id)`
- `raw_to_normalized_event(raw_entry)`

`viewer/server.py` 内部改为使用 adapter，但继续保留 `get_projects(projects_dir)` 和 `get_session(session_id, projects_dir)` 这类旧函数作为 ClaudeAdapter 的薄包装。这样可以减少对 `ccwhat.exporter` 和现有测试的冲击。

备选方案是一次性把所有调用方都改为 adapter 对象。这个方案更纯粹，但会扩大改动面，并使 export/import 测试需要同步重写。v0.1 选择兼容优先。

### 2. ClaudeAdapter 完整迁移现有读取逻辑

`ClaudeAdapter` 负责：

- 默认目录为 `~/.claude/projects`。
- 扫描项目子目录。
- 只识别 UUID 命名的 `.jsonl` session 文件。
- 读取 main entries，并在每条成功解析的 JSON 上保留 `_fileLine`。
- 跳过无法解析的 JSONL 行，不中断整个 session 读取。
- 读取 `<project>/<sessionId>/subagents/agent-*.jsonl` 和对应 `.meta.json`。
- 返回前端兼容结构，并增加 `agent: "claude"`。

这等价于把当前 `viewer/server.py` 的 Claude-only 逻辑移动到更合适的层中。

### 3. registry 明确区分“已支持”和“预留”

`registry.py` 负责 agent 名称规范化和 adapter 创建：

- `claude`、`claude-code` 映射到 `ClaudeAdapter`。
- `codex` 映射到未实现状态。
- `opencode`、`open-code`、`open_code` 映射到未实现状态。

对于 `ccwhat web --agent codex` 或 `--agent opencode`，应给出清晰错误，说明该 adapter 尚未实现，并提示可以使用 `--projects-dir` 加 `--agent claude` 查看 Claude Code 日志。

对于 `ccwhat -- codex` 或 `ccwhat -- opencode`，代理和目标命令仍应可以启动。viewer 启动时可以 fallback 到 ClaudeAdapter，但必须在终端输出 warning，说明当前 viewer 仍展示 Claude Code 历史会话，目标 agent 的日志 adapter 尚未实现。

### 4. `--projects-dir` 优先于 agent 默认路径

`ccwhat web` 的参数解析优先级：

1. 用户显式传入 `--projects-dir` 时，adapter 使用该路径。
2. 用户未传 `--projects-dir` 时，根据 `--agent` 使用 adapter 默认路径。
3. `--agent` 未知或未实现时，返回清晰错误。

为判断“显式传入”，`--projects-dir` 默认值应从 Claude 路径改为 `None`，在命令函数内部解析默认值。

### 5. 前端只消费最小新增字段

`/api/projects` 和 `/api/session/<id>` 返回新增 `agent` 字段。前端只新增当前 agent 的展示和 unsupported/error 状态展示，不改变 session 列表、搜索、导出、分析等核心流程。

如果需要更通用的页面命名，应作为后续独立变更处理。

### 6. Normalized event/turn 是 Agent Log 页面的通用模型

Agent adapter 返回的数据应保留当前 Claude 兼容字段，同时新增通用字段：

- `events`：单条原子事件，如用户消息、assistant 消息、工具调用、工具结果、reasoning、metadata、error。
- `turns`：前端更适合展示的聚合单位，由同一轮用户输入及其后续 assistant 消息、工具调用和工具结果组成。
- `usage`：token/cache 用量对象，可出现在 event、turn 和 session 层级。

第一版前端可以继续优先使用 Claude 的 `main/subagents` 兼容字段；但 API 必须为后续通用 Agent Log 页面提供 `events` 和 usage 数据入口。

### 7. Usage 字段采用通用命名，来源必须标注

`usage` 不直接使用 Claude/OpenCode/Codex 的原始字段名作为主字段，而是映射到 CCWhat 的通用命名：

- `inputTokens`
- `outputTokens`
- `reasoningTokens`
- `totalTokens`
- `cacheReadTokens`
- `cacheWriteTokens`
- `cacheCreationTokens`
- `cachedInputTokens`
- `cacheHitRate`
- `cacheHitRateFormula`
- `scope`
- `source`
- `raw`

来源优先级：

1. 本地 agent 日志或数据库。
2. 可通过 session/message/turn 关联上的网络抓包记录。
3. CCWhat 明确公式下的派生值。
4. 无法获得时保留 `null` 或 `unknown`。

Cache 命中率不是原始事实字段。除非 CCWhat 明确写出公式，否则不应展示 `cacheHitRate`；应优先展示 cache read/write/creation/cached input 等 token 计数。

### 8. Req/Resp 页面保持独立

`req-resp.html` 继续作为网络请求响应查看器存在，不与 Agent Log 页面合并。Agent Log 页面可以在后续通过 message id、turn id 或 session id 与网络抓包记录建立关联，用于补充 usage 或跳转查看原始 request/response。

## Risks / Trade-offs

- [Risk] 保留旧 helper 包装会让 `viewer/server.py` 在短期内仍有少量 Claude 兼容函数名称。→ Mitigation：内部委托 ClaudeAdapter，并在后续 Codex/OpenCode 支持完成后再考虑进一步清理。
- [Risk] `ccwhat -- codex` fallback 到 Claude viewer 可能让用户误解支持范围。→ Mitigation：终端必须输出明确 warning，Web 页面显示当前 agent。
- [Risk] export/import 仍使用 `claude-logs` 命名，和多 agent 目标不完全一致。→ Mitigation：v0.1 不改变包格式，避免破坏兼容；后续新增通用 export schema。
- [Risk] Codex/OpenCode 日志格式未知，提前设计 normalized schema 容易错误。→ Mitigation：v0.1 只定义接口和 raw 降级，不承诺具体格式。
- [Risk] 不同来源的 usage 字段粒度不同，可能是 event、turn 或 session 级。→ Mitigation：`usage.scope` 必须标注粒度，缺失字段不得伪造。
- [Risk] cache 命中率公式在不同 provider/agent 间不统一。→ Mitigation：默认只展示 cache token 计数；命中率必须带公式和 derived 来源。

## Migration Plan

1. 新增 adapter 模块和 ClaudeAdapter。
2. 改造 `viewer/server.py` 使用 adapter，并保留旧 API 包装。
3. 修改 `ccwhat web` 参数，支持 `--agent` 和 `--projects-dir` 优先级。
4. 修改 `ccwhat -- <target>` agent 推断和 viewer 启动参数。
5. 小改前端显示 agent 和错误状态。
6. 补测试并跑现有测试。

如果出现回归，可以暂时回退 `viewer/server.py` 到旧 helper 逻辑，因为 adapter 层迁移不改变底层文件格式。

## Open Questions

- 后续 CodexAdapter 应读取 Codex 的哪个本地目录和哪种 session 标识，需要在实现前通过真实样本确认。
- 后续 OpenCodeAdapter 是否有稳定的本地会话存储格式，也需要通过真实样本确认。
- export/import 包格式是否应从 `claude-logs` 演进为 `agent-logs/<agent>`，建议作为后续变更单独设计。
- 后续是否在 Agent Log 页面显示网络抓包补充 usage，需要先定义稳定的关联键策略。
