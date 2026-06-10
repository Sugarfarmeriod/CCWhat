## Context

上一个 change（`record-sse-content-field`）在 SSE JSONL 记录中新增了 `sse_content` 字段。现在决定将其从原始日志中移除，减少日志冗余。`response.body` 已经是所有事件的拼接，`sse_content` 与其完全重复。

## Goals / Non-Goals

**Goals:**
- 从 SSE JSONL 记录中移除 `sse_content` 字段
- 保留 `sse_events` 和 `response.body` 不变

**Non-Goals:**
- 不修改内存中的 SSE 缓冲逻辑
- 不影响普通 HTTP 记录

## Decisions

### 直接删除写入行，不做任何替代

在 `recorder.py` 中删除 `record["sse_content"] = "\n\n".join(sse_events)` 这一行即可。

**Why**: 变更极小，无需抽象或配置化。

## Risks / Trade-offs

- **破坏性变更**：已依赖 `sse_content` 字段的下游消费方需要改用 `response.body` → 当前项目无已知外部消费方，风险可控
