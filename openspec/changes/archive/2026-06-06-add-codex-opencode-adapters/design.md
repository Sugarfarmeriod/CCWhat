## Context

`add-multi-agent-log-adapters` 已完成 adapter 架构和 ClaudeAdapter。当前 registry 能识别 `codex` 和 `opencode`，但它们仍是未实现状态，run 模式会 fallback 到 Claude。用户本机已经存在 Codex 会话记录和 OpenCode 会话数据库：

- Codex：`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，并有 `~/.codex/state_5.sqlite` 作为 thread metadata。
- OpenCode：`~/.local/share/opencode/opencode.db`，包含 `session`、`message`、`part`、`session_message` 等表。

本阶段目标是实现真实读取，不再只显示 warning/fallback。

## Goals / Non-Goals

**Goals:**

- 实现 `CodexAdapter`，读取 Codex rollout JSONL 并输出 projects、sessions、events、turns、usage。
- 实现 `OpenCodeAdapter`，读取 OpenCode SQLite DB 并输出 projects、sessions、events、turns、usage。
- 更新 registry，使 `codex` 和 `opencode` 成为 implemented agent。
- 让 `ccwhat web --agent codex/opencode` 能显示对应本地会话。
- 让 `ccwhat -- codex/opencode` 启动 viewer 时使用对应 adapter，不再 fallback 到 Claude。
- 前端支持非 Claude session 的基础展示路径，优先展示 normalized turns/events。
- 保持 ClaudeAdapter、导出导入和 Req/Resp 页面不回退。

**Non-Goals:**

- 不合并 Agent Log 页面和 Req/Resp 页面。
- 不实现网络抓包与 Codex/OpenCode 本地日志的完整自动关联。
- 不默认计算 cache 命中率。
- 不要求 Codex/OpenCode 输出 Claude 的 `main/subagents` 原始结构。
- 不重做 export/import 包格式；非 Claude 导出如需完整支持可后续单独设计。

## Decisions

### 1. CodexAdapter 以 rollout JSONL 为主，SQLite 为索引补充

Codex 的真实 transcript 在 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`。adapter 应扫描该目录，按文件名和 `session_meta.payload.id` 得到 session id，按 `session_meta.payload.cwd` 得到 project/workspace 信息。

`~/.codex/state_5.sqlite` 可用于补充 title、updated_at、tokens_used、model、provider 等 thread metadata。读取 SQLite 失败时不能阻塞 JSONL transcript 展示。

### 2. OpenCodeAdapter 以 SQLite DB 为主

OpenCode 的会话数据集中在 `~/.local/share/opencode/opencode.db`。adapter 应读取：

- `session`：session 元数据、project_id、directory、title、agent、model、tokens。
- `project`：project/worktree 信息。
- `message`：role、model、tokens、finish、parentID。
- `part`：text、reasoning、tool、step-start、step-finish 等具体内容。

优先使用 `message` + `part` 还原 events 和 turns；`session_message` 可作为后续兼容或补充来源。

### 3. 非 Claude 数据走 events/turns 展示

Claude 仍保留 `main/subagents` 兼容字段。Codex/OpenCode 不伪装 Claude 原始结构，而是返回：

- `agent`
- `sessionId`
- `projectDir`
- `main: []`
- `subagents: []`
- `events`
- `turns`
- `usage`

前端在发现 `main/subagents` 为空但 `turns/events` 存在时，使用通用展示路径。

### 4. Usage 映射保持通用字段

Codex 映射：

- `input_tokens` -> `inputTokens`
- `cached_input_tokens` -> `cachedInputTokens`
- `output_tokens` -> `outputTokens`
- `reasoning_output_tokens` -> `reasoningTokens`
- `total_tokens` 或 `tokens_used` -> `totalTokens`

OpenCode 映射：

- `tokens_input` 或 `tokens.input` -> `inputTokens`
- `tokens_output` 或 `tokens.output` -> `outputTokens`
- `tokens_reasoning` 或 `tokens.reasoning` -> `reasoningTokens`
- `tokens_cache_read` 或 `tokens.cache.read` -> `cacheReadTokens`
- `tokens_cache_write` 或 `tokens.cache.write` -> `cacheWriteTokens`

缺失字段保留为空，不伪造。cache 命中率不默认计算。

### 5. 默认数据源路径

默认路径：

- Codex：`~/.codex/sessions`，可选读取 `~/.codex/state_5.sqlite`。
- OpenCode：`~/.local/share/opencode/opencode.db`。

`--projects-dir` 对 Codex 表示 sessions 根目录；对 OpenCode 可以接受 DB 所在目录或具体 DB 文件路径。实现时应给出清晰错误。

## Risks / Trade-offs

- [Risk] Codex rollout event 类型多，无法一次覆盖所有 payload。→ Mitigation：先覆盖 message、tool、reasoning、metadata，其他类型保留 raw 并标记 unknown/event。
- [Risk] OpenCode DB schema 版本可能变化。→ Mitigation：先检查必要表和字段，缺失时返回清晰错误。
- [Risk] 非 Claude 前端展示不如 Claude 细。→ Mitigation：先提供基础 turns/events 展示，后续再优化 agent 专属渲染。
- [Risk] `--projects-dir` 对 OpenCode 语义不直观。→ Mitigation：文案说明可传 DB 文件或 DB 所在目录。

## Migration Plan

1. 新增 CodexAdapter 和 OpenCodeAdapter。
2. 更新 registry implemented agent。
3. 更新 viewer API 非 Claude session 返回。
4. 更新前端通用 turns/events 展示。
5. 补测试 fixture。
6. 手动验证 `ccwhat web --agent codex`、`ccwhat web --agent opencode`、`ccwhat -- codex`、`ccwhat -- opencode`。

## Open Questions

- OpenCode 是否应优先使用 `session_message` 而不是 `message/part`，需要实现时用真实 DB 对比。
- Codex 是否只靠 rollout JSONL 就足够列出项目，还是必须依赖 `state_5.sqlite` 才能得到更好标题。
