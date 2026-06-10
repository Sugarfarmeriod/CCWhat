## Context

**数据关联关系：**

会话 JSONL（`~/.claude/projects/<proj>/<sessionId>.jsonl`）中，user 条目有：
- `uuid`：唯一标识（作为 messageId 传给后端）
- `timestamp`：如 `2026-05-08T09:55:12.835Z`

Parsed JSONL（`logs/*_parsed.jsonl`）中，每条记录有：
- `claude_session_id`：对应会话 ID
- `timestamp`：HTTP 请求发出时间，比触发它的 user 消息晚约 0~30 秒（因为 Claude 处理后才发 API 请求）

**匹配逻辑：** 找到 user 条目的 timestamp T，在 parsed JSONL 中查找满足 `claude_session_id == sessionId AND T - 5s <= record.timestamp <= T + 60s` 的记录（留一定宽窗）。通常一条 user 消息对应 1~N 条 API 请求。

## Goals / Non-Goals

**Goals:**
- 后端：`GET /api/message-http/<sessionId>/<messageId>` 查找并返回对应 parsed 记录列表
- 后端：启动参数新增 `--logs-dir`（默认 `./logs`），指定 parsed JSONL 所在目录
- 前端：user 气泡右上角「查看请求」按钮（仅主会话非 tool_result 的用户消息显示）
- 前端：弹窗展示匹配到的记录：timestamp、model、messages 数量、response content.text、usage

**Non-Goals:**
- 不精确匹配（时间窗口近似即可）
- 不展示完整 request_json messages 列表（太大，只显示摘要）
- subagent 消息不显示此按钮

## Decisions

### 时间窗口匹配而非精确 ID 匹配

Parsed JSONL 里没有 promptId/messageId 字段，两边唯一共同字段是 `claude_session_id` 和时间戳。

**Why**: 这是两个独立系统（Claude Code 会话日志 vs mitmproxy 抓包日志）的关联，时间窗口是最实用的方案。窗口设为 `[-5s, +60s]`，容纳 Claude 处理时间（通常 <30s）。

### 后端扫描 logs 目录所有 `*_parsed.jsonl`

不限制具体文件名，扫描目录下所有符合模式的文件。

**Why**: 用户可能在不同日期产生多个 parsed 文件，全扫描确保不遗漏。

### 前端弹窗（模态框）展示

点击按钮后请求后端，返回结果用简单的 overlay 弹窗展示。

**Why**: 不破坏主会话视图布局，弹窗聚焦展示 API 请求信息。

## Risks / Trade-offs

- **时间窗口误匹配**：同一 session 在短时间内有多条 user 消息时可能多匹配 → 展示所有匹配结果，用 timestamp 排序，用户自行判断
- **logs 目录不存在/为空**：返回空数组，前端展示"未找到记录"
