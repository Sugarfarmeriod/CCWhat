## Why

SSE 记录中所有事件的拼接文本目前存储在 `response.body` 字段，与普通 HTTP 响应的字段语义重叠，不便于消费方直接识别和提取 SSE 完整内容。增加专用的 `sse_content` 字段，明确存放所有 SSE 事件拼接后的完整文本，使日志结构更清晰、更易解析。

## What Changes

- SSE 流结束写入 JSONL 时，新增顶层字段 `sse_content`，值为所有 `sse_events` 拼接后的完整字符串（以 `\n\n` 为分隔符）
- `response.body` 保持不变（仍为拼接字符串），保持向后兼容
- 仅影响 `is_sse: true` 的记录，普通 HTTP 记录无变化

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `proxy-interceptor`: 修改"SSE stream recording"需求——SSE 记录写入 JSONL 时须包含 `sse_content` 字段

## Impact

- `deep_ai_analysis/addons/recorder.py`：在构建 SSE record dict 时新增 `sse_content` 字段
- JSONL 日志格式变更：SSE 记录新增 `sse_content` 字段（非破坏性，旧消费方不受影响）
