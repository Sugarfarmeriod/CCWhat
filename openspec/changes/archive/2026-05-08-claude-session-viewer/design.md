## Context

Claude Code 日志目录结构：
```
~/.claude/projects/<project-dir>/
  <sessionId>.jsonl              # 主会话日志
  <sessionId>/
    subagents/
      agent-<agentId>.jsonl      # subagent 日志
      agent-<agentId>.meta.json  # {"agentType": "...", "description": "..."}
```

JSONL 条目结构：
- `type: user`：`message.content` 为字符串或数组（含 `tool_result`）；有 `agentId` 字段时为 subagent 条目
- `type: assistant`：`message.content` 为数组（含 `text` 和 `tool_use` 块）
- `isSidechain: true`：sidechain 条目，在主会话中跳过（subagent 日志本身就是 sidechain）
- `tool_use` / `tool_result` 通过 `tool_use_id` 配对

## Goals / Non-Goals

**Goals:**
- Python 后端：读取本地文件，提供 REST API，无文件上传
- 前端：通过 sessionId 加载主会话 + subagent 列表，分标签展示
- 渲染 user/assistant 消息，工具调用内联展示（输入截断+展开，结果折叠+展开）
- 统计：消息数、工具调用数、token 用量
- subagent 标签显示 description 和 agentType

**Non-Goals:**
- 不支持跨项目浏览
- 不解析 `attachment`、`file-history-snapshot` 等元数据条目
- 不需要认证

## Decisions

### 后端：Python 标准库 http.server + json

使用 `http.server.BaseHTTPRequestHandler`，无需 Flask/FastAPI 等依赖。

**Why**: 项目只有 click/mitmproxy 依赖，viewer 是独立工具，不引入新依赖最简洁。

### API 设计

```
GET /api/session/<sessionId>          → {main: [...entries], subagents: [{agentId, meta, entries}]}
GET /api/projects                     → [{projectDir, sessions: [sessionId, ...]}]
```

后端在启动时接受 `--projects-dir`（默认 `~/.claude/projects`），在该目录下按 sessionId 查找文件。

### 前端：主会话 + subagent 标签页

主会话为第一个标签，每个 subagent 为独立标签（显示 description 截断）。标签间切换不重新请求，一次加载全部。

### 工具调用配对（主会话）

主会话中跳过 `isSidechain: true` 条目。收集 assistant 的 `tool_use`，在后续 user 的 `tool_result` 中匹配，内联渲染在对应 assistant 气泡内。

### Subagent 日志渲染

Subagent 日志全部是 `isSidechain: true`，直接渲染所有 user/assistant 条目（不跳过）。

## Risks / Trade-offs

- **CORS**：前端从 `file://` 打开时无法调用 `http://localhost` API → 后端设置 `Access-Control-Allow-Origin: *`
- **项目目录路径**：项目目录名是工作目录路径转换（`/` → `-`），后端扫描时列出所有目录即可，不需要反推路径
