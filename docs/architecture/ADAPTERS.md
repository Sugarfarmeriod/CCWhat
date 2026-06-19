# 多 Agent Log Adapter 文档

本文档说明 AgentLens 如何读取不同 Coding Agent 的本地日志，以及如何将它们清洗成统一结构。

## Adapter 的职责

Log Adapter 只负责本地 session log：

- 找到 agent 的默认日志目录或数据库。
- 列出 project。
- 列出 session。
- 读取单个 session。
- 将原始记录转成 normalized event / turn / usage。
- 保留 raw 数据。

Log Adapter 不负责：

- 生成报告。
- 调用 AI CLI。
- 读取网络 Request/Response。
- 计算网络层 cache hit rate。

## 入口文件

主要目录：

- `agentlens/adapters/base.py`
- `agentlens/adapters/registry.py`
- `agentlens/adapters/claude.py`
- `agentlens/adapters/opencode.py`
- `agentlens/adapters/codex.py`

`base.py` 定义统一接口：

```python
class AgentAdapter:
    name: str
    def default_projects_dir(self) -> Path: ...
    def list_projects(self) -> list[dict]: ...
    def list_sessions(self) -> list[dict]: ...
    def load_session(self, session_id: str) -> dict | None: ...
    def raw_to_normalized_events(self, raw_entry: dict, session_id: str) -> list[dict]: ...
```

`registry.py` 负责：

- 标准化 agent 名称。
- 根据 agent 创建 adapter。
- 从 target command 推断 observed agent。

## 当前支持的 Agent

### Claude Code

Adapter：`ClaudeAdapter`

默认来源：

```text
~/.claude/projects
```

典型结构：

- project 目录下有 UUID 命名的 `.jsonl` session 文件。
- subagent 通常位于 session 目录下的 `subagents/`。
- usage 字段常见于 assistant message 的 `message.usage`。

常见 token 字段：

- `input_tokens`
- `output_tokens`
- `cache_creation_input_tokens`
- `cache_read_input_tokens`

### OpenCode

Adapter：`OpenCodeAdapter`

默认来源：

```text
~/.local/share/opencode/storage/session
```

OpenCode 的数据主要来自本地 SQLite DB。

常见 token 字段：

- `tokens_input`
- `tokens_output`
- `tokens_reasoning`
- `tokens_cache_read`
- `tokens_cache_write`

注意：

- OpenCode 有 session 级和 step/part 级 token 数据。
- 工具调用时间需要从 part/state 的 start/end 或 created/updated 字段推导。
- DB 中的 agent 字段可能是 `build` 等工作模式，不一定是产品名 `opencode`。

### Codex

Adapter：`CodexAdapter`

默认来源：

```text
~/.codex/sessions
~/.codex/state_5.sqlite
```

Codex 通常同时有：

- rollout JSONL
- SQLite metadata

常见 token 字段：

- `tokens_used`
- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `reasoning_output_tokens`
- `total_tokens`

注意：

- SQLite `threads` 表中 provider 字段可能叫 `model_provider`。
- rollout 中可能包含大量 `developer`、`environment_context`、skills/app instructions。
- 这些上下文必须作为 metadata 或被压缩处理，不能直接当作 assistant/user 正文进入报告。

## Normalized Session 结构

Adapter 的 `load_session()` 应尽量返回：

```json
{
  "agent": "codex",
  "sessionId": "...",
  "projectDir": "...",
  "main": [],
  "subagents": [],
  "events": [],
  "turns": [],
  "usage": {},
  "_metadata": {}
}
```

旧字段 `main` 和 `subagents` 是为了兼容现有前端。

新链路应优先消费：

- `events`
- `turns`
- `usage`
- `_metadata`

## Normalized Event 结构

建议 event 包含：

```json
{
  "id": "...",
  "agent": "opencode",
  "sessionId": "...",
  "turnId": "...",
  "timestamp": "2026-06-09T00:00:00Z",
  "role": "assistant",
  "kind": "tool_call",
  "content": {},
  "summary": "Tool: bash",
  "toolName": "bash",
  "toolCallId": "call_1",
  "parentId": null,
  "usage": {},
  "raw": {}
}
```

常见 `kind`：

- `message`
- `tool_call`
- `tool_result`
- `reasoning`
- `metadata`
- `error`
- `unknown`

常见 `role`：

- `user`
- `assistant`
- `tool`
- `system`
- `null`

## Usage 字段设计

统一 usage 建议使用 camelCase：

```json
{
  "inputTokens": 100,
  "outputTokens": 20,
  "reasoningTokens": 10,
  "cacheReadTokens": 50,
  "cacheWriteTokens": 5,
  "cacheCreationTokens": 5,
  "cachedInputTokens": 30,
  "totalTokens": 130,
  "scope": "event",
  "source": "agent_log",
  "raw": {}
}
```

当前不要默认展示 `cacheHitRate`，原因：

- 三个 agent 本地日志都能拿到 token 和 cache token 计数。
- 三个 agent 都没有统一、官方定义好的 cache 命中率。
- 如果未来要展示 cache hit rate，需要先定义公式和数据来源。

## 添加新 Agent 的步骤

1. 新建 `agentlens/adapters/<agent>.py`。
2. 实现 `AgentAdapter` 接口。
3. 在 `agentlens/adapters/registry.py` 注册名称和别名。
4. 写真实风格 fixture 或临时 SQLite 测试。
5. 覆盖：
   - `list_projects()`
   - `list_sessions()`
   - `load_session()`
   - `raw_to_normalized_events()`
   - usage 映射
   - raw 保留
6. 手动运行：

```bash
agentlens web --agent <agent>
agentlens -- <agent>
```

## 常见坑

- 不要假设不同 agent 的 JSON 字段同名。
- 不要把系统上下文、developer instructions 当成普通 assistant 正文。
- 不要伪造 0 token；没有数据时就不返回该字段。
- 不要丢弃 raw。
- 不要让 adapter 直接调用 analyzer。
- 不要因为某个 agent 的内部 agent 字段叫 `build`，就把 AgentLens 的 agent 显示成 `build`。

