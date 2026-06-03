## Context

`RecorderAddon` 的 `_jsonl_path()` 当前返回 `output_dir / YYYY-MM-DD.jsonl`，在 `response` 钩子中调用。session_id 需要从每条 flow 的请求 header 中提取。

SSE flow 的日志路径在两处写入：
1. `response()` 钩子中的普通请求记录
2. `response()` 钩子中 SSE 流结束后的记录（同一 flow）

两者使用同一 flow 对象，可以在 `response()` 里统一提取 session_id。

## Goals / Non-Goals

**Goals:**
- `_jsonl_path(session_id)` 返回 `output_dir / session_id / YYYY-MM-DD.jsonl`
- session_id 从 `flow.request.headers.get("X-Claude-Code-Session-Id", "unknown")` 提取
- 目录 `output_dir/session_id/` 不存在时自动创建

**Non-Goals:**
- 不对历史日志做迁移
- 不校验 session_id 格式

## Decisions

### 在 `response()` 钩子里提取 session_id，传入 `_jsonl_path()`

**Why**: session_id 是 per-flow 属性，只有 flow 对象才能获取。`_jsonl_path()` 改为接受参数而非查全局状态，保持职责清晰。

### 降级值为 `"unknown"`

**Why**: 非 Claude Code 客户端发出的请求可能没有此 header，用 `"unknown"` 子目录聚合，不丢数据。
