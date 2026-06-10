## Context

原始日志记录结构：`sse_events` 是字符串数组，每条格式为 `event: <type>\ndata: <json>`。`message.id`（`msg_bdrk_xxx`）存在于 `type: "message_start"` 事件的 `message.id` 字段中。

前端已全量加载当前 session+date 的记录，搜索无需额外网络请求。

## Goals / Non-Goals

**Goals:**
- 后端解析 SSE records 的 `message_start` 事件，提取 `message.id`，注入为 `_message_id` 字段
- 前端搜索框支持：精确匹配 `_message_id`（`msg_bdrk_xxx`）、URL path 模糊匹配
- 搜索实时过滤列表（`oninput`），无需回车

**Non-Goals:**
- 不做全文搜索（body 内容搜索）
- 不支持跨 session/date 搜索

## Decisions

### 后端注入 `_message_id`，前端搜索

**Why**: `message.id` 需要解析 SSE events，在后端一次性提取比前端每次过滤都解析更高效；且避免前端依赖 SSE 解析逻辑重复。前缀 `_` 表示这是服务端注入的计算字段，与原始字段区分。

### 搜索范围：`_message_id` + URL

`_message_id` 是本次搜索的核心诉求；URL 是用户常用的过滤维度，一并支持代价很小。
