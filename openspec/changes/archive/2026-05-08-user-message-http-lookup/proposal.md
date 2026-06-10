## Why

在会话查看器中，用户消息气泡目前只展示文本内容，无法看到该用户消息触发的底层 HTTP 请求/响应数据（即向 api.example.com 发出的 Anthropic API 调用）。增加查询入口，让开发者能直接在会话视图中查看每条用户消息对应的原始 API 请求和响应，便于排查和分析。

## What Changes

- 用户消息气泡右上角增加「查看请求」按钮
- 点击后向后端发请求，传入 `sessionId` + `messageId`（会话条目的 uuid），查询对应的 HTTP 请求/响应记录
- 后端新增 `GET /api/message-http/<sessionId>/<messageId>` 接口：
  - 在会话 JSONL 中找到对应 user 条目，获取其时间戳
  - 在 `logs/` 目录下扫描所有 `*_parsed.jsonl` 文件
  - 按 `claude_session_id` + 时间窗口（±30s）匹配，返回匹配到的记录列表
- 前端弹窗展示返回的请求/响应数据（request_json 摘要 + response_json）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `session-viewer`: 用户消息气泡新增「查看请求」按钮和结果弹窗
- `session-viewer`: 后端新增 `/api/message-http/<sessionId>/<messageId>` 接口

## Impact

- `viewer/server.py`：新增 `GET /api/message-http/<sessionId>/<messageId>` 接口
- `viewer/index.html`：用户气泡 UI 新增按钮 + 弹窗展示逻辑
- 需要指定 `--logs-dir`（默认 `./logs`）供后端查找 parsed JSONL
