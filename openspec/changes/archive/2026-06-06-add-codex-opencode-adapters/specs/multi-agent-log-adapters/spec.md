## ADDED Requirements

### Requirement: Codex Adapter
系统 MUST 实现 Codex adapter，用于读取 Codex 本地会话记录并输出 normalized session 数据。

#### Scenario: 列出 Codex sessions
- **WHEN** `~/.codex/sessions` 下存在 `YYYY/MM/DD/rollout-*.jsonl` 文件
- **THEN** Codex adapter 必须列出对应 session，并返回 `agent: "codex"`、`projectDir` 和 `sessions`

#### Scenario: 读取 Codex session
- **WHEN** 请求读取一个存在的 Codex session id
- **THEN** Codex adapter 必须读取对应 rollout JSONL，并返回 `agent: "codex"`、`sessionId`、`projectDir`、`events`、`turns` 和 `usage`

#### Scenario: Codex metadata 补充
- **WHEN** `~/.codex/state_5.sqlite` 可读且包含对应 thread
- **THEN** Codex adapter 必须用 SQLite 中的 title、cwd、model、provider、updated time 或 token metadata 补充 session 信息

#### Scenario: Codex SQLite 不可用
- **WHEN** `~/.codex/state_5.sqlite` 不存在、不可读或缺少对应 thread
- **THEN** Codex adapter 必须仍能基于 rollout JSONL 展示 session，不得整体失败

#### Scenario: Codex usage 映射
- **WHEN** Codex 本地记录提供 `input_tokens`、`cached_input_tokens`、`output_tokens`、`reasoning_output_tokens`、`total_tokens` 或 `tokens_used`
- **THEN** Codex adapter 必须映射到 CCWhat 通用 usage 字段，并标注 `source: "agent_log"`

#### Scenario: Codex unknown event 降级
- **WHEN** Codex rollout JSONL 包含 adapter 尚未识别的 event type
- **THEN** Codex adapter 必须保留 raw 数据并输出 `kind: "unknown"` 或 `kind: "event"` 的 normalized event

### Requirement: OpenCode Adapter
系统 MUST 实现 OpenCode adapter，用于读取 OpenCode 本地 SQLite 会话数据库并输出 normalized session 数据。

#### Scenario: 列出 OpenCode sessions
- **WHEN** `~/.local/share/opencode/opencode.db` 存在且包含 `session` 表
- **THEN** OpenCode adapter 必须列出对应 session，并返回 `agent: "opencode"`、`projectDir` 和 `sessions`

#### Scenario: 读取 OpenCode session
- **WHEN** 请求读取一个存在的 OpenCode session id
- **THEN** OpenCode adapter 必须读取 `session`、`message` 和 `part` 表，并返回 `agent: "opencode"`、`sessionId`、`projectDir`、`events`、`turns` 和 `usage`

#### Scenario: OpenCode project metadata
- **WHEN** `project` 表包含对应 project id
- **THEN** OpenCode adapter 必须用 project/worktree 信息补充 projectDir 或 session metadata

#### Scenario: OpenCode usage 映射
- **WHEN** OpenCode session、message 或 step-finish 提供 `tokens_input`、`tokens_output`、`tokens_reasoning`、`tokens_cache_read`、`tokens_cache_write` 或嵌套 `tokens.cache.read/write`
- **THEN** OpenCode adapter 必须映射到 CCWhat 通用 usage 字段，并标注对应 `scope`

#### Scenario: OpenCode schema 缺失
- **WHEN** OpenCode DB 缺少必要表或字段
- **THEN** OpenCode adapter 必须返回清晰错误，不得静默显示空数据

### Requirement: Registry 支持 Codex 和 OpenCode
系统 MUST 将 Codex 和 OpenCode 注册为已实现 agent。

#### Scenario: 创建 Codex adapter
- **WHEN** 用户指定 `codex`
- **THEN** registry 必须返回 Codex adapter，而不是未实现错误

#### Scenario: 创建 OpenCode adapter
- **WHEN** 用户指定 `opencode`、`open-code` 或 `open_code`
- **THEN** registry 必须返回 OpenCode adapter，而不是未实现错误

#### Scenario: Run 模式不再 fallback
- **WHEN** 用户运行 `ccwhat -- codex` 或 `ccwhat -- opencode`
- **THEN** viewer 必须使用对应 adapter，不得因 adapter 未实现 fallback 到 Claude

### Requirement: 非 Claude Agent Log 展示
系统 MUST 支持基于 normalized events/turns 展示 Codex 和 OpenCode session。

#### Scenario: Session API 返回非 Claude 兼容壳
- **WHEN** 前端请求 Codex 或 OpenCode session
- **THEN** API 必须返回 `main: []`、`subagents: []`、`events` 和 `turns`，不得伪装 Claude 原始结构

#### Scenario: 前端展示 turns
- **WHEN** session 数据没有 Claude `main/subagents` 但包含 `turns`
- **THEN** 前端必须展示 normalized turns 的基础内容、工具调用、reasoning 和 usage

#### Scenario: 前端展示 events
- **WHEN** session 数据没有可用 `turns` 但包含 `events`
- **THEN** 前端必须展示 normalized events 的基础列表

#### Scenario: Req/Resp 页面保持独立
- **WHEN** 展示 Codex 或 OpenCode 本地日志
- **THEN** 系统必须保持 Req/Resp 页面独立，只允许作为跳转或补充来源

### Requirement: Codex/OpenCode 测试
系统 MUST 为 CodexAdapter、OpenCodeAdapter 和非 Claude 展示路径补充测试。

#### Scenario: Codex fixture 测试
- **WHEN** 测试使用临时 Codex rollout JSONL
- **THEN** 测试必须验证 Codex adapter 能列出 session、读取 session、输出 events/turns/usage

#### Scenario: OpenCode fixture 测试
- **WHEN** 测试使用临时 OpenCode SQLite DB
- **THEN** 测试必须验证 OpenCode adapter 能列出 session、读取 session、输出 events/turns/usage

#### Scenario: Registry 测试更新
- **WHEN** 测试请求 `codex` 或 `opencode`
- **THEN** 测试必须验证 registry 返回真实 adapter

#### Scenario: CLI 测试更新
- **WHEN** 测试运行 `ccwhat web --agent codex/opencode`
- **THEN** 测试必须验证 viewer 使用对应 adapter

#### Scenario: Claude 回归
- **WHEN** 运行 ClaudeAdapter、export/import 和现有 viewer 测试
- **THEN** 测试必须继续通过
