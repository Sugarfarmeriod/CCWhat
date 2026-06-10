## Why

原始请求/响应日志查看器（`req-resp.html`）目前只能逐条翻看，无法快速定位特定请求。Claude Code 会话查看器（`index.html`）中点击「查看请求」按钮时使用 `response_json.message.id`（即 `msg_bdrk_xxx`）查询对应日志，但原始日志中该 ID 需要解析 SSE events 才能获取。需要搜索功能，让用户能通过 `message.id` 快速找到对应记录。

## What Changes

- 后端 `GET /api/req-resp/records` 接口在返回记录时预先提取 SSE `message.id`，注入为顶层字段 `_message_id`
- `req-resp.html` 顶部新增搜索框，支持按 `_message_id` 或 URL 片段实时过滤列表

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `session-viewer`: 后端 `/api/req-resp/records` 返回记录时注入 `_message_id`；前端新增搜索过滤

## Impact

- `viewer/server.py`：`get_req_resp_records()` 在返回前解析 SSE events 提取 `message_start.message.id`，注入为 `_message_id`
- `viewer/req-resp.html`：顶部新增搜索框，列表渲染时按 `_message_id` 和 URL 过滤
