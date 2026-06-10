## MODIFIED Requirements

### Requirement: SSE stream recording
代理 addon SHALL 检测并完整记录 SSE（Server-Sent Events）流式响应，连接关闭后将完整记录作为一行追加到 JSONL 文件。记录请求 headers 时，SHALL 过滤掉 `Authorization` header（大小写不敏感）。

#### Scenario: Detect SSE response
- **WHEN** 响应头包含 `content-type: text/event-stream`
- **THEN** addon 识别该响应为 SSE 流，为该 flow 启用流式记录模式（`flow.response.stream = True`）

#### Scenario: Buffer SSE events in memory
- **WHEN** SSE 连接活跃且新的 chunk 到达
- **THEN** addon 解析 chunk 中完整的 SSE 事件（以 `\n\n` 为边界），将每个完整事件追加到该 flow 的内存缓冲 `sse_events` 列表

#### Scenario: Partial SSE chunk buffering
- **WHEN** 接收到的 chunk 末尾不以 `\n\n` 结尾（事件边界不完整）
- **THEN** addon 将不完整部分存入该 flow 的 per-flow 缓冲区，等待后续 chunk 合并后再解析

#### Scenario: SSE session complete — write to JSONL
- **WHEN** SSE 连接关闭（flow 完成）
- **THEN** 将完整记录作为一行 JSON 追加到当天 JSONL 文件：`is_sse: true`，`sse_events` 包含本次连接所有完整事件的原始文本列表，`response.body` 为所有事件拼接的完整字符串，`sse_content` 为所有 `sse_events` 以 `\n\n` 拼接后的完整字符串，`request.headers` 已排除 `Authorization` header

#### Scenario: sse_content field present in SSE record
- **WHEN** SSE 连接关闭，记录写入 JSONL
- **THEN** 记录中包含顶层字段 `sse_content`，其值等于 `"\n\n".join(sse_events)`；普通 HTTP 记录（`is_sse: false`）中不包含 `sse_content` 字段

#### Scenario: SSE Authorization header excluded from log
- **WHEN** SSE 请求携带 `Authorization` header
- **THEN** 写入 JSONL 的 SSE 记录中 `request.headers` 字段不包含该 key
