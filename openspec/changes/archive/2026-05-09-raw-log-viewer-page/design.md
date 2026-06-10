## Context

Parsed JSONL 记录结构（`*_parsed.jsonl`）：
- `timestamp`、`domain`、`method`、`url`
- `claude_session_id`
- `request_json`：`{model, messages[], system[], tools[], ...}`
- `response_json`：`{message: {id, model, stop_reason, content: {text}, usage}}`

## Goals / Non-Goals

**Goals:**
- 后端 `/api/logs?session=<id>&limit=<n>` 扫描 logs_dir，按时间倒序返回记录，支持 session 过滤
- 前端两栏布局：左栏列表（时间、model、stop_reason、token 用量、response 前 80 字），右栏明细
- 明细区展示：基本信息、response 内容、token usage、折叠的 request_json（messages 隐藏）、完整 request_json

**Non-Goals:**
- 不做分页（一次加载全部，性能够用）
- 不支持跨 logs 目录

## Decisions

### 后端一次返回全部记录（不分页）

日常使用量 < 500 条，JSON 序列化后 < 5MB，前端过滤即可。

### 左右分栏，右栏 sticky

左栏固定宽度（380px），右栏占剩余空间，右栏内容 sticky 跟随滚动。

### 列表摘要字段

时间（本地格式）、model（截断）、stop_reason badge、input/output token、response text 前 80 字。

### session 过滤在后端做

扫描所有文件时收集 session 列表，前端 selector 变化时重新请求。
