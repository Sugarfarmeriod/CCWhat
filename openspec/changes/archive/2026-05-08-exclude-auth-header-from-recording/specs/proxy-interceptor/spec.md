## MODIFIED Requirements

### Requirement: Record raw request and response
代理 addon SHALL 在 mitmproxy 的 `response` 钩子中将完整的请求和响应原始内容以 JSONL 格式追加到当天日志文件。记录请求 headers 时，SHALL 过滤掉 `Authorization` header（大小写不敏感），其余 headers 完整保留。

#### Scenario: Record standard HTTP response
- **WHEN** 一个匹配过滤域名的 HTTP 请求完成（非 SSE）
- **THEN** 一条 JSON 记录被追加到 `logs/YYYY-MM-DD.jsonl`，包含：请求时间戳（ISO8601）、URL、HTTP 方法、请求 headers（dict，已排除 `Authorization`）、请求 body（字符串）、响应状态码、完整响应 headers（dict）、响应 body（字符串）、`is_sse: false`

#### Scenario: Authorization header excluded from log
- **WHEN** 请求携带 `Authorization` header（任意大小写，如 `Authorization`、`authorization`、`AUTHORIZATION`）
- **THEN** 写入 JSONL 的记录中 `request.headers` 字段不包含该 key，其他 headers 正常保留

#### Scenario: JSONL append mode
- **WHEN** 同一天内有多条请求被记录
- **THEN** 所有记录追加写入同一个 `logs/YYYY-MM-DD.jsonl` 文件，每条记录占一行，文件内容为合法的 JSONL 格式

#### Scenario: Output directory configuration
- **WHEN** 用户执行 `deep-ai-analysis proxy --output ./my-logs`
- **THEN** 日志文件写入 `./my-logs/YYYY-MM-DD.jsonl`；目录不存在时自动创建

#### Scenario: Log file auto-rotation
- **WHEN** 代理运行跨越午夜（日期变更）
- **THEN** 新的请求写入新日期对应的 `YYYY-MM-DD.jsonl` 文件

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
- **THEN** 将完整记录作为一行 JSON 追加到当天 JSONL 文件：`is_sse: true`，`sse_events` 包含本次连接所有完整事件的原始文本列表，`response.body` 为所有事件拼接的完整字符串，`request.headers` 已排除 `Authorization` header

#### Scenario: SSE Authorization header excluded from log
- **WHEN** SSE 请求携带 `Authorization` header
- **THEN** 写入 JSONL 的 SSE 记录中 `request.headers` 字段不包含该 key
