## MODIFIED Requirements

### Requirement: Record raw request and response
代理 addon SHALL 在 mitmproxy 的 `response` 钩子中将完整的请求和响应原始内容以 JSONL 格式追加到对应 session 子目录下的当天日志文件。记录请求 headers 时，SHALL 过滤掉 `Authorization` header（大小写不敏感），其余 headers 完整保留。

日志路径格式为 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`，sessionId 从请求 header `X-Claude-Code-Session-Id` 提取，不存在时使用 `unknown`。

#### Scenario: Log path includes session ID
- **WHEN** 代理收到来自 Claude Code 客户端的请求（携带 `X-Claude-Code-Session-Id` header）
- **THEN** 日志写入 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`

#### Scenario: Log path fallback for unknown session
- **WHEN** 请求不携带 `X-Claude-Code-Session-Id` header
- **THEN** 日志写入 `<output_dir>/unknown/YYYY-MM-DD.jsonl`

#### Scenario: Record standard HTTP response
- **WHEN** 一个匹配过滤域名的 HTTP 请求完成（非 SSE）
- **THEN** 一条 JSON 记录被追加到 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`，包含：请求时间戳（ISO8601）、URL、HTTP 方法、请求 headers（dict，已排除 `Authorization`）、请求 body（字符串）、响应状态码、完整响应 headers（dict）、响应 body（字符串）、`is_sse: false`

#### Scenario: Authorization header excluded from log
- **WHEN** 请求携带 `Authorization` header（任意大小写，如 `Authorization`、`authorization`、`AUTHORIZATION`）
- **THEN** 写入 JSONL 的记录中 `request.headers` 字段不包含该 key，其他 headers 正常保留

#### Scenario: JSONL append mode
- **WHEN** 同一 session 同一天内有多条请求被记录
- **THEN** 所有记录追加写入同一个 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl` 文件，每条记录占一行

#### Scenario: Output directory auto-creation
- **WHEN** `<output_dir>/<sessionId>/` 目录不存在
- **THEN** 自动创建该目录

#### Scenario: Log file auto-rotation
- **WHEN** 代理运行跨越午夜（日期变更）
- **THEN** 新的请求写入新日期对应的 `YYYY-MM-DD.jsonl` 文件
