## Why

`sse_content` 字段是所有 `sse_events` 拼接后的冗余副本，与 `response.body` 内容相同，在原始日志中重复存储增加了日志体积。该字段的价值在于分析阶段的便捷性，但不应出现在原始 JSONL 日志记录中。

## What Changes

- SSE 记录写入 JSONL 时，移除 `sse_content` 字段
- `sse_events`（原始事件列表）和 `response.body`（拼接字符串）保持不变
- 普通 HTTP 记录无影响

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `proxy-interceptor`: 修改"SSE stream recording"需求——移除 JSONL 记录中的 `sse_content` 字段

## Impact

- `deep_ai_analysis/addons/recorder.py`：删除构建 SSE record 时写入 `sse_content` 的一行代码
- JSONL 日志格式变更：SSE 记录不再包含 `sse_content` 字段（**BREAKING** 对已依赖该字段的消费方）
